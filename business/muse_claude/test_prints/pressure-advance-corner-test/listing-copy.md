# TEST - Pressure Advance Corner Test

**Title (MakerWorld, <= 50 chars):** TEST - Pressure Advance Corner Test

**What it tests:** pressure advance (linear advance / K value) - the
setting that keeps corners sharp at speed. Two hollow square towers
(44 mm and 26 mm, walls 2.4 mm, 40 mm tall) with dead-sharp 90-degree
corners on a shared base: too little advance and each corner bulges
out fat; too much and the corner starves thin and the wall after it
runs under-extruded.

**Why ONE profile, honestly:** on Bambu printers, pressure advance is
NOT a slicer setting - it lives in the printer's own calibration (the
K value stored on the machine / set in the device page or the
filament's calibration result). We probed embedding it in the file
anyway: the values land in the 3MF config, but the sliced toolpath
comes out byte-identical - Bambu Studio itself notes the setting is
"useless for Bambu printers" because the firmware applies it. So this
pack ships ONE Standard profile and the ladder below; anyone who
sells you a "PA test file with the values baked in" for a Bambu is
selling theatre.

**The test:** print the tower three times, setting the K value before
each print (device calibration / filament dialog on the printer):
K = 0.00, then 0.02, then 0.04. Mark each print's base with its K.
Compare the corners at mid height: measure or eyeball the bulge, and
check the wall right after each corner for starvation.

**Record your results:**

| K value | Corner bulge | Post-corner wall | Verdict |
|---|---|---|---|
| 0.00 |  |  |  |
| 0.02 |  |  |  |
| 0.04 |  |  |  |

**Profile in this pack:**

- Standard: 0.20 mm Standard - verified slice 55 min 15 sec - 50.27 g.

**Filament:** matte white PLA, single colour. **Ironing: OFF.**
Supports off.

**Per-profile copy (paste into the profile's description box):**

Prints the Pressure Advance Corner Test: two hollow square towers
(44 mm and 26 mm, 2.4 mm walls, 40 mm tall) with sharp 90-degree
corners on an engraved base. Matte white PLA, 0.20 mm Standard,
3 walls, 15% infill, supports off, no ironing. Verified slice:
55 min 15 sec - 50.27 g. Print it three times, setting K = 0.00 / 0.02 / 0.04 on
the printer before each print (PA is a printer-side calibration on
Bambu machines - it cannot be baked into a print file; see the model
description for the probe evidence), and compare the corners.
