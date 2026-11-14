#!/usr/bin/env python3
"""Pocket Top: the snap's hand calculation, before the coupon is modelled (2026-11-14).

Brief (Benson, approved by Scott): a 3-part spinning top, under 5 g and 10 min, snapped
together by hand, in matte PLA, and the snap must survive 20 cycles. The Gear Heart's
posts snapped because their prongs bent across the layers, so here nothing that flexes
is printed upright.

The joint: a hex stem (printed upright, so its hex and groove are drawn in the plane and
come out true) through a hub printed flat. Three straight spring beams lie in the hub's
plane round the hole, each with a nub at its free end that reaches through a window in
the hole's wall into a groove round the stem. The beams bend in the print plane, along
the layers. The hex drives the spin (friction alone could not: below); the three nubs,
held 0.05 into the groove, centre the stem.

    python3 snap_budget.py      (writes checks/snap_budget.txt)
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from mechanism_budget import PLA, PROCESS, cantilever, engagement, mating_force  # noqa: E402

T, L, B = 1.3, 12.0, 3.4          # beam: thickness in the bend, length, width (= hub height)
PRELOAD = 0.05                    # how far each nub stays bent in the groove
RAMP_IN = 45                      # the stem end's lead-in, from the axis
RAMP_OUT = 30                     # the groove's catch flank, from the axis (60 from horizontal:
                                  # at 45 it faced down on the upright stem and needed support)
VARIANTS = (0.35, 0.45, 0.55)     # the nub's reach into the groove: the coupon's three

out = []
def line(s=""):
    out.append(s)

line("POCKET TOP SNAP: hex stem through a flat hub, three in-plane spring beams")
line(f"  beam {T} thick x {B} wide x {L} long, constant section, bending in the print plane")
line(f"  limits (printed PLA, XY): one snap {100 * PLA['eps_once']:.1f} %, repeated "
     f"{100 * PLA['eps_repeat']:.1f} % (the brief asks for 20 snaps: the repeated limit applies)")
stack = [("nub tip, drawn in XY", PROCESS["xy_wall"]), ("stem's hex face, drawn in XY", PROCESS["xy_wall"])]
for y in VARIANTS:
    c = cantilever(T, L, B, y, repeated=True)
    W_in = mating_force(c["tip_force_N"], RAMP_IN)["W_N"]
    W_out = mating_force(c["tip_force_N"], RAMP_OUT)["W_N"]
    g = engagement(y, stack)
    held = cantilever(T, L, B, PRELOAD)["strain_pct"]
    line(f"  reach {y:.2f}: strain {c['strain_pct']:.2f} % ({'ok' if c['ok'] else 'OVER'} for repeated); "
         f"push on {3 * W_in:.1f} N, pull off {3 * W_out:.1f} N; engagement {g['ratio']:.1f} x RSS "
         f"({'ok' if g['ok'] else 'under 3x'}); held in the groove {held:.2f} %")
line("  It comes apart by pulling, more easily than it goes on: the catch flank is 30 deg from the")
line("  axis so the upright stem prints it without support. Meant to come apart; see FACTS.md.")
line()

# Why the hex: what the snap's friction alone could pass on when the stem is twisted.
m_disc, r_disc = 0.0035, 0.018            # kg, m: about the top's mass, at a 36 mm rim
I = 0.5 * m_disc * r_disc ** 2            # a solid disc, the low end (a rim-heavy one is more)
w = 2 * math.pi * 25                      # 25 rev/s, a firm finger twist
t_twist = 0.05                            # s: how long a finger twist lasts
need = I * w / t_twist * 1000             # N mm
P_held = cantilever(T, L, B, PRELOAD)["tip_force_N"]
have = 3 * P_held * PLA["mu"] * 2.5       # three nubs, friction, at the stem's 2.5 face radius
line("WHY THE STEM IS A HEX")
line(f"  spinning the body up to 25 rev/s in a 0.05 s twist needs about {need:.1f} N mm;")
line(f"  the nubs' grip passes on about {have:.2f} N mm. A round stem would spin inside the body,")
line("  so the hex drives it, and the nubs only hold and centre it.")
text = "\n".join(out)
print(text)
(HERE / "checks" / "snap_budget.txt").write_text(text + "\n")
