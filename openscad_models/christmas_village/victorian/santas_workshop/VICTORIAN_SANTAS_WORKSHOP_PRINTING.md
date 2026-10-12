# Victorian Santa's Workshop — printing notes

The village's centrepiece, built 2026-10-11/12. Scott asked for the workshop
to be redone: "It needs to be the center piece of the village. It needs to be
bigger and more magical within the theme." His answers to the questions
first: the tallest building in the village (about 190 mm), a glowing toy
workshop inside with the toys drawn on its glowing windows, a NORTH POLE sign
and striped pole, the village's four colours, and the same idea in each
village's style. From five shapes (`../../concepts/santas_workshop_forms.jpg`)
he asked for a mix of the workshop castle and the toy factory, and of the two
mixes (`../../concepts/santas_workshop_castle_factory_mixes.jpg`) took A.

The first workshop (one long brick room, one big toy window) is kept in
`../santas_workshop_v1/`.

It is **a toy factory that is also a castle**:

- a brick hall under **three sawtooth roofs**, each tooth's tall upright face
  glazed with three segmental lights, so the roofline glows from inside; two
  more lights in the left end;
- **four round brick turrets** at the corners under slate cones with snow on
  their crowns and finials, the back two taller, two little windows in each;
- a **crenellated gatehouse** out of the front, snow on its merlons:
  slate doors with wreaths and white bows on a step, the SANTA'S / WORKSHOP
  sign over them, a rose window above;
- **seven big arched toy windows** round the hall, each with its own scene
  drawn on the glass in dark lines: rocking horses, trains, teddies, drums,
  sailboats, toy soldiers, jacks-in-the-box and gifts, on the floor and on a
  shelf;
- **two brick chimney stacks**, the village's tallest points, with corbelled
  caps, snow, and evergreen garlands with bobbles;
- a **candy-striped NORTH POLE** at the front corner, a white ball on top
  and a NORTH POLE sign on knee braces;
- a white soffit and icicles under the right end's eave;
- a soft snow base with drifts.

It is a hollow lantern lit from inside by a battery LED tealight: open base,
every window glazed. Inside walls under the two roof valleys carry the
sawtooth, each cut through by a tall lancet arch, so one tealight in the wide
middle bay lights all three; the turrets open off the hall through lancet
doorways, the gatehouse through a lancet arch.

It measures {{SIZE}} mm, snow base and stacks included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_santas_workshop.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the hall and its inside walls, the turrets and their corbels, the gatehouse and merlons, the chimney stacks, the window collars, the step, the pole's red stripe | brick red `#A8483A` |
| roof | the roofs and their slates, the turret cones, the doors, the sign boards, the NORTH POLE board and braces, the toys and lines drawn on the glass | slate `#2E3440` |
| trim | snow base and drifts, snow on the roofs, cones, merlons and stacks, every frame, sill, pane and bar, the copings, the soffit and icicles, the letters, the pole's white stripe and ball, the finials, the wreaths' bows | white `#F4F1EA` |
| accent | the wreaths and the chimney garlands | evergreen `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** {{SUPPORT_LINE}}
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

{{COST}}

## Verified before shipping — on the real exported meshes

{{VERIFIED}}

## What it took to print without supports

The first slice of the finished model asked for supports in eleven places.
Every one was a real overhang and was fixed in the model, not in the slicer:

- **The cone slates.** Each ring of slate was a flat step 0.9 proud, so every
  ring's foot was a ledge and the slicer propped all four cones from the
  table. Chamfered at 50 degrees, each lip was still a thin wedge with air
  under it. They are now the toy shop's courses: an upright foot standing on
  the ring below, sloping back into the cone.
- **The snow on the cones** ended in a level ledge 1 mm proud. Its wavy foot
  is now an upright face standing on the cone.
- **The turrets' hollows** started 0.6 narrower than the rooms under them,
  a ledge round the top of every turret. They are now as wide as the room and
  parallel to the cone.
- **The pointed arches** through the inside walls and into the gatehouse were
  equilateral, whose crowns meet at 30 degrees. They are lancets now (radius
  six times the half-span), crowns at 56 degrees, the same height. The
  turrets' doorways are the same lancet.
- **The chimney caps, garlands and the finials** all flared at exactly 45
  degrees, which the slicer props. They flare at 36 to 52 degrees now, and the
  garlands' bobbles stand on cones instead of hanging as whole spheres.
- **The merlons' snow** ran straight across the crenels and stood 0.3 past
  the stone. It now caps each merlon only, flush.
- **The merlons' corners** were square on a brick block with 1.5 mm rounded
  corners, so each corner hung past the block. They are rounded to match.
- **The NORTH POLE sign's braces** stood in front of the board with their
  tips clear of the pole. Each is now the hull of a strip sunk in the pole and
  the board's end, its underside climbing 50 degrees.
- **The right end's eave** ran 2 mm past the wall, so its lowest edge was its
  tip, in air. It runs 1 mm out over a white soffit climbing 55 degrees from
  the wall; the icicles hang from the soffit. (Before this the icicles had all
  fallen inside the toy window's keep-out and none was made.)
- **The gatehouse's room** ran 3 mm into the hall, so its ridge cut up through
  the hall's roof behind the gatehouse and left the gatehouse's back 0.5 mm
  thick. It now stops a wall short; the pointed arch is the way through.
- **The OBC mark** sat 0.2 mm from the base's edge. It is 1 mm further in.

**And the tealight did not fit.** With three equal roof teeth the inside
walls cut the hall into bays 38.7 mm wide: no room for the village's 46 mm
circle, and a 38 mm tealight only with 0.3 mm to spare. An inside wall cannot
open wider than a lancet whose crown stays under its valley (24 mm), and a
flat doorway 49 mm wide was tried and failed the gate: its lintel's edges print
as perimeters over air. So the middle tooth is wider (51 mm against 36.5 at
the ends) and every tooth climbs 55 mm instead of 47, which keeps the middle
ceiling at 47 degrees and the end ones at 56; the chimney flues moved into
the two end bays. {{TEALIGHT}}

And one found by `print_fidelity`: the window collars' support columns
stopped 0.1 short of the inside walls, a sealed hairline slit down each. The
inside walls' feet are 0.3 thicker, up to the eave.

## Honest weak points

- **The toys are line drawings about 0.8 mm wide**, the old workshop's
  toys and drawing rules; small details are at the limit of a 0.4 mm nozzle.
- **Raised details have sloped undersides.** That is how they print without
  supports.
- **The roofs and cones are solid slate**, so the light comes out through the
  windows, not the roofs.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
