#!/usr/bin/env python3
"""Pie Drum Caddy v2, from the design file: the pilot design-process video (2026-11-26).

    python3 pie_caddy_v2.py              # render missing shots, then the video
    python3 pie_caddy_v2.py --shots-only

Needs the v2 parts exported to openscad_models/pie_caddy/parts_v2/ (base, drum, keeper_seated:
see the scad's `part` list) and Scott's keeper-coupon timelapse (LFS). Every figure in a caption
is from openscad_models/pie_caddy/FACTS.md and ENGINEERING_v2.md; see SCRIPT.md for the sources.
"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

from storyboard import cut, kit, part, render_shots, save_stills, write_script

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PC = ROOT / "openscad_models" / "pie_caddy"
P = PC / "parts_v2"
OUT = HERE / "out" / "pie_caddy_v2"
SHOTS = OUT / "shots" / "v2"           # v1: the flat first look, before the shadow fix
MESH = OUT / "meshes"
REAL = PC / "real" / "keeper_coupon_timelapse_2026-11-26.mp4"

BASE, BB, DRUM, KEEP = [0.42, 0.29, 0.23], [0.93, 0.80, 0.25], [0.91, 0.72, 0.54], [0.95, 0.92, 0.85]
SEAT = 9.0                      # BASE_T + BALL: the drum's underside on the balls
CAM = {"target": [0, 0, 70], "radius": 96}


def meshes():
    MESH.mkdir(parents=True, exist_ok=True)
    balls = MESH / "balls.stl"
    if not balls.exists():
        bs = [trimesh.creation.icosphere(subdivisions=2, radius=3).apply_translation([50 * np.cos(a), 50 * np.sin(a), 6])
              for a in np.linspace(0, 2 * np.pi, 46, endpoint=False)]
        trimesh.util.concatenate(bs).export(balls)
    src = {"base": P / "base.stl", "drum": P / "drum.stl", "keeper": P / "keeper_seated.stl", "balls": balls}
    out = {k: str(v) for k, v in src.items()}
    out.update({"cut_" + k: cut(v, MESH / f"cut_{k}.stl") for k, v in src.items()})
    return out


def shots(m):
    still = lambda z: [[1, [0, 0, z], 0]]
    return {
        # 1. without a keeper, the drum just lifts off
        # (aimed higher and wider than the rest: at 0.9 the lifted drum left the top of the frame)
        "a_lift_v3": dict(frames=40, camera=dict(target=[0, 0, 100], keys=[[1, 35, 20, 0.72], [40, 40, 20, 0.72]]),
                          parts=[
            part(m["base"], BASE), part(m["balls"], BB),
            part(m["drum"], DRUM, [[1, [0, 0, SEAT], 0], [8, [0, 0, SEAT], 0], [34, [0, 0, SEAT + 70], 0]])]),
        # 2. the drum back down, then the keeper drops in and screws home: three turns clockwise
        # (it opens on shot 1's last framing, then settles in as the drum comes down)
        "b_keeper_v3": dict(frames=84, camera=dict(keys=[[1, 40, 20, 0.72, 100], [20, 38, 24, 0.9, 74],
                                                         [84, 32, 30, 1.0, 70]]), parts=[
            part(m["base"], BASE), part(m["balls"], BB),
            part(m["drum"], DRUM, [[1, [0, 0, SEAT + 70], 0], [16, [0, 0, SEAT], 0]]),
            part(m["keeper"], KEEP, [[1, [0, 0, 230], 0], [16, [0, 0, 230], 0], [36, [0, 0, 12], 0],
                                     [80, [0, 0, 0], -1080]])]),
        # 3. swing round to face it, then a cut sweeps through to the middle
        "c_cut": dict(frames=66, camera=dict(keys=[[1, 32, 30, 1.0], [30, 0, 6, 1.05]]),
                      clip_keys=[[1, -200], [30, -90], [62, 0]], parts=[
            part(m["base"], BASE, clip=True), part(m["balls"], BB, clip=True),
            part(m["drum"], DRUM, still(SEAT), clip=True), part(m["keeper"], KEEP, clip=True)]),
        # 3b. the same view, as solid cut faces (what the cut sweep lands on)
        "c_section": dict(frames=1, camera=dict(keys=[[1, 0, 6, 1.05]]), parts=[
            part(m["cut_base"], BASE), part(m["cut_balls"], BB),
            part(m["cut_drum"], DRUM, still(SEAT)), part(m["cut_keeper"], KEEP)]),
        # 5. whole again: it turns on the balls, then lifts in one piece
        "e_final": dict(frames=100, camera=dict(keys=[[1, 0, 6, 1.05, 70], [50, 35, 24, 0.95, 70],
                                                      [60, 36, 24, 0.95, 70], [100, 42, 20, 0.8, 92]]),
                        parts=[
            part(m["base"], BASE, [[1, [0, 0, 0], 0], [60, [0, 0, 0], 0], [86, [0, 0, 40], 0]]),
            part(m["balls"], BB, [[1, [0, 0, 0], 0], [56, [0, 0, 0], -60], [60, [0, 0, 0], -60],
                                  [86, [0, 0, 40], -60]]),
            part(m["drum"], DRUM, [[1, [0, 0, SEAT], 0], [56, [0, 0, SEAT], -120], [60, [0, 0, SEAT], -120],
                                   [86, [0, 0, SEAT + 40], -120]]),
            part(m["keeper"], KEEP, [[1, [0, 0, 0], 0], [60, [0, 0, 0], 0], [86, [0, 0, 40], 0]])]),
    }


def render():
    render_shots(shots(meshes()), SHOTS, CAM)


SEGMENTS = [
    dict(kind="frames", dir=str(SHOTS / "a_lift_v3"), hold_start=0.4, hold_end=0.6, chip="RENDER",
         label="THE PROBLEM", captions=[[0, "It turns on BBs. But without a keeper, pick it up and the drum comes straight off."]]),
    dict(kind="frames", dir=str(SHOTS / "b_keeper_v3"), hold_end=0.8, chip="RENDER",
         label="THE FIX: A KEEPER CUP", captions=[[0, "A pen cup that drops into the middle..."],
                                                  [1.2, "...and screws onto the post. About three turns."]]),
    dict(kind="frames", dir=str(SHOTS / "c_cut"), chip="RENDER", fade=0.5,
         label="INSIDE", captions=[[0, "Cut it in half to see how it holds."]]),
    dict(kind="frames", dir=str(SHOTS / "c_section"), hold_end=3.2, chip="RENDER (CUTAWAY)",
         label="INSIDE", captions=[[0, "A cone stops the cup 0.5 mm above a ledge in the drum."],
                                   [1.6, "The drum still spins, but it can't lift off."]]),
    dict(kind="video", path=str(REAL), start=2.6, dur=3.4, crop="560:560:360:140", chip="REAL",
         label="TESTED FIRST", captions=[[0, "We printed just the thread first. Our verdict here at OBC: great."]]),
    dict(kind="frames", dir=str(SHOTS / "e_final"), hold_end=1.2, chip="RENDER", fade=0,
         label="READY TO PRINT", captions=[[0, "It still turns on 46 BBs..."],
                                           [2.0, "...and now it lifts in one piece."]]),
]


# where each claim on screen comes from (repo paths), for SCRIPT.md
SOURCES = [
    ("Turns on BBs; v1 has nothing locking the drum on", "openscad_models/pie_caddy/FACTS.md (v1: \"Nothing locks it on\")"),
    ("The keeper screws onto the post, about three turns", "pie_caddy/ENGINEERING_v2.md section 2: 12.4 mm of full thread at 4 mm pitch, just over 3 turns"),
    ("Stops 0.5 mm above a ledge; drum spins but can't lift off", "ENGINEERING_v2.md sections 2 and 5 (KEEP_GAP 0.5; fit: lifts 0.45, caught at 0.5)"),
    ("Thread printed first; \"great\"", "Scott, 2026-11-26: \"Test piece was great for the drum caddy\"; footage pie_caddy/real/keeper_coupon_timelapse_2026-11-26.mp4"),
    ("46 BBs", "FACTS.md: 46 airsoft BBs, 6 mm"),
    ("Lifts in one piece", "ENGINEERING_v2.md section 1 (the requirement) and section 3 (40 N design load vs ~1.4 kN thread strip)"),
]


STATUS = ("approved by Scott, 2026-11-26 (\"That video for the caddy is awesome\"), with the tested step "
          "reading \"Our verdict here at OBC\" instead of his name. Ready for Benson to post.")


if __name__ == "__main__":
    render()
    if "--shots-only" in sys.argv:
        sys.exit()
    from compose import render as compose
    op, ec = kit(OUT, "PIE DRUM CADDY V2")
    tl = compose(SEGMENTS, OUT / "pie_caddy_v2_design.mp4", opener=op, endcard=ec)
    (OUT / "timeline.json").write_text(json.dumps(tl, indent=1))
    save_stills(SEGMENTS, OUT / "stills")
    write_script(tl, OUT / "SCRIPT.md", "Pie Drum Caddy v2", STATUS, SOURCES)
    print(f"{tl['total']:.1f} s")
