# Hex Carriage Lantern — printing notes

Built 2026-10-13. Scott picked it, with the drum and gift box lanterns, from
five lantern forms (`../concepts/lantern_forms.jpg`).

A six-sided carriage lantern:

- **six glass panels** between round corner posts, each with its own
  Christmas scene standing out of the glass: a village church under the moon,
  a reindeer leaping across the moon over two houses, the nativity under the
  star, a reindeer by a fir in the forest, a snowman in falling snow, and a
  Christmas tree with its baubles lit;
- **a pointed six-sided roof** with snow on its crown, the snow hanging in
  drips;
- **a red bow** on the front slope of the roof;
- **a hanging ring** on a collar at the top.

It is a hollow shade over a battery LED tealight: the base is open, so it
lifts off and goes back down over the light. Inside it is 61.4 mm across the
flats, room for any tealight.

The maker's mark, OBC, is engraved 0.7 mm into the inside face of the
plinth's front wall, where it reads when the lantern is lifted off.

Lit from inside, every scene shows dark on the glow: the glass is 1.3 mm,
the scenes stand 1.6 mm out of it, and the thicker plastic passes less
light, the way a lithophane does. It works printed all in white.

It measures 84.3 × 73.0 × 155.2 mm.

`images/` holds renders of the model: `*_colour_*` in its three filament
colours, `*_night*` printed in white and lit by a point light where the
tealight's flame goes, and `*_as_printed_*` from the sliced toolpath. They
are renders, not photos of a print; how dark the scenes read on a real print
depends on the filament and the light.

**Print this:** `hex_lantern.3mf`. One object with five parts, already
aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| frame | the plinth, posts, top rail, roof, collar and ring | slate `#2E3440` |
| glass | the six glass panels | white `#F4F1EA` |
| art | the scenes on the glass | slate `#2E3440` |
| snow | the snow on the roof | white `#F4F1EA` |
| bow | the bow | red `#C62F3A` |

Three filaments. In one colour, white is the one that glows.

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **3 h 40 m** | **25.8 m, 77 g** |
| three colour, AMS | slice in Bambu Studio for the real time and purge | about 77 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock).

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.30 mm, median 4.57 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (155.2 mm);
  - 13.5 cm² of bed contact, 22% of the footprint; centre of mass over it.
- `print_fidelity` (the colour slice compared with the model, layer by
  layer): 4.9 mm³ of 79,444 mm³ not printed, 2.2 mm³ printed that was not
  modelled, nothing in the wrong colour. **4 flags, 0.019 mm³ each:** one
  layer, 0.23 mm wide, along the crowns of the bow's two loops (z 113.4). The
  bow prints whole.
- `fragility`: 0 high, 0 watch, no slender runs. The hanging ring is 4 mm
  thick and 3.6 mm round its hole.

## What it took to print without supports

The first slices asked for supports in several places; every one was fixed
in the model:

- **The maker's mark**, cut under the plinth's 4.4 mm ring, came out as
  letters the slicer propped. It is cut into the plinth's inside face
  instead, each step in sloping its ceiling at the relief's 1.6 per 1.
- **The corner posts** stood 2 mm into the hollow over the open base, and
  the slicer propped them from the plate. They are trimmed flush with the
  glass inside.
- **The hanging ring's foot** was wider than the cap under it; the cap is
  wider now, and the ring's hole peaks at 60 degrees.
- **The scenes' undersides** climbed 1.2 per 1 out, which is 5 degrees
  inside the slicer's 45-degree threshold; where two of the relief's steps
  fell in one layer, the slicer propped the stars and the eaves. They climb
  1.6 per 1 now.
- **The stable's roof** in the nativity hung past its posts with a 1 mm gap
  under its ends; the posts stand under the ends now.

And to keep every wall a printable one:

- **The scenes are drawn for the nozzle**: no stroke under 1.3 mm, no gap
  under 0.8 mm, and a cleaning pass drops anything finer before the scene is
  stepped out of the glass. Where two outlines nearly touched, each step of
  the relief had repeated the hairline gap, and the relief came out a comb of
  0.1 mm teeth.
- **The bow's loops** are solid; with holes, their 1 mm rims were a fifth of
  the lantern's too-thin spans.
- **The snow's drips** stop short of the roof's hips, where the next face cut
  them into slivers.
