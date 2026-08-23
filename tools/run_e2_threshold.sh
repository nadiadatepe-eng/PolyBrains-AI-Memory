#!/usr/bin/env bash
# E2: does the vote rule matter more when Monty's vote_evidence_threshold stops
# pre-filtering disagreement away?
#
# NOTE: thresholds must stay in [0,1]: the CMP Message contract asserts
# "Confidence must be in [0,1]", so negative thresholds cannot be tested.
#
# CP-5 found max/mean/consensus nearly indistinguishable at the default
# threshold of 0.8. The synthetic analysis says why: votes above 0.8 are
# near-unanimous by construction (D-index 0.04), so a consensus rule has almost
# nothing to correct. This tests that explanation on the real system by
# lowering the threshold and re-running the arms.
#
# Usage: bash tools/run_e2_threshold.sh
set -u

MONTY="$HOME/PolyBrains/upstream/tbp.monty"
OUT="$HOME/PolyBrains/reports/e2-threshold.tsv"
export MONTY_DATA=~/tbp/data
export MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty
export PYTHONPATH=~/PolyBrains/src

THRESHOLDS=(0.8 0.5 0.2 0.05)
ARMS=(e1_ood_max e1_ood_consensus)
SEEDS=(42 45)     # the two seeds that produced the hardest episodes at 0.8

cd "$MONTY" || exit 1
printf "threshold\tarm\tseed\tepisodes\tcorrect\taccuracy\tseconds\n" > "$OUT"

total=$(( ${#THRESHOLDS[@]} * ${#ARMS[@]} * ${#SEEDS[@]} ))
i=0
for th in "${THRESHOLDS[@]}"; do
  for arm in "${ARMS[@]}"; do
    for seed in "${SEEDS[@]}"; do
      i=$((i+1))
      tag=$(echo "$th" | tr -d '.' | tr '-' 'n')
      run="e2_${tag}_${arm}_s${seed}"
      echo "JCODE_PROGRESS {\"current\":$i,\"total\":$total,\"unit\":\"runs\",\"message\":\"th=$th $arm s$seed\"}"
      start=$(date +%s)
      # override the threshold on every learning module
      ov=()
      for lm in 0 1 2 3 4; do
        ov+=("++experiment.config.monty_config.learning_modules.learning_module_${lm}.vote_evidence_threshold=${th}")
      done
      timeout 1800 .venv/bin/python run.py -cd ~/PolyBrains/configs -cn experiment \
          "experiment=$arm" \
          "++experiment.config.seed=$seed" \
          "++experiment.config.logging.wandb_id=e2" \
          "++experiment.config.logging.run_name=$run" \
          "${ov[@]}" >/dev/null 2>&1
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
        printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$th" "$arm" "$seed" "$eps" "$ok" "$acc" "$elapsed" >> "$OUT"
        echo "  th=$th $arm s$seed -> $ok/$eps = ${acc}%  (${elapsed}s)"
      else
        printf "%s\t%s\t%s\tFAILED\t\t\t%s\n" "$th" "$arm" "$seed" "$elapsed" >> "$OUT"
        echo "  th=$th $arm s$seed -> FAILED (${elapsed}s)"
      fi
    done
  done
done

echo
echo "============ E2: rule effect vs threshold ============"
python3 - "$OUT" <<'PY'
import csv, statistics, sys
from collections import defaultdict
rows = [r for r in csv.DictReader(open(sys.argv[1]), delimiter='\t')
        if r['episodes'] not in ('FAILED','')]
by = defaultdict(list)
for r in rows:
    by[(r['threshold'], r['arm'])].append(float(r['accuracy']))

ths = sorted({k[0] for k in by}, key=float, reverse=True)
print(f"{'threshold':>10} {'max':>10} {'consensus':>12} {'gap':>10}")
print("-"*46)
for th in ths:
    m = by.get((th,'e1_ood_max'), [])
    c = by.get((th,'e1_ood_consensus'), [])
    if m and c:
        mm, cc = statistics.mean(m), statistics.mean(c)
        print(f"{th:>10} {mm:>9.2f}% {cc:>11.2f}% {cc-mm:>+9.2f}pp")
print()
print("If the gap grows as the threshold falls, the CP-5 null is explained by")
print("the threshold pre-filtering disagreement, not by the rule being inert.")
PY
echo "Full results: $OUT"
