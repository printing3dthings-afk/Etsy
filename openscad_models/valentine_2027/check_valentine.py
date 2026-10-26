#!/usr/bin/env python3
"""Run the full check set on a built Valentine's piece (2026-10-26). The steps
live in tools/model_checks.py; this file only describes the pieces.

    python3 check_valentine.py standing_heart [step ...]

Run <piece>/build.sh cgal and <piece>/build.sh union first. Results land in
<piece>/logs and <piece>/images.

Every piece prints in one colour, matte white (Scott's brief). The colours
below are only for the colour render, so the parts can be told apart.

gate_args: the glowing panes are 0.9 mm on purpose (Scott, 2026-10-26: glow
sections thin, 0.8-1.0 mm, so they light properly). At the gate's 1.2 mm
floor they fail min_wall by design, so the wall floor drops to 0.8 for these
pieces only; every structural wall round them is still 1.2 mm or more.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from model_checks import run_checks  # noqa: E402

RED, WHITE, WINE, GOLD = "#B8323F", "#F4F1EA", "#7A1F2B", "#D4A64A"
PIECES = {
    "standing_heart": dict(
        name="standing_heart_lantern",
        label="Standing Heart Love Lantern",
        note="A heart standing in a pedestal over a battery tealight, personalised with two names and a "
             "date. Unlit its faces are plain; lit, a couple under a lamppost shows on the front and two "
             "swans whose necks draw a heart on the back, dark on the glow. One piece, matte white.",
        objects=[[("frame", RED), ("glass", WHITE), ("art", WINE), ("lip", WHITE), ("text", GOLD)]],
        unions=["standing_heart_lantern_union.stl"], light_z=22),
    # three prints on one plate: the drum, the lid (stood on the rim's top, ZT
    # in the .scad, for the renders and the fit check) and the crown, printed
    # flat and shown standing in the lid's slot
    "swan_crown": dict(
        name="swan_crown_lantern",
        label="Swan Crown Love Lantern",
        note="A glowing drum with a pond at night built into the inside of its glass: lit, two swans "
             "glide to meet under a heart among reeds and a crescent moon. On the lid, two swans whose "
             "necks draw a heart. Names and date on the plinth. Three prints, matte white.",
        objects=[[("frame", RED), ("glass", WHITE), ("art", WINE), ("text", GOLD)], [("lid", RED)], [("crown", GOLD)]],
        unions=["swan_crown_lantern_drum_union.stl", "swan_crown_lantern_lid_union.stl",
                "swan_crown_lantern_crown_union.stl"], light_z=24,
        tags=["_drum", "_lid", "_crown"], tag_labels={"_drum": " (drum)", "_lid": " (lid)", "_crown": " (crown)"},
        shown={1: [0, 0, 85.0]}, shown_mesh={"crown": "swan_crown_lantern_crown_shown.stl"}),
}


if __name__ == "__main__":
    key = sys.argv[1]
    P = PIECES[key]
    cfg = dict(label=P["label"], note=P["note"], objects=P["objects"], unions=P["unions"],
               source=f"valentine_2027/{key}/{P['name']}.3mf",
               night=(HERE.parent / "christmas_lanterns" / "concepts" / "night_render.py", P["light_z"]),
               gate_args=["--wall", "0.8"])
    for k in ("tags", "tag_labels", "shown", "shown_mesh"):
        if k in P:
            cfg[k] = P[k]
    run_checks(HERE / key, P["name"], cfg, sys.argv[2:] or None)
