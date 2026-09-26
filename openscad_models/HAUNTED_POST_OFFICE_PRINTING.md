# Haunted Post Office — printing notes

Building #1 of the Haunted Town series (`HAUNTED_TOWN.md`). It is one story:
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
| house | trim | parapet coping, window and door frames, muntins, door, sign board, the parcels' string | cream `#EFE6D2` |
| house | accent | the parcels, the POST OFFICE letters, the brass mail slot | kraft `#D4A96A` |
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
| house, single colour | 5 h 34 m | 48 g |
| lid | 1 h 36 m | 12 g |
| **single colour, both** (e.g. for Jessee to paint) | **7 h 10 m** | **~60 g** |
| **house in three colours + lid** | not reliable here | ~61 g model + purge |

The colour house makes **446 colour changes**, far fewer than the bakery's
1,351. Purge is 89 g at PrusaSlicer's 140 mm³ flush, and about 194 g at the
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
  - watertight;
  - **0 zero-area faces**;
  - every edge shared by exactly two faces.
  - The house as a whole also has 0 zero-area faces.
- **The house parts are disjoint.** All three pairwise intersections are
  EMPTY. The lid touches the house only at its seat (zero volume).
- Every trim and accent piece shares real surface with the part it sits on.
  The sign board shares 641 mm² with the wall, the coping 611 mm², each
  window frame about 250 mm², and the parcel string sits in the parcels.
- **OBC maker's mark:** engraved 0.8 mm deep under the step, strokes
  ≥ 1.0 mm.
- **POST OFFICE letters:** size 4.4, one line, a flush inlay. Eroding them by
  one bead loses no letter.
