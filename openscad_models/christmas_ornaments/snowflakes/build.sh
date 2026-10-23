#!/bin/bash
# Export the six crystal snowflakes, one STL each:  ./build.sh
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
mkdir -p logs
for n in 1 2 3 4 5 6; do
  openscad -D design=$n -o crystal_snowflake_$n.stl crystal_snowflakes.scad > logs/flake_$n.log 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/flake_*.log | sort | uniq -c || true
