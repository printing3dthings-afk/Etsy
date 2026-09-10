# Haunted Manor Lantern — printing notes

Hollow Victorian house shell, lit from inside. Tealight or LED sits under it
through the open base; light escapes only through the windows and door.

| | |
|---|---|
| size | 92.7 × 92.0 × 163 mm |
| volume | 98.4 cm³ |
| **time** | **6h 01m** |
| filament | 113 g |
| supports | none — see the overhang note |
| brim | none — the base footprint is large and open |

**6h 01m is over this shop's 4h/unit ceiling and that is a deliberate open
question, not an oversight.** See "The size decision" below.

## Verified

- watertight, **1 body**, 0 degenerate faces
- **CGAL `Volumes: 2`** — the skill's signature for a genuinely OPEN shell. A
  sealed hollow reports 3. This is the check that proves it is a lantern and
  not a shape with holes in it.
- zero gap fill in the slice
- longest true unsupported span **0.94 mm** (the clapboard groove ceiling).
  The slicer's longest single bridge move is 74.5 mm, which is a line running
  *along* that ledge, not across a void — confirmed by measuring the
  down-facing area in that layer band: 293.9 mm² against 320 mm² predicted for
  perimeter × groove depth. Everything else bridges ≤ 23.7 mm.

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
  the cavity and cuts it free. It is now an exterior stack on the back wall,
  which is where a Victorian house puts one anyway.

## The size decision

At 163 mm tall this is a 6-hour print. The levers, in order of effect:

1. **Height.** Most of the volume is roof and turret.
2. **Wall.** Nominal 2.52 mm because the groove is budgeted into it. Dropping
   the inner offset to 1.26 mm gives a 2.10 mm wall and 1.26 mm at the groove
   floor — still 3 extrusions — for about 17% less shell.
3. **Scale.** 80% would land near 4h, but it also shrinks the wall below whole
   extrusions, so it needs the parameters re-solved rather than a scale factor.

Not applied yet — this is a pricing question as much as a design one.
