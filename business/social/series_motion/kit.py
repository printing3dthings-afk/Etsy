"""The Printed motion kit: every series' opener, end card, lower-third and transition,
in the style Scott picked on 2026-11-20 ("A": titles printed onto the screen layer by layer).

Each series keeps its locked look (quality-bar-examples.md, "Series identity rule", Scott
2026-10-25). SERIES below holds those looks. The Explained and green-line colours are exact (from
the Lesson 006 identity and the rule's #40F264); News & Hype's yellow #FFD21F is from the rule.
Blueprint blue, Friday Makers' charcoal and gold, and the Product posts gradient aren't written
down anywhere in the repo, so they're close matches to the descriptions: Benson, correct the hex
values in SERIES from your templates and re-run. Every clip rebuilds from this file.

    python3 kit.py OUT_DIR                                  # the sample pack, every series
    python3 kit.py OUT_DIR --series versus --chip "DAY 19"  # one series, your episode text
    python3 kit.py OUT_DIR --only opener,endcard            # some pieces only
    python3 kit.py OUT_DIR --sizzle                         # every opener back to back

Pieces (1080 x 1920, 30 fps):
  opener      3.2 s  kicker + title printed by the nozzle, then the episode chip   (mp4)
  endcard     4.0 s  "FOLLOW ONBRANDCRAFTZ" printed, then the series' CTA bar         (mp4)
  lowerthird  3.0 s  a printed strip for a name or a caption, transparent         (mov, alpha)
  transition  0.9 s  the screen prints over in bands and clears, transparent       (mov, alpha)
"""
import argparse
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from directions import (SS, W, H, FPS, clamp, prog, ease_out, ease_back, font, mix, chip,
                        printed_block, nozzle)

SERIES = {
    "explained": dict(name="3D Printing, Explained", bg=(246, 240, 226), title_col=(32, 36, 46),
                      kicker_col=(20, 110, 96), acc=(232, 106, 44), text=(32, 36, 46),
                      kicker="3D PRINTING", title="EXPLAINED", chip="LESSON 007", font="anton",
                      cta="SEND THIS TO A MAKER", exact=True),
    "versus": dict(name="Daily Versus (the green line)", bg=(12, 13, 14), title_col=(64, 242, 100),
                   kicker_col=(245, 245, 240), acc=(64, 242, 100), text=(245, 245, 240),
                   kicker="DAILY", title="VERSUS", chip="DAY 18", font="anton",
                   cta="WHICH ONE WOULD YOU CHOOSE?", exact=True),
    "blueprint": dict(name="Maker's Blueprint", bg=(26, 74, 140), title_col=(245, 247, 250),
                      kicker_col=(214, 170, 64), acc=(214, 170, 64), text=(245, 247, 250),
                      kicker="MAKER'S", title="BLUEPRINT", chip="SPEC 007", font="bold",
                      cta="SAVE THIS FOR YOUR NEXT PRINT", grid=True, exact=False),
    "news": dict(name="News & Hype", bg=(16, 16, 18), title_col=(255, 210, 31), kicker_col=(245, 245, 240),
                 acc=(255, 210, 31), text=(245, 245, 240), kicker="NEWS", title="& HYPE", chip="THIS WEEK",
                 font="anton", cta="THE BIG QUESTION: TELL US BELOW", exact=True),
    "friday": dict(name="Friday Makers", bg=(48, 40, 34), title_col=(246, 240, 226), kicker_col=(206, 164, 74),
                   acc=(206, 164, 74), text=(246, 240, 226), kicker="FRIDAY", title="MAKERS", chip="WEEK 5",
                   font="anton", cta="JOIN THE ONBRANDCRAFTZ MAKERS GROUP", banner=True, exact=False),
    # BIQU "Panda on the Bench" (2026-11-25). Benson hasn't sent the partner series' locked look
    # (asked 2026-11-20, content-ramp thread), so this is ours to change: panda black and white
    # with a bamboo-green accent, and no BIQU or BIGTREETECH logo (their marks, not ours to use).
    "bench": dict(name="Panda on the Bench (BIQU partner series)", bg=(20, 21, 22), title_col=(246, 246, 242),
                  kicker_col=(126, 190, 88), acc=(126, 190, 88), text=(246, 246, 242),
                  kicker="PANDA ON", title="THE BENCH", chip="EP 002", font="anton",
                  cta="WHAT SHOULD WE TEST NEXT?", exact=False),
    "product": dict(name="Product posts", bg=(58, 30, 36), bg2=(196, 98, 58), title_col=(255, 246, 232),
                    kicker_col=(255, 214, 160), acc=(255, 214, 160), text=(255, 246, 232),
                    kicker="NEW PRINT", title="SANTA'S WORKSHOP", chip="DESIGNED BY US", font="anton",
                    cta="LINK IN BIO", gradient=True, exact=False),
}


