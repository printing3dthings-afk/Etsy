# Haunted Post Office — printing notes

Building #1 of the Haunted Town series (`../HAUNTED_TOWN.md`). It is one story:
brick walls, a sagging parapet capped in cream, and a **flat roof that lifts
off**, with a leaning chimney and a crooked stove pipe on it. It is a hollow
lantern with an open base, lit from inside by a battery LED tealight.
78.9 × 64.4 × 70.9 mm; the lid is 72 × 50 mm, 34.7 mm tall with its chimney.

Redesigned 2026-09-25 to Scott's variety plan: brick walls, gable-headed
windows and a flat roof, so it shares nothing with the bakery. The earlier
two-story turret version is archived in `data/trash/`.

**Print this:** `haunted_post_office.3mf`. It is **two objects on one plate**:
the house (three colour parts) and its roof lid (one colour).

| object | part | what it is | colour in the file |
|---|---|---|---|
| house | body | brick walls, plinth, step, the lid's seat inside the parapet | brick `#7A3E33` |
| house | trim | parapet coping, window and door frames, muntins, window panes, door, sign board, the parcels' string | cream `#EFE6D2` |

**Every window is glazed** (added 2026-09-27). A 1.48 mm pane fills the back
of each opening, set into the wall all round, and the window's bars stand on
it. The tealight glows through the panes, like frosted glass. On the first
chapel print the tallest windows' free-standing bars snapped; the pane is
what carries them now. The door stays open.
| house | accent | the parcels, the raised POST OFFICE letters, the brass mail slot | kraft `#D4A96A` |

**The POST OFFICE letters stand 0.84 mm proud of the sign board** (changed
2026-10-07, after the first print: see below). They were carved 0.6 mm into
the board and lined with kraft, and in one colour the carve read poorly.
Raised, they read by their shadow on a one-colour print; in colour they are
kraft letters on cream. `../sign_test/` has a 20-minute test print of this
sign and the town's other three.
| lid | lid | flat roof, leaning chimney, stove pipe | slate `#2B2F38` |

## Settings that are not optional

- **Supports OFF** for both. Verified: 0 support moves and 0 overhang
  perimeters on each.
- **The house prints standing up. The lid prints flat, underside on the
  plate, chimney up** — exactly as they sit in the file.
- 0.2 mm layers.

## Why the roof is a separate print

A flat roof on a hollow house is a flat ceiling, and a flat ceiling can't
print without support. So the roof is its own flat slab. It drops inside the
parapet and rests on a ledge (a corbel with a 55° underside) running round
the inside of the walls. Lift it off by the chimney to switch the tealight;
the base is open too.

## Cost — sliced, not estimated

| | time | filament |
|---|---|---|
| house, single colour | 5 h 34 m | 50 g |
| lid | 1 h 36 m | 12 g |
| **single colour, both** (e.g. for Jessee to paint) | **7 h 10 m** | **~62 g** |
| **house in three colours + lid** | not reliable here | ~63 g model + purge |

The colour house makes **446 colour changes**, far fewer than the bakery's
1,351. Printed together with the lid on one plate, as the file lays them out,
it is **619 changes**: the slate lid shares its first 35 mm of layers with the
house. (Until 2026-09-26 the file put the lid on the brick slot, so a colour
print gave a brick roof. It is now on its own slate slot, number 4.) Purge is 89 g at PrusaSlicer's 140 mm³ flush, and about 194 g at the
350 mm³ Bambu default. Slice it in Bambu Studio for the real number before
pricing. A listing must say which version the buyer gets.

## The tealight

Measured on the exported mesh:
- **50.6 mm clear across from the table up to 54 mm**;
- above that, the lid's seat narrows it to 45.6 mm (from 54 to 58 mm);
- an LED tealight is at most 45 mm tall, so it sits under the seat with 9 mm
  to spare.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the house:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 70.8 of 70.9 mm;
  - flat and stable.
- `product_gate` **PASSED** on the lid:
  - 2.5 mm walls;
  - 0 supports;
  - 100% flat on the plate.
- `mesh_gate` on all four parts:
  - all four are closed, watertight surfaces;
  - body and lid: **0 zero-area faces**, every edge shared by exactly two
    faces;
  - trim: **0 zero-area faces** (27 while the letters were carved);
  - accent: **38 zero-area faces**, all in the raised letters (52 to 56 mm
    up), where their 0.2 mm steps meet. They are slivers of no area, and the
    slicer handles them: the house slices with 0 supports.
  - The house as a whole has 0 zero-area faces and every edge shared by
    exactly two faces.
- **The house parts are disjoint.** All three pairwise intersections are
  EMPTY. The lid touches the house only at its seat (zero volume).
- `print_fidelity` (re-run 2026-10-07 with the raised letters): the house
  loses 0.4 mm³ of 49,691 mm³ and the lid nothing. **No flags** on either:
  every letter prints as drawn.
- `fragility` (2026-10-07): **0 high, 0 watch.**
- Every trim and accent piece shares real surface with the part it sits on.
  The sign board shares 641 mm² with the wall, the coping 611 mm², each
  window frame about 250 mm², and the parcel string sits in the parcels.
- **OBC maker's mark:** engraved 0.8 mm deep under the step: Montserrat
  Black, size 4.6, letter spacing 1.16, 16.2 mm wide. It reads OBC when you
  turn the building over with the front toward you (fixed 2026-09-27: it read
  "ƆBO", and its letters ran together, with 0.39–0.46 mm between them).
- **POST OFFICE letters:** size 4.4, one line, raised 0.84 mm (2026-10-07).
  They are built in five slabs, each keeping only what has letter under it
  all the way down its climb (1.2 up per 1 out, in 0.2 mm steps). So only
  their undersides slope; the holes in the O's and P and the bars of the
  F's and E stay as drawn, and they print with no supports. The town's
  general relief, tried first, let each lower stroke rise into the letter's
  hole and left slivers there, thinner than a bead.

## First print (2026-10-06)

Scott printed the house and lid in one colour (white PLA), and a second one
painted, and photographed both; `photos/` holds them. What the print shows:

- **It printed whole, with no supports.** Brick courses, the parapet's coping,
  the gable-headed door and window, the window's bars on its glass, the
  door's triangle light, the leaning chimney and stove pipe on the lift-off
  lid all came out as modelled. The lid sits in its seat.
- **Lit, it works** (`first_print_2026-10-06_painted_lit.jpg`): the window's
  glass glows evenly behind its bars and the door's light shows.
- **In one colour, the carved sign is hard to read.** The letters' carve
  climbs in 58° steps so it prints without supports; in white, those steps
  catch the light under each letter's arms, and the two F's read close to
  E's ("POST OEFICE"). Lined in the accent colour on an AMS print, or
  painted, the letters read cleanly. A one-colour version needs a fix before
  it is sold that way: raised letters, or a deeper, plainer carve.
  **Fixed in the model 2026-10-07: the letters are raised** (Scott's call,
  for every sign in the town). Not yet printed; `../sign_test/` is the quick
  check.
- **The parcels' top edges are slightly rough,** small faces printed at the
  top of a short stack. Cosmetic.
