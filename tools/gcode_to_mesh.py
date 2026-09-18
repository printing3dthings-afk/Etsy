#!/usr/bin/env python3
"""Turn a viewer job payload into a real bead mesh, for offline rendering.

    python3 tools/gcode_to_mesh.py tools/viewer/jobs/vase.js -o /tmp/vase.ply
    python3 tools/gcode_to_mesh.py tools/viewer/jobs/ -d /tmp/meshes   # all of them

WHY THIS EXISTS. The web viewer draws each extrusion as a three-vertex open
tent, because it has to hold 60fps on a phone. That is the right trade for
watching a print happen and the wrong one for looking at the finished part: a
tent is one bead per 0.2mm layer, which is about a pixel on screen, and the
lighting swinging across a sub-pixel face is what makes the surface read as
sandpaper. Measured, not assumed -- see tools/viewer/README.md.

Offline there is no frame budget, so the bead can be what it actually is: a
closed, swept solid with a squashed cross-section, flat on top and bottom so
consecutive layers stack flush. Path-traced with real filtering, that renders
the way a photograph of the part does.

Input is the payload the viewer already ships rather than raw G-code, for two
reasons: those payloads are committed for all 72 plates, and building from
them guarantees the render shows exactly the same toolpath the viewer does.
Positions are quantised to 0.01mm there, which is a fortieth of a bead.

Output is binary PLY -- indexed, so roughly a third the size of the equivalent
STL, and tools/blender_render.py imports it directly.
"""
import argparse
import base64
import json
import math
import re
import struct
import sys
from pathlib import Path

import numpy as np

# Matches the viewer: sparse infill and the skirt are the two things you would
# not see on the finished part. Everything else is real surface.
DEFAULT_HIDDEN = {3, 9}

# Flat top and bottom so stacked layers meet over a real contact band, bulged
# sides so the bead reads as extruded rather than as a brick. u is across the
# bead (+-half width), v is vertical (+-half layer height).
def cross_section(sides: int, squareness: float = 4.0):
    """A bead's profile: a rounded rectangle, wider than it is tall.

    The first version tapered to half-width at the top and bottom, which put a
    groove half the bead deep between every pair of layers and made the render
    look like a woven basket rather than a printed wall. A real extrusion is
    pressed flat between the nozzle and the layer below: nearly full width for
    most of its height, rounded only at the edges. A superellipse gives that
    with one number -- 2 is an ellipse, 4 is a rounded rectangle, higher is
    squarer.
    """
    if sides < 4:
        raise ValueError("a bead needs at least 4 sides")
    e = 2.0 / squareness
    pts = []
    for i in range(sides):
        a = 2.0 * math.pi * (i + 0.5) / sides
        c, sn = math.cos(a), math.sin(a)
        pts.append((math.copysign(abs(c) ** e, c), math.copysign(abs(sn) ** e, sn)))
    return pts


def _decode(b64: str, dtype):
    return np.frombuffer(base64.b64decode(b64), dtype=dtype)


def load_payload(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"window\.__JOB_LOADED\((.*)\)\s*;?\s*$", text, re.S)
    if not m:
        raise SystemExit("%s is not a viewer job payload "
                         "(no window.__JOB_LOADED wrapper)" % path)
    return json.loads(m.group(1))


