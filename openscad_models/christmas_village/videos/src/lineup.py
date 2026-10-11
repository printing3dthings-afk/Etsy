import bpy, sys, math, json, os, mathutils
cfg = json.loads(open(sys.argv[sys.argv.index('--')+1]).read())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = cfg['res']; sc.render.film_transparent = True
sc.render.image_settings.color_mode = 'RGBA'
e = sc.eevee; e.taa_render_samples = cfg.get('samples', 48); e.use_gtao = True; e.gtao_distance = 6; e.use_soft_shadows = True
e.shadow_cube_size = '2048'; e.shadow_cascade_size = '4096'
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'Medium High Contrast'
def lin(h):
    h = h.lstrip('#'); rgb = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    return [(c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4) for c in rgb]
mats = {}
def mat(h):
    if h not in mats:
        m = bpy.data.materials.new(h); m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*lin(h), 1); b.inputs['Roughness'].default_value = 0.55
        mats[h] = m
    return mats[h]
blds = []
for parts in cfg['buildings']:
    objs = []
    for path, h in parts:
        bpy.ops.import_mesh.stl(filepath=path); o = bpy.context.selected_objects[0]; o.data.materials.append(mat(h)); objs.append(o)
    mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
    for o in objs:
        for v in o.data.vertices:
            mn = mathutils.Vector(map(min, mn, v.co)); mx = mathutils.Vector(map(max, mx, v.co))
    root = bpy.data.objects.new('b', None); sc.collection.objects.link(root)
    c = (mn+mx)/2
    for o in objs: o.location = (-c.x, -c.y, -mn.z); o.parent = root
    blds.append((root, mx-mn))
# two staggered rows, tallest at the back, real relative scale (mm)
blds.sort(key=lambda b: -b[1].z)
half = (len(blds)+1)//2; rows = [blds[:half], blds[half:]]
gap = cfg.get('gap', 10); ydep = [cfg.get('back', 70), 0]
W = 0
for r, row in enumerate(rows):
    width = sum(b[1].x for b in row) + gap*(len(row)-1); x = -width/2 + (0 if r == 0 else cfg.get('stagger', 0))
    # put the tallest in the middle of the back row
    order = sorted(row, key=lambda b: -b[1].z); mid = []
    for i, b in enumerate(order):
        if i % 2: mid.append(b)
        else: mid.insert(0, b)
    for b in mid:
        b[0].location = (x + b[1].x/2, ydep[r], 0); x += b[1].x + gap
    W = max(W, width)
Hmax = max(b[1].z for b in blds)
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=W*1.4, fill_type='NGON', location=(0, 30, 0))
g = bpy.context.object; g.data.materials.append(mat('#E4E9F2'))
def area(name, loc, energy, color, size):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color; l.size = size
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (mathutils.Vector((0, 30, Hmax*0.4)) - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
k = W/100
area('key', (-180*k, -200*k, 260*k), 3.0e6*k*k, (1.0, 0.86, 0.7), 140*k)
area('rim', (160*k, 220*k, 160*k), 2.0e6*k*k, (0.55, 0.7, 1.0), 120*k)
area('fill', (220*k, -140*k, 80*k), 0.6e6*k*k, (0.8, 0.85, 1.0), 160*k)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.06, 0.10, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = cfg.get('lens', 50)
tgt = mathutils.Vector((0, 30, Hmax*cfg.get('aim', 0.35)))
a = math.radians(cfg.get('az', -18)); el = math.radians(cfg.get('elev', 16)); dist = cfg.get('dist', 2.2)*W
cam.location = tgt + mathutils.Vector((math.sin(a)*math.cos(el), -math.cos(a)*math.cos(el), math.sin(el)))*dist
cam.rotation_euler = (tgt-cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = cfg['out']; bpy.ops.render.render(write_still=True)
