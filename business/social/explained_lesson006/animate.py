"""Explained, Lesson 006 ("100% infill is a myth"): the three diagram scenes,
keyframed and eased, for Benson to cut to his voice-over (2026-11-18).

Benson's proposal (threads/2026-11-11_animation-quality.md on main): Claude takes
the animation polish lane for Explained, inside the locked identity:
  cream (246,240,226), ink (32,36,46), burnt orange (232,106,44), teal (20,110,96);
  Anton headlines, Chakra Petch body; a caption band carrying the VO line.
Benson keeps script, voice-over, captions, QC and posting. These clips replace
the diagrams in his cut only if Scott picks them (business/image_choices).

Scenes, each exactly the length of its section in the shipped VO (Ronan, 53.4 s):
  1  BEND   7.6-19.8 s  (12.2 s)  a beam sags; the skins take the stress, the
                                  centre none; a bone's hard shell and sponge
  2  TEST   20.4-33.9 s (13.5 s)  the same hook pulled to breaking: 2 walls at
                                  100% snaps at 64 kg (82 g); 5 walls at 20%
                                  holds 108 kg (54 g). CNC Kitchen's pull tests,
                                  via @3dmartos, credited on screen
  3  OURS   34.5-44.6 s (10.1 s)  our houses: 3 walls, 15% infill (Scott,
                                  2026-11-12), and a hollow room for the tealight

Scene 3 draws the wall the way our prints really are: the three perimeters and
the sparse infill are INSIDE the wall's thickness, and the room is air. (A grid
filling the whole room would say the room is printed with infill. It isn't.)

Every number on screen is the VO's own: CNC Kitchen's figures as Benson shipped
them, and ours from Scott. Nothing else is claimed.

    python3 animate.py OUT_DIR [--scene 1|2|3] [--clean] [--fps 30]

--clean leaves the caption band off, for Benson to lay his own captions over.
"""
import argparse
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H = 1080, 1920
SS = 2                                     # drawn at 2x, then downsampled: clean edges
CREAM = (246, 240, 226)
INK = (32, 36, 46)
ORANGE = (232, 106, 44)
TEAL = (20, 110, 96)
CARD = (252, 249, 242)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def clamp(t):
    return max(0.0, min(1.0, t))


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def ease_out(t):
    return 1 - (1 - clamp(t)) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_in(t):
    return clamp(t) ** 2.2


def ease_back(t):
    t = clamp(t)
    c1 = 1.4
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


_fonts = {}


def font(name, px):
    key = (name, px)
    if key not in _fonts:
        f = {"anton": "Anton-Regular.ttf", "reg": "ChakraPetch-Regular.ttf",
             "semi": "ChakraPetch-SemiBold.ttf", "bold": "ChakraPetch-Bold.ttf"}[name]
        _fonts[key] = ImageFont.truetype(str(HERE / "fonts" / f), int(px * SS))
    return _fonts[key]


