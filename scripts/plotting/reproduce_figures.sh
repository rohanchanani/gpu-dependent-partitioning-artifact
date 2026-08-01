#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/plot_microbenchmarks.py"
python3 "$SCRIPT_DIR/plot_weak_scaling.py"
python3 "$SCRIPT_DIR/plot_repartitioning.py"
