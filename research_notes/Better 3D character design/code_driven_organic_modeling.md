# Code-Driven Organic Modeling for 3D Printing (OpenSCAD/BOSL2 + headless Blender + SDF)

Research date 2026-11-03. Scope: procedural ways to get smooth organic forms (characters, animals, cherubs, figurines) from code in a headless Linux container, for commercial sale.

**About the sources.** Two kinds of evidence appear below:
- **Web sources**, cited with a URL.
- **Local runs in this container**, marked *"measured locally"*. These used Blender 4.0.2, OpenSCAD 2021.01 with the vendored BOSL2 2.0.751, manifold3d 3.5.4, trimesh 5.2.0, shapely 2.2.0, and scikit-image (installed into a scratch target only, not the repo). The code needed to reproduce each run is quoted inline, because the scratchpad copies will not survive the container.

**Network caveat.** iquilezles.org returned HTTP 404 for every article URL, including its root, during this session. A 301 redirect pointed to `/articles/smin/`, which itself returned 404. IQ's own formula pages could therefore not be read directly. The polynomial smin below is confirmed from two independent secondary write-ups that re-derive it. Every other IQ formula is marked as recalled and needs checking against the live article before anyone relies on it.

---

## 1. SDFs and smooth unions: smin variants, primitives, SDF character modeling, and meshing for print

### Takeaway
An SDF character is built from a few primitives (ellipsoids, spheres, capsules and "sticks" whose radius varies along their length), blended with a polynomial smooth-min whose `k` is the fillet width in mm. Turning it into a printable mesh is the easy part. Marching cubes at a 0.15–0.25 mm voxel size gives watertight, print-smooth meshes in seconds, as long as no grid sample falls exactly on the zero level. `manifold3d.Manifold.level_set`, which is already installed in this repo, is a guaranteed-manifold alternative.