class Frame:
    """One frame at SS x size; all coordinates given in 1080 x 1920 units."""

    def __init__(self):
        self.im = Image.new("RGB", (W * SS, H * SS), CREAM)
        self.d = ImageDraw.Draw(self.im)

    @staticmethod
    def s(v):
        return v * SS

    def P(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def text(self, xy, s, fnt, fill, anchor="mm", alpha=1.0, bg=CREAM):
        if alpha <= 0:
            return
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=fnt, fill=mix(bg, fill, alpha), anchor=anchor)

    def line(self, pts, fill, width, alpha=1.0, bg=CREAM):
        if alpha > 0 and len(pts) > 1:
            self.d.line(self.P(pts), fill=mix(bg, fill, alpha), width=int(width * SS), joint="curve")

    def poly(self, pts, fill, outline=None, width=0):
        self.d.polygon(self.P(pts), fill=fill, outline=outline, width=int(width * SS) if outline else 0)

    def rrect(self, box, r, fill=None, outline=None, width=0):
        self.d.rounded_rectangle([v * SS for v in box], radius=r * SS, fill=fill, outline=outline,
                                 width=int(width * SS))

    def circle(self, c, r, fill=None, outline=None, width=0):
        self.d.ellipse([(c[0] - r) * SS, (c[1] - r) * SS, (c[0] + r) * SS, (c[1] + r) * SS],
                       fill=fill, outline=outline, width=int(width * SS))

    def arrow(self, a, b, fill, width=8, head=26, alpha=1.0):
        if alpha <= 0:
            return
        col = mix(CREAM, fill, alpha)
        ax, ay = a
        bx, by = b
        L = math.hypot(bx - ax, by - ay) or 1
        ux, uy = (bx - ax) / L, (by - ay) / L
        base = (bx - ux * head, by - uy * head)
        self.d.line(self.P([a, base]), fill=col, width=int(width * SS))
        px, py = -uy, ux
        self.poly([(bx, by), (base[0] + px * head * 0.62, base[1] + py * head * 0.62),
                   (base[0] - px * head * 0.62, base[1] - py * head * 0.62)], fill=col)

    def out(self):
        return self.im.resize((W, H), Image.LANCZOS)


def chrome(f):
    f.text((60, 70), "3D PRINTING, EXPLAINED", font("semi", 30), INK, anchor="lm")
    f.rrect((826, 46, 1020, 96), 12, outline=ORANGE, width=3)
    f.text((923, 71), "LESSON 006", font("semi", 30), ORANGE)
    f.text((60, 1862), "ONBRANDCRAFTZ", font("semi", 24), INK, anchor="lm")


