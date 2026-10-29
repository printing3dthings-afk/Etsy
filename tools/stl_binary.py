#!/usr/bin/env python3
"""Rewrite ASCII STLs as binary STL, in place, facet for facet (2026-10-29).

    python3 tools/stl_binary.py FILE.stl [...]   convert these
    python3 tools/stl_binary.py --tracked        every ASCII STL git tracks
    python3 tools/stl_binary.py --check [...]    list ASCII STLs, exit 1 if any

Binary STL is the same triangles in about a fifth of the space: OpenSCAD's
ASCII export cost this repo 1.0 GB across 283 files. Every slicer and every
tool here (trimesh, manifold3d, Blender, PrusaSlicer, Bambu Studio) reads both.

It writes what the ASCII file says, not a re-processed mesh: no vertex merging,
no dropped degenerate faces, facets in the same order with the same normals.
trimesh's own export was not used for that reason (it merges vertices on
load). The only change is precision: binary STL stores float32, so a coordinate
moves by at most half a float32 step, 0.000004 mm at 100 mm from the origin
(measured on the haunted post office body: watertight and one body before and
after, volume 72,879.72 against 72,879.73 mm3). Before a file is replaced, the
new one is parsed back and every facet compared with what was parsed; a file
that does not match is left as it was.

data/trash/ is skipped: its copies are promised byte-exact for --restore.

tools/openscad_render.py already writes binary. Shell build scripts that call
openscad directly should pass --export-format binstl; tests/test_stls_are_binary.py
fails if an ASCII STL is ever committed again.
"""
import argparse, os, re, struct, subprocess, sys, tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
_NUM = rb"([-+0-9.eE]+|nan|inf)"
_FACET = re.compile(rb"facet\s+normal\s+" + rb"\s+".join([_NUM] * 3)
                    + rb"\s+outer\s+loop\s+" + rb"\s+".join([rb"vertex\s+" + rb"\s+".join([_NUM] * 3)] * 3)
                    + rb"\s+endloop\s+endfacet", re.I)


def is_ascii(path):
    with open(path, "rb") as f:
        head = f.read(84)
    if not head.lstrip().lower().startswith(b"solid"):
        return False
    # A binary STL may start with "solid" in its header too; it then says its
    # own size exactly.
    if len(head) == 84:
        n = struct.unpack("<I", head[80:84])[0]
        if os.path.getsize(path) == 84 + 50 * n:
            return False
    return True


def parse_ascii(data):
    rows = _FACET.findall(data)
    if not rows:
        return np.zeros((0, 12), np.float32)
    return np.array(rows, dtype=np.float64).astype(np.float32)


def read_binary(path):
    raw = Path(path).read_bytes()
    n = struct.unpack("<I", raw[80:84])[0]
    rec = np.frombuffer(raw, dtype=np.dtype([("v", "<f4", 12), ("a", "<u2")]), count=n, offset=84)
    return rec["v"]


def convert(path):
    path = Path(path)
    data = path.read_bytes()
    facets = parse_ascii(data)
    declared = len(re.findall(rb"endfacet", data, re.I))
    if len(facets) != declared:
        return f"SKIP {path}: parsed {len(facets)} facets of {declared}"
    rec = np.zeros(len(facets), dtype=np.dtype([("v", "<f4", 12), ("a", "<u2")]))
    rec["v"] = facets
    header = b"binary STL from ASCII by tools/stl_binary.py".ljust(80, b" ")
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".stl.tmp")
    with os.fdopen(fd, "wb") as f:
        f.write(header + struct.pack("<I", len(facets)) + rec.tobytes())
    back = read_binary(tmp)
    if back.shape != facets.shape or not np.array_equal(back, facets, equal_nan=True):
        os.unlink(tmp)
        return f"SKIP {path}: read back differently"
    before = len(data)
    os.replace(tmp, path)
    return f"ok   {path}: {len(facets)} facets, {before / 1e6:.1f} -> {path.stat().st_size / 1e6:.1f} MB"


def tracked_stls():
    out = subprocess.run(["git", "ls-files", "-z", "*.stl", "*.STL"], cwd=ROOT,
                         capture_output=True, check=True).stdout
    return [ROOT / p for p in out.decode().split("\0") if p and not p.startswith("data/trash/")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--tracked", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files = [Path(f) for f in a.files] or (tracked_stls() if (a.tracked or a.check) else [])
    ascii_files = [f for f in files if f.exists() and is_ascii(f)]
    if a.check:
        for f in ascii_files:
            print(f"ASCII {f}")
        return 1 if ascii_files else 0
    bad = 0
    for f in ascii_files:
        msg = convert(f)
        print(msg, flush=True)
        bad += msg.startswith("SKIP")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
