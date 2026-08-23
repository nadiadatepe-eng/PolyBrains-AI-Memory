#!/usr/bin/env bash
# CP-5: noise floor. Run one arm N times with different seeds and report the
# spread. Any effect smaller than this is not an effect.
#
# Usage: bash tools/noise_floor.sh <experiment_name> [n_seeds] [out.tsv]
set -u

EXP="${1:-e0_baseline_indomain}"
N="${2:-5}"
OUT="${3:-$HOME/PolyBrains/reports/noise-floor-$EXP.tsv}"
MONTY="$HOME/PolyBrains/upstream/tbp.monty"

export MONTY_DATA=~/tbp/data
export MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty
export PYTHONPATH=~/PolyBrains/src

cd "$MONTY" || exit 1
printf "seed\tepisodes\tcorrect\taccuracy\tseconds\n" > "$OUT"

for i in $(seq 1 "$N"); do
  seed=$((41 + i))
  echo "JCODE_PROGRESS {\"current\":$i,\"total\":$N,\"unit\":\"seeds\",\"message\":\"seed $seed\"}"
  start=$(date +%s)
  timeout 1800 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
      "experiment=$EXP" \
      "++experiment.config.seed=$seed" \
      "++experiment.config.logging.wandb_id=nf$seed" \
      "++experiment.config.logging.run_name=nf_${EXP}_s${seed}" \
      >/dev/null 2>&1
  elapsed=$(( $(date +%s) - start ))

  csv="$MONTY_LOGS/projects/monty_runs/nf_${EXP}_s${seed}/eval_stats.csv"
  if [ -f "$csv" ]; then
    read -r eps ok acc <<< "$(python3 - "$csv" <<'PY'
import csv, sys
r = list(csv.DictReader(open(sys.argv[1])))
ok = sum(1 for x in r if x['primary_performance'].startswith('correct'))
print(len(r), ok, f"{100*ok/len(r):.2f}" if r else 0)
PY
)"
    printf "%s\t%s\t%s\t%s\t%s\n" "$seed" "$eps" "$ok" "$acc" "$elapsed" >> "$OUT"
    echo "  seed $seed -> $ok/$eps = ${acc}%  (${elapsed}s)"
  else
    printf "%s\tFAILED\t\t\t%s\n" "$seed" "$elapsed" >> "$OUT"
    echo "  seed $seed -> FAILED (${elapsed}s)"
  fi
done

echo
echo "=== NOISE FLOOR ==="
python3 - "$OUT" <<'PY'
import csv, statistics, sys
rows = [r for r in csv.DictReader(open(sys.argv[1]), delimiter='\t')
        if r['episodes'] not in ('FAILED', '')]
acc = [float(r['accuracy']) for r in rows]
if not acc:
    print("no successful runs"); raise SystemExit(1)
print(f"n           = {len(acc)}")
print(f"accuracies  = {acc}")
print(f"mean        = {statistics.mean(acc):.2f}%")
if len(acc) > 1:
    print(f"stdev       = {statistics.stdev(acc):.2f} pp")
    print(f"range       = {min(acc):.2f} - {max(acc):.2f}  (spread {max(acc)-min(acc):.2f} pp)")
    print()
    print(f"An arm difference smaller than ~{max(statistics.stdev(acc), (max(acc)-min(acc))/2):.2f} pp is NOT an effect.")
PY
echo "Full results: $OUT"
