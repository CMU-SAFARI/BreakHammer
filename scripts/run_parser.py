import os
import sys
import pandas as pd

from . import result_parser as parser
from . import mem_parser
from .run_config import *

SBATCH_CMD = "sbatch --exclude=kratos10,kratos17,kratos18,kratos19 --cpus-per-task=1 --nodes=1 --ntasks=1"

PRINT_ERROR = False
PRINT_MISSING = False
PRINT_RUNNING = False

def dump_runs(work_dir, result_dir, missing_runs, filename):
    if not os.path.exists(f"{work_dir}/rerun_scripts"):
        os.makedirs(f"{work_dir}/rerun_scripts")
    slurm_filename = f"{work_dir}/rerun_scripts/{filename}_slurm.sh"
    with open(slurm_filename, "w") as f:
        f.write("#! /bin/bash\n")
        for mitigation, stat_str, trace in missing_runs:
            sbatch_filename = f"{work_dir}/run_scripts/{mitigation}_{stat_str}_{trace}.sh"
            result_filename = f"{result_dir}/{mitigation}/stats/{stat_str}_{trace}.txt"
            error_filename = f"{result_dir}/{mitigation}/errors/{stat_str}_{trace}.txt"

            job_name = f"ramulator2"
            sb_cmd = f"{SBATCH_CMD} --chdir={work_dir} --output={result_filename}"
            sb_cmd += f" --error={error_filename} --partition=cpu_part --job-name='{job_name}'"
            sb_cmd += f" {sbatch_filename}"
            f.write(f"{sb_cmd}\n")

    personal_filename = f"{work_dir}/rerun_scripts/{filename}_personal.sh"
    with open(personal_filename, "w") as f:
        f.write("#! /bin/bash\n")
        for mitigation, stat_str, trace in missing_runs:
            config_filename = f"{result_dir}/{mitigation}/configs/{stat_str}_{trace}.yaml"
            result_filename = f"{result_dir}/{mitigation}/stats/{stat_str}_{trace}.txt"
            f.write(f"echo \"[INFO] Running configuration '{config_filename}' with output at '{result_filename}'\"\n")
            f.write(f"{work_dir}/ramulator2 -f {config_filename} > {result_filename} 2>&1\n")

    os.system(f"chmod uog+x {slurm_filename}")
    os.system(f"chmod uog+x {personal_filename}")

