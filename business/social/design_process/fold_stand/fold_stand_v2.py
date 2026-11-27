#!/usr/bin/env python3
"""Fold Stand, from the design file: the v2 cut, template v2 (2026-11-27).

    python3 export_parts.py        # once: the four versions' meshes (as for the first cut)
    python3 fold_stand_v2.py       # render missing shots, then fold_stand_design_v2.mp4

Scott, via Greg: a new version beside the first cut, which stays as it is (fold_stand.py,
fold_stand_design.mp4). Same parts and facts. Fixed here:
  - v2's hinge flickered (0:09-0:11): the pins and knuckles share faces exactly with the plates
    they sit in, and the renderer swapped which one it drew. The pins are drawn 3% thinner and the
    back plate 0.2% narrower, so no two faces coincide. The video only; the parts are unchanged.
  - v3's pieces hung in the air (0:12-0:17): they came down from 70 and 110 mm and lifted apart
    again. Now they slide the last 25 mm into place, eased, and stay seated (the posed parts sit
    0.3-0.4 mm off the base: the real fit).
  - A phone on the stand: a plain 72 x 150 x 9 mm slab, standing on v4's shelf (a prop, labelled
    RENDER like everything else; FACTS: designed for a 250 g phone in a thick case).
No real footage of an assembled stand exists yet, so a marked placeholder holds the place for it.
"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import fold_stand as v1  # noqa: E402
from storyboard import part, render_shots, save_stills  # noqa: E402

OUT, MESH, FS = v1.OUT, v1.MESH, v1.FS
SHOTS = OUT / "shots_v2"
LILAC, WHITE, PINK = v1.LILAC, v1.WHITE, v1.PINK
PHONE, SCREEN = v1.lin("#2B2B31"), v1.lin("#0E1116")
PORT = dict(res=[1080, 1920], look="soft", samples=16, horizon_rgb=[1.22, 1.22, 1.22])
m = v1.m


def fixed(ver, name, sx=1.0, s=1.0):
    """A render-only copy without coincident faces: scaled about its own centre."""
    dst = MESH / ver / f"{name}_r.stl"
    if not dst.exists():
        mesh = trimesh.load(m(ver, name))
        c = mesh.bounds.mean(0)
        mesh.apply_translation(-c)
        mesh.apply_scale(1.0)
        mesh.vertices *= np.array([sx * s, s, s])
        mesh.apply_translation(c)
        mesh.export(dst)
    return dst


def phone(P):
    """A phone in the plate's print frame: on the plate's face (z = PLATE_T 8), its bottom edge on
    the shelf's inner face (y = SHELF_U 10, fold_stand_v4.scad), centred across the plate."""
    body, screen = MESH / "v4" / "phone_body.stl", MESH / "v4" / "phone_screen.stl"
    if not body.exists():
        b = trimesh.creation.box(extents=[72, 150, 9])
        b.apply_translation([0, 10.3 + 75, 8.05 + 4.5])
        b.export(body)
        sc = trimesh.creation.box(extents=[66, 140, 0.4])
        sc.apply_translation([0, 10.3 + 75, 8.05 + 9 + 0.2])
        sc.export(screen)
    return body, screen


