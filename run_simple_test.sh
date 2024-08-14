#! /bin/bash

echo "[INFO] Installing Python dependencies"
pip3 install -r requirements.txt

echo "[INFO] Building Ramulator2"
sh "./build.sh"

if [ "$(ls -A cputraces/)" ]; then
  echo "[INFO] cputraces/ directory is not empty. Skipping download"
else
  echo "[INFO] cputraces/ directory is empty"
  echo "[INFO] Downloading the traces into ./cputraces"
  python3 /app/download_traces.py
  echo "[INFO] Decompressing the traces into ./cputraces"
  tar -xvf cputraces.tar.gz --no-same-owner
fi

echo "[INFO] Running the simple test simulation"
./ramulator2 -f base_config.yaml

rm ./test.cmds1