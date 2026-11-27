#!/usr/bin/env python3
"""Gear Heart, from the design file: gear test, v1 heart, pin test, v2 heart, real prints (2026-11-27).

    python3 gear_heart.py              # render missing shots, then the video
    python3 gear_heart.py --shots-only

Uses the parts the product's own scripts export to openscad_models/gear_heart/parts/ (the gear
test, the clip test, v1's posted plate, v2's plate, gears and posed pins). Every gear is placed at
its layout.json centre and phase and turned at its own ratio and direction (heart.scad's spin()).
Every figure on screen is from the product's ENGINEERING.md, FACTS.md or REPRINT_PINS.md (SCRIPT.md
lists them). Scott's results are quoted as ours, as he asked for the caddy video.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from storyboard import kit, part, render_shots, save_stills, write_script  # noqa: E402

ROOT = HERE.parents[3]
GH = ROOT / "openscad_models" / "gear_heart"
P = GH / "parts"
OUT = HERE.parent / "out" / "gear_heart"
MESH = OUT / "meshes"
SHOTS = OUT / "shots"
REAL = GH / "real"


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


# the heart's own slice colours (make_heart_v2.sh) and the review renders' pin gold
PLATE, GEAR, PIN = lin("#E8C9D2"), lin("#C94F6D"), lin("#D9AD40")
LAY = json.loads((GH / "layout.json").read_text())
G = LAY["gears"]
KNOB = len(G) - 1
LOOP = [0, 1, 3, 5, 7, 9, 11, 13, 12, 10, 8, 6, 4, 2]          # heart_data.scad: round the ring
UP = 9.0                                                         # PLATE_T + WASHER: a gear's underside


def sign(i):
    """heart.scad's sign_of(): the knob +, then alternating round the loop from the top gear."""
    return 1 if i == KNOB else (-1 if LOOP.index(i) % 2 == 0 else 1)


def spin(i, t):
    """heart.scad's spin(): degrees gear i turns while the knob turns t."""
    return sign(i) * t * G[KNOB]["z"] / G[i]["z"]


def meshes():
    MESH.mkdir(parents=True, exist_ok=True)
    pins = sorted(trimesh.load(P / "heart_pins_posed.stl").split(only_watertight=False),
                  key=lambda m: m.bounds.mean(0)[1])
    for i, g in enumerate(G):
        f = MESH / f"gear_{i}.stl"
        if not f.exists():
            m = trimesh.load(P / "heart_gear" / f"g{i}.stl")
            m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(g["phase"]), [0, 0, 1]))
            m.apply_translation([g["at"][0], g["at"][1], UP])
            m.export(f)
        f = MESH / f"pin_{i}.stl"
        if not f.exists():
            near = min(pins, key=lambda m: np.hypot(*(m.bounds.mean(0)[:2] - g["at"])))
            if np.hypot(*(near.bounds.mean(0)[:2] - g["at"])) > 1.0:
                raise SystemExit(f"no pin under gear {i}")
            near.export(f)
    return {i: (str(MESH / f"gear_{i}.stl"), str(MESH / f"pin_{i}.stl")) for i in range(len(G))}


def gear(m, i, drop_at, turn):
    """Gear i: drops on at `drop_at`, then turns with the knob (turn: [[frame, knob deg], ...])."""
    keys = [[1, [0, 0, 70], 0], [drop_at, [0, 0, 70], 0], [drop_at + 12, [0, 0, 0], 0]]
    keys += [[f, [0, 0, 0], spin(i, t)] for f, t in turn if f > drop_at + 12]
    return dict(part(m[i][0], GEAR, keys), pivot=[G[i]["at"][0], G[i]["at"][1], 0], show=[drop_at, 10000])


def order():
    return LOOP + [KNOB]


