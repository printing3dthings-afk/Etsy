#!/usr/bin/env python3
"""Kit-card chalet snap test: the PDF guide (2026-11-25). Renders of the real exported coupon
parts (../coupon/), posed as check_fit.py poses them, then the cards (tools/guide_cards.py).

    python3 make_guide.py            (renders, then Chalet_Snap_Test_Guide.pdf)
    python3 make_guide.py --cards
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
CH = HERE.parent
ROOT = CH.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
TMP = CH / "logs"
R = ROOT / "tools" / "blender_render.py"
BASE_C, STUB_C = "0.93,0.91,0.86", "0.71,0.40,0.11"
GRIP, P, PITCH, BW = 3.0, 2.4, 22.0, 18.0
n = 0


def save(m):
    global n
    n += 1
    p = TMP / f"_g_{n}.stl"
    m.export(p)
    return p


def render(parts, out, az, el):
    args = []
    for p, c in parts:
        args += ["--part", f"{p}:{c}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az),
                    "--elevation", str(el), "--resolution", "1000", "--timeout", "900"], check=True)


def load(k):
    return trimesh.load(CH / "coupon" / f"coupon_{k}.stl", force="mesh")


def stood(i, lift):
    st = load(f"stub_{i}")
    st.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    st.apply_translation([PITCH / 2 + i * PITCH, BW / 2 + P / 2, GRIP + lift])
    return st


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(exist_ok=True)
    base = load("base")
    laid = trimesh.util.concatenate([load(f"stub_{i}").apply_translation([i * 22, -26, 0]) for i in range(3)])
    render([(save(base), BASE_C), (save(laid), STUB_C)], "parts.png", -20, 55)
    up = load("base")
    up.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0], [0, BW / 2, GRIP / 2]))
    render([(save(up), BASE_C), (save(stood(1, 14)), STUB_C)], "push.png", -25, 20)
    render([(save(up), BASE_C), (save(trimesh.util.concatenate([stood(i, 0) for i in range(3)])), STUB_C)],
           "seated.png", -25, 20)
    # the underside: the seated assembly turned over (a camera below the floor plane sees only the floor)
    flip = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0], [0, BW / 2, 0])
    ub = up.copy().apply_transform(flip)
    us = trimesh.util.concatenate([stood(i, 0) for i in range(3)]).apply_transform(flip)
    lift = -min(ub.bounds[0][2], us.bounds[0][2])
    render([(save(ub.apply_translation([0, 0, lift])), BASE_C), (save(us.apply_translation([0, 0, lift])), STUB_C)],
           "underside.png", -25, 50)


def cards():
    a = Card("Chalet: snap test", "The joint every panel of the kit-card chalet will use.")
    a.step(1, "What's on the plate", [
        "!A base strip with three slots, all the same.",
        "!Three panel stubs. Notches on the top edge: one = 0.35, two = 0.45, three = 0.55.",
    ], crop(IMG / "parts.png"))
    a.step(2, "Turn the base over and push a stub in", [
        "Smooth face up, skirt on the table.",
        "Push straight down with a thumb till it clicks. No tools.",
    ], crop(IMG / "push.png"), pic_h=420)
    a.step(3, "Seated", ["The stub's shoulders sit flat on the base.",
                         "Underneath, the two prongs have sprung out under the floor."],
           crop(IMG / "seated.png"), pic_h=420)
    b = Card("Chalet: test it", "Try all three stubs the same way.")
    b.step(1, "Check each one", [
        "!Goes in by thumb, with a click?",
        "!Hold the base upside down and shake it: does the stub stay?",
        "!Pull it out: a firm tug, not a struggle?",
        "!In and out 10 times: any white or cracked prong root?",
        "!Any rattle once it's in?",
    ], crop(IMG / "underside.png"), pic_h=380)
    b.box("Good", ["Clicks in by thumb.", "Stays put upside down.", "Pulls out with a firm tug.",
                   "No whitening after 10."], GOOD)
    b.box("Tell me", ["which stub you'd pick (one, two or three notches);", "any that cracked or whitened;",
                      "any that rattles or falls out."], BAD)
    save_pdf([a, b], HERE / "Chalet_Snap_Test_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_g_*.stl"):
        f.unlink()
