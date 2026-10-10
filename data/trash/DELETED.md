# Deletion Recycle Bin

> Everything deleted by an automated edit (code blocks or whole files) is
> archived here first, kept for **30 days**, then auto-pruned. To recover
> something, run `python tools/trash.py --restore <id>` (or just copy it back
> out of the fenced block below). Byte-exact copies also live in
> `data/trash/files/`.

<!-- TRASH id=20260919-001 date=2026-09-19 kind=snippet source="tools/viewer/app.js" reason="Replaced by plateSurface(): the bed is now a real Bambu flex plate with a per-plate procedural finish and 1:1 markings, not one tiling grey noise map." -->
## 20260919-001 · 2026-09-19 · snippet · `tools/viewer/app.js`
**Reason:** Replaced by plateSurface(): the bed is now a real Bambu flex plate with a per-plate procedural finish and 1:1 markings, not one tiling grey noise map.  
**Payload:** `data/trash/files/20260919-001__snippet.txt`

```javascript
function peiTexture() {
  var c = document.createElement('canvas');
  c.width = c.height = 256;
  var g = c.getContext('2d');
  g.fillStyle = '#343943'; g.fillRect(0, 0, 256, 256);
  var img = g.getImageData(0, 0, 256, 256), d = img.data;
  for (var i = 0; i < d.length; i += 4) {
    var n = (Math.random() - 0.5) * 54;
    d[i] += n; d[i + 1] += n; d[i + 2] += n * 0.9;
  }
  g.putImageData(img, 0, 0);
  var tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(9, 9);
  return tex;
}
```

<!-- /TRASH 20260919-001 -->
<!-- TRASH id=20260919-002 date=2026-09-19 kind=snippet source="tools/viewer/app.js" reason="Rebuilt from Bambu product photography: the AMS has a smoked half-cylinder DOME over the spool row, not a flat lid, and real reel/feeder hardware. The flat-lidded version read as an empty tray from above." -->
## 20260919-002 · 2026-09-19 · snippet · `tools/viewer/app.js`
**Reason:** Rebuilt from Bambu product photography: the AMS has a smoked half-cylinder DOME over the spool row, not a flat lid, and real reel/feeder hardware. The flat-lidded version read as an empty tray from above.  
**Payload:** `data/trash/files/20260919-002__snippet.txt`

```javascript
// The AMS, at its real size, sitting where one actually sits. The spools drawn
// inside are illustrative -- nothing here reads the machine, so they are four
// plausible colours and the panel says as much rather than implying a feed.
function buildAMS(spec, ox, oy, y1, zTop) {
  amsGroup = null;
  if (!spec) { return; }
  amsGroup = new THREE.Group();
  var cy = y1 - spec.d / 2 - 6, cz = zTop + 4 + spec.h / 2;

  // Built as panels, not a solid block: a closed box would hide the spools
  // behind its own lit top face no matter how transparent the lid above it is.
  var wall = 8, shell = surface(0x2a2e35);
  function panel(w, d, h, x, y, z) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), shell);
    m.position.set(x, y, z);
    amsGroup.add(m);
  }
  panel(spec.w, spec.d, wall, ox, cy, cz - spec.h / 2 + wall / 2);
  panel(wall, spec.d, spec.h, ox - spec.w / 2 + wall / 2, cy, cz);
  panel(wall, spec.d, spec.h, ox + spec.w / 2 - wall / 2, cy, cz);
  panel(spec.w, wall, spec.h, ox, cy + spec.d / 2 - wall / 2, cz);
  panel(spec.w, wall, spec.h, ox, cy - spec.d / 2 + wall / 2, cz);
  var amsEdge = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(spec.w, spec.d, spec.h)),
    new THREE.LineBasicMaterial({color: 0x4a515e}));
  amsEdge.position.set(ox, cy, cz);
  amsGroup.add(amsEdge);

  var spools = [], cores = [];
  for (var i = 0; i < spec.slots; i++) {
    var x = ox - (spec.slots - 1) * 46 + i * 92;
    // Spool size is the AMS's own published compatibility range -- 197-202 mm
    // across, 50-68 mm wide -- which is why they very nearly fill the box.
    var fil = new THREE.Mesh(new THREE.CylinderGeometry(99, 99, 56, 28),
      surface(FILAMENT[i % FILAMENT.length], {roughness: 0.45, metalness: 0.0}));
    // Rotated onto X by the PARENT, so the mesh's own X rotation is free to be
    // the spool turning as filament is pulled off it.
    var hub = new THREE.Group();
    hub.rotation.z = Math.PI / 2;
    hub.position.set(x, cy, cz - 2);
    hub.add(fil);
    amsGroup.add(hub);
    spools.push(fil);
    var core = new THREE.Mesh(new THREE.CylinderGeometry(34, 34, 60, 20),
      surface(0x15171c));
    core.rotation.z = Math.PI / 2;
    core.position.set(x, cy, cz - 2);
    amsGroup.add(core);
    cores.push(core);
  }

  // Smoked lid over the spools -- the reason you can see them at all.
  var lid = new THREE.Mesh(new THREE.BoxGeometry(spec.w - 22, spec.d - 22, 5),
    glassMaterial());
  lid.position.set(ox, cy, cz + spec.h / 2 - 3);
  amsGroup.add(lid);
  var lz = cz + spec.h / 2 - 3, fm = surface(0x21252b);
  [[spec.w, 11, ox, cy - spec.d / 2 + 5.5], [spec.w, 11, ox, cy + spec.d / 2 - 5.5],
   [11, spec.d, ox - spec.w / 2 + 5.5, cy], [11, spec.d, ox + spec.w / 2 - 5.5, cy]]
    .forEach(function (f) {
      var m = new THREE.Mesh(new THREE.BoxGeometry(f[0], f[1], 7), fm);
      m.position.set(f[2], f[3], lz);
      amsGroup.add(m);
    });

  // PTFE bundle looping out of the back and into the top of the machine.
  var curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(ox, cy + spec.d / 2 - 4, cz - 40),
    new THREE.Vector3(ox, y1 + 54, cz - 74),
    new THREE.Vector3(ox, y1 - 26, zTop + 3)]);
  var feed = new THREE.Mesh(new THREE.TubeGeometry(curve, 22, 7, 10, false),
    surface(0x171a20));
  amsGroup.add(feed);

  amsGroup.userData.spools = spools;
  amsGroup.userData.cores = cores;
  amsGroup.userData.feed = feed;
  amsGroup.name = 'ams';
  scene.add(amsGroup);
}
```

<!-- /TRASH 20260919-002 -->
<!-- TRASH id=20260919-003 date=2026-09-19 kind=snippet source="tools/viewer/app.js" reason="duplicate object-literal key: the greyscale remap collapsed 0x23262d and 0x22262e onto the same hex, so this row was shadowed by the next one and never applied" -->
## 20260919-003 · 2026-09-19 · snippet · `tools/viewer/app.js`
**Reason:** duplicate object-literal key: the greyscale remap collapsed 0x23262d and 0x22262e onto the same hex, so this row was shadowed by the next one and never applied  
**Payload:** `data/trash/files/20260919-003__snippet.txt`

```javascript
  0x262627: [0.60, 0.10],
```

<!-- /TRASH 20260919-003 -->
<!-- TRASH id=20260923-001 date=2026-09-23 kind=snippet source="tools/viewer/app.js" reason="Dead SURFACE entry: the vertical blue-grey door grip it styled was replaced by the measured horizontal silver pill handle (2026-09-23)." -->
## 20260923-001 · 2026-09-23 · snippet · `tools/viewer/app.js`
**Reason:** Dead SURFACE entry: the vertical blue-grey door grip it styled was replaced by the measured horizontal silver pill handle (2026-09-23).  
**Payload:** `data/trash/files/20260923-001__snippet.txt`

```javascript
  0x7b8493: [0.30, 0.88],  // door grip, brushed aluminium
```

<!-- /TRASH 20260923-001 -->
<!-- TRASH id=20260925-001 date=2026-09-25 kind=file source="openscad_models/haunted_post_office.scad" reason="Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128)." -->
## 20260925-001 · 2026-09-25 · file · `openscad_models/haunted_post_office.scad`
**Reason:** Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128).  
**Payload:** `data/trash/files/20260925-001__haunted_post_office.scad`

