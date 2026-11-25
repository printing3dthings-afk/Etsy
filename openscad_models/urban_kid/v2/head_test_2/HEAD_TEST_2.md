# Urban Kid v2: head test 2, printed upright (2026-11-21)

## What test 1 showed (Scott's photos, `../head_test/photos/`, 2026-11-21)

Test 1 was printed face up, at 0.12 mm.

**What worked:**
- The face reads as the sly smile.
- The ears came out clean.
- The V brows and the crease between them both show.
- The lip line and the smile's high corner read.
- The iris ring shows on one eye.
- The flat back on the textured plate is clean.

**What didn't:**
- **Contour rings over the whole face.** Face up, every cheek and the forehead is a nearly flat
  slope to the nozzle, so each 0.12 mm layer step shows as a ring, like a topo map. The
  as-printed render showed the rings, but much fainter than the real print.
- **A small nub on every high point:** the brow centre, the nose tip, both lips, the chin and one
  cheek. Each peak finishes as a tiny island of top surface.
- **A seam line down the middle** of the forehead and chin. The aligned seam lands there.
- **One eye came out grainy** around the lid fold.

## Test 2

The same head, the same STL, stood upright on its neck. The face is now a near-vertical wall, so
the layer lines run across it as fine horizontal lines, the way busts are usually printed.

**Settings:**
- 0.08 mm Extra Fine, 3 walls, 15% infill.
- Organic tree supports.
- Seam at the back, on the flat cut.

**Where the supports touch** (read from the gcode):
- Under the jaw and the backs of the ears only, up to 16.5 mm high.
- None touch the front of the face.

**About 1 h 7 m and 13.3 g** (Bambu Studio's own estimate).

**File:** `urban_kid_v2_head_test_2_upright.gcode.3mf` (P1S, 0.4 nozzle, PLA Basic, textured
PEI).

**Mesh:** `../head_test/urban_kid_v2_head_test.stl`, rotated so the crown is +Z and the face
-Y (x, y, z -> x, -z, y), then dropped to z = 0. The base is the neck cut, about 248 mm².

## What to compare with test 1
- Are the contour rings gone from the cheeks and forehead?
- Are the nubs gone from the nose, lips and chin?
- Do the lids, pupils and irises come out crisper or softer than test 1? Upright, the brows
  overhang the eyes.
- Are there marks under the chin and behind the ears where the supports came off?

## Scott's decision (2026-11-25): both print options
"Urban kid will have both print options." So v2 ships as:
- **a split colour kit**, like v1 (each print one colour, pegged together);
- **one piece**, printed upright on organic tree supports.

This test is the one-piece option's face, printed the way that version prints. Its result
(rings gone or not, nubs gone or not, lids crisp or soft) sets how the head is printed in both
versions. Test 1 showed that face up prints contour rings.
