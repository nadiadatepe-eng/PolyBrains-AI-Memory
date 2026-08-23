#!/usr/bin/env bash
# P14 (E-null): is unanimity about truth, or about coordination?
#
# Pre-registered in PREDICTIONS.md before the model was pretrained. Reasoning in
# reports/reconsideration-consensus.md.
#
# THE CONDITION THIS CREATES: `dice` is absent from the pretrained model's graph
# memory (verified directly in model.pt, not merely in the config), so every
# module must answer and none can be right. That is Nadi's four-wrong-answers
# scenario, implemented.
#
# 4 eval rotations, so n_eval_epochs=4 is REQUIRED: Predefined indexes the
# rotation list by EPOCH, not episode. Two sweeps in this project were voided by
# exactly this, and the episode count is asserted below.
#
# The run directory is cleared first: Monty APPENDS to an existing
# eval_stats.csv, so an aborted launch leaves rows the rerun adds to (P11).
#
# `run.py -cd -cn` is the invocation, NOT `python -m ...frameworks.run`, which
# exits 0 having done nothing at all. That cost a cycle here on 2026-08-20.
# `wandb_id` must be set explicitly or hydra fails resolving wandb.util.
set -u
MONTY="$HOME/PolyBrains/upstream/tbp.monty"
export MONTY_DATA=~/tbp/data MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty PYTHONPATH=~/PolyBrains/src
ARMS=(p14_holdout_max p14_holdout_novote p14_trained_max)
SEEDS=(42 43 44 45 46)
EPOCHS=4          # one per eval rotation
EXPECT=4          # 1 object x 4 rotations
cd "$MONTY" || exit 1

total=$(( ${#ARMS[@]} * ${#SEEDS[@]} )); i=0; fail=0
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    i=$((i+1)); run="${arm}_s${seed}"
    rm -rf "$MONTY_LOGS/projects/monty_runs/$run"
    echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"$arm seed $seed\"}"
    start=$(date +%s)
    timeout 3600 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
        "experiment=$arm" \
        '++experiment.config.logging.wandb_id=p14' \
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
echo "JCODE_CHECKPOINT {\"message\":\"P14 sweep finished, $fail failures\"}"
echo "failures: $fail"
