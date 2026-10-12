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
  on the icing glass in chocolate lines;
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

It measures {{SIZE}} mm, snow base and stacks included.

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

- **Supports OFF.** {{SUPPORT_LINE}}
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

{{COST}}

## Verified before shipping — on the real exported meshes

{{VERIFIED}}

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
- **The roofs end flush with the smooth walls.** Past them, each slab's corner
  at a valley began in air.

## Honest weak points

- **The toys are line drawings about 0.8 mm wide**; small details are at the
  limit of a 0.4 mm nozzle.
- **Raised details have sloped undersides.** That is how they print without
  supports.
- **The roofs and cones are solid chocolate**, so the light comes out through
  the windows, not the roofs.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
