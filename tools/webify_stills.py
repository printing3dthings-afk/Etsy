#!/usr/bin/env python3
"""Downscale path-traced plate stills to the JPEGs the viewer ships.

    python3 tools/webify_stills.py

Blender writes ~2.5MB PNGs at 1200px. Committing 72 of those is 180MB of git
for files nothing serves, and the artifact ceiling is 64MB total with 54MB of
plate payloads already in it. So the PNGs stay local (gitignored) and these
JPEGs are the committed deliverable -- which also means a fresh CI checkout,
which never had the PNGs, can still build a site with stills in it.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-d", "--dir", default=str(ROOT / "data" / "plate_stills"))
    ap.add_argument("--size", type=int, default=900)
    ap.add_argument("--quality", type=int, default=80)
    a = ap.parse_args()

    d = Path(a.dir)
    pngs = sorted(d.glob("*.png"))
    if not pngs:
        raise SystemExit("no stills in %s -- run tools/render_plate_stills.sh first" % d)

    total = 0
    for png in pngs:
        dst = png.with_suffix(".jpg")
        if dst.exists() and dst.stat().st_mtime >= png.stat().st_mtime:
            total += dst.stat().st_size
            continue
        im = Image.open(png).convert("RGB")
        im.thumbnail((a.size, a.size), Image.LANCZOS)
        im.save(dst, "JPEG", quality=a.quality, optimize=True, progressive=True)
        total += dst.stat().st_size
    print("%d stills -> %.1f MB of JPEG at %dpx q%d"
          % (len(pngs), total / 1048576, a.size, a.quality))


if __name__ == "__main__":
    main()
