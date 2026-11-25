# TEST — Fuzzy Skin Sampler — pack

Status: BUILT Nov 22, 2026 (Batch 2 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
Fuzzy skin hides layer lines and gives parts a cast, leather-like texture —
but how much is enough? Four identical cups on one plate, from glass-smooth
to heavy orange-peel, so the useful range can be picked by touch.

## Geometry (src/fuzzy_skin_sampler.py, src/FuzzySkinSampler_src.3mf, src/FuzzySkinSampler.stl)
- Four open-top cups: outer Ø46 mm, cavity Ø40 mm (3 mm wall), floor 3 mm,
  height 42 mm, watertight.
- A flat label plate (36 x 12 x 2 mm) in front of each cup, engraved OFF /
  0.06 / 0.12 / 0.18. Labels are separate objects with no overrides, so they
  always print smooth and stay readable.
- The STL in src/ is a merged reference copy; the build source is the
  multi-object scene 3MF.

## The variable — per-object slicer settings (NOT geometry)
Per-object overrides (ironing-coupon mechanism); everything else identical:
0.20 mm Standard, 3 walls, 15% grid, matte white PLA, supports off, ironing
off (ironing would smooth the very texture being tested).
- CUP_OFF: fuzzy_skin none (stock values, stated explicitly)
- CUP_006: fuzzy_skin external, thickness 0.06 mm, point distance 0.12 mm
- CUP_012: fuzzy_skin external, thickness 0.12 mm, point distance 0.12 mm
- CUP_018: fuzzy_skin external, thickness 0.18 mm, point distance 0.12 mm
Thickness ladder and point distance follow the Nov 22 design-techniques
research (0.12 mm point distance; 0.06 subtle – 0.18 heavy). "Standard" is
the 0.12 mm middle step. Fuzzy applies to external walls only, so cup
insides stay smooth as a built-in control.

## Verification (variants MUST differ, and they do)
- Readback of the finished file: every cup carries its exact fuzzy values
  through pass 1, the per-object re-slice AND the finish step
  (build_results.json: final_readback).
- Gcode evidence, z 20–21 mm band of the finished file, per cup —
  extrusion length / segment count: OFF 2,624 mm / 890 · 0.06 → 3,604 / 2,203
  · 0.12 → 3,747 / 3,851 · 0.18 → 3,895 / 4,676. Monotonic in both: the
  displaced wall path gets longer and far more segmented as thickness rises.
- Round-trip re-slice with checks ON passed; stock identities; thumbnails in.

## Profile (profiles/, finish-stepped)
- FuzzySkinSampler_Standard_P1S.3mf — one profile only, by design: the
  comparison lives on the plate. Verified slice: 2 hr 53 min - 104.60 g
  (fuzzy toolpaths are slow — thousands of extra segments per layer).

## Gallery
images/ are the Studio plate render of the profile + crops — renders,
labelled as such in the listing copy until Scott prints it.
