import itertools
from .calc_rh_parameters import *


MEM_HIST_PREC = 5
NUM_EXPECTED_INSTS = 100_000_000
NUM_MAX_CYCLES = 100_000_000

CONTROLLER = "BHDRAMController"
SCHEDULER = "BHScheduler"
RFMMANAGER = 2
COLUMN_CAP = 4

mitigation_list = []
tRH_list = []
flat_thresh_list = []
dynamic_thresh_list = []
thresh_type_list = []
cache_only_list = []

mitigation_list = ["AQUA", "Graphene", "Hydra", "PARA", "REGA", "RFM", "TWiCe-Ideal"]
tRH_list = [4096, 2048, 1024, 512, 256, 128, 64]
flat_thresh_list = [32]
dynamic_thresh_list = [0.65]
thresh_type_list = ["MEAN"]
cache_only_list = [False]

params_list = [
    mitigation_list,
    thresh_type_list,
    cache_only_list,
    tRH_list,
    flat_thresh_list,
    dynamic_thresh_list
]

PARAM_STR_LIST = [
    "mitigation",
    "thresh_type",
    "cache_only",
    "tRH",
    "flat_thresh",
    "dynamic_thresh"
]

def get_multicore_params_list():
    params = list(itertools.product(*params_list))
    for cache_only in cache_only_list:
        params.append(("Dummy", "NONE", cache_only, 0, 0, 0.0))
    for mitigation in mitigation_list:
        for tRH in tRH_list:
            params.append((mitigation, "NONE", False, tRH, 0, 0.0))
    for tRH in tRH_list:
        params.append(("BlockHammer", "NONE", False, tRH, 0, 0.0))
    return params

def get_singlecore_params_list():
    return [("Dummy", "NONE", False, 0, 0, 0.0)]

def get_trace_lists(trace_combination_file):
    trace_comb_line_count = 0
    multicore_trace_list = set()
    singlecore_trace_list = set()
    with open(trace_combination_file, "r") as f:
        for line in f:
            trace_comb_line_count += 1
            line = line.strip()
            tokens = line.split(',')
            trace_name = tokens[0]
            trace_list = tokens[2:]
            for trace in trace_list:
                singlecore_trace_list.add(trace)
            multicore_trace_list.add(trace_name)
    return singlecore_trace_list, multicore_trace_list

def make_stat_str(param_list, delim="_"):
    return delim.join([str(param) for param in param_list])

def add_mitigation(config, mitigation, tRH):
    if mitigation == "Graphene":
        num_table_entries, activation_threshold, reset_period_ns = get_graphene_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "Graphene",
                "num_table_entries": num_table_entries,
                "activation_threshold": activation_threshold,
                "reset_period_ns": reset_period_ns
        }})
    elif mitigation == "Hydra":
        hydra_tracking_threshold, hydra_group_threshold, hydra_row_group_size, hydra_reset_period_ns, hydra_rcc_num_per_rank, hydra_rcc_policy = get_hydra_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "Hydra",
                "hydra_tracking_threshold": hydra_tracking_threshold,
                "hydra_group_threshold": hydra_group_threshold,
                "hydra_row_group_size": hydra_row_group_size,
                "hydra_reset_period_ns": hydra_reset_period_ns,
                "hydra_rcc_num_per_rank": hydra_rcc_num_per_rank,
                "hydra_rcc_policy": hydra_rcc_policy
        }})
    elif mitigation == "PARA":
        threshold = get_para_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "PARA",
                "threshold": threshold
        }})
    elif mitigation == "RRS":
        num_hrt_entries, num_rit_entries, rss_threshold, reset_period_ns = get_rrs_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "RRS",
                "reset_period_ns": reset_period_ns,
                "rss_threshold": rss_threshold,
                "num_rit_entries": num_rit_entries,
                "num_hrt_entries": num_hrt_entries
        }})
    elif mitigation == "AQUA":
        art_threshold, num_art_entries, num_qrows_per_bank, num_fpt_entries, reset_period_ns = get_aqua_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "AQUA",
                "art_threshold": art_threshold,
                "num_art_entries": num_art_entries,
                "num_qrows_per_bank": num_qrows_per_bank,
                "num_fpt_entries": num_fpt_entries,
                "reset_period_ns": reset_period_ns 
        }})
    elif mitigation == "RFM":
        rfm_thresh = get_rfm_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "ThrottleRFM"
        }})
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "RFMManager",
                "rfm_thresh": rfm_thresh,
                "rfm_plus": False
        }})
    elif mitigation == "RFMplus":
        rfm_thresh = get_rfmplus_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "ThrottleRFM"
        }})
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "RFMManager",
                "rfm_thresh": rfm_thresh,
                "rfm_plus": True
        }})
    elif mitigation == "TWiCe-Ideal":
        twice_rh_threshold, twice_pruning_interval_threshold = get_twice_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "TWiCe-Ideal",
                "twice_rh_threshold": twice_rh_threshold,
                "twice_pruning_interval_threshold": twice_pruning_interval_threshold
        }})
    elif mitigation == "Dummy":
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "DummyMitigation"
        }})
    elif mitigation == "BlockHammer":
        config["MemorySystem"][CONTROLLER][SCHEDULER]["impl"] = "BlockingScheduler"
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "BlockHammerPlugin",
                "bf_num_rh": tRH,
                "bf_ctr_thresh": int(tRH // 4)
        }})
    elif mitigation == "REGA":
        tRAS, V, T = get_rega_parameters(tRH)
        config["MemorySystem"]["DRAM"]["tRAS"] = tRAS
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "ThrottleREGA",
                "V": V,
                "T": T
        }})