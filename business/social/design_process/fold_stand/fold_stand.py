#!/usr/bin/env python3
"""Fold Stand, from the design file: four versions, three test prints (2026-11-27).

    python3 export_parts.py      # the four versions' meshes, from their own sources
    python3 fold_stand.py        # render missing shots, then the video

Every on-screen claim is from openscad_models/fold_stand's own notes (SCRIPT.md lists them).
Scott's test results are quoted as ours, as he asked for the caddy video ("us", "here at OBC").
"""
import json
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from storyboard import kit, part, render_shots, save_stills, write_script  # noqa: E402

ROOT = HERE.parents[3]
FS = ROOT / "openscad_models" / "fold_stand"
OUT = HERE.parent / "out" / "fold_stand"
MESH = OUT / "meshes"
SHOTS = OUT / "shots"


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


# the stand's own filament colours (FOLD_STAND_PRINTING.md and the v3/v4 ship scripts)
LILAC, WHITE, PINK = lin("#B79CE0"), lin("#F4F1EA"), lin("#F6A6C1")


def m(ver, name):
    p = MESH / ver / f"{name}.stl"
    if not p.exists():
        raise SystemExit(f"no mesh {p}: run export_parts.py {ver}")
    return p


def centre(ver, names):
    b = [trimesh.load(m(ver, n)).bounds for n in names]
    lo = [min(x[0][i] for x in b) for i in range(3)]
    hi = [max(x[1][i] for x in b) for i in range(3)]
    return [(lo[i] + hi[i]) / 2 for i in range(3)], max(hi[i] - lo[i] for i in range(3)) * 0.62


def shots():
    c1, r1 = centre("v1", ["front", "back"])
    c3, r3 = centre("v3", ["base", "plate", "prop"])
    pin = trimesh.load(m("v2", "pins_use_r")).bounds.mean(0).tolist()
    P = json.loads((MESH / "v4" / "poses.json").read_text())
    rho = dict(zip(P["angles"], P["prop_rho"]))
    lift = P["pivot_z"] - P["pivot_in"]

    def v4_keys(seq):
        """seq: [frame, plate angle, prop angle]: the plate turns about its pivot, the prop about
        its hinge in the plate (both the file's own axes)."""
        return ([[f, [0, 0, lift], [th, 0, 0]] for f, th, _ in seq],
                [[f, [0, 0, 0], [r, 0, 0]] for f, _, r in seq])
    plate_k, prop_k = v4_keys([[1, 0, 0], [12, 0, 0], [32, 70, 0], [44, 70, rho[70]], [52, 70, rho[70]],
                               [62, 80, rho[80]], [70, 80, rho[80]], [84, 55, rho[55]], [92, 55, rho[55]],
                               [102, 55, 0], [118, 0, 0]])
    return {
        # 1. version 1 stands, then its pins slide out of the hinge, as on the first print
        "a_v1": (dict(frames=70, camera=dict(keys=[[1, 30, 16, 1.0], [70, 44, 18, 1.0]]), parts=[
            part(m("v1", "front"), LILAC), part(m("v1", "back"), WHITE),
            part(m("v1", "pins_use_l"), PINK, [[1, [0, 0, 0], 0], [38, [0, 0, 0], 0], [58, [-34, 0, 0], 0],
                                                [66, [-38, 0, -6], 0]]),
            part(m("v1", "pins_use_r"), PINK, [[1, [0, 0, 0], 0], [38, [0, 0, 0], 0], [58, [34, 0, 0], 0],
                                                [66, [38, 0, -6], 0]])]),
         dict(target=c1, radius=r1)),
        # 2. version 2: in close on the ratchet pin at the hinge's end
        "b_v2": (dict(frames=64, camera=dict(keys=[[1, 44, 18, 1.0, c1], [64, 64, 14, 2.4, pin]]), parts=[
            part(m("v2", "front"), LILAC), part(m("v2", "back"), WHITE),
            part(m("v2", "pins_use_l"), PINK), part(m("v2", "pins_use_r"), PINK)]),
         dict(target=c1, radius=r1)),
        # 3. version 3: three loose pieces settle into the easel, then lift apart again
        "c_v3": (dict(frames=90, camera=dict(keys=[[1, -125, 22, 0.95], [90, -105, 26, 1.0]]), parts=[
            part(m("v3", "base"), WHITE),
            part(m("v3", "plate"), LILAC, [[1, [0, 0, 70], 0], [10, [0, 0, 70], 0], [30, [0, 0, 0], 0],
                                           [62, [0, 0, 0], 0], [82, [0, 0, 45], 0]]),
            part(m("v3", "prop"), WHITE, [[1, [0, 0, 110], 0], [22, [0, 0, 110], 0], [42, [0, 0, 0], 0],
                                          [62, [0, 0, 0], 0], [82, [0, 0, 80], 0]])]),
         dict(target=[c3[0], c3[1], c3[2] + 12], radius=r3 * 1.15)),
        # 4. version 4: folded flat, it opens, steps through 70, 80 and 55 degrees, and folds again
        "d_v4": (dict(frames=124, camera=dict(keys=[[1, -135, 30, 1.0], [124, -105, 22, 1.0]]), parts=[
            part(m("v4", "base"), WHITE),
            dict(part(m("v4", "plate"), LILAC, plate_k), pivot=[0, 0, P["pivot_in"]]),
            dict(part(m("v4", "prop"), PINK, prop_k), pivot=[0, P["a"], P["hinge_in"]], parent=1)]),
         dict(target=[0, 60, 48], radius=108)),
    }


