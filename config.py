import configparser
import os

CONFIG_FILE_NAME = "config"
SCRIPT_PATH = os.path.realpath(os.path.dirname(__file__))
MODELS_PATH = os.path.join(SCRIPT_PATH, "models")
OUTPUTS_PATH = os.path.join(SCRIPT_PATH, "outputs")
CONFIG_PATH = os.path.join(SCRIPT_PATH, "config")


class Config():
    def __init__(self) -> None:
        config = configparser.ConfigParser()
        with open(CONFIG_PATH, 'r') as config_file:
            config.read_file(config_file)
            config_section_name = "Main"

            self.update_ref_img = config[config_section_name].get("UPDATE_REFERENCE_IMAGE", "").lower() == "true"
            self.ref_img_path = config[config_section_name].get("REFERENCE_IMAGE_PATH", None)
            self.promt = config[config_section_name]["PROMT"]
            self.image_num_to_generate = int(config[config_section_name].get("IMAGES_NUM", 1))
            if self.image_num_to_generate < 1:
                self.image_num_to_generate = 1
            self.enable_img_to_img = config[config_section_name].get("IMG_TO_IMG", "").lower() == "true"

            self.messenger_api = config[config_section_name]["API_TYPE"]
            self.server_url = config[config_section_name]["SERVER_URL"]
            self.auth_login = config[config_section_name]["AUTH_LOGIN"]
            self.auth_pass = config[config_section_name]["AUTH_PASSW"]
            chat_id_str = config[config_section_name]["CHAT_ID"]
            self.chat_ids = set()
            chat_id_str = chat_id_str.replace(" ", "")
            ids = chat_id_str.split(",")
            for chat_id in ids:
                self.chat_ids.add(chat_id)

            self.job_interval = int(config[config_section_name].get("JOB_INTERVAL", 1))
            if self.job_interval < 1:
                self.job_interval = 1
            self.job_unit = config[config_section_name].get("JOB_UNIT", "weeks")
            self.job_day = config[config_section_name].get("JOB_START_DAY", "wednesday" if self.job_unit == "weeks" else None)
            self.job_time = config[config_section_name].get("JOB_TIME", "08:00")


config = Config()
