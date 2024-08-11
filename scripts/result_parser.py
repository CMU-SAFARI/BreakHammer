import os
import sys

from .run_config import *

def no_op_parser(val):
    return val

def int_parser(val):
    return int(val.strip())

def strip_parser(val):
    return val.strip()

def float_parser(val):
    return float(val.strip())

global_tokens = {
    "controller_num_row_conflicts": { "key_name": "rowconf", "def_val": 0, "parser": int_parser },
    "controller_num_row_misses": { "key_name": "rowmiss", "def_val": 0, "parser": int_parser },
    "controller_num_row_hits": { "key_name": "rowhit", "def_val": 0, "parser": int_parser },
    "rfm_counter": { "key_name": "RFM", "def_val": 0, "parser": int_parser },
    "aqua_migrations": { "key_name": "AQUA_migrate", "def_val": 0, "parser": int_parser },
    "aqua_r_migrations": { "key_name": "AQUA_r_migrate", "def_val": 0, "parser": int_parser },
    "rss_num_reswaps": { "key_name": "RRS_reswap", "def_val": 0, "parser": int_parser },
    "rss_num_unswaps": { "key_name": "RRS_unswap", "def_val": 0, "parser": int_parser },
    "rss_num_swaps": { "key_name": "RRS_swap", "def_val": 0, "parser": int_parser },
    "total_energy": { "key_name": "total_energy", "def_val": 0, "parser": float_parser },
    "prac_num_recovery": { "key_name": "prac_recovery", "def_val": 0, "parser": int_parser }
}

per_core_tokens = {
    "controller_core_row_hits_": { "key_name": "rowhit", "def_val": 0, "parser": int_parser },
    "controller_core_row_misses_": { "key_name": "rowmiss", "def_val": 0, "parser": int_parser },
    "controller_core_row_conflicts_": { "key_name": "rowconf", "def_val": 0, "parser": int_parser },
    "insts_recorded_core_": { "key_name": "ins", "def_val": 0, "parser": int_parser },
    "cycles_recorded_core_": { "key_name": "cyc", "def_val": 0, "parser": int_parser },
    "throttler_throttle_count_core_": { "key_name": "num_throttled", "def_val": 0, "parser": int_parser },
    "name_trace_": { "key_name": "name", "def_val": "null", "parser": strip_parser }
}

base_dict = {}
for starter_token in per_core_tokens:
    obj = per_core_tokens[starter_token]
    base_dict[obj["key_name"]] = obj["def_val"]

def process_line(line, per_core_data, global_data):
    processed_line = line.lstrip()
    for stat_token in per_core_tokens:
        if processed_line.startswith(stat_token):
            stat_obj = per_core_tokens[stat_token]
            line_tokens = processed_line.replace(" ", "").split(":")
            dict_key = int(line_tokens[0].replace(stat_token, ""))
            if dict_key not in per_core_data:
                per_core_data[dict_key] = base_dict.copy()
            per_core_data[dict_key][stat_obj["key_name"]] = stat_obj["parser"](line_tokens[1])
            return

    for stat_token in global_tokens:
        if processed_line.startswith(stat_token):
            stat_obj = global_tokens[stat_token]
            line_tokens = processed_line.replace(" ", "").split(":")
            global_data[stat_obj["key_name"]] = stat_obj["parser"](line_tokens[1])
            return

def parse(result_filename, error_filename):
    per_core_data = {}
    global_data = {}
    for starter_token in global_tokens:
        obj = global_tokens[starter_token]
        global_data[obj["key_name"]] = obj["def_val"]
    status = "RUNNING"
    if not os.path.exists(result_filename):
        global_data["prog_stat"] = "MISSING"
        return per_core_data, global_data
    if os.path.exists(error_filename):
        with open(error_filename, "r", encoding="utf-8") as f:
            if len(f.readlines()) > 1:
                global_data["prog_stat"] = "ERROR"
                return per_core_data, global_data
    with open(result_filename, "r", encoding="utf-8") as f:
        for line in f:
            if "CommandCounter" in line:
                status = "DONE"
            process_line(line, per_core_data, global_data)
    global_data["prog_stat"] = status
    return per_core_data, global_data 

def parse_command_count(file):
    commands = { "VRR": 0 }
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            tokens = line.split(",")
            cmd_name = tokens[0].strip()
            cmd_count = tokens[1].lstrip().rstrip()
            commands[cmd_name] = int(cmd_count)
    return commands

def metric_ipc(data):
    return data['ins'] / data['cyc']

def metric_total_row_stat(data):
    return data['rowhit'] + data['rowmiss'] + data['rowconf']

def metric_rowhit_rate(data):
    return data['rowhit'] / metric_total_row_stat(data)