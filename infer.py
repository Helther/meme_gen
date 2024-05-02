from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from transformers import AutoProcessor, LlavaForConditionalGeneration, set_seed
import torch
import os
import time
from PIL import Image
from compel import Compel
from config import config, OUTPUTS_PATH, MODELS_PATH, SCRIPT_PATH
from messenger_api import create_api_from_config


SD_MODEL_ID = "stabilityai/stable-diffusion-2-1"
IMG_TO_TEXT_MODEL_ID = "llava-hf/llava-1.5-7b-hf"
OUTPUT_IMAGE_PATH = os.path.join(OUTPUTS_PATH, f'image_out_0.png')
REFERENCE_IMAGE = Image.open(os.path.join(SCRIPT_PATH, config.ref_img_path)) if config.ref_img_path and config.update_ref_img else None


def get_available_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def clear_dir(dir_name: str) -> None:
    for filename in os.listdir(dir_name):
        file_path = os.path.join(dir_name, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.remove(file_path)


def infer() -> tuple[list[str], str]:
    global current_reference
    global model
    global processor
    global pipe
    global compel
    new_promt = config.promt
    if current_reference:
        model = LlavaForConditionalGeneration.from_pretrained(
            IMG_TO_TEXT_MODEL_ID, 
            torch_dtype=torch.float16 if get_available_device() == "cuda" else None, 
            low_cpu_mem_usage=True,
            load_in_4bit=True,
            cache_dir=MODELS_PATH
        )
        processor = AutoProcessor.from_pretrained(IMG_TO_TEXT_MODEL_ID, cache_dir=MODELS_PATH)
        inputs = processor(config.promt, current_reference, return_tensors='pt').to("cpu", torch.float16)
        output = model.generate(**inputs, max_new_tokens=200, do_sample=False)
        new_promt = processor.decode(output[0], skip_special_tokens=True)[len(config.promt)-1:]
    print(new_promt)

    prompt_embeds = compel([new_promt] * config.image_num_to_generate)
    images = pipe(prompt_embeds=prompt_embeds, generator=torch.Generator().manual_seed(int(time.time()))).images

    res = []
    for i, image in enumerate(images):
        path = os.path.join(OUTPUTS_PATH, f'image_out_{i}.png')
        image.save(path)
        res.append(path)

    return res, new_promt


def post_outputs(files: list[str], promt: str) -> None:
    api = create_api_from_config(config.messenger_api, config.server_url)
    api.login((config.auth_login, config.auth_pass))
    api.upload_files(files, config.chat_id)
    api.post_message(config.chat_id, promt)


def main() -> None:
    global current_reference

    if not os.path.exists(OUTPUTS_PATH):
        os.mkdir(OUTPUTS_PATH)

    if config.update_ref_img and os.path.isfile(OUTPUT_IMAGE_PATH):  # TODO choose from all outputs by text similarity
        img = Image.open(OUTPUT_IMAGE_PATH)
        current_reference = Image.new(mode=img.mode,size=img.size)
        current_reference.paste(img)
        img.close()
    clear_dir(OUTPUTS_PATH)

    saved_images, promt = infer()
    post_outputs(saved_images, promt)


current_reference = REFERENCE_IMAGE
#set_seed(int(time.time()))
pipe = DiffusionPipeline.from_pretrained(SD_MODEL_ID, torch_dtype=torch.float16 if get_available_device() == "cuda" else None, use_safetensors=True, variant="fp16", cache_dir=MODELS_PATH)
pipe.to(get_available_device())
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
compel = Compel(tokenizer=pipe.tokenizer, text_encoder=pipe.text_encoder)


if __name__ == "__main__":
    main()
