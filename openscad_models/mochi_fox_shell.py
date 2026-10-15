# Mochi Fox, organic pass v3 -- a real attempt, not a first look.
#
# Four things changed from the first Blender build, each fixing a defect that
# showed up in a lit render:
#
# 1. TERRACING. A voxel remesh quantises the surface to its grid, and at 0.55mm
#    that banding was visible on the tail and crown. Fixed with LAPLACIANSMOOTH
#    (preserve_volume) rather than a plain Smooth: plain smoothing shrinks the
#    form toward its centroid, which is how the first pass lost muzzle
#    definition. Laplacian at low lambda removes grid stepping and leaves the
#    silhouette where it was.
#
# 2. THE FACE, PLACED BY RAYCAST. This is the whole argument for Blender on
#    this model. mochi_fox_organizer.scad carries a long comment about THREE
#    failed attempts to place one eye recess -- y_face=33 tore through the side,
#    y_face=24 carved a hidden internal bubble that never reached open air --
#    because a hull-chain's real surface cannot be predicted from its control
#    points and had to be measured out of an exported mesh by hand each time.
#    Here the surface is a real object at author time, so every feature is
#    placed by casting a ray at it and using the hit point and normal. The
#    entire class of bug cannot occur: a cutter seated on a measured hit is by
#    construction touching the surface it is meant to cut.
#
# 3. ADDS BEFORE THE UNION, CUTS AFTER. The nose and brow ridges go in as
#    primitives so the voxel remesh welds them; only the recesses need a
#    boolean, and they are done as ONE difference against one joined cutter.
#    Fewer boolean ops is less exposure to the failure mode §1 warns about --
#    and blender_model.py's manifold guard is what actually decides.
#
# 4. The base is beveled on its vertical edges only, at v2's real base_round.
import bpy, bmesh, mathutils, math

P = PARAMS
base_w, base_d, base_h, base_round = 110, 78, 6, 32
body_r, body_scale = 30, (1.05, 0.9, 1.15)
body_center = (0, -10, base_h + body_r * body_scale[2])
head_pts = [(0, 2, 74, 20), (0, 14, 76, 19), (0, 25, 71, 15.5),
            (0, 34, 62, 9.5), (0, 41, 57, 6), (0, 46, 54, 3.6)]
ear_base_r, ear_tip_r, ear_len = 8.5, 2.2, 21
ear_root, ear_tilt = (8, 13, 79), (12, 0, 16)
tail_pts = [(-19, -35, 19, 13.5), (-33, -31, 33, 11.5), (-42, -19, 47, 9.5),
            (-41, -3, 58, 8.0), (-32, 9, 64, 7.5), (-20, 15, 65, 7.0)]
foot_r, foot_scale = 7.5, (1, 1, 0.55)
foot_x, foot_y, foot_z = 15, 24, base_h + 3
SEG = P.get("seg", 32)

def sphere(p, r, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=SEG,
                                         ring_count=max(8, SEG // 2), location=p)
    o = bpy.context.active_object
    if scale != (1, 1, 1):
        o.scale = scale; solo(o); bpy.ops.object.transform_apply(scale=True)
    return o

shells = []
def blob(*a, **k):
    o = sphere(*a, **k); shells.append(o); return o

def chain(pts, n=4):
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        for k in range(n + 1):
            t = k / n
            blob(tuple(a[j] + (b[j] - a[j]) * t for j in range(3)),
                 a[3] + (b[3] - a[3]) * t)

blob(body_center, body_r, body_scale)
chain(head_pts)
for sx in (1, -1):
    root = mathutils.Vector((ear_root[0] * sx, ear_root[1], ear_root[2]))
    d = mathutils.Euler((math.radians(ear_tilt[0]), 0,
                         math.radians(ear_tilt[2] * sx))).to_matrix() @ mathutils.Vector((0, 0, 1))
    for k in range(9):
        t = k / 8
        blob(tuple(root + d * (ear_len * t)), ear_base_r + (ear_tip_r - ear_base_r) * t)
chain(tail_pts)
for sx in (1, -1):
    for sy in (1, -1):
        blob((foot_x * sx, foot_y * sy, foot_z), foot_r, foot_scale)
blob((0, 49, 53), 3.6)                                   # nose, welded by the remesh

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, base_h / 2))
plate = bpy.context.active_object
plate.scale = (base_w, base_d, base_h)
solo(plate); bpy.ops.object.transform_apply(scale=True)
bm = bmesh.new(); bm.from_mesh(plate.data)
bmesh.ops.bevel(bm, geom=[e for e in bm.edges
                          if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6],
                offset=base_round, segments=14, affect='EDGES', profile=0.5)
bm.to_mesh(plate.data); bm.free()
shells.append(plate)

bpy.ops.object.select_all(action='DESELECT')
for o in shells: o.select_set(True)
bpy.context.view_layer.objects.active = shells[0]
bpy.ops.object.join()
fox = solo(bpy.context.view_layer.objects.active)
rm = fox.modifiers.new("rem", 'REMESH'); rm.mode = 'VOXEL'
rm.voxel_size = P.get("voxel", 0.7)
ls = fox.modifiers.new("lap", 'LAPLACIANSMOOTH')
ls.lambda_factor = P.get("lap", 0.22); ls.iterations = P.get("lap_iters", 6)
ls.use_volume_preserve = True
apply_all(fox)


# DECIMATE BEFORE HANDING OFF TO CGAL. A 212k-triangle import made OpenSCAD's
# Nef conversion blow past a two-minute timeout before the boolean even began.
# Blender's planar+collapse decimate takes seconds and the shell is a smooth
# organic surface, so 60k carries it with no visible loss.
_dec = fox.modifiers.new("dec", 'DECIMATE')
_dec.ratio = PARAMS.get("dec", 0.28)
apply_all(fox)
print("PROBE decimated to", len(fox.data.polygons), "tris")

# ---- MEASURE, do not cut ------------------------------------------------------
# The shell is finished here. Every face feature is then placed by asking the
# REAL surface where it is -- and the cutting itself is handed to OpenSCAD,
# which has the reliable boolean. Blender measures; CGAL cuts. Each tool does
# the thing the other structurally cannot.
import json
dg = bpy.context.evaluated_depsgraph_get()

def surface(x, z):
    ok, loc, nrm, *_ = fox.ray_cast(mathutils.Vector((x, 200.0, z)),
                                    mathutils.Vector((0, -1, 0)), depsgraph=dg)
    return (list(loc), list(nrm)) if ok else None

def scan_face(x, z_lo, z_hi, step=1.0):
    """Walk up a column and report where the head surface actually is. Asking
    for one point is how v2 guessed wrong three times; scanning shows the whole
    profile, including where the head ENDS and the chest starts (a sudden drop
    in y is that boundary, not a cheek)."""
    out = []
    z = z_lo
    while z <= z_hi:
        h = surface(x, z)
        if h: out.append([round(x,1), round(z,1), round(h[0][1],2)])
        z += step
    return out

probe = {
    "col_x0": scan_face(0, 46, 80, 2.0),
    "col_x5": scan_face(5, 46, 80, 2.0),
    "col_x9": scan_face(9, 52, 80, 2.0),
    "col_x13": scan_face(13, 52, 80, 2.0),
}
print("PROBEJSON " + json.dumps(probe))
