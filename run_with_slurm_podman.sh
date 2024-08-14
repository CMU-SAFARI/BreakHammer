#! /bin/bash

echo "[INFO] Generating Ramulator2 configurations and run scripts for attacker workloads"
podman run --rm -v $PWD:/app breakhammer_artifact "python3 setup_slurm_podman.py \
    --working_directory $PWD \
    --base_config /app/base_config.yaml \
    --trace_combination /app/mixes/microattack.mix \
    --trace_directory /app/cputraces \
    --result_directory /app/ae_results/microattack"

echo "[INFO] Starting Ramulator2 attacker simulations"
sh "$PWD/run.sh" 

# echo "[INFO] Generating Ramulator2 configurations and run scripts for benign workloads"
# podman run --rm -v $PWD:/app breakhammer_artifact "python3 setup_slurm_podman.py \
#     --working_directory $PWD \
#     --base_config /app/base_config.yaml \
#     --trace_combination /app/mixes/microbenign.mix \
#     --trace_directory /app/cputraces \
#     --result_directory $PWD/ae_results/microbenign"

# echo "[INFO] Starting Ramulator2 benign simulations"
# sh "$PWD/run.sh" 

echo "[INFO] You can track run status with the <check_run_status.sh> script"
# rm "$PWD/run.sh" 