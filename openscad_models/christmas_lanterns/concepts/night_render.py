#!/usr/bin/env python3
"""Render a lantern study lit from inside, in a dark room (2026-10-13).

    python3 night_render.py out.png part.stl [part.stl ...] [--az 35] [--el 16]

Every part is white PLA: a subsurface-scattering material, so light coming
through thin plastic glows and thicker plastic (the scene standing out of the
glass, the frame) shows darker -- the way a lithophane or our glowing toy
windows work. One warm point light stands where the tealight goes. This is a
render of a model, not a photo of a print: how dark the scene reads on a real
print depends on the filament and the light.
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

BLENDER_SCRIPT = r'''
import bpy, json, math, sys, mathutils
a = json.loads(sys.argv[sys.argv.index("--") + 1])
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete()
mat = bpy.data.materials.new("pla"); mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.93, 0.90, 0.84, 1)
b.inputs["Roughness"].default_value = 0.6
b.inputs["Subsurface Weight"].default_value = 1.0
b.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.6)
b.inputs["Subsurface Scale"].default_value = a["sss"]
objs = []
for p in a["parts"]:
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=p)
    for o in set(bpy.data.objects) - before:
        o.data.materials.clear(); o.data.materials.append(mat); objs.append(o)
bpy.context.view_layer.update()
pts = [o.matrix_world @ mathutils.Vector(c) for o in objs for c in o.bound_box]
lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
size = max(hi - lo)
for o in objs:
    o.location -= mathutils.Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
bpy.ops.mesh.primitive_plane_add(size=size * 8)
fl = bpy.context.active_object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.3, 0.27, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
fl.data.materials.append(fm)
# the tealight: a warm point light where the flame would be
bpy.ops.object.light_add(type="POINT", location=(0, 0, a["light_z"]))
L = bpy.context.active_object; L.data.energy = a["energy"]; L.data.color = (1.0, 0.72, 0.42); L.data.shadow_soft_size = 6
w = bpy.context.scene.world; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.008, 0.016, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
az, el = math.radians(a["az"]), math.radians(a["el"])
d = size * 2.15
bpy.ops.object.camera_add(location=(d * math.cos(el) * math.sin(az), -d * math.cos(el) * math.cos(az), d * math.sin(el) + size * 0.25))
cam = bpy.context.active_object
cam.rotation_euler = (mathutils.Vector((0, 0, size * 0.42)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 50
s = bpy.context.scene; s.camera = cam; s.render.engine = "CYCLES"
s.cycles.samples = a["samples"]; s.cycles.use_denoising = False  # no OIDN in this build
# clamp the speckle a point light inside scattering plastic throws
s.cycles.sample_clamp_direct = 4.0; s.cycles.sample_clamp_indirect = 1.0
s.render.resolution_x = s.render.resolution_y = a["res"]
s.render.filepath = a["out"]
bpy.ops.render.render(write_still=True)
print("NIGHT_RENDER_OK", a["out"])
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("parts", nargs="+")
    ap.add_argument("--az", type=float, default=35); ap.add_argument("--el", type=float, default=14)
    ap.add_argument("--light-z", type=float, default=22); ap.add_argument("--energy", type=float, default=60000)
    ap.add_argument("--sss", type=float, default=1.5, help="subsurface scale, mm")
    ap.add_argument("--samples", type=int, default=96); ap.add_argument("--res", type=int, default=900)
    a = ap.parse_args()
    args = dict(parts=[str(Path(p).resolve()) for p in a.parts], out=str(Path(a.out).resolve()), az=a.az, el=a.el,
                light_z=a.light_z, energy=a.energy, sss=a.sss, samples=a.samples, res=a.res)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(BLENDER_SCRIPT)
    r = subprocess.run(["blender", "-b", "--python", f.name, "--", json.dumps(args)], capture_output=True, text=True)
    if "NIGHT_RENDER_OK" not in r.stdout:
        sys.exit(r.stdout[-2000:] + r.stderr[-2000:])
    print("rendered ->", a.out)

if __name__ == "__main__":
    main()
