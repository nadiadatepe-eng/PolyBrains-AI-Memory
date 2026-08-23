#!/usr/bin/env bash
# P13: near-copy control for H1 clause 2 -- 4 arms x 5 seeds x 40 OOD episodes.
#
# One variable: sensor patch separation (0.000 / 0.0025 / 0.01 stock / 0.04).
# Module count is held at 5 in every arm; this tests the DISAGREEMENT term of
# H1 clause 2, not the count term.
#
# n_eval_epochs=4 is REQUIRED: Predefined indexes rotations by EPOCH, so 1 epoch
# silently evaluates 1 of 4 OOD rotations. Two sweeps were voided by this.
#
# The run directory is cleared first: Monty APPENDS to an existing
# eval_stats.csv, so an aborted launch leaves rows the rerun adds to (P11).
#
# send_none% is captured per arm via tools/vote_spy.py and is MANDATORY, not
# optional. P6 moved this same variable to 0.08 and got silence (88% None), not
# disagreement. An arm whose vote path went quiet is not evidence.
set -u
MONTY="$HOME/PolyBrains/upstream/tbp.monty"
export MONTY_DATA=~/tbp/data MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty PYTHONPATH=~/PolyBrains/src
ARMS=(p13_sep000 p13_sep0025 p13_sep001 p13_sep004)
SEEDS=(42 43 44 45 46)
EXPECT=40
SPY=~/PolyBrains/reports/p13-votespy
mkdir -p "$SPY"
cd "$MONTY" || exit 1
total=$(( ${#ARMS[@]} * ${#SEEDS[@]} )); i=0; fail=0
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    i=$((i+1)); run="${arm}_s${seed}"
    rm -rf "$MONTY_LOGS/projects/monty_runs/$run"
    echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"$arm seed $seed\"}"
    start=$(date +%s)
    # Seed 42 of each arm runs under the vote spy so send_none% is measured on
    # the real path rather than assumed. PYTHONSTARTUP does not apply to -c, so
    # the spy is imported explicitly.
    if [ "$seed" = "42" ]; then
      PYTHONPATH="$PYTHONPATH:$HOME/PolyBrains/tools" \
      timeout 2400 .venv/bin/python -c "
import sys; sys.path.insert(0, '$HOME/PolyBrains/tools')
import vote_spy  # noqa: F401  -- patches the vote path, prints at exit
sys.argv = ['run.py', '-cd', '$HOME/PolyBrains/configs', '-cn', 'experiment',
            'experiment=$arm', '++experiment.config.seed=$seed',
            '++experiment.config.n_eval_epochs=4',
            '++experiment.config.logging.wandb_id=p13',
            '++experiment.config.logging.run_name=$run']
from tbp.monty.frameworks.run_env import setup_env; setup_env()
from tbp.monty.frameworks.run import main; main()
" >/dev/null 2>"$SPY/$run.txt" || { echo "FAILED: $run"; fail=$((fail+1)); }
    else
      timeout 2400 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
          "experiment=$arm" "++experiment.config.seed=$seed" \
          "++experiment.config.n_eval_epochs=4" \
          "++experiment.config.logging.wandb_id=p13" \
          "++experiment.config.logging.run_name=$run" >/dev/null 2>&1 \
          || { echo "FAILED: $run"; fail=$((fail+1)); }
    fi
    eps=$(( ($(wc -l < "$MONTY_LOGS/projects/monty_runs/$run/eval_stats.csv" 2>/dev/null || echo 1) - 1) / 5 ))
    [ "$eps" -ne "$EXPECT" ] && { echo "  WARNING $run: $eps episodes, expected $EXPECT"; fail=$((fail+1)); }
    echo "  $run done in $(( $(date +%s) - start ))s, $eps episodes"
  done
done
echo "JCODE_CHECKPOINT {\"message\":\"P13 sweep finished, $fail failures\"}"
echo "failures: $fail"
grep -h "VOTE-SPY" "$SPY"/*.txt 2>/dev/null || echo "(no vote-spy output captured)"
