from pathlib import Path
import json,hashlib,zipfile
import trimesh
R=Path(__file__).resolve().parent
parts=['gecko','gecko_coupon','mushroom_base','mushroom_cap','switch_coupon','stem_coupon']
report={}
for n in parts:
 m=trimesh.load(R/(n+'.stl'));count=len(m.split());expected=7 if n=='gecko' else 2 if n=='gecko_coupon' else 1
 assert m.is_watertight and m.is_winding_consistent and count==expected,(n,count)
 report[n]={'watertight':True,'consistent_winding':True,'bodies':count,'dimensions_mm':m.extents.tolist(),'volume_mm3':m.volume}
(R/'Geometry_Report.json').write_text(json.dumps(report,indent=2))
files=[p for p in sorted(R.iterdir()) if p.is_file() and p.suffix in ['.scad','.svg','.py','.md','.stl','.3mf','.json','.png','.usdz','.txt'] and p.name!='SHA256SUMS.txt']
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files));files.append(R/'SHA256SUMS.txt')
archive=R.parent/'Fidget_Duo_Prototype_Package.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,'Fidget_Duo/'+p.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;print('Verified archive:',len(z.namelist()),'files',archive.stat().st_size,'bytes')
