#!/usr/bin/env python3
"""Pie Drum Caddy v2 keeper test: the PDF guide (2026-11-24). Renders of the real exported
coupon parts (parts_v2/, from pie_caddy_v2.scad), posed as the fit check poses them: the ring
on the disc, the cup screwed down to its stop 0.5 mm above the ring. Then the cards
(tools/guide_cards.py).

    python3 make_keeper_coupon_guide.py            (renders, then Pie_Caddy_v2_Keeper_Test_Guide.pdf)
    python3 make_keeper_coupon_guide.py --cards
"""
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
BASE, RING, CUP = "0.93,0.92,0.88", "0.72,0.61,0.88", "0.95,0.78,0.25"
DISC_T, RING_H, GAP, PITCH = 2.4, 4.0, 0.5, 4.0   # pie_caddy_v2.scad: disc, C_RING_H, KEEP_GAP, TH_P
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
    return trimesh.load(PC / "parts_v2" / f"{k}.stl", force="mesh")


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    base, ring, cup = load("coupon_base"), load("coupon_ring"), load("coupon_keeper_0.2")
    render([(save(base), BASE), (save(ring.copy().apply_translation([36, 0, 0])), RING),
            (save(cup.copy().apply_translation([-36, 0, 0])), CUP)], "keeper_parts.png", -20, 35)
    on = ring.copy().apply_translation([0, 0, DISC_T])
    render([(save(base), BASE), (save(on), RING)], "keeper_ring_on.png", -20, 35)
    home = cup.copy()
    home.apply_transform(trimesh.transformations.rotation_matrix(np.radians(360 * GAP / PITCH), [0, 0, 1]))
    home.apply_translation([0, 0, DISC_T + RING_H + GAP])
    render([(save(base), BASE), (save(on), RING), (save(home), CUP)], "keeper_home.png", -20, 25)
    cut = lambda m: trimesh.intersections.slice_mesh_plane(m, [0, 1, 0], [0, 0, 0], cap=True)
    render([(save(cut(base)), BASE), (save(cut(on)), RING), (save(cut(home)), CUP)], "keeper_section.png", 0, 6)


def cards():
    a = Card("Pie Caddy v2: keeper test",
             "The caddy's new centre: the post's real thread, a slice of the drum's hub, and the cup's nut.")
    a.step(1, "What's on the plate", [
        "!The post (white): a disc with the threaded post the drum turns on.",
        "!The ring (purple): the drum's hub, the part that has to keep spinning.",
        "!The cup (gold): the bottom of the keeper cup, nut and stop. One notch on its rim = 0.2 mm clearance.",
        "The 0.3 mm cup (two notches) is a separate plate: print it only if the 0.2 binds.",
    ], crop(IMG / "keeper_parts.png"))
    a.step(2, "Drop the ring over the post", ["Flat on the disc. It should turn loosely on the post."],
           crop(IMG / "keeper_ring_on.png"), pic_h=420)
    a.step(3, "Screw the cup down", [
        "Clockwise, by fingers only, until it stops. It stops on the post's tip, not on the ring.",
        "Don't force it past the stop.",
    ], crop(IMG / "keeper_home.png"), pic_h=420)
    a.step(4, "Inside", ["Home, the cup's foot sits 0.5 mm above the ring: the ring is caught, never clamped."],
           crop(IMG / "keeper_section.png"), pic_h=360)
    b = Card("Pie Caddy v2: test it", "Three things, a minute each.")
    b.step(1, "Check", [
        "!Does the cup screw down smoothly and stop firmly?",
        "!With the cup home, does the ring still spin freely?",
        "!Lift the ring: does it rise only a hair before it catches?",
        "Then unscrew the cup all the way: it should come off clean.",
    ])
    b.box("Good", ["Smooth thread, firm stop.", "Ring spins under the cup.", "Ring lifts a hair, then stops."], GOOD)
    b.box("Tell me", ["if the thread binds or is loose and wobbly;", "if the ring drags with the cup home;",
                      "which cup you'd pick, 0.2 or 0.3."], BAD)
    save_pdf([a, b], HERE / "Pie_Caddy_v2_Keeper_Test_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_k_*.stl"):
        f.unlink()
