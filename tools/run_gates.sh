#!/usr/bin/env bash
# Run EVERY gate in this project, in the style each one is written in.
#
# Written after P11, where "6/6 gates pass" was claimed from `python tests/X.py`
# exit codes. Four of the six files have NO `__main__` block: run as scripts they
# define their functions, execute zero assertions, print nothing, and exit 0.
# That is the project's own false-coverage failure mode, applied to its gates.
#
#   pytest-style  (assertions collected by pytest): test_consensus,
#                 test_lm_equivalence, test_vote_path, test_weights
#   script-style  (own __main__, print GATE PASSED): test_parliament,
#                 test_iterated_vote
#
# Probes are excluded: they need MuJoCo, data and pretrained models, and take
# minutes. Run those explicitly per experiment.
#
# Usage: bash tools/run_gates.sh
set -u
cd "$(dirname "$0")/.." || exit 1
PY=upstream/tbp.monty/.venv/bin/python
export PYTHONPATH=src   # without this pytest fails at import with ModuleNotFoundError
fail=0

echo "=== pytest-style gates ==="
$PY -m pytest tests/ -q -p no:cacheprovider \
    --ignore=tests/probe_p10_liveness.py \
    --ignore=tests/probe_p9_dead_rounds.py \
    --ignore=tests/probe_p9_liveness.py \
    --ignore=tests/cp1_probe_vote_path.py || fail=$((fail+1))

echo
echo "=== script-style gates ==="
for t in tests/test_parliament.py tests/test_iterated_vote.py tests/test_adaptive_weight.py; do
    # These must PRINT their pass line, not merely exit 0 -- see the header.
    if out=$($PY "$t" 2>&1) && grep -q "GATE PASSED" <<<"$out"; then
        echo "  $(basename "$t"): GATE PASSED"
    else
        echo "  $(basename "$t"): FAILED"
        echo "$out" | tail -5
        fail=$((fail+1))
    fi
done

echo
echo "=== config gates (assert before a sweep runs) ==="
# These gate the sweep itself: P13's caught an arm that was 83% silent, and
# P14's asserts the held-out object is genuinely absent from pretraining.
# The two print DIFFERENT verdict lines -- p13 "GATE PASSED", p14
# "N/N checks passed" -- so each is matched against its own string. Accepting
# either for both would let a file pass while printing no verdict at all.
for t in tests/test_p13_configs.py; do
    if out=$($PY "$t" 2>&1) && grep -q "GATE PASSED" <<<"$out"; then
        echo "  $(basename "$t"): GATE PASSED"
    else
        echo "  $(basename "$t"): FAILED"
        echo "$out" | tail -6
        fail=$((fail+1))
    fi
done
for t in tests/test_p14_configs.py tests/test_p15_configs.py; do
    if out=$($PY "$t" 2>&1) && grep -qE "[0-9]+/[0-9]+ checks passed" <<<"$out"; then
        echo "  $(basename "$t"): $(grep -oE '[0-9]+/[0-9]+ checks passed' <<<"$out")"
    else
        echo "  $(basename "$t"): FAILED"
        echo "$out" | tail -6
        fail=$((fail+1))
    fi
done

echo
echo "=== analyser validators ==="
for t in tests/test_analyse_p12.py; do
    if out=$($PY "$t" 2>&1) && grep -q "VALIDATED" <<<"$out"; then
        echo "  $(basename "$t"): VALIDATED"
    else
        echo "  $(basename "$t"): FAILED"
        echo "$out" | tail -6
        fail=$((fail+1))
    fi
done

# P14's validator reports "N/N checks passed" rather than VALIDATED. Checked
# for its own string rather than loosening the loop above, which would let a
# p12-style validator pass without printing its verdict.
for t in tests/test_analyse_p14.py; do
    if out=$($PY "$t" 2>&1) && grep -qE "[0-9]+/[0-9]+ checks passed" <<<"$out"; then
        echo "  $(basename "$t"): $(grep -oE '[0-9]+/[0-9]+ checks passed' <<<"$out")"
    else
        echo "  $(basename "$t"): FAILED"
        echo "$out" | tail -6
        fail=$((fail+1))
    fi
done

echo
[ "$fail" -eq 0 ] && echo "ALL GATES PASS" || echo "GATE FAILURES: $fail"
exit "$fail"