```
// Haunted Post Office lantern -- building #1 of the Haunted Town series
// (openscad_models/HAUNTED_TOWN.md), built on the bakery's proven parts
// (haunted_bakery.scad): same walls, roof, window frames, relief and every
// gate-tuned margin, so read that file for WHY each of those looks the way it
// does. A hollow shell lit from inside by a battery LED tealight: open base,
// true through-cut windows.
//
// THE POST OFFICE'S OWN FEATURES: an octagonal corner TURRET under a tall,
// leaning witch-hat spire; a crooked POST OFFICE sign; parcels tied with
// string stacked by the wall; a brass mail slot in the door.
//
// WHY OCTAGONAL. Every face of an octagon is flat, so the bakery's planar
// frames, muntins and clapboard carry onto the turret unchanged. On a round
// tower each of those would have had to be rebuilt on a curve.
//
// WHY THE SIGN IS ON THE WALL. A sign hanging from a bracket has a free bottom
// edge, which is an overhang no angle rescues. It is hung crooked instead.
//
// COLOUR PARTS. Render one at a time with -D part="...":
//   body    walls, plinth, turret walls, gables and battens, eave flare, step
//   roof    roof slab, shingles, ridge cap, chimney, turret spire and its eave
//   trim    window and door frames, muntins, door, corner boards, sign board,
//           the parcels' string
//   accent  the parcels, the sign's letters, the mail slot
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// TEALIGHT. The main room is 72.6 x 50.6 mm clear from the plate to the
// ceiling, and the base is open: a 38 mm LED tealight drops in with room to
// spare. The turret's hollow opens into it, so the turret glows too.

include <BOSL2/std.scad>
include <lattice_lib.scad>

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- body ----------------------------------------------------------------
W        = 76;              // along X, the front's width
D        = 54;              // along Y, front (-Y) to back
wall     = 1.68;            // 4 x 0.42
sid_d    = 0.84;            // clapboard stands 2 extrusions proud of plan(0)
corner_r = 1;
H        = 78;              // top of the side walls, where the eave flare begins
plinth_h = 8;               // shared by every building in the town
plinth_o = sid_d + 0.84;    // plinth face, 0.84 proud of the siding
sid_p    = 4.5;             // clapboard course
sid_r    = sid_d * tan(58); // height of each board's outward ramp: 58 deg from
                            // horizontal. 50 was enough for the ramp alone, but
                            // where a ramp crosses a window's crown the two meet
                            // at a corner, and corners need 58 (see the roof note below).

SH       = 1.2;             // shear of every raised relief: 1.2 up per 1 out,
                            // so its underside sits 40 deg from vertical

// ---- roof ----------------------------------------------------------------
e        = 5;               // eave projection
er       = e / tan(40);     // ...carried on a flare 40 deg from vertical
f        = 4;               // fascia height
b        = D/2 + sid_d;
be       = b + e;           // eave edge, half-depth
zf       = H + er + f;      // top of the fascia, where the slope starts
tr       = 2.52;            // slab thickness, normal to the slope (6 extr.)
// NO RAKE OVERHANG, and that is a measured decision. Past a gable the roof's
// underside rises inward at ~50 deg while the rake has to grow outward, and at
// the corner where those meet the outline moves diagonally -- root 2 faster
// than either face. Measured on the gate's own slicer: two 50 deg faces
// meeting at a corner drew 54,002 support moves, 55 deg drew 46,966, and only
// 58 deg or steeper came out clean. No rake angle rescues a 50 deg roof, so
// the roof stops 0.3 mm short of each gable face (distinct surfaces, never
// coplanar) and the gable's top edge shows as a small reveal.
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260925-001 -->
<!-- TRASH id=20260925-002 date=2026-09-25 kind=file source="openscad_models/haunted_post_office.3mf" reason="Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128)." -->
## 20260925-002 · 2026-09-25 · file · `openscad_models/haunted_post_office.3mf`
**Reason:** Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128).  
**Payload:** `data/trash/files/20260925-002__haunted_post_office.3mf`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260925-002 -->
<!-- TRASH id=20260925-003 date=2026-09-25 kind=file source="openscad_models/HAUNTED_POST_OFFICE_PRINTING.md" reason="Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128)." -->
## 20260925-003 · 2026-09-25 · file · `openscad_models/HAUNTED_POST_OFFICE_PRINTING.md`
**Reason:** Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128).  
**Payload:** `data/trash/files/20260925-003__HAUNTED_POST_OFFICE_PRINTING.md`

```
# Haunted Post Office — printing notes

Building #1 of the Haunted Town series (`HAUNTED_TOWN.md`). It is a hollow
lantern with an open base, lit from inside by a battery LED tealight. It has
an octagonal corner turret under a tall witch-hat spire, which leans out
3.5 mm. 110.7 × 81.5 × 160.1 mm including the chimney, the turret and the
parcels.

**Print this:** `haunted_post_office.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | walls, plinth, turret walls, gables and battens, eave flare, step | slate teal `#50666B` |
| roof | roof slab, shingles, ridge cap, chimney, and the turret's spire with its eave and finial | slate `#2B2F38` |
| trim | window and door frames, muntins, door, corner boards, sign board, the parcels' string | cream `#EFE6D2` |
| accent | the parcels, the POST OFFICE letters, the brass mail slot | kraft `#D4A96A` |

The per-part `.stl` files are what the assembler consumes and what the gates
check. They are not the deliverable.

## No supports, and none of the settings below are optional

- **Supports OFF.** Verified: the gate's slicer reports **0 support moves
  and 0 overhang perimeters**.
- **Print it standing up, the way it is in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament | colour changes |
|---|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **13 h 56 m** | **~128 g** | 0 |
| **four colour, AMS** | not reliable here | ~136 g model **+ purge** | **1,285** |

The purge is the real cost of the colour version, the same as the bakery's:
- **255 g** of purge and wipe tower at PrusaSlicer's 140 mm³ per change;
- about **560 g** at the 350 mm³ Bambu default, in flush alone.

Bambu Studio sets its own flush for each colour pair, so slice it there for
the real number before pricing. The four-extruder time estimate overflowed
here, so no four-colour time is quoted. It is longer than the bakery
(11 h 52 m) mainly because of the spire.

A listing must say which version the buyer gets: printed in colour, or
single colour and hand-painted by Jessee.

## The tealight

Measured on the exported mesh: the largest clear circle about the room's
centre is **50.6 mm across at every height from the table to past 90 mm**.
The series rule is ≥ 46 mm across and ≥ 60 mm of headroom. Any common LED
tealight fits (36–38 mm across, 32–45 mm tall). The base is open, and the
house lifts off to reach the switch.

The turret glows too. A tall pointed arch (7 × 47 mm), cut through the
turret's wall where it faces into the room, lets the light in. It can't be
seen from outside.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 160.0 mm of 160.09 modelled (the finial tip);
  - 13.43 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - watertight, consistent winding;
  - **0 zero-area faces**;
  - every edge shared by exactly two faces.
- The roof is two pieces (the main roof and the spire), the trim is 24 and
  the accent is 12. Each piece was checked for real surface contact with
  the part it sits on, sampled by area. The spire shares 226 mm² with the
  turret wall, and the parcels' string shares 314 mm² with the parcels.
- **The parts are disjoint.** All six pairwise intersections render EMPTY.
- The union mesh (used only for the gate) carries 113 zero-area faces,
  every one at z = 84.2 along the eave weld, the same as the bakery. None
  of the four parts that ship has any.
- The 3MF round-trips through the slicer with all four extruders addressed.
- **OBC maker's mark:** engraved 0.8 mm deep under the step, the same mark
  as the bakery, with strokes ≥ 1.0 mm.
- **POST OFFICE letters:** size 4.8, a flush inlay. Eroding them by one
 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260925-003 -->
<!-- TRASH id=20260925-004 date=2026-09-25 kind=file source="openscad_models/haunted_post_office_body.stl" reason="Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128)." -->
## 20260925-004 · 2026-09-25 · file · `openscad_models/haunted_post_office_body.stl`
**Reason:** Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128).  
**Payload:** `data/trash/files/20260925-004__haunted_post_office_body.stl`

```
solid OpenSCAD_Model
  facet normal 0 1 -0
    outer loop
      vertex 39.68 -5.16 79.816
      vertex 38.84 -5.16 116.689
      vertex 39.68 -5.16 116.689
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 38.84 -5.16 116.689
      vertex 39.68 -5.16 79.816
      vertex 38.84 -5.16 78.808
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 39.68 -6.84 114.705
      vertex 39.68 -5.16 79.816
      vertex 39.68 -5.16 116.689
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 39.68 -5.16 79.816
      vertex 39.68 -6.84 114.705
      vertex 39.68 -6.84 79.816
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 38.84 -6.84 114.705
      vertex 39.68 -6.84 79.816
      vertex 39.68 -6.84 114.705
    endloop
  endfacet
  facet normal -0 -1 0
    outer loop
      vertex 39.68 -6.84 79.816
      vertex 38.84 -6.84 114.705
      vertex 38.84 -6.84 78.808
    endloop
  endfacet
  facet normal 0.768221 0 -0.640184
    outer loop
      vertex 39.68 -6.84 79.816
      vertex 38.84 -5.16 78.808
      vertex 39.68 -5.16 79.816
    endloop
  endfacet
  facet normal 0.768221 0 -0.640184
    outer loop
      vertex 38.84 -5.16 78.808
      vertex 39.68 -6.84 79.816
      vertex 38.84 -6.84 78.808
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 39.68 0.839999 110.741
      vertex 38.84 0.839999 121.793
      vertex 39.68 0.839999 121.793
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 38.84 0.839999 121.793
      vertex 39.68 0.839999 110.741
      vertex 38.84 0.839999 109.733
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 39.68 -0.839999 121.793
      vertex 39.68 0.839999 121.793
      vertex 39.68 0 122.785
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 39.68 0.839999 121.793
      vertex 39.68 -0.839999 121.793
      vertex 39.68 0.839999 110.741
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 39.68 0.839999 110.741
      vertex 39.68 -0.839999 121.793
      vertex 39.68 -0.839999 110.741
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 38.84 -0.839999 121.793
      vertex 39.68 -0.839999 110.741
      vertex 39.68 -0.839999 121.793
    endloop
  endfacet
  facet normal -0 -1 0
    outer loop
      vertex 39.68 -0.839999 110.741
      vertex 38.84 -0.839999 121.793
      vertex 38.84 -0.839999 109.733
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 39.68 6.84 110.741
      vertex 38.84 6.84 114.705
      vertex 39.68 6.84 114.705
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 38.84 6.84 114.705
      vertex 39.68 6.84 110.741
      vertex 38.84 6.84 109.733
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 39.68 5.16 110.741
      vertex 39.68 6.84 114.705
      vertex 39.68 5.16 116.689
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 39.68 6.84 114.705
      vertex 39.68 5.16 110.741
      vertex 39.68 6.84 110.741
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 38.84 5.16 116.689
      vertex 39.68 5.16 110.741
      vertex 39.68 5.16 116.689
    endloop
  endfacet
  facet normal -0 -1 0
    outer loop
      vertex 39.68 5.16 110.741
      vertex 38.84 5.16 116.689
      vertex 38.84 5.16 109.733
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 39.68 12.84 83.9802
      vertex 38.84 12.84 107.616
      vertex 39.68 12.84 107.616
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 38.84 12.84 107.616
      vertex 39.68 12.84 83.9802
      vertex 38.84 12.84 82.9722
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 39.68 11.16 83.9802
      vertex 39.68 12.84 107.616
      vertex 39.68 11.16 109.601
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 39.68 12.84 107.616
      vertex 39.68 11.16 83.9802
      ve
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260925-004 -->
<!-- TRASH id=20260925-005 date=2026-09-25 kind=file source="openscad_models/haunted_post_office_roof.stl" reason="Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128)." -->
## 20260925-005 · 2026-09-25 · file · `openscad_models/haunted_post_office_roof.stl`
**Reason:** Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128).  
**Payload:** `data/trash/files/20260925-005__haunted_post_office_roof.stl`

```
solid OpenSCAD_Model
  facet normal 0 1 -0
    outer loop
      vertex 38.54 32.84 83.9888
      vertex 38.18 32.84 88.9588
      vertex 38.54 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 38.18 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 36.52 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 36.52 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 34.86 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 34.86 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 33.2 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 33.2 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 31.54 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 31.54 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 29.88 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 29.88 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 28.22 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 28.22 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 26.56 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 26.56 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 24.9 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 24.9 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 23.24 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 23.24 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 21.58 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 21.58 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 19.92 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 19.92 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 18.26 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 18.26 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 16.6 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 16.6 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 14.94 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 14.94 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 13.28 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 13.28 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 11.62 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 11.62 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 9.96 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 9.96 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 8.3 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 8.3 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 6.64 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 6.64 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 4.98 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 4.98 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 3.32 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 3.32 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex 1.66 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 1.66 32.84 88.9588
      vertex 38.54 32.84 83.9888
      vertex -1.66 32.84 88.9588
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -38.54 32.84 83.9888
      vertex -1.66 32.84 88.9588
      vertex 38.54 32.84 83.9888
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      verte
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260925-005 -->
<!-- TRASH id=20260925-006 date=2026-09-25 kind=file source="openscad_models/haunted_post_office_trim.stl" reason="Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128)." -->
## 20260925-006 · 2026-09-25 · file · `openscad_models/haunted_post_office_trim.stl`
**Reason:** Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128).  
**Payload:** `data/trash/files/20260925-006__haunted_post_office_trim.stl`