# ------------------------------------------------------------------ backgrounds
def background(sp, alpha=False):
    if alpha:
        return Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    im = Image.new("RGB", (W * SS, H * SS), sp["bg"])
    d = ImageDraw.Draw(im)
    if sp.get("gradient"):
        for y in range(0, H * SS, 4):
            d.rectangle((0, y, W * SS, y + 4), fill=mix(sp["bg"], sp["bg2"], (y / (H * SS)) ** 1.3))
    if sp.get("grid"):
        g = mix(sp["bg"], (255, 255, 255), 0.12)
        g2 = mix(sp["bg"], (255, 255, 255), 0.22)
        for i in range(0, W + 1, 45):
            d.line((i * SS, 0, i * SS, H * SS), fill=g2 if i % 180 == 0 else g, width=SS)
        for j in range(0, H + 1, 45):
            d.line((0, j * SS, W * SS, j * SS), fill=g2 if j % 180 == 0 else g, width=SS)
    return im


def banner(im, sp, t):
    """Friday Makers' banner strip, printed across the top."""
    p = ease_out(prog(t, 0.0, 0.5))
    if p <= 0:
        return
    d = ImageDraw.Draw(im)
    d.rectangle((0, 300 * SS, W * SS * p, 380 * SS), fill=sp["acc"])
    if p > 0.6:
        d.text((540 * SS, 340 * SS), "FRIDAY MAKERS", font=font("bold", 40), fill=sp["bg"], anchor="mm")


def title_font(sp, px):
    return font(sp["font"], px)


def fit_px(sp, s, maxw, start):
    px = start
    while px > 60 and title_font(sp, px).getlength(s) / SS > maxw:
        px -= 6
    return px


def brand(im, sp, t):
    a = prog(t, 0.2, 0.6)
    ImageDraw.Draw(im).text((540 * SS, 1820 * SS), "ONBRANDCRAFTZ", font=font("semi", 28),
                            fill=mix(sp["bg"], sp["text"], a * 0.8), anchor="mm")


def plate(im, sp, t, y, t0=0.0):
    a = ease_out(prog(t, t0, t0 + 0.35))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(((540 - 430 * a) * SS, y * SS, (540 + 430 * a) * SS, (y + 16) * SS), 8 * SS,
                        fill=mix(sp["bg"], sp["text"], 0.14))


# ------------------------------------------------------------------ pieces
def opener(sp, t):
    im = background(sp)
    if sp.get("banner"):
        banner(im, sp, t)
    plate(im, sp, t, 1040)
    head_col = mix(sp["bg"], sp["text"], 0.55)
    px = fit_px(sp, sp["title"], 960, 230)
    printed_block(im, sp["title"], title_font(sp, px), sp["title_col"], sp["bg"], 540, 920, 0.2, 1.25, t, 12,
                  nozzle_col=head_col)
    printed_block(im, sp["kicker"], title_font(sp, 92), sp["kicker_col"], sp["bg"], 540, 760, 1.25, 1.75, t, 9,
                  nozzle_col=head_col)
    c = ease_back(prog(t, 1.85, 2.25))
    chip(im, 540, 1180, sp["chip"], sp["acc"], sp["bg"], alpha=clamp(c), scale=max(c, 0.01))
    brand(im, sp, t)
    return im


def endcard(sp, t):
    im = background(sp)
    if sp.get("banner"):
        banner(im, sp, t)
    head_col = mix(sp["bg"], sp["text"], 0.55)
    plate(im, sp, t, 960)
    printed_block(im, "FOLLOW", title_font(sp, 120), sp["kicker_col"], sp["bg"], 540, 700, 0.1, 0.6, t, 10,
                  nozzle_col=head_col)
    px = fit_px(sp, "ONBRANDCRAFTZ", 960, 170)
    printed_block(im, "ONBRANDCRAFTZ", title_font(sp, px), sp["title_col"], sp["bg"], 540, 860, 0.6, 1.7, t, 12,
                  nozzle_col=head_col)
    # the CTA bar prints across in one sweep, then its words appear
    p = ease_out(prog(t, 1.9, 2.4))
    if p > 0:
        d = ImageDraw.Draw(im)
        fnt = font("bold", 50)
        cta = sp["cta"]
        while fnt.getlength(cta) / SS > 900:
            fnt = font("bold", fnt.size / SS - 4)
        d.rounded_rectangle((60 * SS, 1180 * SS, (60 + 960 * p) * SS, 1310 * SS), 22 * SS, fill=sp["acc"])
        if p < 1:
            nozzle(d, 60 + 960 * p, 1180, head_col)
        a = prog(t, 2.35, 2.6)
        d.text((540 * SS, 1245 * SS), cta, font=fnt, fill=mix(sp["acc"], sp["bg"], a), anchor="mm")
    brand(im, sp, t)
    return im


