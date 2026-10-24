#!/bin/bash
# Leland's Toy Story pieces: plaque fidelity, studio renders, then CGAL meshes to print from.
cd "$(dirname "$0")"
T=../../../tools
(cd plaque && python3 ../$T/print_fidelity.py --part leland_plaque_blue.stl:#2B5FA8 --part leland_plaque_white.stl:#F4F1EA \
  --part leland_plaque_red.stl:#C8312B --part leland_plaque_yellow.stl:#F2C230 --json logs/fidelity.json --keep logs/fidelity_work > logs/fidelity.txt 2>&1
 sed -n '/PRINT FIDELITY/,/smaller/p' logs/fidelity.txt | grep -E 'PRINT|dropped \(|flagged|FLAG'; echo PLAQUE_FIDELITY_DONE)
C="0.957,0.945,0.918"; R="0.784,0.192,0.169"; B="0.169,0.373,0.659"; Y="0.949,0.761,0.188"
python3 $T/blender_render.py --part rocket/pizza_planet_rocket_white.stl:$C --part rocket/pizza_planet_rocket_red.stl:$R \
  --part rocket/pizza_planet_rocket_blue.stl:$B --part rocket/pizza_planet_rocket_yellow.stl:$Y --views --resolution 1400 --timeout 2400 -o rocket/images/rocket
python3 $T/blender_render.py --part plaque/leland_plaque_blue.stl:$B --part plaque/leland_plaque_white.stl:$C \
  --part plaque/leland_plaque_red.stl:$R --part plaque/leland_plaque_yellow.stl:$Y --elevation 70 --azimuth 0 --resolution 1400 --timeout 2400 -o plaque/images/plaque.png
echo RENDERS_DONE
mkdir -p print_files
(cd rocket && ./build.sh cgal white red blue yellow plate) && (cd plaque && ./build.sh cgal blue white red yellow)
echo CGAL_DONE
