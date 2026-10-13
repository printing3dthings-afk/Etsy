# Panorama Drum Lantern — printing notes

Built 2026-10-13. Scott picked it, with the hex and gift box lanterns, from
five lantern forms (`../concepts/lantern_forms.jpg`).

One unbroken Christmas Eve wrapped all the way round a glass drum:

- **a village** of four houses and a church with a tall spire;
- **the village Christmas tree**, its star on top and its baubles lit;
- **a forest** with two reindeer nose to nose;
- **a snowman** between two firs, in falling snow;
- in the sky, **Santa's sleigh and two reindeer crossing the full moon**, a
  crescent moon over the village, stars and snowflakes;
- **snowy ground** all the way round;
- a slate base ring and rim, with **snow lying on the rim** and hanging over
  its edge in drips.

It is a hollow shade over a battery LED tealight, open at both ends: it lifts
off and goes back down over the light. Inside it is 68 mm across at its foot
(77.4 mm above it): a low foot inside the base ring carries the maker's mark.

The maker's mark, OBC, is engraved 0.8 mm into the underside of that foot,
at the front, mirrored so it reads from below.

Lit from inside, the scene shows dark on the glow: the glass is 1.3 mm, the
scene stands 1.6 mm out of it, and the thicker plastic passes less light,
the way a lithophane does. It works printed all in white.

It measures 89.7 × 89.7 × 103.3 mm.

`images/` holds renders of the model: `*_colour_*` in its two filament
colours, `*_night*` printed in white and lit by a point light where the
tealight's flame goes, and `*_as_printed_*` from the sliced toolpath. They
are renders, not photos of a print; how dark the scene reads on a real print
depends on the filament and the light.

**Print this:** `drum_lantern.3mf`. One object with five parts, already
aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| frame | the base ring and the rim | slate `#2E3440` |
| glass | the glass drum | white `#F4F1EA` |
| art | the panorama on the glass | slate `#2E3440` |
| bead | the roll of snow along the rim | white `#F4F1EA` |
| drape | the snow hanging over the rim's edge | white `#F4F1EA` |

Two filaments.

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **2 h 7 m** | **20.8 m, 62 g** |
| two colour, AMS | slice in Bambu Studio for the real time and purge | about 62 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock).

## How the panorama is made

OpenSCAD cannot bend geometry. The panorama and the snow's drape are built
flat in `drum_lantern.scad` (`art_flat`, `drape_flat`), stepped out of the
glass the same way as the other lanterns' scenes, and `../lantern_mesh.py
wrap` bends them round the drum: along the glass becomes round it, out of
the glass becomes out from it. They are subdivided to 2.5 mm first, so a
long edge follows the curve to within 0.02 mm. The scene is drawn so nothing
crosses the seam but the snowy ground. `build.sh` does all of it.

## Verified before shipping — on the real exported meshes

- `../lantern_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.30 mm, median 1.94 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (103.4 mm);
  - 25.5 cm² of bed contact, 32% of the footprint; centre of mass over it.
- `print_fidelity` (the colour slice compared with the model, layer by
  layer): 0.56 mm³ of 94,260 mm³ not printed, 0.11 mm³ printed that was not
  modelled, nothing in the wrong colour. **0 flags.**
- `fragility`: 0 high, 0 watch, no slender runs.

## What it took

- **The maker's mark** was first cut into the base ring's own 5.8 mm
  underside and then its curved inside face; on both the slicer propped the
  letters. The foot inside the ring widens the underside to 10.5 mm, and the
  mark sits there.
- **The scene's undersides** climb 1.6 per 1 out, as on the hex lantern,
  whose first slice at 1.2 propped its stars and eaves.
- **The wrap** first came out with two edges shared by four faces, where two
  pieces of the relief touched along a line at the snowman's waist, and the
  welded lantern with thirteen zero-volume slivers beside it. The wrap now
  welds the flat relief to a copy of itself shifted 0.003 mm before bending
  it, and drops anything that encloses no volume.