```
solid OpenSCAD_Model
  facet normal 0.138989 0 0.990294
    outer loop
      vertex -23.3248 -27.0586 75.6606
      vertex -23.3647 -28.6142 75.6662
      vertex -23.3248 -28.6675 75.6606
    endloop
  endfacet
  facet normal 0.155421 -0.000430288 0.987848
    outer loop
      vertex -23.3248 -27.0586 75.6606
      vertex -23.3685 -28.6093 75.6668
      vertex -23.3647 -28.6142 75.6662
    endloop
  endfacet
  facet normal 0.141072 -1.54381e-05 0.989999
    outer loop
      vertex -23.713 -28.1774 75.7159
      vertex -23.3248 -27.0586 75.6606
      vertex -23.5248 -27.0238 75.6891
    endloop
  endfacet
  facet normal 0.140979 -0 0.990013
    outer loop
      vertex -23.713 -28.1774 75.7159
      vertex -23.5248 -27.0238 75.6891
      vertex -23.713 -27.0238 75.7159
    endloop
  endfacet
  facet normal 0.141078 -1.74877e-05 0.989998
    outer loop
      vertex -23.3248 -27.0586 75.6606
      vertex -23.713 -28.1774 75.7159
      vertex -23.3685 -28.6093 75.6668
    endloop
  endfacet
  facet normal -0.949665 0 0.313266
    outer loop
      vertex -29.0867 -28.68 67.9829
      vertex -29.1121 -27.5433 67.9059
      vertex -29.1121 -28.68 67.9059
    endloop
  endfacet
  facet normal -0.949665 0 0.313266
    outer loop
      vertex -29.1121 -27.5433 67.9059
      vertex -29.0867 -28.68 67.9829
      vertex -29.0867 -27.5386 67.9829
    endloop
  endfacet
  facet normal 0.937232 -0 0.348706
    outer loop
      vertex -19.3136 -28.68 69.1171
      vertex -19.2883 -27.4739 69.0491
      vertex -19.3136 -27.4706 69.1171
    endloop
  endfacet
  facet normal 0.937232 0 0.348706
    outer loop
      vertex -19.2883 -27.4739 69.0491
      vertex -19.3136 -28.68 69.1171
      vertex -19.2883 -28.68 69.0491
    endloop
  endfacet
  facet normal -0.924585 0 0.380977
    outer loop
      vertex -28.2861 -28.68 70.1326
      vertex -28.3114 -27.424 70.0712
      vertex -28.3114 -28.68 70.0712
    endloop
  endfacet
  facet normal -0.924585 0 0.380977
    outer loop
      vertex -28.3114 -27.424 70.0712
      vertex -28.2861 -28.68 70.1326
      vertex -28.2861 -27.4215 70.1326
    endloop
  endfacet
  facet normal -0.981584 6.72681e-05 0.191031
    outer loop
      vertex -29.9132 -28.68 65.0142
      vertex -30.0882 -27.8567 64.1147
      vertex -30.1187 -27.912 63.958
    endloop
  endfacet
  facet normal -0.981602 -6.60316e-05 0.190938
    outer loop
      vertex -29.9132 -28.68 65.0142
      vertex -30.1187 -27.912 63.958
      vertex -30.2431 -28.68 63.3182
    endloop
  endfacet
  facet normal -0.981596 0 0.190972
    outer loop
      vertex -30.0882 -27.8567 64.1147
      vertex -29.9132 -28.68 65.0142
      vertex -29.9132 -27.8567 65.0142
    endloop
  endfacet
  facet normal 0.892774 -0 0.450506
    outer loop
      vertex -20.8895 -28.68 72.6518
      vertex -20.7145 -27.3303 72.305
      vertex -20.8895 -27.3303 72.6518
    endloop
  endfacet
  facet normal 0.892279 0.000315423 0.451484
    outer loop
      vertex -20.7145 -27.3303 72.305
      vertex -20.8895 -28.68 72.6518
      vertex -20.6892 -27.3318 72.255
    endloop
  endfacet
  facet normal 0.892763 -3.82556e-05 0.450526
    outer loop
      vertex -20.5145 -28.68 71.9087
      vertex -20.6892 -27.3318 72.255
      vertex -20.8895 -28.68 72.6518
    endloop
  endfacet
  facet normal 0.892823 0 0.450408
    outer loop
      vertex -20.6892 -27.3318 72.255
      vertex -20.5145 -28.68 71.9087
      vertex -20.5145 -27.3538 71.9087
    endloop
  endfacet
  facet normal 0.854839 -0 0.518893
    outer loop
      vertex -22.0903 -28.68 74.7555
      vertex -21.9153 -27.2746 74.4672
      vertex -22.0903 -27.2746 74.7555
    endloop
  endfacet
  facet normal 0.854399 0.000203446 0.519618
    outer loop
      vertex -21.9153 -27.2746 74.4672
      vertex -22.0903 -28.68 74.7555
      vertex -21.89 -27.2756 74.4256
    endloop
  endfacet
  facet normal 0.854845 -3.23558e-05 0.518884
    outer loop
      vertex -21.7153 -28.68 74.1377
      vertex -21.89 -27.2756 74.4256
     
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260925-006 -->
<!-- TRASH id=20260925-007 date=2026-09-25 kind=file source="openscad_models/haunted_post_office_accent.stl" reason="Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128)." -->
## 20260925-007 · 2026-09-25 · file · `openscad_models/haunted_post_office_accent.stl`
**Reason:** Superseded 2026-09-25: Scott asked for a one-story post office with a flatter roof and no turret. This is the gated two-story corner-turret version (commit 9e83128).  
**Payload:** `data/trash/files/20260925-007__haunted_post_office_accent.stl`

```
solid OpenSCAD_Model
  facet normal -1 0 0
    outer loop
      vertex 14 -35.6 0
      vertex 14 -31.6 8
      vertex 14 -31.6 0
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex 14 -31.6 8
      vertex 14 -35.6 0
      vertex 14 -35.6 8
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 14 -30.6 0
      vertex 14 -26.6 8
      vertex 14 -26.6 0
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex 14 -26.6 8
      vertex 14 -30.6 0
      vertex 14 -30.6 8
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 24 -35.6 8
      vertex 24 -31.6 0
      vertex 24 -31.6 8
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 24 -31.6 0
      vertex 24 -35.6 8
      vertex 24 -35.6 0
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 24 -30.6 8
      vertex 24 -26.6 0
      vertex 24 -26.6 8
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 24 -26.6 0
      vertex 24 -30.6 8
      vertex 24 -30.6 0
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 14 -35.6 0
      vertex 18.5 -35.6 8
      vertex 14 -35.6 8
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex 18.5 -35.6 8
      vertex 14 -35.6 0
      vertex 18.5 -35.6 0
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 19.5 -35.6 0
      vertex 24 -35.6 8
      vertex 19.5 -35.6 8
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex 24 -35.6 8
      vertex 19.5 -35.6 0
      vertex 24 -35.6 0
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 24 -26.6 0
      vertex 14 -26.6 8
      vertex 24 -26.6 8
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 14 -26.6 8
      vertex 24 -26.6 0
      vertex 14 -26.6 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 14 -35.6 0
      vertex 18.5 -31.6 0
      vertex 18.5 -35.6 0
    endloop
  endfacet
  facet normal -0 0 -1
    outer loop
      vertex 18.5 -31.6 0
      vertex 14 -35.6 0
      vertex 14 -31.6 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 19.5 -35.6 0
      vertex 24 -31.6 0
      vertex 24 -35.6 0
    endloop
  endfacet
  facet normal -0 0 -1
    outer loop
      vertex 24 -31.6 0
      vertex 19.5 -35.6 0
      vertex 19.5 -31.6 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 18.5 -30.6 0
      vertex 14 -30.6 0
      vertex 18.5 -27.6 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 19.5 -27.6 0
      vertex 24 -30.6 0
      vertex 19.5 -30.6 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 24 -30.6 0
      vertex 19.5 -27.6 0
      vertex 24 -26.6 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 18.5 -27.6 0
      vertex 24 -26.6 0
      vertex 19.5 -27.6 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 18.5 -27.6 0
      vertex 14 -26.6 0
      vertex 24 -26.6 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 14 -26.6 0
      vertex 18.5 -27.6 0
      vertex 14 -30.6 0
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 15.4564 -35.0614 8
      vertex 18.5 -35.6 8
      vertex 18.5 -34.6877 8
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 14 -31.6 8
      vertex 15.4564 -35.0614 8
      vertex 15.0314 -31.6 8
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 15.4564 -35.0614 8
      vertex 14 -35.6 8
      vertex 18.5 -35.6 8
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 14 -35.6 8
      vertex 15.4564 -35.0614 8
      vertex 14 -31.6 8
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 24 -31.6 8
      vertex 23.3967 -34.0864 8
      vertex 24 -35.6 8
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 23.39
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260925-007 -->
<!-- TRASH id=20260926-001 date=2026-09-26 kind=snippet source="openscad_models/haunted_bakery.scad" reason="Sign letters were a flush colour-only inlay; replaced by a carved, lined sign so they show in a one-colour print too" -->
## 20260926-001 · 2026-09-26 · snippet · `openscad_models/haunted_bakery.scad`
**Reason:** Sign letters were a flush colour-only inlay; replaced by a carved, lined sign so they show in a one-colour print too  
**Payload:** `data/trash/files/20260926-001__snippet.txt`

