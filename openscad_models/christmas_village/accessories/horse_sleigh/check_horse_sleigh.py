#!/usr/bin/env python3
"""The full check set for the horse sleigh (2026-10-14): three printed pieces,
the sleigh on its snow and the horse's two halves lying on their cut faces.

    python3 check_horse_sleigh.py [step ...]

Run ./build.sh first. Steps as tools/model_checks.py. The colour renders are
made apart from it (render_scene.sh), of the horse standing in its sockets:
model_checks renders pieces as they lie on the plate.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "tools"))
from model_checks import run_checks  # noqa: E402

COL = {"body": "#A8483A", "roof": "#2E3440", "trim": "#F4F1EA", "accent": "#2F6B45"}
PIECES = ["sleigh", "near", "far"]


def parts(piece):
    return [(f"{piece}_{p}", COL[p]) for p in ("roof", "accent", "trim", "body") if (HERE / f"hs_{piece}_{p}.stl").exists()]


if __name__ == "__main__":
    steps = sys.argv[1:] or [s for s in ["parts", "gate", "cost", "3mf", "fidelity", "fragility", "as_printed", "viewer"]]
    run_checks(HERE, "hs", dict(
        label="Victorian Horse Sleigh",
        note="A black draught horse in harness pulling a red sleigh of presents through the snow. "
             "The horse prints in two halves lying flat and is glued on two filament dowels.",
        source="christmas_village/accessories/horse_sleigh/victorian_horse_sleigh.3mf",
        objects=[parts(p) for p in PIECES],
        unions=[f"hs_{p}_union.stl" for p in PIECES],
        tags=[f"_{p}" for p in PIECES],
        tag_labels={"_sleigh": " (sleigh)", "_near": " (horse, near half)", "_far": " (horse, far half)"},
    ), steps)
    # model_checks names the 3MF after the parts' stem; the notes and the
    # viewer give it its product name
    if (HERE / "hs.3mf").exists():
        (HERE / "hs.3mf").replace(HERE / "victorian_horse_sleigh.3mf")
