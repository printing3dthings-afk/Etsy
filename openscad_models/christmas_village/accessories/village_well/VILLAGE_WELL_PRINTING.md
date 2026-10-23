# Victorian Village Well — printing notes

Built 2026-10-14, a Victorian village accessory from the second batch of
accessory studies (`../concepts/accessories2_scene.jpg`).

A village well under its own little roof:

- **a round brick well** with two course lines and a **stone coping**, its
  water frozen over in slate;
- **four white posts** on the coping carrying **a white valance**, each
  bay's opening closing in a point;
- **a steep slate roof**, pitched at 55°, its eaves standing out on a
  corbel, **white gables**, and **snow** along the ridge;
- **a green wreath** with a red bow on the front gable;
- **a slate bucket** with a white band, standing on the rim under the
  wreath;
- on a round blob of snow with two drifts.

The maker's mark, OBC, is inlaid in slate into the underside: the logo's
letters, 5 mm tall and 17.1 mm wide, cut 0.6 mm into the white and filled
flush, mirrored so they read from below. A groove one layer deep crosses
their face, the stripes of the logo.

It measures 38.0 × 38.0 × 45.4 mm.

`images/` holds renders of the model: `*_colour_*` in its four filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_village_well.3mf`. One object with four parts,
already aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | the well, the bow | brick red `#A8483A` |
| roof | the roof, the ice, the bucket, the OBC mark inlaid underneath | slate `#2E3440` |
| trim | the snow, the coping, posts, valance, gables, the bucket's band | white `#F4F1EA` |
| accent | the wreath | green `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 23 m** | **2.4 m, 7.0 g** |
| four colour | see below | 7.0 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In colour, the colour changes cost far more than the model: the
viewer's colour slice (PrusaSlicer, with a wipe tower, 155 changes) runs
4 h 49 m and 47.0 g. Bambu Studio's purge differs; slice there for the real
number, or print several on one plate so the changes are shared.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.40 mm, median 3.21 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 45.4 mm of 45.42 modelled;
  - 11.3 cm² of bed contact, 78% of the footprint; centre of mass over it.
- `print_fidelity`: 0.16 mm³ of 8,297 mm³ not printed (the deepest spot
  0.28 mm), nothing printed that was not modelled, nothing in the wrong
  colour. **0 flags.**
- `fragility`: **0 high, 4 watch**: the four posts, 10 mm free between the
  coping and the valance at slenderness 5.0, each joined at both ends. Lift
  it by the well, not the roof.

## How it prints without supports

It passed the gate on its first build; these are the choices that let it.

- **The roof** is pitched at 55°, so its underside, open above the well,
  climbs 35° off upright. Its ends are filled by the gables.
- **The valance** carries the roof between the posts. Each bay's opening
  closes in a point whose edges climb 50°, so there is no flat beam to
  bridge.
- **The eaves** stand 1.8 mm out on a corbel that steps out at 1.2 per 1;
  the first draft's 1.0 mm barely cleared the posts.
- **The snow** along the ridge is 1 mm deep there and thins to nothing down
  the slope, so it faces up everywhere.
- **The bucket's** sides flare 10°; the wreath's skirt lands on the valance.
- There is no winding gear or rope. A windlass is a beam across the posts in
  mid-air, and a rope long enough to read is a strand the fragility check
  would mark high.
