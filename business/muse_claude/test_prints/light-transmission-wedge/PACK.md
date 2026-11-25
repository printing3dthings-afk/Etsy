# TEST — Light Transmission Wedge — pack

Status: BUILT Nov 22, 2026 (Batch 1 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
The companion to the Window Glow Coupon: instead of flat panes in a frame, this
is a stepped wedge you slide across a phone flashlight or tea light to compare
how much light each wall thickness passes — the numbers behind lampshade,
lithophane and tea-light diffuser design.

## Geometry (src/transmission_wedge.py, src/LightTransmissionWedge.stl)
- Six steps, each 22 mm wide x 44 mm deep, thicknesses 0.8 / 1.2 / 1.6 / 2.0 /
  2.4 / 3.0 mm, overall 132 x 44 mm, watertight single solid.
- Each tread engraved with its thickness (0.45 mm deep — shallow so the thin
  steps keep a printable floor: the 0.8 mm step keeps ~0.35 mm under the digits).

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- LightTransmissionWedge_Standard_P1S.3mf — 0.20 mm Standard, 3 walls, 15% grid,
  supports off, ironing off. Verified slice: 17 min 55 sec - 11.99 g.
- LightTransmissionWedge_Optimized_P1S.3mf — 0.16 mm Optimal, 3 walls, 12%
  gyroid, supports off, ironing off. Verified slice: 20 min 31 sec - 12.87 g.
- Matte white PLA, P1S stock identities, round-trip re-slice checks ON passed.

## Profile choices / compromises
- Ironing OFF on both, on purpose: ironing densifies the top skin and would
  change the light transmission being measured. Settings are identical in
  spirit across both profiles so the comparison stays about thickness.
- Infill note for the listing: at these thicknesses the steps print mostly as
  shell (5 top / 3 bottom layers at 0.20 mm), so results transfer to printed
  walls and diffuser sleeves of the same thickness.

## Gallery
images/ are the Studio plate render of the Standard profile + crops — renders,
labelled as such in the listing copy until Scott prints it.
