# TEST — Magnet Pocket Fit Test — pack

Status: BUILT Nov 22, 2026 (Batch 3 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
One print finds the press-fit pocket clearance for the five magnet sizes
the shop actually uses, instead of the generic "+0.4 mm" rule of thumb.

## Geometry (src/magnet_pockets.py, src/MagnetPocketFitTest.stl)
- Plate 110 x 108 x 5 mm, blind pockets from the top. Rows = sizes:
  6x2, 6x3, 8x2, 10x2 round + 10x5x2 bar. Columns = clearance ladder
  +0.2 / +0.3 / +0.4 / +0.5 mm over nominal (both dimensions for the bar).
- Pocket depth = magnet height + 0.2 mm (2.2 / 3.2 / 2.2 / 2.2 / 2.2);
  thinnest floor under the deepest pocket is 1.8 mm.
- Row labels (6X2 … BAR) and column labels (+0.2 … +0.5) engraved on the
  plate top.
- Mesh-verified (verify_batch3.py): all 20 pockets measure within 0.005 mm
  of design diameter/dimensions in section; depths ray-cast exact.
- Magnets not included — Scott supplies his own; the copy says so and
  tells him to caliper his magnets first (batch variation is real).

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- MagnetPocketFitTest_Standard_P1S.3mf — 0.20 mm Standard @BBL X1C, 3 walls, 15% grid,
  supports off, ironing off. Verified slice: 54 min 08 sec - 39.60 g.
- MagnetPocketFitTest_Optimized_P1S.3mf — 0.16 mm Optimal @BBL X1C, 3 walls, 12% gyroid,
  supports off, ironing off. Verified slice: 1 hr 12 min - 43.97 g.
- Both: matte white PLA (Bambu PLA Matte @BBL P1S 0.4 nozzle), printer Bambu Lab
  P1S 0.4 nozzle, round-trip re-slice with checks ON passed. Pocket sizes
  IDENTICAL in both — layer height is the only variable.

## Profile choices / compromises
- Ironing OFF (Batch 1 hole-ladder precedent): an ironing pass can lip a
  pocket mouth, and the pocket mouths are the fit surface being measured.
  The plate top is a customer-facing-style flat, but the measurement wins.
- Bar pockets have square corners (the magnets are square-cornered); the
  slicer's line width rounds them slightly in practice — same for both
  profiles, and the ladder absorbs it.

## Gallery
images/ are the Studio plate render of the Standard profile + centre/corner
crops — renders, labelled as such in the listing copy until Scott prints it.
