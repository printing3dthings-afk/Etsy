#!/bin/bash
# Leland's name plaque (personal, not for sale). Fast build by default; ./build.sh cgal to print from.
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../../assets/openscad_libs && pwd)"
name=leland_plaque
mkdir -p logs
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
if [ "$1" = "cgal" ]; then cmd=(openscad); shift; else cmd=("$FAST" --backend=manifold); fi
parts="${*:-slot1 green red yellow}"
for p in $parts; do "${cmd[@]}" -D "part=\"$p\"" -o "${name}_$p.stl" $name.scad > "logs/$p.log" 2>&1 & done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
