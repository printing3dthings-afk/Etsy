#!/usr/bin/env python3
"""OnBrandCraftz tip posts (2026-11-11): Scott's examples were AD3D's numbered tip
carousels: black, one accent colour, heavy condensed type, a numbered grid with a
picture per tip, a source line, and a "save this" call to action. This is our
version, in the logo's black and gold, with our own measured facts.

One spec (a .json beside this file) makes:
  <name>_post.png   1080 x 1350 (4:5), the Instagram/Facebook carousel slide
  <name>_reel.mp4   1080 x 1920 (9:16), the same tips building in one by one

The pictures are drawn diagrams, not product photos, so nothing on them can be
mistaken for something a buyer receives.

    python3 make_tip_post.py nozzle_detail.json
"""
import functools
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
F = ROOT / "assets" / "fonts"
F2 = ROOT / "fonts"
BG, PANEL, LINE = (12, 13, 16), (22, 24, 29), (52, 55, 62)
GOLD, GOLD2, WHITE, SOFT = (222, 172, 58), (255, 205, 92), (246, 244, 238), (170, 174, 184)
LOGO = ROOT / "openscad_models" / "brand" / "icons" / "obc_logo_master_1600.png"


def font(name, size):
    p = F / name if (F / name).exists() else F2 / name
    return ImageFont.truetype(str(p), size)


HEAD = lambda s: font("BebasNeue-Regular.ttf", s)   # noqa: E731
TITLE = lambda s: font("Oswald-Bold.ttf", s)        # noqa: E731
BODY = lambda s: font("Poppins-Regular.ttf", s)     # noqa: E731
BOLD = lambda s: font("Poppins-SemiBold.ttf", s)    # noqa: E731


@functools.lru_cache(maxsize=None)
def logo(height):
    """Scott's OBC logo as it is: the gold letters cropped from the master image."""
    im = Image.open(LOGO).convert("RGB").crop((90, 520, 1490, 1080))
    # lift the gold letters (and their dark stripes) off the logo's own textured
    # ground, by warmth: the ground is neutral, the letters warm. Nothing redrawn.
    r, g, b = [c.point(lambda v: v) for c in im.split()]
    warm = Image.eval(Image.merge("RGB", (r, g, b)).convert("L"), lambda v: 0)
    px, wp = im.load(), warm.load()
    for yy in range(im.height):
        for xx in range(im.width):
            rr, gg, bb = px[xx, yy]
            wp[xx, yy] = 255 if (rr - bb > 9 and rr > 30) else 0
    from PIL import ImageFilter as _F
    warm = warm.filter(_F.MaxFilter(3)).filter(_F.GaussianBlur(1))
    im = im.convert("RGBA")
    im.putalpha(warm)
    return im.resize((int(im.width * height / im.height), height), Image.LANCZOS)


def wrap(d, text, f, width):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=f) <= width:
            line = t
        else:
            out.append(line)
            line = w
    return out + [line]


# ---------- the diagrams: gold lines on the dark, one per kind of tip ----------