```
// The letters are a FLUSH inlay in the board's face, in the accent colour --
// no relief. Raised 1 mm, every horizontal stroke was a sub-bead slab with
// an underside; inlaid, the colour does the work and the face stays flat.
module sign_letters() {
    face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0, fr_t - 0.8])
        linear_extrude(0.8) text("BAKERY", size = 5.2, font = "Montserrat:style=Black",
                                 halign = "center", valign = "center", spacing = 1.06);
}
```

<!-- /TRASH 20260926-001 -->
<!-- TRASH id=20260926-002 date=2026-09-26 kind=snippet source="openscad_models/haunted_post_office.scad" reason="Sign letters were a flush colour-only inlay; replaced by a carved, lined sign so they show in a one-colour print too" -->
## 20260926-002 · 2026-09-26 · snippet · `openscad_models/haunted_post_office.scad`
**Reason:** Sign letters were a flush colour-only inlay; replaced by a carved, lined sign so they show in a one-colour print too  
**Payload:** `data/trash/files/20260926-002__snippet.txt`

```
module sign_letters() {
    face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0.3, fr_t - 0.8])
        linear_extrude(0.8) text("POST OFFICE", size = 4.4, font = "Montserrat:style=Black",
                                 halign = "center", valign = "center", spacing = 1.04);
}
```

<!-- /TRASH 20260926-002 -->
<!-- TRASH id=20260926-003 date=2026-09-26 kind=snippet source="openscad_models/haunted_general_store.scad" reason="Sign letters were a flush colour-only inlay; replaced by a carved, lined sign so they show in a one-colour print too" -->
## 20260926-003 · 2026-09-26 · snippet · `openscad_models/haunted_general_store.scad`
**Reason:** Sign letters were a flush colour-only inlay; replaced by a carved, lined sign so they show in a one-colour print too  
**Payload:** `data/trash/files/20260926-003__snippet.txt`

```
module sign_letters() {
    on_face(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0.3, fr_t - 0.8])
        linear_extrude(0.8) text("MERCANTILE", size = 5.2, font = "Montserrat:style=Black",
                                 halign = "center", valign = "center", spacing = 1.04);
}
```

<!-- /TRASH 20260926-003 -->
<!-- TRASH id=20260926-004 date=2026-09-26 kind=snippet source="openscad_models/haunted_cemetery.scad" reason="Epitaphs were a flush colour-only inlay; replaced by carved, slate-lined lettering" -->
## 20260926-004 · 2026-09-26 · snippet · `openscad_models/haunted_cemetery.scad`
**Reason:** Epitaphs were a flush colour-only inlay; replaced by carved, slate-lined lettering  
**Payload:** `data/trash/files/20260926-004__snippet.txt`

```
module stone_inlays() {
    for (s = STONES) intersection() {
        place_stone(s) stone_body(s);
        place_stone(s) translate([0, -st_t/2 + lt, 0]) rotate([90, 0, 0]) linear_extrude(lt + 0.01) stone_inlay_2d(s);
    }
}
```

<!-- /TRASH 20260926-004 -->
<!-- TRASH id=20260930-001 date=2026-09-30 kind=file source="openscad_models/christmas_village/victorian/shop_house/victorian_shop_house.scad" reason="Replaced by the rounded shop-house (Scott, 2026-09-30: not squared). This is the finished, gated square version (commit 16df111)." -->
## 20260930-001 · 2026-09-30 · file · `openscad_models/christmas_village/victorian/shop_house/victorian_shop_house.scad`
**Reason:** Replaced by the rounded shop-house (Scott, 2026-09-30: not squared). This is the finished, gated square version (commit 16df111).  
**Payload:** `data/trash/files/20260930-001__victorian_shop_house.scad`

```
// Victorian Shop-House -- the Dickens Victorian village's first building with
// "more shape" (Scott, 2026-09-30, picked from four shapes against his
// reference photos in ../../references/). A two-storey shop: a brick shop floor
// with a bay window and a panelled door; above it a white plaster storey with
// dark timbers that JUTS OUT over the street on brackets; a steep front gable
// with a scalloped bargeboard and a finial; a tall stepped chimney stack. On a
// snow base.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on.
//
// The machinery is the first Victorian cottage's (../cottage/victorian_cottage
// .scad), itself the chapel's; every trap it met is written up in
// .claude/skills/3d-print-design/SKILL.md Technique 79 and applied here from
// the start: parts overlap and are cut by priority, never abut; reliefs rise
// from the wall plane; nothing reaches below a ceiling.
//
// COLOUR PARTS, ONE PRINT (victorian_shop_house.3mf), priority roof > accent >
// trim > body:
//   body    brick shop floor, the bay's stall riser, the chimney, the step
//   roof    slate roof, and the "timber": the jetty's beam, cove and
//           brackets, the upper storey's framing, window frames and lattice,
//           the door
//   trim    snow base and drifts, the upper storey's plaster walls, soffits,
//           kneelers, bargeboards and finials, snow on the roof, every pane,
//           the shop floor's window and door frames
//   accent  evergreen: the bay window's frame and bars, the wreath, the
//           window boxes
//
// FRAMES. The shop floor is the brick box, centred on the origin. The upper
// storey and roof are the cottage's roof machinery in their own frame, moved
// forward by the jetty: upper() puts a child there.

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts

$fa = 4;  $fs = 0.4;
part = "all";

// ---- the shop floor --------------------------------------------------------------
W        = 56;              // across the front, both storeys
Wh       = W/2;
Dg       = 50;              // shop floor depth
Dgh      = Dg/2;
wall     = 1.68;
corner_r = 1;
plinth_h = 8;
H1       = 38;              // top of the shop floor; the jetty starts here
SH       = 1.2;

// ---- brick -----------------------------------------------------------------------
bd    = 0.6;
bp    = 2.6;
br    = bd * tan(58);
bj    = 0.6;
bl    = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

// ---- the upper storey and roof -------------------------------------------------------
J     = 4;                  // the jetty: the upper storey stands this far out in front
Du    = Dgh + J/2;          // its half-depth ...
yc    = -J/2;               // ... about this centre
H     = 70;                 // its eave (the side windows' heads clear the eave's flare)
r_ang = 58;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + e;             // plaster: no brick face
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Du - wall;
y_rr  = y_r + 0.4;
cp_lo = -0.2;  cp_hi = 2.6;
module upper() translate([0, yc, 0]) children();

// ---- placement -------------------------------------------------------------------------
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
module ftf(cy, hy, face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, cy + hy, z] : face == 1 ? [u, cy - hy, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module nf(face, u, z) ftf(0, Dgh, face, u, z) children();      // shop floor
module uf(face, u, z) ftf(yc, Du, face, u, z) children();      // upper storey
function loc(f, u) = (f == 0 || f == 3) ? -u : u;

module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260930-001 -->
<!-- TRASH id=20260930-002 date=2026-09-30 kind=file source="openscad_models/christmas_village/victorian/cottage/victorian_cottage.scad" reason="Square Victorian cottage, gated and finished; Scott 2026-09-30 asked for the cottages round (drum + front gable). Also at git commit a8eea51." -->
## 20260930-002 · 2026-09-30 · file · `openscad_models/christmas_village/victorian/cottage/victorian_cottage.scad`
**Reason:** Square Victorian cottage, gated and finished; Scott 2026-09-30 asked for the cottages round (drum + front gable). Also at git commit a8eea51.  
**Payload:** `data/trash/files/20260930-002__victorian_cottage.scad`

```
// Victorian Cottage -- building #1 of the Dickens Victorian Christmas village
// (openscad_models/christmas_village/CHRISTMAS_VILLAGE.md). The cottage from
// the style study, rebuilt to print: brick walls with white quoins, a steep
// slate gable under snow, a pierced white bargeboard with a finial on both
// gables, segmental-arched sash windows with keystones, gothic lancets in the
// gables, a round-arched black door with a wreath and a garland, window boxes,
// icicles under the eaves, a chimney with two pots, on a snow base.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on (the chapel's first print,
// 2026-09-27: free-standing bars snap).
//
// The machinery -- V-course walls, sheared reliefs, the eave flare, kneelers,
// the coping over the gables, frames and panes -- is the Haunted Town chapel's
// (haunted_town/chapel/haunted_chapel.scad), proven on Scott's printer, and
// its WHY comments are there. What is new here is commented here.
//
// COLOUR PARTS, ONE PRINT (victorian_cottage.3mf):
//   body    brick walls, chimney and pots, the kneelers, the bows
//   roof    slate slab and courses, the front door
//   trim    snow base and drifts, quoins, bargeboards and finials, window and
//           door frames, sills, keystones, panes and bars, the eave soffit and
//           icicles, the snow on the roof
//   accent  evergreen: the wreath, the garland, the window boxes
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// TEALIGHT. 60.6 x 54.6 mm clear inside from the table to the 52 mm eave; the
// 58 deg ceiling is 60 mm up at the edge of a 46 mm circle round the centre.

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts; lives in openscad_models/

