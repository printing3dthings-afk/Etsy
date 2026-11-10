#!/usr/bin/env python3
"""Numbers a printed mechanism must show before it is built (2026-11-10).

Scott, after the Fold Stand failed twice: "You need to learn more modeling
engineering ... Your ability and design technique need to be at a much higher
level." Both stands passed every geometric check (watertight, overhangs,
walls, the slicer, a sectioned ratchet check) and failed in the hand. Geometry
checks prove the model is printable, not that the mechanism works once it is
printed with real error. This tool is the missing half: the hand calculations
an engineer does first. The rules and their sources are in
data/knowledge_base/mechanism_engineering_handbook.md.

    from mechanism_budget import *
    cantilever(t=1.6, L=18, b=4, y=1.15)          # strain, force; vs PLA limits
    stack([("pin r", 0.10), ("bore r", 0.20)])     # worst case and RSS
    engagement(depth=0.45, stack_items=[...])      # depth vs the stack: the 3x rule
    mating_force(P=5.0, angle_deg=30)              # push-in force, self-lock check

    python3 tools/mechanism_budget.py --demo       # the Fold Stand v2 hinge, worked
"""
import argparse
import math

# Printed PLA, 23 C, flat (XY) orientation, design values. Ranges and sources in the handbook.
PLA = {"E": 2600.0,            # MPa, tensile modulus of printed PLA, XY (datasheets 2.7-3.5 GPa)
       "eps_yield": 0.020,     # yield strain ~2-3 %; brittle, little ductility
       "eps_once": 0.014,      # one-time snap: ~70 % of yield (amorphous rule, Bayer guide)
       "eps_repeat": 0.008,    # repeated flexing: ~60 % of the one-time value
       "z_factor": 0.55,       # interlayer (Z) strength as a fraction of XY
       "mu": 0.45,             # PLA on PLA, dry, kinetic ~0.35-0.55
       "Tg": 57.0}             # C: a hot car makes PLA creep and soften
PETG = {"E": 2000.0, "eps_yield": 0.040, "eps_once": 0.028, "eps_repeat": 0.017,
        "z_factor": 0.6, "mu": 0.35, "Tg": 78.0}
MATERIALS = {"PLA": PLA, "PETG": PETG}

# What a tuned P1S with a 0.4 nozzle holds, per feature (mm, +/-). Handbook section 1.
PROCESS = {"xy_wall": 0.10,         # an outer wall in XY
           "z_step": 0.10,          # height of a feature, quantised to 0.2 layers: half a layer
           "hole_vertical": 0.15,   # radius of a hole drawn in XY (prints small; compensate)
           "hole_horizontal": 0.25, # radius of a hole along X/Y: teardrop, sag, stair-steps
           "overhang_lip": 0.20,    # a lip or ridge standing out of a vertical wall
           "first_layer": 0.15,     # elephant's foot on the bed face
           "gap_min": 0.30}         # smallest gap that reliably stays open between moving parts


def cantilever(t, L, b, y, mat="PLA", taper=False, repeated=True):
    """A rectangular cantilever (thickness t along the bend, length L, width b) bent y at its
    tip. Bayer/Covestro: constant section y = 0.67 eps L^2 / t, so eps = 1.5 t y / L^2; tapered
    to t/2 at the tip, y = 1.09 eps L^2 / t. Tip force P = (b t^2 / 6) E eps / L."""
    m = MATERIALS[mat]
    eps = (t * y / (1.09 * L * L)) if taper else (1.5 * t * y / (L * L))
    P = b * t * t / 6.0 * m["E"] * eps / L
    limit = m["eps_repeat"] if repeated else m["eps_once"]
    return {"strain_pct": 100 * eps, "limit_pct": 100 * limit, "ok": eps <= limit,
            "tip_force_N": P, "stiffness_N_per_mm": P / y if y else 0.0}


def stack(items):
    """items: (name, +/- tolerance). Worst case adds them; RSS (root sum of squares) is the
    statistical stack when the errors are independent. Design to worst case for anything
    that must work every time; RSS is the expected spread."""
    wc = sum(abs(t) for _, t in items)
    rss = math.sqrt(sum(t * t for _, t in items))
    return {"worst_case": wc, "rss": rss, "items": items}


def engagement(depth, stack_items, ratio=3.0):
    """A catch, notch, undercut or detent of nominal depth against the stack of every error
    between the two parts. The rule this shop now uses: depth >= ratio x RSS AND depth >
    worst case, so that with every error at its limit something is still engaged."""
    s = stack(stack_items)
    return {"depth": depth, "rss": s["rss"], "worst_case": s["worst_case"],
            "ratio": depth / s["rss"] if s["rss"] else float("inf"),
            "min_depth": max(ratio * s["rss"], s["worst_case"] + 0.1),
            "ok": depth >= ratio * s["rss"] and depth > s["worst_case"]}


def mating_force(P, angle_deg, mu=PLA["mu"]):
    """Force to push a snap over its ramp (Bayer): W = P (mu + tan a) / (1 - mu tan a).
    At 90 - a <= atan(mu) the face is self-locking: no push separates it."""
    a = math.radians(angle_deg)
    den = 1 - mu * math.tan(a)
    W = float("inf") if den <= 0 else P * (mu + math.tan(a)) / den
    return {"W_N": W, "self_locking": den <= 0, "friction_angle_deg": math.degrees(math.atan(mu))}


def holding_torque_needed(mass_g, lever_mm, factor=3.0):
    """N mm a joint must hold for a mass on a lever arm, with a safety factor."""
    return mass_g / 1000 * 9.81 * lever_mm * factor


def demo():
    print("Fold Stand v2 hinge, run through the numbers it should have been run through:\n")
    c = cantilever(t=1.6, L=18, b=16, y=1.15)
    print(f"blade bent 1.15 (pin going in): strain {c['strain_pct']:.2f} % vs repeated limit "
          f"{c['limit_pct']:.2f} %: {'ok' if c['ok'] else 'TOO HIGH'}; tip force {c['tip_force_N']:.1f} N")
    items = [("pin radius, vertical, XY", PROCESS["xy_wall"]),
             ("bore radius, horizontal teardrop", PROCESS["hole_horizontal"]),
             ("ridge standing out of an upright wall", PROCESS["overhang_lip"]),
             ("ridge top face, layer quantised", PROCESS["z_step"]),
             ("blade position across the slot", PROCESS["xy_wall"])]
    e = engagement(0.45, items)
    print(f"ratchet notch 0.45 deep vs the stack: RSS {e['rss']:.2f}, worst {e['worst_case']:.2f}; "
          f"ratio {e['ratio']:.1f} -> {'ok' if e['ok'] else 'FAILS'}; needs >= {e['min_depth']:.2f} mm")
    b = engagement(0.58, items[:2] + [("head and barrel faces", PROCESS["xy_wall"])])
    print(f"release-button window 0.58 vs its stack: ratio {b['ratio']:.1f} -> {'ok' if b['ok'] else 'FAILS'}")
    print(f"gap between blade and bore 0.15 vs the smallest gap that stays open "
          f"{PROCESS['gap_min']}: {'ok' if 0.15 >= PROCESS['gap_min'] else 'FAILS'}")
    T = holding_torque_needed(200, 60)
    print(f"a 200 g phone about 60 mm from the hinge, x3: {T:.0f} N mm the lock must hold")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    if ap.parse_args().demo:
        demo()
