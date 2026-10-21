# Village Mini-Lantern Ornaments — printing notes

Built 2026-10-21. Scott picked the mini-lantern form (4E) from five ornament
ideas. Each one is a small six-sided carriage lantern, the shape of the
shop's hex lantern, with a building from the Christmas village raised on its
glass. That way the ornaments match both the village and the lanterns.

A set of six, each its own print, each 40.4 × 35.0 × 70.9 mm with its ring:

| file | the building on its front and back |
|---|---|
| `mini_lantern_1_*.stl` | the church |
| `mini_lantern_2_*.stl` | a cottage |
| `mini_lantern_3_*.stl` | the clock tower |
| `mini_lantern_4_*.stl` | the town tree, a star on top |
| `mini_lantern_5_*.stl` | the toy shop |
| `mini_lantern_6_*.stl` | the well |

They are solid, not shades: no light goes inside. Each lantern has:

- a slate frame: plinth, six corner posts, rail, a pointed roof and a ring to
  hang it by;
- white glass, 30 mm across the flats;
- the building raised 1 mm out of the front and back panels. The four panels
  between carry a snowflake and four stars;
- snow round the roof's crown, with drips down four of its faces;
- a red bow on the front of the roof.

The maker's mark, OBC, is inlaid in the plinth's underside in the glass's
white, 4.4 mm tall.

`images/` holds renders, not photos of a print:
- `mini_lantern_colour_*` shows the six in their colours.
- `mini_lanterns_plate_as_printed_*` comes from the plate's sliced toolpath.

**Print these:** `mini_lantern.3mf` has all six on one plate, each its own
object in five parts already aligned. Assign the filaments:

| part | what it is | colour in the file | slot |
|---|---|---|---|
| frame | plinth, posts, rail, roof, ring | slate `#2E3440` | 1 |
| art | the buildings, snowflakes and stars | slate `#2E3440` | 1 |
| glass | the six panels, and the mark under the plinth | white `#F4F1EA` | 2 |
| snow | the snow on the roof | white `#F4F1EA` | 2 |
| bow | the bow | red `#C62F3A` | 3 |

Three filaments. The art shares the frame's slate and the snow shares the
glass's white, so there are only three colours to change between.

## Settings that are not optional

- **Supports OFF.** None is needed: 0 support moves, 0 overhang perimeters on
  every lantern.
- **Print them upright, plinth on the plate, as they sit in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

Single colour, supports off, timed with the P1S motion model (the viewer's
clock):

| lantern | time | filament |
|---|---|---|
| each of the six | 0 h 39–40 m | 5.6 m, 16.6 g |
| **the set** | about 3 h 55 m one at a time | **99.6 g** |

In three colours, every layer that holds the art, the snow or the bow costs
changes. The art runs the whole height of the glass, so most layers do. Slice
in Bambu Studio for the real purge. With all six on one plate, the changes
are shared between them.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: on every lantern, all five parts closed and no
  two overlapping. Also no overlaps with the six standing side by side.
- `product_gate` **PASSED** on all six, the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.43–1.83 mm, median 30 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 70.8 mm of 70.88 modelled;
  - 10.5 cm² of bed contact, 75% of the footprint.
- `print_fidelity`, on the plate's slice in three filaments:
  - 8.22 mm³ modelled but not printed, of 266,841 mm³;
  - 0.22 mm³ printed but not modelled;
  - 0.0 mm³ in the wrong colour;
  - **12 flags, explained below.**
- `fragility`: 0 high, 0 watch, 0 slender runs on all six.

**The twelve flags** are two on each lantern, at the same place: the top
edge of the bow's left loop, 50.4–50.8 mm up. The bow lies on a roof that
leans back 41°, so its last layers there are only about 0.7 mm out from the
roof. At two points along that edge, the slicer leaves off a strip 0.27–0.28 mm
wide in the last two layers: 0.026–0.028 mm³ each. A bow 1 mm proud on a sloping roof cannot avoid a thin last layer. On
a loop 3 mm across, the difference does not show.

## What it took

- **The rail and the roof lean back within the support angle,** as on the hex
  lantern. The rail's underside climbs 1.6 per 1 out of the glass. The roof's
  faces lean back 41°.
- **The scenes are raised with a skirt under every stroke** (`relief_lib`'s
  `art_skirt`). The first version trimmed each stroke from below instead.
  That kept only slivers 0.24 mm wide of the church's cross and the stars'
  arms in the outer layers.
- **Every stroke is widened 0.16 mm a side.** At this size, the scenes'
  walls and the snowflakes' arms were 0.86–0.95 mm, under the gate's 1.2 mm
  floor.
- **The skirt stops at the plinth.** Below the ground strip, it reached
  1.6 mm down into the plinth and shared 17 mm³ with the frame on every
  lantern. On the plate's slice, 531 mm³ of modelled detail was not
  printed, with 73 flags.
- **The snow is one band round the whole roof.** Drawn face by face and
  welded at the hips, it left a wedge 0.05–0.14 mm thin along every hip. Its
  lower edge stands straight up, with nothing under it.
- **No drips on the bow's face.** There the bow's loops met the drips, and
  cut apart they left a red sliver 0.27 mm wide that the slicer dropped.
- **The bow's tails are square-ended and end on the roof.** Forked, their
  points were 0.27 mm slivers. Lower down, they hung 2 mm past the eave, and
  the slicer built a column from the bed to hold them.
- **The ring's foot is 4.4 mm wide,** so its corners stand on the crown. At
  5.2 mm they stood 0.4 mm past its flats, and the slicer propped them.