$fa = 4;  $fs = 0.4;
part = "all";

// ---- walls ---------------------------------------------------------------------
W        = 64;              // along X, the front gable's width
D        = 58;              // along Y, front (-Y) to back
wall     = 1.68;            // 4 x 0.42
corner_r = 1;
plinth_h = 8;               // the snow base; the walls stand on it
Wh = W/2;  Dh = D/2;
SH       = 1.2;             // relief shear (see relief_up)

// ---- brick -----------------------------------------------------------------------
// The post office's brick: V courses ramping out at 58 deg, flat, chamfered
// back in at 45; stretcher bond.
bd    = 0.6;                // brick face, proud of plan(0)
bp    = 2.6;                // course height
br    = bd * tan(58);
bj    = 0.6;                // joint width
bl    = 7;                  // brick length, joint to joint
// The first groove sits 0.4 above the snow: exactly on the base's top it left
// a zero-thickness sheet of brick along the front wall where the two met.
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

// ---- roof --------------------------------------------------------------------------
// A 58 deg gable: the chapel's roof at the post office's steepest safe angle.
// Its inside is the lantern's ceiling.
H     = 52;
r_ang = 58;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + bd + e;
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Dh - wall;
cp_lo = -0.2;  cp_hi = 2.6;

// ---- placement ---------------------------------------------------------------------
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
module nf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
function loc(f, u) = (f == 0 || f == 3) ? -u : u;

module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0,
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260930-002 -->
<!-- TRASH id=20260930-003 date=2026-09-30 kind=file source="openscad_models/christmas_village/gingerbread/cottage/gingerbread_cottage.scad" reason="Square gingerbread cottage, gated and finished; Scott 2026-09-30 asked for the cottages round (cupcake drum + dome). Also at git commit 7de06df." -->
## 20260930-003 · 2026-09-30 · file · `openscad_models/christmas_village/gingerbread/cottage/gingerbread_cottage.scad`
**Reason:** Square gingerbread cottage, gated and finished; Scott 2026-09-30 asked for the cottages round (cupcake drum + dome). Also at git commit 7de06df.  
**Payload:** `data/trash/files/20260930-003__gingerbread_cottage.scad`

```
// Gingerbread Cottage -- building #1 of the Gingerbread Christmas village
// (openscad_models/christmas_village/CHRISTMAS_VILLAGE.md). The cottage from
// the style study, rebuilt to print: smooth gingerbread walls with piped
// icing beads down every corner and round every window and the door, a steep
// roof of chocolate scallop tiles, icing on the ridge and dripping off the
// eaves and rakes, gumdrops along the ridge, a chocolate-bar door between two
// candy canes, a peppermint round window in each gable, peppermint candies on
// the snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on.
//
// Same frame as the Victorian cottage (victorian/cottage/victorian_cottage.scad)
// and so the chapel's machinery; its WHY comments are in those two files. What
// is new is commented here.
//
// COLOUR PARTS, ONE PRINT (gingerbread_cottage.3mf):
//   body    gingerbread walls, the kneelers
//   roof    chocolate slab and scallop tiles, the chocolate-bar door
//   trim    icing: snow base, corner beads, window and door frames and their
//           beads, panes and bars, eave soffit and drips, rake bands and
//           drips, icing on the roof, the candy canes' white, the
//           peppermints' white
//   accent  candy red: gumdrops, cane stripes, peppermint stripes
// Every part is built DISJOINT from the others (part="chk_*").
//
// TEALIGHT. 60.6 x 54.6 mm clear inside from the table to the 52 mm eave.

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";

// ---- walls ---------------------------------------------------------------------
W        = 64;
D        = 58;
wall     = 1.68;
corner_r = 2.5;             // softer than brick: a baked edge
plinth_h = 8;
Wh = W/2;  Dh = D/2;
SH       = 1.2;
bd       = 0;               // the walls are smooth: no brick face

// ---- roof --------------------------------------------------------------------------
H     = 52;
r_ang = 58;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + bd + e;
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Dh - wall;
cp_lo = -0.2;  cp_hi = 2.2;

// ---- placement ---------------------------------------------------------------------
module nf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
function loc(f, u) = (f == 0 || f == 3) ? -u : u;

module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
module relief_hole(d0, a, b, sh = SH) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up(sh) translate([0, 0, a]) linear_extrude(b - a) translate([0, -sh * d0]) children();
}
module relief_up(d0, d1, sh = SH) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up(sh) translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1, sh) children(1);
    }
}
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();

// ---- nave regions -------------------------------------------------------------------------
module below_ceil() xz(-60, 60) polygon([[-40, -5], [40, -5], [40, z_ceil(40)], [0, z_ceil(0)], [-40, z_ceil(-40)]]);
module gable_keep() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
        xz(Dh - wall, Dh + 5) polygon([[-xe, -5], [xe, -5], [xe, z_out(xe) + 1], [0, z_out(0) + 1], [-xe, z_out(xe) + 1]]);
}
fl_ang = 52;
xf  = xe - 0.08;
zf0 = z_ceil(xf) - (xf - Wh) * tan(fl_ang);
fl_xe = z_ceil(xf) + (xe - xf) * tan(fl_ang);
module kneelers() {
    for (s = [-1, 1], m = [0, 1]
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260930-003 -->
<!-- TRASH id=20261001-001 date=2026-10-01 kind=snippet source="openscad_models/christmas_village/victorian/church/victorian_church.scad" reason="church tower quoins removed: skipped round windows and bands they left isolated white squares that read as noise (render 2026-10-01)" -->
## 20261001-001 · 2026-10-01 · snippet · `openscad_models/christmas_village/victorian/church/victorian_church.scad`
**Reason:** church tower quoins removed: skipped round windows and bands they left isolated white squares that read as noise (render 2026-10-01)  
**Payload:** `data/trash/files/20261001-001__snippet.txt`

```
// QUOINS on its two free corners, short ones (the windows are near), skipped
// where a window's frame or a band is
tq_long = 4.0;  tq_short = 2.4;
function tq_free(z0, z1) = len([for (w = TWIN) if (w[0] != 2 && z1 > w[2] - fr_w - 0.5 && z0 < w[2] + w_top(w) + fr_w + 0.5) 1]) == 0
                         && len([for (b = TB_BANDS) if (z1 > b - 2.6 && z0 < b + 1.8) 1]) == 0;
