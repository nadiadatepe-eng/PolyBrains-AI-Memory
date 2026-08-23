#!/usr/bin/env bash
# CP-5: run the full arm sequence unattended and write a results table.
#
# Order matters and follows PREDICTIONS.md:
#   1. noise floor on the baseline arm (5 seeds) -- without this no difference
#      can be called an effect
#   2. each arm on 3 seeds
#
# Usage: bash tools/run_cp5.sh
set -u

MONTY="$HOME/PolyBrains/upstream/tbp.monty"
OUT="$HOME/PolyBrains/reports/cp5-results.tsv"
export MONTY_DATA=~/tbp/data
export MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty
export PYTHONPATH=~/PolyBrains/src

ARMS=(e0_baseline_indomain e1_ood_max e1_ood_mean e1_ood_consensus)
SEEDS=(42 43 44 45 46)

cd "$MONTY" || exit 1
printf "arm\tseed\tepisodes\tcorrect\taccuracy\tseconds\n" > "$OUT"

total=$(( ${#ARMS[@]} * ${#SEEDS[@]} ))
i=0
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    i=$((i+1))
    run="cp5_${arm}_s${seed}"
    echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"$arm seed $seed\"}"
    start=$(date +%s)
    timeout 1800 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
        "experiment=$arm" \
        "++experiment.config.seed=$seed" \
        "++experiment.config.logging.wandb_id=cp5" \
        "++experiment.config.logging.run_name=$run" \
        >/dev/null 2>&1
    elapsed=$(( $(date +%s) - start ))

    csv="$MONTY_LOGS/projects/monty_runs/$run/eval_stats.csv"
    if [ -f "$csv" ]; then
      read -r eps ok acc <<< "$(python3 - "$csv" <<'PY'
import csv, sys
r = list(csv.DictReader(open(sys.argv[1])))
ok = sum(1 for x in r if x['primary_performance'].startswith('correct'))
print(len(r), ok, f"{100*ok/len(r):.2f}" if r else "0")
PY
)"
      printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$arm" "$seed" "$eps" "$ok" "$acc" "$elapsed" >> "$OUT"
      echo "  $arm s$seed -> $ok/$eps = ${acc}%  (${elapsed}s)"
    else
      printf "%s\t%s\tFAILED\t\t\t%s\n" "$arm" "$seed" "$elapsed" >> "$OUT"
      echo "  $arm s$seed -> FAILED (${elapsed}s)"
    fi
  done
done

echo
echo "================= CP-5 SUMMARY ================="
python3 - "$OUT" <<'PY'
import csv, statistics, sys
from collections import defaultdict
rows = [r for r in csv.DictReader(open(sys.argv[1]), delimiter='\t')
        if r['episodes'] not in ('FAILED','')]
by = defaultdict(list)
for r in rows:
    by[r['arm']].append(float(r['accuracy']))

print(f"{'arm':26} {'n':>2} {'mean':>8} {'stdev':>8} {'min':>7} {'max':>7}")
print("-"*66)
stats = {}
for arm, acc in by.items():
    sd = statistics.stdev(acc) if len(acc) > 1 else 0.0
    stats[arm] = (statistics.mean(acc), sd)
    print(f"{arm:26} {len(acc):>2} {statistics.mean(acc):>7.2f}% {sd:>7.2f} "
          f"{min(acc):>6.2f} {max(acc):>6.2f}")

base = 'e0_baseline_indomain'
if base in stats:
    floor = stats[base][1]
    print()
    print(f"NOISE FLOOR (baseline stdev): {floor:.2f} pp")
    print("Any arm difference smaller than this is NOT an effect.")
    print()
    if 'e1_ood_max' in stats:
        ref = stats['e1_ood_max'][0]
        print(f"{'arm':26} {'vs e1_ood_max':>14} {'verdict':>22}")
        print("-"*66)
        for arm in ('e1_ood_mean','e1_ood_consensus'):
            if arm in stats:
                d = stats[arm][0] - ref
                verdict = "within noise" if abs(d) <= max(floor, 1e-9) else (
                    "BETTER than max" if d > 0 else "WORSE than max")
                print(f"{arm:26} {d:>+13.2f}pp {verdict:>22}")
        print()
        print(f"in-domain (e0) mean: {stats[base][0]:.2f}%")
        print(f"OOD delta for max  : {ref - stats[base][0]:+.2f} pp")
PY
echo
echo "Full results: $OUT"
