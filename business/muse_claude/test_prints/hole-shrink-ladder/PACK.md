# TEST — Hole Shrink Ladder — pack

Status: BUILT Nov 22, 2026 (Batch 1 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
Holes print smaller than designed; pegs print close to size. This ladder gives the
real numbers for a filament: print it, then check each hole with drill bits / pin
gauges (or measure pegs with calipers) and read the shrink per diameter.

## Geometry (src/hole_ladder.py, src/HoleShrinkLadder.stl)
- Base plate 148 x 76 x 5 mm, watertight single solid.
- Through-holes O2, 3, 4, 5, 6, 8, 10 mm in a row (20 mm pitch), each labelled
  with its designed size engraved on the top face.
- Matching solid bosses/pegs at the same seven diameters, 8 mm tall, second row,
  also labelled.
- Labels engraved 0.8 mm (DejaVu Bold, manifold-boolean cut).

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- HoleShrinkLadder_Standard_P1S.3mf — 0.20 mm Standard @BBL X1C, 3 walls, 15% grid,
  supports off, ironing off. Verified slice: 49 min 49 sec - 36.96 g.
- HoleShrinkLadder_Optimized_P1S.3mf — 0.16 mm Optimal @BBL X1C, 3 walls, 12% gyroid,
  supports off, ironing off. Verified slice: 1 hr 07 min - 40.38 g.
- Both: matte white PLA (Bambu PLA Matte @BBL P1S 0.4 nozzle), printer Bambu Lab
  P1S 0.4 nozzle, round-trip re-slice with checks ON passed.

## Profile choices / compromises
- Ironing deliberately OFF on both profiles: an ironing pass can leave a slight
  lip at a hole mouth, and the hole mouths are the measuring surface here. The
  Optimized profile's quality lever is the 0.16 mm layer height (rounder,
  cleaner bores), per the shop rule that Optimized is the best-outcome profile.
- No brim: the 148 x 76 plate has ample bed contact.

## Gallery
images/ are the Studio plate render of the Standard profile + centre/corner
crops — renders, labelled as such in the listing copy until Scott prints it.