def wrap(text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if fnt.getlength(trial) <= maxw * SS:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def caption(f, t, lines):
    """The VO line on screen in the band (Benson's identity), cross-faded."""
    for a, b, s in lines:
        al = min(prog(t, a - 0.15, a + 0.1), 1 - prog(t, b + 0.1, b + 0.3)) if t < b + 0.3 else 0
        if al <= 0:
            continue
        fnt = font("reg", 38)
        ls = wrap(s, fnt, 840)
        h = 64 + 50 * (len(ls) - 1)
        y0 = 1300
        f.rrect((50, y0, 1030, y0 + h + 24), 18, fill=mix(CREAM, INK, al))
        for i, l in enumerate(ls):
            f.text((540, y0 + 12 + 32 + 50 * i), l, fnt, CREAM, alpha=al, bg=mix(CREAM, INK, al))


def headline(f, t, lines, t0=0.0):
    """Lines rise into place, one after the other."""
    for i, (s, col, y) in enumerate(lines):
        p = ease_out(prog(t, t0 + 0.12 * i, t0 + 0.12 * i + 0.55))
        f.text((540, y + 40 * (1 - p)), s, font("anton", 112), col, alpha=p)


# ------------------------------------------------------------------ scene 1: BEND
S1 = 12.2
S1_VO = [(0.0, 4.6, "When a part bends, the outside skin does almost all the work."),
         (4.9, 7.4, "The middle carries almost zero stress."),
         (7.6, 12.2, "Even bones are built this way — hard shell, light sponge inside.")]


def beam_y(x, layer, sag):
    """Top edge of a layer at x (layer 0 the top skin, 8 the bottom face)."""
    u = (x - 120) / 840
    return 640 + 15 * layer + sag * math.sin(math.pi * u)


def scene1(f, t):
    headline(f, t, [("WHEN IT BENDS,", INK, 215), ("THE SKIN WORKS", INK, 330)])
    sag = 78 * ease_in_out(prog(t, 1.1, 2.7))
    stress = ease_out(prog(t, 2.0, 3.4))
    xs = [120 + 840 * i / 60 for i in range(61)]
    paper = (238, 230, 212)
    for k in range(8):
        dist = abs(k - 3.5) / 3.5                   # 1 at either skin, 0 at the middle
        hue = ORANGE if k < 4 else TEAL
        fill = mix(paper, hue, 0.70 * stress * dist ** 1.6)
        top = [(x, beam_y(x, k, sag)) for x in xs]
        bot = [(x, beam_y(x, k + 1, sag)) for x in reversed(xs)]
        f.poly(top + bot, fill=fill)
    for k in range(9):
        f.line([(x, beam_y(x, k, sag)) for x in xs], INK, 4 if k in (0, 8) else 1.6,
               alpha=1.0 if k in (0, 8) else 0.55)
    f.line([(120, beam_y(120, 0, sag)), (120, beam_y(120, 8, sag))], INK, 4)
    f.line([(960, beam_y(960, 0, sag)), (960, beam_y(960, 8, sag))], INK, 4)
    # supports
    for x in (120, 960):
        yb = beam_y(x, 8, sag)
        f.poly([(x, yb), (x - 44, yb + 66), (x + 44, yb + 66)], fill=INK)
    # the load, dropping onto the middle
    pl = ease_back(prog(t, 0.55, 1.15))
    if pl > 0:
        tip = beam_y(540, 0, sag) - 14
        f.arrow((540, tip - 170 - 60 * (1 - pl)), (540, tip - 60 * (1 - pl)), ORANGE, width=11, head=40,
                alpha=min(1, pl))
    # the skins' stress: squeezed at the top, stretched at the bottom (gently pulsing)
    pa = ease_out(prog(t, 2.6, 3.4))
    if pa > 0:
        pulse = 1 + 0.08 * math.sin(2 * math.pi * (t - 2.6) / 1.4) * (t > 3.4)
        for x0, x1 in ((210, 300), (870, 780)):
            y = beam_y((x0 + x1) / 2, 0, sag) - 52
            m = (x0 + x1) / 2
            f.arrow((m - (m - x0) * pulse * pa, y), (m + (x1 - m) * pulse * pa, y), ORANGE, 8, 26, pa)
        for x0, x1 in ((300, 190), (780, 890)):
            y = beam_y((x0 + x1) / 2, 8, sag) + 52
            m = (x0 + x1) / 2
            f.arrow((m - (m - x0) * pulse * pa, y), (m + (x1 - m) * pulse * pa, y), TEAL, 8, 26, pa)
        f.text((200, 520), "SQUEEZED", font("bold", 32), ORANGE, alpha=pa)
        f.text((880, 520), "SQUEEZED", font("bold", 32), ORANGE, alpha=pa)
        f.text((200, 905), "STRETCHED", font("bold", 32), TEAL, alpha=pa)
        f.text((880, 905), "STRETCHED", font("bold", 32), TEAL, alpha=pa)
    # the middle: a dashed line drawn along the neutral axis, and its label
    pd = prog(t, 4.9, 5.9)
    if pd > 0:
        xend = 120 + 840 * ease_out(pd)
        x = 130
        while x < xend - 4:
            x2 = min(x + 22, xend)
            f.line([(x, beam_y(x, 4, sag)), (x2, beam_y(x2, 4, sag))], INK, 4)
            x += 36
        pt = ease_out(prog(t, 5.3, 6.1))
        f.text((540, 1000 + 20 * (1 - pt)), "CENTRE: ~0% STRESS", font("bold", 50), TEAL, alpha=pt)
    # a bone: hard shell, light sponge inside
    pb = ease_out(prog(t, 7.6, 8.5))
    if pb > 0:
        cx, cy, rx, ry = 540, 1150, 150 * (0.85 + 0.15 * pb), 74 * (0.85 + 0.15 * pb)
        shell = mix(CREAM, INK, pb)
        f.d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=mix(CREAM, (236, 226, 204), pb))
        # sponge: open cells, filling in from the middle out
        ps = prog(t, 8.3, 9.8)
        import random
        rnd = random.Random(6)
        for i in range(70):
            a = rnd.uniform(0, 2 * math.pi)
            r = math.sqrt(rnd.uniform(0, 1))
            if r > ps * 1.05:
                continue
            x, y = cx + (rx - 26) * r * math.cos(a), cy + (ry - 22) * r * math.sin(a)
            f.circle((x, y), rnd.uniform(5, 10), outline=mix(CREAM, TEAL, pb), width=3)
        f.d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], outline=shell, width=int(20 * SS))
        pl2 = ease_out(prog(t, 9.0, 9.8))
        f.text((cx - rx - 24, cy - 6), "HARD SHELL", font("bold", 34), ORANGE, anchor="rm", alpha=pl2)
        f.text((cx + rx + 24, cy - 6), "LIGHT SPONGE", font("bold", 34), TEAL, anchor="lm", alpha=pl2)


