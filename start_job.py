import subprocess
import schedule
import time
from config import config

JOB_RETRY_NUM_MAX = 3


def job_func() -> None:
    retry_num = 0
    result = 1
    while result != 0 and retry_num < JOB_RETRY_NUM_MAX:
        process:subprocess.CompletedProcess = subprocess.run("python ./infer.py", shell=True, check=False)
        result = process.returncode
        retry_num += 1


job: schedule.Job = schedule.Job(config.job_interval, scheduler=schedule.default_scheduler)
job.unit = config.job_unit
job.start_day = config.job_day
job.at(config.job_time)
job.do(job_func)
print("started")
job.run()

while True:
    schedule.run_pending()
    time.sleep(1)
