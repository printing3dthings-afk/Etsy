#!/usr/bin/env python3
"""Pie Drum Caddy bearing test: the PDF guide (2026-11-10). Renders of the real exported
parts (base and top) with 27 balls posed as check_bearing_coupon.py poses them, then the
cards (tools/guide_cards.py).

    python3 make_guide.py            (renders, then Pie_Caddy_Bearing_Test_Guide.pdf)
    python3 make_guide.py --cards
"""
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PC = HERE.parent
ROOT = PC.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
TMP = PC / "logs" / "guide"
R = ROOT / "tools" / "blender_render.py"
V = {k: float(v) for k, v in re.findall(r"\b(\w+) = ([0-9.]+);", (PC / "bearing_coupon.scad").read_text())}
BASE, TOP, BB = "0.93,0.92,0.88", "0.72,0.61,0.88", "0.95,0.78,0.25"
n = 0


def save(m):
    global n
    n += 1
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / f"_g_{n}.stl"
    m.export(p)
    return p


def render(parts, out, az, el, res=1000):
    args = []
    for p, c in parts:
        args += ["--part", f"{p}:{c}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az), "--elevation", str(el),
                    "--resolution", str(res), "--timeout", "900"], check=True)


def load(k):
    return trimesh.load(PC / "parts" / f"{k}.stl", force="mesh")


def balls():
    ring = V["D"] / 2 - 10
    bs = [trimesh.creation.icosphere(subdivisions=3, radius=V["BALL"] / 2).apply_translation(
        [ring * np.cos(a), ring * np.sin(a), V["BASE_T"] + V["BALL"] / 2]) for a in np.linspace(0, 2 * np.pi, 27, endpoint=False)]
    return trimesh.util.concatenate(bs)


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    base, top = load("base"), load("top")
    t2 = top.copy().apply_translation([V["D"] + 10, 0, 0])
    loose = trimesh.util.concatenate([trimesh.creation.icosphere(subdivisions=3, radius=3).apply_translation([x, -55, 3])
                                      for x in np.linspace(-20, 100, 9)])
    render([(save(base), BASE), (save(t2), TOP), (save(loose), BB)], "parts.png", -20, 45)
    render([(save(base), BASE), (save(balls()), BB)], "balls_in.png", -20, 55)
    on = top.copy().apply_translation([0, 0, V["BASE_T"] + V["BALL"]])
    render([(save(base), BASE), (save(balls()), BB), (save(on), TOP)], "top_on.png", -20, 25)
    cut = lambda m: trimesh.intersections.slice_mesh_plane(m, [0, 1, 0], [0, 0, 0], cap=True)
    render([(save(cut(base)), BASE), (save(cut(balls())), BB), (save(cut(on)), TOP)], "section.png", 0, 6)


def cards():
    a = Card("Pie Caddy: bearing test", "The caddy's real ball track at 80 mm, and 27 airsoft BBs (6 mm, any brand).")
    a.step(1, "What you need", [
        "!The base (white here): a ball track round a centre post.",
        "!The top (purple): a disc with a hole for the post.",
        "!27 airsoft BBs, 6 mm. Not in the print: a bag of thousands is a few dollars.",
    ], crop(IMG / "parts.png"))
    a.step(2, "Drop the BBs into the track", [
        "All 27, all the way round. A small gap is left on purpose so they can't jam.",
    ], crop(IMG / "balls_in.png"), pic_h=460)
    a.step(3, "Set the top on", [
        "Its hole over the post, flat side down. It rests on the balls, not on the base.",
        "Lift it straight off any time.",
    ], crop(IMG / "top_on.png"), pic_h=420)
    a.step(4, "Inside", ["The balls roll between the track's floor and the top's smooth underside."],
           crop(IMG / "section.png"), pic_h=360)
    b = Card("Pie Caddy: test it", "A mug or a few pens on top makes it a fair test.")
    b.step(1, "Spin it", [
        "!Flick it: does it spin and coast?",
        "Listen: quiet, or does it rumble?",
        "Watch the edge as it turns: does it wobble?",
    ])
    b.box("Good", ["Spins with a flick and coasts.", "Quiet.", "No wobble."], GOOD)
    b.box("Tell me", ["if it grinds or rumbles;", "if it stops quickly;", "if it wobbles, or the balls jam."], BAD)
    save_pdf([a, b], HERE / "Pie_Caddy_Bearing_Test_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_g_*.stl"):
        f.unlink()
