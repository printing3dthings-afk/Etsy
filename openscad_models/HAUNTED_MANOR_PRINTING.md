# Haunted Manor Lantern — printing notes

Hollow Victorian house shell, lit from inside. Tealight or LED sits under it
through the open base; light escapes only through the windows and door.

| | |
|---|---|
| size | 98.1 × 104.6 × 163 mm |
| volume | 127.8 cm³ |
| **time** | **7h 10m** |
| filament | 130.2 g |
| supports | none — see the overhang note |
| brim | none — the base footprint is large and open |

**7h 10m is a deliberate choice, settled 2026-09-10.** The shop's 4h/unit
figure is a goal aimed at the commodity end of the catalogue, not a hard stop —
Scott: *"The 4 hour was for other products when I started. That's still the goal
but not a hard stop limit."* This is a 163 mm lit display piece and is priced as
a lamp. "The size decision" below is kept as the recipe for a smaller variant,
not as an outstanding problem.

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

## The front porch

Scott asked for a porch with steps "so it looks more accurate". It is a real
four-column portico — deck, three treads, columns with plinths and capitals,
knee braces both ways, a frieze board, a flared cornice and a hip roof — and
it needed three things solved.

**Nothing in the substructure has an underside.** The deck and all three treads
start at z = 0, so the lower tread *is* the build surface. A porch is normally
the classic support case; here it costs nothing.

**The house had to grow to make room.** A porch roof has to clear the door
below it and the upper windows above, and the old ground floor left a 3 mm gap
between the two. Three more clapboard courses open that to 25 mm. `ridge_z` is
unchanged, so the house is exactly as tall as it was — the roof simply got
shallower, 39.5° from vertical, still well inside the limit. The door came down
to a 35.9 mm apex so the beam soffit at 40 clears its head.

**The ceiling span was measured, not guessed — and the intuition was wrong.**
The beam soffit is the one real ceiling in the porch. With two columns it
bridged **41.1 mm**. The obvious reading is that it should bridge front-to-back,
wall to beam, about 15 mm — but the slicer picks the bridging direction itself,
and it chose to run across the width. Two more columns took it to **16.1 mm**;
a frieze board along the wall (which is a real Victorian member anyway) carries
the back edge 5.2 mm out and holds it there. The four columns are load-bearing
in the literal sense — they are not styling.

**There is deliberately no balustrade.** One was drawn. A railing scaled
correctly to this house stands about 11 mm above the deck, and the lanterns are
11 mm tall: it hid both of them completely from straight on, which is the only
view a listing thumbnail gets. A low porch with no railing is a real and common
detail. Two jack-o'-lanterns nobody can see is not.

## The jack-o'-lanterns

Scott, on the first version: *"the outer ridges need to be very small. Almost
thin lines or small inward ridges made in modeling."* He was right. That
version was eight lobes swelling 2.2 mm out of a smaller core — real relief,
and far too coarse: it read as a gourd carved out of eight balloons.

The body is now a single smooth surface of revolution and the ribs are **cut
in, 0.35 mm deep and 0.9 mm wide** — under one layer deep and about one
extrusion wide, which is exactly a drawn line. Twelve of them, tapering to a
hairline at both ends the way a real crease does.

**A vertical cylinder cannot cut a crease like this.** It bites deep at the
equator and misses the shoulders entirely — which is what the first version's
two "ribs" actually were. The cut here is a 0.35 mm-thick **shell of the
gourd's own profile**, so it follows the surface at constant depth all the way
up, intersected with six thin slabs through the axis. Each slab gives two
opposite creases, and the slab width is absolute, so they stay thin lines
instead of widening at the equator.

The profile is a superellipse, `p = 2.5`. A plain ellipsoid is too narrow near
the top — the eyes broke through its silhouette — and its base flare reaches
62.7° from vertical, past the limit. 2.5 gives a squat, full-shouldered gourd
whose base flare tops out at 49.3°, on an 11 mm footprint.

The stem is a five-lobed profile tapered and twisted as it rises. **The flutes
are built, not cut** — cut as five vertical channels they were deeper than the
stem was thick at the top and sawed it into loose fins.

Each lantern stands 1.2 mm **clear** of the house wall, on the deck and nothing
else. Embedded in the siding it was tangent to the clapboard grooves along a
long shallow arc, and CGAL turned that into 13 zero-area faces and two inverted
sliver bodies — while still reporting the mesh watertight. A 77 mm² weld to the
deck is plenty; the wall was never carrying it.