def lowerthird(sp, t, text="SCOTT · ONBRANDCRAFTZ"):
    """A strip printed in four quick layers, the words, a hold, then it clears."""
    im = background(sp, alpha=True)
    d = ImageDraw.Draw(im)
    fnt = font("bold", 46)
    w = fnt.getlength(text) / SS + 110
    x0, y0, h = 60, 1350, 104
    n, lh = 4, 104 / 4
    out = prog(t, 2.5, 2.9)
    head_col = mix(sp["bg"], sp["text"], 0.55)
    for k in range(n):
        p = prog(t, 0.05 + 0.13 * k, 0.18 + 0.13 * k)
        if p <= 0 or out >= 1:
            continue
        yb = y0 + h - (k + 1) * lh
        xa, xb = (x0, x0 + w * p) if k % 2 == 0 else (x0 + w * (1 - p), x0 + w)
        xa = max(xa, x0 + w * out)
        if xb > xa:
            d.rectangle((xa * SS, yb * SS, xb * SS, (yb + lh) * SS), fill=sp["bg"] + (255,))
            d.line((xa * SS, (yb + lh) * SS, xb * SS, (yb + lh) * SS), fill=mix(sp["bg"], sp["acc"], 0.4) + (255,),
                   width=SS)
        if p < 1:
            nozzle(d, xb if k % 2 == 0 else xa, yb, head_col + (255,))
    # the accent edge, then the words
    e = ease_out(prog(t, 0.6, 0.8)) * (1 - out)
    if e > 0:
        d.rectangle((x0 * SS, y0 * SS, (x0 + 14) * SS, (y0 + h) * SS), fill=sp["acc"] + (int(255 * e),))
        a = prog(t, 0.7, 0.95) * (1 - out)
        d.text(((x0 + 50) * SS, (y0 + h / 2) * SS), text, font=fnt, fill=sp["text"] + (int(255 * a),), anchor="lm")
    return im


def transition(sp, t, dur=0.9):
    """Bands print bottom to top in the accent colour until the screen is covered (cut under
    it at the midpoint), then clear top to bottom."""
    im = background(sp, alpha=True)
    d = ImageDraw.Draw(im)
    n = 14
    bh = H / n
    half = dur / 2
    head_col = mix(sp["acc"], (0, 0, 0), 0.45)
    if t <= half:
        done = prog(t, 0, half * 0.92) * n
        for i in range(n):
            y1 = H - i * bh
            if i < int(done):
                d.rectangle((0, (y1 - bh) * SS, W * SS, y1 * SS), fill=sp["acc"] + (255,))
            elif i == int(done):
                f = done - i
                xa, xb = (0, W * f) if i % 2 == 0 else (W * (1 - f), W)
                d.rectangle((xa * SS, (y1 - bh) * SS, xb * SS, y1 * SS), fill=sp["acc"] + (255,))
                nozzle(d, xb if i % 2 == 0 else xa, y1 - bh, head_col + (255,))
    else:
        gone = prog(t, half, dur) * n
        for i in range(n):
            y0 = i * bh
            if i >= int(gone):
                if i == int(gone):
                    f = gone - i
                    d.rectangle((W * f * SS, y0 * SS, W * SS, (y0 + bh) * SS), fill=sp["acc"] + (255,))
                else:
                    d.rectangle((0, y0 * SS, W * SS, (y0 + bh) * SS), fill=sp["acc"] + (255,))
    return im


PIECES = {"opener": (opener, 3.2, False), "endcard": (endcard, 4.0, False),
          "lowerthird": (lowerthird, 3.0, True), "transition": (transition, 0.9, True)}


def encode(frames_fn, n, out, alpha):
    if alpha:
        args = ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(out)]
    else:
        args = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", str(out)]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", *args], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frames_fn(i / FPS).resize((W, H), Image.LANCZOS).tobytes())
    ff.stdin.close()
    ff.wait()
    print(out)


def build(out_dir, series, pieces, overrides):
    sp = dict(SERIES[series], **{k: v for k, v in overrides.items() if v})
    for piece in pieces:
        fn, dur, alpha = PIECES[piece]
        ext = "mov" if alpha else "mp4"
        out = Path(out_dir) / series / f"{series}_{piece}.{ext}"
        out.parent.mkdir(parents=True, exist_ok=True)
        encode(lambda t, fn=fn: fn(sp, t), int(round(dur * FPS)), out, alpha)
        # a still of the finished state, for previews and thumbnails
        if not alpha:
            fn(sp, dur - 0.05).resize((W, H), Image.LANCZOS).save(out.with_suffix(".png"))


def sizzle(out_dir):
    names = list(SERIES)
    per = 2.6
    n = int(round(per * len(names) * FPS))

    def fr(t):
        k = min(int(t / per), len(names) - 1)
        return opener(SERIES[names[k]], t - k * per)
    encode(fr, n, Path(out_dir) / "all_series_openers.mp4", False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--series", help="one series; default all")
    ap.add_argument("--only", help="comma-separated pieces")
    ap.add_argument("--title")
    ap.add_argument("--kicker")
    ap.add_argument("--chip")
    ap.add_argument("--cta")
    ap.add_argument("--sizzle", action="store_true")
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.sizzle:
        sizzle(a.out)
        return
    pieces = a.only.split(",") if a.only else list(PIECES)
    for s in ([a.series] if a.series else SERIES):
        build(a.out, s, pieces, dict(title=a.title, kicker=a.kicker, chip=a.chip, cta=a.cta))


if __name__ == "__main__":
    main()
