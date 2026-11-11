"""Blender scene for the village-at-night animation (run by make.py, not directly).

    blender -b --python scene.py -- <config.json>

Three Gingerbread buildings from the sale ZIP, in their README colours, on snow,
at night. Each is a hollow lantern over a battery LED tealight (README,
"LIGHTING"), so each is lit from inside by a small warm light where the tealight
sits, and the glow leaves through the real window openings. Snow falls; the
lights come on one by one; the camera drifts in. EEVEE, so a frame takes seconds.
"""
import json
import math
import random
import sys

import bpy
from mathutils.bvhtree import BVHTree

cfg = json.load(open(sys.argv[sys.argv.index("--") + 1]))
FPS, FRAMES = 30, cfg["frames"]
MM = 0.001

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.fps = FPS


def glow_mat(name, rgb, level):
    """The plastic, plus the tealight shining through it: emission scaled by the
    face's 'glow' attribute (from its measured wall thickness) and by a keyframed
    value that is the building's light coming on (appended to `level`)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.55
    warm = (1.0, 0.62, 0.32)
    # Light through coloured plastic takes its colour, and dark plastic passes far
    # less: measured on the cottage, its white panes (1.8-2.1 mm) and gingerbread
    # walls (1.7-1.9 mm) are the same thickness, so on the real print it's the
    # colour, not the thickness, that makes the windows the bright part.
    lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    passes = lum ** 1.5
    b.inputs["Emission Color"].default_value = (*(w * c * passes for w, c in zip(warm, rgb)), 1)
    att = nt.nodes.new("ShaderNodeAttribute")
    att.attribute_name = "glow"
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(att.outputs["Fac"], mul.inputs[0])
    mul.inputs[1].default_value = 0.0
    level.append(mul.inputs[1])
    nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    return m


def through(tree, start, d):
    """mm of plastic a ray crosses from this surface before it reaches the air
    inside the building. Icing on a wall is two parts touching: stopping at the
    first exit measured the icing alone, and every bit of trim glowed like neon."""
    pos, total, inside = 0.0, 0.0, True
    o = start + d * 0.01
    for _ in range(10):
        hit = tree.ray_cast(o, d, 60.0)
        if hit[0] is None:
            return 99.0
        step = hit[3]
        if inside:
            total = pos + step
        elif step > 0.8:          # a real gap of air: we're through
            return total
        pos += step
        inside = not inside if step > 1e-4 or inside else inside
        o = hit[0] + d * 0.01
        pos += 0.01
    return total


def mat(name, rgb, rough=0.55, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ---- the buildings, each recentred: base on the snow, centre on its spot ----
for b in cfg["buildings"]:
    objs, levels = [], []
    for path, colour in b["parts"]:
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.wm.stl_import(filepath=path)
        o = bpy.context.selected_objects[0]
        o.scale = (MM, MM, MM)
        o.data.materials.append(glow_mat(o.name, srgb(colour), levels))
        objs.append(o)
    # How much light gets through each face: the plastic's thickness under it,
    # measured straight in, through every part of the building. The windows are
    # closed, with 1.48 mm white panes behind them (CHRISTMAS_VILLAGE.md), so the
    # panes glow, the ~2.2 mm walls faintly, thick parts not at all.
    verts, tris = [], []
    for o in objs:
        base = len(verts)
        verts += [v.co.copy() for v in o.data.vertices]
        tris += [[base + i for i in p.vertices] for p in o.data.polygons]
    tree = BVHTree.FromPolygons(verts, tris)
    for o in objs:
        g = o.data.attributes.new("glow", "FLOAT", "FACE")
        vals = []
        for p in o.data.polygons:
            vals.append(math.exp(-max(through(tree, p.center, -p.normal) - 1.4, 0.0) / 0.9))
        g.data.foreach_set("value", vals)
    bpy.context.view_layer.update()
    xs, ys, zs = [], [], []
    for o in objs:
        for v in o.bound_box:
            w = o.matrix_world @ __import__("mathutils").Vector(v)
            xs.append(w.x), ys.append(w.y), zs.append(w.z)
    cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
    for o in objs:
        o.location.x += b["at"][0] - cx
        o.location.y += b["at"][1] - cy
        o.location.z -= z0
        o.rotation_euler.z = 0
    # the tealight: a small warm light where a 45 mm LED tealight would glow
    bpy.ops.object.light_add(type="POINT", location=(b["at"][0], b["at"][1], 0.03))
    lt = bpy.context.active_object
    lt.data.color = (1.0, 0.58, 0.26)
    lt.data.shadow_soft_size = 0.004
    # thin 2 mm walls leak light in EEVEE unless the shadow starts close and
    # contact shadows fill the gap (the first test frame washed the snow white)
    lt.data.shadow_buffer_clip_start = 0.0005
    lt.data.use_contact_shadow = True
    lt.data.contact_shadow_distance = 0.01
    lt.data.contact_shadow_thickness = 0.001
    lt.data.shadow_buffer_bias = 0.0002
    # a tealight's reach: past ~18 cm its light is spent, so stop it there smoothly
    lt.data.use_custom_distance = True
    lt.data.cutoff_distance = 0.18
    on, ramp = b["on"], 14
    for f, e in ((1, 0.0), (on, 0.0), (on + ramp, b["watts"])):
        lt.data.energy = e
        lt.data.keyframe_insert("energy", frame=f)
    # an LED tealight's gentle flicker, after it comes on
    rnd = random.Random(b["name"])
    for f in range(on + ramp + 6, FRAMES + 1, 6):
        lt.data.energy = b["watts"] * (0.9 + 0.2 * rnd.random())
        lt.data.keyframe_insert("energy", frame=f)
    # the glow through the plastic follows the same switch-on and flicker
    for sock in levels:
        for f, e in ((1, 0.0), (on, 0.0), (on + ramp, b["glow"])):
            sock.default_value = e
            sock.keyframe_insert("default_value", frame=f)
        rnd2 = random.Random(b["name"])
        for f in range(on + ramp + 6, FRAMES + 1, 6):
            sock.default_value = b["glow"] * (0.9 + 0.2 * rnd2.random())
            sock.keyframe_insert("default_value", frame=f)

# ---- snow ground, sky, moon ----
# a hair below the bases: flush, the lights leaked under them across the snow
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.0003))
bpy.context.active_object.data.materials.append(mat("snow", (0.82, 0.86, 0.95), rough=0.85))
world = bpy.data.worlds.new("night")
sc.world = world
world.use_nodes = True
# a night sky that lightens toward the horizon, so ground and sky meet softly
nt0 = world.node_tree
tc = nt0.nodes.new("ShaderNodeTexCoord")
sep = nt0.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt0.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0.022, 0.03, 0.06, 1)
ramp.color_ramp.elements[1].position = 0.35
ramp.color_ramp.elements[1].color = (0.004, 0.006, 0.02, 1)
nt0.links.new(tc.outputs["Generated"], sep.inputs[0])
nt0.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
nt0.links.new(ramp.outputs["Color"], nt0.nodes["Background"].inputs["Color"])
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
# a little night haze, so the snow fades into the dark instead of ending at a line
nt = world.node_tree
vol = nt.nodes.new("ShaderNodeVolumeScatter")
vol.inputs["Density"].default_value = 0.12
vol.inputs["Color"].default_value = (0.35, 0.42, 0.65, 1)
if cfg.get("haze", True):
    nt.links.new(vol.outputs[0], nt.nodes["World Output"].inputs["Volume"])
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(60), 0, math.radians(-150)))
moon = bpy.context.active_object
moon.data.color = (0.62, 0.72, 1.0)
moon.data.energy = 0.35
moon.data.angle = math.radians(3)
# a soft cool fill from the front, moonlight off the snow, so the fronts keep their colour
bpy.ops.object.light_add(type="AREA", location=(0.0, -0.6, 0.35))
fill = bpy.context.active_object
fill.data.size = 0.6
fill.data.color = (0.7, 0.78, 1.0)
fill.data.energy = 1.6
fill.rotation_euler = (math.radians(58), 0, 0)

# ---- falling snow: small soft flakes, each falling at its own speed ----
flake = mat("flake", (0.9, 0.93, 1.0), emit=(0.85, 0.9, 1.0), strength=0.35)
rnd = random.Random(7)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1)
proto = bpy.context.active_object
proto.data.materials.append(flake)
for i in range(cfg["flakes"]):
    o = proto.copy()
    sc.collection.objects.link(o)
    s = rnd.uniform(0.0005, 0.0011)
    o.scale = (s, s, s)
    x, y = rnd.uniform(-0.22, 0.22), rnd.uniform(-0.45, 0.25)
    z = rnd.uniform(0.0, 0.5)
    fall = rnd.uniform(0.18, 0.32) * FRAMES / 300
    drift = rnd.uniform(-0.02, 0.02)
    o.location = (x, y, z)
    o.keyframe_insert("location", frame=1)
    o.location = (x + drift, y, z - fall)
    o.keyframe_insert("location", frame=FRAMES)
    for fc in o.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
bpy.data.objects.remove(proto)

# ---- camera: a slow drift in and down toward the street ----
bpy.ops.object.empty_add(location=cfg["look_from"][1])
target = bpy.context.active_object
bpy.ops.object.camera_add()
cam = bpy.context.active_object
sc.camera = cam
cam.data.lens = 35
cam.data.sensor_fit = "VERTICAL"
cam.data.clip_start = 0.005
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
for f, (pos, look) in ((1, cfg["look_from"]), (FRAMES, cfg["look_to"])):
    cam.location = pos
    cam.keyframe_insert("location", frame=f)
    target.location = look
    target.keyframe_insert("location", frame=f)
for o in (cam, target):
    for fc in o.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"
            k.easing = "EASE_IN_OUT"

# ---- render ----
sc.render.engine = "BLENDER_EEVEE"
ee = sc.eevee
ee.taa_render_samples = cfg["samples"]
ee.use_bloom = True
ee.bloom_threshold = 0.9
ee.bloom_intensity = 0.06
ee.bloom_radius = 5.0
ee.use_soft_shadows = True
ee.shadow_cube_size = "2048"
ee.use_volumetric_lights = True
ee.volumetric_end = 40.0
ee.light_threshold = 0.0005
ee.use_gtao = True
sc.render.resolution_x, sc.render.resolution_y = cfg["size"]
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Filmic"
sc.view_settings.look = "Medium High Contrast"
sc.render.filepath = cfg["out"]
if cfg.get("still"):
    sc.frame_set(cfg["still"])
    bpy.ops.render.render(write_still=True)
else:
    sc.frame_start, sc.frame_end = cfg.get("from", 1), cfg.get("to", FRAMES)
    # resumable: a rerun skips frames already on disk (a restart lost hours of frames once)
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    bpy.ops.render.render(animation=True)
print("SCENE_OK")
