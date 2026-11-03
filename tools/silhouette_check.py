#!/usr/bin/env python3
"""Drawing-quality checks for a flat charm or relief outline (2026-11-04).

tools/product_gate.py, print_fidelity.py and fragility.py say whether a part
prints. Nothing said whether it is drawn well, and four rounds of the
Valentine Cupid went to Scott with defects a measurement would have caught: a
knee bent the wrong way, a bow touching the face, clutter, and a back that a
"fix" made bulge further. These checks come from the character-design research
(reports/Better 3D character design.md) and were calibrated on those drafts.

Run on the exported STL of a flat piece (it is sliced at mid-thickness for the
outline and just under the top for anything engraved):

    python3 tools/silhouette_check.py part.stl
    python3 tools/silhouette_check.py part.stl --scad part.scad      # + joint checks
    python3 tools/silhouette_check.py part.stl --against approved.stl --sheet review.png

Checks (FAIL blocks; NOTE is for the eye):
  gaps       two edges closer than --min-gap (0.8) without meeting: a tangent,
             or a slot that prints closed
  thin       material narrower than --min-width (1.2, three beads) that would
             snap or drop out
  specks     holes or islands too small to print, and more than one piece
  joints     every knee and elbow named in the .scad bends the way the joint
             can: the .scad echoes  "JOINT", name, "knee"|"elbow", [root],
             [joint], [end], facing  (facing +1 when he faces +x)
  apart      with --apart A.stl B.stl: two parts that must read as separate
             (a bow and a face) stay at least 1.5 mm apart
  twinning   the outline matches its own mirror image (IoU > 0.9): stiff
  clutter    engraved marks and small cut-throughs counted against limits
  against    with --against: IoU, Hausdorff and each region that grew or
             shrank, so a change is measured before it is shown

Calibrated on the Cupid drafts in git (tests/test_silhouette_check.py):
  - joints flags the draft whose far knee bent backwards (8db56c41) and passes
    the five after it, which Scott did not fault for it again once fixed
  - apart flags both drafts whose bow ran into the face (8db56c41, 9737a502,
    overlapping 1.2-1.3 mm) and passes the four after it (1.7-1.9 mm clear)
  - clutter flags the draft with 9 engraved strokes and passes the rest
What these checks did NOT catch, measured on the same drafts: an outline
"wobble" score and a count of cut-through slots did not separate the drafts
Scott called cluttered or lumpy from the ones he accepted (every draft had 3-4
slots, and the hulled-circle draft scored smoother than the smooth_path ones),
so neither is a gate. The back that bulged, and the fix that made it worse,
are only caught by --against: measure every change against the version before.
"""
from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

MIN_GAP = 0.8      # DETAIL_STANDARD: a slot under two beads prints closed
MIN_WIDTH = 1.2    # three beads: anything handled
MIN_HOLE = 0.8     # an island or hole under 0.8 mm across is dropped
TWIN_IOU = 0.90
# Engraved strokes: the carved-line Cupid had 9 and Scott called it
# cluttered; every draft after had 0. Small cut-throughs: no draft had any, so
# 6 is the research's "few, large gaps" ceiling, not a calibrated number.
MAX_CUTS = 6
MAX_ENGRAVED = 3
# Two parts that must read as separate: the drafts Scott said had "the bow as
# part of the face" overlapped it 1.2-1.3 mm; the accepted ones cleared it
# 1.7-1.9 mm.
MIN_APART = 1.5

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- geometry in
def _polys_from_section(mesh: trimesh.Trimesh, z: float):
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return Polygon()
    planar, to3d = sec.to_2D(to_2D=np.eye(4))
    return unary_union([p for p in planar.polygons_full if p.area > 1e-6])


def load_outline(path: str):
    """(outline at mid-thickness, outline just under the top, thickness)."""
    mesh = trimesh.load(path, force="mesh")
    z0, z1 = mesh.bounds[:, 2]
    t = z1 - z0
    return _polys_from_section(mesh, z0 + t / 2), _polys_from_section(mesh, z1 - min(0.3, t / 4)), t


