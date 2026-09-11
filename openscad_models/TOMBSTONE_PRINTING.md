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
| **stone, `plate` style** | 88 × 28 × 118 | **2h 48m** | 49.9 g |
| stone, `carved`, gag | 88 × 28 × 118 | 3h 02m | 51.5 g |
| stone, `carved`, memorial | 88 × 28 × 118 | 3h 02m | 51.5 g |
| **plaque, gag** | 57.6 × 41.6 × 4 | **21m** | 6.1 g |
| plaque, memorial | 57.6 × 41.6 × 4 | 19m | 6.0 g |

A first `plate` unit is **3h 09m**; every reorder after that is **21 minutes**.
`carved` is 3h per unit, every unit. Both are inside the ~4h-per-unit target
this shop designs to, and `plate` is the only one of the two that stays there
as volume grows.

Carving costs 14 minutes and 1.6g over the blank-recess stone — the incised
strokes add perimeters, nothing structural.

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

Modelled, not implied — 10 edge chips, 16 pits on the front, 12 on the back,
one hull-chained crack. **The back is pitted too, and that is not decoration for
its own sake:** rendered without it the stone reads as two different objects
joined at the edge, a weathered front and a moulded plastic back. The back
carries no crack (one is enough — the same crack on both faces reads as a crack
straight *through* the stone) and fences the maker's mark the way the front
fences the panel.
Every seed is fixed, so the chipping is identical on every render; two stones
off the same file are the same stone.

Two things in there exist because of specific failures:

- A chip is only placed where the outline is **exposed**. One landing on the
  stone's bottom corners sits entirely inside the socle, and a cut with no path
  to open air is not a chip — it is a sealed bubble that counts as its own body.
- A chip centre is interpolated **along** an outline segment and pushed out
  along that segment's normal, never snapped to a vertex. Snapped to a vertex it
  put the sphere's surface exactly through the point where two facets meet and
  CGAL emitted zero-area facets at three of the ten.

The crack cuts 1.1mm deep at the top and 0.55mm at the bottom, and stops at
z=66 — clear of the inscription panel in both styles. An earlier version faded
to a 0.06mm kiss on the face, which is a surface tangency rather than a shallow
crack, and it ran down through where the customer's name goes.

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
| stone, `carved`, memorial | **FAILED**, 10 zero-area faces |
| plaque, gag | **PASSED**, 0 |
| plaque, memorial | **PASSED**, 0 |

`mesh_gate.py` reports a handful of zero-area faces on some `carved` strings
(10 on the memorial set; none on the gag set, none on either plaque, none on
the blank stone). **They are a triangulation artifact, not geometry,
and they were located rather than guessed at:** all ten sat at *one* z on the
y=6 plane, spanning exactly the width of the bottom text row. Every letter in a
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

A second colour is not needed and would not help: the letters read on relief and
shadow, and a two-tone stone reads as plastic.

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
