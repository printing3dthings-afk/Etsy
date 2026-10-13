#!/usr/bin/env python3
"""The full check set for one Victorian village accessory (2026-10-13):

    python3 check_accessory.py pillar_box [step ...]

Run ./build.sh <piece> first. Steps and results as tools/model_checks.py.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from model_checks import run_checks  # noqa: E402

BRICK, SLATE, WHITE, GREEN = "#A8483A", "#2E3440", "#F4F1EA", "#2F6B45"
COLOURS = {"body": BRICK, "roof": SLATE, "trim": WHITE, "accent": GREEN}
PIECES = {
    "pillar_box": ("Victorian Pillar Box", "A hexagonal Penfold pillar box of the 1860s: a flared cornice, a domed "
                   "cap with a bud on top, the door and slot cut into the front, a wreath on the door and snow on the cap."),
    "signpost": ("Victorian Signpost", "A cast-iron fingerpost on a fluted foot: three white arms pointing three ways, "
                 "each on an iron bracket pierced with diamonds, and snow on the acorn finial."),
    "carolers": ("Victorian Carolers", "Four carolers in top hats and bonnets with their songbooks, one holding a "
                 "lantern on a staff, on a patch of snow."),
    "bandstand": ("Victorian Bandstand", "An octagonal bandstand: a brick plinth with steps, white columns, iron "
                  "railings, an arched frieze hung with wreaths and a slate roof under snow."),
    "horse_sleigh": ("Victorian Horse Sleigh", "A draught horse pulling a red sleigh piled with presents through the snow."),
}

if __name__ == "__main__":
    piece = sys.argv[1]
    d = HERE / piece
    name = f"victorian_{piece}"
    parts = [p for p in ("body", "roof", "trim", "accent") if (d / f"{name}_{p}.stl").exists()]
    label, note = PIECES[piece]
    run_checks(d, name, dict(label=label, note=note, objects=[[(p, COLOURS[p]) for p in parts]],
                             unions=[f"{name}_union.stl"],
                             source=f"christmas_village/accessories/{piece}/{name}.3mf"), sys.argv[2:] or None)
