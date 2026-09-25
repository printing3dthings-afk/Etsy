# Deletion Recycle Bin

> Everything deleted by an automated edit (code blocks or whole files) is
> archived here first, kept for **30 days**, then auto-pruned. To recover
> something, run `python tools/trash.py --restore <id>` (or just copy it back
> out of the fenced block below). Byte-exact copies also live in
> `data/trash/files/`.

<!-- TRASH id=20260904-001 date=2026-09-04 kind=snippet source="tools/detail_probe.py" reason="Horizontal-banding metric cut 2026-09-04. Measured a real phenomenon but could not be made trustworthy in three principled attempts: (1) raw high-pass amplitude scored a single box-lid ledge as hard as a stack of ridges; (2) counting baseline crossings did not reject it, because multi-part plates genuinely oscillate; (3) a single-body filter plus a roundness gate finally rejected the box but also rejected every deeply fluted vase, since deep flutes make a rotational body look non-rotational to a radius-spread test. rugosity + texture_recipe.py already answer the question this was for." -->
## 20260904-001 · 2026-09-04 · snippet · `tools/detail_probe.py`
**Reason:** Horizontal-banding metric cut 2026-09-04. Measured a real phenomenon but could not be made trustworthy in three principled attempts: (1) raw high-pass amplitude scored a single box-lid ledge as hard as a stack of ridges; (2) counting baseline crossings did not reject it, because multi-part plates genuinely oscillate; (3) a single-body filter plus a roundness gate finally rejected the box but also rejected every deeply fluted vase, since deep flutes make a rotational body look non-rotational to a radius-spread test. rugosity + texture_recipe.py already answer the question this was for.  
**Payload:** `data/trash/files/20260904-001__snippet.txt`

```python
def ring_texture(m, slices=140, smooth=9):
    """Horizontal banding: high-frequency ripple in radius-vs-height.

    Deliberately NOT measured by slicing along X. An X-slice contains the
    model's whole silhouette profile, so a vase neck or a pumpkin stem
    dimple reads as huge "texture" -- the exact form-contamination the four
    rejected metrics all suffered from. Instead: take the median radius of
    each horizontal slice, subtract a moving average of itself, and keep
    what's left. Taper, flare and belly are low-frequency and vanish in the
    subtraction; a stack of ridges or beads is high-frequency and survives.
    """
    try:
        # One body only. A plate holding a box AND its lid AND three tools
        # makes the median radius jump every time a different part enters
        # the slice, which reads as violent "banding" -- a plain Game Card
        # Box topped the ranking at 41.8% that way, and counting the
        # oscillations did not reject it because there genuinely were 64.
        # The assumption this metric rests on is a single body, so enforce
        # it rather than trying to filter the symptom.
        try:
            parts = m.split(only_watertight=False)
            if len(parts) > 1:
                m = max(parts, key=lambda p: len(p.faces))
        except Exception:
            pass
        V = np.asarray(m.vertices, dtype=np.float64)
        zc = V[:, 2]
        z0, z1 = np.percentile(zc, 6), np.percentile(zc, 94)
        if z1 - z0 <= 0:
            return None
        cx, cy = np.median(V[:, 0]), np.median(V[:, 1])
        rad = np.hypot(V[:, 0] - cx, V[:, 1] - cy)
        edges = np.linspace(z0, z1, slices + 1)
        prof, round_ratio = [], []
        for b in range(slices):
            sel = (zc >= edges[b]) & (zc < edges[b + 1])
            if sel.sum() < 8:
                prof.append(np.nan)
                continue
            rb = rad[sel]
            prof.append(float(np.median(rb)))
            lo_r = float(np.percentile(rb, 10))
            if lo_r > 1e-6:
                round_ratio.append(float(np.percentile(rb, 90)) / lo_r)
        # "Radius from the centroid" only means something on a roughly
        # rotational body. On a flat hinged box it is noise, and that noise
        # topped the banding ranking (a Game Card Box at 41.8%) even after
        # single-body and oscillation filters, because the box really is one
        # body and really does oscillate. Gate on the shape instead: a round
        # or square-ish section stays under ~1.5, a slab does not.
        if not round_ratio or float(np.median(round_ratio)) > 1.5:
            return None
        prof = np.array(prof)
        ok = ~np.isnan(prof)
        if ok.sum() < slices * 0.6:
            return None
        prof = np.interp(np.arange(slices), np.flatnonzero(ok), prof[ok])
        k = np.ones(smooth) / smooth
        base = np.convolve(np.pad(prof, smooth // 2, mode="edge"), k, mode="valid")[:slices]
        resid = np.abs(prof - base)
        # trim the ends: the moving average is least reliable there
        resid = resid[smooth:-smooth] if len(resid) > 3 * smooth else resid
        amp = float(np.median(resid))
        mr = float(np.median(prof))
        if mr < 1.0:
            return None
        # Amplitude alone is not banding. A single ledge -- a box lid step,
        # a base flange -- is a step function, and a step is high-frequency,
        # so it scored as hard as a stack of ridges (a plain "Game Card Box"
        # topped the amplitude ranking at 41.8%). Real banding OSCILLATES,
        # so count how many times the residual actually crosses its own
        # baseline: one ledge gives ~2, a run of beads gives 10+.
        signed = prof - base
        signed = signed[smooth:-smooth] if len(signed) > 3 * smooth else signed
        live = np.abs(signed) > max(amp * 0.5, 1e-6)
        s = np.sign(signed[live])
        cycles = int((np.diff(s) != 0).sum()) if len(s) > 1 else 0
        return {
            "ring_amp_mm": round(amp, 3),
            "ring_amp_pct": round(100.0 * amp / mr, 3),
            "ring_cycles": cycles,
        }
    except Exception:
        return None
```

