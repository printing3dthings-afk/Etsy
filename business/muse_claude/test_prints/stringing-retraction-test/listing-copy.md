# TEST - Stringing / Retraction Test

**Title (MakerWorld, <= 50 chars):** TEST - Stringing Retraction Test

**What it tests:** stringing - the fine hairs a hot end drags between
features - and whether a longer retraction actually cures it. Twelve
slim tapered pins (base 5.2 mm, tip 2.2 mm, 30 mm tall) stand on a
132 x 96 mm base in four rows of three; within a row the pin spacing is
graded 14 / 24 / 34 / 44 mm (engraved at the front of each row), so each
row is a longer set of un-retracted-looking travel moves than the last.

**How to judge:** print the Standard profile and inspect row by row:
which gaps grow hairs, which stay clean? Then print the Retraction 1.0
profile and compare the same rows side by side. If the longer retraction
changes nothing, your stringing is coming from temperature or wet
filament, not retraction - that is a result too.

**Record your results:**

| Profile | GAP 14 | GAP 24 | GAP 34 | GAP 44 |
|---|---|---|---|---|
| Standard (0.8 eff.) |  |  |  |  |
| Retraction 1.0 |  |  |  |  |

(clean / light hairs / heavy strings)

**Profiles in this pack:**

- Standard: stock matte PLA preset - verified slice 1 h 2 min - 36.46 g. Its
  retraction is the preset default (0.8 mm effective; the config value
  is unset/'nil', the printer default applies).
- Retraction 1.0: identical except filament retraction length set to
  1.0 mm - verified slice 1 h 3 min - 36.46 g. The override is verified in the
  file's config AND in its gcode (retract moves read E-1.0 against
  E-0.8 stock).

**Filament:** matte white PLA, single colour. **Ironing: OFF.**
Supports off - the pins are the test, supports would hide the result.

**Per-profile copy (paste into each profile's description box):**

Prints the Stringing / Retraction Test: twelve tapered pins (30 mm
tall) in four rows at 14 / 24 / 34 / 44 mm spacings on a 132 x 96 mm
base, spacings engraved on the base. Matte white PLA, 0.20 mm Standard,
3 walls, 15% infill, supports off, no ironing. Verified slice:
1 h 2 min - 36.46 g. Stock retraction (0.8 mm effective). Count the strings per
row - then print the Retraction 1.0 profile and compare.

Prints the Stringing / Retraction Test: twelve tapered pins (30 mm
tall) in four rows at 14 / 24 / 34 / 44 mm spacings on a 132 x 96 mm
base, spacings engraved on the base. Matte white PLA, 0.20 mm Standard,
3 walls, 15% infill, supports off, no ironing. Verified slice:
1 h 3 min - 36.46 g. Identical to Standard except retraction length 1.0 mm
(verified in config and gcode). Compare the rows against your Standard
print - same rows, one variable changed.
