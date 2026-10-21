# Faceted Nativity — printing notes

Built 2026-10-21. Scott picked the faceted low-poly form (5A) from five
nativity ideas: every figure cut from flat faces, like a carved gem or
folded paper. Eleven prints:

| piece | what it is | size (mm) |
|---|---|---|
| Mary | kneeling, hooded, hands together | 24.5 × 26.5 × 39.6 |
| Joseph | standing with his staff, bearded | 23.4 × 23.5 × 62.0 |
| the baby | swaddled, in the manger on hay | 41.0 × 19.2 × 19.4 |
| king 1 | crown of six points, a casket | 24.8 × 23.9 × 56.5 |
| king 2 | crown of five, a jar | 24.7 × 26.2 × 54.7 |
| king 3 | crown of six, a horn | 24.9 × 25.0 × 54.7 |
| the shepherd | headscarf and staff | 23.5 × 21.5 × 58.0 |
| the ox | lying down, horned | 47.0 × 18.0 × 18.5 |
| the donkey | lying down, long ears | 43.0 × 15.0 × 25.0 |
| the sheep | lying down | 28.7 × 18.7 × 11.5 |
| the stable | an open shell, the Star of Bethlehem on its ridge | 150.0 × 70.0 × 164.0 |

The figures stand about 55–62 mm and the animals lie down. In the renders,
the holy family and the animals stand inside the stable with room between
them (checked: no two overlap).

**Colours:**
- **Wood brown (`#7A5C3F`):** everything except the gold.
- **Gold (`#C9A84C`):** the kings' crowns and gifts, and the star.
- **One colour:** it prints entirely in one, the gold included.

**The maker's mark,** OBC, is engraved 0.8 mm into each piece's underside,
mirrored to read from below:
- 5 mm tall on the figures, 4.4 mm on the sheep and 8 mm on the stable.
- It is cut as whole letters, without the logo's stripe grooves. With no
  second colour to fill them, the stripes left strips one layer thick that
  the gate read as 0.2 mm walls.
- The cut is pulled in 0.15 mm all round, so the walls between letters are
  printable.

`images/` holds renders, not photos of a print:
- `nativity_colour_*` stands the whole set together: the figures inside the
  stable, the kings and the shepherd before it.
- `*_as_printed_*` comes from each plate's sliced toolpath.

## Print these

Eleven pieces do not fit one plate in a row, so they come as three plates:

| file | on it | colours |
|---|---|---|
| `nativity_holy_family.3mf` | Mary, Joseph, the baby, ox, donkey, sheep | 1 |
| `nativity_kings_shepherd.3mf` | the three kings and the shepherd | 2 |
| `nativity_stable.3mf` | the stable and its star | 2 |

Each piece is its own object. Assign the filaments; the gold goes to slot 2.

## Settings that are not optional

- **Supports OFF.** None is needed. Every piece slices with 0 support moves
  and 0 overhang perimeters.
- **Print every piece upright, as it sits in the file.** The faceting is
  what makes that work; see below.
- 0.2 mm layers.

## Cost — sliced, not estimated

Single colour, supports off, timed with the P1S motion model (the viewer's
clock):

| piece | time | filament |
|---|---|---|
| Mary | 0 h 16 m | 4.2 g |
| Joseph | 0 h 23 m | 6.1 g |
| the baby | 0 h 10 m | 4.1 g |
| king 1 | 0 h 22 m | 6.1 g |
| king 2 | 0 h 21 m | 5.9 g |
| king 3 | 0 h 21 m | 5.8 g |
| the shepherd | 0 h 22 m | 5.3 g |
| the ox | 0 h 10 m | 4.5 g |
| the donkey | 0 h 10 m | 3.7 g |
| the sheep | 0 h 5 m | 1.7 g |
| **the figures** | **2 h 40 m** one at a time | **47.4 g** |
| the stable | 3 h 2 m | 121.4 g |
| **the set** | about 5 h 42 m | **168.8 g** |

In two colours, the gold adds colour changes on the kings' plate (crowns and
gifts) and at the top of the stable (the star). Slice in Bambu Studio for
the real purge.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed and no two overlapping, on
  each piece and with the whole set standing together in the stable.
- `product_gate` **PASSED** on all eleven:
  - watertight, one body;
  - 1st-percentile walls 1.29–3.04 mm against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - full printed height;
  - 3.0–7.3 cm² of bed contact on the figures, 104 cm² on the stable.
- `print_fidelity`, on each plate's slice:
  - holy family: 0.55 mm³ not printed of 46,266 mm³;
  - kings and shepherd: 0.77 mm³ of 50,518 mm³, 0.01 mm³ in the wrong colour;
  - stable: 0.0 mm³ of 136,147 mm³.
  - **0 flags on all three.**
- `fragility`: 0 high, 0 watch on every piece.

## What it took to print without supports

- **Robes narrow as they rise**, so their faces lean in.
- **Heads are six-sided double pyramids.**
  - Their lower faces climb 55° and their edges 51°, where a round head
    would overhang under the chin.
  - At 50° and 46°, they sat on the slicer's 45° line, and it propped one
    king's chin from his shoulders.
  - Each head's top is a small flat, not a point: points are sliced away,
    and printed heights came up short.
- **The kings' capes** stand 1.5 mm out of the robe. Their hem's underside
  climbs 55° back into the robe over 4 mm.
  - As a flat ring 2 mm out, the hem put 10,000 support moves under each
    king.
  - At 48°, it still put 7,000.
- **The crowns** are bands that flare out 55° and then rise straight, so
  the rim is square. Flaring all the way to the top made a 60° knife edge.
  - Their points end in flats 1.4 mm square. At 0.5 × 1.0 they read as
    walls under the floor.
  - The points' feet stay inside the band's six flat sides. Their corners
    0.2 mm past the flats made the slicer prop them from the shoulders.
- **Gifts and hands** rest on wedges or cones that climb 55° into the robe.
  On a wedge to one point, king 2's jar hung at 28°.
- **Joseph's beard**, the ox's horns and the donkey's ears all start inside
  the figure. Each one began just outside it, and the slicer propped the
  sliver.
- **The animals lie down**, so there are no legs to snap.
  - The donkey's ears are 2.0 × 2.2 mm at the tip. At 1.2 × 1.4 mm and
    27 mm high, `fragility` watched them.
- **The manger** stands on block feet: square at the toe, then a 55°
  chamfer into the trough. As wedges, their knife edges read as walls
  0.01 mm thick.
  - The baby's bundle and head sink into the hay.
  - Their chin points came up through the mound as a sliver the slicer
    dropped.
- **The sheep's head** has a flat crown. Sloping straight from the back, it
  met the back face in a 60° knife edge.
- **The stable** is a 3 mm shell, open at the front. Solid, it was 606 cm³,
  about 750 g.
  - Its roof climbs 46° to the ridge, and the inside roof is offset
    square to it.
  - The star stands on the front of the ridge, as thick as the shell. 4 mm
    thick, it stood out past the open front over nothing.
  - The star's arms climb 47° or more underneath, where a five-pointed
    star's arms climbed only 38°.
  - Its top arm ends in a flat.
  - Its tail is a 3.2 mm stem into the ridge. Tapering to a point, the whole
    star hung from about 2 mm², which `fragility` watched.
