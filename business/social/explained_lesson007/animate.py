"""Explained, Lesson 007 ("The 0.2 mm rule"): a complete animated lesson, 9:16,
built in the Lesson 006 identity Scott picked on 2026-11-19 (2026-11-20).

Every number on screen is from our own detail test coupon
(openscad_models/detail_calibration/detail_coupon.scad), re-sliced at 0.20 mm layers
on 2026-11-20 and measured from the toolpath by measure_coupon.py. The result is
copied into facts/measured_0.20.json. They are slicer numbers (what the printer is
told to lay down), and the screen says so. Ridges are left out on purpose: their
measured heights in the re-slice did not reproduce the standard's table cleanly.

The caption band carries the narration, so the lesson stands on its own silent. The
same lines, with their times, are in SCRIPT.md for Benson's voice-over.

    python3 animate.py OUT_DIR [--clean] [--stills 3,14,26,38,46]
"""
import argparse
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "explained_lesson006"))
from animate import (CREAM, INK, ORANGE, TEAL, CARD, W, H, Frame, mix, clamp, prog,  # noqa: E402
                     ease_out, ease_in_out, ease_back, font, wrap)

DUR = 50.0
LESSON = "LESSON 007"
CREDIT = "MEASURED ON OUR TEST COUPON'S SLICED TOOLPATH, 0.20 MM LAYERS"

# (start, end, line): the narration. SCRIPT.md is generated from this list.
VO = [
    (0.3, 3.3, "Draw a 0.3 mm groove in your model."),
    (3.5, 6.4, "Your slicer turns it into 0.4. Here's why."),
    (6.8, 10.2, "A printer builds in layers. Ours are 0.2 mm thick."),
    (10.4, 12.6, "So a 1 mm dome isn't a dome."),
    (12.8, 17.2, "It's five stacked layers."),
    (17.8, 21.2, "Anything that runs level has to snap to a layer."),
    (21.4, 24.8, "A 0.3 mm groove takes two layers: 0.4."),
    (25.0, 29.6, "A 0.1 mm groove takes a full layer. Twice the size you drew."),
    (30.2, 32.8, "Lines that run up the face are different."),
    (33.0, 35.8, "The nozzle places those sideways, not in steps."),
    (36.0, 40.8, "Every depth we tested, 0.1 to 1.0 mm, came out within a hundredth."),
    (41.2, 44.0, "Fine detail: run it up the face."),
    (44.2, 47.0, "Heights: put them on the 0.2 mm grid."),
    (47.2, 50.0, "Send this to the maker whose details print wrong."),
]

SCENES = [("HOOK", 0.0, 6.6), ("LAYERS", 6.6, 17.6), ("SNAP", 17.6, 30.0), ("UP", 30.0, 41.0),
          ("RULE", 41.0, DUR)]


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
    """1 inside the scene, easing in at a and out at b."""
    return min(ease_out(prog(t, a, a + d)), 1 - prog(t, b - d, b))


def title(f, t, s, y, a0, col=INK, px=96):
    p = ease_out(prog(t, a0, a0 + 0.55))
    f.text((540, y + 36 * (1 - p)), s, font("anton", px), col, alpha=p)


def credit(f, al):
    f.text((540, 1440), CREDIT, font("semi", 24), mix(CREAM, INK, 0.7), alpha=al)


