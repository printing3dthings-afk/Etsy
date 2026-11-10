#!/usr/bin/env python3
"""Fold Stand v4, the numbers before the model (2026-11-10).

v3's mechanism, made one folding object (Scott: "it needs to be 3 pieces that connect
and stay together ... fold it down and store it"). The plate twist-locks onto the base
on two side pins; the prop is hinged into a slot through the plate, print-in-place, and
folds flush into it. Its hinge is now a fixed axis 2.5 in front of the pivot line, so
there is no socket angle to hold: any push direction is carried by the hinge.

What follows is v3's calculation with v4's geometry.

Scott picked option A after v2 failed ("pins don't click"): a prop whose foot
sits in deep notches in the base, like an easel. Three flat parts, no pins and
nothing that bends: the plate's round bottom edge sits in a groove across the
base, the prop's round top end sits in the top corner of a pocket in the plate's
back face, and its foot drops into one notch per angle. Every load is plastic pressing on plastic,
held by gravity.

This works out, per data/knowledge_base/mechanism_engineering_handbook.md s.7:
  - where each notch goes for each plate angle (side view, y back, z up);
  - the force down the prop and on the notch wall, with a 250 g phone;
  - stability: tipping back and forward, with a 2 N tap on the screen;
  - the engagement and clearance budget for every joint.

    python3 stand_v3_calc.py          prints the table; --scad prints NOTCH_Y for the .scad
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from mechanism_budget import PROCESS, engagement  # noqa: E402

# ---- the design inputs (mm, g) -------------------------------------------------------------
ANGLES = [80, 75, 70, 65, 60, 55]      # the plate's lean from the table, steepest first
PHONE_G, PHONE_L, PHONE_T = 250.0, 160.0, 10.5     # a large phone in a thick case
PLATE_L, PLATE_T, W = 135.0, 8.0, 76.0
TONGUE_R = 3.0                         # the plate's round bottom edge
PIVOT_Z = 10.0                         # the pivot pins' axis above the table (folded, the plate clears the notch bar)
A_SOCKET = 61.0                        # the prop's hinge axis, along the plate from the pivot
NOSE_R = 2.0                           # the prop's round top end
NOSE_IN = 0.6                          # how far the nose centre sits inside the back face
PROP_L = (65.0 ** 2 + 1.0) ** 0.5    # hinge axis to foot centre (the foot sits 1 lower in the print)
FOOT_R = 3.0                           # the prop's round foot
BASE_T = 4.0                           # the base plate; notches are cut into a raised bar
NOTCH_Z = BASE_T + 2.0                 # the foot's centre when seated (table z = 0)
BASE_FRONT = 8.5                       # base length in front of the pivot: just past the lugs
SHELF_U = 10.0                         # the phone's bottom edge, along the plate from the pivot
PIVOT_IN = 3.0                         # the pivot axis above the plate's back face (in the plate's print)
HINGE_IN = 4.0                         # the prop's hinge axis above it
FRONT_F = PLATE_T - PIVOT_IN           # the plate's front face, in front of the pivot line
PLA = 1.24e-3                          # g per mm3


def unit(t):
    return math.cos(math.radians(t)), math.sin(math.radians(t))


def foot_y(theta):
    """Where the foot centre sits behind the pivot for a plate angle theta."""
    c, s = unit(theta)
    # the plate prints on its back: the pivot pins' axis PIVOT_IN above the back face,
    # the prop's hinge axis HINGE_IN above it, so 2.5 in front of the pivot line
    off = -(HINGE_IN - PIVOT_IN)       # the hinge is in FRONT of the pivot line
    ny, nz = A_SOCKET * c + off * s, PIVOT_Z + A_SOCKET * s - off * c
    dz = nz - NOTCH_Z
    if dz > PROP_L:
        return None, (ny, nz)
    return ny + math.sqrt(PROP_L ** 2 - dz ** 2), (ny, nz)


def socket_angle(theta, fy):
    """The prop is a two-force member: its push on the plate runs along it, foot to nose.
    Its angle from the plate's normal, positive up the plate. The pocket's top corner
    holds the nose for any angle from about -24 (friction, sliding down the ceiling) to
    90 (straight up into the upper wall); beyond 90 the prop would pull out."""
    c, s = unit(theta)
    _, (ny, nz) = foot_y(theta)
    dy, dz = ny - fy, nz - NOTCH_Z
    into = dy * (-s) + dz * c
    up = dy * c + dz * s
    return math.degrees(math.atan2(up, into))


def statics(theta, fy):
    """Phone and plate weight about the pivot, carried by the prop. Returns (prop force N,
    its horizontal part at the foot N, pivot reaction N)."""
    c, s = unit(theta)
    g = 9.81 / 1000
    Wp = PHONE_G * g
    Wl = PLATE_L * W * PLATE_T * 0.5 * PLA * g        # plate at ~50 % fill
    # the phone lies on the front face; its centre half its length up, half its depth out
    xp = (SHELF_U + PHONE_L / 2) * c - (FRONT_F + PHONE_T / 2) * s
    xl = (PLATE_L / 2) * c
    M = Wp * xp + Wl * xl                               # moment tipping the plate back (N mm)
    _, (ny, nz) = foot_y(theta)
    dy, dz = fy - ny, NOTCH_Z - nz                      # nose -> foot
    L = math.hypot(dy, dz)
    uy, uz = dy / L, dz / L
    # prop force F along the prop (compression) acts on the plate at the nose, direction
    # foot -> nose = (-uy, -uz); its moment about the pivot must balance M
    arm = ny * (-uz) - (nz - PIVOT_Z) * (-uy)
    F = M / arm if arm else float("inf")
    return F, abs(F * uy), Wp + Wl


BASE_BACK = 140.0                      # base length behind the pivot: the folded plate lies on it
MU_TABLE = 0.35                        # PLA on a wooden or laminate desk, dry (low end)


def stability(theta, fy, tap=1.0, at=1.0):
    """Tipping. The stand's centre of mass must sit between the base's front and back
    edges. Then a tap of `tap` N pressing INTO the screen (normal to it) at fraction `at`
    of the phone's height: its moment about the base's back edge against the weight's.
    Returns (centre of mass y, safety factor = restoring / tipping moment)."""
    c, s = unit(theta)
    g = 9.81 / 1000
    Wp, Wl = PHONE_G * g, PLATE_L * W * PLATE_T * 0.5 * PLA * g
    Wb = (BASE_FRONT + BASE_BACK) * W * BASE_T * 0.7 * PLA * g
    yc = (Wp * ((SHELF_U + PHONE_L / 2) * c - (FRONT_F + PHONE_T / 2) * s) + Wl * (PLATE_L / 2) * c + Wb * (BASE_BACK - BASE_FRONT) / 2) / (Wp + Wl + Wb)
    restore = (Wp + Wl + Wb) * (BASE_BACK - yc)
    # the tap point on the screen, and the force into it: the front face's inward normal
    d = SHELF_U + PHONE_L * at
    py, pz = d * c - (FRONT_F + PHONE_T) * s, PIVOT_Z + d * s + (FRONT_F + PHONE_T) * c
    fy_, fz_ = tap * s, -tap * c                       # back and down, into the screen
    # moment about the back edge (BASE_BACK, 0), positive = tipping backward
    rx, rz = py - BASE_BACK, pz
    tip = rz * fy_ - rx * fz_
    sf_tip = restore / tip if tip > 0 else float("inf")
    # sliding: the tap's push back against the table's grip on the whole stand
    slide = MU_TABLE * (Wp + Wl + Wb + tap * c) / (tap * s)
    return yc, sf_tip, slide


def table():
    rows = []
    for th in ANGLES:
        fy, (ny, nz) = foot_y(th)
        F, H, R = statics(th, fy)
        yc, sf1, sl1 = stability(th, fy, 1.0, 1.0)
        _, sf2, sl2 = stability(th, fy, 2.0, 1.0)
        _, sfm, _ = stability(th, fy, 2.0, 0.5)
        rows.append((th, fy, F, H, socket_angle(th, fy), yc, sf1, sf2, sfm, sl1))
    return rows


def main():
    rows = table()
    print(f"base from y = -{BASE_FRONT:.0f} to {BASE_BACK:.0f} (pivot at 0); a {PHONE_G:.0f} g phone, {PHONE_L:.0f} mm tall")
    print("plate  foot    prop    push on  centre of  safety vs tipping back      sliding,")
    print("angle  at y    force   notch    mass y     1 N top  2 N top  2 N mid    1 N top")
    for th, fy, F, H, ph, yc, sf1, sf2, sfm, sl1 in rows:
        print(f"{th:4d}  {fy:6.1f}  {F:5.2f} N  {H:5.2f} N  {yc:6.1f}    {sf1:5.1f}    {sf2:5.1f}    {sfm:5.1f}      {sl1:5.1f}")
    ys = [r[1] for r in rows]
    gaps = [b - a for a, b in zip(ys, ys[1:])]
    print(f"notch spacing {min(gaps):.1f}-{max(gaps):.1f} mm (want >= 8 so the foot can't sit between two)")
    # the budget for each joint
    # the pivot: a pin 6 round, 3.0 across flats tilted 35 deg on the plate, in a bore whose
    # slot rises straight up, 3.6 wide. It passes only with its flats upright, at a plate
    # angle of 145; folded (0) they are 35 deg off, at the steepest notch (80) 65. At 35 deg
    # off, the pin is 2 x 2.72 across the slot, against 3.6.
    items = [("pin round, its side arcs printed flat (XY)", PROCESS["xy_wall"]),
             ("pin round, layer steps on its arcs", PROCESS["z_step"]),
             ("lug slot, an upright XY wall", PROCESS["xy_wall"]),
             ("lug slot, the other wall, XY", PROCESS["xy_wall"])]
    e = engagement(3 * math.cos(math.radians(25)) - 1.8, items)
    print(f"pivot twist-lock: at its worst angle (folded) each side 0.92 wider than the slot: ratio {e['ratio']:.1f}, worst {e['worst_case']:.2f} -> "
          f"{'ok' if e['ok'] else 'FAIL'}; passes only at 145 deg, 65 past the steepest notch")
    # the prop's hinge: print-in-place cones from the slot's walls into sockets in the
    # prop's sides, 1.28 deep. To come off, the prop must shift sideways 1.28 + 0.4 one way,
    # and the other cone stops it after 0.4
    items = [("slot width, XY walls", PROCESS["xy_wall"]), ("prop width, XY walls", PROCESS["xy_wall"]),
             ("cone tip, its underside an overhang", PROCESS["overhang_lip"])]
    e = engagement(1.28, items)
    print(f"prop hinge: cones 1.28 into the prop's sides: ratio {e['ratio']:.1f}, worst {e['worst_case']:.2f} -> "
          f"{'ok' if e['ok'] else 'FAIL'}; it cannot come off at all (the far cone stops it)")
    items = [("notch, a trough in XY", PROCESS["xy_wall"]), ("foot, its arcs printed in the plate (layer steps)", PROCESS["z_step"]),
             ("foot's teardrop corner", PROCESS["xy_wall"]), ("base bar height", PROCESS["z_step"])]
    e = engagement(3.0, items)
    print(f"notch: rear wall 3.0 high: ratio {e['ratio']:.1f}, worst {e['worst_case']:.2f} -> {'ok' if e['ok'] else 'FAIL'}")
    print(f"clearances: print-in-place 0.45 (cones) and 0.4 (prop to slot); 0.35-0.73 round the pivot pins (their flank corner stands out to 3.38); "
          f"notches 0.7 (the foot's teardrop corners 0.33); against the {PROCESS['gap_min']} minimum open gap")
    if "--scad" in sys.argv:
        print("NOTCH_Y = [" + ", ".join(f"{y:.2f}" for y in ys) + "];")


if __name__ == "__main__":
    main()
