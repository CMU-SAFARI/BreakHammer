#! /bin/bash

echo "[INFO] Building Ramulator2"
sh "./build.sh"

echo "[INFO] Generating Ramulator2 configurations and run scripts for attacker workloads (This might take a while, e.g., >3 mins)"
python3 setup_personalcomputer.py \
    --working_directory "$PWD" \
    --base_config "$PWD/base_config.yaml" \
    --trace_combination "$PWD/mixes/microattack.mix" \
    --trace_directory "$PWD/cputraces" \
    --result_directory "$PWD/ae_results/microattack"

echo "[INFO] Starting Ramulator2 attacker simulations"
sh "$PWD/run.sh" 

echo "[INFO] Generating Ramulator2 configurations and run scripts for benign workloads (This might take a while, e.g., >3 mins)"
python3 setup_personalcomputer.py \
    --working_directory "$PWD" \
    --base_config "$PWD/base_config.yaml" \
    --trace_combination "$PWD/mixes/microbenign.mix" \
    --trace_directory "$PWD/cputraces" \
    --result_directory "$PWD/ae_results/microbenign"

echo "[INFO] Starting Ramulator2 benign simulations"
sh "$PWD/run.sh" 

echo "[INFO] You can track run status with the <check_run_status.sh> script"