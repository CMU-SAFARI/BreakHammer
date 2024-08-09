import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from . import result_parser as parser
from .run_config import *

PRINT_ERROR = False
PRINT_MISSING = False
PRINT_RUNNING = False

def get_parameter_results(result_dir, csv_dir, trace_name_list, num_cores, name_prefix, ignore_partial = True):
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
    rerun_df = pd.DataFrame(columns = PARAM_STR_LIST + ["trace"])
    for trace_name in trace_name_list:
        params_list = get_singlecore_params_list() if "single" in name_prefix else get_multicore_params_list()
        for item in params_list:
            item = list(item)
            result_file = f"{result_dir}/{item[0]}/stats/{make_stat_str(item[1:])}_{trace_name}.txt"
            error_file = f"{result_dir}/{item[0]}/errors/{make_stat_str(item[1:])}_{trace_name}.txt"
            cmd_count_file = f"{result_dir}/{item[0]}/cmd_count/{make_stat_str(item[1:])}_{trace_name}.cmd.count"
            core_stat, global_stat = parser.parse(result_file, error_file)
            if global_stat["prog_stat"] == "ERROR":
                if PRINT_ERROR:
                    print(result_file)
                rerun_df.loc[len(rerun_df)] = item + [trace_name]
                error += 1
                continue 
            if global_stat["prog_stat"] == "MISSING":
                if PRINT_MISSING:
                    print(result_file)
                rerun_df.loc[len(rerun_df)] = item + [trace_name]
                missing += 1
                continue 
            if global_stat["prog_stat"] == "RUNNING":
                if PRINT_RUNNING:
                    print(result_file)
                running += 1
                continue # Skip this guy
            done += 1
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
    print(f"D: {done} R: {running} E: {error} M: {missing}")
    success = (running + error + missing) == 0
    mem_df = mem_df[:mem_df_index]
    df = df[:df_index]
    if success or not ignore_partial:
        df.to_csv(f"{csv_dir}/{name_prefix}.csv", index=False)
        mem_df.to_csv(f"{csv_dir}/{name_prefix}_mem.csv", index=False)
    return success

def parse_parameter_runs(result_dir, csv_dir, trace_path, num_cores, ignore_partial=True):
    singlecore_trace_list, multicore_trace_list = get_trace_lists(trace_path)
    print("Parsing Multicore Runs")
    done_multi = get_parameter_results(result_dir, csv_dir, multicore_trace_list, num_cores, "multicore", ignore_partial)
    print("Parsing Singlecore Runs")
    done_single = get_parameter_results(result_dir, csv_dir, singlecore_trace_list, 1, "singlecore", ignore_partial)
    return (not ignore_partial) or (done_multi and done_single)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        en_str = sys.argv[1].lower()
        if "e" in en_str:
            PRINT_ERROR = True
        if "m" in en_str:
            PRINT_MISSING = True
        if "r" in en_str:
            PRINT_RUNNING = True
    work_dir = "/mnt/panzer/ocanpolat/breakhammer"
    trace_path = f"{work_dir}/mixes/microattack.mix"
    result_dir = f"{work_dir}/ae_results/microattack"
    csv_dir = f"{result_dir}/_csvs"
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    parse_parameter_runs(result_dir, csv_dir, trace_path, 4)