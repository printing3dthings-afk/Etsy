#!/usr/bin/env python3
"""Fold Stand v3, the numbers before the model (2026-11-10).

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
PLATE_L, PLATE_T, W = 120.0, 5.0, 76.0
TONGUE_R = 3.0                         # the plate's round bottom edge
PIVOT_Z = 7.0                          # the tongue's axis above the table (the groove bar)
A_SOCKET = 65.0                        # the prop's nose centre, along the plate from the pivot
NOSE_R = 2.0                           # the prop's round top end
NOSE_IN = 0.6                          # how far the nose centre sits inside the back face
PROP_L = 66.0                          # nose centre to foot centre
FOOT_R = 3.0                           # the prop's round foot
BASE_T = 4.0                           # the base plate; notches are cut into a raised bar
NOTCH_Z = BASE_T + 2.0                 # the foot's centre when seated (table z = 0)
BASE_FRONT = 45.0                      # base length in front of the pivot
SHELF_U = 10.0                         # the phone's bottom edge, along the plate from the pivot
FRONT_F = PLATE_T - TONGUE_R           # the plate's front face, in front of the pivot line
PLA = 1.24e-3                          # g per mm3


def unit(t):
    return math.cos(math.radians(t)), math.sin(math.radians(t))


def foot_y(theta):
    """Where the foot centre sits behind the pivot for a plate angle theta."""
    c, s = unit(theta)
    # the back face is TONGUE_R behind the pivot line (the plate prints on its back with
    # the tongue's axis at z = TONGUE_R); the nose centre sits NOSE_IN inside it, in the
    # pocket's top corner (against its ceiling and its upper wall)
    off = TONGUE_R - NOSE_IN
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


BASE_BACK = 120.0                      # base length behind the pivot: 100 clears the last notch;
                                       # 120 lets a firm 2 N press at the phone's top not tip it
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
    print("plate  foot    prop    push on  push at   centre of  safety vs tipping back      sliding,")
    print("angle  at y    force   notch    socket    mass y     1 N top  2 N top  2 N mid    1 N top")
    for th, fy, F, H, ph, yc, sf1, sf2, sfm, sl1 in rows:
        print(f"{th:4d}  {fy:6.1f}  {F:5.2f} N  {H:5.2f} N  {ph:5.0f} deg  {yc:6.1f}    {sf1:5.1f}    {sf2:5.1f}    {sfm:5.1f}      {sl1:5.1f}")
    phis = [r[4] for r in rows]
    print(f"push at the socket {min(phis):.0f}-{max(phis):.0f} deg from the plate's normal: held from -24 "
          f"to 90, margins {min(phis) + 24:.0f} and {90 - max(phis):.0f} deg")
    ys = [r[1] for r in rows]
    gaps = [b - a for a, b in zip(ys, ys[1:])]
    print(f"notch spacing {min(gaps):.1f}-{max(gaps):.1f} mm (want >= 8 so the foot can't sit between two)")
    # the budget for each joint
    items = [("groove radius, a trough in XY", PROCESS["xy_wall"]),
             ("tongue radius, a horizontal round edge", PROCESS["hole_horizontal"]),
             ("base bar height", PROCESS["z_step"])]
    e = engagement(TONGUE_R + 0.7, items)
    print(f"pivot: tongue {TONGUE_R} in a groove {TONGUE_R + 0.7} deep: ratio {e['ratio']:.1f}, worst {e['worst_case']:.2f} -> {'ok' if e['ok'] else 'FAIL'}")
    items = [("notch, a trough in XY", PROCESS["xy_wall"]), ("foot, an edge printed in XY (prop on its side)", PROCESS["xy_wall"]),
             ("base bar height", PROCESS["z_step"]), ("prop length", PROCESS["xy_wall"])]
    e = engagement(3.0, items)
    print(f"notch: rear wall 3.0 high: ratio {e['ratio']:.1f}, worst {e['worst_case']:.2f} -> {'ok' if e['ok'] else 'FAIL'}")
    items = [("pocket's upper wall, a vertical XY wall", PROCESS["xy_wall"]), ("nose, XY", PROCESS["xy_wall"]),
             ("pocket ceiling, a bridge (sags)", PROCESS["overhang_lip"])]
    e = engagement(NOSE_R + NOSE_IN, items)
    print(f"socket: the nose must come {NOSE_R + NOSE_IN} out of the pocket to pass its upper wall: ratio {e['ratio']:.1f}, worst "
          f"{e['worst_case']:.2f} -> {'ok' if e['ok'] else 'FAIL'}")
    print(f"clearances: 0.4 at the notches and the socket, 0.7 round the tongue (0.32 at its teardrop underside), against the {PROCESS['gap_min']} minimum open gap")
    if "--scad" in sys.argv:
        print("NOTCH_Y = [" + ", ".join(f"{y:.2f}" for y in ys) + "];")


if __name__ == "__main__":
    main()