def build(payload: dict, sides: int = 8, hidden=None,
          squish: float = 1.25, widen: float = 1.04,
          squareness: float = 4.0):
    hidden = DEFAULT_HIDDEN if hidden is None else hidden
    pts = _decode(payload["pts"], np.int16).reshape(-1, 2).astype(np.float64) / 100.0
    polys = _decode(payload["polys"], np.int32).reshape(-1, 3)
    layers = payload["layers"]
    hw = float(payload.get("beadWidth", 0.42)) / 2.0 * widen

    # A bead exactly one layer tall touches its neighbour on a hairline and
    # renders as a stack of separate ribbons with daylight between them. A real
    # extrusion is pressed into the layer below and fuses: the groove stays
    # visible, the gap does not. Overlapping solids are the correct model of
    # that and cost a path tracer nothing -- there is no z-fighting in a ray
    # intersection.

    section = cross_section(sides, squareness)
    verts, faces = [], []
    # A running VERTEX count, not len(verts) -- verts holds one block of n
    # points per cross-section corner, so its length counts blocks. Using it
    # as a base index silently pointed every face at the first fifth of the
    # mesh and left the rest unreferenced: the model looked like a 22mm stub
    # of a 120mm vase while the vertex array was perfectly correct.
    nv = 0

    for li, L in enumerate(layers):
        z_top = L[0] / 100.0
        lh = float(L[5] or 0.2)
        z_ctr = z_top - lh / 2.0
        hh = lh / 2.0 * squish
        for pi in range(L[1], L[1] + L[2]):
            ptype, start, n = int(polys[pi][0]), int(polys[pi][1]), int(polys[pi][2])
            if ptype in hidden or n < 2:
                continue
            p = pts[start:start + n]
            # Miter normal per point: average the incoming and outgoing segment
            # normals so corners close instead of leaving a wedge.
            d = np.diff(p, axis=0)
            seg_len = np.hypot(d[:, 0], d[:, 1])
            seg_len[seg_len == 0] = 1.0
            nx = np.concatenate(([0.0], -d[:, 1] / seg_len))
            ny = np.concatenate(([0.0], d[:, 0] / seg_len))
            nx[:-1] += -d[:, 1] / seg_len
            ny[:-1] += d[:, 0] / seg_len
            m = np.hypot(nx, ny)
            flat = m < 1e-9
            nx[flat], ny[flat], m[flat] = 1.0, 0.0, 1.0
            # 1/|sum| is the standard miter extension; clamped so a hairpin
            # cannot fire a spike across the plate.
            scale = np.minimum(2.4, 2.0 / m)
            ux, uy = nx / m * scale, ny / m * scale

            base = nv
            for (cu, cv) in section:
                verts.append(np.stack([
                    p[:, 0] + ux * hw * cu,
                    p[:, 1] + uy * hw * cu,
                    np.full(n, z_ctr + hh * cv),
                ], axis=1))
            # verts currently holds `sides` blocks of n points each
            for k in range(sides):
                k2 = (k + 1) % sides
                a0 = base_index(base, k, n)
                b0 = base_index(base, k2, n)
                idx = np.arange(n - 1)
                faces.append(np.stack([a0 + idx, a0 + idx + 1, b0 + idx + 1], axis=1))
                faces.append(np.stack([a0 + idx, b0 + idx + 1, b0 + idx], axis=1))
            # caps, so the bead is closed at both ends of an open path
            for end, flip in ((0, False), (n - 1, True)):
                ring = [base_index(base, k, n) + end for k in range(sides)]
                for k in range(1, sides - 1):
                    tri = [ring[0], ring[k], ring[k + 1]]
                    faces.append(np.array([tri[::-1] if flip else tri]))
            nv += sides * n

    if not verts:
        raise SystemExit("nothing to build -- every polyline was filtered out")
    V = np.concatenate(verts).astype(np.float32)
    F = np.concatenate(faces).astype(np.uint32)

    # Orient the surface outward.
    #
    # The sweep's winding depends on which way the miter normal points, which
    # in turn depends on the direction the slicer happened to walk each loop --
    # so the whole mesh came out inside-out, consistently. It is invisible in
    # every check that matters except the one that counts: trimesh called it
    # watertight and winding-consistent, and reported a NEGATIVE volume, and
    # Cycles dutifully rendered the inside of every bead. That is what made a
    # solid wall look like a woven basket.
    #
    # Signed volume by the divergence theorem, one flip if it comes out wrong.
    # Centre on the origin in X and Y, keeping Z as printed height.
    #
    # The mesh is built in plate coordinates, so a part sitting mid-bed is
    # ~128mm off origin in both axes. Every renderer frames on the object, and
    # an object that far out framed as an extreme close-up of its own base --
    # which is why the first renders looked like woven cord: they were a 40mm
    # crop of a 120mm vase, not a bad surface.
    V[:, 0] -= (V[:, 0].min() + V[:, 0].max()) / 2.0
    V[:, 1] -= (V[:, 1].min() + V[:, 1].max()) / 2.0

    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    signed = float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum()) / 6.0
    if signed < 0:
        # ascontiguousarray: the fancy-index reshuffle leaves a
        # non-contiguous view, which .view(uint8) in the writer refuses.
        F = np.ascontiguousarray(F[:, [0, 2, 1]])
    return V, F


def base_index(base, k, n):
    return base + k * n


def write_ply(path: Path, V, F):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "ply\nformat binary_little_endian 1.0\n"
        "comment built by tools/gcode_to_mesh.py from a viewer job payload\n"
        "element vertex %d\nproperty float x\nproperty float y\nproperty float z\n"
        "element face %d\nproperty list uchar uint vertex_indices\n"
        "end_header\n" % (len(V), len(F))
    ).encode("ascii")
    face_block = np.empty((len(F), 13), dtype=np.uint8)
    face_block[:, 0] = 3
    face_block[:, 1:] = F.view(np.uint8).reshape(-1, 12)
    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(V.tobytes())
        fh.write(face_block.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="a jobs/<id>.js payload, or a directory of them")
    ap.add_argument("-o", "--output", help="output .ply (single input only)")
    ap.add_argument("-d", "--out-dir", help="output directory (for a whole folder)")
    ap.add_argument("--sides", type=int, default=8,
                    help="cross-section sides (default 8)")
    ap.add_argument("--squareness", type=float, default=4.0,
                    help="bead profile: 2 is an ellipse, 4 a rounded "
                         "rectangle, higher squarer (default 4)")
    ap.add_argument("--squish", type=float, default=1.25,
                    help="bead height as a multiple of layer height; >1 fuses "
                         "consecutive layers the way real extrusion does "
                         "(default 1.18)")
    ap.add_argument("--widen", type=float, default=1.04,
                    help="bead width multiplier, to close hairlines between "
                         "adjacent passes (default 1.04)")
    ap.add_argument("--all-types", action="store_true",
                    help="include sparse infill and skirt too (default: hide them, "
                         "matching the viewer's real-print mode)")
    a = ap.parse_args()

    src = Path(a.source)
    jobs = sorted(p for p in src.glob("*.js") if p.name != "index.js") \
        if src.is_dir() else [src]
    if not jobs:
        raise SystemExit("no job payloads found in %s" % src)
    hidden = set() if a.all_types else DEFAULT_HIDDEN

    for job in jobs:
        payload = load_payload(job)
        V, F = build(payload, sides=a.sides, hidden=hidden,
                     squish=a.squish, widen=a.widen,
                     squareness=a.squareness)
        if a.output and len(jobs) == 1:
            out = Path(a.output)
        else:
            out = Path(a.out_dir or "meshes") / (job.stem + ".ply")
        write_ply(out, V, F)
        print("%-44s %8d verts %8d tris  %6.1f MB  -> %s"
              % (payload.get("name", job.stem), len(V), len(F),
                 out.stat().st_size / 1048576, out))


if __name__ == "__main__":
    main()
