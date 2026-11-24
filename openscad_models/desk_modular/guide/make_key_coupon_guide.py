#!/usr/bin/env python3
"""Modular organizer butterfly-key test: the PDF guide (2026-11-24). Renders of the real exported
coupon parts (../parts/), posed as ENGINEERING.md's fit check poses them, then the cards
(tools/guide_cards.py).

    python3 make_key_coupon_guide.py            (renders, then Butterfly_Key_Test_Guide.pdf)
    python3 make_key_coupon_guide.py --cards
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
DM = HERE.parent
ROOT = DM.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
TMP = DM / "logs"
R = ROOT / "tools" / "blender_render.py"
A, B, K = "0.93,0.91,0.86", "0.62,0.72,0.60", "0.78,0.20,0.22"
FLOOR_UNDER_POCKET = 2.0   # key_coupon.scad: BH - KEY_D
n = 0


def save(m):
    global n
    n += 1
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / f"_k_{n}.stl"
    m.export(p)
    return p


def render(parts, out, az, el, res=1000):
    args = []
    for p, c in parts:
        args += ["--part", f"{p}:{c}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az), "--elevation", str(el),
                    "--resolution", str(res), "--timeout", "900"], check=True)


def load(k):
    return trimesh.load(DM / "parts" / f"{k}.stl", force="mesh")


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    blk = load("block")
    b2 = blk.copy().apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1], [40, 20, 0]))
    keys = [load(f"key_{c}") for c in ("0.2", "0.25", "0.3")]
    laid = trimesh.util.concatenate([k.copy().apply_translation([40 + 22 * (i - 1), -22, 0]) for i, k in enumerate(keys)])
    apart = b2.copy().apply_translation([14, 0, 0])
    render([(save(blk), A), (save(apart), B), (save(laid), K)], "key_parts.png", -25, 40)
    over = keys[1].copy().apply_translation([40, 20, 22])
    render([(save(blk), A), (save(b2), B), (save(over), K)], "key_drop.png", -25, 35)
    home = keys[1].copy().apply_translation([40, 20, FLOOR_UNDER_POCKET])
    render([(save(blk), A), (save(b2), B), (save(home), K)], "key_home.png", -25, 50)


def cards():
    a = Card("Organizer: key test", "One grid unit of two modules' walls, and three keys to try.")
    a.step(1, "What's on the plate", [
        "!Two blocks (the same part twice): a piece of a module's wall with its key pocket.",
        "!Three keys: one notch = 0.2 mm clearance, two = 0.25, three = 0.3.",
    ], crop(IMG / "key_parts.png"))
    a.step(2, "Stand the blocks face to face", ["Pockets meeting, the two halves making one bow-tie."],
           crop(IMG / "key_drop.png"), pic_h=440)
    a.step(3, "Drop a key in", [
        "Start with one notch (0.2). Push it down with a finger; no tools.",
        "Home, it stands 1.3 mm above the blocks so a fingernail can lift it out.",
    ], crop(IMG / "key_home.png"), pic_h=440)
    b = Card("Organizer: test it", "Try each key the same way.")
    b.step(1, "Check", [
        "!Does it go in with a finger push, and not rattle once in?",
        "!Pull the blocks apart: how much gap opens? Fine on a desk, or too much?",
        "!Lift it out with a fingernail.",
    ])
    b.box("Good", ["Pushes in by hand.", "No rattle; a hairline gap at most.", "Lifts out with a nail."], GOOD)
    b.box("Tell me", ["which key you'd pick (one, two or three notches);", "if a gap opens you can see;",
                      "if any pocket cracks."], BAD)
    save_pdf([a, b], HERE / "Butterfly_Key_Test_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_k_*.stl"):
        f.unlink()
