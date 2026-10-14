#!/usr/bin/env python3
"""Run the full check set on a built lantern (2026-10-13; the steps moved to
tools/model_checks.py on 2026-10-14, when the village accessories became the
check set's second user. This file now only describes the lanterns).

    python3 check_lantern.py hex_lantern|drum_lantern|gift_box_lantern [step ...]

steps (default all, in order): parts gate cost 3mf fidelity fragility colour
night as_printed viewer. cost slices each one-body union in one colour and
times it with the P1S motion model, the same clock the viewer uses. Every result lands in <lantern>/logs and <lantern>/images,
the same layout the village buildings use. Run <lantern>/build.sh and
build.sh union first.

The gift box prints as two objects (box, lid). The lid is built standing on
the plate, so the colour and night renders take a copy lifted onto the box.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from model_checks import run_checks  # noqa: E402

SLATE, WHITE, RED, GREEN = "#2E3440", "#F4F1EA", "#C62F3A", "#2F6B45"
LANTERNS = {
    "hex_lantern": dict(
        label="Hex Carriage Lantern",
        note="A six-sided carriage lantern with a Christmas scene standing out of each glass panel, "
             "a snowy pointed roof, a red bow and a hanging ring. Lit by a tealight underneath, the "
             "scenes show dark on the glow even printed all in white.",
        objects=[[("frame", SLATE), ("glass", WHITE), ("art", SLATE), ("snow", WHITE), ("bow", RED)]],
        unions=["hex_lantern_union.stl"], light_z=30),
    "drum_lantern": dict(
        label="Panorama Drum Lantern",
        note="One unbroken Christmas Eve wraps all the way round a glass drum: a village and its church, "
             "the village tree, reindeer in a forest, a snowman, and Santa crossing the moon. Lit by a "
             "tealight underneath, it shows dark on the glow even printed all in white.",
        objects=[[("frame", SLATE), ("glass", WHITE), ("art", SLATE), ("bead", WHITE), ("drape", WHITE)]],
        unions=["drum_lantern_union.stl"], light_z=30),
    "gift_box_lantern": dict(
        label="Gift Box Lantern",
        note="A present with glass sides and a Christmas scene on each, tied with a red ribbon and bow. "
             "The lid lifts off to put a tealight inside; the box and lid print side by side.",
        objects=[[("frame", GREEN), ("glass", WHITE), ("art", GREEN)], [("lid", GREEN), ("ribbon", RED)]],
        unions=["gift_box_lantern_box_union.stl", "gift_box_lantern_lid_union.stl"], light_z=32,
        lid_lift=64.0),   # zr in gift_box_lantern.scad
}


if __name__ == "__main__":
    name = sys.argv[1]
    L = dict(LANTERNS[name])
    cfg = dict(label=L["label"], note=L["note"], objects=L["objects"], unions=L["unions"],
               source=f"christmas_lanterns/{name}/{name}.3mf",
               night=(HERE / "concepts" / "night_render.py", L["light_z"]))
    if "lid_lift" in L:
        cfg.update(tags=["_box", "_lid"], tag_labels={"_box": " (box)", "_lid": " (lid)"},
                   shown={1: [0, 0, L["lid_lift"]]})
    run_checks(HERE / name, name, cfg, sys.argv[2:] or None)
