import os
import yaml
import copy
import argparse
import pandas as pd

from scripts.run_config import *

argparser = argparse.ArgumentParser(
    prog="RunPersonal",
    description="Run ramulator2 (with Podman) simulations using Slurm "
)

argparser.add_argument("-wd", "--working_directory")
argparser.add_argument("-bc", "--base_config")
argparser.add_argument("-tc", "--trace_combination")
argparser.add_argument("-td", "--trace_directory")
argparser.add_argument("-rd", "--result_directory")

args = argparser.parse_args()

WORK_DIR = args.working_directory
BASE_CONFIG_FILE = args.base_config
TRACE_COMBINATION_FILE = args.trace_combination
TRACE_DIR = args.trace_directory
RESULT_DIR = args.result_directory

HOST_RESULT_DIR = RESULT_DIR.replace("/app", WORK_DIR)

SBATCH_CMD = "sbatch --cpus-per-task=1 --nodes=1 --ntasks=1"

CMD_HEADER = "#! /bin/bash"
CMD = "/app/ramulator2"
LOAD_CMD = f"podman load --quiet -i {WORK_DIR}/breakhammer_artifact.tar"

BASE_CONFIG = None

with open(BASE_CONFIG_FILE, "r") as f:
    try:
        BASE_CONFIG = yaml.safe_load(f)
    except Exception as e:
        print(e)

if BASE_CONFIG == None:
    print("[ERR] Could not read base config.")
    exit(0)

BASE_CONFIG["Frontend"]["num_expected_insts"] = NUM_EXPECTED_INSTS
if NUM_MAX_CYCLES > 0:
    BASE_CONFIG["Frontend"]["num_max_cycles"] = NUM_MAX_CYCLES 

TRACE_COMBS = {}
TRACE_TYPES = {}
with open(TRACE_COMBINATION_FILE, "r") as f:
    for line in f:
        line = line.strip()
        tokens = line.split(',')
        trace_name = tokens[0]
        trace_type = tokens[1]
        traces = tokens[2:]
        TRACE_COMBS[trace_name] = traces
        TRACE_TYPES[trace_name] = trace_type

for mitigation in mitigation_list + ["Dummy", "BlockHammer"]:
    for path in [
            f"{RESULT_DIR}/{mitigation}/stats",
            f"{RESULT_DIR}/{mitigation}/errors",
            f"{RESULT_DIR}/{mitigation}/configs",
            f"{RESULT_DIR}/{mitigation}/cmd_count",
            f"{RESULT_DIR}/{mitigation}/mem_latency"
        ]:
        if not os.path.exists(path):
            os.makedirs(path)

def get_singlecore_run_commands():
    run_commands = []
    singlecore_params = get_singlecore_params_list()
    singlecore_traces, _ = get_trace_lists(TRACE_COMBINATION_FILE)
    for config in singlecore_params:
        mitigation, throttle_type, _, tRH, flat_thresh, dynamic_thresh = config
        stat_str = make_stat_str(config[1:])
        for trace in singlecore_traces:
            result_filename = f"{HOST_RESULT_DIR}/{mitigation}/stats/{stat_str}_{trace}.txt"
            error_filename = f"{HOST_RESULT_DIR}/{mitigation}/errors/{stat_str}_{trace}.txt"
            config_filename = f"{RESULT_DIR}/{mitigation}/configs/{stat_str}_{trace}.yaml"
            cmd_count_filename = f"{RESULT_DIR}/{mitigation}/cmd_count/{stat_str}_{trace}.cmd.count"
            latency_dump_filename = f"{RESULT_DIR}/{mitigation}/mem_latency/{stat_str}_{trace}.memlat.dump"
            config = copy.deepcopy(BASE_CONFIG)

            config["Frontend"]["lat_dump_path"] = latency_dump_filename 
            config["MemorySystem"][CONTROLLER]["plugins"][0]["ControllerPlugin"]["path"] = cmd_count_filename
            config["MemorySystem"][CONTROLLER]["RowPolicy"]["cap"] = COLUMN_CAP 
            config["MemorySystem"][CONTROLLER]["plugins"].append({
                "ControllerPlugin": {
                    "impl": "Throttler",
                    "throttle_type": throttle_type,
                    "throttle_flat_thresh": flat_thresh,
                    "throttle_dynamic_thresh": dynamic_thresh,
                    "window_period_ns": 64000000, 
                    "snapshot_clk": -1,
                    "blacklist_max_mshr": 5,
                    "blacklist_mshr_decrement": 1,
                    "breakhammer_plus": True
                }
            })
                
            config["Frontend"]["traces"] = [f"{TRACE_DIR}/{trace}"]

            add_mitigation(config, mitigation, tRH)

            config_file = open(config_filename, "w")
            yaml.dump(config, config_file, default_flow_style=False)
            config_file.close()

            sbatch_filename = f"{WORK_DIR}/run_scripts/{mitigation}_{stat_str}_{trace}.sh"
            podman_sbatch_filename = f"/app/run_scripts/{mitigation}_{stat_str}_{trace}.sh"
            sbatch_file = open(podman_sbatch_filename, "w")
            sbatch_file.write(f"{CMD_HEADER}\n{LOAD_CMD}\npodman run --rm -v $PWD:/app breakhammer_artifact \"{CMD} -f {config_filename}\"\n")
            sbatch_file.close()

            job_name = f"ramulator2"
            sb_cmd = f"{SBATCH_CMD} --chdir={WORK_DIR} --output={result_filename}"
            sb_cmd += f" --error={error_filename} --partition=cpu_part --job-name='{job_name}'"
            sb_cmd += f" {sbatch_filename}"

            run_commands.append(sb_cmd)
    return run_commands

