#! /usr/bin/bash

echo "[INFO] Generating figures"
python3 plotting_scripts/plot_all.py \
    --working_directory "$PWD" \
    --trace_combination "$PWD/mixes" \
    --trace_directory "$PWD/cputraces" \
    --result_directory "$PWD/ae_results"

echo "[INFO] Generated figures to '$PWD/plots/'"