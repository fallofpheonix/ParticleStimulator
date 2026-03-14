#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
TARGET_PATH="${SCRIPT_DIR}/HIGGS.csv.gz"

echo "Downloading HIGGS.csv.gz from UCI Machine Learning Repository..."
curl -L -o "${TARGET_PATH}" https://archive.ics.uci.edu/ml/machine-learning-databases/00280/HIGGS.csv.gz

echo "Download complete: ${TARGET_PATH}"
echo "Compressed files are supported directly by the training pipeline."
