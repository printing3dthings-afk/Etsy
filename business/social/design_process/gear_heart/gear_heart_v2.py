#!/usr/bin/env python3
"""Gear Heart, from the design file: the v2 cut, template v2 (2026-11-27).

    python3 gear_heart_v2.py              # render missing shots, then gear_heart_design_v2.mp4
    python3 gear_heart_v2.py --shots-only

Scott, via Greg: a new version beside the first cut, which stays as it is (gear_heart.py,
gear_heart_design.mp4). Same parts, same facts, same gear placement and ratios (imported from
gear_heart.py); the template v2 rules are in ../README.md. The whole v2 heart isn't printed yet, so
the real footage stops at the plate and gears, and a marked placeholder holds the place for Scott's
clip of a hand turning the knob.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import gear_heart as v1  # noqa: E402
from storyboard import part, render_shots, save_stills  # noqa: E402

OUT = v1.OUT
SHOTS = OUT / "shots_v2"
P, REAL = v1.P, v1.REAL
PLATE, GEAR, PIN = v1.PLATE, v1.GEAR, v1.PIN
PORT = dict(res=[1080, 1920], look="soft", samples=16, horizon_rgb=[1.22, 1.22, 1.22])   # horizon matched to the soft-lit floor (1.15 read 2 levels dark)
TOP = 300            # parts come in from above the frame, eased: nothing pops in


def gear(m, i, drop_at, turn, fall=18):
    keys = [[1, [0, 0, TOP], 0], [drop_at, [0, 0, TOP], 0], [drop_at + fall, [0, 0, 0], 0]]
    keys += [[f, [0, 0, 0], v1.spin(i, t)] for f, t in turn if f > drop_at + fall]
    return dict(part(m[i][0], GEAR, keys), pivot=[v1.G[i]["at"][0], v1.G[i]["at"][1], 0])


def turning(m, i, turn):
    return dict(part(m[i][0], GEAR, [[f, [0, 0, 0], v1.spin(i, t)] for f, t in turn]),
                pivot=[v1.G[i]["at"][0], v1.G[i]["at"][1], 0])


def shots():
    m = v1.meshes()
    order = v1.order()
    cd0 = 1.5 * (16 + 12) / 2 + 0.20
    heart = dict(target=[0, -7, 10], radius=70)
    return {
        # the payoff: the finished v2 heart, the knob turning all fifteen
        "p_payoff": (dict(PORT, frames=66, camera=dict(keys=[[1, -14, 52, 1.05], [66, 6, 44, 1.12]]), parts=[
            part(P / "heart_plate_v2.stl", PLATE),
            *[part(m[i][1], PIN) for i in order],
            *[turning(m, i, [[1, 0], [66, 150]]) for i in order]]), heart),
        # test print 1: two gears come down onto the 0.20 bar and turn together
        "a_test": (dict(PORT, frames=72, camera=dict(keys=[[1, -20, 36, 1.0], [72, 8, 30, 1.06]]), parts=[
            part(P / "bar0.stl", PLATE), part(P / "bar1.stl", PLATE),
            dict(part(P / "pos_a0.stl", GEAR, [[1, [0, 0, 200], 0], [24, [0, 0, 0], 0], [30, [0, 0, 0], 0],
                                               [72, [0, 0, 0], 120]]), pivot=[0, 0, 0]),
            dict(part(P / "pos_b0.stl", GEAR, [[1, [0, 0, 200], 0], [6, [0, 0, 200], 0], [30, [0, 0, 0], 0],
                                               [72, [0, 0, 0], -160]]), pivot=[cd0, 0, 0])]),
         dict(target=[11, 17, 8], radius=38)),
        # version 1: the gears come down onto the snap posts, then the knob turns them
        "b_v1": (dict(PORT, frames=84, camera=dict(keys=[[1, -24, 50, 1.0], [84, 6, 42, 1.06]]), parts=[
            part(P / "heart_plate.stl", PLATE),
            *[gear(m, i, 1 + 2 * k, [[52, 0], [84, 60]]) for k, i in enumerate(order)]]), heart),
        # test print 2: the bar held up, three pins push up into it, gears on, all set down
        "c_clip": (dict(PORT, frames=84, camera=dict(keys=[[1, -26, 14, 1.0, [26, 0, 24]], [50, -18, 18, 1.0, [26, 0, 24]],
                                                         [84, -10, 34, 1.08, [26, 0, 8]]]), parts=[
            part(P / "clip" / "base.stl", PLATE, [[1, [0, 0, 30], 0], [50, [0, 0, 30], 0], [68, [0, 0, 0], 0]]),
            *[part(P / "clip" / f"pin_use_{k}.stl", PIN, [[1, [0, 0, 2], 0], [2 + 6 * k, [0, 0, 2], 0],
                                                          [20 + 6 * k, [0, 0, 30], 0], [50, [0, 0, 30], 0],
                                                          [68, [0, 0, 0], 0]]) for k in range(3)],
            *[part(P / "clip" / f"gear_use_{k}.stl", GEAR, [[1, [0, 0, 220], 0], [18 + 5 * k, [0, 0, 220], 0],
                                                            [38 + 5 * k, [0, 0, 30], 0], [50, [0, 0, 30], 0],
                                                            [68, [0, 0, 0], 0]]) for k in range(3)]]),
         dict(target=[26, 0, 15], radius=40)),
        # version 2: the plate held up, the pins push in, it sets down, the gears come down, it turns
        "d_v2": (dict(PORT, frames=90, camera=dict(keys=[[1, -20, 16, 1.0, [0, -7, 30]], [30, -22, 24, 1.0, [0, -7, 24]],
                                                       [54, -18, 44, 1.04, [0, -7, 10]], [90, 6, 44, 1.08, [0, -7, 10]]]),
                      parts=[
            part(P / "heart_plate_v2.stl", PLATE, [[1, [0, 0, 30], 0], [22, [0, 0, 30], 0], [36, [0, 0, 0], 0]]),
            *[part(m[i][1], PIN, [[1, [0, 0, 2], 0], [1 + k, [0, 0, 2], 0], [16 + k, [0, 0, 30], 0],
                                  [22, [0, 0, 30], 0], [36, [0, 0, 0], 0]]) for k, i in enumerate(order)],
            *[gear(m, i, 30 + 2 * k, [[72, 0], [90, 40]], fall=14) for k, i in enumerate(order)]]), heart),
    }


SEGMENTS = [
    dict(kind="frames", dir=str(SHOTS / "p_payoff"), hold_end=0.6, chip="RENDER", fade=0.2,
         big=[[1.0, "2 VERSIONS + 2 TEST PRINTS TO GET HERE"]]),
    dict(kind="rewind", dirs=[str(SHOTS / s) for s in ("a_test", "b_v1", "c_clip", "d_v2")], dur=0.8,
         chip="RENDER", fade=0.15, big=[[0, "REWIND"]]),
    dict(kind="frames", dir=str(SHOTS / "a_test"), hold_end=0.3, chip="RENDER", label="TEST PRINT 1",
         captions=[[0, "Two gears, two spacings. We picked the tighter one: 0.20 mm."]]),
    dict(kind="frames", dir=str(SHOTS / "b_v1"), hold_end=0.2, chip="RENDER", label="VERSION 1",
         captions=[[0, "One knob turns all 15 gears. But on our print, a snap post snapped."]]),
    dict(kind="frames", dir=str(SHOTS / "c_clip"), hold_end=0.2, chip="RENDER", label="TEST PRINT 2",
         captions=[[0, "So each gear gets its own pin. Of 3 barb sizes, number 3 felt best."]]),
    dict(kind="frames", dir=str(SHOTS / "d_v2"), hold_end=0.2, chip="RENDER", label="VERSION 2",
         captions=[[0, "All 15 gears on pins, turning together in the design file."]]),
    dict(kind="video", path=str(REAL / "heart_base_on_plate_clip.mov"), start=2.8, dur=2.2, speed=0.8,
         chip="REAL", label="ON OUR PRINTER", captions=[[0, "Our real version 2 plate."]]),
    dict(kind="video", path=str(REAL / "v2_gears_popping_off_2026-11-21.mov"), start=3.4, dur=2.6, speed=0.6,
         chip="REAL", label="ON OUR PRINTER", captions=[[0, "The gears printed clean. The pins are reprinting."]]),
    dict(kind="placeholder", dur=2.8, chip="PLACEHOLDER", label="COMING NEXT",
         lines=["OUR REAL CLIP GOES HERE", "A hand turning the knob on the printed heart. 9:16, about 3 s."]),
]

STATUS = ("waiting on Scott's approval (STANDARDS 8). Not posted. Not postable until the placeholder "
          "holds Scott's hand-turn clip: the whole v2 heart isn't printed yet.")
SOURCES = v1.SOURCES + [
    ("2 versions + 2 test prints", "ENGINEERING.md sections 5-9: the gear test, v1, the clip test, v2"),
    ("Our real version 2 plate", "gear_heart/real/heart_base_on_plate_clip.mov (Scott's phone clip; v2's pin bosses, no posts)"),
    ("The gears printed clean; the pins are reprinting", "gear_heart/reprint/REPRINT_PINS.md"),
]


if __name__ == "__main__":
    for name, (s, cam) in shots().items():
        render_shots({name: s}, SHOTS, cam)
    if "--shots-only" in sys.argv:
        sys.exit()
    from compose_v2 import render as compose, write_script
    tl = compose(SEGMENTS, OUT / "gear_heart_design_v2.mp4")
    (OUT / "timeline_v2.json").write_text(json.dumps(tl, indent=1))
    save_stills(SEGMENTS, OUT / "stills_v2")
    write_script(tl, OUT / "SCRIPT_v2.md", "Gear Heart", STATUS, SOURCES)
    print(f"{tl['total']:.1f} s")
