"""Signature intros: one per series, each its own twist on the Printed style (2026-11-20).

Scott asked whether each series should have its own intro, then said yes to these six:
  explained  annotate  the title prints, then an underline and an arrow draw on, like a diagram
  versus     race      two nozzles race in from opposite sides; "VS" lands where they meet
  blueprint  outline   the title draws as a thin outline with dimension lines, then fills solid
  news       stamp     a fast print, then a "NEWS" stamp thumps down and flashes
  friday     together  a row of small nozzles prints one letter each, side by side
  product    the print the product itself prints layer by layer, then its name

Two lengths of each. On Reels, Shorts and TikTok an intro before the content costs viewers, so:
  sting  1.5 s  transparent (ProRes 4444), laid over the first shot, upper third
  full   3.0 s  opaque, for YouTube and longer posts

Looks (colours, fonts, titles) come from kit.py's SERIES, so a corrected hex there corrects these.

    python3 intros.py OUT [--series versus] [--only sting|full] [--frame versus:full:1.2]
"""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from directions import SS, W, H, FPS, clamp, prog, ease_out, ease_back, font, mix, chip, text_mask, nozzle
from kit import SERIES, background, banner, title_font, fit_px, encode

ROOT = Path(__file__).resolve().parents[3]
PRODUCT_IMG = ROOT / "openscad_models/christmas_village/gingerbread/cottage/images/gingerbread_cottage_colour_three_quarter.png"
INTRO_TEXT = dict(product=dict(title="GINGERBREAD COTTAGE", chip="DESIGNED BY US"))


# ------------------------------------------------------------------ printing a mask
def print_mask(im, mask, x0, y0, colour, p, lh, mode="snake", head_col=None, small=False, lines=True):
    """Print `mask` (L) at (x0, y0) px (SS scale) to fraction p. colour: an RGB tuple, or an
    RGB image the size of the mask (the product picture). mode: "snake" sweeps alternate ways
    each layer; "both" sweeps in from both edges at once. Returns the nozzle positions."""
    w, h = mask.size
    n = max(1, math.ceil(h / lh))
    done = clamp(p) * n
    k = int(done)
    f = done - k
    reveal = Image.new("L", (w, h), 0)
    rd = ImageDraw.Draw(reveal)
    for i in range(min(k, n)):
        rd.rectangle((0, h - (i + 1) * lh, w, h - i * lh), fill=255)
    heads = []
    if k < n and p > 0:
        yt, yb = h - (k + 1) * lh, h - k * lh
        if mode == "both":
            xa, xb = int(w / 2 * f), int(w - w / 2 * f)
            rd.rectangle((0, yt, xa, yb), fill=255)
            rd.rectangle((xb, yt, w, yb), fill=255)
            heads = [(x0 + xa, y0 + yt), (x0 + xb, y0 + yt)]
        else:
            xe = int(w * f) if k % 2 == 0 else int(w * (1 - f))
            rd.rectangle((0, yt, xe, yb) if k % 2 == 0 else (xe, yt, w, yb), fill=255)
            heads = [(x0 + xe, y0 + yt)]
    shown = ImageChops.multiply(mask, reveal)
    src = colour.copy() if isinstance(colour, Image.Image) else Image.new("RGB", (w, h), colour)
    if lines:
        ld = ImageDraw.Draw(src)
        base = colour if isinstance(colour, tuple) else (128, 128, 128)
        dark = mix(base, (0, 0, 0), 0.28) if sum(base) > 200 else mix(base, (255, 255, 255), 0.2)
        for i in range(1, n + 1):
            ld.line((0, h - i * lh, w, h - i * lh), fill=dark, width=max(1, SS))
    im.paste(src, (x0, y0), shown)
    if head_col:
        d = ImageDraw.Draw(im)
        for hx, hy in heads:
            if small:
                small_nozzle(d, hx / SS, hy / SS, head_col)
            else:
                nozzle(d, hx / SS, hy / SS, head_col)
    return heads


