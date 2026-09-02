#!/usr/bin/env python3
"""
tools/flatten_svg_paths.py -- rewrite an SVG's cubic-bezier paths as straight
line segments at a chosen chord tolerance.

Why this exists (2026-09-02): OpenSCAD's import() flattens SVG beziers at its
own fixed, very fine tolerance -- $fs/$fa have no effect on it, confirmed
directly (identical 391,576 facets at $fs=2 and $fs=5). A potrace vectorization
of the OnBrandCraftz brush-script logo came in at ~300-390k facets, and a
single CGAL boolean against a shell built from it ran past eight minutes
without finishing. Coarsening the trace itself barely helped: -O 0.2 -> 2.0 and
-a 1.0 -> 1.334 moved it 305k -> 299k.

Flattening the curves up front is the lever that actually works, because
OpenSCAD has nothing left to subdivide. Tolerance is in the path's own
coordinate units -- read the transform on the enclosing <g> to convert (potrace
writes `scale(0.1,-0.1)`, so a path unit is a tenth of an SVG user unit).

    python3 tools/flatten_svg_paths.py in.svg out.svg --tol 60

Handles the command set potrace actually emits: M, m, l, c, z. Anything else
raises rather than being silently dropped -- a quietly missing stroke in a logo
is exactly the kind of defect that survives to a print.
"""
from __future__ import annotations

import argparse
import re
import sys

_NUM = re.compile(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')
_TOKEN = re.compile(r'([MmLlCcZzHhVvSsQqTtAa])|([-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?)')


def _tokenize(d: str):
    for m in _TOKEN.finditer(d):
        yield ('cmd', m.group(1)) if m.group(1) else ('num', float(m.group(2)))


def _flatten_cubic(p0, p1, p2, p3, tol, out, depth=0):
    """Adaptive subdivision: recurse while either control point sits further
    than `tol` off the chord."""
    if depth >= 16:
        out.append(p3)
        return
    x0, y0 = p0
    x3, y3 = p3
    dx, dy = x3 - x0, y3 - y0
    chord = (dx * dx + dy * dy) ** 0.5
    if chord < 1e-12:
        d1 = ((p1[0] - x0) ** 2 + (p1[1] - y0) ** 2) ** 0.5
        d2 = ((p2[0] - x0) ** 2 + (p2[1] - y0) ** 2) ** 0.5
        flat = max(d1, d2) <= tol
    else:
        d1 = abs((p1[0] - x0) * dy - (p1[1] - y0) * dx) / chord
        d2 = abs((p2[0] - x0) * dy - (p2[1] - y0) * dx) / chord
        flat = max(d1, d2) <= tol
    if flat:
        out.append(p3)
        return
    mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    a, b, c = mid(p0, p1), mid(p1, p2), mid(p2, p3)
    ab, bc = mid(a, b), mid(b, c)
    m = mid(ab, bc)
    _flatten_cubic(p0, a, ab, m, tol, out, depth + 1)
    _flatten_cubic(m, bc, c, p3, tol, out, depth + 1)


def flatten_path(d: str, tol: float) -> str:
    toks = list(_tokenize(d))
    i = 0
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    subpaths: list[list[tuple[float, float]]] = []
    pts: list[tuple[float, float]] = []
    cmd = None

    def nums(k):
        nonlocal i
        vals = []
        for _ in range(k):
            if i >= len(toks) or toks[i][0] != 'num':
                raise ValueError(f"expected {k} numbers for '{cmd}' near token {i}")
            vals.append(toks[i][1])
            i += 1
        return vals

    while i < len(toks):
        kind, val = toks[i]
        if kind == 'cmd':
            cmd = val
            i += 1
            if cmd in 'Zz':
                if pts:
                    subpaths.append(pts)
                    pts = []
                cur = start
                continue
        if cmd is None:
            raise ValueError("path data starts without a command")
        if cmd in 'Mm':
            x, y = nums(2)
            cur = (x, y) if cmd == 'M' else (cur[0] + x, cur[1] + y)
            if pts:
                subpaths.append(pts)
            pts = [cur]
            start = cur
            cmd = 'L' if cmd == 'M' else 'l'      # per SVG spec
        elif cmd in 'Ll':
            x, y = nums(2)
            cur = (x, y) if cmd == 'L' else (cur[0] + x, cur[1] + y)
            pts.append(cur)
        elif cmd in 'Cc':
            v = nums(6)
            if cmd == 'C':
                p1, p2, p3 = (v[0], v[1]), (v[2], v[3]), (v[4], v[5])
            else:
                p1 = (cur[0] + v[0], cur[1] + v[1])
                p2 = (cur[0] + v[2], cur[1] + v[3])
                p3 = (cur[0] + v[4], cur[1] + v[5])
            _flatten_cubic(cur, p1, p2, p3, tol, pts)
            cur = p3
        else:
            raise ValueError(f"unsupported path command {cmd!r} -- refusing to "
                             f"drop geometry silently")
    if pts:
        subpaths.append(pts)

    out = []
    for sp in subpaths:
        if len(sp) < 3:
            continue
        body = " ".join(f"{x:.1f} {y:.1f}" for x, y in sp)
        out.append("M " + body.split(" ", 2)[0] + " " + body.split(" ", 2)[1]
                   + " L " + " ".join(f"{x:.1f} {y:.1f}" for x, y in sp[1:]) + " Z")
    return " ".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--tol", type=float, default=60.0,
                    help="chord tolerance in the path's own coordinate units")
    args = ap.parse_args(argv)

    svg = open(args.src).read()
    n_before = n_after = 0

    def repl(m):
        nonlocal n_before, n_after
        d = m.group(1)
        n_before += len(_NUM.findall(d))
        nd = flatten_path(d, args.tol)
        n_after += len(_NUM.findall(nd))
        return m.group(0).replace(d, nd)

    out = re.sub(r'\bd="([^"]*)"', repl, svg, flags=re.S)
    open(args.dst, "w").write(out)
    print(f"{args.src} -> {args.dst}  tol={args.tol}  "
          f"coords {n_before} -> {n_after} ({n_after / max(n_before, 1):.1%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
