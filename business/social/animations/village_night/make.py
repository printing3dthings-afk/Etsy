#!/usr/bin/env python3
"""Village at night: a 9:16 animation of three real Gingerbread village buildings
(2026-11-11, the first of the "next level" animated posts Scott asked for).

The buildings are the STL parts inside the Gingerbread sale ZIP, in their README
colours, so the animation shows exactly the files on sale. It's a 3D animation of
the design, labelled as one on every frame.

    python3 make.py --still 200          (one test frame, frames/still.png)
    python3 make.py                      (the clip: village_night.mp4)
"""
import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "business" / "store_kit"))
import render_covers as rc  # noqa: E402

ZIP = rc.ZIPS["gingerbread"]
FONTS = ROOT / "assets" / "fonts"
W, H = 1080, 1920
LABEL = "3D animation of the design files"
# left to right along the street; "on" is the frame its tealight comes on
STREET = [
    {"name": "gingerbread_cottage", "at": (-0.058, -0.045), "on": 55, "watts": 0.5, "glow": 5.0},
    {"name": "gingerbread_candy_cane_chapel", "at": (0.0, 0.055), "on": 100, "watts": 0.6, "glow": 5.0},
    {"name": "gingerbread_cocoa_cafe", "at": (0.062, -0.025), "on": 145, "watts": 0.5, "glow": 5.0},
]


def label_png(path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(FONTS / "Poppins-Regular.ttf"), 30)
    w = d.textlength(LABEL, font=f)
    d.text(((W - w) / 2 + 2, 262), LABEL, font=f, fill=(0, 0, 0, 160))
    d.text(((W - w) / 2, 260), LABEL, font=f, fill=(235, 238, 245, 235))
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=int, help="render just this frame")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--flakes", type=int, default=700)
    ap.add_argument("--size", type=int, default=1080, help="width; height is 16:9 of it")
    ap.add_argument("--no-haze", action="store_true")
    a = ap.parse_args()
    frames_dir = HERE / "frames"
    frames_dir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td, zipfile.ZipFile(ZIP) as zf:
        found = rc.buildings(ZIP)
        bl = []
        for b in STREET:
            title, parts = found[b["name"]]
            paths = []
            for s, col in parts:
                zf.extract(s, td)
                paths.append([str(Path(td) / s), col])
            bl.append({**b, "parts": paths})
        cfg = {"buildings": bl, "frames": a.frames, "samples": a.samples, "flakes": a.flakes,
               "size": [a.size, a.size * 16 // 9], "haze": not a.no_haze,
               "look_from": [[0.03, -0.78, 0.24], [0.0, 0.0, 0.06]],
               "look_to": [[-0.01, -0.55, 0.13], [0.0, 0.0, 0.055]],
               "out": str(frames_dir / ("still.png" if a.still else "f_"))}
        if a.still:
            cfg["still"] = a.still
        cj = Path(td) / "cfg.json"
        cj.write_text(json.dumps(cfg))
        r = subprocess.run(["xvfb-run", "-a", "blender", "-b", "--python", str(HERE / "scene.py"), "--", str(cj)],
                           capture_output=True, text=True)
        if "SCENE_OK" not in r.stdout:
            sys.exit(r.stdout[-3000:] + r.stderr[-3000:])
    if a.still:
        print("wrote", frames_dir / "still.png")
        return
    lab = HERE / "label.png"
    label_png(lab)
    out = HERE / "village_night.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(frames_dir / "f_%04d.png"),
                    "-i", str(lab), "-filter_complex", f"[0:v]scale={W}:{H}[v];[v][1:v]overlay=0:0,format=yuv420p",
                    "-c:v", "libx264", "-profile:v", "high", "-crf", "18", "-movflags", "+faststart", "-an",
                    str(out)], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
