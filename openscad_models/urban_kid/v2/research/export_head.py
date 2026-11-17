"""Export a CC0 head base mesh (Blender Studio Human Base Meshes v1.4.1) with its
eyes, subdivided dense for sculpting in code.

    blender -b human_base_meshes_bundle.blend --python export_head.py -- out.ply LEVELS [stylized]

'stylized' takes 'Head - Stylized' (young: rounder face, bigger eyes, shorter
nose), which suits a designer-toy teen; the default is 'Head (Sculpting) - Realistic'.
"""
import sys
import bpy

out, lv = sys.argv[sys.argv.index("--") + 1], int(sys.argv[sys.argv.index("--") + 2])
args = sys.argv[sys.argv.index("--") + 1:]
if len(args) > 2 and args[2] == "stylized":
    names = ["GEO-head_stylized", "GEO-head_stylized.eye.L", "GEO-head_stylized.eye.R"]
else:
    names = ["GEO-head_sculpting_realistic", "GEO-head_sculpting_realistic.sclera.L", "GEO-head_sculpting_realistic.sclera.R"]
dg = bpy.context.evaluated_depsgraph_get()
objs = []
for n in names:
    o = bpy.data.objects[n]
    for m in o.modifiers:
        if m.type == 'MULTIRES':
            m.levels = m.render_levels = m.total_levels
    s = o.modifiers.new("dense", 'SUBSURF')
    s.levels = s.render_levels = lv if n == names[0] else 2
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    me.transform(o.matrix_world)
    t = bpy.data.objects.new(n + "_x", me)
    bpy.context.scene.collection.objects.link(t)
    objs.append(t)
for ob in bpy.context.scene.objects:
    ob.select_set(ob in objs)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
# (bpy.ops attributes always "exist": hasattr() can't pick the exporter. 4.0 has wm.ply_export)
bpy.ops.wm.ply_export(filepath=out, export_selected_objects=True, export_normals=False, export_uv=False, ascii_format=False)
print("HEAD", len(objs[0].data.vertices))
