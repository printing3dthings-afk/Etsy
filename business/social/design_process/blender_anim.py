"""Blender side of the design-process animations (run by anim.py; not on its own).

Reads a shot spec (JSON) and renders its frames as PNGs. Same studio as tools/blender_render.py
(floor, three area lights, matte filament materials, light grey world), so a moving shot and the
design-review stills it cuts to look like one camera.

Spec keys:
  res [w, h], frames N, engine "CYCLES"|"EEVEE", samples, lens, out_dir,
  frame_from/frame_to (optional, to render part of a shot)
  parts: [{path, rgb, keys: [[frame, [dx, dy, dz], rot_z_deg], ...], show: [from, to] (optional),
           clip: true (optional: hide everything with y < the clip value)}]
  camera: {target [x,y,z] / target_z / radius (mm, optional),
           keys: [[frame, az_deg, el_deg, zoom(, aim_z_mm)], ...]}
  clip_keys: [[frame, y_mm], ...]   the cut plane's position over time (y: + is away from az 0)
Positions are in the parts' own frame (mm); the camera is fitted once, to the assembled parts.
"""
import json
import math
import sys

import bpy
import mathutils

spec = json.loads(open(sys.argv[sys.argv.index("--") + 1]).read())
# Everything inside Blender is in metres (the spec is in mm). At mm-as-metres the scene is
# hundreds of units across and EEVEE's shadow maps and light ranges fall apart: the first EEVEE
# tests rendered flat, with no floor shadow. K converts every spec figure on the way in.
K = 0.001
scene = bpy.context.scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

clip_node_values = []


def material(name, rgb, clip):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.5
    if clip:
        # alpha = 1 where the surface is behind the cut plane (world y > clip), else 0
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        val = nt.nodes.new("ShaderNodeValue")
        cmp_ = nt.nodes.new("ShaderNodeMath")
        cmp_.operation = "GREATER_THAN"
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        nt.links.new(sep.outputs["Y"], cmp_.inputs[0])
        nt.links.new(val.outputs[0], cmp_.inputs[1])
        nt.links.new(cmp_.outputs[0], bsdf.inputs["Alpha"])
        mat.blend_method = "CLIP"
        mat.shadow_method = "CLIP"
        clip_node_values.append(val)
    return mat


objs = []
for i, p in enumerate(spec["parts"]):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.stl_import(filepath=p["path"])
    o = bpy.context.selected_objects[0]
    o.name = f"part{i}"
    o.data = o.data.copy()          # its own mesh, then mm -> m in the vertices themselves
    o.data.transform(mathutils.Matrix.Scale(K, 4))
    o.scale = (1, 1, 1)
    for poly in o.data.polygons:
        poly.use_smooth = True
    if hasattr(o.data, "use_auto_smooth"):
        o.data.use_auto_smooth = True
        o.data.auto_smooth_angle = math.radians(30)
    o.data.materials.append(material(f"m{i}", p["rgb"], p.get("clip", False)))
    # the mesh's own origin stays at the parts' frame origin: keys move it from there
    for f, (dx, dy, dz), rz in p.get("keys", [[1, [0, 0, 0], 0]]):
        o.location = (dx * K, dy * K, dz * K)
        o.rotation_euler = (0, 0, math.radians(rz))
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)
    if "show" in p:
        a, b = p["show"]
        for f, hide in ((1, True), (a, False), (b + 1, True)):
            if f < 1:
                continue
            o.hide_render = hide and not (a <= f <= b)
            o.keyframe_insert("hide_render", frame=f)
    objs.append(o)

for val in clip_node_values:
    for f, y in spec.get("clip_keys", [[1, -1e4]]):
        val.outputs[0].default_value = y * K
        val.outputs[0].keyframe_insert("default_value", frame=f)

# fit the camera once, to the parts as assembled (their key at frame 1 ignored: origin frame)
bpy.context.view_layer.update()
vs = []
for o, p in zip(objs, spec["parts"]):
    if p.get("fit", True):
        step = max(1, len(o.data.vertices) // 40000)
        vs += [o.data.vertices[k].co.copy() for k in range(0, len(o.data.vertices), step)]
xs, ys, zs = zip(*[(v.x, v.y, v.z) for v in vs])
size = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
cam_spec = spec["camera"]
target = mathutils.Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
                           cam_spec["target_z"] * K if "target_z" in cam_spec else (min(zs) + max(zs)) / 2))
lens = spec.get("lens", 50.0)
w, h = spec["res"]
tan_half = 18.0 / lens * 0.86 * min(1.0, w / h)
radius = max((v - target).length for v in vs)
# a fixed target and radius (mm) keep every shot of one video on the same framing, whatever its
# parts: a cutaway has half the vertices and would otherwise reframe the camera
if "target" in cam_spec:
    target = mathutils.Vector([c * K for c in cam_spec["target"]])
if "radius" in cam_spec:
    radius = cam_spec["radius"] * K
base_dist = radius / tan_half

bpy.ops.mesh.primitive_plane_add(size=size * 80, location=(target.x, target.y, min(zs)))
floor = bpy.context.active_object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.93, 0.92, 0.90, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
floor.data.materials.append(fm)

bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.lens = lens
cam.data.clip_start = 0.001
cam.data.clip_end = base_dist * 20
scene.camera = cam
# the camera rides an empty at the target: az/el rotate the empty, zoom moves the camera in
bpy.ops.object.empty_add(location=target)
rig = bpy.context.active_object
cam.parent = rig
for key in cam_spec["keys"]:
    f, az, el, zoom = key[:4]
    rig.rotation_euler = (math.radians(90 - el), 0, math.radians(az))
    rig.keyframe_insert("rotation_euler", frame=f)
    if len(key) > 4:                    # a fifth figure aims the camera at this height (mm)
        rig.location = (target.x, target.y, key[4] * K)
        rig.keyframe_insert("location", frame=f)
    cam.location = (0, 0, base_dist / zoom)
    cam.keyframe_insert("location", frame=f)
# Blender's default Bezier easing on every key: each move starts and lands softly

def area(name, loc, energy, sz):
    bpy.ops.object.light_add(type="AREA", location=loc)
    l = bpy.context.active_object
    l.data.energy = energy
    l.data.size = sz
    # the scene is in mm, so in Blender's units it's hundreds of "metres" across: EEVEE's
    # default light reach and shadow range fall far short of it (the first test rendered flat)
    l.data.use_custom_distance = True
    l.data.cutoff_distance = size * 50
    l.data.shadow_buffer_clip_start = size * 0.05
    l.rotation_euler = (target + mathutils.Vector((0, 0, -size * 0.2)) - l.location).to_track_quat("-Z", "Y").to_euler()


eevee = spec.get("engine", "CYCLES") == "EEVEE"
if eevee:
    # EEVEE (Blender 4.0, software GL here) gave the area lights nothing at all, tested
    # 2026-11-26: with the world off the frame was black, and a sun lit it with real shadows.
    # So EEVEE gets soft suns from the stills' three directions: key front-right high, fill left,
    # rim behind.
    def sun(direction, energy, angle_deg, shadow=True):
        bpy.ops.object.light_add(type="SUN")
        l = bpy.context.active_object
        l.data.energy = energy
        l.data.angle = math.radians(angle_deg)
        l.data.use_shadow = shadow
        # the default cascade spans 200 m: keep the shadow map's resolution on the model
        l.data.shadow_cascade_max_distance = size * 12
        l.data.shadow_cascade_count = 2
        l.data.use_contact_shadow = shadow
        l.data.contact_shadow_distance = size * 0.05
        l.rotation_euler = (-mathutils.Vector(direction)).to_track_quat("-Z", "Y").to_euler()
    # The key comes from the side, not from behind the camera: from there (the stills' direction)
    # every shadow fell behind the model and it rendered flat (tested 2026-11-26).
    sun((2.0, -0.4, 1.6), 3.2, 4)
    sun((-1.5, -1.5, 1.0), 0.6, 30, shadow=False)
    sun((-0.5, 2.2, 1.6), 1.0, 20, shadow=False)
else:
    s = size / K / 60.0 * K * K
    c = target
    area("key", (c.x + size * 1.8, c.y - size * 1.6, size * 2.2), 900 * s, size * 0.9)
    area("fill", (c.x - size * 2.0, c.y - size * 0.6, size * 1.2), 250 * s, size * 1.2)
    area("rim", (c.x, c.y + size * 2.2, size * 1.6), 500 * s, size * 0.9)
world = scene.world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.97, 0.97, 0.98, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3 if eevee else 0.6
if eevee:
    # Seen directly, the world is the floor's own lit grey, so the horizon disappears; it lights
    # the scene as before. (With a low camera, the dimmer world showed as a dark band, 2026-11-26.)
    wn = world.node_tree
    bg_cam = wn.nodes.new("ShaderNodeBackground")
    bg_cam.inputs["Color"].default_value = (*spec.get("horizon_rgb", [1.1, 1.1, 1.1]), 1)
    lp = wn.nodes.new("ShaderNodeLightPath")
    mx = wn.nodes.new("ShaderNodeMixShader")
    out = wn.nodes["World Output"]
    wn.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
    wn.links.new(wn.nodes["Background"].outputs[0], mx.inputs[1])
    wn.links.new(bg_cam.outputs[0], mx.inputs[2])
    wn.links.new(mx.outputs[0], out.inputs["Surface"])

if eevee:
    scene.eevee.shadow_cascade_size = "4096"
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = spec.get("samples", 32)
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = size * 0.08
    scene.eevee.light_threshold = 1e-5
    scene.eevee.use_soft_shadows = True
    scene.eevee.shadow_cube_size = "2048"
else:
    scene.render.engine = "CYCLES"
    scene.cycles.samples = spec.get("samples", 24)
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 4
scene.render.resolution_x, scene.render.resolution_y = w, h
scene.render.image_settings.file_format = "PNG"
scene.frame_start = spec.get("frame_from", 1)
scene.frame_end = spec.get("frame_to", spec["frames"])
scene.render.filepath = spec["out_dir"].rstrip("/") + "/f_"
bpy.ops.render.render(animation=True)
print("ANIM_OK size", size, "scale", objs[0].scale[:])
