#!/usr/bin/env python3
"""Press-to-Light Chapel: the lift-and-drop drive, in numbers, before it is modelled
(handbook section 7, step 3), 2026-11-17.

Scott, 2026-11-14: "lift-and-drop first". The steeple is lifted and let go; its weight
drives a twisted star bar down through a short star nut in the spinner's hub, which
turns the spinner. Just before the steeple lands, the star leaves the nut through the
bottom and the spinner coasts free on a point pivot. No spring, matte PLA.

    python3 chapel_budget.py     (writes checks/budget.txt)
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from mechanism_budget import PLA, PROCESS, engagement  # noqa: E402

G = 9.81
# the drive (values the .scad uses)
LEAD = 24.0          # mm of drop per spinner turn (20 leaned the nut's slots past 45 deg)
R_OUT, R_IN = 3.15, 2.0   # the star's tips and roots
TEETH = 4
NUT_H = 4.0
STAR_L = 20.0
CLEARANCES = [0.3, 0.4, 0.5]   # all round, star to nut: the coupon's three hubs
KEY_R = 3.0          # the square key in the guide: its corners bear at about this radius
PIVOT_R = 0.4        # a cone point on a cone socket: friction acts at a fraction of a mm
# masses (g): the coupon's steeple stand-in and shaft, and one hub with its flag
M_STEEPLE, M_SHAFT, M_SPIN = 12.0, 2.5, 6.0
I_SPIN = 6.0e-3 * 0.018 ** 2 * 0.6   # kg m2: about 60 % of its mass at the flag's 18 mm


_m = HERE / "checks" / "masses.json"
MEASURED = _m.exists()
if MEASURED:   # from the exported parts (check_coupon.py), once they exist
    import json
    _d = json.loads(_m.read_text())
    M_STEEPLE, M_SHAFT, M_SPIN, I_SPIN = _d["steeple_g"], _d["shaft_g"], _d["hub_g"], _d["hub_I_kgm2"]


def out(lines, s=""):
    lines.append(s)


def main():
    L = []
    out(L, "PRESS-TO-LIGHT CHAPEL: THE LIFT-AND-DROP DRIVE (hand calculations, before modelling)")
    r_c = (R_OUT + R_IN) / 2
    alpha = math.atan(LEAD / (2 * math.pi * r_c))
    out(L, f"helix: {LEAD} mm a turn; at the teeth's middle (r {r_c:.2f}) {math.degrees(alpha):.1f} deg from level")
    # the nut's slots reach R_OUT + the largest clearance, and the bore under it BORE_R: their
    # flanks lean further than the shaft's (at LEAD 20 the slots leaned 48 deg; the gate propped them)
    leans = {"shaft tips": R_OUT, "nut slots": R_OUT + max(CLEARANCES), "bore under the nut": R_OUT + 0.6}
    ok_print = True
    for name, r in leans.items():
        a = math.degrees(math.atan(2 * math.pi * r / LEAD))
        ok_print &= a <= 45.0
        out(L, f"  printing: {name} (r {r:.2f}) lean {a:.1f} deg from upright (<= 45): {'PASS' if a <= 45 else 'FAIL'}")
    W = (M_STEEPLE + M_SHAFT) / 1000 * G
    Wsp = M_SPIN / 1000 * G
    out(L, f"weight driving it: {W * 1000:.0f} mN ({M_STEEPLE + M_SHAFT:.1f} g); the spinner {Wsp * 1000:.0f} mN "
           f"({'measured on the exported parts' if MEASURED else 'estimated'})")
    worst_ok = True
    for name, mu in (("design", PLA["mu"]), ("worst", 0.55)):
        phi = math.atan(mu)
        if alpha <= phi:
            out(L, f"  mu {mu} ({name}): helix {math.degrees(alpha):.1f} <= friction angle {math.degrees(phi):.1f}: SELF-LOCKING, FAIL")
            worst_ok = False
            continue
        t = math.tan(alpha - phi)
        # torque on the nut; the guide's key reacts it, and its friction eats into the weight
        T = W * (r_c / 1000) * t / (1 + mu * (r_c / KEY_R) * t)
        F_ax = T / ((r_c / 1000) * t)                      # the axial push the nut gets
        T_piv = mu * (Wsp + F_ax) * PIVOT_R / 1000
        net = T - T_piv
        out(L, f"  mu {mu} ({name}): drive torque {T * 1e6:.0f} uN.m, pivot friction {T_piv * 1e6:.0f}, "
               f"net {net * 1e6:.0f} ({T / T_piv:.1f}x)")
        if T < 2 * T_piv:
            worst_ok = False
        # the drop: energy into the spinner over the driven travel, then its coast on the pivot
        d = (STAR_L + NUT_H) / 1000
        theta = 2 * math.pi * d * 1000 / LEAD
        m = (M_STEEPLE + M_SHAFT) / 1000
        k = 2 * math.pi / (LEAD / 1000)                     # rad of spin per m of drop
        E = net * theta                                    # into spin and the falling steeple together
        omega = math.sqrt(2 * E / (I_SPIN + m / k ** 2))
        coast = 0.5 * I_SPIN * omega ** 2 / (mu * Wsp * PIVOT_R / 1000)
        out(L, f"      driven {theta / 2 / math.pi:.2f} turns; leaving the nut at {omega / 2 / math.pi:.1f} turns/s; "
               f"coast on the pivot alone up to {coast / 2 / math.pi:.0f} turns (an upper bound: rubbing the rod adds friction)")
    out(L, f"  drive vs friction, worst case at least 2x: {'PASS' if worst_ok else 'FAIL'}")
    out(L)
    out(L, "ENGAGEMENT: star tips into the nut's teeth, radially, per clearance (3x RSS and worst case)")
    items = [("nut hole, vertical", PROCESS["hole_vertical"]), ("star tips, XY", PROCESS["xy_wall"])]
    eng_ok = True
    for c in CLEARANCES:
        depth = (R_OUT - R_IN) - c
        r = engagement(depth, items)
        eng_ok &= r["ok"]
        out(L, f"  clearance {c}: overlap {depth:.2f} mm, needs {r['min_depth']:.2f} (3x RSS {r['rss']:.2f}, "
               f"worst {r['worst_case']:.2f}): {'PASS' if r['ok'] else 'FAIL'}")
    out(L, f"  open gap: the smallest clearance {min(CLEARANCES)} >= {PROCESS['gap_min']}: "
           f"{'PASS' if min(CLEARANCES) >= PROCESS['gap_min'] else 'FAIL'}")
    out(L, f"RESULT: {'PASS' if ok_print and worst_ok and eng_ok else 'FAIL'}")
    text = "\n".join(L)
    print(text)
    (HERE / "checks").mkdir(exist_ok=True)
    (HERE / "checks" / "budget.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
