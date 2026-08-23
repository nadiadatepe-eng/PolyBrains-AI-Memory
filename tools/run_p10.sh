#!/usr/bin/env bash
# P10: parliamentary voting -- 3 arms x 5 seeds x 40 episodes.
# The 4th arm (plain-3) is P9's rounds=3, already run: the equal-exchange control.
#
# n_eval_epochs=4 is REQUIRED: Predefined indexes rotations by EPOCH, so 1 epoch
# silently evaluates 1 of 4 OOD rotations. See tools/run_p9.sh.
set -u
MONTY="$HOME/PolyBrains/upstream/tbp.monty"
export MONTY_DATA=~/tbp/data MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty PYTHONPATH=~/PolyBrains/src
ARMS=(p10_parl3 p10_parlnoopp p10_parlbatch)
SEEDS=(42 43 44 45 46)
cd "$MONTY" || exit 1
total=$(( ${#ARMS[@]} * ${#SEEDS[@]} )); i=0; fail=0
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    i=$((i+1)); run="${arm}_s${seed}"
    echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"$arm seed $seed\"}"
    start=$(date +%s)
    timeout 2400 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
        "experiment=$arm" "++experiment.config.seed=$seed" \
        "++experiment.config.n_eval_epochs=4" \
        "++experiment.config.logging.wandb_id=p10" \
        "++experiment.config.logging.run_name=$run" >/dev/null 2>&1 || { echo "FAILED: $run"; fail=$((fail+1)); }
    eps=$(( ($(wc -l < "$MONTY_LOGS/projects/monty_runs/$run/eval_stats.csv" 2>/dev/null || echo 1) - 1) / 5 ))
    [ "$eps" -ne 40 ] && { echo "  WARNING $run: $eps episodes, expected 40"; fail=$((fail+1)); }
    echo "  $run done in $(( $(date +%s) - start ))s, $eps episodes"
  done
done
echo "JCODE_CHECKPOINT {\"message\":\"P10 sweep finished, $fail failures\"}"
echo "failures: $fail"
