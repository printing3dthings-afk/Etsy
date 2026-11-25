# TEST — Layer Height Comparison Set — pack

Status: BUILT Nov 22, 2026 (Batch 2 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
Layer height is the oldest quality-vs-time trade in printing. One part with
every kind of surface — a curved dome, a sloped frustum, flat tops and fine
engraved text — sliced at five layer heights with everything else held
constant, so the trade can be read surface by surface.

## Geometry (src/layer_height_token.py, src/LayerHeightToken.stl)
- Single revolved profile, Ø64 mm, 24.7 mm tall, watertight: base disc
  3 mm, frustum slope r22 → r14 over z 3–11 mm, hemisphere dome r14 on top.
- Fine detail: "FINE 123" engraved 0.6 mm deep, 2.8 mm tall, on the flat
  top annulus of the base.

## The variable — layer height ONLY
All five profiles are built from the same stock 0.20 mm Standard process
preset with only layer_height changed (the stock print_settings_id is kept
for all five — the profile names carry the layer height). Everything else
is literally identical: 3 walls, 15% grid infill, first layer 0.20 mm,
matte white PLA, supports off, ironing off — ironing would polish the top
surfaces and confound the comparison, so it stays off on all five.

## Profiles (profiles/, finish-stepped, plate thumbnails in all)
Verified slices (time falls monotonically as layers thicken):
- LayerHeightToken_LH008_P1S.3mf — 0.08 mm — 38 min 14 sec - 13.38 g
- LayerHeightToken_LH012_P1S.3mf — 0.12 mm — 27 min 22 sec - 13.52 g
- LayerHeightToken_LH016_P1S.3mf — 0.16 mm — 22 min 13 sec - 13.79 g
- LayerHeightToken_LH020_P1S.3mf — 0.20 mm — 18 min 38 sec - 13.39 g
- LayerHeightToken_LH028_P1S.3mf — 0.28 mm — 16 min 49 sec - 14.86 g
Each file's exported project_settings was read back: layer_height matches
its profile name, all other checked settings identical across the five.
Round-trip re-slices with checks ON passed for all five.

## Profile choices / compromises
- This model is the exception to the Standard + Optimized pairing (PLAN.md):
  its five profiles ARE the comparison.
- Weights vary slightly and non-monotonically (13.38–14.86 g) — surface
  shell quantisation at different layer heights; reported as sliced.

## Gallery
images/ are the Studio plate render of the 0.20 mm profile + crops —
renders, labelled as such in the listing copy until Scott prints it.