# ------------------------------------------------------------------ scene 2: TEST
S2 = 13.5
S2_VO = [(0.0, 2.1, "Same hook, pulled to breaking."),
         (2.4, 8.8, "Two walls at one hundred percent infill: snapped at sixty-four kilos, "
                    "and used eighty-two grams of plastic."),
         (9.1, 13.5, "Five walls at twenty percent: held one hundred and eight — on fifty-four grams.")]
LOAD_MAX = 120.0


def hook(f, cx, top, stretch, snapped_t, col):
    """A J-hook hanging from the fixture: shank, then the U. stretch opens the U
    as the load grows; after the snap the U falls away, turning."""
    shank_bot = top + 150
    f.line([(cx, top), (cx, shank_bot)], col, 26)
    f.circle((cx, top), 13, fill=col)
    r = 50
    ry = r * (1 + 0.25 * stretch)
    def u_pts(ox, oy, ang=0.0):
        # the U from the shank's foot round to the tip: theta 0 at the shank
        out = []
        for i in range(25):
            th = math.pi * i / 24
            x, y = r - r * math.cos(th), ry * math.sin(th)
            out.append((ox + x * math.cos(ang) - y * math.sin(ang), oy + x * math.sin(ang) + y * math.cos(ang)))
        tip = (2 * r, -34)
        out.append((ox + tip[0] * math.cos(ang) - tip[1] * math.sin(ang), oy + tip[0] * math.sin(ang) + tip[1] * math.cos(ang)))
        return out

    if snapped_t is None:
        pts = u_pts(cx, shank_bot)
        f.line(pts, col, 26, bg=CARD)
        for q in (pts[0], pts[-1]):
            f.circle(q, 13, fill=col)
        return
    # snapped: the shank ends ragged; the U falls, turns and fades
    f.line([(cx - 13, shank_bot), (cx - 4, shank_bot + 10), (cx + 5, shank_bot + 2), (cx + 13, shank_bot + 12)],
           ORANGE, 4)
    fall = snapped_t
    al = 1 - clamp(fall / 0.9)
    if al <= 0:
        return
    pts = u_pts(cx + 40 * fall, shank_bot + 18 + 400 * fall ** 2, 1.6 * fall)
    f.line(pts, col, 26, alpha=al, bg=CARD)


def section(f, cx, cy, walls, infill, p, col):
    """The hook's cross-section, 120 mm-ish square: `walls` perimeter rings and
    `infill` (0-1) inside, each built up as p goes 0 -> 1."""
    s = 64
    f.rrect((cx - s, cy - s, cx + s, cy + s), 10, fill=CARD, outline=INK, width=3)
    nring = walls * clamp(p * 1.6)
    for i in range(int(math.ceil(nring))):
        o = 8 + 9 * i
        al = clamp(nring - i)
        f.rrect((cx - s + o, cy - s + o, cx + s - o, cy + s - o), max(2, 10 - o / 3), outline=mix(CARD, col, al), width=5)
    pi_ = clamp(p * 1.6 - 0.6)
    if pi_ > 0:
        o = 8 + 9 * walls + 2
        x0, y0, x1, y1 = cx - s + o, cy - s + o, cx + s - o, cy + s - o
        if infill >= 0.99:
            f.rrect((x0, y0, x1, y1), 3, fill=mix(CARD, col, 0.85 * pi_))
        else:
            # a sparse grid: lines spaced for the density, drawn in diagonally
            gap = 7 / infill
            n = int((x1 - x0) / gap)
            for k in range(1, n + 1):
                a = clamp(pi_ * (n + 2) - k)
                x = x0 + k * gap
                if x < x1:
                    f.line([(x, y0), (x, y1)], col, 3, alpha=a, bg=CARD)
                y = y0 + k * gap
                if y < y1:
                    f.line([(x0, y), (x1, y)], col, 3, alpha=a, bg=CARD)


