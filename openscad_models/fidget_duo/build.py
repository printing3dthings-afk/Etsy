from pathlib import Path
import subprocess,concurrent.futures,json,hashlib
import trimesh
R=Path(__file__).resolve().parent
work=R/'work';work.mkdir(exist_ok=True)
source_hash=hashlib.sha256((R/'Fidget_Duo.scad').read_bytes()+(R/'OBC.svg').read_bytes()).hexdigest()
parts=['gecko_head']+['segment_'+str(i) for i in range(6)]
def build(p):
 path=work/(p+'.stl');which='gecko_segment' if p.startswith('segment_') else p
 marker=work/(p+'.source_hash')
 if path.exists() and marker.exists() and marker.read_text()==source_hash:
  m=trimesh.load(path);assert m.is_watertight and len(m.split())==1
  return p,{'watertight':True,'bodies':1,'dimensions_mm':m.extents.tolist(),'volume_mm3':m.volume}
 cmd=['openscad','--export-format','binstl','-o',str(path),'-D',f'part="{which}"']
 if p.startswith('segment_'):cmd+=['-D','segment_id='+p.split('_')[1]]
 r=subprocess.run(cmd+[str(R/'Fidget_Duo.scad')],capture_output=True,text=True)
 assert r.returncode==0,r.stderr
 m=trimesh.load(path);pieces=m.split();expected=1
 print(p,'bodies',len(pieces),'watertight',m.is_watertight,'mm',m.extents.round(2),flush=True)
 assert m.is_watertight and m.is_winding_consistent and len(pieces)==expected,(p,len(pieces),r.stderr)
 marker.write_text(source_hash)
 return p,{'watertight':True,'consistent_winding':True,'bodies':len(pieces),'dimensions_mm':m.extents.tolist(),'volume_mm3':m.volume}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(build,parts))
gecko=trimesh.util.concatenate([trimesh.load(work/(p+'.stl')) for p in parts]);assert len(gecko.split())==7
gecko.export(R/'gecko.stl');results['gecko']={'watertight':bool(gecko.is_watertight),'bodies':7,'dimensions_mm':gecko.extents.tolist(),'volume_mm3':gecko.volume}
for p in ['gecko_coupon','mushroom_base','mushroom_cap','switch_coupon','stem_coupon']:
 r=subprocess.run(['openscad','--export-format','binstl','-o',str(R/(p+'.stl')),'-D',f'part="{p}"',str(R/'Fidget_Duo.scad')],capture_output=True,text=True);assert r.returncode==0,r.stderr
 m=trimesh.load(R/(p+'.stl'));assert m.is_watertight and m.is_winding_consistent
 results[p]={'watertight':True,'bodies':len(m.split()),'dimensions_mm':m.extents.tolist(),'volume_mm3':m.volume}
(R/'Geometry_Report.json').write_text(json.dumps(results,indent=2))
