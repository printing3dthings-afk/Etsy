#!/usr/bin/env python3
"""Kit-card A-frame chalet: the panel snap's hand calculation, before the coupon is modelled
(2026-11-25; mechanism handbook section 7).

Scott picked the A-frame chalet (2026-11-17) for the free MakerWorld kit-card pilot: one plate
inside 180 x 180 (an A1 mini), parts snapped together with no glue, an LED tea light inside.
Benson's brief: no slivers, no knife-edge tabs, a child can handle it.

The joint: an arrow tab on a panel's edge, through a slot in the part it joins. The tab is two
prongs that close together as the tab goes in and spring back under the far face. The panels
print flat, so the prongs lie in the panel's plane and bend along the layers: the Pocket Top's
proven beam (1.3 thick, 12 long; Scott picked its reach 0.45 on 2026-11-15), turned into an
edge tab. Nothing that flexes is printed upright (the Gear Heart's lesson).

    python3 snap_budget.py      (writes checks/snap_budget.txt)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from mechanism_budget import PLA, PROCESS, cantilever, engagement, mating_force, stack  # noqa: E402

T, L = 1.3, 12.0          # prong: thickness in the bend, length root to nub (the Pocket Top's beam)
B = 2.4                   # prong width = the panel's thickness (the print's Z)
GRIP = 3.0                # what the tab passes through: the base floor, and the roof
RAMP_IN = 30              # the nub's lead-in, from the insertion axis
CATCH = 50                # the catch flank, from the insertion axis: 60 sat 5 deg off
                          # self-locking (65.8 at mu 0.45), where friction decides everything
VARIANTS = (0.35, 0.45, 0.55)
TABS = 2                  # per panel edge

out = []
line = out.append
line("KIT-CARD CHALET SNAP: an arrow tab, two in-plane prongs, through a 3.0 slot")
line(f"  prong {T} thick x {B} wide x {L} long, constant section, bending in the print plane")
line(f"  limits (printed PLA, XY): one snap {100 * PLA['eps_once']:.1f} %, repeated "
     f"{100 * PLA['eps_repeat']:.1f} % (a kit is built and taken apart: repeated applies)")
st = [("nub tip, drawn in XY", PROCESS["xy_wall"]), ("slot edge, a hole in XY", PROCESS["hole_vertical"])]
for y in VARIANTS:
    c = cantilever(T, L, B, y, repeated=True)
    w_in = 2 * mating_force(c["tip_force_N"], RAMP_IN)["W_N"]
    w_out = 2 * mating_force(c["tip_force_N"], CATCH)["W_N"]
    g = engagement(y, st)
    line(f"  reach {y:.2f}: strain {c['strain_pct']:.2f} % ({'ok' if c['ok'] else 'OVER'}); "
         f"a tab pushes in at {w_in:.1f} N and pulls out at {w_out:.1f} N; a panel edge ({TABS} tabs) "
         f"{TABS * w_in:.1f} N in, {TABS * w_out:.1f} N out; engagement {g['ratio']:.1f} x RSS, "
         f"worst case {g['worst_case']:.2f} ({'ok' if g['ok'] else 'SHORT'})")
# the floor prints face down (its top on the bed): a floor printed face up would bridge the
# skirt's whole cavity. The elephant's foot then narrows the slot's mouth, not the grip.
s = stack([("floor thickness, printed in Z", PROCESS["z_step"]), ("shoulder to catch, drawn in XY", PROCESS["xy_wall"])])
line(f"  grip: the catch starts {GRIP} + 0.15 below the shoulder; the stack along it is worst "
     f"{s['worst_case']:.2f}, RSS {s['rss']:.2f}. Thick by the worst case, the catch lands 0.05 inside "
     f"the floor and its {CATCH} deg flank rides the edge: the nubs stay a little bent and pull the "
     f"panel down tight. Thin by it, the panel can lift 0.35")
line("  the rule (3x RSS and over the worst case) passes at 0.55 only; 0.45, the Pocket Top's pick, is "
     "2.5x. The coupon tries all three.")
line(f"  centre gap between the prongs 1.6: each closes by the reach, so 0.55 leaves "
     f"{1.6 - 2 * 0.55:.2f} at full bend (>= {PROCESS['gap_min']} stays open)")
(HERE / "checks").mkdir(exist_ok=True)
(HERE / "checks" / "snap_budget.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
