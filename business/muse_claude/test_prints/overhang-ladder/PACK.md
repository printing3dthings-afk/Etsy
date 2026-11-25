# TEST — Overhang Ladder — pack

Status: BUILT Nov 22, 2026 (Batch 1 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
Find the steepest downward face your printer/filament/cooling can print cleanly
with no supports. Six fin blocks carry test undersides at 30-80 degrees from
vertical; the first angle that sags, curls or strings is your limit.

## Geometry (src/overhang_ladder.py, src/OverhangLadder.stl)
- Base plate 170 x 46 x 4 mm; six fins 24 wide x 25 deep x 48 tall on top
  (overall 170 x 46 x 52 mm), watertight single solid.
- Each fin has a triangular notch cut from its front-bottom corner; the notch's
  sloped face is the test underside at 30 / 40 / 50 / 60 / 70 / 80 degrees from
  vertical (notch rise H = 25 / tan(angle): 43.3 mm at 30 deg down to 4.4 mm at
  80 deg). Angle engraved on each fin's top face.

## Design history (read before editing)
- V1 fins were free-hanging triangles resting on the base along a knife edge.
  Bambu Studio REFUSES to slice them (error -100, "slicing or export error"):
  the fin cross-section grows from a zero-width edge, producing degenerate
  layers. Five attempts all failed the same way; bisection isolated it to the
  standing-wedge geometry. The notched-block V2 keeps every fin flat-footed —
  slices cleanly. Do not revert to hanging fins.

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- OverhangLadder_Standard_P1S.3mf — 0.20 mm Standard, 3 walls, 15% grid,
  supports off, ironing off. Verified slice: 1 hr 53 min - 86.69 g.
- OverhangLadder_Optimized_P1S.3mf — 0.16 mm Optimal, 3 walls, 12% gyroid,
  supports off, ironing off. Verified slice: 3 hr 02 min - 89.17 g.
- Matte white PLA, P1S stock identities, round-trip re-slice checks ON passed.

## Profile choices / compromises
- This is the heavy coupon of the batch: the fins are solid blocks (the notch
  design that slices), so it uses ~87-89 g. It is a one-time calibration print
  per filament, not a repeat consumable.
- Ironing off: the measured surfaces are undersides; the fin tops carry only
  the labels. Optimized's 0.16 mm layers are the quality lever — thinner layers
  genuinely print cleaner overhangs, so the two profiles double as an A/B read.

## Gallery
images/ are the Studio plate render of the Standard profile + crops — renders,
labelled as such in the listing copy until Scott prints it.
