"""Crop a mesh to a box and render it (a close-up for reviewing a face).
    python3 crop_render.py in.stl out.png x0 x1 y0 y1 z0 z1 azimuth"""
import subprocess, sys
from pathlib import Path
import numpy as np, trimesh
src, out = sys.argv[1], sys.argv[2]
b = np.array(sys.argv[3:9], float).reshape(3, 2)
az = sys.argv[9] if len(sys.argv) > 9 else "-20"
m = trimesh.load(src)
c = m.triangles_center
keep = np.all((c >= b[:, 0]) & (c <= b[:, 1]), axis=1)
sub = m.submesh([np.where(keep)[0]], append=True)
tmp = Path(out).with_suffix(".crop.stl")
sub.export(tmp)
subprocess.run([sys.executable, str(Path(__file__).resolve().parents[4] / "tools" / "blender_render.py"), str(tmp),
                "--color", "0.72,0.68,0.62", "--azimuth", az, "--elevation", "4", "--samples", "64",
                "--resolution", "900", "--no-cache", "-o", out], check=True)
tmp.unlink()        # ~100 MB each: left behind, a few dozen filled the disk
