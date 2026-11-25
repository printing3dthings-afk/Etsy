# FACTS: Christmas trinket trays, v1

Every number comes from this folder (STANDARDS 15). The source is on each line.

## Version
- **v1**, built 2026-11-24 (`tray_set.py`).
- **Scott's picks:**
  - the direction, from his examples: a rippled frame with a smooth insert in a second colour;
  - then all four recommendations: six more shapes, raised detail, two sizes, a thumb scoop.
- **Not printed yet.** Every image is a design-review render, not a photo.
- **Not listed anywhere yet.** Free or paid, and where, is Scott's call.

## What it is
- **A set is two prints:** a frame with a rippled outer wall, and a smooth insert that drops
  inside it.
- **Two-tone without an AMS:** each piece prints in one colour, and you pick the two colours.
- **The insert's floor carries raised detail.** A thumb scoop in the frame's rim lets a finger
  lift the insert out.
- **Twelve shapes, all our own outlines:** star, tree, mitten, bauble, bell, gingerbread,
  snowman, stocking, gift box, snowflake, Santa hat, gingerbread house.

## Numbers
| what | value | source |
|---|---|---|
| Frame | floor 1.6, wall 3.2 inside the ripples, rim 14 mm | `README.md`, `tray_set.py` |
| Insert | wall 1.6, rim 0.8 below the frame's; 0.4 clearance all round | `tray_set.py` (`INSERT_WALL`, `CLEAR`) |
| Raised detail | lines 1.6 wide, 0.8 proud | `tray_set.py` (`DET_W`, `DET_H`) |
| Thumb scoop | rim dips to 5 mm, over 22 mm (large) or 18 mm (small) | `README.md` |
| Large size | 148–196 mm on the long side | `README.md` table |
| Small size | the frame 110 mm on its long side; walls, floors, heights and detail keep their sizes | `tray_set.py` (`SMALL_MAX`) |

## Print time and filament
- **Bambu Studio's own slice:** P1S 0.4, matte PLA, Standard, ironing on flat tops, no
  supports.
- **Every part has its time and grams:** in the tables in `README.md`, and in `slices/`.
  - fastest set: small snowman, 1 h 38 m, 37 g;
  - largest: large snowflake, 6 h 33 m, 148 g.

## Checks
- **Product gate:** all 48 parts pass (`checks/gate_*.txt`).
- **Fragility:** 0 on every set (`checks/fragility_*.txt`).
- **Print fidelity:** on the small gingerbread insert, the finest detail. One flag, 0.06 mm³ at a
  wrist zigzag's inside point; not visible, left as drawn
  (`checks/fidelity_gingerbread_small_insert.txt`).

## Safe to say, word for word
- "Twelve Christmas trinket trays, each a rippled frame and a drop-in insert."
- "Print the frame and insert in two colours: no AMS needed."
- "Two sizes, and a thumb scoop to lift the insert out."
- "No supports."

## Don't say
- That it's printed, tested or food-safe. Not printed yet, and PLA trays aren't sold as
  food-safe.
- Any print time or weight that isn't in `README.md`'s tables.
- That the shapes come from anyone else's design. They're ours. No shape is joined to a
  rectangle: that layout is another maker's MakerWorld exclusive.

## Media (all renders)
| file | shows |
|---|---|
| `images/tray_sheet_large.jpg`, `images/tray_sheet_small.jpg` | all twelve, each size |
| `images/<shape>_set.png`, `images/<shape>_small_set.png` | one set, frame and insert |
