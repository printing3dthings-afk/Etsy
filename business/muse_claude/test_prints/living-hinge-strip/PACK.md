# TEST — Living Hinge Strip — pack

Status: BUILT Nov 22, 2026 (Batch 3 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
Measure what a PLA living hinge can honestly do. The copy does not oversell:
PLA hinges are fold-once / small-angle parts (the strain maths forbids
repeated 180° folds), and this strip counts 90° cycles to whitening/crack
for three web thicknesses at EQUAL design strain.

## Geometry (src/living_hinge.py, src/LivingHingeStrip.stl)
- Strip 157.6 x 24 mm, panels 2.0 mm thick, three hinge webs in series
  separated by rigid panels, end tabs with Ø6 holes.
- Webs 0.2 / 0.4 / 0.6 mm thick (1 / 2 / 3 layers at 0.20 mm). Web floor
  lengths 8 / 16 / 24 mm from ε = t·θ/(2L) with θ = 90°, ε = 2.0% →
  L = 39.27·t, so all three sit at 1.96% strain on a 90° fold — thickness
  is the only variable.
- Grooves cut from the top, 45° ramps blending web into panels (no sharp
  step to concentrate bending). Labels ("WEB 0.2" …) engraved on the
  segment after each hinge.
- The sub-1.2 mm webs are the research's named gate exception: localised,
  justified — the web is the test.
- Mesh-verified (verify_batch3.py): web min thicknesses measure exactly
  0.200 / 0.400 / 0.600 mm in section.

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- LivingHingeStrip_Standard_P1S.3mf — 0.20 mm Standard @BBL X1C, 3 walls, 15% grid,
  supports off, ironing off. Verified slice: 14 min 39 sec - 5.17 g.
- LivingHingeStrip_Optimized_P1S.3mf — 0.16 mm Optimal @BBL X1C, 3 walls, 12% gyroid,
  supports off, ironing off. Verified slice: 17 min 18 sec - 5.01 g.
- Both: matte white PLA (Bambu PLA Matte @BBL P1S 0.4 nozzle), printer Bambu Lab
  P1S 0.4 nozzle, round-trip re-slice with checks ON passed.

## Profile choices / compromises
- Ironing OFF: the ironing pass runs over the hinge webs (they are
  top-facing thin features) and would change their effective thickness.
- Layer quantisation is a real confound and the copy says so: at 0.16 mm
  layers the 0.2/0.4/0.6 webs are not whole-layer counts, so the Optimized
  strip's webs slice to the nearest layer stack (~0.32/0.48/0.64 class).
  Standard is the reference print; Optimized shows what the finer profile
  does to the same file.

## Gallery
images/ are the Studio plate render of the Standard profile + centre/corner
crops — renders, labelled as such in the listing copy until Scott prints it.
