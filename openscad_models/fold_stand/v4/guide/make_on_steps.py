#!/usr/bin/env python3
"""Fold Stand v4 hinge test: putting the plate on the lugs, as three side views along the
pins (2026-11-14, Scott asked to see it). Renders of the real exported coupon parts,
posed as check_stand_v4.py poses them, in darker colours than the guide's (those washed
out on the light floor). Writes images/on_steps.png.

    python3 make_on_steps.py
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
from guide_cards import BODYB, INK, crop  # noqa: E402

IMG = HERE / "images"
TMP = V4 / "logs" / "on_steps"
R = ROOT / "tools" / "blender_render.py"
BASE, PLATE, PROP = "0.55,0.50,0.46", "0.50,0.40,0.78", "0.86,0.42,0.58"


def frame(T, out, az, el):
    TMP.mkdir(parents=True, exist_ok=True)
    plate, prop = sorted(c.load("coupon_plate").split(only_watertight=False), key=lambda m: m.volume)[::-1]
    parts = [(c.load("coupon_base"), BASE), (plate.apply_transform(T), PLATE), (prop.apply_transform(T), PROP)]
    args = []
    for i, (m, col) in enumerate(parts):
        p = TMP / f"{out}_{i}.stl"
        m.export(p)
        args += ["--part", f"{p}:{col}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(TMP / f"{out}.png"), "--azimuth", str(az),
                    "--elevation", str(el), "--resolution", "900", "--timeout", "900"], check=True)
    return crop(TMP / f"{out}.png", 20)


def main():
    steps = [
        (c.tr(0, 0, 14) @ c.plate_T(c.PASS), "1. Prop folded in. Plate tipped forward to about 145°, pins above the slots"),
        (c.plate_T(c.PASS), "2. Lower it straight down: the pins drop into the slots"),
        (c.plate_T(60), "3. Tilt it back: it turns, and now it can't lift out"),
    ]
    side = [frame(T, f"side_{k}", 90, 4) for k, (T, _) in enumerate(steps)]
    angled = [frame(T, f"angled_{k}", 55, 22) for k, (T, _) in enumerate(steps)]
    cw, ch = 620, 560
    sheet = Image.new("RGB", (cw * 3, 60 + 2 * ch + 70), "white")
    d = ImageDraw.Draw(sheet)
    for k, (_, lab) in enumerate(steps):
        for row, pics in enumerate((side, angled)):
            im = pics[k].copy()
            im.thumbnail((cw - 30, ch - 20))
            sheet.paste(im, (k * cw + (cw - im.width) // 2, 50 + row * ch + (ch - im.height) // 2))
        words, lines, cur = lab.split(), [], ""
        for w in words:
            if d.textlength(cur + " " + w, font=BODYB) > cw - 40:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        for i, ln in enumerate(lines):
            d.text((k * cw + 20, 50 + 2 * ch + i * 30 - 10), ln, font=BODYB, fill=INK)
    d.text((20, 12), "Top: from the side, along the pins.  Bottom: from an angle.  Design-review renders of the real parts, not photos.",
           font=BODYB, fill=INK)
    IMG.mkdir(parents=True, exist_ok=True)
    sheet.save(IMG / "on_steps.png")
    for f in TMP.glob("*.stl"):
        f.unlink()


if __name__ == "__main__":
    main()