def shots():
    m = meshes()
    cd0 = 1.5 * (16 + 12) / 2 + 0.20                    # gear_coupon.scad cd(0): bar 1, +0.20
    heart_cam = dict(target=[0, -7, 12], radius=66)
    return {
        # 1. the gear test: two gears drop onto the +0.20 bar, and turn together
        "a_test": (dict(frames=72, camera=dict(keys=[[1, -25, 38, 1.0], [72, 10, 30, 1.05]]), parts=[
            part(P / "bar0.stl", PLATE), part(P / "bar1.stl", PLATE),
            dict(part(P / "pos_a0.stl", GEAR, [[1, [0, 0, 50], 0], [6, [0, 0, 50], 0], [18, [0, 0, 0], 0],
                                               [30, [0, 0, 0], 0], [72, [0, 0, 0], 120]]), pivot=[0, 0, 0]),
            dict(part(P / "pos_b0.stl", GEAR, [[1, [0, 0, 50], 0], [12, [0, 0, 50], 0], [24, [0, 0, 0], 0],
                                               [30, [0, 0, 0], 0], [72, [0, 0, 0], -160]]), pivot=[cd0, 0, 0])]),
         dict(target=[11, 17, 8], radius=36)),
        # 2. version 1: fifteen gears drop onto snap posts, then the knob turns them all
        "b_v1": (dict(frames=110, camera=dict(keys=[[1, -30, 52, 1.0], [110, 8, 40, 1.05]]), parts=[
            part(P / "heart_plate.stl", PLATE),
            *[gear(m, i, 4 + 3 * k, [[60, 0], [110, 90]]) for k, i in enumerate(order())]]),
         heart_cam),
        # 3. the pin test: the plate held up, three pins push up into it, three gears go on
        # (v2: closer, the aim following the parts down; v1 sat small in the frame)
        "c_clip_v2": (dict(frames=84, camera=dict(keys=[[1, -28, 12, 1.3, [26, 0, 26]], [56, -20, 14, 1.3, [26, 0, 30]],
                                                       [84, -10, 34, 1.5, [26, 0, 8]]]),
                        parts=[
            part(P / "clip" / "base.stl", PLATE, [[1, [0, 0, 36], 0], [52, [0, 0, 36], 0], [72, [0, 0, 0], 0]]),
            *[part(P / "clip" / f"pin_use_{k}.stl", PIN, [[1, [0, 0, 6], 0], [10 + 8 * k, [0, 0, 6], 0],
                                                          [24 + 8 * k, [0, 0, 36], 0], [52, [0, 0, 36], 0],
                                                          [72, [0, 0, 0], 0]]) for k in range(3)],
            *[part(P / "clip" / f"gear_use_{k}.stl", GEAR, [[1, [0, 0, 110], 0], [26 + 6 * k, [0, 0, 110], 0],
                                                            [42 + 6 * k, [0, 0, 36], 0], [52, [0, 0, 36], 0],
                                                            [72, [0, 0, 0], 0]]) for k in range(3)]]),
         dict(target=[26, 0, 22], radius=46)),
        # 4. version 2: the plate held up, fifteen pins push up into it, it sets down, the gears
        #    drop on, and the knob turns them all
        # (b: closer on the pins going in; at 0.9 the plate sat small in the frame)
        "d_v2b": (dict(frames=150, camera=dict(keys=[[1, -20, 10, 1.12, [0, -7, 34]], [40, -22, 12, 1.12, [0, -7, 36]],
                                                    [64, -26, 40, 1.0, [0, -7, 12]], [150, 10, 44, 1.05, [0, -7, 12]]]), parts=[
            part(P / "heart_plate_v2.stl", PLATE, [[1, [0, 0, 40], 0], [42, [0, 0, 40], 0], [60, [0, 0, 0], 0]]),
            *[part(m[i][1], PIN, [[1, [0, 0, 8], 0], [6 + 2 * k, [0, 0, 8], 0], [18 + 2 * k, [0, 0, 40], 0],
                                  [42, [0, 0, 40], 0], [60, [0, 0, 0], 0]]) for k, i in enumerate(order())],
            *[gear(m, i, 60 + 2 * k, [[102, 0], [150, 90]]) for k, i in enumerate(order())]]),
         heart_cam),
    }


