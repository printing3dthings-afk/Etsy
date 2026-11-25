"""Top-down flat view of a camera sign's two colour parts (2026-11-25): each part's
cross-section, filled in its colour, at 20 px/mm. A check of how the letters read, not a
photo or a render of the print.

    python3 flat_view.py out.png base.stl letters.stl [base_hex letters_hex]
"""
import sys
import trimesh
from PIL import Image, ImageDraw

out, base, letters = sys.argv[1:4]
cols = sys.argv[4:6] or ["#1C1C1F", "#F28C28"]
PX = 20
meshes = [trimesh.load(p, force="mesh") for p in (base, letters)]
lo = meshes[0].bounds[0]; hi = meshes[0].bounds[1]
W, H = int((hi[0] - lo[0]) * PX) + 40, int((hi[1] - lo[1]) * PX) + 40
im = Image.new("RGB", (W, H), "#B9A68A")
d = ImageDraw.Draw(im)
for m, c in zip(meshes, cols):
    z = (m.bounds[0][2] + m.bounds[1][2]) / 2
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    p2, _ = sec.to_planar(to_2D=trimesh.transformations.translation_matrix([0, 0, -z]))
    for poly in p2.polygons_full:
        f = lambda pts: [((x - lo[0]) * PX + 20, H - ((y - lo[1]) * PX + 20)) for x, y in pts]
        d.polygon(f(poly.exterior.coords), fill=c)
        for h in poly.interiors:
            d.polygon(f(h.coords), fill="#1C1C1F" if c != cols[0] else "#B9A68A")
im.save(out)