module tower_quoins() intersection() {
    at_tw() brick_skin(tw_s, tw_s, z_tw - 2);
    for (j = [0 : floor((z_tw - 6 - zc(0)) / (2 * bp)) - 1], sy = [-1, 1]) let (z0 = zc(2 * j), z1 = zc(2 * j + 2))
        if (tq_free(z0, z1)) let (lx = j % 2 == 0 ? tq_long : tq_short, ly = j % 2 == 0 ? tq_short : tq_long) {
            translate([TB[0] - 3, sy > 0 ? TB[3] - 0.5 : TB[2] - 3, z0 + q_off]) cube([lx + 3, 3.5, z1 - z0]);
            translate([TB[0] - 3, sy > 0 ? TB[3] - ly : TB[2] - 3, z0 + q_off]) cube([3.5, ly + 3, z1 - z0]);
        }
}
```

<!-- /TRASH 20261001-001 -->
<!-- TRASH id=20261001-002 date=2026-10-01 kind=snippet source="openscad_models/christmas_village/victorian/church/victorian_church.scad" reason="church door_hole removed: cut outward through the door's face it erased the wreath's brick bow (two loose fragments, slicer supports); the slate leaf fills the opening so no frame hole is needed" -->
## 20261001-002 · 2026-10-01 · snippet · `openscad_models/christmas_village/victorian/church/victorian_church.scad`
**Reason:** church door_hole removed: cut outward through the door's face it erased the wreath's brick bow (two loose fragments, slicer supports); the slate leaf fills the opening so no frame hole is needed  
**Payload:** `data/trash/files/20261001-002__snippet.txt`

```
module door_hole() nf(1, 0, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) door_outline();
```

<!-- /TRASH 20261001-002 -->
<!-- TRASH id=20261007-001 date=2026-10-07 kind=snippet source="openscad_models/haunted_town/bakery/haunted_bakery.scad" reason="Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print." -->
## 20261007-001 · 2026-10-07 · snippet · `openscad_models/haunted_town/bakery/haunted_bakery.scad`
**Reason:** Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print.  
**Payload:** `data/trash/files/20261007-001__snippet.txt`

```
// The letters are CARVED 0.6 into the board and lined with the accent part
// (2026-09-26). As a flush inlay they were colour alone: a one-colour print,
// or a slicer that put every part on one filament, lost the sign entirely.
// The cut's ceilings rise outward at 58 deg -- a straight-cut 0.6
// recess drew 1,528 support moves on a test block, the sheared one none.
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(58);  lt_n = 8;
module sign_text() text("BAKERY", size = 5.2, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.06);
module sign_at() face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0, fr_t]) children();
// 2D: the part of the letters whose whole climb of h above it stays inside
// them, sampled every lt_step. The same steps for every slab, so each deeper
// slab lies inside the one in front of it and no cut can close over a pocket.
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
// The cut, in lt_n slabs, each as deep as its ceiling allows. Built from 2D
// slabs rather than sheared copies of one prism: the copies' sides lay in
// shared planes and left zero-area faces.
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
// The letters and the board's hole are cut from the SAME placed cutter, so
// their faces are one computation (placed as one already-cut solid, the
// cemetery's linings came out a rounding error off their holes).
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}
```

<!-- /TRASH 20261007-001 -->
<!-- TRASH id=20261007-002 date=2026-10-07 kind=snippet source="openscad_models/haunted_town/post_office/haunted_post_office.scad" reason="Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print." -->
## 20261007-002 · 2026-10-07 · snippet · `openscad_models/haunted_town/post_office/haunted_post_office.scad`
**Reason:** Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print.  
**Payload:** `data/trash/files/20261007-002__snippet.txt`

```
// The letters are CARVED 0.6 into the board and lined with the accent part
// (2026-09-26). As a flush inlay they were colour alone: a one-colour print,
// or a slicer that put every part on one filament, lost the sign entirely.
// The cut's ceilings rise outward at 58 deg -- a straight-cut 0.6
// recess drew 1,528 support moves on a test block, the sheared one none.
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(58);  lt_n = 8;
module sign_text() text("POST OFFICE", size = 4.4, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.04);
module sign_at() face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0.3, fr_t]) children();
// 2D: the part of the letters whose whole climb of h above it stays inside
// them, sampled every lt_step. The same steps for every slab, so each deeper
// slab lies inside the one in front of it and no cut can close over a pocket.
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
// The cut, in lt_n slabs, each as deep as its ceiling allows. Built from 2D
// slabs rather than sheared copies of one prism: the copies' sides lay in
// shared planes and left zero-area faces.
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
// The letters and the board's hole are cut from the SAME placed cutter, so
// their faces are one computation (placed as one already-cut solid, the
// cemetery's linings came out a rounding error off their holes).
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}
```

<!-- /TRASH 20261007-002 -->
<!-- TRASH id=20261007-003 date=2026-10-07 kind=snippet source="openscad_models/haunted_town/general_store/haunted_general_store.scad" reason="Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print." -->
## 20261007-003 · 2026-10-07 · snippet · `openscad_models/haunted_town/general_store/haunted_general_store.scad`
**Reason:** Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print.  
**Payload:** `data/trash/files/20261007-003__snippet.txt`

```
// The letters are CARVED 0.6 into the board and lined with the accent part
// (2026-09-26). As a flush inlay they were colour alone: a one-colour print,
// or a slicer that put every part on one filament, lost the sign entirely.
// The cut's ceilings rise outward at 61 deg, 58 plus the front's forward lean, -- a straight-cut 0.6
// recess drew 1,528 support moves on a test block, the sheared one none.
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(61);  lt_n = 8;
// Spacing 1.06, not 1.04 (2026-09-26): at 1.04 the carve's stepped ceilings
// left a knife edge where CGAL joined the lining to the board, and the union
// failed the watertight gate. Nudging the sign, the step (0.19 drew supports
// under every letter: only 0.2 steps sit on the layers) or a proud lining all
// just moved it; 1.06 closed it, and MERCANTILE is 51.5 of the board's 56 mm.
module sign_text() text("MERCANTILE", size = 5.2, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.06);
module sign_at() on_face(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0.3, fr_t]) children();
// 2D: the part of the letters whose whole climb of h above it stays inside
// them, sampled every lt_step. The same steps for every slab, so each deeper
// slab lies inside the one in front of it and no cut can close over a pocket.
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
// The cut, in lt_n slabs, each as deep as its ceiling allows. Built from 2D
// slabs rather than sheared copies of one prism: the copies' sides lay in
// shared planes and left zero-area faces.
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
// The letters and the board's hole are cut from the SAME placed cutter, so
// their faces are one computation (placed as one already-cut solid, the
// cemetery's linings came out a rounding error off their holes).
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}
```

<!-- /TRASH 20261007-003 -->
<!-- TRASH id=20261007-004 date=2026-10-07 kind=snippet source="openscad_models/haunted_town/undertaker/haunted_undertaker.scad" reason="Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print." -->
## 20261007-004 · 2026-10-07 · snippet · `openscad_models/haunted_town/undertaker/haunted_undertaker.scad`
**Reason:** Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print.  
**Payload:** `data/trash/files/20261007-004__snippet.txt`

```
// carved 0.6 into the board and lined with the accent (the bakery's method)
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(58);  lt_n = 8;
module sign_text() text("UNDERTAKER", size = 4.0, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.06);
module sign_at() face_tf(1, 0, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0, fr_t]) children();
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}
```

<!-- /TRASH 20261007-004 -->
<!-- TRASH id=20261007-005 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/coaching_inn/victorian_coaching_inn.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-005 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/coaching_inn/victorian_coaching_inn.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-005__snippet.txt`

```
// the sign: a brick-red board on the plaster, INN inlaid white and flush
```

<!-- /TRASH 20261007-005 -->
<!-- TRASH id=20261007-006 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/coaching_inn/victorian_coaching_inn.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-006 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/coaching_inn/victorian_coaching_inn.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-006__snippet.txt`

```
module sign_text() intersection() {
    sign_board();
    nf(3, dr_u, sg_z + sg_h / 2) translate([0, 0, 0.2]) linear_extrude(2)
        text("INN", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.0);
}
```

<!-- /TRASH 20261007-006 -->
<!-- TRASH id=20261007-007 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/santas_workshop/victorian_santas_workshop.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-007 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/santas_workshop/victorian_santas_workshop.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-007__snippet.txt`

```
// the sign: a slate board, SANTA'S / WORKSHOP inlaid white and flush
```

<!-- /TRASH 20261007-007 -->
<!-- TRASH id=20261007-008 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/santas_workshop/victorian_santas_workshop.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-008 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/santas_workshop/victorian_santas_workshop.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-008__snippet.txt`

```
module sign_text() intersection() {
    sign_board();
    nf(3, dr_u, sg_z + sg_h / 2) translate([0, 0, 0.2]) linear_extrude(2)
        for (l = [["SANTA'S", 2.6], ["WORKSHOP", -2.6]]) translate([0, l[1]])
            text(l[0], size = 3.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.0);
}
```

<!-- /TRASH 20261007-008 -->
<!-- TRASH id=20261007-009 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/toy_shop/victorian_toy_shop.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-009 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/toy_shop/victorian_toy_shop.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-009__snippet.txt`

```
// the letters, raised on the fascia
module toys() bplace(1, (by_g[1] + by_t) / 2 + 0.2) relief_up(-0.4, 0.6)
```

<!-- /TRASH 20261007-009 -->
<!-- TRASH id=20261007-010 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/gingerbread/sweet_shop/gingerbread_sweet_shop.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-010 · 2026-10-07 · snippet · `openscad_models/christmas_village/gingerbread/sweet_shop/gingerbread_sweet_shop.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-010__snippet.txt`

```
// SWEETS round the front, over the shop's ridge, inlaid flush: raised, every
// level stroke (the E's arms, the T's bar) came to a knife edge under its
// sloped underside, down to 0.01 mm
module sweets() intersection() {
    difference() { cylinder(r = T(0)[0] + 0.01, h = 100, $fn = FNC); cylinder(r = T(0)[0] - 0.6, h = 100, $fn = FNC); }
    cyl_relief(T(0)[0], 270, 56.2, 12.5, 0.6) translate([0, 0, -1.5]) linear_extrude(2)
        text("SWEETS", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.08);
}
```

<!-- /TRASH 20261007-010 -->
<!-- TRASH id=20261007-011 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-011 · 2026-10-07 · snippet · `openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-011__snippet.txt`

```
module cocoa_text() press(270, 55.8)
    text("COCOA", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.08);
```

<!-- /TRASH 20261007-011 -->
<!-- TRASH id=20261008-001 date=2026-10-08 kind=snippet source="victorian_santas_workshop.scad" reason="Toy window art given relief so a white print shows it (2026-10-08)." -->
## 20261008-001 · 2026-10-08 · snippet · `victorian_santas_workshop.scad`
**Reason:** Toy window art given relief so a white print shows it (2026-10-08).  
**Payload:** `data/trash/files/20261008-001__snippet.txt`

```
module bw_art() nf(3, BW_u, BW_z) translate([0, 0, -recess - pane_t]) linear_extrude(pane_t) pane_art2d();
```

<!-- /TRASH 20261008-001 -->
<!-- TRASH id=20261008-002 date=2026-10-08 kind=snippet source="openscad_models/christmas_village/gingerbread/candy_cane_chapel/gingerbread_candy_cane_chapel.scad" reason="Crook's raised rings removed: an 11 mm rod leaning to 40 deg; the rings needed 1,413 support moves even clipped clear of base and tip (2026-10-08)" -->
## 20261008-002 · 2026-10-08 · snippet · `openscad_models/christmas_village/gingerbread/candy_cane_chapel/gingerbread_candy_cane_chapel.scad`
**Reason:** Crook's raised rings removed: an 11 mm rod leaning to 40 deg; the rings needed 1,413 support moves even clipped clear of base and tip (2026-10-08)  
**Payload:** `data/trash/files/20261008-002__snippet.txt`

