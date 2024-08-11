#! /bin/bash

echo "[INFO] Checking attacker simulations"
python3 -m scripts.run_parser "$PWD" "$PWD/mixes/microattack.mix" "$PWD/ae_results/microattack" 3

echo "[INFO] Checking benign simulations"
python3 -m scripts.run_parser "$PWD" "$PWD/mixes/microbenign.mix" "$PWD/ae_results/microbenign" 4