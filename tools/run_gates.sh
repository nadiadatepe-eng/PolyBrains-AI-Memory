#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/measure_m2_recall.py
test "$(python3 tools/measure_m2_recall.py --json)" = "$(cat reports/cp-r1-v01-result.json)"
python3 tools/measure_r3_replication.py >/dev/null