```
module cr_at_g(i, d) let (p = cr_pts(i)) translate([TC[0] + p[0], TC[1], cr_z0 + p[1]]) sphere(r = cr_r(i) + d, $fn = 24);
module crook_g(d) for (i = [0 : cr_n - 1]) hull() { cr_at_g(i, d); cr_at_g(i + 1, d); }
// Climbing 2 SH per 1 out, not SH: on stripes tilted 28 deg, SH alone left the
// slicer propping a test column's (the turret house, 2026-10-08); twice that
// sliced clean. And clear of the tip's end cap, which faces down past the rod.
module crook_stripes_up() for (k = [0 : 1]) intersection() {
    difference() { crook_g((k + 1) * 0.15); crook_g(k * 0.15); }
    crook_stripes();
    translate([0, 0, 2 * SH * (k + 1) * 0.15]) crook_stripes();
    translate([-100, -100, 0]) cube([200, 200, cr_z0 + cr_pts(cr_n)[1] - cr_r(cr_n)]);
}
```

<!-- /TRASH 20261008-002 -->
<!-- TRASH id=20261008-003 date=2026-10-08 kind=snippet source="openscad_models/christmas_village/gingerbread/turret_house/gingerbread_turret_house.scad" reason="Turret spire's raised rings removed, as the chapel crook's: a bent candy-cane rod leaning to 40 deg (2026-10-08)" -->
## 20261008-003 · 2026-10-08 · snippet · `openscad_models/christmas_village/gingerbread/turret_house/gingerbread_turret_house.scad`
**Reason:** Turret spire's raised rings removed, as the chapel crook's: a bent candy-cane rod leaning to 40 deg (2026-10-08)  
**Payload:** `data/trash/files/20261008-003__snippet.txt`

```
module sp_at_g(i, d) let (p = sp_pts(i)) translate([tx + p[0] * cos(tc_ang), ty + p[0] * sin(tc_ang), sp_z0 + p[1]]) sphere(r = sp_r(i) + d, $fn = 24);
module spire_g(d) for (i = [0 : sp_n - 1]) hull() { sp_at_g(i, d); sp_at_g(i + 1, d); }
module spire_stripes_up() for (k = [0 : 1]) lean() intersection() {
    difference() { spire_g((k + 1) * 0.15); spire_g(k * 0.15); }
    stripe_slabs([tx, ty], sp_z0 + 1, sp_z0 + 12, 2.2, 0.9, 28);
    translate([0, 0, 2 * SH * (k + 1) * 0.15]) stripe_slabs([tx, ty], sp_z0 + 1, sp_z0 + 12, 2.2, 0.9, 28);
    translate([-100, -100, 0]) cube([200, 200, sp_z0 + sp_pts(sp_n)[1] - sp_r(sp_n)]);
}
```

<!-- /TRASH 20261008-003 -->
<!-- TRASH id=20261008-004 date=2026-10-08 kind=snippet source="openscad_models/christmas_village/gingerbread/candy_cane_chapel/gingerbread_candy_cane_chapel.scad" reason="Chapel tower's raised spiral bands (wall, inner and swept spire): sliced on the old chapel they needed ~21,000 support moves (outer) and ~56,000 (with inner) at every lower edge; steeper climb, 0.1 steps, a lower top and clipping to outside the nave did not clear them (2026-10-08)" -->
## 20261008-004 · 2026-10-08 · snippet · `openscad_models/christmas_village/gingerbread/candy_cane_chapel/gingerbread_candy_cane_chapel.scad`
**Reason:** Chapel tower's raised spiral bands (wall, inner and swept spire): sliced on the old chapel they needed ~21,000 support moves (outer) and ~56,000 (with inner) at every lower edge; steeper climb, 0.1 steps, a lower top and clipping to outside the nave did not clear them (2026-10-08)  
**Payload:** `data/trash/files/20261008-004__snippet.txt`

```
module tower_prof2d() {
    polygon([[rti - 0.3, plinth_h - 0.5], [rt, plinth_h - 0.5], [rt, R_zc(RS, rt) + 0.6], [rti - 0.3, R_zc(RS, rti - 0.3) + 0.6]]);
    R_full(RS, kv0s);
}
module tower_shell(t0, t1) at_tc() rotate_extrude($fn = FNT) difference() {
    intersection() { offset(delta = t1) tower_prof2d(); translate([0, plinth_h]) square([100, 300]); }
    offset(delta = t0) tower_prof2d();
    R_room(RS);
}
// 0.05 on into the wall: one that ends at the wall's face only touches it, and
// the union can keep the face between (the coaching inn, 2026-10-08)
module tower_in_shell(t0, t1) at_tc() rotate_extrude($fn = FNT)
    translate([rti - t1, plinth_h]) square([t1 - t0 + 0.05, RS[0] - 1 - plinth_h]);
// A band raised t its stripe moved up SH * t: the stripe narrowed by the angle
// that climb turns through, so its upper edge (in angle) is the one that steps.
// Built narrowed rather than as the stripe intersected with a raised copy of
// itself: the two copies' twisted facets crossed, and left 1,838 crumbs of
// band up the spire and round the door (2026-10-08).
function st_climb(t) = st_w - 360 * SH * t / st_P;
// the straight wall's bands stop under the eave's flare (st_zw); the spire's
// are swept (spire_bands)
st_zw = 87.9;
module stripe_bands() {
    zt = R_top(RS, 0) + 1;
    for (i = [0 : 1]) intersection() {
        tower_shell(i * 0.2, (i + 1) * 0.2); helix(plinth_h - 1, zt, st_climb((i + 1) * 0.2));
        translate([-100, -100, 0]) cube([200, 200, st_zw]);
    }
    spire_bands();
    difference() {
        for (i = [0 : 2]) intersection() { tower_in_shell(i * 0.2, (i + 1) * 0.2); helix(plinth_h - 1, zt, st_climb((i + 1) * 0.2)); }
        // through the doorway, the inner bands stop at its edge, the cut over
        // its head climbing SH per 1 into the room
        cyl_relief(rt, dth, plinth_h, door_a + 2.4) relief_hole(-wall, -wall - 1.2, 0.5, -SH) offset(delta = 0.2) polygon(arch_pts(door_a, door_h));
    }
}
// No band over the door and the windows: there it stood as a skin over their
// frames, the door's leaf and the panes. It stops at each frame's edge, and
// the frame below holds up whatever runs over a head.
module tower_frames_clear() {
    tw_frames(); door_frame();
    for (w = TW) cyl_relief(rt, w[0], w[1], tframe_U(w)) translate([0, 0, -1]) linear_extrude(3) offset(r = fr_w) win_outline(tw(w));
    cyl_relief(rt, dth, plinth_h, door_a + fr_w + 1.2) translate([0, 0, -1]) linear_extrude(3) offset(r = fr_w) polygon(arch_pts(door_a, door_h));
}
// THE SPIRE'S BANDS, swept along its profile rather than cut from a shell: a
// 0.2 mm shell on the 68 deg spire, cut by the twisted prism's facets, came
// apart into 1,274 crumbs (2026-10-08). Each band is one solid from the eave's
// edge to below the crook: its inner face 0.05 inside the spire, its outer
// 0.4 out along the profile's normal, and its upper edge in angle trimmed by
// the climb, so that side slopes SH up per 1 out like every band below it.
sp_h = 0.4;  sp_n = 110;  sp_J = 8;
function sp_v(i) = RS[5] - 0.2 - (RS[5] - 1.6) * i / (sp_n - 1);
function sp_p(i) = [sp_v(i), R_top(RS, sp_v(i))];
function sp_nrm(i) = let (a = sp_p(max(i - 1, 0)), b = sp_p(min(i + 1, sp_n - 1)), t = (b - a) / norm(b - a)) [t[1], -t[0]];
function sp_last() = max([for (i = [0 : sp_n - 1]) if (sp_p(i)[1] < cr_z0 - 1) i]);
function sp_pt(i, j, s) = let (q = sp_p(i) + sp_nrm(i) * (s == 0 ? -0.05 : sp_h),
        a = 360 * (q[1] - (plinth_h - 1)) / st_P + j / sp_J * (s == 0 ? st_w : st_climb(sp_h)))
    [q[0] * cos(a), q[0] * sin(a), q[1]];
module spire_band() let (N = sp_last() + 1, J = sp_J, id = function (i, j, s) (i * (J + 1) + j) * 2 + s)
    polyhedron([for (i = [0 : N - 1], j = [0 : J], s = [0 : 1]) sp_pt(i, j, s)], concat(
        [for (i = [0 : N - 2], j = [0 : J - 1]) [id(i, j, 1), id(i + 1, j, 1), id(i + 1, j + 1, 1), id(i, j + 1, 1)]],
        [for (i = [0 : N - 2], j = [0 : J - 1]) [id(i, j + 1, 0), id(i + 1, j + 1, 0), id(i + 1, j, 0), id(i, j, 0)]],
        [for (i = [0 : N - 2]) [id(i, 0, 0), id(i + 1, 0, 0), id(i + 1, 0, 1), id(i, 0, 1)]],
        [for (i = [0 : N - 2]) [id(i, J, 1), id(i + 1, J, 1), id(i + 1, J, 0), id(i, J, 0)]],
        [for (j = [0 : J - 1]) [id(0, j, 0), id(0, j, 1), id(0, j + 1, 1), id(0, j + 1, 0)]],
        [for (j = [0 : J - 1]) [id(N - 1, j + 1, 0), id(N - 1, j + 1, 1), id(N - 1, j, 1), id(N - 1, j, 0)]]));
module spire_bands() at_tc() for (k = [0 : st_n - 1]) rotate(k * 360 / st_n) spire_band();
// where the tower's wall is cut away inside the nave (its doorway), no band
module stripe_relief() difference() { stripe_bands(); difference() { nave_room(); turret_partition(); } tower_frames_clear(); }
```