### Four ways the crease cut broke first, none of which raised an error

1. **The profile apex was clamped to r = 0.001** rather than landing on the
   axis, to avoid a zero radius. That left a 10.5 mm near-axis edge for
   `rotate_extrude` to sweep and it could not close the result — *"The given
   mesh is not closed"*, twice, with **0.02 cm³ of the 1.35 cm³ lantern
   surviving**. A profile that touches x = 0 is the normal case; it is how a
   semicircle becomes a sphere.
2. **`offset(r = -rib_d)` pulls the profile off the AXIS as well as off the
   surface**, so the inner solid came out with a 0.35 mm bore down its middle.
   Every slab passes through the axis, so the crease cut then hollowed that
   bore into a sealed void running the height of the gourd — `Volumes: 3` and a
   −2.92 mm³ inverted body. A square plugging the axis fixes it.
3. **The stem was unioned before the creases were cut.** Near the apex the
   whole cross-section is shell, so the six slabs crossing at the axis cut a
   star clean through the top and left each stem floating as its own body. It
   is unioned after now.
4. **The cutter's outer surface was the gourd's own surface.** Coincident faces
   between a solid and its subtrahend — the same trap the knee braces fell
   into. The crease ends came out as zero-area facets and a −0.0002 mm³
   inverted body. The cutter is 0.4 mm oversized now; only the `rib_d` that
   reaches inside does any cutting.

A fifth was pure floating-point luck: at 0° phase the taper ends of the ribs at
210° and 240° produced two zero-area facets **on the left lantern only**, with
identical geometry clean at x = +15 and clean again in isolation at the origin.
15° of rib phase clears it — and it also stops a crease running straight down
the middle of the face and through the nose.

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

## The warnings the slicer gives, and what each one actually is

PrusaSlicer reports **Floating bridge anchors, Long bridging extrusions**. Every
one of them was located by slicing partial models and then measured out of the
g-code, rather than lived with:

| model | warning |
|---|---|
| outer solid form only | clean |
| solid − cavity (the bare shell) | clean |
| solid − cavity − openings | **Collapsing overhang** |
| same, with the window transom bars disabled | clean |
| full model without the porch canopy | **Collapsing overhang** only |

- **Collapsing overhang** is the **transom bars** — the horizontal glazing bar
  left as material across each window. Each is 1.68 mm tall and 1.68 mm deep,
  and the mullion splits its span into two bridges of **4.66 mm**. That is a
  span a P1S bridges without comment. Making it strictly self-supporting would
  need a ceiling rising at 35° over the half-light, which is 1.63 mm of rise
  inside a 1.68 mm bar — impossible without a chunky 3.3 mm transom on a
  20.8 mm window. Present since the first build, left alone deliberately.
- **The porch ceiling** bridges **16.1 mm** (was 41.1 mm before the extra
  columns and the frieze). Hidden surface, well inside what the machine does.
- **The rest are lines running ALONG narrow ledges, not across voids.** The
  longest single bridging move in the whole print is 74.1 mm at z 81.6 — a line
  following the top clapboard groove around the body. The down-facing area in
  that band measures **315.5 mm²**, which is perimeter × groove depth; if it
  were a real 74 mm void the area would be orders of magnitude larger. The
  cornice used to add a 42.6 mm line of the same kind along its 1.5 mm lip;
  flaring the cornice (1.5 mm out over 3 mm of rise, 26.6° from vertical)
  removed that ledge entirely.

## The size decision

Not a problem to solve — the levers, kept in case a smaller variant is ever
wanted:

1. **Height.** Most of the volume is roof and turret.
2. **Wall.** Nominal 2.52 mm because the clapboard groove is budgeted into it.
   Dropping the inner offset to 1.26 mm gives a 2.10 mm wall and 1.26 mm at the
   groove floor — still 3 extrusions — for about 17% less shell.
3. **Scale.** 80% would land near 4h30, but it also shrinks the wall below whole
   extrusions, so it needs the parameters re-solved rather than a scale factor
   applied. It would also take the lantern faces and the tower bats below the
   size at which they read.

None of it is applied. At lamp pricing the full-size piece is the product.
