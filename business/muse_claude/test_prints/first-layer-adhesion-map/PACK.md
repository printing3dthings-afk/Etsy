# TEST — First-Layer Adhesion Map — pack

Status: BUILT Nov 22, 2026 (Batch 1 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
One print that maps the whole build plate: 100 thin squares spread over the
printable area. Squares that lift, warp, print thin or refuse to stick mark
the zones with level, adhesion or contamination problems — and where the
first layer is dialled in, every square comes out identical.

## Geometry (src/adhesion_map.py, src/FirstLayerAdhesionMap.stl)
- 10 x 10 grid of 20 x 20 x 0.6 mm squares at 24 mm pitch (236 mm span),
  plus a 3 mm rail along the front edge = orientation marker, and a O8 mm
  hole in the front-left square = corner marker. Watertight single solid.
- P1S exclusion-zone fix (found by a failed slice, error -50 "no object is
  fully inside the print volume"): the plate has an 18 x 28 mm bed exclusion
  zone at the front-left (bed_exclude_area in the machine preset). The
  front-left square is shifted +10 mm in X and the rail starts at plate
  x = 22 mm so nothing enters it. That corner physically cannot print.

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- FirstLayerAdhesionMap_Standard_P1S.3mf — 0.20 mm Standard, 3 walls, 15%
  grid, supports off, ironing off. Verified slice: 1 hr 11 min - 31.24 g.
  (0.6 mm squares = exactly 3 layers.)
- FirstLayerAdhesionMap_Optimized_P1S.3mf — 0.16 mm Optimal, 3 walls, 12%
  gyroid, supports off, ironing off. Verified slice: 1 hr 26 min - 35.51 g.
  (Squares print 4 layers / 0.64 mm at this layer height.)
- Matte white PLA, P1S stock identities, round-trip re-slice checks ON passed.

## Profile choices / compromises
- No brim and no ironing, by design: anything that pins the squares down or
  presses them flat afterwards would hide exactly what the map is measuring.

## Gallery
images/ are the Studio plate render of the Standard profile + crops — renders,
labelled as such in the listing copy until Scott prints it.
