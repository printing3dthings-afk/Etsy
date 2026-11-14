#!/usr/bin/env python3
"""Draw a print's bed face as you will see it once it is printed and turned over.

Why (2026-11-14, Brief A): the Label Tile shipped with its text on the face that prints
against the bed, drawn reading correctly from ABOVE, so the printed tile reads backwards.
Nothing in the pipeline looked at a part's underside the way a buyer does. This slices
the shipped file just above the bed (every colour part separately, so an inlay shows as
its own colour and an engraving as a hole) and draws that slice mirrored left-right:
the view from below. Text that reads correctly in this picture prints correctly.

    python3 tools/underside_view.py model.3mf [more.3mf|.stl ...] -o sheet.png [--z 0.3]

Reads Bambu (component) and PrusaSlicer (volume range) 3MFs and plain STLs. Each file
gets one panel, labelled with its path.
"""
import argparse
import io
import re
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

PALETTE = [(40, 40, 40), (214, 160, 20), (200, 70, 90), (60, 120, 200), (90, 160, 90),
           (150, 90, 190), (230, 120, 40), (120, 120, 120)]
FONT = Path(__file__).resolve().parents[1] / "fonts" / "Montserrat-Bold.ttf"


def _matrix(s):
    if not s:
        return np.eye(4)
    v = [float(x) for x in s.split()]
    m = np.eye(4)
    m[:3, :3] = np.array(v[:9]).reshape(3, 3).T
    m[:3, 3] = v[9:12]
    return m


def parts_3mf(path):
    """Every printable part of a 3MF as a trimesh, in build coordinates."""
    z = zipfile.ZipFile(path)
    models = {}
    for n in z.namelist():
        if n.lower().endswith(".model"):
            models["/" + n] = z.read(n).decode("utf-8", "replace")
    root = "/3D/3dmodel.model"
    objs = {}
    for mpath, xml in models.items():
        for m in re.finditer(r'<object\b([^>]*)>(.*?)</object>', xml, re.S):
            attrs, body = m.group(1), m.group(2)
            oid = re.search(r'\bid="(\d+)"', attrs).group(1)
            if "<mesh" in body:
                v = np.array(re.findall(r'<vertex\s+x="([^"]+)"\s+y="([^"]+)"\s+z="([^"]+)"', body), float)
                f = np.array(re.findall(r'<triangle\s+v1="(\d+)"\s+v2="(\d+)"\s+v3="(\d+)"', body), int)
                objs[(mpath, oid)] = ("mesh", v, f)
            else:
                comps = []
                for c in re.finditer(r'<component\b([^>]*)/>', body):
                    ca = c.group(1)
                    cid = re.search(r'objectid="(\d+)"', ca).group(1)
                    p = re.search(r'(?:p:)?path="([^"]+)"', ca)
                    t = re.search(r'transform="([^"]+)"', ca)
                    comps.append((p.group(1) if p else mpath, cid, _matrix(t.group(1) if t else None)))
                objs[(mpath, oid)] = ("comps", comps)
    # PrusaSlicer: one mesh object split into volumes by triangle ranges
    ranges = {}
    for cfgname in ("Metadata/Slic3r_PE_model.config",):
        if cfgname in z.namelist():
            cfg = z.read(cfgname).decode("utf-8", "replace")
            for o in re.finditer(r'<object id="(\d+)"[^>]*>(.*?)</object>', cfg, re.S):
                vols = [(int(a), int(b)) for a, b in re.findall(r'<volume firstid="(\d+)" lastid="(\d+)"', o.group(2))]
                if vols:
                    ranges[o.group(1)] = vols

    out = []

    def emit(key, T):
        o = objs.get(key)
        if o is None:
            return
        if o[0] == "mesh":
            _, v, f = o
            pieces = [f[a:b + 1] for a, b in ranges[key[1]]] if key[0] == root and key[1] in ranges else [f]
            for ff in pieces:
                m = trimesh.Trimesh(v, ff, process=False)
                m.remove_unreferenced_vertices()
                m.apply_transform(T)
                out.append(m)
        else:
            for p, cid, M in o[1]:
                emit((p, cid), T @ M)

    xml = models[root]
    for it in re.finditer(r'<item\b([^>]*)/?>', xml):
        a = it.group(1)
        oid = re.search(r'objectid="(\d+)"', a).group(1)
        t = re.search(r'transform="([^"]+)"', a)
        emit((root, oid), _matrix(t.group(1) if t else None))
    return out


def load_parts(path):
    p = Path(path)
    if p.suffix.lower() == ".3mf":
        return parts_3mf(p)
    return [trimesh.load(p, force="mesh")]


def panel(path, dz, size=560):
    parts = load_parts(path)
    z0 = min(m.bounds[0][2] for m in parts)
    lo = np.min([m.bounds[0][:2] for m in parts], axis=0)
    hi = np.max([m.bounds[1][:2] for m in parts], axis=0)
    span = max(hi - lo) or 1.0
    s = (size - 40) / span
    img = Image.new("RGB", (size, size + 40), "white")
    d = ImageDraw.Draw(img)

    def px(x, y):
        # mirrored left-right: the view from below
        return (20 + (hi[0] - x) * s, 20 + (hi[1] - y) * s)

    n_shapes = 0
    for k, m in enumerate(parts):
        if m.bounds[0][2] > z0 + dz:
            continue
        try:
            sec = m.section(plane_origin=[0, 0, z0 + dz], plane_normal=[0, 0, 1])
        except Exception:
            sec = None
        if sec is None:
            continue
        try:
            p2, _ = sec.to_2D(to_2D=np.eye(4))
        except Exception:
            continue
        col = PALETTE[k % len(PALETTE)]
        for g in p2.polygons_full:
            n_shapes += 1
            d.polygon([px(x, y) for x, y in g.exterior.coords], fill=col)
            for h in g.interiors:
                d.polygon([px(x, y) for x, y in h.coords], fill="white")
    f = ImageFont.truetype(str(FONT), 15)
    d.text((10, size + 8), f"{path}  ({len(parts)} parts, {n_shapes} shapes at z+{dz})", font=f, fill=(20, 20, 20))
    return img


