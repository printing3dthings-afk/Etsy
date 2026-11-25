#!/usr/bin/env python3
"""Plinko big-ball test: a one-card PDF guide (2026-11-25). Renders of the real model (the board
and its balls, exported separately from big_ball_coupon.scad), then the card (tools/guide_cards.py).

    python3 make_big_ball_guide.py BOARD.stl BALLS.stl
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
R = ROOT / "tools" / "blender_render.py"


def render(parts, out, az, el):
    args = []
    for p, c in parts:
        args += ["--part", f"{p}:{c}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az), "--elevation", str(el),
                    "--resolution", "1000", "--timeout", "900"], check=True)


def main(board, balls):
    IMG.mkdir(parents=True, exist_ok=True)
    render([(board, "0.93,0.91,0.86"), (balls, "0.78,0.20,0.22")], "big_ball_plate.png", -25, 55)
    # the board cut open: everything below the cage, to show the balls on their necks
    b = trimesh.load(board)
    cut = b.slice_plane([0, 0, 14.4], [0, 0, -1], cap=True)
    tmp = HERE.parent / "logs" / "_open.stl"
    cut.export(tmp)
    render([(tmp, "0.93,0.91,0.86"), (balls, "0.78,0.20,0.22")], "big_ball_inside.png", -25, 50)
    tmp.unlink()
    a = Card("Plinko: big-ball test", "Bigger balls printed inside the cage, each on a neck you snap.")
    a.step(1, "What's on the plate", [
        "!Three pockets under the cage, two 10 mm balls in each.",
        "!Notches on the left edge: one = 1.6 mm neck, two = 2.0, three = 2.4.",
    ], crop(IMG / "big_ball_plate.png"))
    a.step(2, "Inside (cage cut away in this picture)", ["Each ball stands on a short neck to the floor.",
                                                         "Push a toothpick through the cage onto a ball's side to snap it."],
           crop(IMG / "big_ball_inside.png"), pic_h=420)
    b2 = Card("Plinko: big-ball test, tell me", "")
    b2.step(1, "Check each pocket", [
        "!Did every ball print round, or did any break loose while printing?",
        "!Does the toothpick snap it free? How hard?",
        "!Once free, does it rattle and roll?",
    ])
    b2.box("Good", ["Balls printed whole.", "Snap free with a toothpick.", "Roll inside the pocket."], GOOD)
    b2.box("Tell me", ["which neck printed whole and still snapped;", "any ball that broke loose mid-print."], BAD)
    save_pdf([a, b2], HERE / "Plinko_Big_Ball_Test_Guide.pdf")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