def card(f, t, cx, walls, infill, build, pull, peak, end_txt, grams, snap):
    x0, x1 = cx - 205, cx + 205
    rise = ease_out(prog(t, 0.3 + (0.15 if cx > 540 else 0), 1.1 + (0.15 if cx > 540 else 0)))
    if rise <= 0:
        return
    oy = 60 * (1 - rise)
    f.rrect((x0, 400 + oy, x1, 1185 + oy), 26, fill=mix(CREAM, CARD, rise), outline=mix(CREAM, INK, rise), width=3)
    f.line([(cx - 80, 440 + oy), (cx + 80, 440 + oy)], INK, 9, alpha=rise, bg=CARD)
    # the load: rises with an accelerating count, then snaps or holds
    a, b = pull
    lp = prog(t, a, b)
    load = peak * ease_in(lp)
    snapped_t = (t - b) / 1.1 if snap and t >= b else None
    stretch = load / LOAD_MAX
    hook(f, cx, 460 + oy, stretch, snapped_t, INK)
    # status
    if t >= b:
        ps = ease_back(prog(t, b, b + 0.35))
        col = ORANGE if snap else TEAL
        word = "SNAPPED" if snap else "HELD"
        fnt = font("bold", int(40 * (0.7 + 0.3 * ps)))
        f.text((cx, 708 + oy), word, fnt, col, alpha=clamp(ps), bg=CARD)
    section(f, cx, 800 + oy, walls, infill, prog(t, *build), INK)
    # counter and bar
    col = INK if t < b else (ORANGE if snap else TEAL)
    shake = 6 * math.sin(60 * t) * (1 - clamp((t - b) / 0.3)) if snap and t >= b else 0
    f.text((cx + shake, 945 + oy), f"{int(round(load))} kg", font("anton", 104), col, alpha=rise, bg=CARD)
    f.rrect((cx - 150, 1010 + oy, cx + 150, 1042 + oy), 16, outline=mix(CARD, INK, rise), width=3)
    fw = 300 * load / LOAD_MAX
    if fw > 8:
        f.rrect((cx - 150 + 4, 1014 + oy, cx - 150 + 4 + fw - 8, 1038 + oy), 12, fill=col)
    f.text((cx, 1078 + oy), f"{walls} WALLS", font("bold", 36), INK, alpha=rise, bg=CARD)
    f.text((cx, 1118 + oy), f"{int(infill * 100)}% INFILL", font("reg", 34), INK, alpha=rise, bg=CARD)
    pg = ease_out(prog(t, *grams))
    f.text((cx, 1156 + oy), end_txt, font("semi", 30), INK, alpha=pg * 0.85, bg=CARD)


def scene2(f, t):
    headline(f, t, [("SAME HOOK.", INK, 205), ("PULLED TO BREAKING.", INK, 318)])
    card(f, t, 300, 2, 1.00, (2.4, 3.6), (3.0, 7.0), 64, "82 g of plastic", (7.6, 8.2), True)
    card(f, t, 780, 5, 0.20, (9.1, 10.3), (9.7, 12.6), 108, "54 g of plastic", (12.8, 13.3), False)
    pc = ease_out(prog(t, 1.0, 1.6))
    f.text((540, 1238), "CNC Kitchen pull tests, via @3dmartos", font("reg", 30), INK, alpha=0.75 * pc)


