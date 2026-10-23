# Victorian Town Christmas Tree — printing notes

Built 2026-10-14, a Victorian village accessory from the second batch of
accessory studies (`../concepts/accessories2_scene.jpg`).

The town's Christmas tree:

- **an octagonal brick plinth** with two course lines and a **stone cap**;
- **five tiers of green boughs**, twelve-sided, each turned 15° from the one
  below, **snow** along every tier's edge;
- **twenty red baubles** on the tiers;
- **a white star** on top;
- **five presents** in the snow round the plinth, red, green and slate, each
  tied with a white ribbon and bow;
- on a round blob of snow with two drifts.

The maker's mark, OBC, is inlaid in slate into the underside: the logo's
letters, 5 mm tall and 17.1 mm wide, cut 0.6 mm into the white and filled
flush, mirrored so they read from below. A groove one layer deep crosses
their face, the stripes of the logo.

It measures 46.0 × 46.0 × 77.5 mm.

`images/` holds renders of the model: `*_colour_*` in its four filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_town_tree.3mf`. One object with four parts,
already aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | the plinth, the baubles, two presents | brick red `#A8483A` |
| roof | one present, the OBC mark inlaid underneath | slate `#2E3440` |
| trim | the snow, the cap, the star, the ribbons | white `#F4F1EA` |
| accent | the tree, two presents | green `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 37 m** | **4.8 m, 14.4 g** |
| four colour | see below | 14.4 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In colour, the colour changes cost far more than the model: the
viewer's colour slice (PrusaSlicer, with a wipe tower, 160 changes) runs
5 h 12 m and 56.4 g. Bambu Studio's purge differs; slice there for the real number, or
print several on one plate so the changes are shared.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.73 mm, median 19.66 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 77.4 mm of 77.45 modelled;
  - 16.5 cm² of bed contact, 78% of the footprint; centre of mass over it.
- `print_fidelity`: 3.7 mm³ of 26,623 mm³ not printed, all of it hairlines
  under the flag size (the deepest 0.35 mm, at the baubles' edges); nothing
  printed that was not modelled, nothing in the wrong colour. **0 flags.**
- `fragility`: 0 high, 0 watch, no slender runs.

## What it took to print without supports

- **The tiers.** Each tier's underside climbs 1.3 per 1 out from the tier
  below, so it stands out like a skirt. 1.3 rather than the usual 1.2,
  because on a twelve-sided tier a corner sits 1.035 times further out than
  the middle of a flat.
- **The bottom tier** first grew from a short trunk, and its underside was a
  long cone: the tree read as a spinning top. It stands on the plinth's cap
  now, as a broad skirt, and a fifth tier keeps the tree's height.
- **Each tier's foot** sinks 0.5 mm into the tier below. Turned 15°, its
  corners stand over the lower tier's flats, which lie 0.3 mm inside the
  profile; left level, that was a shelf in the air.
- **The snow** lay exactly on each tier's top, the two shared faces, and the
  union came out of CGAL with open edges. It sinks 0.2 mm into the tier now,
  and thickens to its 0.8 mm at the edge, so it faces up everywhere.
- **The baubles** sit on the tiers' tops, which slope 52°, at a facet's
  corner (where the top is the profile and not a flat inside it), sunk
  0.25 mm so each is less than half a ball: a full half-ball on a 52° slope
  would hang its downhill edge out at 52°, and sinking it turns that edge
  up by 11° to 16°, inside the limit. One first touched the snow's
  edge and left an open edge in the red part; every bauble is clear of the
  snow and of the tier above now.
- **The star.** Its lower points run into a short funnel onto the tree's
  tip, and the funnel fills the notch between them: left open, that notch
  was a ceiling the slicer propped. Its inner points sit at 0.6 of the outer,
  so the side points' lower edges climb 38°. Its tips are rounded 0.5 mm:
  sharp, each was a sliver under one bead.
- **The plinth's** course lines were at 5.0 and 6.8 mm, and the brick
  between them was 1.16 mm tall; they are at 4.6 and 6.6 now.
