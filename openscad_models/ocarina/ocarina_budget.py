#!/usr/bin/env python3
"""Ocarina (Scott's form A, 2026-11-12): the acoustic budget. Helmholtz resonator:

    f = c / (2 pi) * sqrt(S / V),   S = S_window + sum over open holes of A / (t + k r)

S is in metres (area over effective length), V the chamber volume, c the speed of sound
in warm breath. Two constants can't be known before a print:
  S_window   the voicing window's own term, set by the window, windway and labium;
  k          the end correction on a finger hole (literature 1.5-1.7 for thin walls).
The voicing test whistle measures both: three notes on a tuner (closed, one hole, both).

    python3 ocarina_budget.py                          priors, writes checks/budget.txt
    python3 ocarina_budget.py --coupon F0 F1 F2        a whistle's three measured notes (Hz)
"""
import argparse
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = 350.0            # m/s: air at about 30 C, breath-warmed
T = 2.4              # mm, wall (Benson's spec: >= 2.4)
S_W_PRIOR = 4.3      # mm: a prior for the window term; the coupon replaces it
K_PRIOR = 1.6
D_MAX, D_MIN = 10.5, 3.0   # finger pads close holes up to about 11 mm

# 12-hole Alto C: all closed is A4; the holes open one at a time (Pure Ocarinas'
# fingering page: subholes, right hand pinky to index, left ring to index, then the
# thumbs; the left pinky last)
NOTES = [("A4", 0), ("B4", 2), ("C5", 3), ("D5", 5), ("E5", 7), ("F5", 8), ("G5", 10), ("A5", 12),
         ("B5", 14), ("C6", 15), ("D6", 17), ("E6", 19), ("F6", 20)]
HOLES = ["subhole 1", "subhole 2", "right pinky", "right ring", "right middle", "right index",
         "left ring", "left middle", "left index", "left thumb", "right thumb", "left pinky"]

# the voicing whistle (voicing_coupon.scad): chamber and its two holes
COUPON_V = 24 * 14 * 16 + 24 * 14 * (7 / math.tan(math.radians(37))) / 2   # mm3: box plus gable roof
COUPON_HOLES = [5.0, 8.0]


TIP = math.radians(37)   # finger holes are teardrops: a circle of radius r, its roof 37 deg
                         # from upright (they go through upright walls on the printer)


def area(d):
    r = d / 2
    return r * r * (math.pi - (math.pi - 2 * TIP) / 2 + 1 / math.tan(TIP))


def a_over_l(d, k):
    return area(d) / (T + k * d / 2)


def solve_d(s, k):
    lo, hi = 0.5, 30.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if a_over_l(mid, k) < s else (lo, mid)
    return (lo + hi) / 2


def freq(s_mm, v_mm3):
    return C / (2 * math.pi) * math.sqrt((s_mm * 1e-3) / (v_mm3 * 1e-9))


def design(s_w, k):
    """Chamber volume for A4 with all closed, and each hole's diameter."""
    k2 = (2 * math.pi * 440.0 / C) ** 2          # 1/m^2
    v = (s_w * 1e-3) / k2 * 1e9                  # mm3
    rows, prev = [], s_w
    for (note, semis), hole in zip(NOTES[1:], HOLES):
        s = s_w * 2 ** (semis / 6)               # f^2 grows as S
        d = solve_d(s - prev, k)
        rows.append((hole, note, 440 * 2 ** (semis / 12), d))
        prev = s
    return v, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coupon", nargs=3, type=float, metavar=("F0", "F1", "F2"))
    a = ap.parse_args()
    s_w, k, src = S_W_PRIOR, K_PRIOR, "priors (not measured)"
    out = []
    if a.coupon:
        f0, f1, f2 = a.coupon
        k2 = lambda f: (2 * math.pi * f / C) ** 2
        s_w = k2(f0) * COUPON_V * 1e-9 * 1e3                  # mm
        s1 = k2(f1) * COUPON_V * 1e-9 * 1e3 - s_w             # hole 1's term
        lo, hi = 0.0, 5.0                                      # solve k from hole 1
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if a_over_l(COUPON_HOLES[0], mid) > s1 else (lo, mid)
        k = (lo + hi) / 2
        pred2 = freq(s_w + a_over_l(COUPON_HOLES[0], k) + a_over_l(COUPON_HOLES[1], k), COUPON_V)
        src = f"measured on the whistle: {f0:.0f}, {f1:.0f}, {f2:.0f} Hz"
        out.append(f"check: with both holes open the model predicts {pred2:.0f} Hz; measured {f2:.0f} "
                   f"({1200 * math.log2(f2 / pred2):+.0f} cents)")
    v, rows = design(s_w, k)
    head = [f"OCARINA ACOUSTIC BUDGET (Alto C, 12 holes, A4-F6), from {src}",
            f"window term {s_w:.2f} mm, hole end correction k {k:.2f}, wall {T} mm, c {C} m/s",
            f"chamber volume for A4 = 440 Hz with every hole closed: {v / 1000:.1f} cm3",
            "", f"{'hole':<14}{'opens':<6}{'target Hz':>10}{'diameter mm':>13}"]
    def chimney(d):
        # a hole under D_MIN is drawn at D_MIN instead, through a raised collar long
        # enough that its A / (length + k r) still gives the step it needs
        need, r = a_over_l(d, k), D_MIN / 2
        return area(D_MIN) / need - k * r
    body = [f"{h:<14}{n:<6}{f:>10.1f}{d:>13.2f}" + ("  <-- too big for a finger" if d > D_MAX else
            f"  <-- under {D_MIN}: draw {D_MIN} through a {chimney(d):.1f} mm deep hole (a {chimney(d) - T:.1f} mm collar)"
            if d < D_MIN else "") for h, n, f, d in rows]
    whistle = ["", "voicing whistle (voicing_coupon.scad), chamber %.1f cm3, holes 5.0 and 8.0 mm:" % (COUPON_V / 1000),
               "  predicted from these constants: closed %.0f Hz, one hole %.0f Hz, both %.0f Hz" % (
                   freq(s_w, COUPON_V), freq(s_w + a_over_l(5, k), COUPON_V),
                   freq(s_w + a_over_l(5, k) + a_over_l(8, k), COUPON_V))]
    note = ["", "TARGETS, NOT MEASURED: the full instrument is a tuning draft until a print is checked",
            "against a tuner. Hole sizes move by tenths of a millimetre after that check."]
    text = "\n".join(head + body + whistle + out + note)
    print(text)
    if not a.coupon:
        (HERE / "checks" / "budget.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