def shots():
    c1, r1 = v1.centre("v1", ["front", "back"])
    c3, r3 = v1.centre("v3", ["base", "plate", "prop"])
    pin = trimesh.load(m("v2", "pins_use_r")).bounds.mean(0).tolist()
    P = json.loads((MESH / "v4" / "poses.json").read_text())
    rho = dict(zip(P["angles"], P["prop_rho"]))
    lift = P["pivot_z"] - P["pivot_in"]
    body, screen = phone(P)

    def v4(seq, phone_in=None):
        """seq: [frame, plate angle, prop angle]; phone_in: [frame from, frame seated], or None if
        the phone is on throughout."""
        plate = [[f, [0, 0, lift], [th, 0, 0]] for f, th, _ in seq]
        prop = [[f, [0, 0, 0], [r, 0, 0]] for f, _, r in seq]
        # the phone comes down the plate from above the frame; until the plate stands it's kept
        # hidden there (switched on off-screen, so nothing pops in)
        ph = [[1, [0, 0, 0], 0]] if phone_in is None else \
            [[1, [0, 320, 0], 0], [phone_in[0], [0, 320, 0], 0], [phone_in[1], [0, 0, 0], 0]]
        show = {} if phone_in is None else {"show": [phone_in[0] - 8, 100000]}
        piv = [0, 0, P["pivot_in"]]
        return [part(m("v4", "base"), WHITE),
                dict(part(m("v4", "plate"), LILAC, plate), pivot=piv),
                dict(part(m("v4", "prop"), PINK, prop), pivot=[0, P["a"], P["hinge_in"]], parent=1),
                dict(part(body, PHONE, ph), pivot=piv, parent=1, roughness=0.5, **show),
                dict(part(screen, SCREEN, ph), pivot=piv, parent=1, roughness=0.15, **show)]

    v4cam = dict(target=[0, 60, 60], radius=112)
    return {
        # the payoff: the finished stand holding a phone, going from 70 to 60 degrees (seen from the
        # front: the phone is on the plate's front face, the prop behind)
        "p_payoff": (dict(PORT, frames=66, camera=dict(keys=[[1, 28, 16, 1.0], [66, 48, 14, 1.04]]),
                          parts=v4([[1, 70, rho[70]], [16, 70, rho[70]], [56, 60, rho[60]], [66, 60, rho[60]]])),
                     v4cam),
        # version 1 stands, then its pins slide out of the hinge, as on the first print
        "a_v1": (dict(PORT, frames=78, camera=dict(keys=[[1, 30, 16, 1.0], [78, 44, 18, 1.04]]), parts=[
            part(m("v1", "front"), LILAC), part(fixed("v1", "back", sx=0.998), WHITE),
            part(fixed("v1", "pins_use_l", s=0.97), PINK, [[1, [0, 0, 0], 0], [30, [0, 0, 0], 0], [56, [-34, 0, 0], 0],
                                                           [68, [-38, 0, -6], 0]]),
            part(fixed("v1", "pins_use_r", s=0.97), PINK, [[1, [0, 0, 0], 0], [30, [0, 0, 0], 0], [56, [34, 0, 0], 0],
                                                           [68, [38, 0, -6], 0]])]),
         dict(target=c1, radius=r1)),
        # version 2: in close on the ratchet pin at the hinge's end (no coincident faces: no flicker)
        "b_v2": (dict(PORT, frames=78, camera=dict(keys=[[1, 44, 18, 1.0, c1], [70, 64, 14, 2.4, pin], [78, 64, 14, 2.4, pin]]),
                      parts=[
            part(m("v2", "front"), LILAC), part(fixed("v2", "back", sx=0.998), WHITE),
            part(fixed("v2", "pins_use_l", s=0.97), PINK), part(fixed("v2", "pins_use_r", s=0.97), PINK)]),
         dict(target=c1, radius=r1)),
        # version 3: the plate and prop slide the last 25 mm into the easel and stay seated
        "c_v3": (dict(PORT, frames=84, camera=dict(keys=[[1, -128, 22, 1.0], [84, -108, 24, 1.04]]), parts=[
            part(m("v3", "base"), WHITE),
            part(m("v3", "plate"), LILAC, [[1, [0, 0, 25], 0], [6, [0, 0, 25], 0], [30, [0, 0, 0], 0]]),
            part(m("v3", "prop"), WHITE, [[1, [0, 0, 25], 0], [22, [0, 0, 25], 0], [46, [0, 0, 0], 0]])]),
         dict(target=[c3[0], c3[1], c3[2] + 12], radius=r3 * 1.15)),
        # version 4: folded flat, it opens to 70, the phone goes on, then 80 and down to 55
        "d_v4": (dict(PORT, frames=108, camera=dict(keys=[[1, 62, 30, 1.0], [108, 44, 18, 1.0]]),
                      parts=v4([[1, 0, 0], [8, 0, 0], [28, 70, 0], [38, 70, rho[70]], [58, 70, rho[70]],
                                [70, 80, rho[80]], [76, 80, rho[80]], [96, 55, rho[55]], [108, 55, rho[55]]],
                               phone_in=[40, 56])),
         v4cam),
    }


