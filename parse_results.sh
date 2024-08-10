#!/usr/bin/bash

echo "[INFO] Parsing attacker simulation results"
python3 -m scripts.run_processor "$PWD" "$PWD/mixes/microattack.mix" "$PWD/ae_results/microattack" 3

echo "[INFO] Parsing benign simulation results"
python3 -m scripts.run_processor "$PWD" "$PWD/mixes/microbenign.mix" "$PWD/ae_results/microbenign" 4