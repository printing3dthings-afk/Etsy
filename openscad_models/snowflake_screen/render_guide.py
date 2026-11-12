#!/usr/bin/env python3
"""Snowflake Screen: the guide's pictures (2026-11-12), rendered from the real
exported parts (parts/snowflake_screen_blue/white.stl, parts/coupon.stl) and the
pins as snowflake_screen.scad draws them (1.75 mm filament cut to length), in the
print colours. Design-review renders, not photos.

    python3 render_guide.py      (images/guide_*.png)
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
BLUE, WHITE, PIN = "0.61,0.78,0.88", "0.96,0.965,0.97", "0.55,0.55,0.58"
PANELS = [f"{HERE / 'parts' / 'snowflake_screen_blue.stl'}:{BLUE}",
          f"{HERE / 'parts' / 'snowflake_screen_white.stl'}:{WHITE}"]
SHOTS = [  # (image, parts, pins pose, azimuth, elevation)
    ("guide_parts", PANELS, "pins_loose", 0, 62),
    ("guide_pin", PANELS, "pins_half", 20, 38),
    ("guide_coupon", [f"{HERE / 'parts' / 'coupon.stl'}:{BLUE}"], "coupon_pins", 20, 45),
]


def pins(pose):
    out = HERE / "poses" / f"{pose}.stl"
    env = dict(os.environ, OPENSCADPATH=str(ROOT / "assets" / "openscad_libs"))
    subprocess.run(["openscad", "-o", str(out), "-D", f'part="{pose}"', str(HERE / "snowflake_screen.scad")],
                   check=True, env=env, capture_output=True)
    return f"{out}:{PIN}"


def main():
    (HERE / "poses").mkdir(exist_ok=True)
    for name, parts, pose, az, el in SHOTS:
        args = []
        for p in parts + [pins(pose)]:
            args += ["--part", p]
        subprocess.run([sys.executable, str(TOOLS / "blender_render.py"), *args,
                        "-o", str(HERE / "images" / f"{name}.png"), "--azimuth", str(az),
                        "--elevation", str(el), "--samples", "48", "--resolution", "1100"], check=True)


if __name__ == "__main__":
    main()
