#!/usr/bin/bash

WORKLOAD=""
N_BENIGN_CORES=0

if [ "$#" -ne 1 ]; then
    echo "Usage: check_run_status.sh <type> (i.e., attack or benign)"
    exit 1
fi

if [[ "$1" == "attack" ]]; then
    WORKLOAD="microattack"
    N_BENIGN_CORES=3
fi

if [[ "$1" == "benign" ]]; then
    WORKLOAD="microbenign"
    N_BENIGN_CORES=4
fi

if [[ "$WORKLOAD" == "" ]]; then
    echo "Usage: check_run_status.sh <type> (i.e., attack or benign)"
    exit 1
fi

python3 -m scripts.run_processor "$PWD" "$PWD/mixes/$WORKLOAD.mix" "$PWD/ae_results/$WORKLOAD" $N_BENIGN_CORES