### Cited Findings
**smin, the core operator**
- **Polynomial (quadratic) smin.** The code is `h = clamp(0.5 + 0.5*(a-b)/k, 0, 1); return mix(a, b, h) - k*h*(1-h);`.
  - It is C¹, and the blend only acts where |a−b| < k.
  - It approximates min well for small k (0.01) but is "incorrect" for large k (0.8). — [vgracianos, smin](https://vgracianos.github.io/blog/smin)
- **Independent re-derivation of the same smin.** The second write-up concludes the result "is exactly iq's function".
  - k is the half-width of the closeness interval [−k, k].
  - At a == b the result is (a+b)/2 − k/4, i.e. **k/4 below the hard min**. This undercut is what produces the fillet "web", and it also slightly fattens the blend region.
  - The original article it cites is https://www.iquilezles.org/www/articles/smin/smin.htm. — [Stranathan, Polynomial smin](https://ianstranathan.github.io/html/Graphics/polynomial-smin)
- **Families, continuity and order dependence.** IQ's article describes exponential, polynomial (quadratic, cubic) and root variants.
  - The exponential form is order-independent, which suits folding long lists of distances.
  - The polynomial forms give results that depend on the order in which values are combined.
  - The cubic is C² at about the cost of the quadratic.
  - The code multiplies k by a per-variant constant (normalization).
  - A variant also returns a blend factor, used for material and colour mixing.
  - Source: [IQ smin article](https://iquilezles.org/articles/smin) (secondary summary via search; the page was unreachable this session).
- **glslify/glsl-smooth-min (MIT)** packages poly, pow and exp variants. It calls poly "probably the fastest, and also the easiest to control" and says k "maps directly to a blending band size/distance". It notes that poly "probably suffers from second order discontinuities". — [glsl-smooth-min](https://github.com/glslify/glsl-smooth-min)
- **min, max and sums.** Taking min/max of SDFs gives a valid union/intersection SDF; adding SDFs does not. — [HN discussion](https://hn.jakechampion.name/item/46380054) (via search snippet)

**SDF character modeling ("Happy Jumping", IQ 2019)**
- The shader header describes "a happy and blobby creature jumping and looking around" and links a 6-hour making-of video.
- Its primitives are an *approximate* `sdEllipsoid` and a "stick" (a capsule between two points with interpolated radii), combined with smin/smax.
- The shader's own comment admits the character goes "off-model very often" but "looks good enough".
- **License warning.** The header says the code "can't be used, shared, or hosted as part of a commercial or non-commercial product without permission". Do not copy that shader's code into a product pipeline. Reimplementing the standard math (smin, capsule distance) is a different matter.
- Sources: [port of the shader, rt_glsl_puppy.glsl](https://git.rustybever.be/vieter-v/v/raw/commit/04c4f16f75b7a6eb20fcd888d05eeec50cc0dcae/examples/sokol/04_multi_shader_glsl/rt_glsl_puppy.glsl) (seen via search snippet; the fetch returned 503); Shadertoy page https://www.shadertoy.com/view/3lsSzf (not fetched).
- A node-based recreation exists: [iklsr/sdfsandbox](https://awesome.ecosyste.ms/projects/github.com%2Fiklsr%2Fsdfsandbox).

**SDF tools and licenses**
- **fogleman/sdf (MIT, Python).**
  - Meshes with marching cubes via scikit-image, evaluating the SDF in numpy batches across worker threads.
  - Resolution is set by `step=` (voxel size, can be per-axis) or `samples=` (default `2**22`). `batch_size` defaults to `32**3`.
  - "Sparse" sampling skips batches far from the surface.
  - Primitives include `sphere, capsule, rounded_cone, ellipsoid, rounded_box, torus, capped_cone, rounded_cylinder`, plus 2D shapes and extrusions.
  - Smooth booleans are written `a | b.k(0.25)` or `union(a, b, k=0.25)`, and likewise for `-` and `&`.
  - It writes binary STL natively and other formats via meshio.
  - **Gotcha:** non-uniform scaling gives an inexact SDF that "can cause bounds estimation problems, and sparse sampling can leave holes". Set bounds manually or pass `sparse=False`.
  - It is not on PyPI under that name: install with `pip install -e .` from a clone. Mesh-as-SDF needs OpenVDB.
  - Source: [fogleman/sdf](https://github.com/fogleman/sdf)
- **libfive.** The kernel and core libraries are **MPL** ("commercially friendly"); Studio (the GUI) is **GPL**. It has Scheme and Python bindings and supports headless use ("run it as a service"). Its homepage does not name the meshing algorithm. — [libfive.com](https://libfive.com/)
- **Curv (Apache-2.0).**
  - Exports STL/OBJ/X3D that it claims are "watertight, manifold, with no self intersections".
  - It can run headless from the command line, though image export may need a dummy X server.
  - The `-Ojit` export path needs a C++ compiler and glm.
  - The GitHub repo was **archived 2023-09-27** and the project moved to Codeberg.
  - Source: [curv3d/curv](https://github.com/curv3d/curv)
- **manifold3d (installed here, 3.5.4).** Per its own docstring (`help(manifold3d.Manifold.level_set)`, checked locally):
  - Signature: `Manifold.level_set(f(x,y,z)->float, bounds=[xmin,ymin,zmin,xmax,ymax,zmax], edgeLength, level=0.0, tolerance=-1)`.
  - It uses "a form of Marching Tetrahedra … better for manifoldness" on a body-centred cubic grid.
  - **Positive values are inside**, which is the opposite of the usual SDF convention.
  - The function need not be a true distance, or even continuous.
  - `level` insets or outsets the surface.
  - It also exposes `smooth`, `smooth_by_normals`, `smooth_out`, `refine`, `refine_to_length` and `refine_to_tolerance`.
  - Project repo: [elalish/manifold](https://github.com/elalish/manifold).

**Measured locally: chibi SDF meshed with skimage marching cubes**
- **Test model:** body sphere r=9, head sphere r=7.5 with smin k=4, capsule arms r=2.5 with k=2.5, ear spheres with k=1.5, and a flat base cut with `max(d, -z)`. About 32×24×33 mm.

  | voxel step | faces | time | volume (mm³) |
  |---|---|---|---|
  | 1.0 mm | 5.1k | ~0 s | 5152 |
  | 0.5 mm | 20.6k | 0.1 s | 5178 |
  | 0.25 mm | 82k | 1.6 s | 5185 |
  | 0.15 mm | 229k | 9.5 s | 5186 |

  - Volume converges by about 0.25 mm, which is roughly half a 0.4 mm nozzle line and finer than a 0.2 mm layer.
- **Gotcha found: exact-zero samples break watertightness.** At 1.0/0.5/0.25 mm steps the mesh was **not watertight**, because the z=0 cut plane fell exactly on grid samples and produced degenerate triangles that were then removed.
  - Nudging zero samples (`D[abs(D)<1e-9] = 1e-6`) made every resolution watertight (1.0 mm: 5,104 faces; 0.5 mm: 20,344 faces).
  - Offsetting the grid origin by half a voxel would also work.
- **manifold3d `level_set` on the same model, with a per-point Python callback:**
  - edge 1.0 mm: 9.9k tris, watertight, 5172 mm³, 5.0 s.
  - edge 0.5 mm: 36.7k tris, watertight, 5183 mm³, 37 s.
  - It is always manifold, but the scalar Python callback is about 300× slower than vectorized numpy plus skimage.

### Inferences
- **Recalled, unverified constants.** IQ's article (recalled from training data; the site was unreachable this session) normalizes k so that k equals the blend width for each variant:
  - quadratic: `k *= 4.0; h = max(k-abs(a-b),0)/k; return min(a,b) - h*h*k*(1/4)`
  - cubic: `k *= 6.0; … - h*h*h*k*(1/6)`
  - exponential: `k *= 1.0; r = exp2(-a/k) + exp2(-b/k); return -k*log2(r)`
  - It also has "circular" and "root" variants, and recommends the quadratic/cubic for speed.
- **Which smin for figurines.** Use the cubic (C²) polynomial for character joints. A C¹ blend can show a faint highlight crease on glossy silk PLA, while C² gives continuous reflections.
- **Choosing k.** Use the exponential (order-independent) form when folding many parts, e.g. 20 fingers or toes, to avoid ordering artefacts. A sensible k for a 30–60 mm figurine is 1.5–5 mm at the neck and limbs and 0.8–1.5 mm for ears and features. Below about 0.6 mm (1.5 nozzle widths) a fillet is unlikely to print as a visible curve.
- **sdRoundCone and sdEllipsoid (recalled from IQ's distfunctions article).**
  - `sdRoundCone(p, r1, r2, h)` is exact: a cone capped by spheres of different radii, which makes it the natural "limb that tapers" primitive.
  - IQ's `sdEllipsoid` is a *bound*, not exact (`k0 = length(p/r); k1 = length(p/(r*r)); return k0*(k0-1)/k1`).
  - That inexactness matters for smin, because the blend width becomes anisotropic near the long axis. It also matters for fogleman's sparse sampling, which can leave holes, as fogleman's own warning implies.
  - Practical fix: mesh with `sparse=False`, or use exact sphere/capsule/round-cone shapes non-uniformly scaled only slightly.
- **Choosing the mesher.** For print work, plain marching cubes at 0.2 mm, plus a quick trimesh watertight check, is enough. Dual contouring (as in libfive) mainly preserves *sharp* features, which organic figurines do not need, so it buys little here.

### Gaps
- IQ's live smin and distfunctions pages could not be retrieved (404 on every URL), so exact normalization constants, sdRoundCone code and sdEllipsoid code are unverified this session.
- Licensing of the code snippets on IQ's *articles* (as opposed to the Happy Jumping shader) was not confirmed. The safe route is to implement the math independently.
- No benchmark of libfive or Curv mesh quality was run; neither is installed.

---

## 2. Metaballs and implicit surfaces in Blender via Python

### Takeaway
Blender metaballs script and mesh cleanly in headless mode. They produce watertight output, but they are a weaker modeling tool than SDF smin:
- an element's `radius` is not its surface radius;
- blending is controlled indirectly through the global `threshold`;
- elements that are too far apart silently become separate bodies.

### Cited Findings
- **Measured locally (Blender 4.0.2, `blender -b --factory-startup --python`).**
  - Test: three ball elements of radius 6/5/6 at 8 mm and 7 mm spacing, `resolution=0.3`, `threshold=0.6`.
  - Converting with `bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))` gave 6,632 verts, a watertight mesh, consistent winding and 450 mm³.
  - **The result was 2 separate bodies**, and each lobe was only about 3.4 mm in radius against the requested 5–6.
  - Element radius is a field-influence radius, so the visible surface sits well inside it and depends on `threshold`.
- **The skin vertex API is similar in spirit.** Per-vertex `radius` is a 2-float (X, Y) array alongside `use_root` and `use_loose`. — [Blender API: MeshSkinVertex](https://docs.blender.org/api/blender_python_api_2_74_5/bpy.types.MeshSkinVertex.html)

### Inferences
- **Recipe if metaballs are used anyway:**
  - Calibrate once by measuring the meshed extent per element radius at your chosen threshold, then size elements from that calibration.
  - Use capsule and ellipsoid elements for limbs.
  - Use negative elements to carve the mouth or eye sockets.
  - Set `render_resolution` to about 0.2–0.3 mm.
  - Always check `body_count == 1` after meshing.
- **Metaballs versus a numpy SDF.** Metaballs offer nothing over a numpy SDF except interactivity in the GUI, which is irrelevant headless. A numpy or fogleman SDF gives exact control of radius and blend width.

### Gaps
- The Blender manual pages for Metaball Properties and the Skin Modifier did not render through the fetch tool (navigation only, 200k+ chars), so official wording on threshold, stiffness and element types is not quoted here.

---

## 3. OpenSCAD/BOSL2 techniques for organic shapes, including 2D silhouettes

### Takeaway
CSG cannot blend 3D solids smoothly: `union()` always leaves a crease, `minkowski()` and `hull()` only round convex shapes, and nothing in CSG fillets a concave join. For **2D silhouettes**, OpenSCAD can produce excellent results in two ways:
- **Morphological closing** `offset(r=-R) offset(r=R)` fillets every concave crease of a union of circles, though only to G1 (a circular arc).
- **BOSL2 `smooth_path` / `round_corners(method="smooth")`** gives curvature-continuous (G2) outlines from a few control points.

For 3D, BOSL2 `skin()`, `path_sweep()`, `offset_sweep()`, `rounded_prism()`, `vnf_vertex_array()` and `bezier_vnf()` cover lofts, swept limbs and computed surfaces. True organic blends still need an SDF, which can be imported as an STL.

### Cited Findings
- **BOSL2 license and version.** BOSL2 is BSD-2-Clause, so it is safe for commercial output (local `assets/openscad_libs/BOSL2/LICENSE`); the vendored version is `[2,0,751]`. — [BOSL2 repo](https://github.com/BelfrySCAD/BOSL2)
- **Rounding functions** ([rounding.scad](https://github.com/BelfrySCAD/BOSL2/blob/master/rounding.scad), signatures read from the local copy):
  - `round_corners(path, method="circle"|"smooth"|"chamfer", radius|cut|joint|width, k, closed)`.
  - "We compute continuous curvature rounding using 4th order Bezier curves", which BOSL2 calls "smooth" rounding.
  - `k` (default 0.5) sets how gradual the flat-to-round transition is; the docs mention a gentler `k=0.3`.
  - For smooth rounding "be sure to use lots of segments".
- **`smooth_path`** has signature `smooth_path(path, tangents, size, relsize, method="edges"|"corners", splinesteps=10, uniform, closed)`. It interpolates a closed spline through a handful of points. — local `rounding.scad` line 600–743, same GitHub file
- **Other BOSL2 tools, signatures from local source:**
  - `offset_sweep(path, height, top=os_smooth(...), bottom=...)` extrudes a 2D outline with rounded or "smooth" top and bottom edges. This is the ideal way to give a charm a pillowy, domed edge.
  - `rounded_prism(bottom, top, joint_bot, joint_top, joint_sides, k=0.5, splinesteps=16)`.
  - `join_prism()` builds a filleted junction of a prism onto a base. It is the only true *concave fillet between solids* in BOSL2, and it is limited to prisms.
  - `skin(profiles, slices, method="direct"|"reindex"|"distance"|"tangent"|..., caps)` lofts between cross-sections, e.g. a torso from stacked ellipses.
  - `path_sweep(shape, path, twist, scale)` sweeps a profile along a curve, e.g. a tapering tail or limb.
  - `bezpath_curve(bezpath, splinesteps, N=3)` and `bezier_curve()`.
  - `bezier_vnf(patches)` builds surfaces from Bezier patches.
  - `vnf_vertex_array(points, ...)` turns a computed (u,v) grid of points into a polyhedron, which is how to build a parametric body surface.
  - Sources: [skin.scad](https://github.com/BelfrySCAD/BOSL2/blob/master/skin.scad), [beziers.scad](https://github.com/BelfrySCAD/BOSL2/blob/master/beziers.scad), [vnf.scad](https://github.com/BelfrySCAD/BOSL2/blob/master/vnf.scad)
- **Measured locally: cat-head silhouette** (head circle r=15, two ear circles r=6, chin circle r=8), 2D, with `$fa=2; $fs=0.2`, exported to SVG and analysed with a discrete turning angle and curvature (the angle change between consecutive edges divided by the mean edge length).

  | outline | max turn at one vertex | max curvature | max curvature jump between neighbours |
  |---|---|---|---|
  | raw `union()` | 80.2° | 48 /mm (6 crease vertices >20°) | — |
  | closing `offset(r=-3) offset(r=3)` | 3.8° | 0.44 /mm | 0.73 /mm |
  | BOSL2 `smooth_path(..., closed=true, method="corners", size=2, splinesteps=16)` (10 control points) | 5.1° | 0.31 /mm | 0.15 /mm |

  - Closing scored IoU 0.997 against the raw union, with a Hausdorff distance of 0.59 mm. The silhouette is unchanged except at the creases.
  - The smooth_path's curvature jump is about 5× lower than the closing's. That is the G2-versus-G1 difference, measured.
- **OpenSCAD docs.** `offset(r=...)` rounds; `offset(delta=...)` keeps sharp corners. The "fillet" idiom is a negative offset applied around a positive one. — [OpenSCAD manual, Transformations / offset](https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Transformations#offset) (standard documented idiom; page not re-fetched this session)

### Inferences
- **The 2D silhouette recipe for charms (best quality per effort):**
  1. Block the shape out from circles and ellipses.
  2. Apply `offset(r=-Rc) offset(r=+Rc)` to fillet the concave creases, then `offset(r=+Ro) offset(r=-Ro)` (opening) to soften any sharp convex points such as ear tips. Choose Rc ≥ 1.5–3 mm and Ro ≥ the nozzle width.
  3. For hero shapes, retrace the final outline with `smooth_path` or Bezier control points to get G2.
  4. Extrude with `offset_sweep(..., top=os_smooth(joint=...))` for a domed, pillowy edge.
  - Nested offsets are cheap in 2D, unlike 3D `minkowski()`.
- **The limits of 3D CSG for organics.** `hull()` chains of spheres give convex-only "sausage" limbs. `minkowski()` with a sphere rounds every convex edge but cannot fillet concave joins and is very slow. A `union()` of ellipsoids always creases at the neck and armpits. That crease is exactly the "lumps where shapes are unioned" problem, and no 3D offset exists in OpenSCAD 2021 to fix it.
- **A workaround in 3D:** build each body part as a `skin()` loft or `vnf_vertex_array` surface whose cross-sections already merge (one continuous torso-to-head loft), instead of unioning separate solids.
- **When to leave OpenSCAD.** Do the organic core as an SDF in Python, export STL, then `import()` it into OpenSCAD only for the mechanical additions: flat base, peg holes, maker's mark, keyring loop. CGAL booleans on a 200k-triangle import are slow; manifold3d (Python) or a newer OpenSCAD with the Manifold backend is much faster.

### Gaps
- No published maker or CAD blog benchmarking organic modeling in OpenSCAD was retrieved within the tool budget.
- The installed OpenSCAD is 2021.01, which predates the Manifold backend; newer-build performance on large imports was not measured.

---

## 4. Blender headless Python: skin modifier, subsurf, remesh, smoothing, and STL export

### Takeaway
A vertex skeleton with per-vertex skin radii, followed by Subdivision Surface, Voxel Remesh and Smooth, is a fast, fully scriptable "ZSphere-style" path to chubby figurines. It produced a watertight single-body mesh in under a second here. The catch: final dimensions come out **smaller than the radii you set**, and cross-sections are not round, so calibrate.

### Cited Findings
- **Measured locally (Blender 4.0.2, headless).**
  - Skeleton: a vertical chain at z=0/8/16/24 with radii 6/9/5/8, plus two arm verts with radius 2.5.
  - Modifiers: Skin, then Subsurf level 2, then Remesh VOXEL 0.4 mm, then Smooth ×5. Applied with `bpy.ops.object.modifier_apply`.
  - Result: 15,340 faces, **watertight, consistent winding, 1 body**, 2124 mm³. Total script time 0.6 s, including the metaball test.
  - **Size gotcha:** with a max radius of 9 on the body vertex, the mesh measured only ±7.5 mm in X and **±5.6 mm in Y**, and z spanned 1.2–23.3 against vertices at 0–24. The skin's box cross-section shrinks under subsurf, and the shrink is anisotropic, so radius ≠ final size.
- **Skin radii are set per vertex** via `obj.data.skin_vertices[0].data[i].radius = (rx, ry)`, plus `.use_root = True` on one vertex per connected tree. (API: `radius` float[2], `use_root`, `use_loose`.) — [MeshSkinVertex](https://docs.blender.org/api/blender_python_api_2_74_5/bpy.types.MeshSkinVertex.html)
- **Radii live only in the skin layer.** "If the modifier is deleted, the skinning radii will be lost" (Skin Resize, Ctrl-A). — [Blender manual: Skin Resize](https://docs.blender.org/manual/en/dev/modeling/meshes/editing/mesh/transform/skin_resize.html)
- **Measured locally: STL export operators.** In Blender 4.0.2 both `bpy.ops.export_mesh.stl(filepath, use_selection=True)` (legacy add-on) and `bpy.ops.wm.stl_export(filepath, export_selected_objects=True)` (new C++ exporter) exist.
- **Headless invocation that worked:** `blender -b --factory-startup -noaudio --python script.py`. Start the script with `bpy.ops.wm.read_factory_settings(use_empty=True)` to remove the default cube.
  - To read modifier results without applying them: `ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()`.

### Inferences
- **Pitfalls in headless mode:**
  - `bpy.ops` operators need a valid active and selected object; set `view_layer.objects.active` and `select_set(True)` before `modifier_apply`.
  - Prefer data-API equivalents (depsgraph `to_mesh` / `meshes.new_from_object`) over operators where possible; they do not depend on context.
  - Sculpt-mode brush operators via `bpy.ops.sculpt.*` need a 3D-viewport context override and are fragile in background mode. Scripted "sculpting" is better done as vertex displacement in numpy on `mesh.vertices.foreach_get/foreach_set`, or with Displace and Smooth modifiers driven by procedural textures.
- **Scripted pipeline for figurines:**
  - For a stylized silhouette: skin skeleton, then Subsurf 2, then Voxel Remesh at 0.3–0.5 mm (this fuses limbs into one manifold shell and removes skin-modifier self-intersections at branches), then Smooth or Corrective Smooth, then optionally Subsurf again.
  - Booleans for a flat base, holes and the mark: use the Boolean modifier with the EXACT solver *after* remesh.
  - Export, then verify with trimesh (`is_watertight`, `body_count == 1`).
- **Version caveat.** The legacy `export_mesh.stl` operator was reportedly removed in Blender 4.2, with `wm.stl_export` as the replacement. This is from memory and unverified here. Write scripts against `wm.stl_export` with a fallback.
- **Geometry Nodes** offers "Mesh to Volume" / "Volume to Mesh", which does SDF-like blending of mesh parts inside Blender, and Points to Volume for metaball-like blobs. Not tested here.
- **Licensing.** Blender and OpenSCAD are GPL applications. The general understanding is that their *output* (meshes, STLs) is not GPL-covered. That should be confirmed from Blender's own licensing FAQ (not fetched).

### Gaps
- Official Skin and Remesh modifier manual text could not be extracted (the fetch returned navigation only).
- Geometry Nodes volume blending and the Blender 4.2+ exporter change were not verified.
- No authoritative Blender StackExchange answer on headless sculpt overrides was retrieved.

---

## 5. Measuring and validating smoothness and appeal programmatically

### Takeaway
Smoothness is measurable cheaply.
- **In 2D:** discrete turning angle per vertex and the curvature jump between neighbouring vertices (the G1-versus-G2 signal).
- **In 3D:** dihedral-angle statistics plus watertight/body-count checks.

Fidelity to a reference silhouette is measured with IoU and Hausdorff distance via shapely, both of which are installed. "Appeal" has no validated metric; balance proxies such as area distribution and head-to-body ratio are only heuristics.

### Cited Findings
- **Measured locally (shapely 2.2.0).**
  - The 2D numbers in section 3: max turn/vertex, max curvature and max curvature jump separated a creased union (80°, 48/mm) from a G1 closing (3.8°, jump 0.73/mm) and a G2 spline (5.1°, jump 0.15/mm).
  - `Polygon.intersection().area / union().area` and `exterior.hausdorff_distance()` ran in milliseconds. Closing against raw gave IoU 0.997 and Hausdorff 0.59 mm. A hand-placed 10-point spline against raw gave IoU 0.831 and Hausdorff 7.96 mm, which correctly flags that hand-tracing drifted from the blocked-out reference.
- **Existing house rule.** The repo's own 3d-print-design skill already sets a 3D smooth-organic target: **mean dihedral < 4°, p95 < 9°, hard edges < 1.5%**, plus `$fa = 2; $fs = 0.4;` for organic models. — local `.claude/skills/3d-print-design/SKILL.md` (lines ~4011–4190)
- **Mesh validity checks used here:** trimesh `is_watertight`, `is_winding_consistent`, `body_count` and `volume`. Volume convergence across voxel sizes (5152 → 5186 mm³) is a practical way to pick the meshing resolution. — [trimesh](https://github.com/mikedh/trimesh) (MIT, from pip metadata)

### Inferences
- **Suggested 2D gates for charms:**
  - max turn per vertex < 10° at `$fs=0.2`, which catches creases;
  - curvature jump < ~0.3/mm, which catches G1 kinks visible as highlight breaks;
  - minimum convex radius ≥ nozzle/2 and minimum concave radius ≥ 1 nozzle width (from 1/curvature), so features actually print;
  - IoU ≥ 0.97 and Hausdorff ≤ 0.5 mm against the approved reference outline, so a smoothing pass has not drifted.
- **Turning-function distance** (Arkin et al., 1991) is the standard rotation- and scale-invariant 2D shape comparison and is a good "same character?" check between versions. It was not implemented here.
- **Appeal proxies for chibi forms**, all heuristics with no validation source found:
  - head-to-body height ratio of about 1:1 to 1:2;
  - silhouette centroid low (stable, "chubby");
  - an outline that has no parallel straight runs (rhythm);
  - ears and limbs readable as separate lobes at thumbnail size, e.g. the silhouette eroded by 1 mm still shows the lobes. That last idea ties to this shop's "silhouette reads at thumbnail size" bar.

### Gaps
- No peer-reviewed or industry metric for character "appeal" was found.
- The turning-function source was not fetched (cited from general knowledge).
- The repo's existing rejected silhouette metric (skill Technique 68) was not reviewed in detail.

---

## 6. Recommendation: which approach for (a) flat charms, (b) chubby stylized figurines, (c) semi-realistic figures

### Takeaway
- **(a) Flat charms:** stay in OpenSCAD/BOSL2 2D. Block out with circles, apply closing and opening offsets, retrace in G2 with `smooth_path`, then `offset_sweep` with a smooth top.
- **(b) Chubby figurines:** use a numpy (or fogleman/sdf) SDF with cubic or quadratic smin, meshed by skimage marching cubes at 0.2–0.25 mm. The Blender skin-modifier pipeline is the faster-to-pose alternative.
- **(c) Semi-realistic figures:** neither method is quality-per-effort competitive with hand sculpting. Scripted Blender (skin base, voxel remesh, procedural displacement) gets a base; real realism needs human sculpting or licensed or AI-generated meshes, which are outside this scope.

### Cited Findings
- 2D closing and smooth_path give crease-free, G1/G2 outlines with negligible fidelity loss (IoU 0.997). *Measured locally, section 3.* BOSL2 is BSD-2. — [BOSL2](https://github.com/BelfrySCAD/BOSL2)
- An SDF chibi meshes watertight at 0.25 mm in 1.6 s once zero-samples are nudged. *Measured locally, section 1.*
  - fogleman/sdf is MIT. — [fogleman/sdf](https://github.com/fogleman/sdf)
  - libfive's kernel is MPL (the GUI is GPL). — [libfive](https://libfive.com/)
  - Curv is Apache-2.0 but archived. — [Curv](https://github.com/curv3d/curv)
- The Blender skin pipeline meshes watertight in under a second, but its dimensions shrink anisotropically (±7.5 × ±5.6 mm from a radius of 9). *Measured locally, section 4.*
- IQ's own SDF character "gets off-model very often". Pure SDF primitive modeling trades precise control for blobby charm. It also has a no-commercial-use code license, so do not reuse its code. — [shader port header](https://git.rustybever.be/vieter-v/v/raw/commit/04c4f16f75b7a6eb20fcd888d05eeec50cc0dcae/examples/sokol/04_multi_shader_glsl/rt_glsl_puppy.glsl) (via search snippet)

### Inferences
- **Quality-per-effort ranking:**
  - **(a) Charms:** OpenSCAD 2D, then SDF-2D extruded, then Blender. Charms are judged entirely by outline smoothness and edge profile, which OpenSCAD 2D plus `offset_sweep` already does best.
  - **(b) Chubby figurines:** SDF in Python is best.
    - Exact control of every radius and blend width in mm.
    - Vectorized numpy; no extra dependency beyond scikit-image, or manifold3d `level_set` already installed.
    - Every license permissive (numpy BSD, skimage BSD, manifold Apache-2.0 *believed, not verified this session*).
    - Recipe: ellipsoid and round-cone body parts, cubic smin with k of 2–5 mm at the neck and limbs, a `max(d, -z+eps)` flat base, eyes and mouth as `smax` carve-outs (smooth subtraction) of at least 0.8 mm depth, an embossed mark added afterwards in OpenSCAD on a flat face, then the existing printability gates.
    - The Blender skin pipeline is second-best: better for posing from a "stick figure", worse for precise radii.
  - **(c) Semi-realistic figures:** procedural code hits diminishing returns. The scriptable ceiling is SDF or skin bases plus noise displacement; anatomy and faces need human sculpting.
- **Printability notes for organic SDF figures on the P1S:**
  - The underside of spheres overhangs past 45°. Cut a flat base at ≥ 35–40% of the lowest sphere's radius, or lean on Bambu tree supports.
  - Chin and arm undersides are the usual 45° failures; check with the existing gate.
  - Use 0.1 mm layers for visible organic tops.

### Gaps
- No head-to-head print test of SDF versus skin-modifier figurines was done (renders and prints were out of scope).
- Manifold's Apache-2.0 license and Blender's output-license FAQ were not fetched this session.
- The quality of AI-generated 3D meshes for semi-realistic figures was not researched; that is the remit of adjacent researchers.
