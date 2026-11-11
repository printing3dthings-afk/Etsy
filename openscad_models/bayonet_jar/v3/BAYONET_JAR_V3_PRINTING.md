# Bayonet Jar v3: closes clockwise, in 16 sizes

2026-11-11. v2 (`../../bayonet_jar.scad`) is untouched; v3 sits beside it.

You printed v2: "The lid closes perfectly. Now two things. I want this in different
sizes include height and diameter. Second the lid twist shut the wrong direction."

## What changed

- **It closes clockwise now,** seen from above, like any jar. v2's lock channel ran
  counter-clockwise from its entry. Only the direction changes: the channel's
  section, its 0.35 mm ramp, the 0.25 mm lock clearance and the 0.45 mm entry are
  v2's exactly, so it should close as well as the one you printed.
- **Any size from one file.** `D` is the jar's outside diameter, `H` its body height.
  - The lock zone and the lid are measured down from the rim, so they're the same
    in section at every size.
  - **One lid fits every height of its diameter.**
- **The inside slope under the lock collar is now 35° off vertical** (v2 was 45°), so
  the slicer no longer wants supports in there. It's inside the jar, away from the
  lid, so the fit doesn't change.
- **The OBC mark** on the bottom scales with the jar, from 5 mm letters on the 40 mm
  jar to 9 mm on the 80 mm one.

## The sizes

One print file per size, the jar and its lid on one plate, one colour. Bambu Studio,
P1S 0.4, 0.20 mm Standard, PLA Basic, no supports:

| file | across (jar / lid) | tall closed | inside the jar | time | filament |
|---|---|---|---|---|---|
| `bayonet_jar_v3_D40_H30.3mf` | 40 / 45.3 | 36 | 35 wide, 27 deep | 55 min | 21.1 g |
| `bayonet_jar_v3_D40_H45.3mf` | 40 / 45.3 | 51 | 35 wide, 42 deep | 1 h 6 min | 25.4 g |
| `bayonet_jar_v3_D40_H70.3mf` | 40 / 45.3 | 76 | 35 wide, 67 deep | 1 h 23 min | 32.6 g |
| `bayonet_jar_v3_D40_H100.3mf` | 40 / 45.3 | 106 | 35 wide, 97 deep | 1 h 44 min | 41.2 g |
| `bayonet_jar_v3_D50_H30.3mf` | 50 / 55.3 | 36 | 45 wide, 27 deep | 1 h 16 min | 28.4 g |
| `bayonet_jar_v3_D50_H45.3mf` | 50 / 55.3 | 51 | 45 wide, 42 deep | 1 h 30 min | 33.7 g |
| `bayonet_jar_v3_D50_H70.3mf` | 50 / 55.3 | 76 | 45 wide, 67 deep | 1 h 54 min | 42.5 g |
| `bayonet_jar_v3_D50_H100.3mf` | 50 / 55.3 | 106 | 45 wide, 97 deep | 2 h 22 min | 53.1 g |
| `bayonet_jar_v3_D65_H30.3mf` | 65 / 70.3 | 36 | 60 wide, 27 deep | 1 h 48 min | 40.8 g |
| `bayonet_jar_v3_D65_H45.3mf` | 65 / 70.3 | 51 | 60 wide, 42 deep | 2 h 5 min | 47.8 g |
| `bayonet_jar_v3_D65_H70.3mf` | 65 / 70.3 | 76 | 60 wide, 67 deep | 2 h 35 min | 59.5 g |
| `bayonet_jar_v3_D65_H100.3mf` | 65 / 70.3 | 106 | 60 wide, 97 deep | 3 h 10 min | 73.6 g |
| `bayonet_jar_v3_D80_H30.3mf` | 80 / 85.3 | 36 | 75 wide, 27 deep | 2 h 24 min | 55.7 g |
| `bayonet_jar_v3_D80_H45.3mf` | 80 / 85.3 | 51 | 75 wide, 42 deep | 2 h 46 min | 64.3 g |
| `bayonet_jar_v3_D80_H70.3mf` | 80 / 85.3 | 76 | 75 wide, 67 deep | 3 h 23 min | 78.7 g |
| `bayonet_jar_v3_D80_H100.3mf` | 80 / 85.3 | 106 | 75 wide, 97 deep | 4 h 8 min | 96.0 g |

- **Inside width** is below the collar. The opening at the rim is 3.2 mm narrower
  (the collar).
- **50 × 45 is v2's size.**

**Another size:** open `bayonet_jar_v3.scad`, set `D` (40 to 120) and `H` (28 to
240), and export `part="base"` and `part="lid"`. Then run `python3 build_sizes.py`
with the size added to its lists, so it's checked before you print it.

## Closing it

1. Set the lid on and turn it gently until it drops, about 8 mm.
2. Twist it clockwise, about 25°, until it stops.

To open, twist it back and lift. The guide, `Bayonet_Jar_v3_Guide.pdf`, shows both.

## Printing

Print both parts as they lie in the file. The lid is already flipped, cap on the
plate. If one size feels stiff to turn, open `lock_clear` to 0.30. If it rattles,
close it to 0.20. As on v2, that's the one number worth touching.

## Checked

**`build_sizes.py`, on the exported parts of all 16 sizes:**
- the lid drops on at the entry untouched;
- it turns clockwise to locked untouched, its cap on the rim while the ramp closes
  the channel ceiling onto the bumps;
- locked, nothing overlaps, and lifted 0.3 mm the bumps hit the channel ceilings, so
  there's no free lift;
- from the entry it won't turn counter-clockwise: 8° that way it hits;
- 8° past locked, the channel's end stops it.

**Print fidelity** (50 × 45, jar and lid, sliced with no supports): 0 flags. The lock
channels and bumps print as modelled.

**Fragility:** nothing slender on either part.

**Product gate:**
- **The supports check fails** on every jar and every lid. It flags exactly two
  features, both the lock's working surfaces:
  - **on the jar:** the ceilings of the three lock channels, cut into the outside wall;
  - **on the lid:** the undersides of the three bumps, which print facing the plate.
    That is the face that bears on the channel ceiling.
- **I kept them.** Reshaping them would change the fit you said closes perfectly.
- **The evidence they print:** v2 has the same features at the same section, and you
  printed it without supports. The no-support fidelity slice agrees.
- **Every other gate check passes.**

**Not tested on the printer:** any size but 50 × 45, and the clockwise direction.
Print one, and tell me which size and how it closes.

## Rebuilding

```
python3 build_sizes.py     # exports every size and checks each fit
./ship_sizes.sh            # gates, 3MFs, slices
python3 render_v3.py       # design-review renders, not photos
python3 make_guide.py      # the PDF
```
