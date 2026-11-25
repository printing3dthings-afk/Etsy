#!/usr/bin/env python3
"""Instagram QR tile for the camera-sign plate (2026-11-25).

Scott: "I want all 3 on one plate to print. Make the prime tower an object and make it a QR
code to the instagram." The plate's single colour change (near-black base, orange top) is the
same one the signs make, so the tile needs no extra changes and the prime tower is turned off.

Two colours by height, like the signs: a near-black base 0 to THICK - RAISE, and an orange top
RAISE thick that is the code's LIGHT part (its background and quiet zone). The dark modules
are holes in the orange showing the black underneath: dark on light, the polarity every phone
camera reads (inverted codes are hit and miss).

    python3 qr_tile.py            writes camera_sign_qr_base.stl, camera_sign_qr_letters.stl, flat_view.png
"""
from pathlib import Path

import numpy as np
import segno
import shapely
import trimesh
from shapely.geometry import box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
URL = "https://instagram.com/onbrandcraftz2026"
MOD = 2.0         # module size, mm: five beads a module, so every hole and island prints
                  # with room to spare, and the tile still fits the plate beside three signs
QUIET = 4         # quiet zone, modules (the standard's minimum)
FRAME = 2.0       # black rim round the quiet zone
CORNER = 3.0
THICK, RAISE = 2.4, 0.8   # the signs' numbers
GROW = 0.08       # each dark hole drawn this much bigger a side: the orange bead bulges into
                  # it, and diagonal dark neighbours then meet instead of pinching to a point


def matrix():
    q = segno.make(URL, error="m", micro=False)
    return q, np.array([[bool(v) for v in row] for row in q.matrix])


def shapes():
    q, m = matrix()
    n = m.shape[0]
    side = (n + 2 * QUIET) * MOD
    dark = unary_union([box(c * MOD - GROW, (n - 1 - r) * MOD - GROW, (c + 1) * MOD + GROW, (n - r) * MOD + GROW)
                        for r in range(n) for c in range(n) if m[r, c]])
    dark = shapely.affinity.translate(dark, QUIET * MOD - side / 2, QUIET * MOD - side / 2)
    light = box(-side / 2, -side / 2, side / 2, side / 2).difference(dark)
    o = side / 2 + FRAME
    tile = box(-o + CORNER, -o + CORNER, o - CORNER, o - CORNER).buffer(CORNER, quad_segs=8)
    return q, n, tile, light


def extrude(poly, z0, h):
    parts = [trimesh.creation.extrude_polygon(p, h) for p in getattr(poly, "geoms", [poly])]
    m = trimesh.util.concatenate(parts)
    m.apply_translation([0, 0, z0])
    return m


def flat_view(tile, light, out, px=12):
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = tile.bounds
    W, H = int((x1 - x0) * px) + 80, int((y1 - y0) * px) + 80
    im = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(im)
    f = lambda pts: [((x - x0) * px + 40, H - ((y - y0) * px + 40)) for x, y in pts]
    d.polygon(f(tile.exterior.coords), fill="#1C1C1F")
    for p in getattr(light, "geoms", [light]):
        d.polygon(f(p.exterior.coords), fill="#F28C28")
        for h in p.interiors:
            d.polygon(f(h.coords), fill="#1C1C1F")
    im.save(out)
    return im


if __name__ == "__main__":
    q, n, tile, light = shapes()
    print(f"{URL}: version {q.version}, {q.error} error correction, {n} x {n} modules")
    print(f"tile {tile.bounds[2] - tile.bounds[0]:.1f} mm square, module {MOD} mm")
    extrude(tile, 0, THICK - RAISE).export(HERE / "camera_sign_qr_base.stl")
    extrude(light, THICK - RAISE, RAISE).export(HERE / "camera_sign_qr_letters.stl")
    flat_view(tile, light, HERE / "flat_view.png")
