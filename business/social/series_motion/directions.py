"""Series motion: three animation directions for Scott to pick from (2026-11-20).

Scott, 2026-11-20: "We also need some really eye catching and fun animated graphics. We need to
start standing out. We have several series that run and all are different in what they deliver."

Each series' look is locked (quality-bar-examples.md, "Series identity rule", Scott 2026-10-25):
colours, fonts and layout stay. What's new is how the series moves. Each direction below is shown
as a 3-second opener on two contrasting series, so Scott sees how the motion carries across looks:

  A  PRINTED  the title is printed onto the screen, layer by layer, by a nozzle that sweeps
              back and forth. Nobody outside 3D printing can own this.
  B  POP      kawaii sticker energy: letters bounce in one by one with squash and overshoot,
              sticker borders, a burst of filament confetti.
  C  SLAM     kinetic type: colour bars wipe across, words slam in with a flash and a shake.

    python3 directions.py OUT_DIR [--only A] [--frame A:explained:1.2]
"""
import argparse
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "explained_lesson006" / "fonts"
W, H, SS, FPS = 1080, 1920, 2, 30
DUR = 3.2

SERIES = {
    "explained": dict(bg=(246, 240, 226), ink=(32, 36, 46), acc=(232, 106, 44), acc2=(20, 110, 96),
                      kicker="3D PRINTING", lines=["EXPLAINED"], chip="LESSON 007", chip_col=(232, 106, 44)),
    "versus": dict(bg=(12, 13, 14), ink=(64, 242, 100), acc=(64, 242, 100), acc2=(245, 245, 240),
                   kicker="DAILY", lines=["VERSUS"], chip="DAY 18", chip_col=(245, 245, 240)),
}


def clamp(t):
    return max(0.0, min(1.0, t))


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def ease_out(t):
    return 1 - (1 - clamp(t)) ** 3


def ease_back(t, c=1.7):
    t = clamp(t)
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def ease_elastic(t):
    t = clamp(t)
    if t in (0, 1):
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


_f = {}


def font(name, px):
    k = (name, px)
    if k not in _f:
        f = {"anton": "Anton-Regular.ttf", "semi": "ChakraPetch-SemiBold.ttf", "bold": "ChakraPetch-Bold.ttf"}[name]
        _f[k] = ImageFont.truetype(str(FONTS / f), int(px * SS))
    return _f[k]


def mix(a, b, t):
    t = clamp(t)
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def canvas(bg):
    return Image.new("RGB", (W * SS, H * SS), bg)


def text_mask(s, fnt):
    """The text as an L mask, cropped tight, at SS scale."""
    l, t, r, b = fnt.getbbox(s)
    m = Image.new("L", (r - l + 8, b - t + 8), 0)
    ImageDraw.Draw(m).text((4 - l, 4 - t), s, font=fnt, fill=255)
    return m


