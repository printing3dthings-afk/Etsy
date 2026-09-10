# Haunted Manor Lantern — printing notes

Hollow Victorian house shell, lit from inside. Tealight or LED sits under it
through the open base; light escapes only through the windows and door.

| | |
|---|---|
| size | 98.1 × 87.8 × 163 mm |
| volume | 106.6 cm³ |
| **time** | **6h 20m** |
| filament | 116.8 g |
| supports | none — see the overhang note |
| brim | none — the base footprint is large and open |

**6h 20m is over this shop's 4h/unit ceiling and that is a deliberate open
question, not an oversight.** See "The size decision" below.

## Verified

- watertight, **1 body**, 0 degenerate faces
- **CGAL `Volumes: 2`** — the skill's signature for a genuinely OPEN shell. A
  sealed hollow reports 3. This is the check that proves it is a lantern and
  not a shape with holes in it.
- **no CGAL errors** on the final render. Two `The given mesh is not closed`
  errors appeared mid-build, one per jack-o'-lantern: neighbouring teeth in
  the carved grin met at exactly one coincident point, which is a non-manifold
  2D union. Overlapping them by 0.15 mm fixed it. Worth knowing that OpenSCAD
  still produced an STL that gated watertight while those errors were on
  screen — the error line is the only place it shows.
- zero gap fill in the slice
- longest true unsupported span **0.94 mm** (the clapboard groove ceiling).
  The slicer's longest single bridge move is 73.9 mm at z 68.2, which is a line
  running *along* that ledge, not across a void — re-confirmed on this build by
  measuring the down-facing area in that layer band: **311.8 mm²** against
  ~355 mm² predicted for perimeter × groove depth, the shortfall being where
  windows and the turret junction interrupt the ring. Every other extrusion
  type tops out at 22.2 mm.

## Every period detail here is also the printable choice

- **A steep Victorian roof is the printable one.** The roof's INNER face is the
  overhang and pitch from *vertical* is what matters: a 45° cottage roof sits
  exactly on the 55° limit; this one is far steeper and has room to spare.
- **Gothic lancet windows are self-supporting; round-arched ones are not.** An
  equilateral arch's apex tangent is 60° from vertical, just over the limit.
  The lancet here is drawn to land near 50°.
- **Mullions are structural, not decoration.** They are subtracted from the cut
  so they survive as material, and they break a 22 mm opening into four panes
  under 5 mm wide — so every pane roof is a trivial bridge instead of one wide
  one.
- **Clapboard is cut as grooves, not built as raised boards.** Technique 52:
  relief cut into a shell is capped by the wall, so the wall carries it — the
  outer face sits at plan(+0.84) and the groove floor at plan(0), leaving
  1.68 mm (4 extrusions) at the thinnest point.

## The Halloween detail is light and silhouette, never relief

The first pass put flat bosses on the walls — a 22 mm bat standing 2.2 mm
proud — and two jack-o'-lantern faces cut 0.9 mm into them. Rendered straight
on, the bats read as scribbles: a 22 × 3 mm wing lying on clapboard is the same
tone as the clapboard, and its only cue is a shadow a shelf lamp will not give
it. The lantern faces were worse than useless — 0.9 mm pockets in a boss on a
**solid** wall, so they were blind. Dark faces on a product whose entire promise
is that it lights up.

What replaced it is the two things that survive at 90 mm on a shelf, neither of
which needs support:

- **Real 3D objects standing on the ground.** A two-step porch grows straight
  off the build plate — the lower tread *is* the build surface, so there is no
  underside anywhere — and carries a jack-o'-lantern either side of the door.
  Each is a hull of a 4.2 mm disc on the tread and a 6.4 mm sphere above it, so
  the sides lean out at 20° from vertical and the only true overhang is the top
  of the dome, which is the printable end. A pumpkin floating on a wall is a
  boss; a pumpkin on a step is an object.
- **Through-cuts that glow.** The face is cut 26 mm deep in Y — from outside the
  dome at 45.8 through the wall's inner face at 33.2 — so it is a window into
  the lit interior. The spiderweb rose window above the door is eight radials
  and two rings left as material inside a 22 mm opening, which is the same
  trick the window mullions already use. Two bats are cut clean through the
  tower's two exposed faces, where a 16 mm wingspan covers 62% of a 26 mm face.