def _parts(g):
    if g.is_empty:
        return []
    return list(g.geoms) if hasattr(g, "geoms") else [g]


def _where(g) -> str:
    c = g.representative_point()
    return f"({c.x:.1f}, {c.y:.1f})"


# ---------------------------------------------------------------- the checks
def check_gaps(shape, min_gap=MIN_GAP):
    """Places where two edges come within min_gap without the material between
    them being part of the shape: a closing by min_gap/2 fills exactly those."""
    r = min_gap / 2 * 0.98
    filled = shape.buffer(r, join_style=1).buffer(-r, join_style=1).difference(shape)
    out = []
    for g in _parts(filled):
        # an inside corner fills a sliver too; a real near-touch is long
        if g.area < 0.15:
            continue
        minx, miny, maxx, maxy = g.bounds
        if max(maxx - minx, maxy - miny) < 1.0:
            continue
        out.append(("FAIL", f"gap narrower than {min_gap} mm at {_where(g)}, {g.area:.2f} mm2: "
                            "edges nearly touch (a tangent), or a slot that prints closed"))
    return out


def check_thin(shape, min_width=MIN_WIDTH):
    r = min_width / 2 * 0.98
    lost = shape.difference(shape.buffer(-r, join_style=1).buffer(r, join_style=1))
    out = []
    for g in _parts(lost):
        if g.area < 0.3:
            continue
        minx, miny, maxx, maxy = g.bounds
        if max(maxx - minx, maxy - miny) < 1.5:      # a rounded tip, not a member
            continue
        out.append(("FAIL", f"narrower than {min_width} mm at {_where(g)}, {g.area:.2f} mm2: "
                            "under three beads, it snaps or drops out"))
    return out


def check_specks(shape, pieces=1):
    out = []
    parts = _parts(shape)
    if len(parts) != pieces:
        out.append(("FAIL", f"{len(parts)} separate pieces, expected {pieces}"))
    for p in parts:
        if p.area < MIN_HOLE ** 2:
            out.append(("FAIL", f"island of {p.area:.2f} mm2 at {_where(p)}: too small to print"))
        for ring in p.interiors:
            h = Polygon(ring)
            if h.area < 1.0 or h.buffer(-MIN_HOLE / 2).is_empty:
                out.append(("FAIL", f"speck hole of {h.area:.2f} mm2 at {_where(h)}: prints closed, "
                                    "reads as a flaw"))
    return out


def check_twinning(shape):
    c = shape.centroid
    best = 0.0
    for xf, yf in ((-1, 1), (1, -1)):
        m = affinity.scale(shape, xfact=xf, yfact=yf, origin=c)
        best = max(best, shape.intersection(m).area / shape.union(m).area)
    if best > TWIN_IOU:
        return [("FAIL", f"outline matches its own mirror image (IoU {best:.2f} > {TWIN_IOU}): "
                         "stiff and symmetric; turn it to a 3/4 or profile view, vary one side")]
    return [("OK", f"mirror IoU {best:.2f}")]


def check_clutter(shape, top):
    # a bow's or handle's big opening (over 20 mm2) is form, not detail
    holes = [h for h in (Polygon(r) for p in _parts(shape) for r in p.interiors) if h.area <= 20]
    engraved = 0
    if top is not None and not top.is_empty:
        # marks cut into the face show on the top slice but not through it; 1 mm
        # in from the edge, so the rounded-over rim is not counted as one
        marks = shape.buffer(-1.0).difference(top).buffer(-0.05)
        engraved = sum(1 for g in _parts(marks) if g.area > 0.2 and
                       g.minimum_rotated_rectangle.length > 6)
    n = len(holes)
    out = []
    msg = f"{len(holes)} small cut-throughs, {engraved} engraved marks"
    if n > MAX_CUTS:
        out.append(("FAIL", f"cluttered: {msg} (limit {MAX_CUTS} cuts): keep only the gaps that "
                            "separate forms (wing from head, arm from body, the legs)"))
    if engraved > MAX_ENGRAVED:
        out.append(("FAIL", f"cluttered: {msg} (limit {MAX_ENGRAVED} engraved): "
                            "show detail with the outline, not with lines on the face"))
    if not out:
        out.append(("OK", msg))
    return out


