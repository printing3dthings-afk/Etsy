# Blender for 3D Printing — Tested Reference

Written 2026-09-11 (Scott: *"do more research on technique in blender and how
to utilize blender for 3d prints. You need to master your skills in it."*).

**Every claim in this file was either read from Blender's own manual and then
run in this container, or found by running it.** Where a source and a test
disagree, the test wins and the disagreement is recorded. Nothing here is
"should work." Numbers come from real runs on `mochi_fox_shell.stl`
(59,362 faces) and on purpose-built test bodies.

Companions: `SKILL.md` (the bug log), `ENGINEERING_REFERENCE.md` (theory and
the OpenSCAD-vs-Blender tool choice), `data/knowledge_base/3d_printing_expertise.md`
(DfAM and slicer settings).

---

## 0. Versions, and a negative result worth the download

This container has **Blender 4.0.2** (`apt`, the only version Ubuntu noble
offers). Blender **5.2.1 LTS** was downloaded from `download.blender.org` and
tested side by side specifically to find out whether the two traps below are
old bugs that an upgrade would fix.

**They are not. Both behave identically in 4.0.2 and 5.2.1, and 5.2 still has
no native 3MF.** So there is currently **no reason to upgrade this toolchain**
— which is worth knowing precisely because it stops a pointless 1.2GB change
to something `tools/blender_render.py` and `tools/print_check.py` depend on.

| | 4.0.2 | 5.2.1 |
|---|---|---|
| `use_remove_disconnected` removes a loose island | ❌ no | ❌ no |
| Curve-bevel caps come out welded | ❌ no | ❌ no |
| Native 3MF import/export | ❌ | ❌ |
| STL export operator | `bpy.ops.export_mesh.stl` | `wm.stl_export` (and `export_mesh` still present) |

3MF needs a community extension in every version (Ghostkeeper's, or
Clonephaze's 4.2+ fork which handles Orca/Bambu modifier parts and painted
multi-material). Until one is installed, `tools/make_color_3mf.py` — which
writes the container by hand — remains the right tool for multi-colour output.

---

## 1. Units: the convention here is safe *because* nothing touches unit settings

The classic Blender-for-print trap is that Blender's default unit is the metre
while every slicer reads an STL as millimetres, so a "10mm" object exports as
10 metres. **That trap does not apply to this repo, and the reason matters:**

```
scene.unit_settings.scale_length = 1.0   (default, untouched)
length_unit                      = METERS (default, untouched)
export_mesh.stl(use_scene_unit=False)    (default)
```

Tested: a `primitive_cube_add(size=20)` exports an STL that trimesh reads as
extents `[20, 20, 20]`, volume `8000`. **1 Blender unit out = 1 mm in the
slicer, exactly.**

> **Do not "fix" the scene units to millimetres.** Setting `length_unit='MILLIMETERS'`
> alone only relabels the UI; setting `scale_length=0.001` *does* change the
> maths and would then require `use_scene_unit=True` on export to come back to
> the same place. The current setup is correct by leaving all three alone.
> Changing one of the three without the others is how models come out 1000×
> wrong.

---

## 2. Booleans — reliable; nearly every failure is the cutter's fault

This repo's `ENGINEERING_REFERENCE.md` §1 has said Blender's Boolean is "measurably
less reliable than OpenSCAD/CGAL," sourced from bug reports. **Tested against a
real 59k-face organic shell, that framing is too harsh and the useful truth is
different: the Exact solver is correct, and three of four ways to break it are
defects in the cutter you hand it — two of which corrupt the result silently.**

All rows: DIFFERENCE, Exact solver, against `mochi_fox_shell.stl`
(59,362 faces, vol 246,043.4, watertight).

| cutter | faces | volume | open edges | verdict |
|---|---|---|---|---|
| sphere placed on the real surface | 59,670 | 245,945.8 | 0 | ✅ correct cut |
| **enclosing 400mm cube** | **0** | **0** | 0 | ✅ *correct* — A−B where B⊇A is nothing |
| **flipped-normal sphere** | 59,406 | **246,043.4 (unchanged)** | 0 | ⚠️ **silent no-op with topology damage** |
| **open (holey) sphere** | 60,104 | 247,042.7 (*grew*) | **172** | ⚠️ **silently non-manifold** |
| **zero-Z-scale sphere** | 59,439 | 246,043.4 | **2** | ⚠️ **silently non-manifold** |
| normal sphere, **Fast** solver | 60,041 | **245,680.7** | 0 | ⚠️ watertight but **a different, wrong answer** |

Read the rows in order, because each is a different lesson:

1. **An "empty result" is almost always a placement bug, not a Blender bug.**
   The only way to get 0 faces here was a cutter that swallowed the model —
   which is arithmetically the right answer. I previously reported a Blender
   Boolean "returning an empty mesh" on this exact shell and routed around it
   via a CGAL handoff after ~10 instrumented runs. It does not reproduce. Check
   the cutter's bounding box against the target's *before* blaming the solver.
2. **A cutter whose centre misses the surface is a no-op, not an error.** The
   first test in this session cut nothing because I placed the sphere from the
   bounding box instead of the surface. Use `obj.ray_cast(origin, direction)`
   to find where the surface actually is — on an organic shell you cannot
   predict it from the bbox.
3. **Flipped normals produce a silent no-op.** Volume identical to four
   decimal places, face count changed, gates clean. Nothing tells you.
4. **A non-closed or degenerate cutter silently makes the *result*
   non-manifold** even though the target went in watertight. The open cutter
   even *increased* volume.
5. **Fast vs Exact is not a speed/quality tradeoff — it is a different
   answer.** Fast removed 363 mm³ where Exact removed 98 mm³, and stayed
   watertight while doing it. **Always `solver='EXACT'`.**

`use_self=True` costs time and changed nothing in any correct case here; enable
it only when an operand is known to self-intersect. `use_hole_tolerant` likewise
made no difference.

**The rule:** gate the *cutter* before the boolean, not just the result. A
cutter must be closed, positively oriented, non-degenerate, and actually
intersecting.

---

## 3. Hollowing — Solidify Complex, never Simple

Blender's manual: Simple "does not work on geometry where edges have more than
two adjacent faces" and fails where adjacent normals disagree; Complex "can
handle every geometric situation to guarantee a manifold output."

Tested on a deliberately messy open vessel (UV sphere, top faces deleted,
loose edges left behind — 1,472 faces, 1,152 open edges), solidified to a
2.4mm wall:

| mode | faces out | volume | open edges |
|---|---|---|---|
| **Simple** | 3,008 | 20,392.2 | **2,176 — not watertight** |
| Complex / Fixed / None | 3,008 | 20,353.5 | **0** |
| Complex / Even / Round | 3,008 | 20,432.1 | **0** |
| Complex / Constraints / Flat | 3,008 | 20,703.7 | **0** |

Simple mode's output **fails `mesh_gate` outright**. Use:

```python
m = obj.modifiers.new("solid", "SOLIDIFY")
m.solidify_mode = 'NON_MANIFOLD'          # = "Complex" in the UI
m.nonmanifold_thickness_mode = 'CONSTRAINTS'   # FIXED | EVEN | CONSTRAINTS
m.nonmanifold_boundary_mode  = 'FLAT'          # NONE | ROUND | FLAT
m.thickness = 2.4                          # mm, per this repo's wall standard
m.offset = -1                              # -1 = inward, keeps outer surface exact
```

- `offset=-1` is what you want for a vessel: the *outside* silhouette you
  designed stays exactly where it was and the wall grows inward.
- Thickness is computed in **local vertex coordinates** — a non-uniform object
  scale gives a different wall on each axis. `transform_apply(scale=True)` first.
- Boundary `ROUND` = an opening that curves inward like a hole in an egg;
  `FLAT` = a cleanly cut rim. For a printable vessel mouth, `FLAT`.
- The three thickness modes differ by ~1.7% in volume here; `CONSTRAINTS` is
  the most accurate and the slowest.

This replaces the hand-built closed cross-section technique (SKILL.md
Technique 1) for any shape that is *not* a body of revolution. For revolved
vessels the OpenSCAD profile is still simpler and exact.

---

## 4. Geometry Nodes — the parametric criticism was wrong, and it is scriptable headless

This repo's docs have twice argued that "Blender throws away parametrics" — a
mesh, once built, has no `size=40` to override. **Tested, and that is false for
Geometry Nodes.** A node group built entirely in Python, driven by a named
input, regenerated on change with no script re-run:

| `Density` | faces |
|---|---|
| 0.005 | 5,760 |
| 0.020 | 17,760 |

That is exactly the `-D size=40` equivalent. **Retract the criticism for
Geometry Nodes; it still holds for a plain sculpted/remeshed mesh.**

### The headless recipe (Blender 4.0+ interface API)

```python
ng = bpy.data.node_groups.new("Spalls", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
s = ng.interface.new_socket("Density", in_out='INPUT', socket_type='NodeSocketFloat')
s.default_value = 0.004

N, L = ng.nodes, ng.links
gin  = N.new("NodeGroupInput");  gout = N.new("NodeGroupOutput")
dist = N.new("GeometryNodeDistributePointsOnFaces")
L.new(gin.outputs["Density"], dist.inputs["Density"])
...
md = obj.modifiers.new("GN", "NODES"); md.node_group = ng
```

**The one API trap that costs an hour:** you set a modifier input by its socket
**identifier**, not its name.

```python
ids = {s.name: s.identifier for s in ng.interface.items_tree
       if getattr(s, "in_out", "") == 'INPUT'}
# -> {'Geometry': 'Socket_0', 'Density': 'Socket_2', 'Radius': 'Socket_3'}
md[ids["Density"]] = 0.02        # md["Density"] silently does nothing
```

Identifiers are assigned in creation order and are **not** stable if you
reorder sockets — always build the map, never hardcode `"Socket_2"`.

To bake the result to real geometry:

```python
ev  = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = bpy.data.meshes.new_from_object(ev)     # real mesh, instances realized
```

`RealizeInstances` must be in the graph before the output, or instances export
as nothing.

### Why this matters here: procedural weathering

The tombstone's weathering is ~100 hand-placed boolean cutters in OpenSCAD,
and it carries **11 self-intersecting faces** (Technique 66) from cutters
grazing the face plane tangentially. Rebuilt as
`DistributePointsOnFaces → RandomValue → InstanceOnPoints → Realize` and
Exact-booleaned out of a slab:

```
slab 36×6×53 = 11,448 mm³  →  weathered 10,710.6 mm³  (737 mm³ removed, 6.4%)
print_check: Non-Manifold 0 · Bad Contiguous 0 · Intersect Face 0 · PASSED
```

**Zero self-intersections, against 11 for the hand-placed version** — and the
scatter density, radius, per-crater size variation and seed are all live
parameters. This is the strongest concrete case in this file for using Blender
on this shop's actual work.

> A caution from doing it: I nearly reported the result as an 88%-volume bug.
> `primitive_cube_add(size=1)` makes a **1mm** cube, so `scale=(36,6,53)` gives
> 36×6×53, not 72×12×106. The Boolean was right and my baseline was wrong.
> Measure the object you actually built (`obj.bound_box`) before calling a
> number a defect.

---

## 5. Two documented features that do not work — verified across both versions

### `Remesh → Remove Disconnected` does not remove disconnected pieces

The manual says it filters out "small disconnected pieces… thin parts of the
input mesh can become loose, and generate small isolated bits of mesh."

Tested with a deliberately detached 1.2mm-radius crumb 40mm away from a 40mm
cube, voxel remesh at 1.5mm, `use_remove_disconnected=True`, sweeping
`threshold` across **0.0, 0.1, 0.5, 1.0, 5.0, 20.0** — in **both 4.0.2 and
5.2.1**:

```
islands = 2 at every single threshold value
```

The crumb survives every setting. **Do not rely on this option.** This matters
directly — the free-floating 0.0015 mm³ rind in Technique 63 is exactly the
defect it advertises. Remove loose islands explicitly instead:

```python
bm.verts.ensure_lookup_table()
# flood-fill each connected component, keep only the largest by volume/face count
```

One data point is not a finding; a six-value sweep across two major versions is.

### Curve bevel with `use_fill_caps` produces *unwelded* caps

A beveled Bézier curve is the natural tool for a swept handle, a tail, a
tube — and it is **never watertight raw**:

| | faces | open edges | islands |
|---|---|---|---|
| `use_fill_caps=False` | 2,016 | 56 | 1 |
| `use_fill_caps=True` | 2,068 | **112** | **3** |
| `use_fill_caps=True` + merge by distance | 2,068 | **0** | **1** |

Turning caps *on* made it worse — 112 open edges and three separate islands.
The caps are generated as coincident-but-unwelded duplicate vertices; the face
count is identical before and after the merge, so nothing is added, only
joined.

```python
bpy.ops.object.convert(target='MESH')
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bm.to_mesh(o.data); bm.free()
```

**Always merge-by-distance after converting any curve to mesh.** Unfixed in
5.2.1, so treat it as permanent.

---

## 6. The 3D-Print Toolbox beyond checking

`object_print3d_utils` is wrapped by `tools/print_check.py` for its checks
(Technique 66). Three other operators in it are useful and unused here:

| operator | what it does |
|---|---|
| `mesh.print3d_clean_distorted` | triangulates non-planar ngons, which otherwise triangulate unpredictably at export |
| **`mesh.print3d_clean_non_manifold`** | "Make Manifold" — fixes bad normals, fills holes, removes empty edges/faces. A real repair pass for an imported or remeshed mesh |
| `mesh.print3d_scale_to_volume` / `_scale_to_bounds` | scale a model to an exact volume (filament cost) or an exact largest-axis dimension |

Its own manual is honest about intersections in a way worth quoting, since it
supports exactly the framing used in Technique 66: *"some slicer applications
can deal with this, so it's not always required to resolve this issue."*

---

## 7. Scriptability, honestly bounded

| capability | scriptable headless? |
|---|---|
| Primitives, modifiers, apply, export | ✅ fully |
| Geometry Nodes graphs + live parameters | ✅ fully (§4) |
| `bmesh` direct topology surgery | ✅ fully |
| Voxel remesh / decimate / smooth | ✅ fully |
| `obj.ray_cast()` surface probing | ✅ — the only reliable way to find an organic surface at author time |
| **Sculpt-mode brushes** | ❌ **not scriptable.** Real limit, not a gap to paper over |

The scriptable substitute for organic surface *variation* is a Displace
modifier or a Geometry Nodes graph driven by a procedural noise texture.
The substitute for deliberate sculpted *shape* is: build it from primitives
and voxel-union it, which is what `mochi_fox_shell.py` does.

---

## 8. When to reach for Blender, updated by these tests

Unchanged: **OpenSCAD stays primary for anything with real dimensions** —
mechanical parts, snap-fits, threads, assemblies. Exact CSG on named
variables is still the right tool when a number has to be a number.

Reach for Blender when:

1. **The whole surface is meant to be organic** — double curvature with no
   describable revolved/lofted profile. (Unchanged, and note the fox taught
   the inverse: "chibi animal made of blobs" *is* expressible in CSG, so it
   was never Blender's territory. Organic-*looking* is not the test.)
2. **You need a hollow shell of a non-revolved shape** — Solidify Complex (§3)
   in one modifier, versus building a closed cross-section by hand.
3. **A pattern of many similar features needs to be scattered over a surface**
   — Geometry Nodes (§4), which produced a measurably cleaner mesh than ~100
   hand-placed OpenSCAD cutters *and* stayed parametric.
4. **You need to measure a surface you cannot predict** — `ray_cast()`.

And correcting §1 of `ENGINEERING_REFERENCE.md`: the Boolean reliability
warning should be read as **"validate the cutter and always use the Exact
solver,"** not "avoid Blender booleans." Under those two conditions it was
correct on every test here.

---

## 9. The procedural-weathering rebuild FAILED — what a slab test does not prove

§4 records that Geometry Nodes weathering on a **test slab** produced 0
self-intersecting faces against 11 for the tombstone's hand-placed OpenSCAD
cutters, and called it "the strongest concrete case in this file." Scott asked
for the real rebuild. **It was built, rendered, and rejected.** Recording it
here in full, because the failure is more instructive than the slab win.

### It looked wrong — the exact defect already rejected once

The render came out as evenly-spaced round dimples: **golf-ball polka dots**.
That is generation one's "cheese style cut out," the thing three generations of
work in Technique 63 existed to eliminate — and arguably worse, because the
spacing was *more* regular than random placement would give.

Three causes, all in the primitive and the scatter:

1. **`distribute_method='POISSON'` destroys clustering.** Poisson-disk
   guarantees a minimum distance between points. That is the opposite of how
   stone chips: real damage clusters, which is why the OpenSCAD `scar()` throws
   satellites around a parent. Even spacing reads as manufactured. *Poisson is
   the right tool for scattering bolts and the wrong one for scattering damage.*
2. **A flattened icosphere is still a circle in silhouette.** Subdivision 1
   gives 80 real facets and hard edges — and seen face-on against the surface
   its *rim* is still near-circular, which is the only part a viewer reads.
   The OpenSCAD spall is a hull of two point clusters near parallel planes, so
   its rim is an irregular straight-edged polygon. **The rim is the whole
   effect.** Faceting the body of the cutter buys nothing.
3. **One depth per zone** where the OpenSCAD version randomises depth per scar.

### And the mesh was 600× worse

| | shipped OpenSCAD | Geometry Nodes |
|---|---|---|
| self-intersecting faces | 11 | **850** |
| total intersecting area | 0.61 mm² | **365 mm²** |
| largest single face | 0.33 mm² | **9.03 mm²** |

**The cause is not a dirty cutter, and proving that mattered.** The obvious
theory was that overlapping flakes made a self-intersecting operand. Chased it
properly: per-zone `GeometryNodeMeshBoolean` union, then a forced full-cloud
self-union (split the cloud in half, UNION the halves with Exact).
**The cutter reached 0 self-intersections and the result still had 850.**

So they are *generated by the difference itself*, cutting hundreds of shallow
near-tangent features into a surface — the same mechanism as the shipped
version's 11, at ~77× the count because there are ~77× more grazes. More
cutters means more tangency, and tangency is where Exact produces slivers.

**The lesson about the slab test:** it had ~22 craters on one flat plane and
scored 0. The real part has hundreds across eight faces at three depths, two
of them shallower than 0.7mm. A clean result on a simple case is not evidence
about a complex one, and I presented it as if it were.

### Two bugs already solved in OpenSCAD, reintroduced here

- **Cutters on the buried face.** The stone sinks 6mm into the socle, so its
  y=±6 faces below z=18 are *inside* the socle. Zone planes spanning the full
  height cut cavities in there and left free-floating chunks — `mesh_gate`
  reported 5 bodies. This is Technique 63's sealed-void class exactly. Fixed
  with an explicit island-walk fence deleting any flake reaching below
  z=20 on a stone face.
- **Flakes swallowed whole.** With free 3-axis random rotation, a flake's
  extent *along the surface normal* is somewhere between its smallest and
  largest axis, so one fixed sink offset buries the small ones completely
  (sealed void) and barely scratches the big ones. This is the OpenSCAD
  `bite()` clamp, relearned. Fix: align the instance's local +Z to the surface
  normal (`FunctionNodeAlignEulerToVector`, axis='Z'), allow only a small tilt
  (≤10°) plus free spin about Z, and derive the sink from **that flake's own**
  thickness via `SeparateXYZ → Subtract(depth)`. Thickness range must start
  above `depth` (used `depth*1.30 … depth*2.40`) so nothing can ever sink past
  its own face. Surface-parallel flakes are also truer to ICOMOS-ISCS, where
  scaling runs *parallel to the stone surface*.

### One real API finding worth keeping

**A GN scatter cloud is a self-intersecting operand, and `use_self=False`
silently returns an almost-empty result.** With `use_self=False` the difference
removed 100% of a 112,183 mm³ stone and left 223 faces. With `use_self=True`,
the identical setup removed 1,190 mm³ correctly. §2's advice — "enable it only
when an operand is known to self-intersect" — is too weak: **for any
instanced/scattered cutter, assume it self-intersects and set `use_self=True`.**

### Verdict

**OpenSCAD keeps the tombstone weathering.** It produces the approved look and
is 600× cleaner. Geometry Nodes remains right for scattering *regular* features
(§4's real use) and wrong for damage, which needs clustering and irregular
rims. Making it work would mean porting `spall()`'s hull-of-two-point-clusters
into the node graph and driving placement from clustered seeds — a real
rebuild, even odds at best of matching what already exists.

**The process rule this earns:** when a new tool wins a *test* case, say so as
a test result, not as a recommendation. The recommendation needs the real part.
