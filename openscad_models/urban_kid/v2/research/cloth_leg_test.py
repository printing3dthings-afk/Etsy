"""Cloth-fold proof (Urban Kid v2, 2026-11-17): a baggy trouser leg, longer than
the leg, falls under gravity onto a leg and a sneaker block and stacks into
real folds. Blender's own cloth solver, headless. Real-world metres; the figure
is about 1/36 of this.

    blender -b --python cloth_leg_test.py -- out.stl
"""
import sys

import bpy
import bmesh

out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 90


def add(obj_data, name):
    o = bpy.data.objects.new(name, obj_data)
    sc.collection.objects.link(o)
    return o


def cylinder(name, r, z0, z1, segs=64, rings=1, cap=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=segs, radius1=r, radius2=r, depth=z1 - z0)
    bmesh.ops.translate(bm, vec=(0, 0, (z0 + z1) / 2), verts=bm.verts)
    if rings > 1:
        edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6]
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=rings - 1, use_grid_fill=False)
    bm.to_mesh(me)
    return add(me, name)


# the leg: calf and thigh as a tapered capsule, the sneaker a rounded block
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.055, radius2=0.085, depth=0.80, location=(0, 0, 0.55))
leg = bpy.context.object
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.05, 0.065))
shoe = bpy.context.object
shoe.scale = (0.12, 0.30, 0.13)
bpy.ops.object.modifier_add(type='BEVEL')
shoe.modifiers[-1].width, shoe.modifiers[-1].segments = 0.03, 4
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
ground = bpy.context.object
for o in (leg, shoe, ground):
    o.modifiers.new("col", 'COLLISION')
    o.collision.thickness_outer = 0.004
    o.collision.cloth_friction = 8

# the trouser leg: open tube, 0.115 m radius, 1.05 m long hanging from 0.95: about
# 0.2 m too long, so it has to stack on the shoe
pant = cylinder("pant", 0.115, -0.10, 0.95, segs=72, rings=110, cap=False)
pin = pant.vertex_groups.new(name="pin")
pin.add([v.index for v in pant.data.vertices if v.co.z > 0.94], 1.0, 'REPLACE')
cl = pant.modifiers.new("cloth", 'CLOTH')
s = cl.settings
s.quality = 8
s.mass = 0.25
s.tension_stiffness = s.compression_stiffness = 15
s.shear_stiffness = 5
s.bending_stiffness = 0.6          # cotton twill: soft enough to fold, stiff enough to hold
s.pin_stiffness = 1
s.vertex_group_mass = "pin"
cs = cl.collision_settings
cs.use_self_collision = True
cs.self_distance_min = 0.004
cs.distance_min = 0.004
cs.collision_quality = 3
cl.point_cache.frame_end = sc.frame_end

for f in range(1, sc.frame_end + 1):
    sc.frame_set(f)
    if f % 15 == 0:
        print("frame", f, flush=True)

bpy.context.view_layer.objects.active = pant
pant.select_set(True)
bpy.ops.object.modifier_apply(modifier="cloth")
so = pant.modifiers.new("thick", 'SOLIDIFY')
so.thickness = 0.006
so.offset = 1
sub = pant.modifiers.new("smooth", 'SUBSURF')
sub.levels = 1
bpy.ops.object.select_all(action='DESELECT')
for o in (pant, leg, shoe):
    o.select_set(True)
bpy.ops.export_mesh.stl(filepath=out, use_selection=True, use_mesh_modifiers=True)   # Blender 4.0
print("DONE", out)
