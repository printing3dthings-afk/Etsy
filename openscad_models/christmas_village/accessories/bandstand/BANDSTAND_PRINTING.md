# Victorian Bandstand — printing notes

Built 2026-10-13, a Victorian village accessory. Scott circled it from the
second batch of accessory studies (`../concepts/accessories2_scene.jpg`).

An octagonal bandstand on a village green:

- **a brick plinth** in courses, with **stone steps** up at the front and a
  stone floor;
- **eight white columns** with bases and capitals;
- **iron railings** in every bay but the front, each pierced with three
  pointed arches;
- **a white valance** between the column tops, each bay's opening closing in
  a point, with **a green wreath and a red bow** over every bay;
- **a slate roof**, bell-cast, with **snow** on its upper half and **a
  finial** on top;
- on a round blob of snow with four low drifts.

The maker's mark, OBC, is inlaid in slate into the middle of the underside:
the logo's letters, 6 mm tall and 20.1 mm wide, cut 0.6 mm into the white
and filled flush, mirrored so they read from below. Two grooves one layer
deep cross their face, the stripes of the logo.

It measures 72.0 × 72.0 × 72.1 mm.

`images/` holds renders of the model: `*_colour_*` in its four filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_bandstand.3mf`. One object with four parts,
already aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | the brick plinth, the bows | brick red `#A8483A` |
| roof | the roof, the finial, the railings, the OBC mark inlaid underneath | slate `#2E3440` |
| trim | the snow, the floor, steps, columns, valance, cornice | white `#F4F1EA` |
| accent | the wreaths | green `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **1 h 15 m** | **10.8 m, 32 g** |
| four colour | see below | 32 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In four colours the viewer's colour slice (PrusaSlicer, with a wipe
tower) runs 5 h 48 m and 73.5 g, most of it colour changes: the wreaths and
bows bring green and red into layers that are otherwise white and slate.
Bambu Studio's purge differs; slice there for the real number.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.40 mm, median 7.13 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 72.2 mm of 72.14 modelled;
  - 40.5 cm² of bed contact, 78% of the footprint; centre of mass over it.
- `print_fidelity`: 4.8 mm³ of 53,624 mm³ not printed, 0.08 mm³ printed that
  was not modelled, nothing in the wrong colour. **0 flags.**
- `fragility`: 0 high, 0 watch. Fourteen slender runs of slenderness 3.5 at
  most: the bars between the railings' arches, 1.6 mm wide and 5.6 mm tall,
  held at both ends.

## How the roof prints

The roof spans the whole bandstand, 40 mm of air. Inside, it is a cone
climbing 1.2 per 1 in (50 degrees) from the valance to its apex, so every
layer sits on the one below; the roof's outside is drawn over that cone. The
valance carries no flat beam between columns: each bay's opening closes in a
point, its edges climbing 50 degrees from the columns. The cornice and the
eave corbel out at the same 1.2 per 1.

## What it took

- **Open edges.** The ceiling's foot first stopped at the valance's inner
  face, and the two shared that face; CGAL left the union with open edges
  along it. The foot runs on into the valance now.
- **The first fix hung below each point.** Run on down its slope into the
  valance, the ceiling came out 0.6 mm below each opening's point, an island
  the slicer propped with 9,519 support moves. It runs in level, 0.3 mm above
  the point.
- **Thin walls.** The capitals' rims and the wreaths' rings were just under
  one bead; the rims are 1.24 mm, the wreaths r 2.1 with a 0.6 hole.
- **The snow** first covered nearly the whole roof and hid the slate; it
  covers the upper half.