def get_multicore_run_commands():
    run_commands = []
    multicore_params = get_multicore_params_list()
    _, multicore_traces = get_trace_lists(TRACE_COMBINATION_FILE)
    for config in multicore_params:
        mitigation, throttle_type, _, tRH, flat_thresh, dynamic_thresh = config
        stat_str = make_stat_str(config[1:])
        for trace in multicore_traces:
            result_filename = f"{HOST_RESULT_DIR}/{mitigation}/stats/{stat_str}_{trace}.txt"
            error_filename = f"{HOST_RESULT_DIR}/{mitigation}/errors/{stat_str}_{trace}.txt"
            config_filename = f"{RESULT_DIR}/{mitigation}/configs/{stat_str}_{trace}.yaml"
            cmd_count_filename = f"{RESULT_DIR}/{mitigation}/cmd_count/{stat_str}_{trace}.cmd.count"
            latency_dump_filename = f"{RESULT_DIR}/{mitigation}/mem_latency/{stat_str}_{trace}.memlat.dump"
            config = copy.deepcopy(BASE_CONFIG)

            config["Frontend"]["lat_dump_path"] = latency_dump_filename 
            config["MemorySystem"][CONTROLLER]["plugins"][0]["ControllerPlugin"]["path"] = cmd_count_filename
            config["MemorySystem"][CONTROLLER]["RowPolicy"]["cap"] = COLUMN_CAP 
            config["MemorySystem"][CONTROLLER]["plugins"].append({
                "ControllerPlugin": {
                    "impl": "Throttler",
                    "throttle_type": throttle_type,
                    "throttle_flat_thresh": flat_thresh,
                    "throttle_dynamic_thresh": dynamic_thresh,
                    "window_period_ns": 64000000, 
                    "snapshot_clk": -1,
                    "blacklist_max_mshr": 5,
                    "blacklist_mshr_decrement": 1,
                    "breakhammer_plus": True
                }
            })

            trace_comb = TRACE_COMBS[trace]
            trace_type = TRACE_TYPES[trace]
            traces = []
            no_wait_traces = []
            for idx in range(len(trace_type)):
                cur_type = trace_type[idx]
                cur_trace = f"{TRACE_DIR}/{trace_comb[idx]}"
                if cur_type != "A":
                    traces.append(cur_trace)
                else:
                    no_wait_traces.append(cur_trace)
                
            config["Frontend"]["traces"] = traces
            if len(no_wait_traces) > 0:
                config["Frontend"]["no_wait_traces"] = no_wait_traces

            add_mitigation(config, mitigation, tRH)

            config_file = open(config_filename, "w")
            yaml.dump(config, config_file, default_flow_style=False)
            config_file.close()

            sbatch_filename = f"{WORK_DIR}/run_scripts/{mitigation}_{stat_str}_{trace}.sh"
            podman_sbatch_filename = f"/app/run_scripts/{mitigation}_{stat_str}_{trace}.sh"
            sbatch_file = open(podman_sbatch_filename, "w")
            sbatch_file.write(f"{CMD_HEADER}\n{LOAD_CMD}\npodman run --rm -v $PWD:/app breakhammer_artifact \"{CMD} -f {config_filename}\"\n")
            sbatch_file.close()

            job_name = f"ramulator2"
            sb_cmd = f"{SBATCH_CMD} --chdir={WORK_DIR} --output={result_filename}"
            sb_cmd += f" --error={error_filename} --partition=cpu_part --job-name='{job_name}'"
            sb_cmd += f" {sbatch_filename}"

            run_commands.append(sb_cmd)
    return run_commands

os.system(f"rm -r /app/run_scripts")
os.system(f"mkdir -p /app/run_scripts")

single_cmds = get_singlecore_run_commands()
multi_cmds = get_multicore_run_commands()

with open("run.sh", "w") as f:
    f.write(f"{CMD_HEADER}\n")
    for cmd in single_cmds + multi_cmds:
        f.write(f"{cmd}\n")
    
os.system("chmod uog+x run.sh")