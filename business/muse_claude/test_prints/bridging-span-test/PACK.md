# TEST — Bridging Span Test — pack

Status: BUILT Nov 22, 2026 (Batch 1 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
How far can your printer bridge before the strands sag? Six labelled spans
from 10 to 60 mm on one plate give the working limit for designing lids,
windows and horizontal holes.

## Geometry (src/bridging_test.py, src/BridgingSpanTest.stl)
- Base plate 158 x 66 x 3 mm; two rows of four posts (6 x 12 mm footprint,
  11 mm tall on the base), watertight single solid.
- Bridge bars 5 mm wide x 3 mm thick at 14 mm above the base, spanning:
  front row gaps 10 / 30 / 50 mm, back row gaps 20 / 40 / 60 mm. Bars run
  post-centre to post-centre so each span is fully supported at both ends.
- Each span engraved on the base in front of its gap.

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- BridgingSpanTest_Standard_P1S.3mf — 0.20 mm Standard, 3 walls, 15% grid,
  supports off, ironing off. Verified slice: 50 min 42 sec - 36.04 g.
- BridgingSpanTest_Optimized_P1S.3mf — 0.16 mm Optimal, 3 walls, 12% gyroid,
  supports off, ironing off. Verified slice: 1 hr 07 min - 40.33 g.
- Matte white PLA, P1S stock identities, round-trip re-slice checks ON passed.

## Profile choices / compromises
- Supports off by design (the test IS unsupported spanning). No brim: posts
  sit on a full base plate. Ironing off: the measured surfaces are the bridge
  undersides; Optimized's finer layers are the quality lever.

## Gallery
images/ are the Studio plate render of the Standard profile + crops — renders,
labelled as such in the listing copy until Scott prints it.
