#!/bin/bash
# Fetch the 10 "distinct objects" from the official YCB S3 bucket into MuJoCo layout.
# Avoids habitat_sim.utils.datasets_download, which is unavailable on Linux
# (the PyPI wheel is macosx_13_0_arm64 + cp310 only).
#
# MuJoCo's _load_custom_object needs exactly two files per object:
#   <name>/textured.obj  and  <name>/texture_map.png
set -u

DEST="${MONTY_DATA:-$HOME/tbp/data}/mujoco/objects/ycb"
WORK="${TMPDIR:-/tmp}/ycb-fetch-$$"

declare -A M=(
  [mug]=025_mug
  [bowl]=024_bowl
  [potted_meat_can]=010_potted_meat_can
  [spoon]=031_spoon
  [strawberry]=012_strawberry
  [mustard_bottle]=006_mustard_bottle
  [dice]=062_dice
  [golf_ball]=058_golf_ball
  [c_lego_duplo]=073-c_lego_duplo
  [banana]=011_banana
)

mkdir -p "$DEST" "$WORK"
cd "$WORK" || exit 1

for name in "${!M[@]}"; do
  ycb=${M[$name]}
  if [ -f "$DEST/$name/textured.obj" ] && [ -f "$DEST/$name/texture_map.png" ]; then
    echo "have $name"
    continue
  fi
  url="https://ycb-benchmarks.s3.amazonaws.com/data/berkeley/${ycb}/${ycb}_berkeley_meshes.tgz"
  curl -sfL "$url" -o "${ycb}.tgz" || { echo "FAIL download $name"; continue; }
  tar xzf "${ycb}.tgz" 2>/dev/null

  # '! -name ._*' matters: the tarballs carry macOS AppleDouble resource-fork
  # files that sort first and are not valid PNG/OBJ. Without this filter MuJoCo
  # fails with "incorrect PNG signature, it's no PNG or corrupted".
  obj=$(find . -path "*${ycb}*" -name "textured.obj" ! -name "._*" | head -1)
  [ -z "$obj" ] && { echo "FAIL no mesh $name"; continue; }
  tex=$(find "$(dirname "$obj")" -name "*.png" ! -name "._*" | head -1)
  [ -z "$tex" ] && { echo "FAIL no texture $name"; continue; }

  mkdir -p "$DEST/$name"
  cp "$obj" "$DEST/$name/textured.obj"
  cp "$tex" "$DEST/$name/texture_map.png"
  echo "ok $name"
done

echo "--- verify (all must read 'PNG image data') ---"
for d in "$DEST"/*/; do
  printf "%-18s %s\n" "$(basename "$d")" "$(file -b "$d/texture_map.png" | head -c 40)"
done

echo
echo "Scratch left at: $WORK  (delete manually when satisfied)"
