#!/usr/bin/env bash
# P11: the P10 parliament under vote_mode=consensus -- 5 arms x 5 seeds x 40 eps.
#
# All five arms run consensus, including the plain baselines: reusing P9's max
# arms would confound the reduction rule with the parliamentary structure.
#
# n_eval_epochs=4 is REQUIRED: Predefined indexes rotations by EPOCH, so 1 epoch
# silently evaluates 1 of 4 OOD rotations. Two sweeps were voided by this.
set -u
MONTY="$HOME/PolyBrains/upstream/tbp.monty"
export MONTY_DATA=~/tbp/data MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty PYTHONPATH=~/PolyBrains/src
ARMS=(p11_plain1 p11_plain3 p11_parl3 p11_parlnoopp p11_parlbatch)
SEEDS=(42 43 44 45 46)
cd "$MONTY" || exit 1
total=$(( ${#ARMS[@]} * ${#SEEDS[@]} )); i=0; fail=0
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    i=$((i+1)); run="${arm}_s${seed}"
    # Monty APPENDS to an existing eval_stats.csv. An aborted earlier launch
    # therefore leaves rows that the rerun adds to, producing a run with more
    # than 40 episodes whose first rows came from a different process. Caught
    # here in P11 by the episode-count guard; removed at the source now.
    rm -rf "$MONTY_LOGS/projects/monty_runs/$run"
    echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"$arm seed $seed\"}"
    start=$(date +%s)
    timeout 2400 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
        "experiment=$arm" "++experiment.config.seed=$seed" \
        "++experiment.config.n_eval_epochs=4" \
        "++experiment.config.logging.wandb_id=p11" \
        "++experiment.config.logging.run_name=$run" >/dev/null 2>&1 || { echo "FAILED: $run"; fail=$((fail+1)); }
    eps=$(( ($(wc -l < "$MONTY_LOGS/projects/monty_runs/$run/eval_stats.csv" 2>/dev/null || echo 1) - 1) / 5 ))
    [ "$eps" -ne 40 ] && { echo "  WARNING $run: $eps episodes, expected 40"; fail=$((fail+1)); }
    echo "  $run done in $(( $(date +%s) - start ))s, $eps episodes"
  done
done
echo "JCODE_CHECKPOINT {\"message\":\"P11 sweep finished, $fail failures\"}"
echo "failures: $fail"
