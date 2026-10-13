# Gingerbread Santa's Workshop — printing notes

The village's centrepiece, built 2026-10-11/12 alongside the Victorian one
(`../../victorian/santas_workshop/`), which has the full story of the brief
and of every printability fix: the two share one layout and differ only in
their skin. Scott asked for the workshop to be "the center piece of the
village … bigger and more magical within the theme," the same idea in each
village's style, and picked the castle-factory mix.

The first workshop (a round gingerbread drum with a loading wing) is kept in
`../santas_workshop_v1/`.

It is **a gingerbread toy factory that is also a castle**:

- a gingerbread hall under **three chocolate sawtooth roofs**, each tooth's
  tall face glazed in icing with three lights, so the roofline glows from
  inside; two more lights in the left end;
- **four round gingerbread turrets** at the corners, each under a frosted
  ledge with icing drips and a chocolate shingle cone with icing on its crown
  and a red gumdrop on its point, the back two taller;
- an **iced gatehouse** out of the front, red and white gumdrops on its
  battlements: chocolate-bar doors with a peppermint on each leaf, the
  SANTA'S / WORKSHOP sign over them, a rose window above;
- **seven big arched windows** round the hall, each with its own toys drawn
  on the icing glass in chocolate lines. Behind the glass every line stands
  1.8 mm out of the pane, so lit from inside the toys show as dark outlines
  on the glow even printed all in white, the way a lithophane works;
- **two candy-cane chimney stacks**, the village's tallest points, white with
  red stripes winding up them;
- a **red-and-white NORTH POLE** at the front corner, a white ball on top and
  a NORTH POLE sign on knee braces;
- a white soffit and icing drips under the right end's eave;
- a soft snow base with drifts and red and white gumdrops.

A hollow lantern lit from inside by a battery LED tealight: open base, every
window glazed. Inside walls under the two roof valleys carry the sawtooth,
each cut through by a tall lancet arch, so one tealight in the wide middle
bay lights all three; the turrets open off the hall through lancet doorways,
the gatehouse through a lancet arch.

It measures 206 × 129 × 192, snow base and stacks included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. They are renders, not photos of a print.

**Print this:** `gingerbread_santas_workshop.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the hall and its inside walls, the turrets, the gatehouse and its battlements, the window collars, the step | gingerbread `#C68642` |
| roof | the roofs and their shingles, the turret cones, the chocolate-bar doors, the sign boards, the NORTH POLE board and braces, the toys and lines drawn on the glass | chocolate `#5A3825` |
| trim | snow base and drifts, icing on the roofs, ledges, cones and battlements, every frame, sill, pane and bar, the copings, the soffit and drips, the letters, the chimneys' white, the pole's white stripe and ball, the white gumdrops, the peppermints' white | icing white `#F7F3EE` |
| accent | the chimneys' and the pole's red stripes, the red gumdrops, the peppermints' stripes | candy red `#D7263D` |

## Settings that are not optional

- **Supports OFF.** The slice of the four parts together needs none: 0 support moves and 0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **11 h 56 m** | **282 cm³, about 350 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 350 g of model **+ purge**; 2,343 filament changes |

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the CGAL union of the four parts
  (2026-10-12):
  - watertight, one body;
  - 1st-percentile wall 1.48 mm, median 2.86 mm, against the 1.2 mm floor
    (it was 0.70 mm before the fixes below);
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (192.0 mm);
  - 77.36 cm² of bed contact, 29% of the footprint;
  - centre of mass over the base.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 49.1 mm³ of 412,301 mm³ is not printed, 3.6 mm³ printed that was
  not modelled, 20.3 mm³ printed in another colour. **7 flags:**
  - three 0.3 mm slivers of icing glass beside the rose window's spokes
    (0.07-0.43 mm³ each): too narrow to extrude; the spokes and the glass
    print;
  - two 0.5 mm slivers at the wavy foot of the roof snow over a shingle
    (0.24 and 0.28 mm³);
  - one layer of one sign letter's top (0.08 mm³);
  - one layer (0.2 mm) of the right candy-cane chimney printed in
    gingerbread instead of its white skin, 19 mm³, where the chimney is
    inside the hall below the roof. It cannot be seen; the same layer was
    clean on an earlier slice of the same model.
- `fragility`: nothing slender enough to snap. 0 high, 0 watch; the most
  slender runs are the snow base's lips, slenderness 1.6.
- Renders: `images/*_colour_*` from the four parts, `images/*_as_printed_*`
  from the four-colour toolpath (outer walls, skins and overhangs: what any
  outside view sees).

## What it took to print without supports

Every fix in the Victorian notes applies here, made once in the shared layout.
These were this skin's own:

- **The candy-cane stripes** were cut to a ring 2 mm wider than the chimney,
  so they stood out of it as helical ribs, every underside an overhang (1,342
  overhang perimeters on their own). They are cut to the cane's own outline
  now, flush.
- **Five of the base gumdrops** stood past the snow base's edge, and one sat
  inside a turret's hollow. Every one is now its own width inside the base.
- **The chocolate-bar doors' scores**: each groove's upper flank climbed 40
  degrees and its mouth left a 0.2 mm level lip; the two upright scores ran
  up into the arch under the white frame. The grooves' roots are lowered so
  the flank climbs 50 degrees, and the upright scores stop short of the arch
  under pointed tops.
- **The toys on the glass had never been printed at all.** The room was cut
  out of the chocolate part, which holds them, and took everything that
  stood out of the back of the pane with it: lit, the windows would have
  shown no toys. The room now stays off that space, and the lines stand
  1.8 mm out instead of 0.8 (2026-10-12).
- **The wall check failed** at a 1st percentile of 0.70 mm on three things:
  the roof snow rose 0.6 above each coping as a 0.3 mm fin; the glazed
  teeth's frame heads were 1.2 mm wedges at their face; and the turrets'
  doorway jambs met the round walls at 70 degrees, a knife edge of wall.
  The snow starts flush with the coping, the frame heads are full depth,
  and the jambs are radial.
- **The roofs end flush with the smooth walls.** Past them, each slab's corner
  at a valley began in air.

## Honest weak points

- **The toys are line drawings about 0.8 mm wide** on the outside; small
  details are at the limit of a 0.4 mm nozzle. Behind the glass they are
  1.4 mm wide, and each line's sloped underside reads in the glow as a soft
  shadow under it.
- **The glow outlines have not been seen lit yet.** 3.3 mm of plastic on a
  line against the pane's 1.5 is the lithophane rule of thumb; how dark they
  read depends on the filament and the light.
- **Raised details have sloped undersides.** That is how they print without
  supports.
- **The roofs and cones are solid chocolate**, so the light comes out through
  the windows, not the roofs.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