**The grin is carved, not bridged.** The first mouth was one flat 8.3 mm
ceiling and PrusaSlicer's stability check named it exactly — *Floating bridge
anchors* — because both ends of that bridge landed on the dome's own leaning
surface rather than on anything solid. Cutting it instead as four overlapping
apex-up teeth removes every horizontal ceiling: the opening's top boundary is a
zigzag at 64° from horizontal, the same self-supporting logic as the lancet
windows. Eyes and nose are apex-up triangles for the same reason.

**The front ground floor has no windows on purpose.** It is the entrance
elevation. With windows at x = ±19 as well, a lantern big enough to read
reached z = 20, which is exactly where those sills started. Ten windows, a
door, a rose and two bats are already more openings than the shell needs.

**Bat height is fenced by the tower's own windows, not chosen by eye.** The
lower twin's lancet apex lands at z = 60.8 and the upper twin's sill at 82, so
a bat centred at 71 clears both by about 7 mm. At the first attempt (z = 63)
the wingtips merged into the lancet head and read as a fault, not a bat.

## The one thing that dictated the whole construction

OpenSCAD 2021.01's CGAL **aborts outright** — assertion violation in
`applyUnion3D`, not a warning — when unioning two TEXTURED surfaces that
interpenetrate. Bisected directly: body alone renders, turret alone renders,
plain-turret-into-textured-body renders, textured-turret-into-plain-body
renders, and only textured-into-textured fails; moving them apart also renders,
which proves it is the intersection curve and not the solids.

So every union here is plain-against-plain or plain-against-textured. The body
and turret are plain prisms of one shared 2D plan, the clapboard is cut
afterwards, and the two shingled roofs never touch each other (checked: at the
turret roof's springing the main roof is 12.9 mm from the axis and the turret
needs 17.5).

## Faults found and fixed while building it

Each of these rendered, and most gated watertight:

- **The turret roof was a detached 5.6 cm³ body.** A roof that merely sits on
  its wall at one shared plane is two solids touching, not one. The eave flares
  are what turn each of those planes into a real interpenetration.
- **Every window cut was 228 mm long and centred on the far face**, so each
  opening punched a matching hole through the wall opposite — the door cut a
  door-shaped hole in the back of the house. Combined with the grooves this
  left 19 loose fragments. Grooves alone gave 1 body; windows alone gave 5.
- **The windows were tall enough that the two rows overlapped each other** and
  reached into the roof, and every collision with a groove isolated a sliver.
- **The cavity stopped at body_top instead of eave_z**, leaving the 4 mm band
  under the eave solid with a slab of it floating loose inside.
- **The chimney was rooted in the roof**, which puts its base entirely inside
  the cavity and cuts it free. It became an exterior stack, which is where a
  Victorian house puts one anyway.
- **On the back wall that stack ran straight through a window.** Scott caught
  this in the viewer. The stack sat at x 17…33 while the back window at x = +19
  spans 13.5…24.5 — the window cut a window-shaped hole through the masonry.
  It is now on the **+X wall**, whose windows are at y = ±17, leaving 23 mm of
  uninterrupted masonry between them to land on.

## The one warning the slicer still gives, and where it actually is

PrusaSlicer reports **Collapsing overhang**. It is not new — the same warning
is on the version before any Halloween work — and it was worth locating rather
than living with, so it was bisected by slicing partial models:

| model | warning |
|---|---|
| outer solid form only | clean |
| solid − cavity (the bare shell) | clean |
| solid − cavity − openings | **Collapsing overhang** |
| same, with the window transom bars disabled | clean |

So it is the **transom bars** — the horizontal glazing bar left as material
across each window. Each one is 1.68 mm tall and 1.68 mm deep, and the mullion
splits its span into two bridges of **4.66 mm**. That is a span a P1S bridges
without comment; the flag is the slicer's island heuristic, not a real risk.
Making it strictly self-supporting would need a ceiling rising at 35° over the
half-light, which is 1.63 mm of rise inside a 1.68 mm bar — it cannot be done
without a chunky 3.3 mm transom on a 20.8 mm window. Left as is, deliberately,
and recorded here so nobody hunts it again.

## The size decision

At 163 mm tall this is a 6-hour print. The levers, in order of effect:

1. **Height.** Most of the volume is roof and turret.
2. **Wall.** Nominal 2.52 mm because the groove is budgeted into it. Dropping
   the inner offset to 1.26 mm gives a 2.10 mm wall and 1.26 mm at the groove
   floor — still 3 extrusions — for about 17% less shell.
3. **Scale.** 80% would land near 4h, but it also shrinks the wall below whole
   extrusions, so it needs the parameters re-solved rather than a scale factor.

Not applied yet — this is a pricing question as much as a design one.