def chip(im, cx, cy, s, col, bg, alpha=1.0, scale=1.0, rot=0.0, fill=False):
    if alpha <= 0 or scale <= 0:
        return
    fnt = font("semi", 44 * scale)
    tw = fnt.getlength(s)
    pw, ph = int(tw + 70 * SS * scale), int(86 * SS * scale)
    tile = Image.new("RGBA", (pw + 20, ph + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    c = mix(bg, col, alpha)
    if fill:
        d.rounded_rectangle((10, 10, pw + 10, ph + 10), 20 * SS * scale, fill=c + (int(255 * alpha),))
        d.text((10 + pw / 2, 10 + ph / 2), s, font=fnt, fill=bg + (255,), anchor="mm")
    else:
        d.rounded_rectangle((10, 10, pw + 10, ph + 10), 20 * SS * scale, outline=c + (255,), width=int(5 * SS))
        d.text((10 + pw / 2, 10 + ph / 2), s, font=fnt, fill=c + (255,), anchor="mm")
    if rot:
        tile = tile.rotate(rot, resample=Image.BICUBIC, expand=True)
    im.paste(tile, (int(cx * SS - tile.width / 2), int(cy * SS - tile.height / 2)), tile)


def brand(im, sp, t):
    d = ImageDraw.Draw(im)
    a = prog(t, 0.2, 0.6)
    d.text((540 * SS, 1820 * SS), "ONBRANDCRAFTZ", font=font("semi", 28), fill=mix(sp["bg"], sp["ink"], a * 0.8),
           anchor="mm")


# ------------------------------------------------------------------ A: PRINTED
def nozzle(d, x, y, col):
    """A hotend seen from the front: block, cone, tip at (x, y)."""
    s = SS
    d.rounded_rectangle(((x - 46) * s, (y - 120) * s, (x + 46) * s, (y - 50) * s), 10 * s, fill=col)
    d.polygon([((x - 26) * s, (y - 52) * s), ((x + 26) * s, (y - 52) * s), ((x + 7) * s, (y - 6) * s),
               ((x - 7) * s, (y - 6) * s)], fill=col)
    d.rectangle(((x - 5) * s, (y - 8) * s, (x + 5) * s, y * s), fill=col)


def printed_block(im, s, fnt, col, bg, cx, cy, t0, t1, t, line_px=11, show_nozzle=True, nozzle_col=None):
    """Print text s centred at (cx, cy) between t0 and t1: bottom layer first, sweeping in
    alternate directions, with visible layer lines and a nozzle at the bead's front."""
    m = text_mask(s, fnt)
    w, h = m.size
    x0, y0 = int(cx * SS - w / 2), int(cy * SS - h / 2)
    lh = line_px * SS
    n = math.ceil(h / lh)
    p = prog(t, t0, t1)
    if p <= 0:
        return None
    done = p * n
    k = int(done)                                   # layers finished
    frac = done - k
    reveal = Image.new("L", (w, h), 0)
    rd = ImageDraw.Draw(reveal)
    for i in range(min(k, n)):
        rd.rectangle((0, h - (i + 1) * lh, w, h - i * lh), fill=255)
    head = None
    if k < n:
        # the current layer, part-way along; left to right on even layers, back on odd
        y_top, y_bot = h - (k + 1) * lh, h - k * lh
        if k % 2 == 0:
            xe = int(w * frac)
            rd.rectangle((0, y_top, xe, y_bot), fill=255)
        else:
            xe = int(w * (1 - frac))
            rd.rectangle((xe, y_top, w, y_bot), fill=255)
        head = ((x0 + xe) / SS, (y0 + y_top) / SS)
    shown = ImageChops.multiply(m, reveal)
    layer = Image.new("RGB", (w, h), col)
    # layer lines: a darker hairline at every layer boundary, the printed look
    ld = ImageDraw.Draw(layer)
    dark = mix(col, (0, 0, 0), 0.28) if sum(col) > 200 else mix(col, (255, 255, 255), 0.2)
    for i in range(1, n + 1):
        yy = h - i * lh
        ld.line((0, yy, w, yy), fill=dark, width=max(1, SS))
    im.paste(layer, (x0, y0), shown)
    if head and show_nozzle:
        nozzle(ImageDraw.Draw(im), head[0], head[1], nozzle_col or mix(bg, (120, 124, 130), 0.9))
    return head


def dir_printed(sp, t):
    im = canvas(sp["bg"])
    d = ImageDraw.Draw(im)
    bed = mix(sp["bg"], sp["ink"], 0.12)
    # a build-plate line the words print onto
    a = ease_out(prog(t, 0.0, 0.35))
    d.rounded_rectangle(((540 - 430 * a) * SS, 1040 * SS, (540 + 430 * a) * SS, 1056 * SS), 8 * SS, fill=bed)
    printed_block(im, sp["kicker"], font("anton", 92), sp["acc2"] if sp is SERIES["explained"] else sp["acc2"],
                  sp["bg"], 540, 760, 1.25, 1.75, t, 9, nozzle_col=mix(sp["bg"], sp["ink"], 0.55))
    printed_block(im, sp["lines"][0], font("anton", 230), sp["ink"] if sp is SERIES["explained"] else sp["acc"],
                  sp["bg"], 540, 920, 0.2, 1.25, t, 12, nozzle_col=mix(sp["bg"], sp["ink"], 0.55))
    # done: the plate drops away, the chip pops
    c = ease_back(prog(t, 1.85, 2.25))
    chip(im, 540, 1180, sp["chip"], sp["chip_col"], sp["bg"], alpha=clamp(c), scale=max(c, 0.01))
    brand(im, sp, t)
    return im


# ------------------------------------------------------------------ B: POP
def sticker_letter(ch, fnt, col, border, shadow):
    l, t, r, b = fnt.getbbox(ch)
    pad = 26 * SS
    tile = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    xy = (pad - l, pad - t)
    sh = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 8 * SS, xy[1] + 10 * SS), ch, font=fnt, fill=shadow + (110,),
                            stroke_width=int(12 * SS), stroke_fill=shadow + (110,))
    sh = sh.filter(ImageFilter.GaussianBlur(4 * SS))
    tile.alpha_composite(sh)
    d.text(xy, ch, font=fnt, fill=col + (255,), stroke_width=int(12 * SS), stroke_fill=border + (255,))
    return tile


