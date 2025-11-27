#!/bin/sh
set -eu

ENGINE="engines/chocolate"
DATA="/tmp/cocodoom"
DATA_RAW="/tmp/cocodoom-raw"
PYTHONPATH="python"

# Generate raw ResearchDoom exports for the six cocodoom dataset configs
(
  set -ex
  for run in 1 2 3 4 5; do
    if test -e "${DATA_RAW}/cocodoom_run${run}/.done"; then continue; fi
    PYTHONPATH="$PYTHONPATH" python3 -m rdm.rdm \
      engine.path="$ENGINE" \
      output_dir="$DATA_RAW" \
      dataset="cocodoom_run${run}"
    touch "${DATA_RAW}/cocodoom_run${run}/.done"
  done
)

# Convert each raw run to the CocoDoom format
mkdir -p "$DATA"
for run in 1 2 3; do
  PYTHONPATH="$PYTHONPATH" python3 -m rdm.cocodoom_make \
    "${DATA_RAW}/cocodoom_run${run}" \
    "$DATA" \
    --run-id "$run" \
    --run-name "run${run}"
done

# Merge all maps within each run into one COCO JSON per run
for run in 1 2 3; do
  PYTHONPATH="$PYTHONPATH" python3 -m rdm.cocodoom_combine \
    $DATA/run${run}/map*/coco.json \
    "$DATA/run${run}.json"
done

# Generate the standard train/val/test split files
PYTHONPATH="$PYTHONPATH" python3 -m rdm.cocodoom_split \
  --data-dir "$DATA"

# Optional QA: print split/run stats for any standard split files that exist
PYTHONPATH="$PYTHONPATH" python3 -m rdm.cocodoom_test \
  --data-path "$DATA" || true

# Optional QA: build a gallery from one merged run annotation file
PYTHONPATH="$PYTHONPATH" python3 -m rdm.cocodoom_gallery \
  --coco-path "$DATA/run1.json" \
  --data-path "$DATA" \
  --output-path "$DATA/cocodoom-gallery.png" || true