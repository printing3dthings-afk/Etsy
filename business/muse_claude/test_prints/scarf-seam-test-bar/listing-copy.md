# TEST - Scarf Seam Test Bar

**Title (MakerWorld, <= 50 chars):** TEST - Scarf Seam Test Bar

**What it tests:** the seam - where every layer starts and stops - in
its three slicer treatments. Two smooth curved solids with nowhere for
a seam to hide: a 36 mm diameter cylinder (45 mm tall) and an 18 mm
capsule bar with a hemispherical top. No corners, no texture: whatever
ridge, scar or scatter you see IS the seam treatment.

**The three profiles (the profiles ARE the test):**

- **Aligned** - stock seam placement: one vertical seam line.
  Verified slice 25 min 39 sec - 23.44 g.
- **Random** - seam position randomised per layer: no line, but a
  speckle of start/stop points over the whole surface.
  Verified slice 28 min 4 sec - 23.44 g.
- **Scarf** - scarf joint seam ON (the filament preset's scarf seam
  type set to "all", verified in the file's config): the seam is laid
  down as a long shallow overlap instead of a step. Verified slice
  29 min 55 sec - 23.45 g.

Measured from the shipped files' gcode (extruding segments in a
20-22 mm height band): Aligned 271 segments / 4329.0 mm of extrusion path; Random 426 segments / 4371.5 mm of extrusion path; Scarf
2317 segments / 6177.1 mm of extrusion path - the scarf profile's seam zone really is sliced
differently, not just labelled differently.

**How to judge:** print all three in the same filament, then run a
fingertip around each cylinder at mid height and look at it under a
low-angle light. Score the seam's visibility and feel per profile;
check the capsule's dome too - curved-in-two-directions surfaces are
where scarf joints earn their keep.

**Record your results:**

| Profile | Seam visible? | Fingertip feel | Dome read | Verdict |
|---|---|---|---|---|
| Aligned |  |  |  |  |
| Random |  |  |  |  |
| Scarf |  |  |  |  |

**Filament:** matte white PLA, single colour. **Ironing: OFF** - the
surface is the measurement. Supports off.

**Per-profile copy (paste into each profile's description box):**

Prints the Scarf Seam Test Bar (ALIGNED): a 36 mm cylinder and an
18 mm capsule bar, smooth curved solids that give the seam nowhere to
hide. Matte white PLA, 0.20 mm Standard, 3 walls, 15% infill, supports
off, no ironing. Seam position: aligned (stock). Verified slice:
25 min 39 sec - 23.44 g. Print all three profiles and compare the seam line.

Prints the Scarf Seam Test Bar (RANDOM): a 36 mm cylinder and an
18 mm capsule bar, smooth curved solids that give the seam nowhere to
hide. Matte white PLA, 0.20 mm Standard, 3 walls, 15% infill, supports
off, no ironing. Seam position: random (verified in config). Verified
slice: 28 min 4 sec - 23.44 g. Print all three profiles and compare the surface.

Prints the Scarf Seam Test Bar (SCARF): a 36 mm cylinder and an
18 mm capsule bar, smooth curved solids that give the seam nowhere to
hide. Matte white PLA, 0.20 mm Standard, 3 walls, 15% infill, supports
off, no ironing. Scarf joint seam ON via the filament preset (verified
in config; its gcode lays the seam down as ~8x more, shorter segments
than Aligned in the measured band). Verified slice: 29 min 55 sec - 23.45 g. Print
all three profiles and compare.