<!-- /TRASH 20260904-001 -->
<!-- TRASH id=20260905-001 date=2026-09-05 kind=snippet source="tests/test_kb_skill_docs.py" reason="Static grep over test sources for the ops_runbook writer. Replaced by a real before/after hash of data/knowledge_base/ in tests/run_all.py. The grep could only catch a test that NAMED the writer, so it stayed green while test_competitor_research_refresh appended to the real doc on every run via _run_competitor_research_refresh()'s internal call. Keeping both would leave a weaker duplicate that reads as coverage it does not provide." -->
## 20260905-001 · 2026-09-05 · snippet · `tests/test_kb_skill_docs.py`
**Reason:** Static grep over test sources for the ops_runbook writer. Replaced by a real before/after hash of data/knowledge_base/ in tests/run_all.py. The grep could only catch a test that NAMED the writer, so it stayed green while test_competitor_research_refresh appended to the real doc on every run via _run_competitor_research_refresh()'s internal call. Keeping both would leave a weaker duplicate that reads as coverage it does not provide.  
**Payload:** `data/trash/files/20260905-001__snippet.txt`

```python
def test_suite_never_writes_to_the_real_runbook():
    """No test may append to the git-tracked ops_runbook.md.

    Found 2026-09-05: test_health_check_reap and test_health_check_broadened
    exercise the escalation paths on purpose, and _append_ops_runbook_entry()
    writes to _OPS_RUNBOOK_PATH -- which is _volume_or_local(...), so with no
    volume mounted it falls back to the real data/knowledge_base copy. A suite
    run put eight fabricated incidents (TESTCRASH, TESTHUNG, a /tmp/... volume)
    into the document Frank reads as ground truth when Scott asks why something
    broke. Any test that can reach that writer must repoint _OPS_RUNBOOK_PATH
    at a tempfile first.
    """
    # Reaching the writer means calling something that appends, directly or via
    # the health loop. A bare "_escalate" substring was too loose on the first
    # pass -- it matched a test NAMED test_escalates_..., which writes nothing.
    reaches = ("_append_ops_runbook_entry(", "server._escalate", "_health_check_iteration(")
    # Two valid isolations: repoint the path, or mock the writer outright.
    # Matched against CODE only. The first version of this check searched the
    # raw file text, so the explanatory comment naming _OPS_RUNBOOK_PATH was
    # enough to satisfy it -- deleting the actual assignment left the guard
    # silently green. Verified by deleting it and watching this fail.
    isolates = (_re.compile(r"^\s*server\._OPS_RUNBOOK_PATH\s*=", _re.M),
                _re.compile(r'patch\.object\(\s*server\s*,\s*"_append_ops_runbook_entry"'))
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue  # this file names the patterns it searches for
        src = path.read_text()
        if not any(r in src for r in reaches):
            continue
        code = "\n".join(ln for ln in src.splitlines()
                         if not ln.lstrip().startswith("#"))
        check(any(pat.search(code) for pat in isolates),
              f"{path.name} can reach the ops_runbook writer but neither repoints "
              "server._OPS_RUNBOOK_PATH at a tempfile nor mocks "
              "_append_ops_runbook_entry — it will append test fixtures to the "
              "real git-tracked doc Frank reads as ground truth")
```

