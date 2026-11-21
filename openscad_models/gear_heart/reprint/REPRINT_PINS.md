# Gear Heart v2: re-print the 15 axle pins (2026-11-21)

**What happened.** Scott printed `gear_heart_gears_v2.3mf`:
- All 15 gears came out clean.
- The 15 axle pins, lying in two columns at the back right of the plate, came loose and turned
  into spaghetti (`../real/v2_gears_plate_pins_failed_2026-11-21.jpg`).

Scott's P1S timelapse of that print (`../real/v2_gears_timelapse_2026-11-21.mp4`, 71 frames) shows
when: the pins' first layers went down clean (frame 2), and by frame 8 of 71 the pins at the far
back right were already loose and tangling, while the gears in front carried on and finished.

The same pins printed fine on the clip test, so the pin design isn't the suspect. The back of the
plate is:
- Scott reported one area of the plate printing badly.
- An earlier print the same day (`real_timelapses/failed_blue_spaghetti_2026-11-21.mp4`) also
  came loose at the back, from its first layers.

**The re-print.** `heart_pins_only.gcode.3mf`:
- The same 15 pins (barb 0.65, from `heart.scad` `part="pins"`), packed 5 × 3 in the middle of
  the plate, away from the back.
- A 4 mm brim, because each pin touches the plate with a thin face.
- About 38 m 45 s and 8.1 g (Bambu Studio's estimate). PLA Basic, 0.20 mm Standard, textured PEI.

**Before printing it:**
- Wash the plate with dish soap and hot water.
- Make sure "Bed leveling" is ticked when you send it.
- Run `../../calibration/first_layer_map/` first if you want to see which area is off.
