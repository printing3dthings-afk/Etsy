TEST - Pressure Advance Corner Test - upload pack (PRIVATE until Scott prints it)

Profile (verified end-to-end: pass1 -> finish -> strict -> round-trip):
- PACornerTest_Standard_P1S.3mf - 55 min 15 sec - 50.27 g

Gallery: images/01-plate.png (plate render from the Standard file) +
02-centre-crop.png + 03-corner-crop.png. Renders, not photos - swap in
Scott's real print photos after he prints them.

Copy: listing-copy.md (model description + per-profile copy).

Notes: SHIPPED IN REDUCED FORM, deliberately - one profile instead of
three. Probe evidence (../probe/): the PA override lands in config
(enable_pressure_advance / pressure_advance read back fine) but emits
no M900 / SET_PRESSURE_ADVANCE and leaves the extrusion path
byte-identical to stock; Bambu applies PA in firmware. The copy says
so plainly and gives the 0.00 / 0.02 / 0.04 ladder to set per print.
