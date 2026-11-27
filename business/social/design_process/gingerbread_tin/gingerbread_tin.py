#!/usr/bin/env python3
"""Gingerbread Tin, from the design file: prototype to colour canister (2026-11-26).

Scott, 2026-11-26: "we need more like that from other builds and how different versions were
made from prototype prints and how they were designed."

    python3 export_versions.py           # the four versions' meshes, from git
    python3 gingerbread_tin.py           # render missing shots, then the video

Every version on screen is the repo's own source at the commit where it was current
(export_versions.py says which). Every figure is from openscad_models/clickers/CLICKERS_PRINTING.md
or the scad at that commit; SCRIPT.md lists the sources.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from storyboard import cut, kit, part, render_shots, write_script  # noqa: E402

ROOT = HERE.parents[3]
OUT = HERE.parent / "out" / "gingerbread_tin"
MESH = OUT / "meshes"
SHOTS = OUT / "shots"
REAL = ROOT / "openscad_models" / "clickers" / "gingerbread_tin" / "real"

def lin(hexcol):
    """A design colour (sRGB hex) as the linear RGB a Blender material takes. Given the sRGB
    numbers directly, the red tin rendered pink (2026-11-26)."""
    c = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


# the clicker's own filament colours (CLICKERS_PRINTING.md): red, white, green, brown; the switch grey
RED, WHITE, GREEN, BROWN, SW = lin("#B3262E"), lin("#F4F1EA"), lin("#3E8E4A"), lin("#9A5B2E"), lin("#8A8A90")
PROTO = [0.95, 0.94, 0.91]                   # the white prototype, printed in one white
PRESS = 4.0                                  # mx_travel: the cookie's press
CAM = {"target": [0, 0, 16], "radius": 40}  # the clicker
CAN_CAM = {"target": [0, 0, 32], "radius": 52}
SEAM = [26.5, 0, 47.5]                       # aims at the collar: the seam (z ~50), thread and guide ring below it

LID_GROUP = ["lid", "lid_holly", "lid_snow", "mx", "cookie", "cookie_icing", "cookie_red", "cookie_green"]
COLOURS = {"tin": RED, "tin_snow": WHITE, "canister": RED, "canister_snow": WHITE, "lid": RED,
           "lid_holly": GREEN, "lid_snow": WHITE, "mx": SW, "cookie": BROWN, "cookie_icing": WHITE,
           "cookie_red": RED, "cookie_green": GREEN}


CUT_LID = lin("#F4F1EA")   # in the cutaways the lid is shown white: red on red, the seam and thread vanished


def parts(ver, names, keys=None, white=False, clip=False, cutaway=False, lid_tint=None):
    """`keys` maps a name (or "lid_group") to its keyframes."""
    out = []
    for n in names:
        p = MESH / ver / f"{n}.stl"
        if not p.exists():      # a missing part would quietly vanish from the shot: stop instead
            raise SystemExit(f"no mesh {p}: run export_versions.py {ver}")
        if cutaway:
            p = cut(p, MESH / ver / f"cut_{n}.stl")
        k = (keys or {}).get(n) or ((keys or {}).get("lid_group") if n in LID_GROUP else None)
        rgb = SW if n == "mx" else (PROTO if white else COLOURS[n])
        if lid_tint and n == "lid":
            rgb = lid_tint
        out.append(part(p, rgb, k, clip))
    return out


def screw(f0, f1, turns, pitch, z_above=0.0, f_drop=None):
    """Keys for a lid that drops to its thread, then screws down `turns` clockwise (right-hand)."""
    rise = turns * pitch
    k = []
    if f_drop is not None:
        k += [[f_drop, [0, 0, z_above], turns * 360]]
    k += [[f0, [0, 0, rise], turns * 360], [f1, [0, 0, 0], 0]]
    return k


CLICKER = ["tin", "tin_snow"] + LID_GROUP
CANISTER = ["canister", "canister_snow"] + LID_GROUP


def shots():
    return {
        # 1. the first design: the parts come together, then the cookie presses and clicks
        "a_v1": dict(frames=64, camera=dict(keys=[[1, 30, 34, 0.85], [64, 38, 30, 1.0]]), parts=parts("v1", CLICKER, {
            "lid": [[1, [0, 0, 40], 0], [22, [0, 0, 0], 0]], "lid_holly": [[1, [0, 0, 40], 0], [22, [0, 0, 0], 0]],
            "lid_snow": [[1, [0, 0, 40], 0], [22, [0, 0, 0], 0]],
            "mx": [[1, [0, 0, 60], 0], [10, [0, 0, 60], 0], [30, [0, 0, 0], 0]],
            **{c: [[1, [0, 0, 80], 0], [22, [0, 0, 80], 0], [40, [0, 0, 0], 0], [48, [0, 0, 0], 0],
                   [51, [0, 0, -PRESS], 0], [56, [0, 0, 0], 0]]
               for c in ("cookie", "cookie_icing", "cookie_red", "cookie_green")}}, white=True)),
        # 3. version 2: the same clicker, its lid now screws on (2.7 pitch, 1.6 turns)
        "c_v2_lin": dict(frames=70, camera=dict(keys=[[1, 24, 26, 0.9], [70, 34, 30, 1.0]]), parts=parts("v2", CLICKER, {
            "lid_group": screw(18, 66, 1.6, 2.7, z_above=40, f_drop=1)})),
        # 4. the canister: the clicker becomes its lid (the first canister, 2026-11-03)
        "d_can1_lin": dict(frames=70, camera=dict(keys=[[1, 30, 24, 0.9], [70, 36, 20, 1.0]]), parts=parts("can1", CANISTER, {
            "lid_group": screw(18, 66, 1.6, 2.7, z_above=50, f_drop=1)})),
        # 5. swing to face it and cut through
        "e_can1_cut_w": dict(frames=64, camera=dict(keys=[[1, 36, 20, 1.0], [28, 0, 6, 1.0]]),
                           clip_keys=[[1, -200], [28, -40], [60, 0]], parts=parts("can1", CANISTER, clip=True, lid_tint=CUT_LID)),
        # 5b. the cut faces, then in close on the seam and the thread
        "f_can1_seam_w": dict(frames=40, camera=dict(keys=[[1, 0, 6, 1.0], [8, 0, 6, 1.0], [40, 0, 4, 4.0, SEAM]]),
                            parts=parts("can1", CANISTER, cutaway=True, lid_tint=CUT_LID)),
        # 6. the same close-up of today's: the picture dissolves from the old to this
        "g_now_seam_w": dict(frames=1, camera=dict(keys=[[1, 0, 4, 4.0, SEAM]]), parts=parts("now", CANISTER, cutaway=True, lid_tint=CUT_LID)),
        # 6b. pull back from today's cut, and close it up whole again
        "h_now_out_w": dict(frames=36, camera=dict(keys=[[1, 0, 4, 4.0, SEAM], [36, 0, 6, 1.0]]),
                          parts=parts("now", CANISTER, cutaway=True, lid_tint=CUT_LID)),
        # 7. today's canister, whole: turn it, then press the cookie
        "i_now": dict(frames=70, camera=dict(keys=[[1, 0, 6, 1.0], [40, 32, 22, 0.95], [70, 40, 26, 1.0]]),
                      parts=parts("now", CANISTER, {
                          c: [[1, [0, 0, 0], 0], [50, [0, 0, 0], 0], [54, [0, 0, -PRESS], 0], [60, [0, 0, 0], 0]]
                          for c in ("cookie", "cookie_icing", "cookie_red", "cookie_green")})),
    }


def cams():
    return {k: (CAM if k in ("a_v1", "c_v2_lin") else CAN_CAM) for k in shots()}


SEGMENTS = [
    dict(kind="frames", dir=str(SHOTS / "a_v1"), hold_end=0.5, chip="RENDER", label="THE IDEA",
         captions=[[0, "A gingerbread cookie you press into a Christmas tin..."],
                   [1.4, "...and it clicks on a real keyboard switch."]]),
    dict(kind="video", path=str(REAL / "tin_clicker_white_timelapse_2026-10-30.mp4"), start=0, dur=2.6,
         crop="480:480:380:90", chip="REAL", label="FIRST PRINT",
         captions=[[0, "The first print, all in white, to test it."]]),
    dict(kind="image", path=str(REAL / "photos" / "02-photo-lid-and-base.jpg"), dur=2.4, zoom=[1.0, 1.1],
         centre=[0.5, 0.42], chip="REAL", label="FIRST PRINT",
         captions=[[0, "It clicked fine, but the lid just sat on top, loose."]]),
    dict(kind="frames", dir=str(SHOTS / "c_v2_lin"), hold_end=0.4, chip="RENDER", label="VERSION 2",
         captions=[[0, "So version 2 got a thread: the lid screws down."]]),
    dict(kind="frames", dir=str(SHOTS / "d_can1_lin"), hold_end=0.4, chip="RENDER", label="THEN A CANISTER",
         captions=[[0, "Then a tin that holds things, with the clicker as its lid."]]),
    dict(kind="frames", dir=str(SHOTS / "e_can1_cut_w"), chip="RENDER", fade=0.4, label="THE FIRST CANISTER",
         captions=[[0, "We printed it, then cut the design in half to look closer."]]),
    dict(kind="frames", dir=str(SHOTS / "f_can1_seam_w"), hold_end=1.8, chip="RENDER (CUTAWAY)", fade=0.7,
         label="THE FIRST CANISTER", captions=[[0, "A 3.4 mm gap under the lid, on a fine 2.7 mm thread."]]),
    dict(kind="frames", dir=str(SHOTS / "g_now_seam_w"), hold_end=3.8, chip="RENDER (CUTAWAY)", fade=0.3,
         label="AFTER THAT PRINT", captions=[[0, "Now: a 1.86 mm seam and a deeper, coarser 4 mm thread..."],
                                             [2.2, "...and a guide ring, so the lid can't cross-thread."]]),
    dict(kind="frames", dir=str(SHOTS / "h_now_out_w"), chip="RENDER (CUTAWAY)", fade=0.3, label="AFTER THAT PRINT",
         captions=[[0, "...and a guide ring, so the lid can't cross-thread."]]),
    dict(kind="frames", dir=str(SHOTS / "i_now"), hold_end=0.4, chip="RENDER", label="TODAY",
         captions=[[0, "62 mm across, it holds your sweets, and it still clicks."]]),
    dict(kind="video", path=str(REAL / "canister_colour_timelapse.mp4"), start=1.0, dur=3.0,
         crop="560:560:180:120", chip="REAL", label="IN COLOUR",
         captions=[[0, "Printed in colour: red, gold snowflakes..."]]),
    dict(kind="image", path=str(REAL / "photos" / "05-photo-canister-1.jpg"), dur=2.8, zoom=[1.0, 1.12],
         centre=[0.5, 0.55], chip="REAL", label="IN COLOUR", fade=0,
         captions=[[0, "...and the gingerbread cookie on top."]]),
]

STATUS = "waiting on Scott's approval (STANDARDS 8). Not posted."
SOURCES = [
    ("Presses into a tin; clicks on a keyboard switch", "CLICKERS_PRINTING.md, Gingerbread Tin (MX switch, plate mount)"),
    ("First print, all in white", "real/tin_clicker_white_timelapse_2026-10-30.mp4 and real/photos/01-04 (Benson's media pack)"),
    ("It clicked fine, but the lid sat loose", "CLICKERS_PRINTING.md, \"The lid screws on (2026-10-30)\": \"Your first test print clicked fine, but the lid sat loose.\""),
    ("Version 2 screws down", "commit 965fa247 (2.7 pitch, 1.6 turns); the v1 shown is e56e99f3, the lid pressed on"),
    ("A tin that holds things, the clicker as its lid", "CLICKERS_PRINTING.md, Canister (2026-10-30 ask); the canister shown is b5c6490a, the version printed before 2026-11-05"),
    ("3.4 mm gap; 2.7 mm thread", "CLICKERS_PRINTING.md, \"the gap opened to 3.4 mm at the outside\"; b5c6490a TH_P = 2.7"),
    ("1.86 mm seam; 4 mm thread; guide ring", "CLICKERS_PRINTING.md, \"Changed after your print (2026-11-05)\"; TH_P = 4.0, TH_D = 1.2; RING_H"),
    ("62 mm across; holds things; still clicks", "CLICKERS_PRINTING.md, Canister: \"62 mm across\", \"a tin that actually holds things, with the lid as the clicker\" (its 86 cm³ predates the guide ring, so no figure on screen)"),
    ("Red, gold snowflakes, cookie on top", "real/canister_colour_timelapse.mp4 and real/photos/05-08"),
]


if __name__ == "__main__":
    for name, s in shots().items():
        render_shots({name: s}, SHOTS, cams()[name])
    if "--shots-only" in sys.argv:
        sys.exit()
    from compose import render as compose
    op, ec = kit(OUT, "GINGERBREAD TIN")
    tl = compose(SEGMENTS, OUT / "gingerbread_tin_design.mp4", opener=op, endcard=ec)
    (OUT / "timeline.json").write_text(json.dumps(tl, indent=1))
    write_script(tl, OUT / "SCRIPT.md", "Gingerbread Tin", STATUS, SOURCES)
    print(f"{tl['total']:.1f} s")
