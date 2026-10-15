# Victorian Pillar Box — printing notes

Built 2026-10-13, a Victorian village accessory. Scott circled it from the
second batch of accessory studies (`../concepts/accessories2_scene.jpg`).

A hexagonal Penfold pillar box, the kind that stood on British streets in the
1860s and 70s:

- **a six-sided shaft** on a bevelled plinth, a band under a **flared
  cornice**, a domed six-sided cap and **a bud** on top;
- **the door** standing out of the front, with **the letter slot** cut
  through it;
- **a green wreath** on the door with **a white bow**;
- **snow** lying on the cap, its foot running out to nothing on the slope;
- on a small soft blob of snow with two drifts.

The maker's mark, OBC, is inlaid in brick red into the middle of the
underside: the logo's letters, 4 mm tall and 14.1 mm wide, cut 0.6 mm into
the white and filled flush, mirrored so they read from below. A groove one
layer deep crosses their face, the stripes of the logo.

It measures 21.0 × 21.0 × 33.3 mm.

`images/` holds renders of the model: `*_colour_*` in its three filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_pillar_box.3mf`. One object with three parts,
already aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | the box, the OBC mark inlaid underneath | brick red `#A8483A` |
| trim | the snow, the base, the bow | white `#F4F1EA` |
| accent | the wreath | green `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 12 m** | **0.9 m, 2.6 g** |
| three colour | see below | 2.6 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In colour, the colour changes cost far more than the model: the
viewer's colour slice (PrusaSlicer, with a wipe tower) runs 1 h 49 m and
18.7 g. Bambu Studio's purge differs; slice there for the real number, or
print several on one plate so the changes are shared.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.37 mm, median 10.58 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 33.2 mm of 33.31 modelled;
  - 3.5 cm² of bed contact, 78% of the footprint; centre of mass over it.
- `print_fidelity`: 0.02 mm³ of 4,100 mm³ not printed, nothing printed that
  was not modelled. **0 flags.**
- `fragility`: 0 high, 0 watch, no slender runs.

## What it took to print without supports

- **The door** was first an outline cut into the face, 6.2 mm wide on a face
  6.24 mm wide: it ran into the hexagon's corners as slivers 0.15 mm thick,
  and the wreath bridged its groove. It is a panel standing 0.6 mm out of the
  face now, 0.6 mm clear of the corners, the slot cut through it.
- **The wreath** first floated 0.01 mm off the door.
- **The drifts** first ran over the base's rounded edge and hung off it;
  they are kept inside it.
- **The bow's lobes** reached past the door panel; they are smaller.
