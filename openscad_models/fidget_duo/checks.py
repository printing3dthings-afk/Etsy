from pathlib import Path
import json,math,sys,os,subprocess,concurrent.futures
import numpy as np,trimesh
R=Path(__file__).resolve().parent;W=R/'work'
def intersect(a,b):
 m=trimesh.boolean.intersection([a,b],engine='manifold');return max(0.,float(m.volume)) if len(m.faces) else 0.
def movement():
 meshes=[trimesh.load(W/'gecko_head.stl')]+[trimesh.load(W/f'segment_{i}.stl') for i in range(6)]
 r={};stationary=[]
 for i in range(6):
  p=[18+26*i,0,4];a,b=meshes[i:i+2];values={}
  for degrees in [0,5,10,15,20]:
   moved=b.copy();moved.apply_transform(trimesh.transformations.rotation_matrix(math.radians(degrees),[0,0,1],p));values[str(degrees)]=intersect(a,moved)
  r[f'joint_{i+1}_yaw_collision_mm3']=values
  for distance in [0,.5,1,2]:
   m=b.copy();m.apply_translation([distance,0,0]);r[f'joint_{i+1}_pull_{distance}_collision_mm3']=intersect(a,m)
 for i,a in enumerate(meshes):
  for j,b in enumerate(meshes[i+1:],i+1):
   v=intersect(a,b);assert v<.01,(i,j,v)
 base=trimesh.load(R/'mushroom_base.stl');base.apply_translation([0,0,-26]);base.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]));cap=trimesh.load(R/'mushroom_cap.stl')
 for stroke in [0,1,2,3,4]:
  m=cap.copy();m.apply_translation([0,0,27.7-stroke]);v=intersect(base,m);r[f'cap_base_stroke_{stroke}_collision_mm3']=v;assert v<.01,(stroke,v)
 (R/'Movement_Report.json').write_text(json.dumps(r,indent=2));print('Movement',r,flush=True)
def slice_parts():
 candidates=[Path(os.environ['FIDGET_TOOLS_DIR'])] if 'FIDGET_TOOLS_DIR' in os.environ else [R.parent/'crescent_work/tools',R.parents[1]/'tools']
 toolroot=next((p for p in candidates if (p/'virtual_printer.py').exists()),None)
 if toolroot is None:raise RuntimeError('Set FIDGET_TOOLS_DIR to the Etsy repository tools directory')
 sys.path.insert(0,str(toolroot));from virtual_printer import slice_model,analyse
 os.environ['PATH']=os.environ.get('FIDGET_SLICER_DIR',str(R.parent/'crescent_work/runtime/PrusaSlicer-2.7.2+linux-x64-GTK3-202402291307'))+os.pathsep+os.environ['PATH']
 def one(name):
  p=R/(name+'.stl');m=trimesh.load(p);g=W/(name+'.gcode');supports=name=='mushroom_cap';extra={'perimeters':'3','top-solid-layers':'5','bottom-solid-layers':'5','fill-pattern':'gyroid'}
  if name=='switch_coupon':extra.update({'layer-height':'0.15','first-layer-height':'0.15'})
  slice_model(p,g,supports=supports,extra=extra)
  r=analyse(g,float(m.extents[2]));r['supports_enabled']=supports;r['profile_note']='Support off to preserve joints; physical bridge/clearance test required' if name.startswith('gecko') else 'Supports on inside cap recess' if supports else 'Support off; supplied orientation';(W/(name+'_slice.json')).write_text(json.dumps(r,indent=2));print(name,r,flush=True);return name,r
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:r=dict(pool.map(one,['gecko','gecko_coupon','mushroom_base','mushroom_cap','switch_coupon','stem_coupon']))
 (R/'Slice_Report.json').write_text(json.dumps(r,indent=2))
if __name__=='__main__':
 if 'slice' in sys.argv:slice_parts()
 else:movement()
