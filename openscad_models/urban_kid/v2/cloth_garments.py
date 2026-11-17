"""Urban Kid v2: the clothes, simulated as cloth on the mannequin (2026-11-17).

Scott's references get their folds from sculptors copying real cloth. This makes
the real cloth instead: each garment is cut a little too long or too wide, then
pushed into place over the body (mannequin.py) by Blender's cloth solver, and
it folds the way fabric does where it's compressed or hanging:

  pants    each leg a tube from the hip to above the sneaker, its waist ring
           pushed down 8 mm: the legs stack in folds over the shoes
  sleeves  tubes along the arm, carried past the hand, the cuff ring drawn
           back to the wrist: compression folds at the elbow and forearm
  body     the hoodie's body hung from its shoulders, its hem ring drawn up
           and in to the waistband: hanging folds and the blousing over the hem

Each garment collides only with the body parts it covers (an arm doesn't push
the hoodie's body, which the sleeve covers there anyway). Simulated at real
human size (1 mm of v1 = 15 mm) so the cloth behaves like cloth, and written
back in v1's mm frame as a raw surface (no thickness): assemble.py gives it
thickness and joins it.

    blender -b --python cloth_garments.py -- SIM_DIR pants|sleeves|body [frames]
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SIM, WHICH = Path(argv[0]), argv[1]
FRAMES = int(argv[2]) if len(argv) > 2 else 60
K = 0.015                       # v1 mm -> simulated metres
STEP = 0.38                     # mm between rings and round each ring

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES


def link(obj):
    sc.collection.objects.link(obj)
    return obj


def collider(path, coll):
    bpy.ops.import_mesh.stl(filepath=str(path))
    o = bpy.context.selected_objects[0]
    o.scale = (K, K, K)
    bpy.ops.object.transform_apply(scale=True)
    o.modifiers.new("col", 'COLLISION')
    o.collision.thickness_outer = 0.003
    o.collision.cloth_friction = 6
    for c in o.users_collection:
        c.objects.unlink(o)
    coll.objects.link(o)
    return o


def frames_along(pts):
    """Unit tangents and a rotation-minimising normal frame along a polyline."""
    T = []
    for i in range(len(pts)):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        T.append((b - a).normalized())
    u = T[0].orthogonal().normalized()
    if abs(T[0].z) > 0.7:                 # a near-vertical tube: u points along +x
        u = (Vector((1, 0, 0)) - T[0] * T[0].x).normalized()
    U = [u]
    for i in range(1, len(pts)):
        u = U[-1] - T[i] * U[-1].dot(T[i])
        U.append(u.normalized())
    return T, U, [t.cross(u) for t, u in zip(T, U)]


def resample(ctrl, step):
    """Catmull-Rom through ctrl, sampled every `step` along its length."""
    ctrl = [Vector(c) for c in ctrl]
    dense = []
    P = [ctrl[0] * 2 - ctrl[1]] + ctrl + [ctrl[-1] * 2 - ctrl[-2]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(40):
            t = k / 40
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(ctrl[-1])
    out, acc = [dense[0]], 0.0
    for a, b in zip(dense[:-1], dense[1:]):
        acc += (b - a).length
        if acc >= step:
            out.append(b)
            acc = 0.0
    if (out[-1] - dense[-1]).length > step * 0.3:
        out.append(dense[-1])
    return out


def tube(name, centres, radii, segs):
    """An open tube: ring i at centres[i] with semi-axes radii[i] = (along u, along v)."""
    T, U, Vv = frames_along(centres)
    bm = bmesh.new()
    rings = []
    for c, (a, b), u, v in zip(centres, radii, U, Vv):
        rings.append([bm.verts.new((c + a * math.cos(2 * math.pi * k / segs) * u
                                    + b * math.sin(2 * math.pi * k / segs) * v) * K) for k in range(segs)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(segs):
            bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    o = link(bpy.data.objects.new(name, me))
    n = len(centres)
    return o, [list(range(i * segs, (i + 1) * segs)) for i in range(n)]


def lerp_radii(zs, table):
    """Semi-axes at each z from a (z, a, b) table, linear between rows."""
    table = sorted(table)
    out = []
    for z in zs:
        for (z0, a0, b0), (z1, a1, b1) in zip(table[:-1], table[1:]):
            if z0 <= z <= z1:
                t = (z - z0) / (z1 - z0)
                out.append((a0 + (a1 - a0) * t, b0 + (b1 - b0) * t))
                break
        else:
            out.append(table[0][1:] if z < table[0][0] else table[-1][1:])
    return out


def empty_at(name, loc):
    e = link(bpy.data.objects.new(name, None))
    e.location = Vector(loc) * K
    return e


def hook(o, idx, e, keys):
    """Drag the vertices idx with the empty e: keys = [(frame, offset_mm, scale)]."""
    h = o.modifiers.new("hook_" + e.name, 'HOOK')
    h.object = e
    h.vertex_indices_set(idx)
    h.center = e.location
    h.matrix_inverse = Matrix.Translation(e.location).inverted()   # e.matrix_world is stale until a depsgraph update
    base = e.location.copy()
    for f, off, s in keys:
        e.location = base + Vector(off) * K
        e.scale = (s, s, 1.0)
        e.keyframe_insert("location", frame=f)
        e.keyframe_insert("scale", frame=f)


def cloth(o, pin_idx, colliders, bending, mass=0.3):
    g = o.vertex_groups.new(name="pin")
    g.add(pin_idx, 1.0, 'REPLACE')
    cl = o.modifiers.new("cloth", 'CLOTH')
    s = cl.settings
    s.quality = 10
    s.mass = mass
    s.tension_stiffness = s.compression_stiffness = 15
    s.shear_stiffness = 5
    s.bending_stiffness = bending
    s.pin_stiffness = 1
    s.vertex_group_mass = "pin"
    cs = cl.collision_settings
    cs.collection = colliders
    cs.use_self_collision = True
    cs.self_distance_min = 0.003
    cs.distance_min = 0.003
    cs.collision_quality = 3
    cl.point_cache.frame_end = FRAMES
    return cl


def collection(name, files):
    c = bpy.data.collections.new(name)
    sc.collection.children.link(c)
    for f in files:
        collider(SIM / f, c)
    return c


ground = bpy.data.collections.new("ground")
garments = []
if WHICH == "pants":
    col = collection("legs", ["col_legs.stl", "shoes.stl"])
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 5.0 * K))
    gp = bpy.context.object
    gp.modifiers.new("col", 'COLLISION')
    for c in gp.users_collection:
        c.objects.unlink(gp)
    col.objects.link(gp)
    for s in (1, -1):
        top, bot = Vector((s * 8.0, 1.0, 40.0)), Vector((s * 9.0, 0.3, 15.0))
        n = int((top - bot).length / STEP) + 1
        cs = [top.lerp(bot, i / (n - 1)) for i in range(n)]
        rad = lerp_radii([c.z for c in cs], [(15.0, 7.8, 8.4), (26.0, 7.2, 7.6), (34.0, 6.4, 7.0), (40.0, 6.0, 6.8)])
        o, rings = tube(f"leg_{s}", cs, rad, 96)
        e = empty_at(f"waist_{s}", top)
        hook(o, rings[0], e, [(4, (0, 0, 0), 1.0), (40, (0, 0, -8.0), 1.0)])
        cloth(o, rings[0], col, bending=3.0, mass=0.45)      # cotton twill: broad folds, not crumple
        garments.append(o)
elif WHICH == "sleeves":
    col = collection("arms", ["col_arms.stl"])
    ARM = {"sh": (16.0, 1.0, 60.5), "el": (17.2, 2.6, 50.6), "ha": (9.4, -5.6, 47.8)}
    for s in (1, -1):
        sh, el, ha = (Vector((s * ARM[k][0], ARM[k][1], ARM[k][2])) for k in ("sh", "el", "ha"))
        fore = (ha - el).normalized()
        # from inside the hoodie's body (its open end hidden there) over the shoulder
        ctrl = [Vector((s * 12.5, 1.0, 59.0)), sh + Vector((0, 0, 0.5)), sh.lerp(el, 0.5), el, el.lerp(ha, 0.5), ha,
                ha + fore * 5.0]
        cs = resample(ctrl, STEP)
        L = [0.0]
        for a, b in zip(cs[:-1], cs[1:]):
            L.append(L[-1] + (b - a).length)
        tot = L[-1]
        rad = [(6.0 - 1.4 * t / tot, 6.0 - 1.4 * t / tot) for t in L]
        o, rings = tube(f"sleeve_{s}", cs, rad, 72)
        e = empty_at(f"cuff_{s}", cs[-1])
        hook(o, rings[-1], e, [(4, (0, 0, 0), 1.0), (40, tuple(-fore * 4.0), 0.92)])
        cloth(o, rings[0] + rings[-1], col, bending=12.0, mass=0.4)    # fleece
        garments.append(o)
elif WHICH == "body":
    # hung from a ring round the neck, the cloth flaring out over the shoulders
    # (every ring starts clear of them) and narrowing under the arms to the
    # sleeves, which lie outside it; the hem ring is drawn up and in
    col = collection("torso", ["col_torso.stl"])
    top, bot = 67.0, 39.5
    n = int((top - bot) / STEP) + 1
    cs = [Vector((0, 0.8, top - (top - bot) * i / (n - 1))) for i in range(n)]
    rad = lerp_radii([c.z for c in cs], [(39.5, 15.4, 11.2), (45.0, 15.4, 11.8), (52.0, 15.0, 11.8),
                                         (57.0, 15.6, 11.4), (60.0, 18.0, 11.0), (63.0, 18.8, 10.6),
                                         (65.6, 17.2, 10.0), (66.6, 13.5, 8.6), (67.0, 7.8, 7.4)])
    o, rings = tube("body", cs, rad, 150)
    e = empty_at("hem", cs[-1])
    hook(o, rings[-1], e, [(4, (0, 0, 0), 1.0), (40, (0, 0, 2.5), 0.86)])
    cloth(o, rings[0] + rings[-1], col, bending=4.0, mass=0.35)    # fleece
    garments.append(o)
else:
    raise SystemExit("pants, sleeves or body")

for f in range(1, FRAMES + 1):
    sc.frame_set(f)
    if f % 10 == 0:
        print(WHICH, "frame", f, flush=True)

for o in garments:
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    o.data.transform(Matrix.Scale(1.0 / K, 4))
bpy.ops.object.select_all(action='DESELECT')
for o in garments:
    o.select_set(True)
out = SIM / f"cloth_{WHICH}.stl"
bpy.ops.export_mesh.stl(filepath=str(out), use_selection=True)   # Blender 4.0
print("DONE", out, flush=True)
