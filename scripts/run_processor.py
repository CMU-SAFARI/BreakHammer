import os
import sys
import pandas as pd

from .run_config import *
from .run_parser import parse_runs

def merge_alone_ipcs_dummy(row, sc_df, mixes):
    if row["trace"] in mixes:
        workload_mix = mixes[row["trace"]]
        for core, workload in enumerate(workload_mix):
            matching_row = sc_df[\
                (sc_df.mitigation == "Dummy") &\
                (sc_df.workload == workload)]
            row[f"aipc_{int(core)}"] = matching_row["alone_ipc"].values[0]
        return row

def process_results(csv_dir, trace_path, num_cores):
    sc_df = pd.read_csv(f"{csv_dir}/singlecore.csv")
    sc_df.drop(columns=list(set(sc_df.columns) - set(["mitigation", "thresh_type", "tRH", "flat_thresh", "dynamic_thresh", "trace", "ipc_0"])), inplace=True)
    sc_df["alone_ipc"] = sc_df["ipc_0"]
    sc_df["workload"] = sc_df["trace"]

    mc_df = pd.read_csv(f"{csv_dir}/multicore.csv")

    trace_combination_file = open(trace_path, "r")
    mixes = {}
    types = {}
    for line in trace_combination_file.readlines():
        mix = line.split(",")[0]
        trace_type = line.split(",")[1]
        traces = [t.strip() for t in line.split(",")[2:]]
        mixes[mix] = traces
        types[mix] = trace_type

    mc_df = mc_df.apply(lambda row: merge_alone_ipcs_dummy(row, sc_df, mixes), axis=1)

    # Calculate the shared IPCs
    for core_id in range(num_cores):
        mc_df[f"soa_{core_id}"] = mc_df[f"ipc_{core_id}"] / mc_df[f"aipc_{core_id}"]
        mc_df[f"aos_{core_id}"] = mc_df[f"aipc_{core_id}"] / mc_df[f"ipc_{core_id}"]
    
    # Calculate the multiprogrammed performance metrics
    mc_df["weighted_speedup"] = 0
    mc_df["harmonic_speedup"] = 0
    for core_id in range(num_cores):
        mc_df["weighted_speedup"] += mc_df[f"soa_{core_id}"]
        mc_df["harmonic_speedup"] += mc_df[f"aos_{core_id}"]
    mc_df["harmonic_speedup"] = (num_cores) / mc_df["harmonic_speedup"]
    mc_df["max_slowdown"] = 1 - mc_df[[f"soa_{c}" for c in range(num_cores)]].min(axis=1)
    ins_columns = [f"insn_{core_id}" for core_id in range(num_cores)]
    mc_df["min_insn"] = mc_df[ins_columns].min(axis=1)
    mc_df["total_energy"] = mc_df["total_energy"] * 100_000_000 / mc_df["min_insn"]

    # Normalize the metrics to baseline for each configuration
    cache_only = False
    base_df = mc_df[(mc_df.mitigation == "Dummy") & (mc_df.cache_only == cache_only)].copy()
    base_df = base_df[["trace", "weighted_speedup", "harmonic_speedup", "max_slowdown", "total_energy"]]
    mc_df = mc_df[mc_df.cache_only == False]
    merged_df = mc_df.merge(base_df, on=["trace"], how="left", suffixes=("", "_base"))

    for metric in ["weighted_speedup", "harmonic_speedup", "max_slowdown"]:
        merged_df[f"norm_{metric}"] = merged_df[metric] / merged_df[f"{metric}_base"]
    merged_df["norm_energy"] = merged_df["total_energy"] / merged_df["total_energy_base"]
    merged_df.to_csv(f"{csv_dir}/merged.csv")

if __name__ == "__main__":
    work_dir = sys.argv[1]
    trace_path = sys.argv[2]
    result_dir = sys.argv[3]
    num_benign_cores = int(sys.argv[4])
    csv_dir = f"{result_dir}/_csvs"
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    parse_runs(result_dir, csv_dir, trace_path, num_benign_cores)
    process_results(csv_dir, trace_path, num_benign_cores)