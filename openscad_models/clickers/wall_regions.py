#!/usr/bin/env python3
"""The regions each gingerbread print declares to the product gate's 1.2 mm wall
floor, as product_gate.py flags (2026-11-05). See product_gate.wall_skipper()
for the rule and CLICKERS_PRINTING.md for why each is legitimate:

  relief  the raised colour detail, each colour its own part: snowflakes, holly,
          icing, gumdrops. DETAIL_STANDARD sizes; print_fidelity checks them.
  thread  the teeth: from the root to the crest, the thread's height. A tooth's
          axial width runs from 3.7 at its root to a 0.29 crest flat by design.
          The collar's wall outside the root and the lid's wall inside it are
          NOT in the band, and are held to the floor.
  socket  the cookie's MX socket post: 5.6 across to ride into the switch's stem
          opening, round the 4.1 standard cross, so 0.6-0.7 at the arm tips.
          Fixed by the switch, not chosen; it is the post on the printed clicker.

Every number is read from the .scad files, so the regions follow the design.

    python3 wall_regions.py tin_print      (prints the flags)
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLK = (HERE / "gingerbread_tin" / "gingerbread_tin_clicker.scad").read_text()
CAN = (HERE / "gingerbread_tin" / "gingerbread_tin_canister.scad").read_text()
LIB = (HERE / "clicker_lib.scad").read_text()


def num(src, name):
    return float(re.search(rf"(?<![\w.]){name}\s*=\s*([\d.]+)\s*;", src).group(1))


TH_R, TH_D, TH_C, TH_H, TH_P = (num(CLK, k) for k in ("TH_R", "TH_D", "TH_C", "TH_H", "TH_P"))
WELL_H = num(LIB, "mx_below") + num(LIB, "mx_pins") + 0.6
S = 1.6 + WELL_H                                   # the tin's top face, the lid's floor
T = num(CAN, "T")                                  # the canister's
POD_H = WELL_H + num(CAN, "PFLOOR")                # the pod lifts the lid's floor this far
BORE = TH_R - TH_D + TH_C - 0.1                    # the collar's crests
NUT = (BORE - 0.05, TH_R + TH_C + 0.05)            # crest to root, in the collar
SCREW = (TH_R - TH_D - 0.05, TH_R + 0.05)          # root to crest, on the lid
POST = num(LIB, "post_r") + 0.1
CAV_H = num(LIB, "cav_h")

D = "gingerbread_tin/parts/"
REGIONS = {
    # the nut's teeth run up through the collar's sloped top to its flat
    "tin_print": ([D + "tin_snow.stl"], [(*NUT, S, S + TH_H + TH_P)]),
    "lid_print": ([D + "lid_holly.stl", D + "lid_snow.stl"], [(*SCREW, 0.0, TH_H)]),
    "cookie_print": ([D + "cookie_icing.stl", D + "cookie_red.stl", D + "cookie_green.stl"],
                     [(0.0, POST, -0.1, CAV_H + 0.1)]),
    "canister_print": ([D + "canister_snow.stl"], [(*NUT, T, T + TH_H + TH_P)]),
    "lid_closed_print": ([D + "lid_closed_holly.stl", D + "lid_closed_snow.stl"],
                         [(*SCREW, POD_H, POD_H + TH_H)]),
}


def flags(name):
    parts, bands = REGIONS[name]
    out = []
    for p in parts:
        out += ["--wall-skip-part", str(HERE / p)]
    for b in bands:
        out += ["--wall-skip-band", ",".join(f"{v:.3f}" for v in b)]
    return out


if __name__ == "__main__":
    print(" ".join(flags(sys.argv[1])))