SEGMENTS = [
    dict(kind="frames", dir=str(SHOTS / "a_test"), hold_start=0.6, hold_end=1.8, chip="RENDER", label="TESTED FIRST",
         captions=[[0, "Before the heart, a test: two gears, on bars set two spacings apart."],
                   [2.4, "Our pick: the tighter one, 0.20 mm."]]),
    dict(kind="frames", dir=str(SHOTS / "b_v1"), hold_end=2.2, chip="RENDER", label="VERSION 1",
         captions=[[0, "Then the heart: 14 gears round the edge, and a knob in the middle."],
                   [2.4, "One knob turns all fifteen."],
                   [4.0, "Our first print turned, but one of the snap posts snapped."]]),
    dict(kind="frames", dir=str(SHOTS / "c_clip_v2"), hold_end=2.4, chip="RENDER", label="THE FIX, TESTED",
         captions=[[0, "So each gear got its own pin, printed lying down so it flexes along its layers."],
                   [2.6, "We tested three barb sizes. Number 3 felt best."]]),
    dict(kind="frames", dir=str(SHOTS / "d_v2b"), hold_end=1.8, chip="RENDER", label="VERSION 2",
         captions=[[0, "Version 2: fifteen of those pins..."],
                   [2.0, "...the gears go on..."],
                   [3.6, "...and in the design file, all fifteen turn together. Nothing rubs."]]),
    dict(kind="video", path=str(REAL / "heart_base_on_plate_clip.mov"), start=2.8, dur=3.0, speed=0.8, crop="1080:1080:0:0",
         chip="REAL", label="ON OUR PRINTER",
         captions=[[0, "The real version 2 plate, fresh off our printer."]]),
    dict(kind="video", path=str(REAL / "v2_gears_popping_off_2026-11-21.mov"), start=3.4, dur=4.8, speed=0.5,
         crop="1080:1080:0:100", chip="REAL", label="ON OUR PRINTER",
         captions=[[0, "The gears came out clean. The pins came loose, so they're printing again on their own."],
                   [2.6, "Next: the whole heart, turning for real."]]),
]

STATUS = "waiting on Scott's approval (STANDARDS 8). Not posted. The whole v2 heart isn't printed yet."
SOURCES = [
    ("Gear test: two gears, two bar spacings; our pick 0.20 mm",
     "gear_heart/ENGINEERING.md section 7: Scott picked bar 1, +0.20 (\"Number 1\"); gear_coupon.scad DCS [0.20, 0.40]"),
    ("14 gears round the edge and a knob; one knob turns all fifteen",
     "ENGINEERING.md section 7: 14 gears round the heart plus the knob gear; check_heart.py fit PASS"),
    ("First print turned, one snap post snapped",
     "ENGINEERING.md section 8: Scott, 2026-11-13, it meshes and turns; \"one post snapped\""),
    ("Each gear its own pin, printed lying down so it flexes along its layers",
     "ENGINEERING.md section 8: the pin printed on its side, prongs bend in the print plane"),
    ("Three barb sizes; number 3 felt best",
     "ENGINEERING.md section 8: barbs 0.45 / 0.55 / 0.65; Scott, 2026-11-16, \"Number 3 seems to feel the best\""),
    ("v2: all fifteen turn together in the design file; nothing rubs",
     "ENGINEERING.md section 9 / FACTS.md: fit PASS on the exported parts; no gear touches its pin"),
    ("Real v2 plate", "gear_heart/real/heart_base_on_plate_clip.mov (Scott's phone clip; the plate has v2's pin bosses, no posts)"),
    ("Gears clean, pins came loose, re-printing on their own",
     "gear_heart/reprint/REPRINT_PINS.md; footage gear_heart/real/v2_gears_popping_off_2026-11-21.mov"),
    ("How the gears move", "each gear at layout.json's centre and phase, turned by heart.scad's spin() (ratio and direction)"),
]


if __name__ == "__main__":
    for name, (s, cam) in shots().items():
        render_shots({name: s}, SHOTS, cam)
    if "--shots-only" in sys.argv:
        sys.exit()
    from compose import render as compose
    op, ec = kit(OUT, "GEAR HEART")
    tl = compose(SEGMENTS, OUT / "gear_heart_design.mp4", opener=op, endcard=ec)
    (OUT / "timeline.json").write_text(json.dumps(tl, indent=1))
    save_stills(SEGMENTS, OUT / "stills")
    write_script(tl, OUT / "SCRIPT.md", "Gear Heart", STATUS, SOURCES)
    print(f"{tl['total']:.1f} s")
