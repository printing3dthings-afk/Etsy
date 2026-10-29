#!/usr/bin/env bash
# The two Click Into Celebration clickers: export every colour part (CGAL, one
# at a time), the loose-socket caps, and the merged prints the gate reads.
#   ./build.sh            both
#   ./build.sh tin|jar    one
set -uo pipefail
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../assets/openscad_libs && pwd)"
want=${1:-all}
run() {   # dir scad part [out-suffix] [extra -D]
    local d=$1 f=$2 p=$3 o=${4:-$3} x=${5:-}
    local out=$d/parts/${o}.stl
    mkdir -p $d/parts $d/logs
    [ -s "$out" ] && [ "$out" -nt "$d/$f" ] && [ "$out" -nt clicker_lib.scad ] && return
    echo "  $d $o"
    openscad -D "part=\"$p\"" $x -o "$out.tmp.stl" "$d/$f" > "$d/logs/$o.log" 2>&1 \
        && mv "$out.tmp.stl" "$out" || { echo "FAILED $d $o"; tail -3 "$d/logs/$o.log"; }
}
if [ $want = all ] || [ $want = tin ]; then
    T=gingerbread_tin F=gingerbread_tin_clicker.scad
    for p in tin tin_snow lid cookie cookie_icing cookie_red cookie_green tin_print lid_print cookie_print; do run $T $F $p; done
    run $T $F cookie cookie_loose "-D sock_fit=0.22"
fi
if [ $want = all ] || [ $want = jar ]; then
    J=cookie_jar F=cookie_jar_clicker.scad
    for p in jar jar_label jar_letters top top_rim gb gb_icing gb_red jar_print top_print gb_print; do run $J $F $p; done
    run $J $F gb gb_loose "-D sock_fit=0.22"
fi
grep -l "ERROR\|WARNING" */logs/*.log 2>/dev/null && echo "(warnings in the logs above)" || true
