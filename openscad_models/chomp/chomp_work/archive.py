from pathlib import Path
import hashlib, json, zipfile
root=Path(__file__).resolve().parent.parent
out=root/'Chomp'
files=[p for p in sorted(out.iterdir()) if p.is_file() and p.suffix in ['.blend','.png','.usdz','.md','.json']]
files += [root/'chomp_work'/n for n in ['build.py','preview.py','brand.scad','archive.py']]
files += [root/'OBC.svg']
for p in files:assert p.stat().st_size>0,p
report=json.loads((out/'Geometry_Report.json').read_text())
assert all(v['watertight'] and v['winding_consistent'] for v in report.values())
with zipfile.ZipFile(out/'Chomp_Phone_View.usdz') as z:assert z.testzip() is None
archive=root/'Chomp_Design_Review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(root))
 z.writestr('SHA256SUMS.txt',''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in files))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;print(json.dumps({'files':z.namelist(),'bytes':archive.stat().st_size}))
