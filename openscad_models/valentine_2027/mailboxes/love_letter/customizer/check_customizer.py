#!/usr/bin/env python3
"""Check love_letter_customizer.scad (2026-11-05):

- it stands alone: no include, use or import
- under OpenSCAD 2021's CGAL engine, the default (NAME = "OLIVIA") and a few
  other names render, each timed; MakerWorld gives up after about 60-75 s
- each matches love_letter.scad's body_print with the same name (rendered by
  Manifold): the same bounding box, volume within 0.02%, and the geometry where
  the two differ at all (their symmetric difference) under 0.05% of the body,
  broken down by where it is. Every part of it comes from a change
  build_customizer.py makes on purpose: the name's curves at 12 segments, the
  relief's circles at fewer, the pocket's exact slope. Measured 2026-11-05
  for OLIVIA: the name 33.6 mm3, the pocket 5.5, the relief 10.6, elsewhere 0.2.
- Cupid, in his pocket, sits in the new body as he does in the shipped one:
  his overlap with each is the same (his pegs in his holes, nothing else)

    python3 check_customizer.py
"""
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
LL = HERE.parent
CUST = HERE / "love_letter_customizer.scad"
LIBS = HERE.parents[4] / "assets" / "openscad_libs"
# an OpenSCAD with the Manifold engine (2026 snapshot), as ship.sh uses
FAST = os.environ.get("OPENSCAD_FAST", "/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun")
NAMES = ["OLIVIA", "MAXIMILIAN", "Ana", "MARY-JO"]
LIMIT = 30.0          # seconds, under CGAL here: half MakerWorld's timeout
fails = []


def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    if not ok:
        fails.append(text)


def mfd(path):
    m = trimesh.load(path, force="mesh")
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def where(m):
    """the volume of m by region of the envelope"""
    out = {}
    for piece in m.decompose():
        b = piece.bounding_box()
        x, y, z = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2
        r = ("pocket" if -80 < x < -16 and 4 < z < 66 and y < -28 else "name" if -14 < x < 82 and 38 < z < 62 and y < -30
             else "front relief" if y < -30.9 else "back relief" if y > 30.9 else "elsewhere")
        out[r] = out.get(r, 0) + piece.volume()
    return ", ".join(f"{k} {v:.1f}" for k, v in sorted(out.items(), key=lambda kv: -kv[1]))


def main():
    src = CUST.read_text()
    say(not re.search(r"^\s*(include|use)\s*<|import\s*\(", src, re.M), "stands alone: no include, use or import")
    exposed = src.split("/* [Hidden] */")[0]
    params = re.findall(r"^(\w+)\s*=", exposed, re.M)
    say(params == ["NAME"] and 'NAME = "OLIVIA";' in exposed, f"exposes NAME only, default OLIVIA ({params})")
    cupid = mfd(LL / "parts" / "cupid_use.stl")
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for name in NAMES:
            print(f"== {name}")
            out = tmp / "cust.stl"
            s = time.time()
            r = subprocess.run(["openscad", "-o", str(out), "-D", f'NAME="{name}"', str(CUST)], capture_output=True, text=True)
            dt = time.time() - s
            err = [l for l in r.stderr.splitlines() if "ERROR" in l or "WARNING" in l]
            say(r.returncode == 0 and not err, f"renders under OpenSCAD 2021 (CGAL) in {dt:.1f} s{'; ' + err[0] if err else ''}")
            say(dt < LIMIT, f"in under {LIMIT:.0f} s")
            ref = tmp / "ref.stl"
            src_ll = (LL / "love_letter.scad")
            subprocess.run([FAST, "--backend=manifold", "--export-format", "binstl", "-D", 'part="body_print"',
                            "-D", f'NAME="{name}"', "-o", str(ref), str(src_ll)], cwd=LL, capture_output=True,
                           env={**os.environ, "OPENSCADPATH": str(LIBS)}, check=True)
            a, b = mfd(out), mfd(ref)
            ta = trimesh.load(out)
            say(ta.is_watertight and len(ta.split(only_watertight=False)) == 1, "one closed body")
            va, vb = a.volume(), b.volume()
            ba, bb = np.array(a.bounding_box()), np.array(b.bounding_box())
            diff = (a - b).volume() + (b - a).volume()
            say(abs(va - vb) < 0.0002 * vb, f"volume {va:.2f} mm3 against the shipped {vb:.2f} ({va - vb:+.2f})")
            say(np.abs(ba - bb).max() < 0.02, f"bounding box {(ba[3:] - ba[:3]).round(2)} against {(bb[3:] - bb[:3]).round(2)}")
            say(diff < 0.0005 * vb, f"where they differ at all: {diff:.1f} mm3, {100 * diff / vb:.3f}% of the body")
            print(f"        added: {where(a - b)}\n        left out: {where(b - a)}")
            if name == NAMES[0]:
                ca, cb = (cupid ^ a).volume(), (cupid ^ b).volume()
                say(abs(ca - cb) < 0.5, f"Cupid in his pocket overlaps the new body {ca:.2f} mm3, the shipped one {cb:.2f}"
                    " (his pegs in their holes)")
    print("\nCUSTOMIZER CHECK " + ("OK" if not fails else "FAILED:\n  " + "\n  ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