<!-- /TRASH 20260905-001 -->
<!-- TRASH id=20260909-001 date=2026-09-09 kind=file source="openscad_models/monogram_keychain_J_all.3mf" reason="OpenSCAD's 3MF export MERGES every body into one object with no materials (verified: 1 object, 1 item, 0 basematerials, 20,065 fused triangles). This file looked like the print-ready deliverable and could not have filaments assigned at all. Superseded by monogram_keychain_J.3mf from tools/assemble_3mf.py." -->
## 20260909-001 · 2026-09-09 · file · `openscad_models/monogram_keychain_J_all.3mf`
**Reason:** OpenSCAD's 3MF export MERGES every body into one object with no materials (verified: 1 object, 1 item, 0 basematerials, 20,065 fused triangles). This file looked like the print-ready deliverable and could not have filaments assigned at all. Superseded by monogram_keychain_J.3mf from tools/assemble_3mf.py.  
**Payload:** `data/trash/files/20260909-001__monogram_keychain_J_all.3mf`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260909-001 -->
<!-- TRASH id=20260909-002 date=2026-09-09 kind=file source="openscad_models/monogram_keychain_J_ring.3mf" reason="superseded by the assembled monogram_keychain_J.3mf" -->
## 20260909-002 · 2026-09-09 · file · `openscad_models/monogram_keychain_J_ring.3mf`
**Reason:** superseded by the assembled monogram_keychain_J.3mf  
**Payload:** `data/trash/files/20260909-002__monogram_keychain_J_ring.3mf`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260909-002 -->
<!-- TRASH id=20260909-003 date=2026-09-09 kind=file source="openscad_models/monogram_keychain_J_rotor.3mf" reason="superseded by the assembled monogram_keychain_J.3mf" -->
## 20260909-003 · 2026-09-09 · file · `openscad_models/monogram_keychain_J_rotor.3mf`
**Reason:** superseded by the assembled monogram_keychain_J.3mf  
**Payload:** `data/trash/files/20260909-003__monogram_keychain_J_rotor.3mf`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260909-003 -->
<!-- TRASH id=20260909-004 date=2026-09-09 kind=file source="openscad_models/monogram_keychain_J_letter.3mf" reason="superseded by the assembled monogram_keychain_J.3mf" -->
## 20260909-004 · 2026-09-09 · file · `openscad_models/monogram_keychain_J_letter.3mf`
**Reason:** superseded by the assembled monogram_keychain_J.3mf  
**Payload:** `data/trash/files/20260909-004__monogram_keychain_J_letter.3mf`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260909-004 -->
<!-- TRASH id=20260909-005 date=2026-09-09 kind=file source="openscad_models/bayonet_jar.scad" reason="superseded by v2: lid seated on rim, internal lock collar, ramped lock channel, OBC mark" -->
## 20260909-005 · 2026-09-09 · file · `openscad_models/bayonet_jar.scad`
**Reason:** superseded by v2: lid seated on rim, internal lock collar, ramped lock channel, OBC mark  
**Payload:** `data/trash/files/20260909-005__bayonet_jar.scad`

