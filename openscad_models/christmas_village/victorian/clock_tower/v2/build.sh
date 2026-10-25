#!/bin/bash
# v2 of the clock tower (the clock that shows when lit). Same parts as ../build.sh.
#   ./build.sh          fast: OpenSCAD 2026 manifold engine, for checking
#   ./build.sh cgal     the shipping export: OpenSCAD 2021.01 CGAL (hours)
# The manifold engine renders a part in under a minute and agrees with CGAL's
# volume to 0.2 mm3, but its STL carries zero-area slivers at T-junctions that
# mesh_gate reads as open edges (2026-10-24), so shipped meshes stay CGAL's.
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../../../assets/openscad_libs && pwd)"
name=victorian_clock_tower_v2
mkdir -p logs
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
if [ "$1" = "cgal" ]; then cmd=(openscad); shift; else cmd=("$FAST" --backend=manifold); fi
parts="${*:-body roof trim accent}"
for p in $parts; do
  "${cmd[@]}" -D "part=\"$p\"" -o "${name}_$p.stl" $name.scad > "logs/$p.log" 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
