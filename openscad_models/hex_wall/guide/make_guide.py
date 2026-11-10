#!/usr/bin/env python3
"""Hex Wall Tiles hang test: the PDF guide (2026-11-10). Renders of the real exported parts
(the tile strip and the two hook modules), posed as check_hang_coupon.py poses them,
turned upright as on a wall, then the cards (tools/guide_cards.py).

    python3 make_guide.py            (renders, then Hex_Wall_Hang_Test_Guide.pdf)
    python3 make_guide.py --cards
"""
import math
import re
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
HW = HERE.parent
ROOT = HW.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
TMP = HW / "logs" / "guide"
R = ROOT / "tools" / "blender_render.py"
V = {k: float(v) for k, v in re.findall(r"\b(\w+) = ([0-9.]+);", (HW / "hang_coupon.scad").read_text())}
TILE, MOD = "0.93,0.92,0.88", "0.72,0.61,0.88"
n = 0


def save(m):
    global n
    n += 1
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / f"_g_{n}.stl"
    m.export(p)
    return p


def render(parts, out, az, el, res=1000):
    args = []
    for p, c in parts:
        args += ["--part", f"{p}:{c}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az), "--elevation", str(el),
                    "--resolution", str(res), "--timeout", "900"], check=True)


def load(k):
    return trimesh.load(HW / "parts" / f"{k}.stl", force="mesh")


# print frame (tile on its back: y up the wall, z out of it) -> standing on a wall: z out
# toward the viewer (-y in the render), y up (+z)
UPRIGHT = trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])


def hung(dy=0.0):
    y = V["RAIL_Y0"] + V["RAIL_L"] - V["SLOT_LEN"] + dy
    return trimesh.transformations.translation_matrix([0, y, V["T"]])


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    tile, m1, m2 = load("tile"), load("module_0.2"), load("module_0.3")
    m1.apply_translation([45, 0, 0])
    m2.apply_translation([45, 65, 0])
    render([(save(tile), TILE), (save(m1), MOD), (save(m2), MOD)], "parts.png", -20, 50)
    tile_up = load("tile").apply_transform(UPRIGHT)
    above = load("module_0.2").apply_transform(UPRIGHT @ hung(40))
    render([(save(tile_up), TILE), (save(above), MOD)], "ready.png", 210, 15)
    on = load("module_0.2").apply_transform(UPRIGHT @ hung())
    render([(save(tile_up), TILE), (save(on), MOD)], "hung.png", 210, 15)
    render([(save(tile_up), TILE), (save(on), MOD)], "hung_side.png", 270, 5)


def cards():
    a = Card("Hex Wall: hang test", "A strip of tile with the real rail, and two hook modules.")
    a.step(1, "What's in the print", [
        "!The tile strip (white here): a dovetail rail, and a screw hole below it.",
        "!Two hook modules (purple). The notches on the side say how loose the slot is:",
        "1 notch = 0.2 mm (snug), 2 notches = 0.3 (easier).",
        "The window through each module is the slot: you'll see the rail through it.",
    ], crop(IMG / "parts.png"))
    a.step(2, "Put the tile up", [
        "Screw it to the wall through its hole, rail upright, the hole at the bottom. Or hold it against a wall for the first tries.",
    ])
    a.step(3, "Slide a module down onto the rail", [
        "Hook facing out, the slot's open end at the bottom. Line it up over the rail and let it slide down.",
    ], crop(IMG / "ready.png"), pic_h=520)
    a.step(4, "It hangs on the rail's top end", [
        "Its back sits flat on the tile. Its weight holds it down; the dovetail holds it to the wall.",
    ], crop(IMG / "hung.png"), pic_h=520)
    b = Card("Hex Wall: test it", "Try both modules.")
    b.step(1, "For each module", [
        "!Slide it on: smooth, or does it catch?",
        "Pull it straight out from the wall: it must not come off.",
        "Lift it up: it comes off.",
        "Hang a bag or keys on the hook.",
    ], crop(IMG / "hung_side.png"), pic_h=420)
    b.box("Good", ["Slides on easily, sits flat.", "Pulling straight out does nothing.", "Holds a bag without moving."], GOOD)
    b.box("Tell me", ["which slid on better (1 or 2 notches), and which rattled less;",
                      "if either catches or jams;", "if either came off when pulled out."], BAD)
    save_pdf([a, b], HERE / "Hex_Wall_Hang_Test_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_g_*.stl"):
        f.unlink()
