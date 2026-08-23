#!/usr/bin/env bash
# P15: four held-out objects. Is the attractor coordination or a shared prior?
#
# Pre-registered in PREDICTIONS.md before the six-object model was pretrained.
# Follows reports/p14-enull.md, which found 90% unanimity on ONE impossible
# target with 83% present without voting at all.
#
# `dice`, `banana`, `mug` and `strawberry` are absent from the model's graph
# memory -- verified in model.pt, not merely in the config. Nine arms:
# 4 objects x {max, novote} + the trained-object control.
#
# 4 eval rotations, so n_eval_epochs=4 is REQUIRED: Predefined indexes the
# rotation list by EPOCH. Run dirs cleared first (Monty APPENDS). Episode count
# asserted after.
#
# `run.py -cd -cn`, NOT `python -m ...frameworks.run`, which exits 0 having done
# nothing. `wandb_id` must be set explicitly or hydra fails on wandb.util.
#
# Seed 42 is EXPECTED to fail on some objects: upstream's
# surface_normal_total_least_squares asserts its eigendecomposition is real and
# on some viewpoints it is not (sensor_processing.py:444). It fails identically
# on both arms of an object, so it is neutral for the max-vs-novote contrast.
set -u
MONTY="$HOME/PolyBrains/upstream/tbp.monty"
export MONTY_DATA=~/tbp/data MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty PYTHONPATH=~/PolyBrains/src
OBJECTS=(dice banana mug strawberry)
SEEDS=(42 43 44 45 46)
EPOCHS=4
EXPECT=4
cd "$MONTY" || exit 1

ARMS=()
for o in "${OBJECTS[@]}"; do ARMS+=("p15_${o}_max" "p15_${o}_novote"); done
ARMS+=("p15_trained_max")

total=$(( ${#ARMS[@]} * ${#SEEDS[@]} )); i=0; fail=0
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    i=$((i+1)); run="${arm}_s${seed}"
    rm -rf "$MONTY_LOGS/projects/monty_runs/$run"
    echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"$arm seed $seed\"}"
    start=$(date +%s)
    timeout 3600 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
        "experiment=$arm" \
        '++experiment.config.logging.wandb_id=p15' \
        "++experiment.config.seed=$seed" \
        "++experiment.config.n_eval_epochs=$EPOCHS" \
        "++experiment.config.logging.run_name=$run" >/dev/null 2>&1
    rc=$?
    [ $rc -ne 0 ] && { echo "  FAILED: $run (rc=$rc)"; fail=$((fail+1)); }
    csv="$MONTY_LOGS/projects/monty_runs/$run/eval_stats.csv"
    eps=$(( ($(wc -l < "$csv" 2>/dev/null || echo 1) - 1) / 5 ))
    [ "$eps" -ne "$EXPECT" ] && { echo "  WARNING $run: $eps episodes, expected $EXPECT"; fail=$((fail+1)); }
    echo "  $run done in $(( $(date +%s) - start ))s, $eps episodes"
  done
done
echo "JCODE_CHECKPOINT {\"message\":\"P15 sweep finished, $fail failures\"}"
echo "failures: $fail"
