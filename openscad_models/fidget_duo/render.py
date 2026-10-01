import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;W=R/'work'
def material(n,rgb):
 m=bpy.data.materials.new(n);m.diffuse_color=(*rgb,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.6;return m
for title,items in json.loads((W/'scenes.json').read_text()).items():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for item in items:
  bpy.ops.wm.stl_import(filepath=str(W/(item['name']+'_view.stl')));o=bpy.context.object;o.data.materials.append(material(item['name'],item['rgb']))
  o.data.materials.append(material('Paint fill',(.86,.82,.70) if item['name']=='mushroom_cap' else (.025,.03,.03)))
  for p in o.data.polygons:
   p.use_smooth=True;c=p.center
   if item['name']=='gecko_head' and c.z>12 and min((c-Vector((-13,s*13,15))).length for s in [-1,1])<3.06:p.material_index=1
   if item['name']=='mushroom_cap':
    centres=[Vector((14*math.cos(math.radians(a)),14*math.sin(math.radians(a)),39.4)) for a in [20,140,260]]+[Vector((0,0,41.5))]
    if min(abs((c-q).length-r) for q,r in zip(centres,[4.2,4.2,4.2,4]))<.08:p.material_index=1
  o.data.set_sharp_from_angle(angle=math.radians(35))
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.resolution_x=1300;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.world.color=(.6,.6,.6)
 bpy.ops.mesh.primitive_plane_add(size=10000,location=(0,0,-.15));bpy.context.object.data.materials.append(material('Background',(.86,.84,.80)))
 isgecko=title=='Pebble_Gecko';target=Vector((72,17,7) if isgecko else (0,0,20));size=245 if isgecko else 85
 for delta,power,area in [((-100,-130,220),1300000,200),((180,30,200),1000000,180),((0,180,230),1400000,150)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(delta));o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=area;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add(location=target+Vector((-175,-225,220) if isgecko else (70,-110,65)));cam=bpy.context.object;sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=size;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 sc.render.filepath=str(R/(title+'_Preview.png'));bpy.ops.render.render(write_still=True)
