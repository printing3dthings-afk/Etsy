"""Explained, Lesson 008 ("What 100% infill costs"): Lesson 006's advice, priced on our own
Gingerbread Cottage (2026-11-20). Same identity and engine as Lessons 006 and 007.

The cottage was sliced three times in Bambu Studio on 2026-11-20 (tools/bambu_slice.py, P1S
0.4, PLA Basic, 0.20 mm Standard, supports off), changing only walls and infill. The figures
are each slice's own Metadata/slice_info.config, copied to facts/slices.json. No strength is
claimed for these three slices: strength stays with Lesson 006's credited pull tests.

    python3 animate.py OUT_DIR [--clean] [--stills ...] [--frame T]
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "explained_lesson006"))
from animate import (CREAM, INK, ORANGE, TEAL, CARD, W, H, SS, Frame, mix, clamp, prog,  # noqa: E402
                     ease_out, ease_in_out, ease_back, font, wrap)

ROOT = HERE.parents[2]
RENDER = ROOT / "openscad_models/christmas_village/gingerbread/cottage/images/gingerbread_cottage_colour_three_quarter.png"
DUR = 42.0
LESSON = "LESSON 008"
FACTS = json.loads((HERE / "facts" / "slices.json").read_text())
# The three setups, in the order they're shown; keys match facts/slices.json.
SETUPS = [("w2_i100", "2 WALLS, 100% INFILL", INK), ("w5_i20", "5 WALLS, 20% INFILL", ORANGE),
          ("w3_i15", "OURS: 3 WALLS, 15%", TEAL)]
CREDIT = "BAMBU STUDIO SLICES OF OUR GINGERBREAD COTTAGE, P1S, 0.20 MM LAYERS"


def hm(secs):
    m = round(secs / 60)
    return f"{m // 60} h {m % 60:02d} m"


G = {k: FACTS[k]["grams"] for k, _, _ in SETUPS}
T = {k: FACTS[k]["seconds"] for k, _, _ in SETUPS}
EXTRA_MIN = round((T["w2_i100"] - T["w3_i15"]) / 600) * 10      # "about N minutes", to the nearest 10

VO = [
    (0.3, 3.0, "Lesson 6 said: don't print at 100% infill."),
    (3.2, 6.6, "So we sliced our own Gingerbread Cottage three ways."),
    (7.0, 10.2, "Same house, same printer. Only the walls and infill change."),
    (10.6, 14.4, f"Two walls at 100% infill: {G['w2_i100']:.0f} grams of plastic."),
    (14.6, 17.4, f"Five walls at 20%: {G['w5_i20']:.0f} grams."),
    (17.6, 21.6, f"Ours, three walls at 15%: {G['w3_i15']:.0f} grams. Less than half."),
    (22.2, 26.6, f"The solid one also takes about {EXTRA_MIN} minutes longer to print."),
    (27.0, 31.6, "Lesson 6 showed where the strength is: in the walls."),
    (31.8, 35.6, "The plastic in the middle mostly just costs you."),
    (36.0, 39.0, "Before you print solid, slice it both ways."),
    (39.2, 42.0, "Send this to the maker who prints everything at 100%."),
]
SCENES = [("HOOK", 0.0, 6.8), ("SETUPS", 6.8, 10.4), ("GRAMS", 10.4, 22.0), ("TIME", 22.0, 26.8),
          ("RULE", 26.8, DUR)]


def chrome(f):
    f.text((60, 70), "3D PRINTING, EXPLAINED", font("semi", 30), INK, anchor="lm")
    f.rrect((826, 46, 1020, 96), 12, outline=ORANGE, width=3)
    f.text((923, 71), LESSON, font("semi", 30), ORANGE)
    f.text((60, 1862), "ONBRANDCRAFTZ", font("semi", 24), INK, anchor="lm")


def caption(f, t):
    for a, b, s in VO:
        al = min(prog(t, a - 0.15, a + 0.1), 1 - prog(t, b + 0.1, b + 0.3)) if t < b + 0.3 else 0
        if al <= 0:
            continue
        fnt = font("reg", 40)
        ls = wrap(s, fnt, 860)
        h = 66 + 52 * (len(ls) - 1)
        y0 = 1500
        f.rrect((50, y0, 1030, y0 + h + 24), 18, fill=mix(CREAM, INK, al))
        for i, l in enumerate(ls):
            f.text((540, y0 + 12 + 33 + 52 * i), l, fnt, CREAM, alpha=al, bg=mix(CREAM, INK, al))


def fade(t, a, b, d=0.35):
    return min(ease_out(prog(t, a, a + d)), 1 - prog(t, b - d, b))


def title(f, t, s, y, a0, col=INK, px=96):
    p = ease_out(prog(t, a0, a0 + 0.55))
    f.text((540, y + 36 * (1 - p)), s, font("anton", px), col, alpha=p)


def credit(f, al):
    f.text((540, 1440), CREDIT, font("semi", 24), mix(CREAM, INK, 0.7), alpha=al)


_render = {}


def render_img(size):
    if size not in _render:
        im = Image.open(RENDER).convert("RGB").resize((size * SS, size * SS), Image.LANCZOS)
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 28 * SS, fill=255)
        _render[size] = (im, m)
    return _render[size]


def paste_render(f, x, y, size, al):
    if al <= 0:
        return
    im, m = render_img(size)
    if al < 1:
        m = m.point(lambda v: int(v * al))
    f.im.paste(im, (int(x * SS), int(y * SS)), m)
    f.rrect((x, y, x + size, y + size), 28, outline=mix(CREAM, INK, al), width=4)
    f.text((x + size / 2, y + size + 30), "Design-review render, not a photo", font("reg", 26), INK, alpha=al)


def section(f, x, y, s, walls, infill, col, al):
    """A square of wall in cross-section: perimeters round the outside, infill inside."""
    if al <= 0:
        return
    f.rrect((x, y, x + s, y + s), 10, fill=mix(CREAM, CARD, al), outline=mix(CREAM, INK, al), width=3)
    lw = 14
    for i in range(walls):
        o = 10 + i * (lw + 4)
        f.rrect((x + o, y + o, x + s - o, y + s - o), 8, outline=mix(CREAM, col, al), width=lw)
    o = 10 + walls * (lw + 4)
    x0, y0, x1, y1 = x + o, y + o, x + s - o, y + s - o
    if infill >= 100:
        k = y0
        while k < y1:
            f.line([(x0, k + 7), (x1, k + 7)], col, 12, alpha=al)
            k += 16
    else:
        gap = {20: 34, 15: 44}[infill]
        n = int((x1 - x0) / gap) + 1
        for i in range(-n, n + 1):
            a = (x0 + i * gap, y0)
            b = (x0 + i * gap + (y1 - y0), y1)
            c = (x0 + i * gap + (y1 - y0), y0)
            d = (x0 + i * gap, y1)
            for p, q in ((a, b), (c, d)):
                # clip each diagonal to the box
                pts = []
                for u in [k / 40 for k in range(41)]:
                    px, py = p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u
                    if x0 <= px <= x1:
                        pts.append((px, py))
                if len(pts) > 1:
                    f.line(pts, col, 4, alpha=al)


# ------------------------------------------------------------------ scenes
def hook(f, t):
    al = fade(t, 0.0, 6.8)
    title(f, t, "WHAT 100% INFILL", 300, 0.25, INK, 104)
    title(f, t, "COSTS", 420, 0.45, ORANGE, 104)
    paste_render(f, 240, 560, 600, ease_out(prog(t, 3.2, 3.9)) * al)
    f.text((540, 1300), "OUR GINGERBREAD COTTAGE", font("anton", 64), TEAL, alpha=ease_out(prog(t, 3.6, 4.2)) * al)


def setups(f, t):
    a0, a1 = 6.8, 10.4
    al = fade(t, a0, a1)
    title(f, t, "SAME HOUSE, 3 WAYS", 280, a0 + 0.1, INK, 92)
    for i, (k, lab, col) in enumerate(SETUPS):
        p = ease_back(prog(t, a0 + 0.5 + 0.35 * i, a0 + 1.1 + 0.35 * i)) * al
        x = 60 + i * 330
        section(f, x + 15, 560, 270, int(lab.split()[0]) if i < 2 else 3,
                {0: 100, 1: 20, 2: 15}[i], col, clamp(p))
        for j, ln in enumerate(lab.replace(": ", ":\n").replace(", ", ",\n").split("\n")):
            f.text((x + 150, 900 + 46 * j), ln.strip(), font("bold", 34), col, alpha=clamp(p))
    f.text((540, 1300), "ONLY WALLS AND INFILL CHANGE", font("anton", 62), INK,
           alpha=ease_out(prog(t, a0 + 1.8, a0 + 2.3)) * al)


def bars(f, t, a0, a1, key_t, values, fmt, unit_title, at):
    al = fade(t, a0, a1)
    title(f, t, unit_title, 280, a0 + 0.1, INK, 96)
    vmax = max(values.values())
    for i, (k, lab, col) in enumerate(SETUPS):
        p = ease_out(prog(t, at[i], at[i] + 0.9)) * al
        y = 470 + i * 260
        f.text((80, y), lab, font("bold", 36), col, anchor="lm", alpha=clamp(p * 2))
        L = 900 * values[k] / vmax * ease_in_out(prog(t, at[i], at[i] + 0.9))
        if L > 4:
            f.rrect((80, y + 36, 80 + L, y + 136), 16, fill=mix(CREAM, col, al))
        f.text((80 + max(L, 0) + 22 if L < 700 else 80 + L - 24, y + 86), fmt(values[k]), font("anton", 64),
               CREAM if L >= 700 else col, anchor="rm" if L >= 700 else "lm", alpha=clamp(p),
               bg=col if L >= 700 else CREAM)
    credit(f, ease_out(prog(t, a0 + 0.6, a0 + 1.2)) * al)


def grams(f, t):
    bars(f, t, 10.4, 22.0, None, G, lambda v: f"{v:.0f} g", "FILAMENT", [10.7, 14.7, 17.7])
    p = ease_out(prog(t, 20.0, 20.6)) * fade(t, 10.4, 22.0)
    f.text((540, 1300), "LESS THAN HALF", font("anton", 80), TEAL, alpha=p)


def time_(f, t):
    bars(f, t, 22.0, 26.8, None, T, hm, "PRINT TIME", [22.3, 22.6, 22.9])
    p = ease_out(prog(t, 24.4, 25.0)) * fade(t, 22.0, 26.8)
    f.text((540, 1300), f"ABOUT {EXTRA_MIN} MIN LONGER", font("anton", 72), INK, alpha=p)


def rule(f, t):
    a0 = 26.8
    al = ease_out(prog(t, a0, a0 + 0.4))
    title(f, t, "SPEND IT ON WALLS", 300, a0 + 0.1, TEAL, 96)
    for k, (head, body, at, col) in enumerate([
            ("STRENGTH", "Is in the walls (Lesson 006).", 27.0, ORANGE),
            ("THE MIDDLE", "Mostly just costs plastic.", 31.8, INK),
            ("BEFORE YOU PRINT SOLID", "Slice it both ways.", 36.0, TEAL)]):
        p = ease_out(prog(t, at, at + 0.6))
        y = 480 + 250 * k
        f.rrect((90, y + 30 * (1 - p), 990, y + 200 + 30 * (1 - p)), 22, fill=mix(CREAM, CARD, p),
                outline=mix(CREAM, col, p), width=5)
        f.text((150, y + 68 + 30 * (1 - p)), head, font("anton", 58), col, anchor="lm", alpha=p)
        f.text((150, y + 145 + 30 * (1 - p)), body, font("semi", 48), INK, anchor="lm", alpha=p)
    f.text((540, 1300), "SEND THIS TO A MAKER", font("anton", 64), INK, alpha=ease_out(prog(t, 39.2, 39.8)) * al)
    credit(f, al)


DRAW = {"HOOK": hook, "SETUPS": setups, "GRAMS": grams, "TIME": time_, "RULE": rule}


def frame_at(t, clean=False):
    f = Frame()
    chrome(f)
    for name, a, b in SCENES:
        if a - 0.01 <= t < b + 0.4:
            DRAW[name](f, t)
    if not clean:
        caption(f, t)
    return f.out()


def render(out_dir, fps=30, clean=False, stills=()):
    out = Path(out_dir) / f"lesson008{'_clean' if clean else ''}.mp4"
    nf = int(round(DUR * fps))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                           "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                          stdin=subprocess.PIPE)
    for i in range(nf):
        t = i / fps
        im = frame_at(t, clean)
        ff.stdin.write(im.tobytes())
        for st in stills:
            if abs(t - st) < 0.5 / fps:
                im.save(Path(out_dir) / f"lesson008_{st:.1f}s.png")
    ff.stdin.close()
    ff.wait()
    print(out, f"{DUR} s, {nf} frames")


def script_md():
    lines = ["# Lesson 008 script: the narration, timed", "",
             "Generated from `VO` in `animate.py`; the numbers in it are read from `facts/slices.json`.",
             "A voice-over recorded to these lines drops onto the video with no retiming.", "",
             "| start | end | line | scene |", "|---|---|---|---|"]
    for a, b, s in VO:
        sc = next(n for n, x, y in SCENES if x <= a < y)
        lines.append(f"| {a:.1f} | {b:.1f} | {s} | {sc} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--stills", default="")
    ap.add_argument("--frame", type=float)
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.frame is not None:
        p = Path(a.out) / f"frame_{a.frame:.1f}.png"
        frame_at(a.frame, a.clean).save(p)
        print(p)
        return
    (HERE / "SCRIPT.md").write_text(script_md())
    render(a.out, a.fps, a.clean, [float(s) for s in a.stills.split(",") if s])


if __name__ == "__main__":
    main()
