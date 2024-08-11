#! /bin/bash

PLOT_ID=$1

echo "[INFO] Generating Figure$1"
python3 plotting_scripts/figure$1.py \
    --working_directory "$PWD" \
    --trace_combination "$PWD/mixes/" \
    --trace_directory "$PWD/cputraces" \
    --result_directory "$PWD/ae_results/"

echo "[INFO] Figure$1 generated to '$PWD/plots/figure$1.pdf'"