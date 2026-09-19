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
