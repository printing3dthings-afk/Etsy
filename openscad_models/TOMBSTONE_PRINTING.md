# Personalized Tombstone — printing notes

`openscad_models/tombstone.scad`. One file, **two personalization modes** and
**two text layouts**, all from the same geometry.

| flag | values | what it changes |
|---|---|---|
| `style` | `plate` · `carved` | plaque seated in a recess, or the name cut straight into the stone |
| `text_set` | `gag` · `memorial` | R.I.P./HERE LIES/`<name>` · `<name>`/`<dates>`/`<line>` |
| `part` | `all` · `stone` · `plate` | which piece to export |

`carved` is one seamless object and every order is a fresh render, slice and
full print. `plate` lets the stone be **batched as stock** and only the plaque
printed per order — 20 minutes and 6 grams instead of three hours and 50.
An inset plaque is a real monument detail, so the reveal around it reads as
intentional rather than as a seam.

## Real print cost — sliced, not estimated

Sliced against `tools/p1s_slice_profile.ini` as it now stands.

| part | outside | time | filament |
|---|---|---|---|
| **stone, `plate` style** | 88 × 28 × 118 | **3h 04m** | 50.5 g |
| stone, `carved`, gag | 88 × 28 × 118 | 3h 19m | 52.2 g |
| stone, `carved`, memorial | 88 × 28 × 118 | 3h 19m | 52.2 g |
| **plaque, gag** | 57.6 × 41.6 × 4 | **21m** | 6.1 g |
| plaque, memorial | 57.6 × 41.6 × 4 | 20m | 6.0 g |

A first `plate` unit is **3h 25m**; every reorder after that is **21 minutes**.
`carved` is 3h 19m per unit, every unit. Both are inside the ~4h-per-unit target
this shop designs to, and `plate` is the only one of the two that stays there
as volume grows.

Carving costs 15 minutes and 1.7g over the blank-recess stone — the incised
strokes add perimeters, nothing structural. The two weathering rebuilds of
2026-09-11 cost about 16 minutes and 0.6g between them on top of the numbers
this table held before them; modelled surface is real geometry, not a texture
map, so it is not free — it is just cheap.

## Orientation — upright, and that is the whole design

**Print it standing up. No supports, no brim, no rotation in the slicer.**

The tablet is a 2D outline extruded through its thickness, and the outline only
ever *narrows* going up, so every face on it is vertical or up-facing: the mesh
gate measures **2.0 cm² past 55°** on the whole stone and every bit of it is a
chip, a pit or the recess ceiling, none of it structure. The socle's top
chamfer is 45° from vertical (2.6mm in over 2.6mm up), up-facing,
self-supporting.

Printed this way the layer lines run **horizontally across the face**, which on
a gravestone reads as sedimentary strata. This is the rare part where the
orientation most prints fight is the one that flatters it — do not lie it down
to "save time", it will need supports across the whole face and gain nothing.

The plaque prints **face up, back on the bed**: zero overhang anywhere
(gate: 0.00 cm²), and the raised letters are the last thing laid down on a flat
top surface, which is the best surface an FDM machine produces.

## The recess ceiling is the one real bridge

Measured from the g-code, not from the model — the slicer picks the bridging
direction, not you. Every layer with bridge extrusion on the stone:

| z | bridge mm | longest line | what it is |
|---|---|---|---|
| 17.4 | 2614 | 33.8 | solid infill over sparse, inside the socle |
| 30.4 | 647 | 8.9 | same, over the maker's mark |
| **73.2** | **408** | **58.1** | **the plaque recess ceiling** |
| 110–117 | 360 | 10.0 | same, closing the crown |

Only the 73.2 line is a real open-air bridge, and it is a 3.2mm-deep ledge
fused along its whole 58mm back edge — a standard recess ceiling, not a free
span. Expect it slightly rough; the plaque covers it. The 0.2mm per-side
clearance absorbs any droop.

## Fit

`pl_clr = 0.2` per side — the standard slip fit for two *separately printed*
parts, the same number measured on this shop's snap box (0.190) and on a real
tongue-and-groove case lid (0.195). The plaque is 57.6 × 41.6 in a 58 × 42
pocket and rests on the pocket floor. Do **not** glue it in for a first fit
test; if it is tight, print the plaque with Bambu Studio's XY contour
compensation at −0.05 rather than editing the model.

## Lettering

`Noto Serif Bold`, not the Trajan-style face this started with.
Cinzel Decorative is the right *look* for a monument and is unprintable at
these sizes: measured on the real cutter, **13–34% of its strokes fall under
one 0.42mm extrusion**, and a recess narrower than one bead is not cut at all —
it comes out as broken scratches. Noto Serif Bold measures **0.0% under a bead**
at every size used here, lower quartile 1.3–2.6 extrusions.

