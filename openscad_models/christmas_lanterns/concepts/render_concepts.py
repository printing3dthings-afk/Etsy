#!/usr/bin/env python3
"""Render the five lantern form studies (2026-10-13): export every colour part
of every form from lantern_concepts.scad, render each form in Blender in its
colours, and join the three-quarter views into one comparison sheet.

    python3 render_concepts.py          # all five
    python3 render_concepts.py 2 4      # some
"""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MESH, IMG = HERE / "meshes", HERE / "images"
PARTS = ["frame", "glass", "art", "accent"]
PAL = {1: ["#2E3440", "#F4F1EA", "#2E3440", "#F4F1EA"], 2: ["#2E3440", "#F4F1EA", "#2E3440", "#F4F1EA"],
       3: ["#2F6B45", "#F4F1EA", "#C62F3A", "#D4A017"], 4: ["#C62F3A", "#F4F1EA", "#2F6B45", "#D4A017"],
       5: ["#2F6B45", "#F4F1EA", "#2E3440", "#C62F3A"]}
NAMES = {1: "1  Hex carriage lantern", 2: "2  Panorama drum", 3: "3  Christmas tree",
         4: "4  Star", 5: "5  Gift box"}

def rgb(h):
    h = h.lstrip("#"); return ",".join(f"{int(h[i:i+2], 16) / 255:.3f}" for i in (0, 2, 4))

def export(job):
    f, p = job
    out = MESH / f"lantern{f}_{p}.stl"
    subprocess.run(["openscad", "-D", f"form={f}", "-D", f'part="{p}"', "-o", str(out), str(HERE / "lantern_concepts.scad")],
                   check=True, capture_output=True)
    return out

def main(forms):
    MESH.mkdir(exist_ok=True); IMG.mkdir(exist_ok=True)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(export, [(f, p) for f in forms for p in PARTS]))
    for f in forms:
        args = []
        for p, c in zip(PARTS, PAL[f]):
            m = MESH / f"lantern{f}_{p}.stl"
            if m.stat().st_size > 200:
                args += ["--part", f"{m}:{rgb(c)}"]
        subprocess.run([sys.executable, str(ROOT / "tools/blender_render.py"), *args, "-o", str(IMG / f"lantern{f}.png"),
                        "--views", "--front=-y", "--samples", "48", "--timeout", "900"], check=True)
    sheet()

def sheet():
    tiles = [(f, IMG / f"lantern{f}_three_quarter.png") for f in sorted(NAMES) if (IMG / f"lantern{f}_three_quarter.png").exists()]
    T = 600
    S = Image.new("RGB", (T * len(tiles), T + 50), "white"); d = ImageDraw.Draw(S)
    try: font = ImageFont.truetype(str(ROOT / "fonts/Montserrat-Bold.ttf"), 26)
    except OSError: font = ImageFont.load_default()
    for i, (f, p) in enumerate(tiles):
        im = Image.open(p).convert("RGB"); w, h = im.size; c = int(min(w, h) * 0.12)
        S.paste(im.crop((c, c, w - c, h - c)).resize((T, T), Image.LANCZOS), (T * i, 50))
        d.text((T * i + 16, 12), NAMES[f], fill="#2E3440", font=font)
    S.save(HERE / "lantern_forms.jpg", quality=90)

if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5])
