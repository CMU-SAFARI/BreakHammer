import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor

from scripts.run_config import *

argparser = argparse.ArgumentParser(
    prog="ExecuteRunScript",
    description="Execute a simulation run script"
)

argparser.add_argument("-s", "--slurm", action="store_true")

args = argparser.parse_args()

SLURM = args.slurm

def check_running_jobs():
    return int(os.popen(f"squeue -u {SLURM_USERNAME} -h | wc -l").read())

def run_slurm(commands):
    for cmd in commands:
        while check_running_jobs() >= MAX_SLURM_JOBS:
            print(f"[INFO] Maximum Slurm Job limit ({MAX_SLURM_JOBS}) reached. Retrying in {SLURM_RETRY_DELAY} seconds")
            time.sleep(SLURM_RETRY_DELAY)
        os.system(cmd)
        time.sleep(SLURM_SUBMIT_DELAY)

def run_personal(commands):
    with ThreadPoolExecutor(max_workers=PERSONAL_RUN_THREADS) as executor:
        def run_command(cmd):
            os.system(f"echo \"Running: {cmd}\"")
            os.system(cmd)
        executor.map(run_command, commands)

if __name__ == "__main__":
    lines = []
    with open("run.sh", "r") as f:
        lines = [l.strip() for l in f.readlines()]
    
    if SLURM:
        run_slurm(lines)
    else:
        run_personal(lines) 