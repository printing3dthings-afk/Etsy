#!/usr/bin/env python3
"""Fold Stand v4: the PDF guide (2026-11-10) for both prints, the hinge test (print it
first) and the full stand. Every picture is a render of the real exported parts, posed
as check_stand_v4.py / check_hinge_test.py pose them, then the cards (tools/guide_cards.py).
Some pictures come from render_stand_v4.py; run that first.

    python3 make_guide.py            (renders, then Fold_Stand_v4_Guide.pdf)
    python3 make_guide.py --cards    (cards only, from the renders already made)
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
V4 = HERE.parent
ROOT = V4.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(V4))
import check_stand_v4 as c  # noqa: E402
from guide_cards import BAD, BODYB, GOOD, INK, W, Card, crop, fit, save_pdf  # noqa: E402

IMG = HERE / "images"
STUDIO = V4 / "images"
TMP = V4 / "logs" / "guide"
R = ROOT / "tools" / "blender_render.py"
LILAC, WHITE, PINK = "0.72,0.61,0.88", "0.96,0.95,0.92", "0.96,0.62,0.74"
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
    for p, col in parts:
        args += ["--part", f"{p}:{col}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az), "--elevation", str(el),
                    "--resolution", str(res), "--timeout", "900"], check=True)


def coupon_plate():
    prop, plate = sorted(c.load("coupon_plate").split(only_watertight=False), key=lambda m: m.volume)
    return plate, prop


def coupon_hinge(r):
    return c.rx(r, (0, 14.0, c.HIN))


def stand(th, prop_r=None, lift=0.0, base=True):
    T = c.tr(0, 0, lift) @ c.plate_T(th)
    out = [(V4 / "parts" / "base.stl", WHITE)] if base else []
    out.append((save(c.load("plate_only").apply_transform(T)), LILAC))
    P = T if prop_r is None else T @ c.prop_in_plate(prop_r)
    out.append((save(c.load("prop_only").apply_transform(P)), PINK))
    return out


def renders():
    IMG.mkdir(parents=True, exist_ok=True)
    cb = c.load("coupon_base")
    plate, prop = coupon_plate()
    # the hinge test: the prop swung out behind the plate, the plate held upright
    up = c.plate_T(80)
    render([(save(plate.copy().apply_transform(up)), LILAC),
            (save(prop.copy().apply_transform(up @ coupon_hinge(-110))), PINK)], "t_swing.png", 60, 15)
    on = c.tr(0, 0, 12) @ c.plate_T(c.PASS)
    render([(save(cb), WHITE), (save(plate.copy().apply_transform(on)), LILAC),
            (save(prop.copy().apply_transform(on)), PINK)], "t_on.png", 60, 20)
    back = c.plate_T(60)
    render([(save(cb), WHITE), (save(plate.copy().apply_transform(back)), LILAC),
            (save(prop.copy().apply_transform(back)), PINK)], "t_back.png", 60, 20)
    # the full stand
    render(stand(90), "s_upright.png", 60, 20)


def pair(a, b, la, lb, h=420):
    cw = (W - 120) // 2
    pics = [fit(crop(p, 10), cw - 20, h) for p in (a, b)]
    ph = max(p.height for p in pics)
    strip = Image.new("RGB", (W - 120, ph + 60), "white")
    d = ImageDraw.Draw(strip)
    f = BODYB
    for i, (p, lab) in enumerate(zip(pics, (la, lb))):
        x = i * cw
        strip.paste(p, (x + (cw - p.width) // 2, ph - p.height))
        d.text((x + (cw - d.textlength(lab, font=f)) / 2, ph + 12), lab, font=f, fill=INK)
    return strip


def cards():
    t1 = Card("Fold Stand v4: hinge test", "Print this first: both new joints at full size, on a short plate. About 30 minutes.")
    t1.step(1, "What's in the print", [
        "!The small base (white here), with its two lugs.",
        "!The small plate (purple), with its prop (pink) printed inside it, already on its hinge.",
        "Nothing to glue, and nothing extra to buy.",
    ], crop(STUDIO / "fold_stand_v4_hinge_test.png"), pic_h=420)
    t1.step(2, "Free the prop", [
        "Push the prop out from the plate's back. It turns on two small cones, one each side.",
        "If it's stiff the first time, work it back and forth a few times.",
    ], crop(IMG / "t_swing.png"), pic_h=480)
    t1.step(3, "Put the plate on the lugs", [
        "!Fold the prop back into the plate first.",
        "Tip the plate forward, well past upright, top end leaning out over the front: about 145 degrees.",
        "Lower its two side pins straight down into the lugs' slots. It only fits at this angle.",
    ], crop(IMG / "t_on.png"), pic_h=480)
    t1.step(4, "Tilt it back", [
        "Now it turns, but can't lift out: at every angle from flat to upright the pins are locked in.",
    ], crop(IMG / "t_back.png"), pic_h=420)
    t2 = Card("Fold Stand v4: test the hinges", "Both joints have to move freely and never come apart.")
    t2.step(1, "Try each joint", [
        "!The prop: swing it in and out. Does it stay on? Try to wiggle it off sideways.",
        "!The plate: tilt it from flat to upright. Lift it at each angle: it must not come off.",
        "Tip it to about 145 again: it should lift straight off.",
    ])
    t2.box("Good", ["The prop swings freely and won't come off.", "The plate turns smoothly in the lugs.",
                    "It only comes off at the tipped-forward angle."], GOOD)
    t2.box("Tell me", ["if the prop was stuck, fused, or snapped freeing it;",
                       "if either joint feels loose or rattles;",
                       "if the plate came off at any angle except tipped forward."], BAD)

    s1 = Card("Fold Stand v4: put it together", "Three pieces that stay together. Print it once the hinge test works.")
    s1.step(1, "What's in the box", [
        "!The base (white here).",
        "!The plate (purple), with the prop (pink) printed inside it, folded flush.",
    ], crop(STUDIO / "fold_stand_v4_prints.png"), pic_h=420)
    s1.step(2, "Put the plate on", [
        "Prop folded in. Tip the plate forward, top end out over the front (about 145 degrees).",
        "Lower its two side pins straight down into the lugs' slots.",
    ], crop(STUDIO / "fold_stand_v4_going_on.png"), pic_h=480)
    s1.step(3, "Tilt it back", [
        "Bring it back to upright. From here on it's locked in: it turns, but won't lift out.",
    ], crop(IMG / "s_upright.png"), pic_h=480)
    s1.step(4, "Swing the prop out and set it in a notch", [
        "Push the prop out from the plate's back. Set its rounded foot in one of the six notches on the base.",
        "The notch nearest the plate is the steepest angle.",
    ], crop(STUDIO / "fold_stand_v4_back.png"), pic_h=480)
    s2 = Card("Fold Stand v4: use it and fold it", "Six angles from 80 to 55 degrees.")
    s2.step(1, "Stand your phone on the shelf", [
        "Its bottom edge on the shelf, its back against the plate.",
    ], crop(STUDIO / "fold_stand_v4_three_quarter.png"), pic_h=520)
    s2.step(2, "Change the angle", [
        "Lift the phone, move the prop's foot to another notch.",
    ], pair(STUDIO / "fold_stand_v4_side_80.png", STUDIO / "fold_stand_v4_side_55.png",
            "nearest notch: 80 deg", "farthest notch: 55 deg"), pic_h=480)
    s2.step(3, "Fold it", [
        "Lift the prop's foot out of its notch and fold the prop flush into the plate.",
        "Lay the plate down flat onto the base. Folded it's 34 mm tall, and still one piece.",
    ], crop(STUDIO / "fold_stand_v4_folded.png"), pic_h=460)
    s2.box("Good", ["Each angle holds when you tap the screen.", "Folds flat and nothing comes loose when you carry it."], GOOD)
    s2.box("Tell me", ["if any angle slips or the stand tips;", "if the prop won't fold flush;",
                       "if the plate rubs the base anywhere."], BAD)
    save_pdf([t1, t2, s1, s2], HERE / "Fold_Stand_v4_Guide.pdf")


if __name__ == "__main__":
    if "--cards" not in sys.argv:
        renders()
    cards()
    for f in TMP.glob("_g_*.stl"):
        f.unlink()