_conf = None


def confetti():
    global _conf
    if _conf is None:
        rnd = random.Random(7)
        _conf = [dict(a=rnd.uniform(0, 2 * math.pi), v=rnd.uniform(500, 1300), spin=rnd.uniform(-8, 8),
                      L=rnd.uniform(26, 60), k=rnd.randrange(3)) for _ in range(46)]
    return _conf


def dir_pop(sp, t):
    im = canvas(sp["bg"]).convert("RGBA")
    word = sp["lines"][0]
    fnt = font("anton", 220)
    border = (255, 255, 255) if sp is SERIES["explained"] else (12, 13, 14)
    col = sp["acc"] if sp is SERIES["explained"] else sp["acc"]
    widths = [fnt.getlength(c) / SS for c in word]
    total = sum(widths) + 8 * (len(word) - 1)
    x = 540 - total / 2
    rnd = random.Random(3)
    for i, (c, w) in enumerate(zip(word, widths)):
        t0 = 0.25 + 0.07 * i
        p = prog(t, t0, t0 + 0.55)
        if p > 0:
            sc = ease_elastic(p)
            sq = 1 + 0.18 * math.sin(min(p, 1) * math.pi) * (1 - p)    # squash on landing
            rot = rnd.uniform(-9, 9) * (1 - ease_out(p)) + (3 if i % 2 else -3)
            tile = sticker_letter(c, fnt, col, border, (0, 0, 0))
            tw, th = tile.size
            tile = tile.resize((max(1, int(tw * sc * sq)), max(1, int(th * sc / sq))), Image.BICUBIC)
            tile = tile.rotate(rot, resample=Image.BICUBIC, expand=True)
            cx, cy = (x + w / 2) * SS, (930 - 120 * (1 - ease_out(p))) * SS
            im.alpha_composite(tile, (int(cx - tile.width / 2), int(cy - tile.height / 2)))
        x += w + 8
    # kicker drops on top like a label
    kp = ease_back(prog(t, 0.05, 0.45))
    if kp > 0:
        chip(im, 540, 660 - 80 * (1 - kp), sp["kicker"], sp["ink"] if sp is SERIES["explained"] else sp["acc2"],
             sp["bg"], alpha=clamp(kp), scale=1.25, rot=-4, fill=True)
    # filament confetti
    tb = t - 1.05
    if 0 < tb < 2.1:
        d = ImageDraw.Draw(im)
        cols = [sp["acc"], sp["acc2"], sp["ink"] if sp is SERIES["explained"] else (245, 245, 240)]
        for c in confetti():
            px = 540 + math.cos(c["a"]) * c["v"] * tb
            py = 930 + math.sin(c["a"]) * c["v"] * tb + 900 * tb * tb
            ang = c["spin"] * tb
            dx, dy = math.cos(ang) * c["L"] / 2, math.sin(ang) * c["L"] / 2
            al = 1 - prog(tb, 1.4, 2.1)
            d.line(((px - dx) * SS, (py - dy) * SS, (px + dx) * SS, (py + dy) * SS),
                   fill=mix(sp["bg"], cols[c["k"]], al) + (255,), width=int(11 * SS))
    cp = ease_back(prog(t, 1.5, 1.9))
    chip(im, 540, 1170, sp["chip"], sp["chip_col"], sp["bg"], alpha=clamp(cp), scale=max(cp, 0.01), rot=3)
    im = im.convert("RGB")
    brand(im, sp, t)
    return im