# ------------------------------------------------------------------ scene 3: OURS
S3 = 10.1
S3_VO = [(0.0, 2.4, "It's why our houses are hollow shells."),
         (2.7, 6.7, "Three walls, fifteen percent infill, mostly air inside."),
         (7.0, 10.1, "Strong where it works. Air where it doesn't.")]
HX0, HX1, HY0, HY1 = 250, 830, 650, 1110        # the house's outside
WALL = 64                                       # drawn wall thickness (exaggerated to read)


def partial(pts, p):
    """The first fraction p (by length) of a polyline."""
    if p >= 1:
        return pts
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    goal, out = sum(seg) * p, [pts[0]]
    for (a, b), L in zip(zip(pts, pts[1:]), seg):
        if goal <= L:
            r = goal / L if L else 0
            out.append((a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r))
            return out
        out.append(b)
        goal -= L
    return out


def scene3(f, t):
    headline(f, t, [("OUR HOUSES?", INK, 215), ("HOLLOW SHELLS.", ORANGE, 330)])
    po = ease_in_out(prog(t, 0.3, 1.7))
    # the wall band, filled once the walls go on
    pw = prog(t, 2.7, 4.2)
    glow = ease_out(prog(t, 7.0, 8.2))
    # the room's air, and the tealight's glow in it
    ix0, ix1, iy0, iy1 = HX0 + WALL, HX1 - WALL, HY0 + WALL, HY1 - WALL
    if glow > 0:
        cx, cy = 540, iy1 - 60
        for k in range(16, 0, -1):
            r = 22 * k
            f.circle((cx, cy), r, fill=mix(CREAM, (250, 214, 160), glow * (1 - k / 17) ** 1.3))
    # walls: an outline that draws itself, then 3 perimeters and sparse infill
    outline = [(HX0, HY1), (HX0, HY0), (HX1, HY0), (HX1, HY1), (HX0, HY1)]
    roof = [(HX0 - 50, HY0), (540, HY0 - 210), (HX1 + 50, HY0), (HX0 - 50, HY0)]
    f.line(partial(roof, po), INK, 8)
    f.line(partial(outline, po), INK, 6)
    if po >= 1:
        f.line([(ix0, iy1), (ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)], INK, 4, alpha=prog(t, 1.7, 2.1))
    for i in range(3):
        a = ease_out(prog(t, 2.7 + 0.45 * i, 3.1 + 0.45 * i))
        if a <= 0:
            continue
        o = 9 + 11 * i
        f.line([(HX0 + o, HY1 - o), (HX0 + o, HY0 + o), (HX1 - o, HY0 + o), (HX1 - o, HY1 - o), (HX0 + o, HY1 - o)],
               INK, 6, alpha=a)
    pi_ = prog(t, 4.3, 5.4)
    if pi_ > 0:
        # 15% infill: a sparse grid inside the wall, between the perimeters and the room
        o0, o1 = 9 + 11 * 2 + 9, WALL - 4
        gap = 26
        bands = [((HX0 + o0, HY0 + o0), (HX0 + o1, HY1 - o0)), ((HX1 - o1, HY0 + o0), (HX1 - o0, HY1 - o0)),
                 ((HX0 + o0, HY0 + o0), (HX1 - o0, HY0 + o1)), ((HX0 + o0, HY1 - o1), (HX1 - o0, HY1 - o0))]
        for (x0, y0), (x1, y1) in bands:
            n = int(max(x1 - x0, y1 - y0) / gap)
            for k in range(n + 1):
                a = clamp(pi_ * (n + 3) - k)
                if x1 - x0 > y1 - y0:
                    x = x0 + k * gap
                    f.line([(x, y0), (min(x + (y1 - y0), x1), y1)], TEAL, 3, alpha=a)
                    f.line([(min(x + (y1 - y0), x1), y0), (x, y1)], TEAL, 3, alpha=a)
                else:
                    y = y0 + k * gap
                    f.line([(x0, y), (x1, min(y + (x1 - x0), y1))], TEAL, 3, alpha=a)
                    f.line([(x0, min(y + (x1 - x0), y1)), (x1, y)], TEAL, 3, alpha=a)
    # the tealight, lit
    pt = ease_out(prog(t, 1.9, 2.5))
    if pt > 0:
        cx, by = 540, iy1 - 6
        f.rrect((cx - 46, by - 40, cx + 46, by), 8, fill=mix(CREAM, INK, pt))
        flick = 1 + 0.06 * math.sin(13 * t) + 0.04 * math.sin(29 * t)
        fh = 34 * flick * max(glow, 0.55 * pt)
        f.poly([(cx, by - 44 - fh), (cx - 11, by - 50), (cx, by - 42), (cx + 11, by - 50)], fill=mix(CREAM, ORANGE, pt))
        f.circle((cx, by - 52), 11, fill=mix(CREAM, ORANGE, pt))
    # labels
    l1 = ease_out(prog(t, 3.5, 4.1))
    f.arrow((300, 1196), (HX0 + 20, HY1 - 60), INK, 4, 18, l1)
    f.text((300, 1220), "3 WALLS", font("bold", 46), INK, alpha=l1)
    l2 = ease_out(prog(t, 4.6, 5.2))
    f.arrow((780, 1196), (HX1 - 40, HY1 - 60), TEAL, 4, 18, l2)
    f.text((780, 1220), "15% INFILL", font("bold", 46), TEAL, alpha=l2)
    l3 = ease_out(prog(t, 5.5, 6.2))
    f.text((540, (iy0 + iy1) / 2 - 30), "AIR", font("anton", 120), mix(CREAM, INK, 0.18), alpha=l3)
    f.text((540, 1268), "MOSTLY AIR INSIDE", font("semi", 38), INK, alpha=l3 * (1 - prog(t, 6.8, 7.2)))
    # strong where it works: the walls pick out in orange, then the air in teal
    sw = ease_out(prog(t, 7.2, 7.8)) * (1 - 0.35 * prog(t, 8.6, 9.2))   # after MOSTLY AIR INSIDE has gone
    if sw > 0:
        f.line(outline, ORANGE, 10, alpha=sw)
        f.line([(ix0, iy1), (ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)], ORANGE, 6, alpha=sw)
        f.text((540, 1268), "STRONG WHERE IT WORKS.", font("bold", 40), ORANGE, alpha=sw * (1 - prog(t, 8.5, 8.8)))
    sa = ease_out(prog(t, 8.7, 9.2))
    f.text((540, 1268), "AIR WHERE IT DOESN'T.", font("bold", 40), TEAL, alpha=sa)


