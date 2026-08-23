#!/usr/bin/env bash
# P9: iterated voting -- 3 arms x 5 seeds x 50 episodes = 750 episodes.
#
# Pre-registered at 0d9b386. Mechanism gated at b95ad06 (rounds=1 == upstream
# call-for-call; all arms verified live).
#
# rounds=1 is the replication control: it must reproduce P7's max arm. If it
# does not, the loop changed something other than the number of exchanges and
# the whole comparison is void.
#
# n_eval_epochs=4 is REQUIRED and is not in the yaml. `Predefined.__call__`
# (object_init_samplers.py:82) indexes the rotation list by EPOCH, not episode,
# so with n_eval_epochs=1 only the FIRST of the four OOD rotations is ever
# evaluated -- 10 episodes instead of 50, and 1 of 4 OOD conditions. The first
# P9 sweep was voided by exactly this. P7's powered run passed it on the
# command line, which is why its committed yaml also says 1.
#
# Usage: bash tools/run_p9.sh
set -u

MONTY="$HOME/PolyBrains/upstream/tbp.monty"
export MONTY_DATA=~/tbp/data
export MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty
export PYTHONPATH=~/PolyBrains/src

ROUNDS=(1 2 3)
SEEDS=(42 43 44 45 46)
EPOCHS=4   # one per OOD rotation -- see note above

cd "$MONTY" || exit 1
total=$(( ${#ROUNDS[@]} * ${#SEEDS[@]} ))
i=0
fail=0

for r in "${ROUNDS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    i=$((i+1))
    run="p9_r${r}_s${seed}"
    echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"rounds=$r seed $seed\"}"
    start=$(date +%s)
    if ! timeout 1800 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
        "experiment=p9_rounds${r}" \
        "++experiment.config.seed=$seed" \
        "++experiment.config.n_eval_epochs=$EPOCHS" \
        "++experiment.config.logging.wandb_id=p9" \
        "++experiment.config.logging.run_name=$run" \
        >/dev/null 2>&1; then
      echo "FAILED: $run"
      fail=$((fail+1))
    fi
    # Guard: a run that did not produce 50 episodes is not comparable to P7.
    eps=$(( ($(wc -l < "$MONTY_LOGS/projects/monty_runs/$run/eval_stats.csv") - 1) / 5 ))
    if [ "$eps" -ne 40 ]; then
      echo "  WARNING $run produced $eps episodes, expected 40 (10 objects x 4 rotations)"
      fail=$((fail+1))
    fi
    echo "  $run done in $(( $(date +%s) - start ))s, $eps episodes"
  done
done

echo "JCODE_CHECKPOINT {\"message\":\"P9 sweep finished, $fail failures\"}"
echo "failures: $fail"
