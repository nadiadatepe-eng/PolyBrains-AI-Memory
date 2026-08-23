#!/usr/bin/env bash
# P12: H2's first real test -- 3 arms x 5 seeds x 90 episodes.
#
# 9 rotations (5 in-domain + 4 OOD), so n_eval_epochs=9 is REQUIRED: Predefined
# indexes the rotation list by EPOCH, not episode. With fewer epochs the run
# silently evaluates a subset -- two sweeps were voided by exactly this.
#
# The run directory is cleared first: Monty APPENDS to an existing
# eval_stats.csv, so an aborted launch leaves rows the rerun adds to (P11).
#
# w(t) liveness is checked by tools/analyse_p12.py from the weight trace each
# run writes. An adaptive arm whose weights never move is a dead arm.
set -u
MONTY="$HOME/PolyBrains/upstream/tbp.monty"
export MONTY_DATA=~/tbp/data MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty PYTHONPATH=~/PolyBrains/src
ARMS=(p12_frozen p12_ood p12_indomain)
SEEDS=(42 43 44 45 46)
EPOCHS=9          # one per rotation: 5 in-domain + 4 OOD
EXPECT=90         # 10 objects x 9 rotations
TRACE=~/PolyBrains/reports/p12-weights
mkdir -p "$TRACE"
cd "$MONTY" || exit 1
total=$(( ${#ARMS[@]} * ${#SEEDS[@]} )); i=0; fail=0
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    i=$((i+1)); run="${arm}_s${seed}"
    rm -rf "$MONTY_LOGS/projects/monty_runs/$run"
    echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"$arm seed $seed\"}"
    start=$(date +%s)
    # Run through a wrapper so the weight trace is written: it lives on the
    # experiment object and is not part of eval_stats.csv.
    timeout 3600 .venv/bin/python - "$arm" "$seed" "$EPOCHS" "$TRACE/$run.tsv" <<'PY' >/dev/null 2>&1
import sys, csv
from hydra import compose, initialize_config_dir
from tbp.monty.hydra import register_resolvers, instantiate_experiment
from tbp.monty.frameworks.run import output_dir_from_run_name
arm, seed, epochs, tracefile = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
register_resolvers()
with initialize_config_dir(config_dir='[source PolyBrains checkout]/configs', version_base=None):
    cfg = compose(config_name='experiment', overrides=[
        f'experiment={arm}',
        f'++experiment.config.seed={seed}',
        f'++experiment.config.n_eval_epochs={epochs}',
        '++experiment.config.logging.wandb_id=p12',
        f'++experiment.config.logging.run_name={arm}_s{seed}',
    ])
# run.py:61 does this before instantiating. Skipping it makes every run log to
# the PARENT directory instead of its own -- the first P12 launch wrote no
# eval_stats.csv at all and the episode-count guard caught it at 0 episodes.
cfg.experiment.config.logging.output_dir = str(output_dir_from_run_name(cfg))
exp = instantiate_experiment(cfg.experiment)
with exp:
    exp.run()
with open(tracefile, 'w', newline='') as fh:
    w = csv.writer(fh, delimiter='\t')
    w.writerow(['episode', 'lm', 'weight', 'score', 'was_correct'])
    w.writerows(exp.weight_trace)
PY
    rc=$?
    [ $rc -ne 0 ] && { echo "FAILED: $run (rc=$rc)"; fail=$((fail+1)); }
    eps=$(( ($(wc -l < "$MONTY_LOGS/projects/monty_runs/$run/eval_stats.csv" 2>/dev/null || echo 1) - 1) / 5 ))
    [ "$eps" -ne "$EXPECT" ] && { echo "  WARNING $run: $eps episodes, expected $EXPECT"; fail=$((fail+1)); }
    echo "  $run done in $(( $(date +%s) - start ))s, $eps episodes"
  done
done
echo "JCODE_CHECKPOINT {\"message\":\"P12 sweep finished, $fail failures\"}"
echo "failures: $fail"
