# Nesting Cats — printing notes

2026-10-28. Five kawaii cats that screw apart at the belly, each one hiding
the next. They're drawn to match the concept render you picked
(`concepts/form1_egg_cat.png`), with a belly seam, as you chose.

| cat | height | body colour | file |
|---|---|---|---|
| 1 | 90 mm | lavender `#B9A6D6` | `cat0.3mf` |
| 2 | 72 mm | pink `#EFB3C6` | `cat1.3mf` |
| 3 | 57 mm | mint `#A9DCC8` | `cat2.3mf` |
| 4 | 43 mm | peach `#F2C99A` | `cat3.3mf` |
| 5 | 28 mm | sky blue `#A9CDEB` | `cat4.3mf` (solid, doesn't open) |

**One 3MF per cat, one plate each.** Cats 1–4 have the bottom and the top
side by side. The smallest cat is one solid piece. Every file is already set
up for the AMS in four colours:

| AMS slot | colour | used for |
|---|---|---|
| 1 | the cat's body colour | the body (bottom and top) |
| 2 | cream `#F7F1E3` | the scarf, its tail, the paws |
| 3 | dark brown `#4A2A30` | the eyes and nose |
| 4 | pink `#F08FA0` | the cheeks |

Only slot 1 changes from cat to cat. If you'd rather print in one colour,
set every part to the same filament. The face, scarf and paws are raised,
so they still read in one colour.

## Print settings

- PLA, Bambu Studio **0.20mm Standard**, 0.4 nozzle, textured or smooth PEI.
- **Supports OFF.** None of the nine prints needs any. Each was sliced with
  supports on: 0 support moves on every one.
- Leave the orientation as it is in the file. The bottom stands on its foot.
  The top stands on its rim, the right way up, so the ears print as they
  look. Inside, its hollow narrows at 40° to a small flat ceiling the printer
  bridges.
- **Don't scale.** The threads are sized in millimetres. A scaled cat won't
  screw onto its own bottom.
- Rough times, top half only (from the slicer I check with, not Bambu
  Studio, so the AMS's own colour-change purges will add to it): about
  3 h 40 min, 2 h 50 min, 2 h 20 min, 1 h 50 min, and 1 h 25 min for the
  solid one.
  The bottoms are one colour and quicker.

## Thread clearance: provisional

The thread uses **0.3 mm** clearance, the middle value on the fit test
plate. If the plate shows a different value works on your printer (say 0.2
or 0.4), tell me and I'll rebuild all five. It's one number in
`nesting_cats.scad` (`CLR`), then `./build.sh`.

## Putting them together

Screw each top onto its bottom clockwise, like a jar lid. It's an ordinary
right-hand thread, pitch 3 mm, about one and two-thirds turns. The cats are round below the head, so there's no face to
line up. To nest them, open a cat, stand the next smaller one closed on its
floor, and screw the top back on.

## What was checked before this was pushed

- **Product gate:** all 9 prints PASS (4 bottoms, 4 tops, the solid cat):
  watertight, walls ≥ 1.2 mm, flat base, stable, no supports.
- **Fits, from the exported parts** (`check_cats.py`):
  - Each top screwed onto its bottom, and at four points on the way down:
    0 mm³ overlap.
  - Each closed cat stood inside the next bigger one: 0 mm³ overlap,
    ears included.
  - Each cat's widest point against the neck it has to pass through:
    2.31 / 1.11 / 0.60 / 0.84 mm of room all round.
- **Print fidelity** (`tools/print_fidelity.py`, every colour part): no
  detail dropped, filled in, or printed in the wrong colour above the
  reporting floor on any of the nine. The as-printed still of the 72 mm top
  (`images/nesting_cats_72mm_top_as_printed.png`, rendered from the toolpath)
  shows the face, scarf and paws intact.
- **Fragility** (`tools/fragility.py`): no slender parts on any of the nine
  (0 high, 0 watch).
- The maker's mark is engraved 0.5 mm deep under the four largest cats.
  The 28 mm cat's foot is too small for 4.4 mm letters.

## Where it differs from the concept, and why

- **The seam is at the belly**, not under the scarf. Each cat has to pass
  through the opening of the one outside it, and only at the widest point is
  that opening big enough for five sizes.
- **The ears lean 40°**, not the concept's 68°, so they print without
  support. They're also a little shorter (0.13 of the height, not 0.17), so
  each cat's ears clear the ceiling of the cat outside it.
- **The scarf's underside is a 50° cone**, not a round tube, so it prints
  without support. Seen from the front, it still looks like the concept's
  round scarf.
- **The eyes, nose, cheeks and paws have flat fronts**, raised on sloped
  skirts that let them print. The nose and cheeks lean back with the head,
  so their skirts barely show. The eyes and paws stand upright: leant, the
  slicer needed supports under the eyes, and the paws looked sunk in.
- **The smallest cat is 28 mm**, not 30. The thicker thread wall the gate
  needed left a 30 mm cat only 0.10 mm of room through the 43 mm cat's neck.
  At 28 it has 0.84.

## Renders

`images/nesting_cats_lineup.png` is the set as in the concept: the largest
opened, the rest closed. `images/nesting_cats_72mm_*.png` is the 72 mm cat
from three sides. These are design-review renders from the real parts, not
listing photos. The 72 mm top is also in the print viewer.

## Rebuilding

`./build.sh` exports every part, runs the fit check and writes the five
3MFs. `./gate_cats.sh` runs the product gate. `python3 render_cats.py --each`
renders the line-up and the 72 mm cat in three views into `images/`. The
STLs aren't committed (193 MB as text). Every part is in the 3MFs, and
`build.sh` remakes them.
