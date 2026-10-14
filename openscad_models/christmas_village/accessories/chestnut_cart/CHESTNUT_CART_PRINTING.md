# Victorian Chestnut Cart — printing notes

Built 2026-10-14, a Victorian village accessory from the second batch of
accessory studies (`../concepts/accessories2_scene.jpg`).

A hot chestnut seller's barrow parked in the snow:

- **a red box** with rounded corners and a **white rim**, its underside a
  hopper that narrows down to a drift of snow;
- **two slate wheels** with white spokes, rim and hub, standing in the snow;
- **two handles** resting on the snow behind;
- **an iron brazier** on the lid, its pointed vents glowing red, a **pan of
  chestnuts** on top and **a tall chimney** with a cap;
- **a green wreath** with a red bow on the front end, **snow** on the lid;
- on an oval of snow with two drifts.

The maker's mark, OBC, is engraved 0.8 mm into the underside, mirrored so it
reads from below.

It measures 52.0 × 30.0 × 42.9 mm.

`images/` holds renders of the model: `*_colour_*` in its four filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_chestnut_cart.3mf`. One object with four parts,
already aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | the box, the bow, the embers, the chestnuts | brick red `#A8483A` |
| roof | the wheels, axles, handles, brazier, chimney | slate `#2E3440` |
| trim | the snow, the rim, the spokes | white `#F4F1EA` |
| accent | the wreath | green `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 20 m** | **2.2 m, 6.7 g** |
| four colour | see below | 6.7 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In colour, the colour changes cost far more than the model: the
viewer's colour slice (PrusaSlicer, with a wipe tower, 146 changes) runs
4 h 26 m and 37.8 g. Bambu Studio's purge differs; slice there for the real
number, or print several on one plate so the changes are shared.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.30 mm, median 3.2 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 42.8 mm of 42.85 modelled;
  - 11.7 cm² of bed contact, 75% of the footprint; centre of mass over it.
- `print_fidelity`: 0.04 mm³ of 8,708 mm³ not printed, nothing printed that
  was not modelled, nothing in the wrong colour. **0 flags.**
- `fragility`: **0 high, 3 watch.** The chimney (16.8 mm free above the
  brazier, slenderness 6.0) and the two handles (4.9 and 4.7). Lift it by
  the box, not the chimney.

## What it took to print without supports

- **It first stood on a block of snow** as wide as the box, and read as a
  cart on a plinth. The box now narrows underneath into a hopper, its sides
  climbing 1.2 per 1 out, onto a small drift; the wheels stand in the snow
  on their own, their curve leaving it 42° off upright.
- **The corners.** Square, the hopper's and the rim's corners stepped out
  1.4 times as far on the diagonal as on the sides, and the slicer propped
  all four. The box's corners are rounded 2.5 mm now, so a corner climbs at
  the same rate as a side.
- **The rim** started below the top of its own flare, a flat ledge the
  slicer propped; at 0.8 mm tall its edge was also under one bead. It is a
  2 mm band now, flaring out 0.6 mm at the climb.
- **The axles** bridged 2 mm of air from wheel to hopper. Each one sits on a
  web that climbs from the wheel's inner face to the hopper.
- **The handles** reached the snow at 42°; they meet it at 38° now.
- **The spokes** were raised the usual way, trimmed from below, and the
  level spoke came out 0.9 mm tall. They are skirted instead, full height.
- **The wreath** first hung on the side, behind a wheel; its bow was
  mirrored about the wrong point and printed as a loose piece. It is on the
  front end now, high enough that its skirt clears the hopper.
- **The pan's wall** was 1.1 mm; it is 1.3.