def check_runs(work_dir, result_dir, csv_dir, trace_name_list, num_cores, name_prefix, mix_name, parse_results):
    running = 0
    missing = 0
    error = 0
    done = 0
    num_configs = len(trace_name_list) *\
        len(get_singlecore_params_list() if "single" in name_prefix else get_multicore_params_list())
    stat_expected_size = num_configs 
    df_index = 0
    df = pd.DataFrame(index=range(stat_expected_size), columns=PARAM_STR_LIST + ["trace"] + [f"ipc_{i}" for i in range(num_cores)] +\
                        ["VRR", "RFM", "RRS_reswap", "RRS_unswap", "RRS_swap",\
                        "AQUA_migrate", "AQUA_r_migrate"] + ["total_energy"] +\
                        [f"insn_{i}" for i in range(num_cores)])
    mem_expected_size = 101 * 4 * num_configs
    mem_df_index = 0
    mem_df = pd.DataFrame(index = range(mem_expected_size), columns = PARAM_STR_LIST + ["trace", "core_id", "pN_key", "pN_val"])
    error_runs = []
    missing_runs = []
    for trace_name in trace_name_list:
        params_list = get_singlecore_params_list() if "single" in name_prefix else get_multicore_params_list()
        for item in params_list:
            item = list(item)
            stat_str = make_stat_str(item[1:])
            result_file = f"{result_dir}/{item[0]}/stats/{stat_str}_{trace_name}.txt"
            error_file = f"{result_dir}/{item[0]}/errors/{stat_str}_{trace_name}.txt"
            cmd_count_file = f"{result_dir}/{item[0]}/cmd_count/{stat_str}_{trace_name}.cmd.count"
            mem_latency_file = f"{result_dir}/{item[0]}/mem_latency/{make_stat_str(item[1:])}_{trace_name}.memlat.dump"
            core_stat, global_stat = parser.parse(result_file, error_file)
            if global_stat["prog_stat"] == "ERROR":
                error += 1
                error_runs.append((item[0], stat_str, trace_name))
                continue 
            if global_stat["prog_stat"] == "MISSING":
                missing += 1
                missing_runs.append((item[0], stat_str, trace_name))
                continue 
            if global_stat["prog_stat"] == "RUNNING":
                running += 1
                continue
            done += 1
            if not parse_results:
                continue
            for i in range(num_cores):
                mem_hist = mem_parser.get_mem_hist(f"{mem_latency_file}.core{i}")
                if len(mem_hist) == 0:
                    for pN in range(101):
                        mem_df.iloc[mem_df_index] = item + [trace_name, i, pN, 0]
                        mem_df_index += 1
                    continue
                _, total_reqs = mem_hist[-1]
                n_percentile = 0
                pN_step = total_reqs / 100
                for bucket, running_sum in mem_hist:
                    while running_sum >= (pN_step * n_percentile):
                        mem_df.iloc[mem_df_index] = item + [trace_name, i, n_percentile, bucket + MEM_HIST_PREC - 1]
                        n_percentile += 1
                        mem_df_index += 1
            num_commands = parser.parse_command_count(cmd_count_file)
            item += [trace_name]
            item += [parser.metric_ipc(core_stat[core_id]) for core_id in range(num_cores)]
            item += [num_commands["VRR"], global_stat["RFM"], global_stat["RRS_reswap"],\
                        global_stat["RRS_unswap"], global_stat["RRS_swap"], global_stat["AQUA_migrate"],
                        global_stat["AQUA_r_migrate"]]
            item += [global_stat["total_energy"]]
            item += [core_stat[core_id]["ins"] for core_id in range(num_cores)]
            df.iloc[df_index] =  item 
            df_index += 1
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    print(f" >Done   : {done}\n >Running: {running}\n >Error  : {error}\n >Missing: {missing}")
    if len(error_runs) > 0:
        dump_runs(work_dir, result_dir, error_runs, f"{mix_name}_{name_prefix}_error")
        print(f"[INFO] You can rerun simulations with errors using scripts at: {work_dir}/rerun_scripts")
    if len(missing_runs) > 0:
        dump_runs(work_dir, result_dir, missing_runs, f"{mix_name}_{name_prefix}_missing")
        print(f"[INFO] You can rerun missing simulations using scripts at: {work_dir}/rerun_scripts" +\
                " (if you are using slurm make sure these runs are not waiting for resources)")
    if not parse_results:
        return
    mem_df = mem_df[:mem_df_index]
    df = df[:df_index]
    df.to_csv(f"{csv_dir}/{name_prefix}.csv", index=False)
    mem_df.to_csv(f"{csv_dir}/{name_prefix}_mem.csv", index=False)

def parse_runs(work_dir, result_dir, csv_dir, trace_path, num_cores, parse_results):
    singlecore_trace_list, multicore_trace_list = get_trace_lists(trace_path)
    mix_name = trace_path[trace_path.rindex("/")+1:trace_path.rindex(".mix")]
    action_str = "Parsing" if parse_results else "Checking"
    caution_str = " (This might take a while, e.g., >5 mins)" if parse_results else ""
    print(f"[INFO] {action_str} {mix_name} multicore runs{caution_str}")
    check_runs(work_dir, result_dir, csv_dir, multicore_trace_list, num_cores, "multicore", mix_name, parse_results)
    print(f"[INFO] {action_str} {mix_name} singlecore runs")
    check_runs(work_dir, result_dir, csv_dir, singlecore_trace_list, 1, "singlecore", mix_name, parse_results)

if __name__ == "__main__":
    work_dir = sys.argv[1]
    trace_path = sys.argv[2]
    result_dir = sys.argv[3]
    num_benign_cores = int(sys.argv[4])
    csv_dir = f"{result_dir}/_csvs"
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    parse_runs(work_dir, result_dir, csv_dir, trace_path, num_benign_cores, False)