SEGMENTS = [
    dict(kind="frames", dir=str(SHOTS / "a_v1"), hold_start=0.8, hold_end=1.8, chip="RENDER", label="VERSION 1",
         captions=[[0, "Two plates on a hinge that should click at five angles."],
                   [2.1, "Our first print: no click at all, and the pin fell out."]]),
    dict(kind="frames", dir=str(SHOTS / "b_v2"), hold_end=2.8, chip="RENDER", label="VERSION 2",
         captions=[[0, "A ratchet, with buttons to release it. Still no click."],
                   [2.2, "Its teeth were 0.45 mm deep. Printing errors can add up to 0.75 mm."]]),
    dict(kind="frames", dir=str(SHOTS / "c_v3"), hold_start=0.6, hold_end=2.0, chip="RENDER", label="VERSION 3",
         captions=[[0, "So we started from the numbers: an easel, its angles set by deep notches."],
                   [2.8, "Our test print: good, but it needs to be 3 pieces that stay together."]]),
    dict(kind="frames", dir=str(SHOTS / "d_v4"), hold_start=1.2, hold_end=1.6, chip="RENDER", label="VERSION 4",
         captions=[[0, "The prop is hinged inside the plate, and the plate is pinned to the base."],
                   [2.8, "Six angles, from 80 down to 55 degrees..."],
                   [4.3, "...and it folds flat to 34 mm, with nothing to lose."]]),
    dict(kind="image", path=str(FS / "v4" / "images" / "fold_stand_v4_hinge_test.png"), dur=5.0, zoom=[1.35, 1.5], centre=[0.56, 0.6],
         chip="RENDER", label="TESTED FIRST", fade=0,
         captions=[[0, "We printed just the two hinges first. Our verdict: it works well."],
                   [2.6, "Next: the whole stand goes on the printer."]]),
]

STATUS = "waiting on Scott's approval (STANDARDS 8). Not posted."
SOURCES = [
    ("v1: two plates, a hinge clicking at five angles", "fold_stand/FOLD_STAND_PRINTING.md (form A, 2026-11-04: five openings, 81 to 57 deg)"),
    ("v1 print: no click, the pin fell out", "v2/FOLD_STAND_V2_PRINTING.md, \"Why v2\": Scott, \"No click at all. Very loose pin falls out.\""),
    ("v2: ratchet with release buttons; still no click", "v2/FOLD_STAND_V2_PRINTING.md; v3/ENGINEERING_v3.md, \"Why v3\" (Scott: \"pins don't click\")"),
    ("0.45 mm teeth; errors up to 0.75 mm", "v3/ENGINEERING_v3.md: \"v2's ratchet notch was 0.45 deep ... a tolerance stack of about 0.75 mm worst case\""),
    ("v3: easel, angles set by deep notches", "v3/ENGINEERING_v3.md sections 1-2 (Scott's pick, option A)"),
    ("v3 test print: good, needs 3 pieces that stay together", "v4/ENGINEERING_v4.md, \"Why v4\": Scott, \"It's good, but it needs to be 3 pieces that connect and stay together.\""),
    ("v4: prop hinged in the plate, plate pinned to the base; six angles 80-55; folds to 34 mm", "v4/FOLD_STAND_V4_PRINTING.md, \"How it works\""),
    ("Hinge test printed: it works well", "v4/FOLD_STAND_V4_PRINTING.md: Scott, 2026-11-14, \"It works well\""),
    ("The full stand isn't printed yet", "v4/FOLD_STAND_V4_PRINTING.md: \"The full stand itself isn't printed yet.\""),
    ("How each version is shown", "export_parts.py: each from its own .scad; v1/v2 stood by render_stand.py's stance; v3 by its pose(); v4 turned about its own PIVOT and hinge axes at prop_rho()'s angles"),
]


if __name__ == "__main__":
    for name, (s, cam) in shots().items():
        render_shots({name: s}, SHOTS, cam)
    if "--shots-only" in sys.argv:
        sys.exit()
    from compose import render as compose
    op, ec = kit(OUT, "FOLD STAND")
    tl = compose(SEGMENTS, OUT / "fold_stand_design.mp4", opener=op, endcard=ec)
    (OUT / "timeline.json").write_text(json.dumps(tl, indent=1))
    save_stills(SEGMENTS, OUT / "stills")
    write_script(tl, OUT / "SCRIPT.md", "Fold Stand", STATUS, SOURCES)
    print(f"{tl['total']:.1f} s")
