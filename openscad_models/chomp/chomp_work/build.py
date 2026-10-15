import bpy, math, json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent.parent; O=R/'Chomp';O.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def bevel(o,r,segments=8):
 active(o);m=o.modifiers.new('Soft manufactured edges','BEVEL');m.width=r;m.segments=segments;bpy.ops.object.modifier_apply(modifier=m.name)
def box(n,loc,dims,r):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dims;active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if r:bevel(o,r)
 return o
def ell(n,loc,dims):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=loc);o=bpy.context.object;o.name=n;o.scale=dims;active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
def boolean(o,c,operation='DIFFERENCE'):
 active(o);m=o.modifiers.new(operation,'BOOLEAN');m.operation=operation;m.solver='EXACT';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
body=box('Chomp_body',(0,0,109),(164,78,178),23)
mouth=box('mouth_cut',(0,-34,91),(119,112,111),20);boolean(body,mouth)
bevel(body,3,5)
for s in [-1,1]:
 foot=box('foot',(s*52,-26,13),(58,69,26),11)
 for dx in [-10,9]:
  groove=box('toe_groove',(s*52+dx,-60,11),(2.5,13,19),1.2);boolean(foot,groove)
 boolean(body,foot,'UNION')
 arm=ell('arm',(s*81,-4,117),(12,16,30));arm.rotation_euler[1]=s*math.radians(-12);boolean(body,arm,'UNION')
# Tall rear storage is part of the silhouette, with a 3.5 mm floor and walls.
pocket=box('rear_pocket',(0,54,112),(137,60,166),12)
inside=box('pocket_inside',(0,54,119),(130,53,173),9);boolean(pocket,inside);boolean(body,pocket,'UNION')
# Continuous tongue surface, curved around its front edge and rising gently at the back.
verts=[]
profile=[(-63,34),(-63,44),(-51,46),(-27,48),(0,64),(15,66),(15,34)]
for x in [-54,54]:verts.extend([(x,y,z) for y,z in profile])
n=len(profile);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('tongue_surface');mesh.from_pydata(verts,[],faces);mesh.update();tongue=bpy.data.objects.new('Chomp_tongue',mesh);bpy.context.collection.objects.link(tongue);bevel(tongue,5,8)
slot=box('cable_slot',(0,-63,40),(12,22,25),3);boolean(tongue,slot)
for s in [-1,1]:
 lip=box('retaining_lip',(s*30,-59,47),(45,9,12),4);boolean(tongue,lip,'UNION')
# Domed eyes seated into the forehead instead of flat discs.
items=[(body,(.68,.20,.13)),(tongue,(.075,.12,.20))]
for s in [-1,1]:
 eye=ell('Chomp_eye_'+str(s),(s*47,-34,169),(18,11,22));items.append((eye,(.95,.91,.80)))
 pupil=ell('Chomp_pupil_'+str(s),(s*47+4,-44,170),(8,3.5,10));items.append((pupil,(.022,.028,.03)))
 highlight=ell('Chomp_glint_'+str(s),(s*47+6,-47,174),(2.2,1.2,2.7));items.append((highlight,(1,1,1)))
# Approved SVG cutter, recessed in the hidden left-foot underside.
bpy.ops.wm.stl_import(filepath=str(R/'chomp_work/brand.stl'));brand=bpy.context.object;brand.location=(-52,-26,0);boolean(body,brand)
def mat(n,rgb):
 m=bpy.data.materials.new(n);m.diffuse_color=(*rgb,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.55;return m
scene=[]
for o,rgb in items:
 o.data.materials.append(mat(o.name,rgb))
 for p in o.data.polygons:p.use_smooth=True
 o.data.set_sharp_from_angle(angle=math.radians(40))
 active(o);bpy.ops.wm.stl_export(filepath=str(O/(o.name+'.stl')),export_selected_objects=True)
 scene.append({'name':o.name,'rgb':rgb})
(O/'scene.json').write_text(json.dumps(scene))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Chomp_Design.blend'))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.resolution_x=1300;sc.render.resolution_y=1300;sc.render.resolution_percentage=100;sc.world.color=(.65,.65,.65)
bpy.ops.mesh.primitive_plane_add(size=20000,location=(0,0,-.1));bpy.context.object.data.materials.append(mat('Backdrop',(.86,.84,.80)))
target=Vector((0,4,98))
for loc,power,size in [((-200,-250,360),2100000,260),((220,-20,250),1200000,220),((0,260,310),1800000,200)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=292
for name,loc in [('Preview',(245,-440,270)),('Rear',(240,410,280))]:
 cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/('Chomp_'+name+'.png'));bpy.ops.render.render(write_still=True)
