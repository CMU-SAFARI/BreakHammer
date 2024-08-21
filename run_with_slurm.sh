#! /bin/bash

AE_SLURM_PART_NAME="cpu_part"

echo "[INFO] Generating Ramulator2 configurations and run scripts for attacker workloads"
python3 setup_slurm.py \
    --working_directory "$PWD" \
    --base_config "$PWD/base_config.yaml" \
    --trace_combination "$PWD/mixes/microattack.mix" \
    --trace_directory "$PWD/cputraces" \
    --result_directory "$PWD/ae_results/microattack" \
    --partition_name "$AE_SLURM_PART_NAME"

echo "[INFO] Starting Ramulator2 attacker simulations"
python3 execute_run_script.py --slurm

echo "[INFO] Generating Ramulator2 configurations and run scripts for benign workloads"
python3 setup_slurm.py \
    --working_directory "$PWD" \
    --base_config "$PWD/base_config.yaml" \
    --trace_combination "$PWD/mixes/microbenign.mix" \
    --trace_directory "$PWD/cputraces" \
    --result_directory "$PWD/ae_results/microbenign" \
    --partition_name "$AE_SLURM_PART_NAME"

echo "[INFO] Starting Ramulator2 benign simulations"
python3 execute_run_script.py --slurm

echo "[INFO] You can track run status with the <check_run_status.sh> script"
rm "$PWD/run.sh" 