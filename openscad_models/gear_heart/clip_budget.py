#!/usr/bin/env python3
"""Gear Heart clips v2: the hand calculation before the model (Brief E, 2026-11-14).

Scott printed the whole heart (2026-11-13): the gears mesh and turn, but "the clips the
gears go on need to be much stronger"; one SNAPPED. This compares the old snap post with
the new pin, by tools/mechanism_budget.py.

Old: two prongs standing up out of the plate, printed upright. Pushing a gear over the
barb bends each prong at its root, and that bend is ACROSS the layers: printed PLA holds
roughly half its in-plane strength that way (handbook section 3, z_factor 0.55).

New: a separate pin, printed lying on its side. Its prongs bend in the print plane, along
the layers. Its head sits in a pocket in the plate's underside; its barbs catch the
gear's top, with a square catch face (it prints flat, so nothing hangs over air).

    python3 clip_budget.py        (writes checks/clip_budget.txt)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from mechanism_budget import PLA, PROCESS, cantilever, engagement, mating_force  # noqa: E402

out = []


def line(s=""):
    out.append(s)


# ---- the old post (gear_lib.scad, as printed) ----
old = cantilever(t=1.6, L=13.5, b=4.0, y=0.9)
z_once = 100 * PLA["eps_once"] * PLA["z_factor"]
line("OLD SNAP POST (printed upright, the prong's bend across the layers)")
line(f"  prong 1.6 x 4.0, 13.5 long, barb 0.9: strain {old['strain_pct']:.2f} %")
line(f"  limit across layers, one snap: {100 * PLA['eps_once']:.1f} % x {PLA['z_factor']} = {z_once:.2f} %"
     f"  -> {old['strain_pct'] / z_once:.0%} of it: FAIL (Scott's snapped)")
line()

# ---- the new pin ----
# Prongs: half-rounds of the 3.5 shank, flattened to 4.8 wide (the faces it prints on),
# split by a slot that widens from 2.4 at its rounded root to 3.2 at the tip, so each
# prong tapers from 2.3 to 1.9 thick. The root is in the head; the barb catches 0.35
# above the gear's top: 13.15 mm of prong.
H_ROOT, H_TIP, B, L = 2.3, 1.9, 4.8, 13.15
taper_k = 1.5 - (1.5 - 1 / 1.09) * (1 - H_TIP / H_ROOT) / 0.5   # between constant and full taper
line("NEW PIN (printed on its side, the prong's bend along the layers)")
line(f"  prong {H_ROOT} -> {H_TIP} thick (tapered), {B} wide, {L} long; strain coefficient {taper_k:.2f}")
stack = [("gear bore r (hole drawn in XY)", PROCESS["hole_vertical"]),
         ("barb r (drawn in XY, pin on its side)", PROCESS["xy_wall"])]
for e in (0.45, 0.55, 0.65):
    eps = taper_k * H_ROOT * e / (L * L)
    P = B * H_ROOT ** 2 / 6 * PLA["E"] * eps / L
    W = mating_force(P, 30)["W_N"]
    g = engagement(e, stack)
    line(f"  barb {e:.2f}: strain {100 * eps:.2f} % (one snap {100 * PLA['eps_once']:.1f}, repeated "
         f"{100 * PLA['eps_repeat']:.1f}: {'ok' if eps <= PLA['eps_repeat'] else 'ok once' if eps <= PLA['eps_once'] else 'FAIL'}); "
         f"push-on {2 * W:.0f} N for both prongs; engagement {g['ratio']:.1f} x RSS "
         f"({'ok' if g['ok'] else 'under 3x'})")
line("  catch face square: it self-locks (1 - mu tan 90 < 0), so the gear can't be pulled off;")
line("  squeeze the two prongs together to take one off.")
line()
line("  shank in the plate: double-D, 7.0 x 4.8, in a 7.7 hole (0.35 a side, as the old post)")
line("  head: a bar 10.5 x 4.8 x 2.4 in a pocket 11.0 x 5.3 under the plate, its roof pitched")
line("  at 55 deg (it prints with no support); it can't turn, so the gear turns on the pin,")
line("  and it can't pull up through the 7.7 hole.")
text = "\n".join(out)
print(text)
(HERE / "checks").mkdir(exist_ok=True)
(HERE / "checks" / "clip_budget.txt").write_text(text + "\n")
