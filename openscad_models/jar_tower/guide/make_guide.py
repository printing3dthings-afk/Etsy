#!/usr/bin/env python3
"""Stacking Jar Tower thread test: the PDF guide (2026-11-10). Renders of the real exported
parts (the spigot and the three mouths), posed as check_thread_coupon.py poses them, then
the cards (tools/guide_cards.py).

    python3 make_guide.py            (renders, then Jar_Tower_Thread_Test_Guide.pdf)
    python3 make_guide.py --cards    (cards only, from the renders already made)
"""
import math
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
JT = HERE.parent
ROOT = JT.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(JT))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
TMP = JT / "logs" / "guide"
R = ROOT / "tools" / "blender_render.py"
SPIGOT, MOUTH = "0.96,0.62,0.74", "0.72,0.61,0.88"
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
    return trimesh.load(JT / "parts" / f"{k}.stl", force="mesh")


def seated(C):
    import check_thread_coupon as c
    V, P, TA = c.V, c.P, c.TA
    cs = (V["R_OUT"] - V["CS"] - (V["TH_R"] + C)) / TA
    z0 = V["H_MOUTH"] - cs - V["TH_H"] - P
    zs = V["H_MOUTH"] - cs - C / TA - V["TH_H"]
    t = trimesh.transformations.rotation_matrix(math.radians(360 * (zs - z0) / P), [0, 0, 1])
    t[2, 3] = zs
    return t


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    sp = load("spigot")
    lay = [(save(sp), SPIGOT)]
    for i, C in enumerate((0.2, 0.3, 0.4)):
        m = load(f"mouth_{C}")
        m.apply_translation([[80, 0, 80][i], [0, 80, 80][i], 0])
        lay.append((save(m), MOUTH))
    render(lay, "parts.png", -25, 45)
    mo = load("mouth_0.3")
    up = load("spigot")
    up.apply_translation([0, 0, 28])
    render([(save(mo), MOUTH), (save(up), SPIGOT)], "ready.png", -20, 18)
    home = load("spigot").apply_transform(seated(0.3))
    render([(save(mo), MOUTH), (save(home), SPIGOT)], "home.png", -20, 18)
    # cut in half to show the teeth engaged and the cone seated
    cut = lambda m: trimesh.intersections.slice_mesh_plane(m, [0, 1, 0], [0, 0, 0], cap=True)
    render([(save(cut(mo)), MOUTH), (save(cut(home)), SPIGOT)], "section.png", 0, 8)


def cards():
    a = Card("Jar Tower: thread test", "One screw-in bottom (pink here) and three mouths (purple), at the jars' real 72 mm size.")
    a.step(1, "What's in the print", [
        "!The spigot: a jar's threaded bottom, with a cone above its thread.",
        "!Three mouths: a jar's threaded top. The notches on each rim say how loose its thread is:",
        "1 notch = 0.2 mm (snug), 2 notches = 0.3, 3 notches = 0.4 (easy).",
    ], crop(IMG / "parts.png"))
    a.step(2, "Screw the spigot into a mouth", [
        "Teeth down, into the mouth. Turn it clockwise.",
        "It stops when its cone lands in the mouth's countersink: don't force it past that.",
    ], crop(IMG / "ready.png"), pic_h=480)
    a.step(3, "Screwed home", [
        "The cone pulls the seam shut, the same on every mouth.",
        "Cut in half below: the teeth engaged, and the cone seated on the countersink.",
    ], crop(IMG / "home.png"), pic_h=420)
    a.step(4, "Inside the joint", [], crop(IMG / "section.png"), pic_h=420)
    b = Card("Jar Tower: test it", "Try the spigot in all three mouths.")
    b.step(1, "For each mouth", [
        "!Screw it on: does it go all the way by hand and stop on the cone?",
        "Screwed home, wiggle it: is there play?",
        "Tug it straight up: it must hold.",
        "Start it a little crooked: it should find the thread, not jam.",
    ])
    b.box("Good", ["Screws on by hand, smooth, all the way to the stop.", "No wobble when it's home.",
                   "Finds the thread even if you start it crooked."], GOOD)
    b.box("Tell me", ["which mouth felt best (1, 2 or 3 notches);", "if any bound, or jammed crooked;",
                      "if any wobbled when screwed home."], BAD)
    save_pdf([a, b], HERE / "Jar_Tower_Thread_Test_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_g_*.stl"):
        f.unlink()