def diagram(kind, w, h):
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W, H = w * 2, h * 2
    lw = 5

    def layers(x0, x1, y0, n, step, fill=(60, 63, 70, 255)):
        for i in range(n):
            y = y0 - i * step
            d.rectangle([x0, y - step + 3, x1, y], fill=fill)

    if kind == "groove_up":       # a wall face with layer lines and one crisp upright groove
        x0, x1, y1 = W * 0.18, W * 0.82, H * 0.88
        for i in range(10):
            y = y1 - i * H * 0.075
            d.rectangle([x0, y - H * 0.07, x1, y], fill=(60, 63, 70, 255))
        gx = W * 0.5
        d.rectangle([gx - 14, H * 0.13, gx + 14, y1], fill=(20, 21, 25, 255))
        d.line([gx - 14, H * 0.13, gx - 14, y1], fill=GOLD2, width=lw)
        d.line([gx + 14, H * 0.13, gx + 14, y1], fill=GOLD2, width=lw)
        for y in (H * 0.07, H * 0.94):
            d.polygon([(gx - 30, y), (gx + 30, y), (gx, y + (24 if y < H / 2 else -24))], fill=GOLD)
    elif kind == "snap":          # drawn 0.3 (a layer and a half) vs printed 0.4 (two whole layers)
        base, step = H * 0.72, H * 0.2
        for k, (x0, x1, hgt, col, lab, dash) in enumerate((
                (W * 0.08, W * 0.46, 1.5, WHITE, "drawn 0.3", True),
                (W * 0.54, W * 0.92, 2.0, GOLD2, "printed 0.4", False))):
            for li in range(3):
                d.line([x0, base - li * step, x1, base - li * step], fill=(70, 73, 80), width=3)
            top = base - hgt * step
            if dash:
                for x in range(int(x0), int(x1), 26):
                    d.line([x, top, min(x + 14, x1), top], fill=col, width=5)
                d.line([x0, top, x0, base], fill=col, width=3)
                d.line([x1, top, x1, base], fill=col, width=3)
            else:
                d.rectangle([x0, top, x1, base], outline=col, width=lw)
            d.text(((x0 + x1) / 2, base + 22), lab, font=BOLD(36), fill=col, anchor="mt")
    elif kind == "grow":          # a hairline groove becomes a whole layer
        fs = int(min(40, H * 0.16))   # labels scale with the tile, so a short reel tile keeps them inside
        x0, x1, base = W * 0.12, W * 0.88, H * 0.92
        step = (base - fs * 1.3) / 4
        layers(x0, x1, base, 3, step)
        y = base - 2 * step
        d.rectangle([W * 0.2, y - step * 0.5, W * 0.45, y], outline=WHITE, width=3)
        d.rectangle([W * 0.55, y - step, W * 0.8, y], outline=GOLD2, width=lw)
        d.text((W * 0.325, y - step * 0.5 - fs * 0.25), "0.1", font=BOLD(fs), fill=WHITE, anchor="mb")
        d.text((W * 0.675, y - step - fs * 0.25), "0.2", font=BOLD(fs), fill=GOLD2, anchor="mb")
    elif kind == "stairs":        # a dome drawn smooth, printed as five stacked rings
        cx, base, r = W * 0.5, H * 0.86, H * 0.62
        d.arc([cx - r, base - r, cx + r, base + r], 180, 360, fill=WHITE, width=4)
        n = 5
        for i in range(n):
            y0 = base - (i + 1) * r / n
            hw = math.sqrt(max(r * r - ((i + 0.5) * r / n) ** 2, 0))  # each ring as wide as the dome at its middle
            d.rectangle([cx - hw, y0, cx + hw, y0 + r / n - 4], outline=GOLD2, width=lw)
    elif kind == "letters":       # a 3 mm letter beside a too-small blob
        fs = int(min(36, H * 0.15))
        rule = H - fs * 1.4
        d.text((W * 0.33, rule / 2), "A", font=HEAD(int(rule * 0.8)), fill=GOLD2, anchor="mm")
        d.text((W * 0.72, rule * 0.62), "a", font=HEAD(int(rule * 0.3)), fill=(110, 112, 118), anchor="mm")
        d.line([W * 0.6, rule * 0.2, W * 0.86, rule * 0.92], fill=(200, 70, 60), width=8)
        d.line([W * 0.08, rule, W * 0.58, rule], fill=WHITE, width=4)
        d.text((W * 0.33, rule + fs * 0.25), "3 mm", font=BOLD(fs), fill=WHITE, anchor="mt")
    elif kind == "dots":          # a row of dots: big ones stay, tiny ones vanish
        sizes = [0.30, 0.22, 0.15, 0.08]
        x = W * 0.12
        for i, s in enumerate(sizes):
            r = H * s / 2
            cx, cy = x + r, H * 0.5
            if i < 2:
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD2)
            else:
                d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(110, 112, 118), width=4)
            x += 2 * r + W * 0.07
        d.text((W * 0.3, H * 0.92), "kept", font=BODY(34), fill=GOLD2, anchor="mm")
        d.text((W * 0.74, H * 0.92), "dropped", font=BODY(34), fill=SOFT, anchor="mm")
    return im.resize((w, h), Image.LANCZOS)


# ---------- the card ----------