def small_nozzle(d, x, y, col):
    s = SS
    d.rounded_rectangle(((x - 20) * s, (y - 56) * s, (x + 20) * s, (y - 24) * s), 5 * s, fill=col)
    d.polygon([((x - 12) * s, (y - 25) * s), ((x + 12) * s, (y - 25) * s), ((x + 3) * s, (y - 2) * s),
               ((x - 3) * s, (y - 2) * s)], fill=col)


def text_at(s, fnt, cx, cy):
    m = text_mask(s, fnt)
    return m, int(cx * SS - m.width / 2), int(cy * SS - m.height / 2)


def head(sp):
    return mix(sp["bg"], sp["text"], 0.55)


# ------------------------------------------------------------------ the six intros
# Each draws at centre height cy and size k (1.0 full, smaller for the sting), with u the
# fraction of the intro played (0..1), so one function serves both lengths.
def explained(im, sp, u, cy, k):
    d = ImageDraw.Draw(im)
    px = fit_px(sp, sp["title"], 900 * k, 230 * k)
    m, x0, y0 = text_at(sp["title"], title_font(sp, px), 540, cy)
    print_mask(im, m, x0, y0, sp["title_col"], prog(u, 0.0, 0.45), int(12 * k * SS), head_col=head(sp))
    km, kx, ky = text_at(sp["kicker"], title_font(sp, 92 * k), 540, cy - 160 * k)
    print_mask(im, km, kx, ky, sp["kicker_col"], prog(u, 0.45, 0.6), int(9 * k * SS), head_col=head(sp))
    # the underline draws, then an arrow curves in to the title with the lesson chip at its tail
    ul = ease_out(prog(u, 0.55, 0.7))
    if ul > 0:
        xa, xb, yy = x0 / SS, x0 / SS + (m.width / SS) * ul, cy + 100 * k
        d.line((xa * SS, yy * SS, xb * SS, yy * SS), fill=sp["acc"], width=int(10 * k * SS))
    ar = ease_out(prog(u, 0.62, 0.82))
    if ar > 0:
        p0, p1, p2 = (860, cy + 330 * k), (900, cy + 180 * k), (760, cy + 115 * k)
        pts = []
        for i in range(int(30 * ar) + 1):
            s = i / 30
            pts.append(((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * p1[0] + s * s * p2[0],
                        (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * p1[1] + s * s * p2[1]))
        if len(pts) > 1:
            d.line([(x * SS, y * SS) for x, y in pts], fill=sp["kicker_col"], width=int(7 * k * SS), joint="curve")
        if ar >= 1:
            hx, hy = p2
            d.polygon([(hx * SS, hy * SS), ((hx + 34 * k) * SS, (hy - 4 * k) * SS),
                       ((hx + 18 * k) * SS, (hy + 26 * k) * SS)], fill=sp["kicker_col"])
    c = ease_back(prog(u, 0.78, 0.95))
    chip(im, 860, cy + 380 * k, sp["chip"], sp["acc"], sp["bg"], alpha=clamp(c), scale=max(c, 0.01) * k)


def versus(im, sp, u, cy, k):
    px = fit_px(sp, sp["title"], 900 * k, 230 * k)
    m, x0, y0 = text_at(sp["title"], title_font(sp, px), 540, cy)
    print_mask(im, m, x0, y0, sp["title_col"], prog(u, 0.0, 0.5), int(12 * k * SS), mode="both", head_col=head(sp))
    km, kx, ky = text_at(sp["kicker"], title_font(sp, 92 * k), 540, cy - 160 * k)
    print_mask(im, km, kx, ky, sp["kicker_col"], prog(u, 0.5, 0.62), int(9 * k * SS), mode="both",
               head_col=head(sp))
    # VS lands where the nozzles met, with a burst of sparks
    v = prog(u, 0.6, 0.72)
    if v > 0:
        d = ImageDraw.Draw(im)
        sc = (2.4 - 1.4 * ease_out(v)) * k
        r = 70 * sc
        d.ellipse(((540 - r) * SS, (cy + 170 * k - r) * SS, (540 + r) * SS, (cy + 170 * k + r) * SS),
                  fill=sp["title_col"])
        d.text((540 * SS, (cy + 170 * k) * SS), "VS", font=title_font(sp, 80 * sc), fill=sp["bg"], anchor="mm")
        sp_ = prog(u, 0.72, 0.9)
        if 0 < sp_ < 1:
            for i in range(12):
                a = i * math.pi / 6
                r0, r1 = (90 + 120 * sp_) * k, (120 + 180 * sp_) * k
                d.line(((540 + r0 * math.cos(a)) * SS, (cy + 170 * k + r0 * math.sin(a)) * SS,
                        (540 + r1 * math.cos(a)) * SS, (cy + 170 * k + r1 * math.sin(a)) * SS),
                       fill=mix(sp["bg"], sp["kicker_col"], 1 - sp_), width=int(6 * k * SS))
    c = ease_back(prog(u, 0.8, 0.95))
    chip(im, 540, cy + 330 * k, sp["chip"], sp["kicker_col"], sp["bg"], alpha=clamp(c), scale=max(c, 0.01) * k)


def blueprint(im, sp, u, cy, k):
    d = ImageDraw.Draw(im)
    fnt = title_font(sp, fit_px(sp, sp["title"], 900 * k, 210 * k))
    m, x0, y0 = text_at(sp["title"], fnt, 540, cy)
    # outline first: the mask's edge, revealed left to right
    o = ease_out(prog(u, 0.0, 0.4))
    if o > 0:
        edge = ImageChops.subtract(m, m.filter(__import__("PIL.ImageFilter", fromlist=["x"]).MinFilter(5)))
        cut = Image.new("L", m.size, 0)
        ImageDraw.Draw(cut).rectangle((0, 0, int(m.width * o), m.height), fill=255)
        im.paste(Image.new("RGB", m.size, sp["title_col"]), (x0, y0), ImageChops.multiply(edge, cut))
    # dimension lines: across the top and up the side
    dl = ease_out(prog(u, 0.2, 0.5))
    if dl > 0:
        c = sp["kicker_col"]
        xa, xb = x0 / SS, (x0 + m.width) / SS
        ya = y0 / SS - 40 * k
        d.line((xa * SS, ya * SS, (xa + (xb - xa) * dl) * SS, ya * SS), fill=c, width=int(3 * SS))
        for x in (xa, xa + (xb - xa) * dl):
            d.line((x * SS, (ya - 14 * k) * SS, x * SS, (ya + 14 * k) * SS), fill=c, width=int(3 * SS))
        yb = (y0 + m.height) / SS
        xs = xa - 50 * k
        ytop = yb - (yb - y0 / SS) * dl
        d.line((xs * SS, yb * SS, xs * SS, ytop * SS), fill=c, width=int(3 * SS))
        for y in (yb, ytop):
            d.line(((xs - 14 * k) * SS, y * SS, (xs + 14 * k) * SS, y * SS), fill=c, width=int(3 * SS))
        if dl >= 1:
            d.text(((xa + xb) / 2 * SS, (ya - 34 * k) * SS), sp["chip"], font=font("bold", 34 * k), fill=c,
                   anchor="mm")
    # then it fills, layer by layer
    print_mask(im, m, x0, y0, sp["title_col"], prog(u, 0.45, 0.8), int(12 * k * SS), head_col=head(sp))
    km, kx, ky = text_at(sp["kicker"], title_font(sp, 80 * k), 540, cy - 250 * k)
    print_mask(im, km, kx, ky, sp["kicker_col"], prog(u, 0.78, 0.92), int(9 * k * SS), head_col=head(sp))


def news(im, sp, u, cy, k):
    px = fit_px(sp, sp["title"], 900 * k, 230 * k)
    m, x0, y0 = text_at(sp["title"], title_font(sp, px), 540, cy)
    print_mask(im, m, x0, y0, sp["title_col"], prog(u, 0.0, 0.35), int(16 * k * SS), head_col=head(sp))
    d = ImageDraw.Draw(im)
    s = prog(u, 0.38, 0.5)
    if s > 0:
        sc = (2.6 - 1.6 * ease_out(s)) * k
        shake = 18 * k * math.exp(-max(u - 0.5, 0) * 30) * math.sin(u * 300) if u > 0.5 else 0
        fnt = font("bold", 88 * sc)
        tw = fnt.getlength(sp["kicker"]) / SS
        cx, yy = 540 + shake, cy - 190 * k
        blink = 1 if (u > 0.55 and int((u - 0.55) * 20) % 2 == 0 and u < 0.8) else 0
        fill = sp["title_col"] if not blink else sp["text"]
        d.rounded_rectangle(((cx - tw / 2 - 40 * sc) * SS, (yy - 62 * sc) * SS, (cx + tw / 2 + 40 * sc) * SS,
                             (yy + 62 * sc) * SS), 16 * SS, fill=fill)
        d.text((cx * SS, yy * SS), sp["kicker"], font=fnt, fill=sp["bg"], anchor="mm")
    # a ticker under the title
    t = ease_out(prog(u, 0.55, 0.7))
    if t > 0:
        y = cy + 170 * k
        d.rectangle((0, y * SS, W * SS * t, (y + 70 * k) * SS), fill=sp["title_col"])
        tick = "NEWS & HYPE  •  " * 8
        off = (u * 900) % 600
        d.text(((20 - off) * SS, (y + 35 * k) * SS), tick, font=font("bold", 38 * k), fill=sp["bg"], anchor="lm")
    c = ease_back(prog(u, 0.8, 0.95))
    chip(im, 540, cy + 330 * k, sp["chip"], sp["title_col"], sp["bg"], alpha=clamp(c), scale=max(c, 0.01) * k)


def friday(im, sp, u, cy, k):
    fnt = title_font(sp, fit_px(sp, sp["title"], 880 * k, 230 * k))
    ws = [fnt.getlength(c) / SS for c in sp["title"]]
    total = sum(ws) + 14 * k * (len(ws) - 1)
    x = 540 - total / 2
    for i, (c, w) in enumerate(zip(sp["title"], ws)):
        m = text_mask(c, fnt)
        x0, y0 = int((x + w / 2) * SS - m.width / 2), int(cy * SS - m.height / 2)
        a = 0.04 * i
        print_mask(im, m, x0, y0, sp["title_col"], prog(u, a, a + 0.5), int(12 * k * SS), head_col=head(sp),
                   small=True)
        x += w + 14 * k
    km, kx, ky = text_at(sp["kicker"], title_font(sp, 92 * k), 540, cy - 170 * k)
    print_mask(im, km, kx, ky, sp["kicker_col"], prog(u, 0.6, 0.75), int(9 * k * SS), head_col=head(sp))
    c = ease_back(prog(u, 0.8, 0.95))
    chip(im, 540, cy + 190 * k, sp["chip"], sp["acc"], sp["bg"], alpha=clamp(c), scale=max(c, 0.01) * k)


_prod = {}


def product_cutout(size):
    """The render with its studio grey keyed out, so it can print as a shape."""
    if size not in _prod:
        src = Image.open(PRODUCT_IMG).convert("RGB")
        bg = src.getpixel((4, 4))
        diff = ImageChops.difference(src, Image.new("RGB", src.size, bg)).convert("L")
        a = diff.point(lambda v: 0 if v < 14 else min(255, (v - 14) * 12))
        box = a.getbbox()
        src, a = src.crop(box), a.crop(box)
        sc = size * SS / max(src.size)
        sz = (int(src.width * sc), int(src.height * sc))
        _prod[size] = (src.resize(sz, Image.LANCZOS), a.resize(sz, Image.LANCZOS))
    return _prod[size]


def product(im, sp, u, cy, k):
    img, a = product_cutout(int(560 * k))
    x0, y0 = int(540 * SS - img.width / 2), int((cy - 120 * k) * SS - img.height / 2)
    print_mask(im, a, x0, y0, img, prog(u, 0.0, 0.6), int(14 * k * SS), head_col=head(sp), lines=True)
    ImageDraw.Draw(im).text((540 * SS, (y0 / SS + img.height / SS + 26 * k) * SS),
                            "Design-review render, not a photo", font=font("semi", 22 * k),
                            fill=mix(sp["bg"], sp["text"], 0.6 * prog(u, 0.6, 0.7)), anchor="mm")
    px = fit_px(sp, sp["title"], 940 * k, 120 * k)
    m, tx, ty = text_at(sp["title"], title_font(sp, px), 540, cy + 270 * k)
    print_mask(im, m, tx, ty, sp["title_col"], prog(u, 0.6, 0.85), int(10 * k * SS), head_col=head(sp))
    c = ease_back(prog(u, 0.85, 0.97))
    chip(im, 540, cy + 380 * k, sp["chip"], sp["acc"], sp["bg"], alpha=clamp(c), scale=max(c, 0.01) * k)


INTROS = {"explained": explained, "versus": versus, "blueprint": blueprint, "news": news, "friday": friday,
          "product": product}
LENGTH = {"sting": 1.5, "full": 3.0}


def frame(series, kind, t):
    sp = dict(SERIES[series], **INTRO_TEXT.get(series, {}))
    dur = LENGTH[kind]
    if kind == "full":
        im = background(sp)
        if sp.get("banner"):
            banner(im, sp, t)
        INTROS[series](im, sp, clamp(t / (dur * 0.9)), 900, 1.0)
        return im
    # sting: a panel in the series' own background, upper third, over transparent
    im = background(sp, alpha=True)
    k, cy = 0.62, 520
    grow = ease_out(prog(t, 0.0, 0.12)) * (1 - prog(t, dur - 0.15, dur))
    if grow > 0:
        d = ImageDraw.Draw(im)
        hw, hh = 470 * grow, 330 * grow
        d.rounded_rectangle(((540 - hw) * SS, (cy - hh) * SS, (540 + hw) * SS, (cy + hh) * SS), 36 * SS,
                            fill=sp["bg"] + (240,))
        if sp.get("grid"):
            pass
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    canvas = Image.new("RGB", im.size, sp["bg"])
    INTROS[series](canvas, sp, clamp(t / (dur * 0.85)), cy, k)
    # only what the intro drew (anything not the plain background) goes onto the panel
    diff = ImageChops.difference(canvas, Image.new("RGB", im.size, sp["bg"])).convert("L").point(
        lambda v: 255 if v > 3 else 0)
    panel = Image.new("L", im.size, 0)
    ImageDraw.Draw(panel).rounded_rectangle(((540 - 470) * SS, (cy - 330) * SS, (540 + 470) * SS,
                                             (cy + 330) * SS), 36 * SS, fill=255)
    vis = ImageChops.multiply(diff, panel).point(lambda v: int(v * clamp(grow * 1.5)))
    layer.paste(canvas, (0, 0), vis)
    im.alpha_composite(layer)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--series")
    ap.add_argument("--only", choices=list(LENGTH))
    ap.add_argument("--frame", help="series:kind:t")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.frame:
        s, kind, t = a.frame.split(":")
        im = frame(s, kind, float(t))
        if im.mode == "RGBA":
            bg = Image.new("RGBA", im.size, (110, 120, 130, 255))
            bg.alpha_composite(im)
            im = bg.convert("RGB")
        p = out / f"{s}_{kind}_{float(t):.2f}.png"
        im.resize((W, H), Image.LANCZOS).save(p)
        print(p)
        return
    for s in ([a.series] if a.series else INTROS):
        for kind in ([a.only] if a.only else LENGTH):
            alpha = kind == "sting"
            dst = out / s / f"{s}_intro_{kind}.{'mov' if alpha else 'mp4'}"
            dst.parent.mkdir(parents=True, exist_ok=True)
            encode(lambda t, s=s, kind=kind: frame(s, kind, t), int(round(LENGTH[kind] * FPS)), dst, alpha)


if __name__ == "__main__":
    main()
