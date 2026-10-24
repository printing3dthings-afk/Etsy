#!/bin/bash
# v2's checks after a change: rebuild, four-colour fidelity slice, then renders.
cd "$(dirname "$0")"
./build.sh body roof trim accent
p=victorian_santas_workshop_v2
python3 ../../../../../tools/print_fidelity.py --part ${p}_body.stl:#A8483A --part ${p}_roof.stl:#2E3440 \
  --part ${p}_trim.stl:#F4F1EA --part ${p}_accent.stl:#2F6B45 --json logs/fidelity.json --keep logs/fidelity_work > logs/fidelity.txt 2>&1
echo FIDELITY_DONE
./render_compare.sh
