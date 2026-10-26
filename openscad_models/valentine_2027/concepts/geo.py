"""Concept massing for the Valentine's 2027 forms (2026-10-26).

Concepts only: quick, honest massing to choose a form from, built with
manifold3d in Python and rendered in Blender. Per the brief, no OpenSCAD is
written until Scott has picked; the picked forms are then modelled properly
(and gated) in OpenSCAD. Nothing here is a print file.

Units mm, z up, the front faces -y.
"""
import math
from pathlib import Path

import manifold3d as m3
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box as sbox
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[3]
M = m3.Manifold
m3.set_circular_segments(64)


# ---- 2D ---------------------------------------------------------------------------------
def heart(w, cx=0.0, cy=0.0, n=120):
    """A heart w wide, centred on (cx, cy), point down."""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    s = w / 32.0
    p = Polygon(np.c_[x * s, y * s]).buffer(0)
    b = p.bounds
    return affinity.translate(p, cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)


def heart_curve(w, cx=0.0, cy=0.0, n=160, t0=0.0, t1=2 * math.pi):
    t = np.linspace(t0, t1, n)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    s = w / 32.0
    return LineString(np.c_[x * s + cx, y * s + cy + 2.5 * s])


def arch(w, h):
    """A round-headed window w wide, h tall to its crown, foot on y = 0."""
    r = w / 2
    return unary_union([sbox(-r, 0, r, h - r), Point(0, h - r).buffer(r, 48)])


def stroke(coords, w):
    return LineString(coords).buffer(w / 2, cap_style=1, join_style=1)


def text2d(s, h, font="PlayfairDisplay-Bold.ttf", px=24):
    """Text as polygons, cap height ~h mm, centred on the origin, reading
    left to right as seen from the face it is laid on."""
    f = ImageFont.truetype(str(ROOT / "fonts" / font), int(px * 4))
    try:                                   # a variable font loads its Thin master by default
        f.set_variation_by_name("Bold")
    except (OSError, ValueError):
        pass
    l, t, r, b = f.getbbox(s)
    im = Image.new("L", (r - l + 8, b - t + 8), 0)
    ImageDraw.Draw(im).text((4 - l, 4 - t), s, font=f, fill=255)
    a = np.array(im) > 127
    rects = []
    for y in range(a.shape[0]):
        row = a[y]
        d = np.diff(np.r_[0, row.astype(int), 0])
        for x0, x1 in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            rects.append(sbox(x0, -y - 1, x1, -y))
    g = unary_union(rects).simplify(0.6)
    b = g.bounds
    k = h / (b[3] - b[1])
    g = affinity.scale(g, k, k, origin=(0, 0))
    b = g.bounds
    return affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)


def cs(g):
    """shapely -> manifold CrossSection"""
    if g.is_empty:
        return m3.CrossSection()
    polys = [g] if g.geom_type == "Polygon" else [p for p in g.geoms if p.geom_type == "Polygon"]
    cont = []
    for p in polys:
        p = orient(p)
        cont.append(np.array(p.exterior.coords)[:-1])
        cont += [np.array(r.coords)[:-1] for r in p.interiors]
    return m3.CrossSection(cont, m3.FillRule.EvenOdd)


# ---- 3D ---------------------------------------------------------------------------------
def ext(g, h, z0=0.0):
    return M.extrude(cs(g), h).translate([0, 0, z0])


def box(x0, y0, z0, x1, y1, z1):
    return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(r, h, z0=0.0, r2=None, fn=96):
    return M.cylinder(h, r, r if r2 is None else r2, fn).translate([0, 0, z0])


def prism_y(g, y0, y1):
    """A 2D shape in (x, z) extruded along y from y0 to y1."""
    return M.extrude(cs(g), y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def prism_x(g, x0, x1):
    """A 2D shape in (y, z) extruded along x from x0 to x1."""
    return M.extrude(cs(g), x1 - x0).rotate([90, 0, 90]).translate([x0, 0, 0])


def on_face(g, origin, angle, d0, d1):
    """Lay a 2D shape (u along the face, v up) on a vertical face whose outward
    normal points at `angle` degrees (0 = -y, the front; 90 = +x), with the
    face plane through `origin` (x, y) and spanning d0..d1 along the normal."""
    s = M.extrude(cs(g), d1 - d0).translate([0, 0, d0])        # z = out of the face
    s = s.rotate([90, 0, 0])                                     # z -> -y, v -> z
    return s.rotate([0, 0, angle]).translate([origin[0], origin[1], 0])


def radial(g, r, d0, d1, angle=0.0, fn=128):
    """Wrap a flat drawing (u = arc length along the face, v up) round a
    cylinder of radius r, from r + d0 to r + d1, centred at `angle` (0 = front)."""
    out = M()
    if g.is_empty:
        return out
    u0, _, u1, _ = g.bounds
    step = 2 * math.pi * r / fn
    k = math.floor(u0 / step)
    while k * step < u1:
        a, b = k * step, (k + 1) * step
        piece = g.intersection(sbox(a - 0.01, -1e3, b + 0.01, 1e3))
        if not piece.is_empty:
            um = (a + b) / 2
            piece = affinity.translate(piece, -um, 0)
            ang = angle + math.degrees(um / r)
            out += on_face(piece, (r * math.sin(math.radians(ang)), -r * math.cos(math.radians(ang))), ang, d0, d1)
        k += 1
    return out


def save(parts, outdir, stem):
    """Write each non-empty part as STL; return {part: path}."""
    outdir.mkdir(parents=True, exist_ok=True)
    res = {}
    for name, man in parts.items():
        if man is None or man.is_empty():
            continue
        mesh = man.to_mesh()
        tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
        p = outdir / f"{stem}_{name}.stl"
        tm.export(p)
        res[name] = p
    return res
