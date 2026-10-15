# Haunted Town — raised-letter sign test

A quick test print of the four shop signs with their new **raised letters**,
to check in real filament that they read before printing a whole building.

Made 2026-10-07. The first post office print (2026-10-06, one colour) showed
the old carved letters were hard to read: the two F's looked like E's. Scott
asked for raised letters on every sign, and for this test.

**Print this:** `haunted_town_sign_test.3mf`. It has four separate objects on
one plate, one per sign. Delete any you don't want.

| piece | letters | slicer estimate | filament |
|---|---|---|---|
| POST OFFICE | 4.4 mm tall | 24 min | 3.4 g |
| BAKERY | 5.2 mm | 20 min | 2.9 g |
| MERCANTILE (general store) | 5.2 mm | 28 min | 4.3 g |
| UNDERTAKER | 4.0 mm, the smallest | 22 min | 3.1 g |

Times are the PrusaSlicer estimate with the P1S profile, one piece at a time.
Bambu Studio will give its own number.

- **Supports off.** Print standing up, as they sit in the file. 0.2 mm layers.
- **One colour.** White shows the worst case, since the letters must read by
  their shadow alone. If they read in white, they read in any colour.

## What each piece is

Each piece is that building's real sign: the board and its letters come from
the building's own `.scad` (`sign_board()` and `sign_letters()`), in the same
place, tilt and lean as on the building. So the test prints exactly what the
building will. Behind the sign is a plain slab of wall, 2 mm round the board,
standing on a 1.2 mm foot. The real walls' brick and clapboard are left off,
because the letters are what is being tested.

`sign_test_<building>.scad` builds each piece; open it in OpenSCAD with the
repo's BOSL2 path to rebuild.

## Checked before shipping

- Each piece sliced with supports off: **0 support moves, 0 overhang
  perimeters**, full height.
- `print_fidelity` on the POST OFFICE and UNDERTAKER pieces (the two with the
  smallest letters): **nothing dropped**, nothing flagged. Every letter
  prints as drawn.
- `product_gate` fails each piece's thin-wall check, and that is expected
  here: almost all of each piece is letters, and letter strokes are under the
  1.2 mm floor by nature (the same strokes are 0.2–0.3% of a whole building,
  where the gate passes). The slicer and the fidelity check above are the
  real test of them.

## What to look for

- Do the F's read as F's, and the E's as E's?
- Are the holes in O, P, R, A and B open?
- Do the smallest letters (UNDERTAKER) read at arm's length?

If any don't, tell Claude which letters, and a photo if you can.

`sign_test_render.png` is a render of the four pieces, not a photo of a print.
