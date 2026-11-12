#!/usr/bin/env python3
"""The otter's joint, by the numbers, before it is modelled (handbook section 7).

Scott picked 7A, a print-in-place articulated otter that curls on its back holding
a shell (2026-11-11). It moves, so it follows the mechanism process: requirement,
concept, hand calculations, failure modes, then a coupon he prints before the otter
is built around the joint.

The joint is a vertical "spinning-top" pin in a C-ring. Segment n ends in an upright
pin, narrow at its foot and head and widest in the middle; segment n+1 wraps it in a
C-shaped ring whose bore follows the pin with a gap all round. Every slope is 37 deg
from upright and both parts rise from the plate, so nothing bridges and no gap hangs
over air. The bulge holds the pin in vertically; the C's opening, narrower than the
pin's waist, holds it in sideways; a fin through the opening joins the pin to its
segment and stops the swing at the opening's sides.

    python3 joint_budget.py            (prints the budget; writes checks/budget.txt)
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from mechanism_budget import PROCESS, engagement, stack  # noqa: E402

# ---- requirement ----
SWING = 15.0          # deg each way per joint; 8 joints curl the otter about 120 deg
LOAD_N = 20.0         # a firm tug on one segment, by hand
LEVER = 15.0          # mm from the pin to where it is pulled
PLA_XY_MPA = 45.0     # printed PLA along the beads, design value (handbook section 3: 45-60)
SAFETY = 2.0

# ---- the joint ----
H = 10.0              # joint height, 50 layers
SLOPE = 37.0          # deg from upright, every cone (DETAIL_STANDARD rule 7)
BULGE = 1.5           # radial: the pin's middle over its waist
GAP = 0.35            # normal gap, pin to bore (the coupon tries 0.30 / 0.35 / 0.45)
WALL = 2.0            # ring wall outside the bore at the bulge
FIN = 3.2             # fin width across the swing (Y); 2.8 failed bending (23 MPa vs 22.5)
ENGAGE = 3.0          # the rule: engagement >= 3 x RSS and > worst case
WAIST_MIN = 4.0       # one waist for every variant, so the coupon tests the gap alone; retention then about twice the 3 x RSS rule


def opening(r_a, gap=GAP):
    """The C's slot is a wedge with radial sides (2026-11-11). Its half-angle lets the fin
    swing SWING each way: the fin's edge sits furthest round at the bore's waist, where it
    leaves the pin, at SWING + asin((FIN/2 + gap) / (r_a + gap)). Radial sides meet the bore
    square-on; the first coupon's parallel-sided slot met it at 39 deg and left a thin
    wedge at each lip (product gate: min wall 0.86)."""
    r_out = r_a + BULGE + gap + WALL
    theta = SWING + math.degrees(math.asin((FIN / 2 + gap) / (r_a + gap)))
    half_chord = (r_a + gap) * math.sin(math.radians(theta))     # the opening at the waist
    return theta, half_chord, r_out


def solve_waist(gap=GAP):
    """The smallest pin waist radius whose sideways retention (waist radius minus the
    opening's half-chord at the waist) meets the engagement rule."""
    side = [("pin radius, XY wall", PROCESS["xy_wall"]),
            ("slot edge, XY wall", PROCESS["xy_wall"]),
            ("slot edge, other side", PROCESS["xy_wall"])]
    need = engagement(0.0, side, ENGAGE)["min_depth"]
    r = 2.5
    while True:
        theta, hc, r_out = opening(r, gap)
        if r - hc >= need:
            return r, side
        r += 0.05


def report(gap=GAP):
    out = []
    r_a, side = solve_waist(gap)
    r_a = max(math.ceil(r_a * 10) / 10, WAIST_MIN)      # round up to 0.1; never thinner than WAIST_MIN
    theta, hc, r_out = opening(r_a, gap)
    r_b = r_a + BULGE
    cone_h = BULGE / math.tan(math.radians(SLOPE))
    g_cone = gap / math.cos(math.radians(SLOPE))          # horizontal gap across a cone
    out.append(f"gap {gap:.2f} normal ({g_cone:.2f} across the cones)")
    out.append(f"  pin waist r {r_a:.2f}, bulge r {r_b:.2f}, cones {cone_h:.2f} tall at {SLOPE:.0f} deg")
    out.append(f"  ring bore r {r_b + gap:.2f} at the bulge, outside r {r_out:.2f} (joint {2 * r_out:.1f} across)")
    out.append(f"  C slot a wedge, half-angle {theta:.1f} deg: {2 * hc:.2f} wide at the waist (fin {FIN} wide, +/-{SWING:.0f} deg)")
    e_side = engagement(r_a - hc, side, ENGAGE)
    out.append(f"  sideways retention {r_a - hc:.2f}: RSS {e_side['rss']:.2f}, worst {e_side['worst_case']:.2f}, "
               f"ratio {e_side['ratio']:.1f} -> {'ok' if e_side['ok'] else 'FAIL'}")
    up = [("pin radius, XY wall", PROCESS["xy_wall"]),
          ("bore radius, vertical hole", PROCESS["hole_vertical"]),
          ("cone standing out of the wall", PROCESS["overhang_lip"]),
          ("cone height, layer quantised", PROCESS["z_step"])]
    e_up = engagement(BULGE - gap, up, ENGAGE)
    out.append(f"  vertical retention {BULGE - gap:.2f} (bulge minus gap): RSS {e_up['rss']:.2f}, worst "
               f"{e_up['worst_case']:.2f}, ratio {e_up['ratio']:.1f} -> {'ok' if e_up['ok'] else 'FAIL'}")
    close = stack([("pin XY", PROCESS["xy_wall"]), ("bore, vertical hole (prints small)", PROCESS["hole_vertical"])])
    free = gap - close["worst_case"]
    out.append(f"  running gap {gap:.2f} less the worst case {close['worst_case']:.2f} closing it = {free:.2f} "
               f"-> {'open' if free > 0 else 'MAY RUB'} (handbook: >= {PROCESS['gap_min']} drawn, as here, "
               f"{'ok' if gap >= PROCESS['gap_min'] else 'UNDER'})")
    first = gap + 2 * 0.45 - 2 * PROCESS["first_layer"]
    out.append(f"  first layer: gap {gap:.2f} + 0.45 chamfer each side - elephant's foot "
               f"{2 * PROCESS['first_layer']:.2f} = {first:.2f} -> {'ok' if first >= PROCESS['gap_min'] else 'FUSES'}")
    M = LOAD_N * LEVER
    Z = H * FIN ** 2 / 6
    sig = M / Z
    out.append(f"  fin bending: {LOAD_N:.0f} N at {LEVER:.0f} mm = {M:.0f} N mm on a {FIN} x {H} section "
               f"(Z {Z:.1f} mm3): {sig:.0f} MPa vs {PLA_XY_MPA:.0f}/{SAFETY:.0f} = {PLA_XY_MPA / SAFETY:.0f} "
               f"-> {'ok' if sig <= PLA_XY_MPA / SAFETY else 'FAIL'}")
    ok = e_side["ok"] and e_up["ok"] and free > 0 and first >= PROCESS["gap_min"] and sig <= PLA_XY_MPA / SAFETY
    return out, ok, dict(r_a=r_a, r_b=r_b, theta=theta, r_out=r_out, cone_h=cone_h)


def main():
    lines = ["OTTER JOINT BUDGET (handbook section 7; values from mechanism_budget.PROCESS)",
             f"requirement: +/-{SWING:.0f} deg a joint, survives {LOAD_N:.0f} N at {LEVER:.0f} mm, print in place, no hardware", ""]
    all_ok = True
    for g in (0.30, 0.35, 0.45):
        out, ok, _ = report(g)
        lines += out + [""]
        all_ok &= ok
    lines.append("PASS: every variant meets the rules" if all_ok else "FAIL: change the design before modelling")
    text = "\n".join(lines)
    print(text)
    (HERE / "checks").mkdir(exist_ok=True)
    (HERE / "checks" / "budget.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
