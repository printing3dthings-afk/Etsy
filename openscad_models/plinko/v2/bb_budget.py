#!/usr/bin/env python3
"""Snowfall Plinko v2: the numbers for 6 mm airsoft BBs and a snap-in loading plug (2026-11-25).

Scott's release test (2026-11-25): the bridged cage was great, but the 5 mm print-in-place balls
broke loose during the print ("everything is too small for that"). He picked 6 mm airsoft BBs.
So the board loads them through a port in its top wall, closed by a plug that snaps in: the
chalet's arrow tab (kit_card_chalet/snap_budget.py), two in-plane prongs through a 3.0 wall.

    python3 bb_budget.py      (writes ../checks/bb_budget.txt)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from mechanism_budget import PLA, PROCESS, cantilever, engagement, mating_force  # noqa: E402

BB = 6.0
PASS, STOP = 1.3 * BB, 0.7 * BB       # the v1 gap rule (6.5 and 3.5 for 5 mm), scaled
T, L, B = 1.3, 12.0, 6.4              # prong: bend thickness, length, width (= plug thickness)
CATCH, RAMP = 50, 30
out = []
line = out.append
line(f"BALLS: 6 mm airsoft BBs. Gap rule: a pass >= {PASS:.1f}, a stop <= {STOP:.1f}, nothing between")
line(f"  chamber depth 6.8 (0.4 each side of a BB); front openings 3.0 (a stop); prong gap 4.0 (a stop)")
st = [("nub tip, drawn in XY", PROCESS["xy_wall"]), ("port edge, drawn in XY", PROCESS["xy_wall"])]
for y in (0.35, 0.45, 0.55):
    c = cantilever(T, L, B, y)
    w_in = 2 * mating_force(c["tip_force_N"], RAMP)["W_N"]
    w_out = 2 * mating_force(c["tip_force_N"], CATCH)["W_N"]
    g = engagement(y, st)
    line(f"PLUG reach {y:.2f}: strain {c['strain_pct']:.2f} % ({'ok' if c['ok'] else 'OVER'}, limit "
         f"{100 * PLA['eps_repeat']:.1f}); {w_in:.1f} N in, {w_out:.1f} N out; engagement {g['ratio']:.1f}x RSS "
         f"({'ok' if g['ok'] else 'short'})")
line("  the port is a wall drawn in XY (0.10), not a hole (0.15) as the chalet's slot was, so 0.45 now")
line("  passes the 3x rule too. Prongs are 6.4 wide, not 2.4, so the forces are 2.7x the chalet's.")
mass = 0.12 * 30                       # g: about 30 BBs at 0.12 g (0.12 g grade)
line(f"LOAD: ~30 BBs at 0.12 g = {mass:.1f} g; on the plug when the board is turned over: "
     f"{mass / 1000 * 9.81:.3f} N, against {2 * mating_force(cantilever(T, L, B, 0.45)['tip_force_N'], CATCH)['W_N']:.1f} N to pull it at 0.45")
(HERE.parent / "checks").mkdir(exist_ok=True)
(HERE.parent / "checks" / "bb_budget.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