# ------------------------------------------------------------------ C: SLAM
def dir_slam(sp, t):
    bg = sp["bg"]
    # flash on each slam
    flash = max(1 - prog(t, 0.55, 0.7), 0) * (t >= 0.55) + max(1 - prog(t, 0.95, 1.1), 0) * (t >= 0.95) * 0.6
    im = canvas(mix(bg, (255, 255, 255) if sum(bg) < 300 else sp["acc"], flash * 0.55))
    d = ImageDraw.Draw(im)
    # two diagonal bars wipe across
    for k, (col, y, t0) in enumerate([(sp["acc"], 820, 0.05), (sp["acc2"], 1010, 0.18)]):
        p = ease_out(prog(t, t0, t0 + 0.35))
        out = ease_out(prog(t, 0.36, 0.62))         # a swipe: gone before the first word lands
        xa = -400 + 1900 * out
        xb = -400 + 1900 * p
        if xb > xa:
            d.polygon([(xa * SS, (y - 70) * SS), ((xb + 120) * SS, (y - 70) * SS), (xb * SS, (y + 70) * SS),
                       ((xa - 120) * SS, (y + 70) * SS)], fill=mix(bg, col, 0.9 if k == 0 else 0.5))
    shake = 0
    for ts in (0.55, 0.95):
        if t >= ts:
            e = math.exp(-(t - ts) * 14)
            shake += 22 * e * math.sin((t - ts) * 90)

    def slam(s, fnt, col, cy, ts):
        p = prog(t, ts - 0.18, ts)
        if p <= 0:
            return
        sc = 2.6 - 1.6 * (p ** 2)
        m = text_mask(s, fnt)
        m = m.resize((int(m.width * sc), int(m.height * sc)), Image.BICUBIC)
        a = int(255 * min(1, p * 2))
        m = m.point(lambda v: v * a // 255)
        x0 = int((540 + shake) * SS - m.width / 2)
        y0 = int((cy + shake * 0.4) * SS - m.height / 2)
        # speed lines behind the word while it lands
        if p < 1:
            for j in range(9):
                yy = y0 + m.height * (j + 0.5) / 9
                d.line((0, yy, W * SS, yy), fill=mix(bg, col, 0.25 * (1 - p)), width=int(4 * SS))
        im.paste(Image.new("RGB", m.size, col), (x0, y0), m)

    txt_col = sp["ink"] if sp is SERIES["explained"] else sp["acc"]
    slam(sp["kicker"], font("anton", 110), sp["acc2"] if sp is SERIES["explained"] else sp["acc2"], 760, 0.55)
    slam(sp["lines"][0], font("anton", 240), txt_col, 930, 0.95)
    cp = ease_out(prog(t, 1.35, 1.6))
    if cp > 0:
        chip(im, 540 + 700 * (1 - cp), 1170, sp["chip"], sp["chip_col"], bg, alpha=1.0, scale=1.0, fill=True)
    brand(im, sp, t)
    return im


DIRS = {"A": ("printed", dir_printed), "B": ("pop", dir_pop), "C": ("slam", dir_slam)}


def frame(direction, series, t):
    return DIRS[direction][1](SERIES[series], t).resize((W, H), Image.LANCZOS)


def render(direction, out_dir):
    name = DIRS[direction][0]
    out = Path(out_dir) / f"{direction}_{name}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                           "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                          stdin=subprocess.PIPE)
    for series in SERIES:
        for i in range(int(DUR * FPS)):
            ff.stdin.write(frame(direction, series, i / FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--only")
    ap.add_argument("--frame", help="DIR:series:t, one PNG")
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.frame:
        dr, se, t = a.frame.split(":")
        p = Path(a.out) / f"{dr}_{se}_{float(t):.2f}.png"
        frame(dr, se, float(t)).save(p)
        print(p)
        return
    for dr in ([a.only] if a.only else DIRS):
        render(dr, a.out)


if __name__ == "__main__":
    main()