SCENES = {1: ("scene1_beam", S1, scene1, S1_VO), 2: ("scene2_hookpull", S2, scene2, S2_VO),
          3: ("scene3_hollow", S3, scene3, S3_VO)}


def render(n, out_dir, fps=30, clean=False, stills=()):
    name, dur, fn, vo = SCENES[n]
    out = Path(out_dir) / f"{name}{'_clean' if clean else ''}.mp4"
    nf = int(round(dur * fps))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                           "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                          stdin=subprocess.PIPE)
    for i in range(nf):
        t = i / fps
        f = Frame()
        chrome(f)
        fn(f, t)
        if not clean:
            caption(f, t, vo)
        im = f.out()
        ff.stdin.write(im.tobytes())
        for st in stills:
            if abs(t - st) < 0.5 / fps:
                im.save(Path(out_dir) / f"{name}_{st:.1f}s.png")
    ff.stdin.close()
    ff.wait()
    print(out, f"{dur} s, {nf} frames")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--scene", type=int, choices=(1, 2, 3))
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--stills", default="", help="comma-separated times (s) to also save as PNG")
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    st = [float(s) for s in a.stills.split(",") if s]
    for n in ([a.scene] if a.scene else [1, 2, 3]):
        render(n, a.out, a.fps, a.clean, st)


if __name__ == "__main__":
    main()
