#!/usr/bin/env python3
"""Plinko v2 BB test: the PDF guide (2026-11-25). Renders of the real exported parts (../), posed
as check_bb.py poses them, then the cards (tools/guide_cards.py).

    python3 make_guide.py            (renders, then Plinko_BB_Test_Guide.pdf)
    python3 make_guide.py --cards
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
ROOT = V2.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
TMP = V2 / "logs"
R = ROOT / "tools" / "blender_render.py"
BOARD, PLUG, BB = "0.93,0.91,0.86", "0.78,0.20,0.22", "0.95,0.95,0.95"
FLOOR, D, TOPWALL, H = 1.4, 6.8, 3.0, 34.0
n = 0


def save(m):
    global n
    n += 1
    p = TMP / f"_g_{n}.stl"
    m.export(p)
    return p


def render(parts, out, az, el):
    args = []
    for p, c in parts:
        args += ["--part", f"{p}:{c}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az), "--elevation", str(el),
                    "--resolution", "1000", "--timeout", "900"], check=True)


def load(k):
    return trimesh.load(V2 / f"bb_coupon_{k}.stl", force="mesh")


def plug_at(i, out):
    p = load(f"plug_{i}")
    p.apply_translation([0, H / 2 + TOPWALL + out, FLOOR + 0.2])
    return p


def bbs(pts):
    return trimesh.util.concatenate([trimesh.creation.icosphere(subdivisions=3, radius=3.0).apply_translation(
        [x, y, FLOOR + D / 2]) for x, y in pts])


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(exist_ok=True)
    b = load("board")
    laid = trimesh.util.concatenate([load(f"plug_{i}").apply_translation([30 + i * 20, 0, 0]) for i in range(3)])
    render([(save(b), BOARD), (save(laid), PLUG)], "parts.png", -20, 55)
    # stood up, as used: rotate so +y is up (board's back toward the viewer's back)
    up = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    def stand(m):
        return m.copy().apply_transform(up)
    lift = H / 2 + 1.6
    def place(m):
        return m.apply_translation([0, 0, lift])
    render([(save(place(stand(b))), BOARD), (save(place(stand(bbs([(0, 26), (0, 33)])))), BB)],
           "load.png", -20, 15)
    render([(save(place(stand(b))), BOARD), (save(place(stand(plug_at(1, 0)))), PLUG),
            (save(place(stand(bbs([(-12, -14), (0, -14), (12, -14), (-6, -9)])))), BB)], "closed.png", -20, 15)


def cards():
    a = Card("Plinko v2: BB test", "6 mm airsoft BBs, the cage you liked, and a snap-in plug.")
    a.step(1, "What's on the plate", [
        "!The test board: the cage, two rows of pegs, a loading port in the top.",
        "!Three plugs. Notches on the head: one = 0.35, two = 0.45, three = 0.55.",
        "You also need 6 mm airsoft BBs (about 10).",
    ], crop(IMG / "parts.png"))
    a.step(2, "Load the BBs", ["Stand the board up, port on top.", "Drop the BBs in through the port."],
           crop(IMG / "load.png"), pic_h=420)
    a.step(3, "Push a plug in", ["Start with two notches (0.45). Push it straight in with a thumb till it clicks."],
           crop(IMG / "closed.png"), pic_h=420)
    b = Card("Plinko v2: test it", "Try each plug, and the BBs.")
    b.step(1, "Check", [
        "!Turn the board over and back: do the BBs fall through the pegs, every time, without sticking?",
        "!Do any BBs catch between the cage and the back?",
        "!Shake it upside down: does the plug stay in?",
        "!Pull the plug: a firm tug, not a struggle? Try all three.",
    ])
    b.box("Good", ["BBs fall freely both ways.", "No BB catches anywhere.", "The plug clicks in and holds upside down."],
          GOOD)
    b.box("Tell me", ["which plug you'd pick (one, two or three notches);", "where any BB sticks;",
                      "if the cage or a prong cracks."], BAD)
    save_pdf([a, b], HERE / "Plinko_BB_Test_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_g_*.stl"):
        f.unlink()
