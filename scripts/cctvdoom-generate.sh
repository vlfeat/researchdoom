#!/usr/bin/env bash
set -eu

PYTHON="python/.venv/bin/python3"
PYTHONPATH="python"
DATA_RAW="/tmp/cctvdoom-raw"
DATASETS=("cctvdoom_run1") # Add more runs here

# Generate the CCTV-Doom raw exports for the configured datasets.
for dataset in "${DATASETS[@]}"; do
	if test -e "${DATA_RAW}/${dataset}/.done"; then continue; fi

	PYTHONPATH="$PYTHONPATH" "$PYTHON" -m rdm.rdm \
		output_dir="$DATA_RAW" \
		dataset="$dataset"

	touch "${DATA_RAW}/${dataset}/.done"
done
