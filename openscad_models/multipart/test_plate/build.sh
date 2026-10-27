#!/usr/bin/env bash
# Exports every part of the fit test plate (three clearances each), checks the
# pairs assembled, lays them out on the P1S plate and writes the 3MF.
#   ./build.sh          everything
#   ./build.sh parts    only the STLs
set -euo pipefail
cd "$(dirname "$0")"
export OPENSCADPATH=../../../assets/openscad_libs
mkdir -p parts logs
KINDS=(screw nut ball socket gear_base gear20 gear10 detent_base detent_wheel bayonet_ring bayonet_cap)
jobs=()
for k in "${KINDS[@]}"; do for i in 0 1 2; do
    out=parts/${k}_${i}.stl
    [ -s "$out" ] && [ "$out" -nt fit_test_plate.scad ] && [ "$out" -nt ../thread_lib.scad ] && continue
    ( openscad -D "kind=\"$k\"" -D "idx=$i" -o "$out.tmp.stl" fit_test_plate.scad > "logs/${k}_${i}.log" 2>&1 \
        && mv "$out.tmp.stl" "$out" || echo "FAILED $k $i (logs/${k}_${i}.log)" ) &
    while [ "$(jobs -rp | wc -l)" -ge "${JOBS:-3}" ]; do sleep 1; done
done; done
wait
[ "${1:-}" = parts ] && exit 0
python3 check_fits.py parts
python3 pack_plate.py parts fit_test_plate.3mf
