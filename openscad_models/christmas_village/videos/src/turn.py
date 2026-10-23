import bpy, sys, math, json, os
argv = sys.argv[sys.argv.index('--')+1:]
cfg = json.loads(open(argv[0]).read())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = cfg.get('engine', 'BLENDER_EEVEE')
sc.render.resolution_x, sc.render.resolution_y = cfg['res']
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
if sc.render.engine == 'BLENDER_EEVEE':
    e = sc.eevee; e.taa_render_samples = cfg.get('samples', 32); e.use_gtao = True; e.gtao_distance = 6; e.use_soft_shadows = True; e.shadow_cube_size='2048'; e.shadow_cascade_size='2048'
    e.use_bloom = False
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'Medium High Contrast'
objs = []
for path, hexc in cfg['parts']:
    bpy.ops.import_mesh.stl(filepath=path)
    o = bpy.context.selected_objects[0]
    h = hexc.lstrip('#'); rgb = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    lin = [(c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4) for c in rgb]
    m = bpy.data.materials.new('m'); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*lin, 1); b.inputs['Roughness'].default_value = 0.55
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = False
    objs.append(o)
# center and scale to 10 units tall
import mathutils
mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
for o in objs:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co; mn = mathutils.Vector(map(min, mn, w)); mx = mathutils.Vector(map(max, mx, w))
c = (mn+mx)/2; s = 10.0/max(mx.z-mn.z, (mx.x-mn.x)*0.8, (mx.y-mn.y)*0.8)
root = bpy.data.objects.new('root', None); sc.collection.objects.link(root)
for o in objs:
    o.location -= mathutils.Vector((c.x, c.y, mn.z)); o.parent = root
root.scale = (s, s, s)
if cfg.get('ground_only'):
    for o in objs: o.hide_render = True
H = (mx.z-mn.z)*s
# snowy ground disc (shadow catcher-ish: real white ground)
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=14, fill_type='NGON', location=(0,0,0))
g = bpy.context.object; gm = bpy.data.materials.new('g'); gm.use_nodes = True
gb = gm.node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (0.85,0.88,0.95,1); gb.inputs['Roughness'].default_value = 0.9
g.data.materials.append(gm); g.is_shadow_catcher = True if hasattr(g, 'is_shadow_catcher') else False
if not cfg.get('ground', True): g.hide_render = True
# lights: warm key, cool rim, fill
def area(name, loc, energy, color, size):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color; l.size = size
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    d = mathutils.Vector((0,0,H*0.45)) - mathutils.Vector(loc); o.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
area('key', (-14,-16,18), 9000, (1.0,0.86,0.7), 10)
area('rim', (12,14,12), 6000, (0.55,0.7,1.0), 8)
area('fill', (16,-10,6), 1800, (0.8,0.85,1.0), 12)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05,0.06,0.10,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = cfg.get('lens', 60)
dist = cfg.get('dist', 34); elev = math.radians(cfg.get('elev', 14)); tgt = mathutils.Vector((0,0,H*cfg.get('aim', 0.45)))
n = cfg['frames']; a0 = math.radians(cfg.get('az0', -40)); a1 = math.radians(cfg.get('az1', 40))
out = cfg['out']; os.makedirs(out, exist_ok=True)
for i in range(cfg.get('start', 0), n):
    p = os.path.join(out, '%04d.png' % i)
    if os.path.exists(p): continue
    t = i/max(1, n-1); t = 0.5-0.5*math.cos(math.pi*t) if cfg.get('ease', True) else t
    a = a0+(a1-a0)*t
    cam.location = tgt + mathutils.Vector((math.sin(a)*math.cos(elev), -math.cos(a)*math.cos(elev), math.sin(elev)))*dist
    cam.rotation_euler = (tgt-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath = p; bpy.ops.render.render(write_still=True)