def card(spec, size, show=None, t_in=None):
    """The post. `show` = how many tips are visible (all when None); `t_in` = 0..1,
    how far the newest tip has slid in (for the reel)."""
    W, H = size
    tall = H / W > 1.5
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # a faint gold glow behind the headline, the one bit of atmosphere
    glow = Image.new("RGB", (W, H), BG)
    ImageDraw.Draw(glow).ellipse([W * 0.1, -H * 0.12, W * 0.9, H * 0.28], fill=(52, 40, 14))
    im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(120)), 0.9)
    d = ImageDraw.Draw(im)
    # the reel keeps everything between y 225 and 1440: TikTok/Reels put their top
    # bar above that and the caption and buttons in the bottom quarter below it
    top = 225 if tall else 40
    lg = logo(66)
    im.paste(lg, ((W - lg.width) // 2, top), lg)
    y = top + 80
    for line, col in spec["headline"]:
        f = HEAD(118 if not tall else 122)
        d.text((W / 2, y), line, font=f, fill=GOLD2 if col == "gold" else WHITE, anchor="mt")
        y += f.size * 0.86
    d.text((W / 2, y + 8), spec["sub"], font=BODY(34), fill=WHITE, anchor="mt")
    y += 76
    tips = spec["tips"]
    n = len(tips) if show is None else show
    # three columns of two: number and title, the picture, then the line of text.
    # (Two columns left no room for the pictures, and they were dropped.)
    cols = 3
    rows = math.ceil(len(tips) / cols)
    gx, gap = 36, 16
    cw = (W - 2 * gx - gap * (cols - 1)) / cols
    bottom = H - (630 if tall else 170)
    ch = (bottom - y - gap * (rows - 1)) / rows
    for i, t in enumerate(tips[:n]):
        c, r = i % cols, i // cols
        x0, y0 = gx + c * (cw + gap), y + r * (ch + gap)
        dy, alpha = 0, 255
        if t_in is not None and i == n - 1:
            ease = 1 - (1 - t_in) ** 3
            dy, alpha = (1 - ease) * 60, int(255 * ease)
        tile = Image.new("RGBA", (int(cw), int(ch)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        td.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=20, fill=PANEL + (255,), outline=LINE + (255,), width=2)
        td.text((18, 10), f"{i + 1:02d}", font=HEAD(78), fill=GOLD2)
        tf = TITLE(27 if not tall else 30)
        lines = wrap(td, t["title"].upper(), tf, cw - 110)
        ty = 18 if len(lines) > 1 else 34
        for ln in lines:
            td.text((92, ty), ln, font=tf, fill=WHITE)
            ty += tf.size + 6
        bf = BODY(20 if not tall else 21)
        body = wrap(td, t["text"], bf, cw - 36)
        lh = bf.size + 7
        by = ch - 16 - lh * len(body)
        for k2, ln in enumerate(body):
            td.text((18, by + k2 * lh), ln, font=bf, fill=SOFT)
        top_pic = 100
        dh = int(by - top_pic - 10)
        if dh > 60:
            dg = diagram(t["picture"], int(cw - 40), dh)
            tile.alpha_composite(dg, (20, top_pic))
        if alpha < 255:
            tile.putalpha(tile.getchannel("A").point(lambda v: v * alpha // 255))
        im.paste(tile, (int(x0), int(y0 + dy)), tile)
    # call to action and source
    cy = bottom + (20 if tall else 22)
    d.rounded_rectangle([gx, cy, W - gx, cy + 84], radius=18, fill=GOLD)
    d.text((W / 2, cy + 44), spec["cta"], font=HEAD(58), fill=BG, anchor="mm")
    sf = BODY(21)
    for k2, ln in enumerate(wrap(d, spec["source"], sf, W - 2 * gx)):
        d.text((W / 2, cy + (96 if tall else 102) + k2 * 28), ln, font=sf, fill=SOFT, anchor="mt")
    return im


def main():
    spec_path = Path(sys.argv[1]).resolve()
    spec = json.loads(spec_path.read_text())
    name = spec_path.stem
    card(spec, (1080, 1350)).save(HERE / f"{name}_post.png")
    # the reel: headline alone, then each tip slides in and stays long enough to
    # read (2.2 s each; 0.9 s was too quick), then a hold on the whole card.
    # Frames that don't move are rendered once and copied.
    fps, per, slide, hold0, hold1 = 30, 2.2, 0.45, 1.2, 3.5
    n = len(spec["tips"])
    with tempfile.TemporaryDirectory() as td:
        frames = []
        frames += [card(spec, (1080, 1920), show=0)] * int(hold0 * fps)
        for i in range(1, n + 1):
            moving = int(slide * fps)
            frames += [card(spec, (1080, 1920), show=i, t_in=j / moving) for j in range(moving)]
            still = card(spec, (1080, 1920), show=i, t_in=1.0)
            frames += [still] * (int(per * fps) - moving)
        frames += [card(spec, (1080, 1920))] * int(hold1 * fps)
        for k, im in enumerate(frames):
            im.save(f"{td}/f{k:04d}.png", compress_level=1)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", f"{td}/f%04d.png",
                        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "18",
                        "-movflags", "+faststart", "-an", str(HERE / f"{name}_reel.mp4")], check=True)
    print("wrote", HERE / f"{name}_post.png", "and", HERE / f"{name}_reel.mp4")


if __name__ == "__main__":
    main()
