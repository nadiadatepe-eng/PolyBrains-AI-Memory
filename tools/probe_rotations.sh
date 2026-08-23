#!/usr/bin/env bash
# CP-5 blocker probe: which of the 14 `rotations_all` entries are usable under
# MuJoCo, and which trigger "no visible target object"?
#
# CP-0 worked around this by training on [[0,0,0]] alone, which is why its 60%
# accuracy is a liveness check and not a baseline. This finds the real answer
# by running each rotation individually rather than guessing.
#
# Usage:  bash tools/probe_rotations.sh [output.tsv]
set -u

OUT="${1:-$HOME/PolyBrains/reports/rotation-probe.tsv}"
MONTY="$HOME/PolyBrains/upstream/tbp.monty"
export MONTY_DATA=~/tbp/data
export MONTY_MODELS=~/tbp/results/monty/pretrained_models
export MONTY_LOGS=~/tbp/results/monty/probe

ROTATIONS=(
  "[0,0,0]" "[0,90,0]" "[0,180,0]" "[0,270,0]"
  "[90,0,0]" "[90,180,0]"
  "[35,45,0]" "[325,45,0]" "[35,315,0]" "[325,315,0]"
  "[35,135,0]" "[325,135,0]" "[35,225,0]" "[325,225,0]"
)

cd "$MONTY" || exit 1
printf "rotation\tstatus\tseconds\tdetail\n" > "$OUT"

n=${#ROTATIONS[@]}
i=0
for rot in "${ROTATIONS[@]}"; do
  i=$((i+1))
  echo "JCODE_PROGRESS {\"current\":$i,\"total\":$n,\"unit\":\"rotations\",\"message\":\"$rot\"}"
  start=$(date +%s)
  log=$(timeout 600 .venv/bin/python run.py \
      -cd ~/PolyBrains/configs -cn experiment \
      'experiment=cp0_pretrain_5lms_mujoco' \
      '++experiment.config.logging.wandb_id=rotprobe' \
      '++experiment.config.n_train_epochs=1' \
      "++experiment.config.train_env_interface_args.object_init_sampler.rotations=[$rot]" \
      2>&1)
  rc=$?
  elapsed=$(( $(date +%s) - start ))

  if [ $rc -eq 124 ]; then
    status="TIMEOUT"; detail="exceeded 600s"
  elif echo "$log" | grep -q "no visible target object"; then
    status="NO_VIEW"; detail="ValueError: no visible target object"
  elif [ $rc -ne 0 ]; then
    status="ERROR"
    detail=$(echo "$log" | grep -E "Error|Exception" | tail -1 | cut -c1-90)
  else
    status="OK"; detail=""
  fi
  printf "%s\t%s\t%s\t%s\n" "$rot" "$status" "$elapsed" "$detail" >> "$OUT"
  echo "  $rot -> $status (${elapsed}s)"
done

echo
echo "=== SUMMARY ==="
awk -F'\t' 'NR>1{c[$2]++} END{for(k in c) printf "%-8s %d\n", k, c[k]}' "$OUT"
echo
echo "Usable rotations:"
awk -F'\t' 'NR>1 && $2=="OK"{printf "%s ", $1} END{print ""}' "$OUT"
echo "Full results: $OUT"
