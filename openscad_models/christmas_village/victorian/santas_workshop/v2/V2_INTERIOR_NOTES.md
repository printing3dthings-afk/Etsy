# Santa's Workshop v2: the inside opened up for three tealights (2026-10-28)

Scott's matte-white print glowed only in the middle bay. Seen from underneath,
the hall was three rooms. Two inside walls under the roof valleys split it,
each with one 24 mm lancet through it, and a solid column stood in each end
room. One tealight in the middle could not reach the rest. This is folded into
v2 (the detail-print pilot), so there is **one corrected file:
`victorian_santas_workshop_v2.3mf`**. The listed file one folder up is
unchanged until Scott chooses to swap.

## What the two columns were

**The chimney stacks**, carried all the way down. Each of the two brick stacks
(`STACKS`) was modelled from the floor to its cap as a hollow flue, 16 and
18 mm across. One stood in the middle of each end bay (comment from 2026-10-12:
"flues from the floor"). Inside the hall they did nothing structural. The
roof's slab carries a stack: its underside climbs 56°, and a stack's wall
stands on it all round. **Now each stack starts at the roof's underside.**
Above the roof nothing changed. One difference in how it lights: on the v1
print the flues looked solid from underneath (Scott's photo, 2026-10-29),
because the snow base plugged each one at the floor. Now each bore opens into
the hall, so the chimney tops will glow faintly. The geometry outside is the
same. If you'd rather keep them dark, a 1 mm cap inside each chimney is a
one-line change.

One catch, found on the slice and fixed: with the flue gone, the bore was a
round hole through the sloped slab. The slab built its uphill rim out over the
hole a layer at a time, a round arch the slicer propped on both stacks.
Through the slab the bore is now a teardrop pointing up the slope, narrowing
back to round at 50° before it reaches the roof's face, so the rim closes at
38°. On a test slab at the same pitch, the round hole needed 3,484 support
moves and the teardrop needs none. From above, the bore is round as it was.

## What the inside walls were for, and what replaced them

They do hold the building up. Each one sits under a roof valley. There, the
lower tooth's slab ends in a level line 68 mm long from the front wall to the
back, and the next tooth's glazed face stands on that line. With nothing
under it, the line would be the first thing printed at that height, in the
air, and would carry 55 mm of glazed wall. So the walls could not simply go.

**Each is now one opening as wide as the room.** It is open from wall to wall
at the floor and closes at 38° from upright to a point 0.9 mm under the valley.
What's left of each wall is two triangles hanging from the front and back
walls. They carry the valley line from each wall to the middle and print
without support, like the rest of the building's slopes.

## Clear inside, before and after

| | before | after |
|---|---|---|
| the hall | 120.6 × 68.6 mm, three bays | 120.6 × 68.6 mm, one chamber |
| opening between bays | a 24 mm lancet, 49.8 tall, **816 mm²** | 63.3 wide at the floor (68.6 between the walls), 50.6 tall, **1,984 mm²** |
| share of each inside wall that is open | 23% | 56% |
| columns in the end bays | two, 17.6 and 19.6 mm across with their collars, floor to roof | none |
| clear floor at 12 mm up | 6,884 mm² | 7,747 mm² |
| clear floor at 30 mm up | 6,850 mm² | 7,578 mm² |
| tealights | one, middle bay | three |

## Three tealights

The lights stand on the table under the open base, as on every building in
the line, so their flames sit at 30–40 mm, level with the big toy windows
(their sills at 16 mm, their arches up to about 47). **Three rings on the floor**, tied to the base,
place them. Lower the building over the lights and the rings' chamfered tops
centre each one. Each ring is 39.2 mm inside, for a 38 mm light with 0.6 to
spare all round.

**The 46 mm bay could not be met, and here is why.** Three 46 mm bays in a
row need 138 mm; the hall is 120.6 inside and the turrets take its corners.
Measured on the real outline, three equal circles fit at 42.4 mm at most, and
only staggered; in a straight row the most is 38.4, the lights touching. So
the rings are staggered: the middle one forward under the gatehouse, the end
ones back. The 46 mm circle exists so a hand can set a light down inside a
building. Here the lights go on the table first and the building comes down
over them, so the rings do that job. If you want the full 46, it takes a
longer hall: an exterior change, or two lights instead of three.

| ring | centre (x, y) mm | lights |
|---|---|---|
| left | −36.5, +9.5 | the left bay and the back-left windows |
| middle | 0, −13.1 | the middle bay, the gatehouse, the back-middle window |
| right | +36.5, +9.5 | the right bay and the back-right windows |

## Panes

All were 1.48 mm, except the turrets' 1.38. **Every pane is now 0.84 mm**,
two lines, the line's thin-pane spec (the cocoa café v2). Each keeps its front
face where it was, so nothing changes outside. On the big toy windows the
collar behind the pane is simply 0.64 shallower. On the glazed teeth, the
turrets and the rose window, the wall left behind the thinner pane is a pocket
whose head climbs 1.2 per 1 inward, so it prints like the toy windows' sloped
heads. The toys' lines on the big windows
still stand 1.8 mm out of the back of the pane, now 2.64 of plastic on a line
against 0.84 (was 3.3 against 1.48), so they show darker on the glow. The rose
window's spokes are thickened behind its pane the same way.

## Checks on the shipping meshes

The four colour parts were exported with OpenSCAD 2021's CGAL engine, one at
a time (two at once ran the container out of memory). The gate's verdict is
on their CGAL union (`part="union"`, about 3.5 hours), as v1's was. It was run
again after the mark was changed to an engraving, with the same result.

**`product_gate` on the CGAL union:**

| check | result |
|---|---|
| fits the P1S | 206.0 × 129.0 × 193.6 mm, the same as before |
| watertight, one body, normals agree | yes |
| supports | **0 support moves, 0 overhang perimeters** |
| printed height | 193.6 of 193.6 mm |
| flat base | 75.84 cm², 28.5% of the footprint |
| stable | centre of mass over the base |
| walls | **1st percentile 0.84 mm: the panes**, median 2.84 |

The wall check reads as a FAIL, and the panes are the only reason. They are
0.84 mm by request, and there are enough of them now that they are the
thinnest 1% of the building. Every span under 1.2 mm was traced:
- **0.84:** the panes.
- **0.75:** a ray crossing a turret's curved glass at an angle. The glass is
  0.84 through.
- **Under 0.5:** clips at the edges of brick joints and relief, the same
  detail v1 shipped with.
- **1.0–1.1:** the floor rings' height.

No structural wall is under 1.2 mm. The panes are held all round by their
frames, like the cocoa café v2's.

**Other checks:**
- **Fragility** (`tools/fragility.py`, all four parts): nothing high. One
  "watch": a 7.2 mm stretch of the middle floor ring between its spokes,
  slenderness 4.4 ("high" starts at 15). It is a 1.6 mm ring on the table
  that carries nothing.
- **The maker's mark is now engraved, not inlaid.** It was cut into the base
  and filled with the roof's slate colour, which reads only in a four-colour
  print. Printed all in matte white, the fill is white too, so the mark
  disappears; your current print most likely has no visible mark for that
  reason. It is now cut whole, 0.8 mm deep, as on the line's one-colour
  pieces. Seen from underneath with the building tipped toward you, it reads
  OBC (checked on the exported base). In four colours it shows as a recess.
- **Supports, the long way round.** Merging the parts with manifold3d (a
  minute, against CGAL's hours) leaves edges shared by four faces where two
  colours only touch. The slicer props those: 7,725 support moves on v2 and
  7,665 on the listed v1, in the same four places at the same heights. v1's
  CGAL union, like v2's, slices to none. That merge is used only for renders
  and for comparing v1 with v2.
- **Print fidelity in white** (`tools/print_fidelity.py` on the closed CGAL
  union, finished 2026-10-30, 968 layers): 7.0 mm³ of 360,099 mm³ not
  printed, 0.05 mm³ printed that wasn't modelled. **19 flags, none over
  0.42 mm³, all cosmetic:**
  - 3 at the rose window. The frame is sheared upward so its underside
    needs no support. Below the centre, its inner edge feathers out to a
    point, and the last 0.28 mm of it is too thin to extrude: 0.41, 0.37
    and 0.07 mm³. The frame, glass and spokes all print.
  - 16 at the eight turret windows, two per sill. Each sill is a flat strip
    wrapped onto a round turret, so its ends meet the drum as knife edges.
    Two layers, 0.22 mm wide, 0.035-0.051 mm³ each. The rest of each
    sill prints.
  - This run covers everything but the engraved mark: it started before
    the mark changed from inlaid to engraved. Earlier runs on the loose
    part meshes gave nonsense, because those meshes aren't closed. The
    tool now refuses them, so the CGAL union is the right input.

## Renders (white, design review, not photos)

- `images/v2_as_printed_white_{front,three_quarter,top}.png`: rendered from the
  sliced toolpath in white, outer surfaces only, the same setup as the earlier
  as-printed views.
- `images/v2_interior_underside.png`: turned over, looking up into the open
  base. One chamber, no columns, the three rings, the two inside walls'
  triangles, and the engraved OBC by the front step.
- `images/v2_interior_cutaway.png`: cut through the middle bay, seen from the
  left: the right-hand inside wall's opening face on, rings either side, a
  toy window's rocking horse through it.

## Files

- `victorian_santas_workshop_v2.scad`: the source. Changes are dated
  2026-10-28 at each place.
- `victorian_santas_workshop_v2.3mf`: **the one file to print.** Four parts,
  aligned; in matte white, assign the same filament to all four. Supports off.
- `build.sh cgal` exports the parts; `ship.sh` runs the checks, 3MF and
  renders; `render_interior.py` the two interior views.