def dashed(f, pts, col, width, dash=16, gap=12, alpha=1.0):
    """A dashed polyline: what the model asked for, as against what prints."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L // (dash + gap)) + 1)
        for k in range(n):
            s = k * (dash + gap) / L
            e = min(1.0, (k * (dash + gap) + dash) / L)
            if s >= 1:
                break
            f.line([(x0 + (x1 - x0) * s, y0 + (y1 - y0) * s), (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)],
                   col, width, alpha=alpha)


def beads(f, x_back, fronts, y_top, lh, col, alpha=1.0, outline=INK):
    """Layers seen in section, top layer first: a run from x_back to its front,
    rounded where the bead ends, as a real bead does."""
    c = mix(CREAM, col, alpha)
    o = mix(CREAM, outline, alpha)
    for i, xf in enumerate(fronts):
        y0 = y_top + i * lh
        f.rrect((x_back, y0 + 2, xf, y0 + lh - 2), (lh - 4) / 2, fill=c, outline=o, width=2)


# ------------------------------------------------------------------ HOOK
def hook(f, t):
    al = fade(t, 0.0, 6.6)
    title(f, t, "DRAW 0.3 MM.", 330, 0.25)
    title(f, t, "GET 0.4.", 450, 3.5, ORANGE)
    # a wall in section with a level groove: drawn 0.3 (dashed), printed 0.4
    lh, n, xb, fx, d = 100, 6, 160, 760, 170
    y_top = 640
    snap = ease_in_out(prog(t, 3.6, 4.6))
    fronts = [fx] * n
    for i in (2, 3):                        # the two layers the groove takes
        fronts[i] = fx - d * snap
    beads(f, xb, fronts, y_top, lh, CARD, alpha=al)
    z0 = y_top + 2 * lh                     # drawn groove: 0.3 mm = 1.5 layers, from a layer line
    dashed(f, [(fx + 40, z0), (fx - d, z0), (fx - d, z0 + 1.5 * lh), (fx + 40, z0 + 1.5 * lh)], ORANGE, 6,
           alpha=al * ease_out(prog(t, 1.0, 1.6)))
    lab = ease_out(prog(t, 1.4, 2.0)) * al
    f.text((fx + 70, z0 + 0.75 * lh), "0.3", font("bold", 50), ORANGE, anchor="lm", alpha=lab)
    lab2 = ease_out(prog(t, 4.4, 4.9)) * al
    bx = fx + 190                           # the printed size, bracketed clear of the beads
    f.line([(bx, z0), (bx, z0 + 2 * lh)], INK, 5, alpha=lab2)
    f.line([(bx - 14, z0), (bx + 14, z0)], INK, 5, alpha=lab2)
    f.line([(bx - 14, z0 + 2 * lh), (bx + 14, z0 + 2 * lh)], INK, 5, alpha=lab2)
    f.text((bx + 30, z0 + lh), "0.4", font("bold", 50), INK, anchor="lm", alpha=lab2)
    f.text((540, 1330), "THE 0.2 MM RULE", font("anton", 80), TEAL, alpha=ease_out(prog(t, 4.8, 5.4)) * al)


# ------------------------------------------------------------------ LAYERS
def layers(f, t):
    a0, a1 = 6.6, 17.6
    al = fade(t, a0, a1)
    title(f, t, "LAYERS, 0.2 MM", 250, a0 + 0.2, INK, 88)
    # a 1.0 mm dome on a wall face, in section: 1 mm = 600 px, a layer = 120 px
    S = 600
    r = 0.5 * S
    lh = 0.2 * S
    fx, cy = 380, 860
    xb = 110
    top = cy - 2.5 * lh
    # the wall: five layers, then the dome's layers stepping out
    show = ease_out(prog(t, a0 + 0.4, a0 + 1.0)) * al
    zc = [(-0.4 + 0.2 * i) for i in range(5)]          # layer middles, mm from the dome's centre
    grow = [ease_out(prog(t, 12.9 + 0.35 * i, 13.4 + 0.35 * i)) for i in range(5)]
    fronts = [fx + S * math.sqrt(max(0.0, 0.25 - z * z)) * g for z, g in zip(zc, grow)]
    beads(f, xb, [fx] * 5, top, lh, CARD, alpha=show)
    for i, (xf, g) in enumerate(zip(fronts, grow)):
        if g > 0:
            y0 = top + i * lh
            f.rrect((fx - 60, y0 + 2, xf, y0 + lh - 2), (lh - 4) / 2, fill=mix(CREAM, ORANGE, g * al),
                    outline=mix(CREAM, INK, g * al), width=2)
    # the dome as drawn
    dl = ease_out(prog(t, 10.4, 11.3)) * al
    if dl > 0:
        pts = [(fx + r * math.cos(a), cy - r * math.sin(a)) for a in
               [math.pi / 2 - math.pi * k / 48 for k in range(49)]]
        n = max(2, int(len(pts) * dl))
        dashed(f, pts[:n], TEAL, 6, 14, 10)
    f.text((fx + r + 40, cy - 30), "1 MM DOME", font("bold", 44), TEAL, anchor="lm", alpha=dl)
    f.text((fx + r + 40, cy + 30), "AS DRAWN", font("semi", 34), TEAL, anchor="lm", alpha=dl)
    st = ease_out(prog(t, 14.8, 15.4)) * al
    f.text((540, 1300), "AS PRINTED: 5 LAYERS", font("anton", 76), ORANGE, alpha=st)


# ------------------------------------------------------------------ SNAP
def snap(f, t):
    a0, a1 = 17.6, 30.0
    al = fade(t, a0, a1)
    title(f, t, "LEVEL LINES SNAP", 250, a0 + 0.2, INK, 88)
    lh, n, xb, fx, d = 90, 9, 140, 620, 150
    y_top = 380
    # layer grid lines carry on past the face, so the snapping is visible
    grid = ease_out(prog(t, a0 + 0.5, a0 + 1.2)) * al
    for i in range(n + 1):
        y = y_top + i * lh
        dashed(f, [(fx, y), (1000, y)], mix(CREAM, INK, 0.35), 2, 8, 10, alpha=grid)
    # groove A: 0.3 drawn -> 2 layers (layers 1-2); groove B: 0.1 drawn -> 1 layer (layer 6)
    sA = ease_in_out(prog(t, 22.6, 23.5))
    sB = ease_in_out(prog(t, 26.6, 27.5))
    fronts = [fx] * n
    fronts[1] = fronts[2] = fx - d * sA
    fronts[6] = fx - d * sB
    beads(f, xb, fronts, y_top, lh, CARD, alpha=al)
    zA = y_top + 1 * lh
    zB = y_top + 6 * lh
    dA = ease_out(prog(t, 21.4, 22.0)) * al
    dashed(f, [(fx + 30, zA), (fx - d, zA), (fx - d, zA + 1.5 * lh), (fx + 30, zA + 1.5 * lh)], ORANGE, 6,
           alpha=dA)
    f.text((fx + 60, zA + 0.75 * lh), "DRAWN 0.3", font("bold", 40), ORANGE, anchor="lm", alpha=dA)
    pA = ease_out(prog(t, 23.4, 23.9)) * al
    f.text((fx + 60, zA + 0.75 * lh + 56), "PRINTS 0.4", font("bold", 40), INK, anchor="lm", alpha=pA)
    dB = ease_out(prog(t, 25.0, 25.6)) * al
    dashed(f, [(fx + 30, zB), (fx - d, zB), (fx - d, zB + 0.5 * lh), (fx + 30, zB + 0.5 * lh)], ORANGE, 6,
           alpha=dB)
    f.text((fx + 60, zB + 0.25 * lh), "DRAWN 0.1", font("bold", 40), ORANGE, anchor="lm", alpha=dB)
    pB = ease_out(prog(t, 27.4, 27.9)) * al
    f.text((fx + 60, zB + 0.25 * lh + 56), "PRINTS 0.2", font("bold", 40), INK, anchor="lm", alpha=pB)
    f.text((540, 1300), "ROUNDED TO WHOLE LAYERS", font("anton", 66), TEAL,
           alpha=ease_out(prog(t, 28.2, 28.8)) * al)
    credit(f, ease_out(prog(t, a0 + 1.0, a0 + 1.6)) * al)


# ------------------------------------------------------------------ UP
DEPTHS = [0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0]
PRINTED = [0.10, 0.19, 0.30, 0.39, 0.60, 0.79, 1.00]     # facts/measured_0.20.json


def check(f, c, s, col, alpha):
    x, y = c
    f.line([(x - s, y), (x - s * 0.3, y + s * 0.7), (x + s, y - s * 0.8)], col, 7, alpha=alpha)


def up(f, t):
    a0, a1 = 30.0, 41.0
    al = fade(t, a0, a1)
    title(f, t, "UPRIGHT LINES DON'T", 250, a0 + 0.2, INK, 88)
    f.text((540, 340), "LOOKING DOWN ON ONE LAYER", font("semi", 34), mix(CREAM, INK, 0.7),
           alpha=ease_out(prog(t, a0 + 0.6, a0 + 1.1)) * al)
    S = 150                                  # 1 mm = 150 px
    fy, band = 640, 330
    w = 0.4 * S
    xs = [130 + 135 * i for i in range(7)]
    # the wall, seen from above, with seven upright grooves cut into its face
    path = [(70, fy)]
    for x, dpt in zip(xs, DEPTHS):
        path += [(x - w / 2, fy), (x - w / 2, fy + dpt * S), (x + w / 2, fy + dpt * S), (x + w / 2, fy)]
    path += [(1010, fy)]
    body = path + [(1010, fy + band), (70, fy + band)]
    show = ease_out(prog(t, a0 + 0.4, a0 + 1.0)) * al
    f.poly(body, fill=mix(CREAM, CARD, show), outline=mix(CREAM, INK, show), width=3)
    # the outer-wall bead runs along the face, into every groove
    pr = ease_in_out(prog(t, 33.0, 35.8))
    if pr > 0:
        seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])]
        goal, acc, part = sum(seg) * pr, 0.0, [path[0]]
        for (a, b), L in zip(zip(path, path[1:]), seg):
            if acc + L <= goal:
                part.append(b)
                acc += L
            else:
                u = (goal - acc) / L
                part.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
                break
        inset = 0.2 * S                      # the bead's centreline sits half a bead in
        f.line([(x, y + inset) for x, y in part], ORANGE, int(0.4 * S * 0.8), alpha=al)
    for i, (x, dpt, got) in enumerate(zip(xs, DEPTHS, PRINTED)):
        la = ease_out(prog(t, a0 + 1.0 + 0.1 * i, a0 + 1.5 + 0.1 * i)) * al
        f.text((x, fy - 50), f"{dpt:.1f}", font("bold", 40), INK, alpha=la)
        ca = ease_back(prog(t, 36.6 + 0.25 * i, 37.1 + 0.25 * i)) * al
        f.text((x, fy + band + 50), f"{got:.2f}", font("bold", 36), TEAL, alpha=clamp(ca))
        check(f, (x, fy + band + 115), 18, TEAL, clamp(ca))
    f.text((40, fy - 50), "MM", font("semi", 28), INK, anchor="lm",
           alpha=ease_out(prog(t, a0 + 1.0, a0 + 1.5)) * al)
    f.text((540, 1300), "WITHIN 0.01 MM", font("anton", 80), TEAL, alpha=ease_out(prog(t, 38.9, 39.5)) * al)
    credit(f, ease_out(prog(t, a0 + 1.0, a0 + 1.6)) * al)


# ------------------------------------------------------------------ RULE
def rule(f, t):
    a0 = 41.0
    al = ease_out(prog(t, a0, a0 + 0.4))
    title(f, t, "THE 0.2 MM RULE", 300, a0 + 0.1, TEAL, 104)
    for k, (head, body, at, col) in enumerate([
            ("FINE DETAIL", "Run it up the face.", 41.2, ORANGE),
            ("HEIGHTS", "On the 0.2 mm grid.", 44.2, INK)]):
        p = ease_out(prog(t, at, at + 0.6))
        y = 560 + 300 * k
        f.rrect((90, y + 30 * (1 - p), 990, y + 230 + 30 * (1 - p)), 22, fill=mix(CREAM, CARD, p),
                outline=mix(CREAM, col, p), width=5)
        f.text((150, y + 80 + 30 * (1 - p)), head, font("anton", 64), col, anchor="lm", alpha=p)
        f.text((150, y + 165 + 30 * (1 - p)), body, font("semi", 54), INK, anchor="lm", alpha=p)
    f.text((540, 1250), "SEND THIS TO A MAKER", font("anton", 64), INK, alpha=ease_out(prog(t, 47.2, 47.8)) * al)
    credit(f, al)


DRAW = {"HOOK": hook, "LAYERS": layers, "SNAP": snap, "UP": up, "RULE": rule}


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
    out = Path(out_dir) / f"lesson007{'_clean' if clean else ''}.mp4"
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
                im.save(Path(out_dir) / f"lesson007_{st:.1f}s.png")
    ff.stdin.close()
    ff.wait()
    print(out, f"{DUR} s, {nf} frames")


def script_md():
    lines = ["# Lesson 007 script: the narration, timed", "",
             "Generated from `VO` in `animate.py`. These are the caption-band lines; a voice-over",
             "recorded to them drops onto the video with no retiming.", "",
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
    ap.add_argument("--frame", type=float, help="write one PNG at this time and stop")
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
