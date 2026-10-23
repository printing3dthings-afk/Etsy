#!/usr/bin/env python3
"""Render the Victorian village accessory studies (2026-10-13) round the
Victorian cottage, for scale: export each colour part of the scene from
accessories_concepts.scad, then render it in Blender with the cottage's own
four parts in the same colours."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COT = HERE.parents[1] / "victorian" / "cottage"
COLS = {"body": "#A8483A", "roof": "#2E3440", "trim": "#F4F1EA", "accent": "#2F6B45"}

def rgb(h):
    h = h.lstrip("#"); return ",".join(f"{int(h[i:i+2], 16) / 255:.3f}" for i in (0, 2, 4))

def export(p):
    out = HERE / "meshes" / f"accessories_{p}.stl"
    subprocess.run(["openscad", "-D", f'part="{p}"', "-o", str(out), str(HERE / "accessories_concepts.scad")], check=True, capture_output=True)
    return out

if __name__ == "__main__":
    (HERE / "meshes").mkdir(exist_ok=True); (HERE / "images").mkdir(exist_ok=True)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(export, COLS))
    args = []
    for p, c in COLS.items():
        args += ["--part", f"{HERE / 'meshes' / f'accessories_{p}.stl'}:{rgb(c)}", "--part", f"{COT / f'victorian_cottage_{p}.stl'}:{rgb(c)}"]
    subprocess.run([sys.executable, str(ROOT / "tools/blender_render.py"), *args, "-o", str(HERE / "images" / "accessories.png"),
                    "--views", "--front=-y", "--lens", "50", "--samples", "64", "--timeout", "1200", "--no-cache"], check=True)