```
include <BOSL2/std.scad>

// ============================================================
// Bayonet twist-lock storage jar -- a genuinely new mechanism class for
// this shop (rotational push-then-twist lock, not a hinge or a screw
// thread; threading.scad/gears.scad aren't vendored in this BOSL2 copy,
// so this deliberately doesn't need them). Base + lid, shown assembled
// and LOCKED (unlike the cable clip's hinge, a correctly-designed
// bayonet lock has zero real overlap in its closed/locked pose by
// construction -- the pin only ever occupies carved-out slot space,
// never solid wall material -- so there's no "must export open" concern
// here the way there was for the clip's interference-fit latch).
// ============================================================

base_r   = 25;
base_h   = 45;
wall     = 2.4;
floor    = 3;

n_pins     = 3;
pin_r      = 2.0;
slot_clear = 0.5;
slot_r     = pin_r + slot_clear;   // radius of the tube-shaped slot cutter

travel_v      = 8;    // vertical entry length (push distance before twisting)
lock_angle    = 25;   // degrees of horizontal travel to reach the locked position
slot_top_z    = base_h;              // vertical entry starts at the base's own rim
slot_bottom_z = base_h - travel_v;   // horizontal lock channel height, and the
                                      // pin's real height once locked

// ---- Base: hollow body with 3 bayonet slots cut through the neck wall ----

module one_slot() {
    // Vertical entry: a plain radial box, thin tangentially (2*slot_r),
    // spanning the full wall thickness with margin so it's a clean
    // through-cut, from the rim down to where the lock channel begins.
    translate([base_r - wall - 1, -slot_r, slot_bottom_z])
        cube([wall + 2, 2 * slot_r, travel_v + slot_r + 1]);
    // Horizontal lock channel: a tube swept around the cylinder's own
    // curvature via rotate_extrude(angle=...) -- follows the true radius
    // exactly, no straight-line approximation of a curved wall.
    //
    // Cut angle_margin degrees PAST lock_angle -- the locked pin sits with
    // its CENTER exactly at lock_angle, so a cut stopping exactly there
    // leaves half the pin's own angular footprint overshooting into
    // uncut wall. angle_margin must clear atan(pin_r/base_r) (~4.6 deg
    // here) with real margin, not sit flush against it -- confirmed by a
    // direct intersection() render coming back non-empty at exactly this
    // boundary before the margin was added.
    angle_margin = 8;
    translate([0, 0, slot_bottom_z])
        rotate_extrude(angle = lock_angle + angle_margin, $fn = 90)
            translate([base_r, 0])
                circle(r = slot_r, $fn = 16);
}

module all_slots() {
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins])
            one_slot();
}

logo_depth = 0.6;
logo_size  = 1.8;   // tightened from 2.2 (49.1% of diameter) to target ~40%
                     // ratio for this string+font -- still verified below
                     // before treating it as final, not assumed correct
module brand_mark() {
    translate([0, -6, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

module base_body() {
    difference() {
        cylinder(r = base_r, h = base_h, $fn = 96);
        translate([0, 0, floor])
            cylinder(r = base_r - wall, h = base_h, $fn = 96);
        all_slots();
        brand_mark();
    }
}

// ---- Lid: a cup with 3 inward pins, shown in the LOCKED position ----
// (pins offset by lock_angle from each slot's entry, at world z =
// slot_bottom_z -- the exact height and angle where a pin sits once
// pushed down and twisted shut).

lid_skirt_r_in = base_r + 0.4;   // sliding clearance over the base's outer wall
lid_wall       = 2.4;
lid_skirt_h    = 20;
lid_cap_h      = 6;
lid_ski
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260909-005 -->
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

