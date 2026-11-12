#!/usr/bin/env python3
"""Moon Phase Coasters: the guide's pictures (2026-11-11), rendered from the real
exported parts posed by moon_coasters.scad (part = flat, step_panel, step_coaster),
in the print colours. Design-review renders, not photos.

    python3 render_guide.py      (images/guide_*.png)
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / "tools"
COL = {"navy": "0.12,0.16,0.29", "cream": "0.95,0.9,0.78", "slate": "0.36,0.4,0.5"}
SHOTS = [  # (pose, image, azimuth, elevation)
    ("flat", "guide_parts", 0, 62),
    ("step_panel", "guide_panel", 28, 24),
    ("step_coaster", "guide_coaster", 28, 24),
]


def main():
    for pose, name, az, el in SHOTS:
        parts = []
        for c in ("navy", "cream", "slate"):
            f = HERE / "parts" / "guide" / f"{pose}_{c}.stl"
            if f.exists():
                parts += ["--part", f"{f}:{COL[c]}"]
        subprocess.run([sys.executable, str(TOOLS / "blender_render.py"), *parts,
                        "-o", str(HERE / "images" / f"{name}.png"), "--azimuth", str(az),
                        "--elevation", str(el), "--samples", "48", "--resolution", "1100"], check=True)


if __name__ == "__main__":
    main()
