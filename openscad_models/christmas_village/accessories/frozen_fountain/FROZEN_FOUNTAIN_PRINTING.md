# Victorian Frozen Fountain — printing notes

Built 2026-10-14, a Victorian village accessory from the second batch of
accessory studies (`../concepts/accessories2_scene.jpg`).

A tiered fountain that froze as it ran:

- **a twelve-sided brick basin** with two course lines and a **stone
  coping**, its water frozen over in slate;
- **a column** rising from the ice to **a big bowl**, a **small bowl** above
  it, and **a jet frozen in the air** on top, a crown of spikes;
- **falls of ice** pouring over each bowl's lip, nine round the big bowl and
  five round the small, each narrowing and swelling as it falls the way an
  icicle does, and landing in a frozen splash;
- **a green wreath** with a red bow on the basin's front, **snow** on the
  ice;
- on a round blob of snow with two drifts.

The maker's mark, OBC, is inlaid in slate into the underside: the logo's
letters, 5 mm tall and 17.1 mm wide, cut 0.6 mm into the white and filled
flush, mirrored so they read from below. A groove one layer deep crosses
their face, the stripes of the logo.

It measures 56.0 × 56.0 × 42.9 mm.

`images/` holds renders of the model: `*_colour_*` in its four filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_frozen_fountain.3mf`. One object with four parts,
already aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | the basin, the column and bowls, the bow | brick red `#A8483A` |
| roof | the ice in the basin and the bowls, the OBC mark inlaid underneath | slate `#2E3440` |
| trim | the snow, the coping, the falls, the jet | white `#F4F1EA` |
| accent | the wreath | green `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 35 m** | **4.4 m, 13.1 g** |
| four colour | see below | 13.1 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In colour, the colour changes cost far more than the model: the
viewer's colour slice (PrusaSlicer, with a wipe tower, 206 changes) runs
6 h 19 m and 55.3 g. Bambu Studio's purge differs; slice there for the real
number, or print several on one plate so the changes are shared.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.21 mm, median 3.78 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 42.8 mm of 42.9 modelled;
  - 24.5 cm² of bed contact, 78% of the footprint; centre of mass over it.
- `print_fidelity`: 0.01 mm³ of 17,742 mm³ not printed, nothing printed
  that was not modelled, nothing in the wrong colour. **0 flags.**
- `fragility`: **0 high, 14 watch.** All of them are the falls: the big
  bowl's run 16.8 mm at slenderness 8.8 to 10.3, the small bowl's 7.6 mm.
  Each is joined at both ends, to the bowl's lip and to the ice, so none is
  a free end like the chapel's window bar that snapped (15). Lift it by the
  basin.

## What it took to print without supports

- **The bowls** print because their undersides climb 1.2 per 1 out from the
  column. The study had icicles hanging from their rims; hanging, each tip
  is an island in the air.
- **The falls** went through four versions. Even round falls read as a ring
  of posts; a fluted veil all the way round read as a cake and asked for 483
  support moves; sixteen streams read as a birdcage. Nine and five streams
  of uneven width and spacing, each narrowing through four knots, read as
  water that froze. Icicles lying along the bowls' undersides between them
  were tried and needed support: a ridge on a surface that already climbs at
  the limit leans past it.
- **The coping's lip** was 1.0 mm and read under one bead; it is 1.4.
- **The wreath** sits on the bricks at the course lines' depth, so it does
  not bridge them.
