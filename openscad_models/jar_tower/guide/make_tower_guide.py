#!/usr/bin/env python3
"""Stacking Jar Tower: the PDF guide (2026-11-13). Renders of the real exported parts
(parts/tower_*.stl), posed as check_tower.py poses them: each part screwed home on the one
below, its thread's phase following. Then the cards (tools/guide_cards.py).

    python3 make_tower_guide.py            (renders, then Stacking_Jar_Tower_Guide.pdf)
    python3 make_tower_guide.py --cards    (cards only, from the renders already made)
"""
import math
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
JT = HERE.parent
ROOT = JT.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(JT))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
TMP = JT / "logs" / "guide_tower"
R = ROOT / "tools" / "blender_render.py"
# render colours only: every part prints in whatever one filament Scott loads
# (darker than the filaments look: on the light studio floor paler ones wash out)
JARS = ["0.86,0.42,0.58", "0.55,0.42,0.80", "0.36,0.68,0.54", "0.90,0.68,0.26"]
END = "0.50,0.45,0.42"
n = 0


def save(m):
    global n
    n += 1
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / f"_t_{n}.stl"
    m.export(p)
    return p


def render(parts, out, az, el, res=1000):
    args = []
    for p, c in parts:
        args += ["--part", f"{p}:{c}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az), "--elevation", str(el),
                    "--resolution", str(res), "--timeout", "1200"], check=True)


def load(k):
    return trimesh.load(JT / "parts" / f"tower_{k}.stl", force="mesh")


def home(rim):
    """(z, turn) of a spigot screwed home in a mouth whose rim is at z=rim (check_tower.py's zs)."""
    import check_tower as c
    V, T, P, TA, CL = c.V, c.T, c.P, c.TA, c.CL
    cs = (V["R_OUT"] - V["CS"] - (V["TH_R"] + CL)) / TA
    mz = rim - V["H_MOUTH"]
    z0 = mz + V["H_MOUTH"] - cs - V["TH_H"] - P
    zs = mz + V["H_MOUTH"] - cs - CL / TA - V["TH_H"]
    return zs, 360 * (zs - z0) / P


def place(m, z, deg):
    t = trimesh.transformations.rotation_matrix(math.radians(deg), [0, 0, 1])
    t[2, 3] = z
    return m.copy().apply_transform(t)


def stack(k_jars, cap=True):
    """The foot, k_jars jars and (optionally) the cap, each screwed home: [(mesh, colour)]."""
    import check_tower as c
    out = [(load("foot"), END)]
    rim, deg = c.T["FOOT_FLOOR"] + c.V["H_MOUTH"], 0.0
    jar = load("jar")
    for k in range(k_jars):
        z, t = home(rim)
        deg += t                # a turn relative to the part below, which is itself turned
        out.append((place(jar, z, deg), JARS[k % 4]))
        rim = z + c.T["H_JAR"]
    if cap:
        z, t = home(rim)
        out.append((place(load("cap_up"), z, deg + t), END))
    return out, rim


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    # what's on the plates: a jar, the cap (as printed, upside down) and the foot
    jar, capp, foot = load("jar"), load("cap"), load("foot")
    capp.apply_translation([90, 0, 0])
    foot.apply_translation([-95, 0, 0])
    render([(save(foot), END), (save(jar), JARS[0]), (save(capp), END)], "tower_parts.png", -20, 30)
    full, _ = stack(4)
    render([(save(m), col) for m, col in full], "tower_full.png", -25, 12, res=1200)
    two, rim = stack(1, cap=False)
    # the next jar lifted above it, ready to screw on
    up = load("jar")
    up.apply_translation([0, 0, rim + 18])
    render([(save(m), col) for m, col in two] + [(save(up), JARS[1])], "tower_screw.png", -25, 14)
    # cut in half: a jar on a jar, the teeth engaged and the cone shut
    cut = lambda m: trimesh.intersections.slice_mesh_plane(m, [0, 1, 0], [0, 0, 0], cap=True)
    pair, _ = stack(2, cap=True)
    render([(save(cut(m)), col) for m, col in pair], "tower_section.png", 0, 6, res=1200)


def cards():
    a = Card("Stacking Jar Tower", "Four jars that screw into one another, a foot below and a cap on top. "
                                   "The thread is the test print's 0.2 mm one, the snug one you picked.")
    a.step(1, "What you print", [
        "!4 jars (the same file 4 times), 1 cap, 1 foot. Pick any colours.",
        "!Jar: prints standing on its teeth, as the test spigot did.",
        "!Cap: prints upside down, its flat top on the plate.",
        "Foot: prints as it stands, its wide skirt on the plate.",
    ], crop(IMG / "tower_parts.png"))
    a.step(2, "Build it from the bottom", [
        "!Foot on the table. Screw a jar into it, teeth down, turning clockwise.",
        "Each jar stops when its cone lands in the mouth below: snug it there, don't force past it.",
        "Then the next jar into that one's top, and so on. The cap goes on last.",
    ], crop(IMG / "tower_screw.png"), pic_h=460)
    b = Card("Stacking Jar Tower: built", "About 25 cm tall with all four jars. Each jar holds about 150 ml.")
    b.step(3, "The tower", [
        "Any jar opens by unscrewing everything above it.",
        "Use fewer jars for a shorter tower: the cap fits any jar, and any jar fits the foot.",
    ], crop(IMG / "tower_full.png"), pic_h=620)
    b.step(4, "Inside a joint", [
        "Cut in half: the teeth engaged and the cone closing the seam.",
    ], crop(IMG / "tower_section.png"), pic_h=420)
    c = Card("Stacking Jar Tower: test it", "Check each joint as you build it.")
    c.step(5, "For every joint", [
        "!Screws in by hand, smooth, all the way to the stop?",
        "Screwed home, wiggle it: any play?",
        "Pick the tower up by the cap: does everything come with it?",
        "Unscrew a middle jar and screw it back: same feel as the first time?",
    ])
    c.box("Good", ["Every joint feels like test mouth 1.", "No wobble; the seams close all round.",
                   "Lifting by the cap lifts the whole tower."], GOOD)
    c.box("Tell me", ["any joint that binds, or goes on crooked;", "any that wobbles when home;",
                      "if a jar's floor or a seam lets light through;", "how it looks from across the room."], BAD)
    save_pdf([a, b, c], HERE / "Stacking_Jar_Tower_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_t_*.stl"):
        f.unlink()