SEGMENTS = [
    dict(kind="frames", dir=str(SHOTS / "p_payoff"), hold_end=0.6, chip="RENDER", fade=0.2,
         big=[[1.0, "4 VERSIONS TO GET HERE"]]),
    dict(kind="rewind", dirs=[str(SHOTS / s) for s in ("a_v1", "b_v2", "c_v3", "d_v4")], dur=0.8,
         chip="RENDER", fade=0.15, big=[[0, "REWIND"]]),
    dict(kind="frames", dir=str(SHOTS / "a_v1"), hold_end=0.2, chip="RENDER", label="VERSION 1",
         captions=[[0, "A hinge meant to click at five angles. On our print: no click, and the pin fell out."]]),
    dict(kind="frames", dir=str(SHOTS / "b_v2"), hold_end=0.2, chip="RENDER", label="VERSION 2",
         captions=[[0, "A ratchet. Its teeth were 0.45 mm deep; printing errors can add up to 0.75 mm. No click."]]),
    dict(kind="frames", dir=str(SHOTS / "c_v3"), hold_end=0.2, chip="RENDER", label="VERSION 3",
         captions=[[0, "An easel set by deep notches. Our test: good, but the 3 pieces need to stay together."]]),
    dict(kind="frames", dir=str(SHOTS / "d_v4"), hold_end=0.3, chip="RENDER", label="VERSION 4",
         captions=[[0, "Folds flat, then six angles: 80 down to 55 degrees."]]),
    dict(kind="image", path=str(FS / "v4" / "images" / "fold_stand_v4_hinge_test.png"), dur=2.4, zoom=[1.0, 1.12],
         centre=[0.56, 0.6], chip="RENDER", label="TESTED FIRST",
         captions=[[0, "We printed just the hinges first. Our verdict: it works well."]]),
    dict(kind="placeholder", dur=2.8, chip="PLACEHOLDER", label="COMING NEXT",
         lines=["OUR REAL CLIP GOES HERE", "The printed stand holding a phone, opening up. 9:16, about 3 s."]),
]

STATUS = ("waiting on Scott's approval (STANDARDS 8). Not posted. Not postable until the placeholder holds "
          "Scott's clip: the full v4 stand isn't printed yet.")
SOURCES = v1.SOURCES + [
    ("4 versions to get here", "fold_stand/, v2/, v3/, v4/: one .scad each"),
    ("The phone", "a plain 72 x 150 x 9 mm slab drawn for the video, on v4's shelf (SHELF_U 10, PLATE_T 8); "
                  "v4 is designed for a 250 g phone in a thick case (ENGINEERING_v4.md section 1)"),
    ("Folds flat; six angles 80 to 55", "v4/FOLD_STAND_V4_PRINTING.md, \"How it works\"; poses.json"),
]


if __name__ == "__main__":
    for name, (s, cam) in shots().items():
        render_shots({name: s}, SHOTS, cam)
    if "--shots-only" in sys.argv:
        sys.exit()
    from compose_v2 import render as compose, write_script
    tl = compose(SEGMENTS, OUT / "fold_stand_design_v2.mp4")
    (OUT / "timeline_v2.json").write_text(json.dumps(tl, indent=1))
    save_stills(SEGMENTS, OUT / "stills_v2")
    write_script(tl, OUT / "SCRIPT_v2.md", "Fold Stand", STATUS, SOURCES)
    print(f"{tl['total']:.1f} s")