**Stone letters are incised (1.2mm); plaque letters stand proud (1.0mm).** That
is a material decision, not a style one: a cut stone is incised, a plaque set
into one is cast, and cast letters stand proud. It is also the more forgiving
of the two — a raised stroke under one bead wide still prints as a single bead
ridge, where the same stroke incised is simply not there.

### Name length

The name auto-fits: the nominal size in `rows_gag`/`rows_mem` is a **ceiling**,
and a long name shrinks to fit the panel. OpenSCAD 2021.01 has no
`textmetrics()`, so the font's own per-character advances are baked into `ADV`
straight out of its hmtx table; OpenSCAD renders `text()` at a stable 1.34× the
advance sum (measured across five strings, 1.337–1.341).

Below about **size 6** the strokes stop being reliably printable. That is a real
limit of roughly:

- **8–9 characters** on the plaque (`plate`, 50mm of usable width)
- **10 characters** carved (`carved`, 60mm)

Longer than that and the name still renders — it just gets too fine to print
well. Check the fitted size before committing a long one.

## Weathering

**Rebuilt 2026-09-11** (Scott, on the first version: *"it looks like a cheese
style cut out"*). He was right, and the reason is worth writing down: every scar
on that version was **one sphere**, and a sphere pushed into a flat face can
only ever cut a circular rim around an evenly curved bowl. Thirty-eight of
those, each biting the same fraction of its own radius, is a wheel of cheese.
The regularity was the tell, not the size. Nothing outside this section changed.

### Second pass: the edges are hard because granite's are

Scott again, on the first rebuild: *"still too rounded looking on the chips…
make use of reference to other tombstones with chips from online sources."*
He was right a second time, and the reason is that the first rebuild made the
scars irregular while still hulling **spheres** — so every rim was still a
smooth curve. This time it was checked against how stone actually breaks
instead of guessed at twice.

[Rock & Gem](https://www.rockngem.com/conchoidal-fracture-lucky-break/), on
conchoidal fracture, settles the material question outright: *"Unlike the
**jagged breaks of common granite**, a conchoidal break produces a surface
that catches light in a series of shimmering, curved arcs."* Granite — which
is what a headstone is — does not break in smooth curves at all. Curved scars
were modelling obsidian.

The [ICOMOS-ISCS Illustrated Glossary on Stone Deterioration
Patterns](https://iscs.icomos.org/wp-content/uploads/2022/06/Monuments_and_Sites_15_ISCS_Glossary_Stone.pdf),
the standard reference for this vocabulary, gives the geometry directly:

| pattern | ICOMOS wording |
|---|---|
| **Fragmentation** | *"into portions of variable dimensions that are irregular in form, thickness and volume"*, substrate sound *"on both sides of the **detachment plane**"* |
| **Splintering** | *"detachment of **sharp, slender** pieces of stone"* (Fr. *"aux arêtes vives"* — live edges) |
| **Chipping** | *"breaking off of pieces… **from the edges** of a block"* |
| **Scaling** | detaching *"**parallel to the stone surface**"*, thickness *"negligeable compared to its surface dimension"* |
| **Rounding** | *"preferential erosion of **originally angular** stone"* |
| **Pitting** | *"generally have a **cylindrical or conical** shape"* — not spherical |

Every one of those says the same thing geometrically: a scar's floor is a
**plane**, its rim is a **straight-edged polygon**, and *rounding is what
happens to that later* — a separate decay pattern, not the default state.

### The primitive is a faceted flake, not a ball

Every scar is the convex hull of a **point cloud held near two parallel
planes** — not a hull of spheres. Hulling tiny cubes is how you take the convex
hull of a point set in OpenSCAD; 0.05mm of cube is slop too small to round an
edge. The result has a planar floor (the detachment plane), planar side facets
meeting it at hard angles (the rim), and **no curved surface anywhere on it**.
It is then stretched along one in-plane axis and spun to a random heading, so
nothing is round in plan and no two scars share a profile.

It is also **cheaper** than the sphere version — 8 vertices per point instead of
roughly 100 — which took a full carved render from 6m11s down to 2m48s.

Four things are randomised **separately**, and that is the point — one shared
"size" knob is what made the first version look stamped:

| | |
|---|---|
| `R` | how big the scar is |
| `d` | how deep it bites, **independent of** how big it is |
| `e` | how elongated it is in plan |
| `f` | how flattened it is into the face — a chunk taken out vs. worn-away surface |

A broad shallow flake and a small deep gouge are different events on a real
stone. Tying depth to radius made every scar the same event at five sizes.

### And they cluster

About a third of the scars carry one or two smaller satellites overlapping them.
Real spalling is not a Poisson scatter of isolated dots — one flake takes its
neighbours with it, and the compound scar that leaves, with a floor at two or
three levels, is the single biggest visual difference from the sphere version.

### Grain

The discrete scars are the events; the grain is the surface they happened to.
Forty-eight broad, hard-flattened flakes 0.35–0.7mm deep across the front, 30 on
the back, 11 on the socle. **Without it the stone between the chips is
glass-smooth, and under real light that one fact reads as plastic no matter how
good the chips are** — confirmed on a lit render before this existed, which is
the only kind of render that shows it.

0.4mm is the floor on purpose: at 0.2mm layers that is two layers of relief,
which shows. Anything shallower is under a layer, so the slicer does not cut it
and it would cost render and print time to produce nothing.

### Placement: by zone, not by scatter

The front is scarred in three zones rather than one scatter with a fence:

| zone | where | scars |
|---|---|---|
| crown | z 63–96, full width | 11, the big ones |
| sill | z 7–17, full width | 8 |
| flanks | \|x\| 29.5–34.5, z 20–60 | 12, small, allowed to run off the edge |

A uniform scatter loses half its candidates to the panel fence and the survivors
are almost all above it — the first attempt put nearly everything in the crown
and left the bottom two thirds bare, which reads as "the top weathered and the
rest is new". The **flanks** are what matter: they are the only scars level with
the inscription, and without them the middle of the stone is a blank rectangle
with a plaque sitting on it.

Nothing is placed on the panel — a pit through an inscription reads as a
misprint, not as age.

### The socle weathers too

A crisp moulded base under a chewed-up stone reads as two materials bolted
together, and the base is the part that would actually sit in dirt. Grain only,
no chips: the socle's edges are what the print stands on and what the eye uses
to read it as level. **Nothing is cut below z = 4.5** — that is the bed-contact
region and the ground line; a scar there costs first-layer adhesion and gains no
appearance.

### The crack

Cuts 1.1mm at the top down to 0.35mm, stops at z=66 clear of the panel in both
styles, and **forks** — the path is denser and no longer monotonic, with radii
that wander up as well as down and two short branches that split off and die. A
chain of steadily shrinking spheres tapers smoothly, which is the one thing a
fracture never does.

An earlier version faded to a **0.06mm kiss** on the face, which is a surface
tangency rather than a shallow crack, and it ran down through where the
customer's name goes.

### Four failures this section has actually produced

Every seed is fixed, so the chipping is identical on every render — two stones
off the same file are the same stone. These are the traps that cost real time:

- **A cutter whose centre sinks below the face can be swallowed whole.** Seating
  a spall at `face + R·f − d` bites `d` deep, but when `d` exceeds the cutter's
  own half-depth the centre goes under the surface and a small enough cutter
  ends up entirely inside the stone. That is not a shallow scar, it is a sealed
  void — the mesh still gates watertight and single-bodied, and the only thing
  that sees it is CGAL reporting `Volumes: 4` instead of 2. It happened on the
  flattened grain layer and again on cluster satellites. `d` is now clamped to
  `0.8 · R · f`, which keeps the centre outside the face *by construction* at
  every size rather than by a range that happens to work.
- **A cluster satellite must genuinely overlap its parent, not merely land near
  it.** At ±1.15·R with radii from 0.38·R the two solids could meet along a
  sliver, and where that happened at the stone's own silhouette it left a rind
  of stone 0.30 × 0.12 × 0.41mm standing free — **0.0015 cubic millimetres**,
  smaller than one extrusion bead in every dimension, and a separate body as far
  as the mesh is concerned. Isolating it took one render per cutter group: edge
  chips, grain and flanks were each clean alone, the crown clusters were not,
  and re-seeding the other two — twice — never moved it, which is the tell that
  a seed was never the cause. Satellites now sit within ±0.85·R with radii from
  0.45·R, so the overlap is at least 0.6·R by construction.
- **A chip is only placed where the outline is exposed.** One landing on the
  stone's bottom corners sits entirely inside the socle — same sealed-bubble
  class, reached a different way.
- **A chip centre is interpolated along an outline segment and pushed out along
  that segment's normal, never snapped to a vertex.** Snapped to a vertex it put
  the cutter's surface exactly through the point where two facets meet, and CGAL
  emitted zero-area facets at three of the ten.
- **The 0.06mm crack kiss above** — a fade that ends in tangency is not a fade.

## Maker's mark

"OBC" on the back of the socle line, 7.5mm, `Montserrat Black`, 0.8mm deep — not
the full wordmark, because at the same footprint every stroke of "OBC" is 3.4×
thicker, which is the difference between a mark that prints and one the slicer
drops entirely.

## Known: zero-area facets in `carved` mode

Where every build stands:

| build | gate |
|---|---|
| stone, `plate` (the stock blank) | **PASSED**, 0 zero-area faces |
| stone, `carved`, gag | **PASSED**, 0 zero-area faces |
| stone, `carved`, memorial | **FAILED**, 15 zero-area faces |
| plaque, gag | **PASSED**, 0 |
| plaque, memorial | **PASSED**, 0 |

`mesh_gate.py` reports a handful of zero-area faces on some `carved` strings
(15 on the memorial set; none on the gag set, none on either plaque, none on
the blank stone). **They are a triangulation artifact, not geometry,
and they were located rather than guessed at:** every one of them sits at `y =
6.00` exactly — the face plane — on just two z values, each the shared baseline
of one text row (10 on the bottom row, 5 on the dates row). Every letter in a
row shares a baseline, which puts 42 collinear vertices in a straight line
through a single large planar face, and CGAL's constrained triangulation
resolves that with slivers.

The mesh is still watertight, still one body, still Euler 2, its volume is right
to 0.1%, and **PrusaSlicer takes it with zero warnings and zero repairs**
(verified — the g-code above is from that exact mesh).

It is deliberately not "fixed": the string is whatever the customer types, so
any number nudged until CGAL is happy with `REST WELL` says nothing about the
next name. The gate should keep flagging it. If a future build wants it gone
for real, the fix is to stop the face being one big plane — a subtly crowned or
rock-faced front is a genuine monument detail and would remove the cause.

## Filament and plate

**Matte PLA in a grey** (Ash Grey / Nardo Grey) — matte is the whole point; silk
or glossy PLA fights the granite read. Smooth PEI plate. Standard 0.2mm layers:
0.1mm buys nothing here, because the horizontal layer lines across the face are
a feature and finer ones show it less.

The bed-contact face is the **bottom of the socle**, 88 × 28 — invisible in use,
so plate texture does not matter to the look.

A second colour is not needed for the stone itself — the carved letters read on
relief and shadow, and a two-tone *stone* reads as plastic.

## Four colours, if you want them

The model does split cleanly into **four printable colour regions**, and this is
worth knowing because **every boundary is a flat plane at a constant Z in the
print pose** — an ordinary filament change at a layer. No colour painting, no
AMS strictly required, no paint-the-region guesswork:

| # | region | boundary | how it prints |
|---|---|---|---|
| 1 | socle | world z ≤ 18 | filament change at layer z = 18 on the stone |
| 2 | stone body | world z ≥ 18 | — |
| 3 | plaque field | print z ≤ 3.0 | filament change at layer z = 3.0 on the plaque |
| 4 | raised letters | print z ≥ 3.0 | the letters are the last thing laid down |

Region 3/4 is the reason the `plate` style earns this and `carved` does not: on
the plaque the letters **stand proud and print last**, so the colour change is a
clean layer boundary. Carved letters are recessed into the face, which needs
real colour painting and gets you a worse result.

Two schemes rendered below. The bronze one is not a stylistic invention — a
bronze plaque on a granite stone is the standard real-world monument, and a dark
oxidised field with bright raised lettering is exactly what a two-filament
layer change produces.

Split the regions yourself with the four `intersection`/`difference` planes
listed above against `stone()` and `plate()`; the colours are assigned in the
slicer, not in the model, so nothing about the shipped STLs changes.

## Rendering a custom order

```bash
# a plaque for one order (the common case)
openscad -o plaque.stl -D 'part="plate"' -D 'style="plate"' \
         -D 'text_set="gag"' openscad_models/tombstone.scad

# stock stones, no name on them at all
openscad -o stone.stl -D 'part="stone"' -D 'style="plate"' \
         openscad_models/tombstone.scad

# one-piece carved, memorial layout
openscad -o stone.stl -D 'part="stone"' -D 'style="carved"' \
         -D 'text_set="memorial"' openscad_models/tombstone.scad
```

The name itself lives in `rows_gag` / `rows_mem` in the file — edit the string,
leave the size and z alone, the fit handles the rest.

**Always run the gate before sending anything to a printer:**

```bash
python3 tools/mesh_gate.py stone.stl --overhang
```