# ---- reading an OBC mark from the geometry (2026-11-14) ----------------------------
# Scott's convention (tests/test_obc_mark_reading.py): the mark reads OBC, upright, when
# the piece is tipped back to look underneath (front edge, -y, away from you). From the
# slice as seen from ABOVE that means: flip y, then O left, C right, B's spine left and
# its bigger bowl at the bottom.
def _glyph_rings(polys):
    """(ring, holes) for every small closed shape: an inlay's letters are polygons, an
    engraving's letters are holes in a bigger polygon (with their counters as islands)."""
    from shapely.geometry import Polygon
    out = []
    for g in polys:
        out.append((g.exterior, len(g.interiors)))
        for r in g.interiors:
            rp = Polygon(r)
            out.append((r, sum(1 for h in polys if h is not g and rp.contains(h.representative_point()))))
    return out


def _b_spine_left_bottom_bigger(ring, px=30):
    from shapely.geometry import Polygon
    from shapely import contains_xy
    P = Polygon(ring)
    x0, y0, x1, y1 = P.bounds
    xs = np.arange(x0, x1, 1 / px)
    ys = np.arange(y1, y0, -1 / px)                       # row 0 = top
    X, Y = np.meshgrid(xs, ys)
    b = contains_xy(P, X, Y)
    h, w = b.shape
    k = max(1, w // 8)
    spine_left = b[:, :k].mean() > b[:, -k:].mean()

    def reach(rows):
        cols = [np.where(r)[0] for r in rows if r.any()]
        return np.mean([c.max() if spine_left else w - 1 - c.min() for c in cols])
    return spine_left, reach(b[int(h * 0.62):]) > reach(b[: int(h * 0.38)])


def obc_marks(path, dz=0.3):
    """Every OBC mark on the bed face, as 'correct' (reads upright tipped back),
    'upside down' (reads only turned side to side) or 'mirrored' (never reads)."""
    from shapely.geometry import Polygon
    found = []
    parts = load_parts(path)
    z0 = min(m.bounds[0][2] for m in parts)
    for m in parts:
        if m.bounds[0][2] > z0 + dz:
            continue
        try:
            p2, _ = m.section(plane_origin=[0, 0, z0 + dz], plane_normal=[0, 0, 1]).to_2D(to_2D=np.eye(4))
        except Exception:
            continue
        rings = _glyph_rings(list(p2.polygons_full))
        for ring, holes in rings:
            if holes != 2:
                continue
            P = Polygon(ring)
            bx0, by0, bx1, by1 = P.bounds
            bw, bh = bx1 - bx0, by1 - by0
            if not (1.5 < bh < 30 and bw < 1.5 * bh):
                continue
            cy, cx = (by0 + by1) / 2, (bx0 + bx1) / 2
            nb = []
            for r2, h2 in rings:
                Q = Polygon(r2)
                if Q.equals(P) or h2 not in (0, 1):
                    continue
                qx0, qy0, qx1, qy1 = Q.bounds
                qcx, qcy = (qx0 + qx1) / 2, (qy0 + qy1) / 2
                if abs((qy1 - qy0) - bh) < 0.25 * bh and abs(qcy - cy) < 0.3 * bh and 0.4 * bw < abs(qcx - cx) < 2.2 * bw:
                    nb.append((qcx, h2))
            left = [h for x, h in nb if x < cx]
            right = [h for x, h in nb if x > cx]
            if len(left) != 1 or len(right) != 1 or sorted(left + right) != [0, 1]:
                continue
            # tipped back: y flips, x stays
            o_left = left[0] == 1
            spine_left, bottom_bigger = _b_spine_left_bottom_bigger(ring)
            bottom_bigger_tb = not bottom_bigger
            if o_left and spine_left and bottom_bigger_tb:
                v = "correct"
            elif (not o_left) and (not spine_left) and (not bottom_bigger_tb):
                v = "upside down"
            else:
                v = "mirrored"
            found.append({"verdict": v, "at": (round(cx, 1), round(cy, 1)), "height": round(bh, 1)})
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--z", type=float, default=0.3, help="height above the bed to slice (default 0.3)")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--marks", action="store_true", help="also print each OBC mark's verdict")
    a = ap.parse_args()
    if a.marks:
        for f in a.files:
            try:
                ms = obc_marks(f, a.z)
            except Exception as e:
                ms = [{"verdict": f"error: {e}"}]
            print(f"{f}: " + (", ".join(m["verdict"] for m in ms) if ms else "no OBC mark"))
    panels = []
    for f in a.files:
        try:
            panels.append(panel(f, a.z))
        except Exception as e:
            im = Image.new("RGB", (560, 600), "white")
            ImageDraw.Draw(im).text((10, 280), f"{f}: {e}"[:80], fill="red")
            panels.append(im)
    cols = min(a.cols, len(panels))
    rows = (len(panels) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 560, rows * 600), "white")
    for i, p in enumerate(panels):
        sheet.paste(p, ((i % cols) * 560, (i // cols) * 600))
    sheet.save(a.out)
    print(f"{len(panels)} panels -> {a.out}")


if __name__ == "__main__":
    main()