def read_joints(scad: str, openscad: str):
    """JOINT echoes from the .scad: name, kind, [root], [joint], [end], facing."""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "j.echo"
        r = subprocess.run([openscad, "-o", str(out), scad], capture_output=True, text=True,
                           env={**__import__("os").environ,
                                "OPENSCADPATH": str(ROOT / "assets" / "openscad_libs")})
        text = out.read_text() if out.exists() else r.stderr
    return parse_joints(text)


def parse_joints(text: str):
    joints = []
    for line in text.splitlines():
        m = re.search(r'"JOINT",\s*"([^"]+)",\s*"(knee|elbow)",(.*)', line)
        if not m:
            continue
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", m.group(3))]
        if len(nums) >= 7:
            joints.append((m.group(1), m.group(2), nums[0:2], nums[2:4], nums[4:6], 1 if nums[6] >= 0 else -1))
    return joints


def joint_bend(kind, root, joint, end, facing):
    """Signed bend in degrees: positive is the way the joint can bend.
    Seen from the side with the figure facing +x and y up, a knee folds the
    shin back (hip-knee-ankle turns clockwise) and an elbow folds the forearm
    forward (anticlockwise). Mirror for a figure facing -x."""
    u, v = np.subtract(joint, root), np.subtract(end, joint)
    ang = math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], float(np.dot(u, v))))
    want = -1 if kind == "knee" else 1
    return ang * want * facing


def check_joints(joints):
    """A knee or elbow is a one-way hinge. The draft Scott called 'legs
    backwards' had its far knee folded the wrong way (8db56c41, -12 deg)."""
    out = []
    for name, kind, root, joint, end, facing in joints:
        b = joint_bend(kind, root, joint, end, facing)
        if b < -5:
            out.append(("FAIL", f"{name}: the {kind} bends backwards ({b:.0f} deg); "
                                f"a {kind} only folds one way"))
        else:
            out.append(("OK", f"{name}: {kind} bends {b:.0f} deg the right way"))
    return out


def check_apart(a, b, name, min_gap=MIN_APART):
    inter = a.intersection(b)
    if inter.area > 0.01:
        return [("FAIL", f"{name}: overlap {inter.area:.1f} mm2 at {_where(inter)}; they should "
                         f"read as two things, {min_gap} mm apart")]
    d = a.distance(b)
    if d < min_gap:
        return [("FAIL", f"{name}: only {d:.2f} mm apart (need {min_gap}): they read as touching")]
    return [("OK", f"{name}: {d:.2f} mm apart")]


def compare(shape, ref):
    iou = shape.intersection(ref).area / shape.union(ref).area
    haus = shape.hausdorff_distance(ref)
    out = [("NOTE", f"against the reference: IoU {iou:.3f}, Hausdorff {haus:.2f} mm")]
    for label, diff in (("grew", shape.difference(ref)), ("shrank", ref.difference(shape))):
        regions = sorted((g for g in _parts(diff) if g.area > 1.0), key=lambda g: -g.area)
        for g in regions[:4]:
            far = max(Point(xy).distance(ref.boundary if label == "grew" else shape.boundary)
                      for xy in g.exterior.coords)
            out.append(("NOTE", f"{label} {g.area:.1f} mm2 at {_where(g)}, up to {far:.1f} mm"))
    return out


