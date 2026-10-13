# Victorian Signpost — printing notes

Built 2026-10-13, a Victorian village accessory. Scott's circle round the
bandstand on the second batch of accessory studies
(`../concepts/accessories2_scene.jpg`) took in the signpost too.

A cast-iron fingerpost:

- **a round post** on a fluted foot, a collar and **an acorn finial** with
  **snow** on it;
- **three white arms** pointing three ways, each standing on **an iron
  bracket** pierced with two diamonds;
- a soft heap of snow round its foot, on a small blob of snow with a drift.

The arms carry no lettering: at this size a word would be under one
extrusion wide.

The maker's mark, OBC, is engraved 0.8 mm into the middle of the underside,
mirrored so it reads from below.

It measures 25.1 × 20.0 × 44.2 mm.

`images/` holds renders of the model: `*_colour_*` in its two filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_signpost.3mf`. One object with two parts, already
aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| roof | the post and the brackets | slate `#2E3440` |
| trim | the arms, the snow, the base | white `#F4F1EA` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 14 m** | **0.7 m, 2.1 g** |
| two colour | see below | 2.1 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). The arms and the post change colour on most of its 220 layers, so in
two colours the changes dominate: the viewer's colour slice (PrusaSlicer,
with a wipe tower) runs 2 h 30 m and 23.8 g. Bambu Studio's purge differs;
slice there for the real number, or print several on one plate.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.29 mm, median 3.2 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 44.0 mm of 44.2 modelled;
  - 2.6 cm² of bed contact, 51% of the footprint; centre of mass over it.
- `print_fidelity`: 9.6 mm³ of 1,912 mm³ not printed, in slivers 0.1 mm wide
  where the arms meet the post and the brackets; 0.2 mm³ printed that was not
  modelled. **0 flags.**
- `fragility`: 0 high, 0 watch. Three short slender runs (slenderness 2 at
  most) where the arms join the post.

## What it took to print without supports

- **The arms.** Out on their own, each is a ledge 11 mm long over nothing.
  Each stands on a bracket whose edge falls 39 degrees from upright.
- **An open knee brace** looked lighter, but the arm then had to bridge from
  the post to the brace, and the slicer would not take it as a bridge: 6,762
  support moves. The brackets are solid, pierced with diamonds whose sides
  climb at 58 and 59 degrees.
- **The brackets** were first thinner than the arms, which left a 0.3 mm
  ledge of arm hanging past them; they are as thick as the arms now and run
  their full length.
- **The collar** was too thin to print whole; it is 2.0 mm tall.