<!-- /TRASH 20261008-004 -->
<!-- TRASH id=20261008-005 date=2026-10-08 kind=snippet source="openscad_models/christmas_village/gingerbread/cottage/gingerbread_cottage.scad" reason="Cottage canes' raised stripes removed: trimmed to a narrow cane's flat front they left slivers (0.04-0.89 mm spans) and the 1st-percentile wall at 1.19 mm (2026-10-08)" -->
## 20261008-005 · 2026-10-08 · snippet · `openscad_models/christmas_village/gingerbread/cottage/gingerbread_cottage.scad`
**Reason:** Cottage canes' raised stripes removed: trimmed to a narrow cane's flat front they left slivers (0.04-0.89 mm spans) and the 1st-percentile wall at 1.19 mm (2026-10-08)  
**Payload:** `data/trash/files/20261008-005__snippet.txt`

```
module cane_stripes_up() sclip(Rw, fr_t + 0.81) for (s = [-1, 1]) srelief(Rw, s * cane_s, plinth_h, cane_R * 2 + cane_w + 0.6)
    translate([0, 0, fr_t + 0.5]) art_skirt(0.3, 2) w12() intersection() { top_face(fr_t + 0.8) cane2d(-s); stripes2d(); }
```

<!-- /TRASH 20261008-005 -->
<!-- TRASH id=20261009-001 date=2026-10-09 kind=snippet source="tools/viewer/app.js" reason="Replaced by the fetch-and-parse loader (plates read as data, real progress); the <script> path survives as loadJobScriptTag for file://" -->
## 20261009-001 · 2026-10-09 · snippet · `tools/viewer/app.js`
**Reason:** Replaced by the fetch-and-parse loader (plates read as data, real progress); the <script> path survives as loadJobScriptTag for file://  
**Payload:** `data/trash/files/20261009-001__snippet.txt`

```javascript
function loadJob(id) {
  if (id === currentId && JOB) { return; }
  currentId = id;
  loading.hidden = false;
  loading.firstChild.textContent = 'Loading ' +
    (INDEX.filter(function (j) { return j.id === id; })[0] || {name:id}).name;
  paintJobList();
  setPlaying(false);
  var s = document.createElement('script');
  s.setAttribute('data-job', id);
  s.src = 'jobs/' + id + '.js';
  s.onerror = function () {
    loading.innerHTML = '<div style="text-align:center;color:var(--bad)">' +
      'Could not load jobs/' + id + '.js</div>';
  };
  document.body.appendChild(s);
}
```

<!-- /TRASH 20261009-001 -->
<!-- TRASH id=20261009-002 date=2026-10-09 kind=snippet source="openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad" reason="Cocoa cafe: mug windows' inner thickening (art_in) overhung on the curved inner wall; the slicer propped it from the mug floor (gate 2026-10-09)" -->
## 20261009-002 · 2026-10-09 · snippet · `openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad`
**Reason:** Cocoa cafe: mug windows' inner thickening (art_in) overhung on the curved inner wall; the slicer propped it from the mug floor (gate 2026-10-09)  
**Payload:** `data/trash/files/20261009-002__snippet.txt`

```
    cyl_relief(MRi, w[0], w[1], w[2] + 2.2, 0.6) art_in(0.8, 4) mw2d(w);
```

<!-- /TRASH 20261009-002 -->
<!-- TRASH id=20261009-003 date=2026-10-09 kind=snippet source="openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad" reason="Cocoa cafe: stirrer stripe relief on the tilted cane needed supports; stripes left to paint" -->
## 20261009-003 · 2026-10-09 · snippet · `openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad`
**Reason:** Cocoa cafe: stirrer stripe relief on the tilted cane needed supports; stripes left to paint  
**Payload:** `data/trash/files/20261009-003__snippet.txt`

```
module st_at_g(i, d) let (p = st_pts(i)) rotate(st_th) translate([st_r0 + p[0], 0, st_z0 + p[1]]) sphere(r = 1.9 + d, $fn = 24);
module stirrer_g(d) for (i = [0 : st_n - 1]) hull() { st_at_g(i, d); st_at_g(i + 1, d); }
module stirrer_stripes_up() for (k = [0 : 1]) intersection() {
    difference() { stirrer_g((k + 1) * 0.15); stirrer_g(k * 0.15); }
    stirrer_stripes();
    translate([0, 0, SH * (k + 1) * 0.15]) stirrer_stripes();
}
    stirrer_stripes_up();
```

<!-- /TRASH 20261009-003 -->
<!-- TRASH id=20261009-004 date=2026-10-09 kind=snippet source="openscad_models/christmas_village/gingerbread/cookie_clock_tower/gingerbread_cookie_clock_tower.scad" reason="Cookie clock tower: stripe relief on the tilted cane needed 4,638 support moves on a fresh union (2026-10-09); stripes left to paint" -->
## 20261009-004 · 2026-10-09 · snippet · `openscad_models/christmas_village/gingerbread/cookie_clock_tower/gingerbread_cookie_clock_tower.scad`
**Reason:** Cookie clock tower: stripe relief on the tilted cane needed 4,638 support moves on a fresh union (2026-10-09); stripes left to paint  
**Payload:** `data/trash/files/20261009-004__snippet.txt`

```
module cr_at_g(i, d) let (p = cr_pts(i)) translate([p[0], 0, cr_z0 + p[1]]) sphere(r = cr_r(i) + d, $fn = 24);
module cane_g(d) {
    translate([0, 0, z_co(0) - 3]) cylinder(r = 1.9 + d, h = cn_z0 + cn_h - z_co(0) + 3, $fn = 24);
    for (i = [0 : cr_n - 1]) hull() { cr_at_g(i, d); cr_at_g(i + 1, d); }
}
module cane_slabs(dz) for (z = [cn_z0 + 1.0 : 2.4 : cr_z0 + cr_L + 2]) translate([0, 0, z + dz]) rotate([0, -28, 0]) cube([20, 20, 1.0], center = true);
// above the cone's cap only: below it the rod is buried in the icing
module cane_stripes_up() for (k = [0 : 1]) intersection() {
    difference() { cane_g((k + 1) * 0.15); cane_g(k * 0.15); }
    cane_slabs(0);
    cane_slabs(SH * (k + 1) * 0.15);
    translate([-50, -50, cn_z0]) cube([100, 100, 100]);
}
    cane_stripes_up();
```

<!-- /TRASH 20261009-004 -->
<!-- TRASH id=20261010-001 date=2026-10-10 kind=snippet source="tools/viewer/app.js" reason="buildEnvironment's softbox room: every panel sat beyond r128 PMREM fromScene's far plane (100) and never rendered; replaced by the captured Poly Haven studio with a uniform-dark placeholder" -->
## 20261010-001 · 2026-10-10 · snippet · `tools/viewer/app.js`
**Reason:** buildEnvironment's softbox room: every panel sat beyond r128 PMREM fromScene's far plane (100) and never rendered; replaced by the captured Poly Haven studio with a uniform-dark placeholder  
**Payload:** `data/trash/files/20261010-001__snippet.txt`

```javascript
// ── environment ────────────────────────────────────────────────────────────
// The thing that actually makes metal look like metal. Without an environment
// map a MeshStandardMaterial with metalness 0.9 has nothing to reflect and
// renders nearly black -- which is the classic "I switched to PBR and it got
// worse" failure. This builds a small studio by hand (overhead softbox, cool
// fill from one side, warm bounce from below) and runs it through PMREM so
// rough surfaces get a properly blurred version of it.
function buildEnvironment() {
  var pmrem = new THREE.PMREMGenerator(renderer);
  var room = new THREE.Scene();
  room.background = new THREE.Color(lin(0x0b0d12));

  function panel(w, h, d, color, intensity, x, y, z, rx, ry) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d),
      new THREE.MeshBasicMaterial({color: lin(color)}));
    m.material.color.multiplyScalar(intensity);
    m.position.set(x, y, z);
    if (rx) { m.rotation.x = rx; }
    if (ry) { m.rotation.y = ry; }
    room.add(m);
    return m;
  }

  // First pass at these numbers had a 1.5-intensity cool fill and it turned
  // the whole machine powder blue -- an environment map lights EVERYTHING, so
  // a tint that looks like a tasteful accent in isolation becomes the colour
  // of the product. Warm key, restrained cool, and a dark back wall so metal
  // has something black to reflect: without a dark region in the environment,
  // polished surfaces have no contrast and read as flat grey plastic.
  panel(600, 10, 420, 0xfff2de, 2.2,    0,  360,   40, 0, 0);   // key softbox
  panel(10, 460, 420, 0xa8c0e0, 0.45, -420,  60,    0, 0, 0);   // cool fill
  panel(10, 460, 420, 0xffcfa0, 0.30,  420,  40,    0, 0, 0);   // warm kicker
  panel(600, 10, 420, 0x5a6270, 0.18,   0, -300,    0, 0, 0);   // floor bounce
  panel(600, 460, 10, 0x05070b, 1.0,    0,   40, -360, 0, 0);   // back wall

  envRT = pmrem.fromScene(room, 0.5);
  scene.environment = envRT.texture;
  room.traverse(function (o) {
    if (o.geometry) { o.geometry.dispose(); }
    if (o.material) { o.material.dispose(); }
  });
  pmrem.dispose();
}
```

<!-- /TRASH 20261010-001 -->