# ---------------------------------------------------------------- review sheet
def review_sheet(shape, out: str, ref=None):
    """Black-fill silhouette, its mirror, a thumbnail at Etsy search size, and
    with a reference an overlay (reference in red): the same views every round."""
    from PIL import Image, ImageDraw, ImageFont

    def draw(g, size, flip=False, ref=None):
        minx, miny, maxx, maxy = (unary_union([g, ref]) if ref is not None else g).bounds
        s = (size * 0.9) / max(maxx - minx, maxy - miny)
        im = Image.new("RGB", (size, size), "white")
        d = ImageDraw.Draw(im)

        def tr(x, y):
            u = (x - minx) * s + size * 0.05
            u = size - u if flip else u
            return (u, size - ((y - miny) * s + size * 0.05))

        def fill(gg, colour, outline=None):
            for p in _parts(gg):
                d.polygon([tr(*c) for c in p.exterior.coords], fill=colour, outline=outline)
                for r in p.interiors:
                    d.polygon([tr(*c) for c in r.coords], fill="white")
        fill(g, "black")
        if ref is not None:
            for p in _parts(ref):
                d.line([tr(*c) for c in p.exterior.coords], fill=(220, 30, 30), width=3)
                for r in p.interiors:
                    d.line([tr(*c) for c in r.coords], fill=(220, 30, 30), width=3)
        return im

    tiles = [("silhouette", draw(shape, 600)), ("mirrored", draw(shape, 600, flip=True)),
             ("thumbnail, 180 px", draw(shape, 180))]
    if ref is not None:
        tiles.append(("over the reference (red)", draw(shape, 600, ref=ref)))
    W = Image.new("RGB", (620 * len(tiles), 660), (240, 238, 234))
    d = ImageDraw.Draw(W)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        f = None
    for i, (label, im) in enumerate(tiles):
        W.paste(im, (10 + 620 * i, 50))
        d.text((10 + 620 * i, 14), label, fill=(40, 30, 30), font=f)
    W.save(out)


# ---------------------------------------------------------------- run
def run(path, scad=None, against=None, pieces=1, openscad="openscad", sheet=None, apart=()):
    shape, top, _ = load_outline(path)
    results = []
    results += [("gaps", *r) for r in check_gaps(shape)] or [("gaps", "OK", "no near-touches")]
    results += [("thin", *r) for r in check_thin(shape)] or [("thin", "OK", "nothing under 1.2 mm")]
    results += [("specks", *r) for r in check_specks(shape, pieces)] or [("specks", "OK", "one clean piece")]
    if scad:
        js = read_joints(scad, openscad)
        results += [("joints", *r) for r in check_joints(js)] if js else [("joints", "NOTE", "no JOINT echoes")]
    for a, b in apart:
        pa, pb = load_outline(a)[0], load_outline(b)[0]
        results += [("apart", *r) for r in check_apart(pa, pb, f"{Path(a).stem} / {Path(b).stem}")]
    results += [("twinning", *r) for r in check_twinning(shape)]
    results += [("clutter", *r) for r in check_clutter(shape, top)]
    ref = None
    if against:
        ref, _, _ = load_outline(against)
        results += [("against", *r) for r in compare(shape, ref)]
    if sheet:
        review_sheet(shape, sheet, ref)
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stl")
    ap.add_argument("--scad", help="the .scad, for its JOINT echoes")
    ap.add_argument("--against", help="an earlier or approved STL to measure the change against")
    ap.add_argument("--pieces", type=int, default=1)
    ap.add_argument("--sheet", help="write a review sheet PNG here")
    ap.add_argument("--apart", nargs=2, action="append", default=[], metavar=("A.stl", "B.stl"),
                    help="two part outlines that must stay 1.5 mm apart (repeatable)")
    ap.add_argument("--openscad", default="openscad")
    a = ap.parse_args(argv)
    res = run(a.stl, a.scad, a.against, a.pieces, a.openscad, a.sheet, a.apart)
    fails = 0
    for check, level, msg in res:
        print(f"  {level:<4}  {check:<9} {msg}")
        fails += level == "FAIL"
    print("SILHOUETTE CHECK " + ("PASSED" if not fails else f"FAILED ({fails})"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
