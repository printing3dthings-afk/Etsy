#!/usr/bin/env python3
"""Render the second batch of Victorian village accessory studies
(2026-10-13) round the Victorian cottage, for scale. Same as
render_concepts.py, for accessories_concepts2.scad."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from render_concepts import HERE, ROOT, COT, COLS, rgb

def export(p):
    out = HERE / "meshes" / f"accessories2_{p}.stl"
    subprocess.run(["openscad", "-D", f'part="{p}"', "-o", str(out), str(HERE / "accessories_concepts2.scad")], check=True, capture_output=True)
    return out

if __name__ == "__main__":
    (HERE / "meshes").mkdir(exist_ok=True); (HERE / "images").mkdir(exist_ok=True)
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(export, COLS))
    args = []
    for p, c in COLS.items():
        args += ["--part", f"{HERE / 'meshes' / f'accessories2_{p}.stl'}:{rgb(c)}", "--part", f"{COT / f'victorian_cottage_{p}.stl'}:{rgb(c)}"]
    subprocess.run([sys.executable, str(ROOT / "tools/blender_render.py"), *args, "-o", str(HERE / "images" / "accessories2.png"),
                    "--views", "--front=-y", "--lens", "50", "--samples", "64", "--timeout", "1200", "--no-cache"], check=True)
