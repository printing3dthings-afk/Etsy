#!/usr/bin/env python3
"""
tools/vectorize_brand_logo.py -- turn the OnBrandCraftz raster logo into two
registered, print-ready vector SVGs (charcoal brush script + gold swash).

Why: the canonical brand file, tools/api_server/static/brand/
onbrandcraftz-wordmark.svg, is an SVG wrapper around a base64 PNG. There is no
vector geometry in it, so OpenSCAD's import() cannot use it, and a multi-colour
inlay needs the two ink colours as separate closed regions.

Output goes to assets/brand_vector/ and is consumed by
openscad_models/snap_box.scad. Both files keep one shared coordinate frame, so
a single scale + offset in OpenSCAD keeps them registered to each other.

    python3 tools/vectorize_brand_logo.py

Two non-obvious steps, both there because of real defects:

  * The gold mask is cut back from a DILATED dark mask. The swash passes under
    the script's descenders, so the two masks share a boundary, and potrace
    does not place the two outlines on exactly the same sub-pixel line. The
    resulting overlap made every downstream boolean non-manifold -- and simply
    subtracting the script from the swash in OpenSCAD did not fix it, because
    that leaves razor-thin slivers along the same boundary. A real gap, opened
    here in the bitmap, is what actually works. It only removes gold adjacent
    to the script, so the swash keeps its full width everywhere else.

  * The traced curves are flattened to straight segments afterwards
    (flatten_svg_paths.py). import() subdivides SVG beziers at its own fixed
    tolerance and ignores $fs/$fa, which put 391,576 facets into the script and
    ran a single boolean past eight minutes. See that tool's docstring.
"""
from __future__ import annotations

import base64
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools/api_server/static/brand/onbrandcraftz-wordmark.svg"
OUT = ROOT / "assets/brand_vector"

UPSAMPLE = 4          # potrace traces a larger bitmap much more smoothly
ALPHA_MIN = 110       # opaque enough to count as ink
GOLD_RB = 40          # red-minus-blue that separates the gold swash from ink
GAP_PX = 8            # dilation of the dark mask, in upsampled px (~0.15mm)
FLATTEN_TOL = 30      # path units; ~0.05mm at the box's logo size


def _masks():
    m = re.search(r'href="data:image/png;base64,([^"]+)"', SRC.read_text())
    if not m:
        raise SystemExit(f"no embedded PNG found in {SRC}")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(base64.b64decode(m.group(1)))
        raw = f.name
    im = Image.open(raw).convert("RGBA")
    big = im.resize((im.width * UPSAMPLE, im.height * UPSAMPLE), Image.LANCZOS)
    a = np.array(big)
    alpha = a[..., 3].astype(int)
    red, blue = a[..., 0].astype(int), a[..., 2].astype(int)
    ink = alpha > ALPHA_MIN
    gold = ink & ((red - blue) > GOLD_RB) & (red > 120)
    dark = ink & ~gold
    return dark, gold


def _dilate(mask, n):
    m = mask.copy()
    for _ in range(n):
        d = m.copy()
        d[1:, :] |= m[:-1, :]; d[:-1, :] |= m[1:, :]
        d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
        m = d
    return m


def _write_pbm(mask, path):
    h, w = mask.shape
    packed = np.packbits(mask.astype(np.uint8), axis=1)
    with open(path, "wb") as f:
        f.write(b"P4\n%d %d\n" % (w, h))
        f.write(packed.tobytes())


def main() -> int:
    if not shutil_which("potrace"):
        raise SystemExit("potrace is not installed. apt-get install -y potrace")
    OUT.mkdir(parents=True, exist_ok=True)
    dark, gold = _masks()
    gold_clear = gold & ~_dilate(dark, GAP_PX)
    print(f"ink px: dark={dark.sum()} gold={gold.sum()} "
          f"gold after {GAP_PX}px clearance={gold_clear.sum()}")

    for name, mask in (("script", dark), ("swash", gold_clear)):
        with tempfile.TemporaryDirectory() as td:
            pbm = Path(td) / f"{name}.pbm"
            traced = Path(td) / f"{name}.svg"
            _write_pbm(mask, pbm)
            subprocess.run(["potrace", "-b", "svg", "-a", "1.0", "-O", "0.2",
                            "-t", "12", "-o", str(traced), str(pbm)], check=True)
            subprocess.run([sys.executable, str(ROOT / "tools/flatten_svg_paths.py"),
                            str(traced), str(OUT / f"onbrandcraftz-{name}.svg"),
                            "--tol", str(FLATTEN_TOL)], check=True)
    return 0


def shutil_which(x):
    import shutil
    return shutil.which(x)


if __name__ == "__main__":
    sys.exit(main())
