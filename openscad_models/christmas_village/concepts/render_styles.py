#!/usr/bin/env python3
"""Render the five Christmas-cottage style concepts (2026-09-27).

Exports every piece of every style from christmas_cottage_styles.scad, then
renders each style in Blender with its own four filament colours, and joins
the five three-quarter views into one comparison image.

    python3 render_styles.py            # all five
    python3 render_styles.py nordic     # one
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCAD = HERE / "christmas_cottage_styles.scad"
MESH = HERE / "meshes"
IMG = HERE / "images"

# Four filament colours per style: body, roof, trim (always the white one,
# which is also the snow), accent.
PALETTE = {
    "victorian":   {"body": "#8B3A2F", "roof": "#3B4150", "trim": "#F2EFE8", "accent": "#2E5B3C"},
    "gingerbread": {"body": "#A8662F", "roof": "#4B2A1C", "trim": "#F7F1E6", "accent": "#C62F3A"},
    "nordic":      {"body": "#EDE8DE", "roof": "#2E3035", "trim": "#A52A24", "accent": "#D6A83E"},
    "chalet":      {"body": "#8A5A34", "roof": "#3A2E28", "trim": "#F2EFE8", "accent": "#B3312F"},
    "kawaii":      {"body": "#F4B6C6", "roof": "#9FD8C8", "trim": "#FBF8F4", "accent": "#F4D06F"},
}
# The Nordic house is white, so its snow is the body colour and its red is
# the trim.
WHITE = {s: ("body" if s == "nordic" else "trim") for s in PALETTE}

def roles(style):
    """piece -> colour role."""
    w = WHITE[style]
    r = {"walls": "body", "tex": "body", "plaster": "trim", "base": w,
         "roof": "roof", "shingles": "roof", "chimney": "body",
         "snow": w, "drips": w, "frames": "trim", "barge": "trim",
         "door": "accent", "deco": "accent", "deco2": w}
    if style == "chalet":
        r.update(frames="body", barge="body", deco2="body", door="roof", chimney="trim")
    if style == "gingerbread":
        r.update(door="roof")
    if style == "nordic":
        r.update(door="trim")
    if style == "kawaii":
        r.update(deco2="body")
    return r

def rgb(hexcol):
    h = hexcol.lstrip("#")
    return ",".join("%.3f" % (int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))

def export(style, piece):
    out = MESH / style / f"{piece}.stl"
    out.parent.mkdir(parents=True, exist_ok=True)
    env = {"OPENSCADPATH": str(ROOT / "assets" / "openscad_libs"), "PATH": "/usr/bin:/bin"}
    r = subprocess.run(["openscad", "-o", str(out), "-D", f'style="{style}"',
                        "-D", f'piece="{piece}"', str(SCAD)],
                       capture_output=True, text=True, env=env, timeout=1800)
    if r.returncode != 0 or not out.exists() or out.stat().st_size < 200:
        if "top level object is empty" in r.stderr.lower() or "empty" in r.stderr.lower():
            out.unlink(missing_ok=True)
            return None
        raise RuntimeError(f"{style}/{piece} failed:\n{r.stderr[-2000:]}")
    return out

def render(style):
    role = roles(style)
    pal = PALETTE[style]
    with ThreadPoolExecutor(4) as ex:
        got = dict(zip(role, ex.map(lambda p: export(style, p), role)))
    args = []
    for piece, path in got.items():
        if path:
            args += ["--part", f"{path}:{rgb(pal[role[piece]])}"]
    subprocess.run([sys.executable, str(ROOT / "tools" / "blender_render.py"), *args,
                    "-o", str(IMG / f"{style}.png"), "--views", "--front=-y",
                    "--samples", "64", "--resolution", "1000", "--no-cache"],
                   check=True, capture_output=True)
    for f in IMG.glob(f"{style}*.rendercache"):
        f.unlink()

if __name__ == "__main__":
    IMG.mkdir(exist_ok=True)
    for s in sys.argv[1:] or list(PALETTE):
        render(s)
        print("rendered", s, flush=True)
