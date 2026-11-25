# Urban Kid: one piece, on tree supports

Print option 2 of 2 (Scott, 2026-11-25: "Urban kid will have both print options").
Option 1 is the split colour kit (v1: 7 prints, glued or pegged). This option is the
whole figure in one print, one colour, on Bambu's organic tree supports, to paint or
leave plain.

**Status: not test-printed.** Everything below is from the model and the slicer.

## What it is
`make_one_piece.py` joins v1's eight assembled kit parts (base, both shoes, pants,
hoodie, head, cap, chain) into one solid body and scales it to 190 mm tall.
- **Peg pockets dropped:** the kit's peg-clearance pockets end up sealed inside the
  union. They come out as 8 negative-volume shells and are dropped, so the figure is
  solid where the kit had pockets.
- **Chain seated:** in the kit the chain is glued on, standing a hair off the chest.
  Here it is moved 0.4 mm into the chest (`SEAT`), or it prints as a separate,
  floating piece.
- **v1's head**, until head test 2 decides the v2 head; then it swaps in.

Result: one body, watertight, 91.1 x 111.6 x 190.0 mm, 427.7 cm3.

## Checks
- **product_gate:** passes all but `no_unsupported_overhang`, which fails by
  design: this option is the one printed on supports. Contact with the plate is 60.8 cm2
  (59.8 % of the footprint), and the centre of mass sits over the base. Report:
  `gate.txt`.
- **fragility:** 0 high, 0 watch, 0 slender runs. Report: `fragility.txt`.
- **print_fidelity:** report in `checks/`.

## Slices (P1S 0.4, PLA Matte, Textured PEI, tree supports)
| file | layer | time | filament | of which support |
|---|---|---|---|---|
| `urban_kid_one_piece_190_standard.gcode.3mf` | 0.20 | 6 h 38 m | 213 g | 89 g |
| `urban_kid_one_piece_190_fine.gcode.3mf` | 0.12 | 9 h 54 m | 217 g | 120 g |

About 40-55 % of the filament is support. The trees land under:
- the cap's brims;
- the chin, over the hoodie collar;
- the hoodie hem and the pocketed arms;
- the hood at the back.

Those are mostly faces you look up at, so the support marks sit there, not on the face
or the OBC chain.

## Renders
`urban_kid_one_piece_190_views_*.png`: design-review renders of the mesh, not photos
or a print.
