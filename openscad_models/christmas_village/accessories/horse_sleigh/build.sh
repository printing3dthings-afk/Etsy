#!/bin/bash
# Export the horse sleigh's three printed pieces, each as colour parts and a
# one-body union, and the whole horse standing (for renders):
#   ./build.sh            pieces: sleigh near far horse
# Empty parts are dropped. tools/part_mesh.py check proves the rest closed.
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../../assets/openscad_libs && pwd)"
mkdir -p logs
jobs_=()
for piece in ${@:-sleigh near far horse}; do
  for p in body roof trim accent union; do
    [ "$piece" = horse ] && [ "$p" = union ] && continue
    jobs_+=("$piece $p")
  done
done
printf '%s\n' "${jobs_[@]}" | xargs -P 4 -L 1 sh -c \
  'openscad -D "piece=\"$0\"" -D "part=\"$1\"" -o "hs_$0_$1.stl" victorian_horse_sleigh.scad > "logs/$0_$1.log" 2>&1'
for f in logs/*_*.log; do
  b=$(basename "$f" .log)
  grep -q "Current top level object is empty" "$f" && rm -f "hs_$b.stl" && echo "$b: empty"
done
grep -h "WARNING\|ERROR" logs/*_*.log | sort | uniq -c || true
