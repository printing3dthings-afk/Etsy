#!/usr/bin/env python3
"""Turn Bambu Studio G-code into the PrusaSlicer-tagged form our readers expect (2026-11-14).

WHY. Every toolpath reader here (print_fidelity.parse_gcode, gcode_viewer_data, as_printed)
was written against PrusaSlicer's markers: ";LAYER_CHANGE", ";Z:", ";HEIGHT:", ";TYPE:",
";WIDTH:". Bambu Studio, the slicer Scott actually prints from, writes "; CHANGE_LAYER",
"; Z_HEIGHT:", "; LAYER_HEIGHT:", "; FEATURE:", "; LINE_WIDTH:", and draws curves as G2/G3
arcs (3,635 of them on the Pocket Top coupon), which those readers skip, so a Bambu slice
read raw came out as one layer. Translated, the readers see what Bambu Studio will print:
its fuzzy skin, its vase mode, its own walls, not PrusaSlicer's guess at them.

    python3 tools/bambu_gcode.py plate.gcode.3mf -o plate.gcode     (or a bare .gcode in)
"""
import argparse
import math
import re
import zipfile
from pathlib import Path

# Bambu's feature names -> PrusaSlicer's. The readers file any name they don't know as
# "Other", which as_printed hides: before the model's own features were mapped, a Bambu
# slice rendered with no tops, bottoms or infill (2026-11-14, the texture sampler).
FEATURES = {"Outer wall": "External perimeter", "Inner wall": "Perimeter",
            "Overhang wall": "Overhang perimeter", "Sparse infill": "Internal infill",
            "Internal solid infill": "Solid infill", "Bottom surface": "Solid infill",
            "Floating vertical shell": "Solid infill", "Top surface": "Top solid infill",
            "Ironing": "Top solid infill",   # the top's smoothing pass; as "Other" it drew the top black
            "Bridge": "Bridge infill", "Internal Bridge": "Bridge infill", "Gap infill": "Gap fill",
            "Prime tower": "Wipe tower", "Support": "Support material",
            "Support interface": "Support material interface", "Support transition": "Support material",
            "Brim": "Skirt/Brim", "Skirt": "Skirt/Brim"}
_NUM = re.compile(r"([XYZEIJF])([-+]?\d*\.?\d+)")
ARC_STEP = 0.2          # mm of arc per straight piece: well under a bead's width


def _arc(x0, y0, x1, y1, i, j, cw):
    """Points along a G2 (cw) / G3 arc from (x0, y0) to (x1, y1) about (x0 + i, y0 + j)."""
    cx, cy = x0 + i, y0 + j
    r = math.hypot(i, j)
    a0, a1 = math.atan2(y0 - cy, x0 - cx), math.atan2(y1 - cy, x1 - cx)
    sweep = a1 - a0
    if cw and sweep >= 0:
        sweep -= 2 * math.pi
    if not cw and sweep <= 0:
        sweep += 2 * math.pi
    if abs(x1 - x0) < 1e-9 and abs(y1 - y0) < 1e-9:
        sweep = -2 * math.pi if cw else 2 * math.pi          # a full circle
    n = max(2, int(abs(sweep) * r / ARC_STEP) + 1)
    return [(cx + r * math.cos(a0 + sweep * k / n), cy + r * math.sin(a0 + sweep * k / n)) for k in range(1, n + 1)]


def convert(lines):
    out, x, y, rel = [], 0.0, 0.0, True
    for line in lines:
        s = line.rstrip("\n")
        if s.startswith("; CHANGE_LAYER"):
            out.append(";LAYER_CHANGE")
            continue
        if s.startswith("; Z_HEIGHT:"):
            out.append(";Z:" + s.split(":", 1)[1].strip())
            continue
        if s.startswith("; LAYER_HEIGHT:"):
            out.append(";HEIGHT:" + s.split(":", 1)[1].strip())
            continue
        if s.startswith("; FEATURE:"):
            f = s.split(":", 1)[1].strip()
            out.append(";TYPE:" + FEATURES.get(f, f))
            continue
        if s.startswith("; LINE_WIDTH:"):
            out.append(";WIDTH:" + s.split(":", 1)[1].strip())
            continue
        if s.startswith("M83"):
            rel = True
        elif s.startswith("M82"):
            rel = False
        if s.startswith(("G2 ", "G3 ")):
            v = dict((a, float(b)) for a, b in _NUM.findall(s.split(";", 1)[0]))
            nx, ny = v.get("X", x), v.get("Y", y)
            pts = _arc(x, y, nx, ny, v.get("I", 0.0), v.get("J", 0.0), s.startswith("G2"))
            e = v.get("E")
            if e is not None and not rel:
                raise SystemExit("absolute-E arcs aren't handled (Bambu Studio writes M83)")
            done = 0.0
            for k, (px, py) in enumerate(pts):
                seg = f"G1 X{px:.3f} Y{py:.3f}"
                if e is not None:
                    # the last piece takes the remainder, so the arc's filament is kept exactly
                    share = round(e / len(pts), 6) if k < len(pts) - 1 else round(e - done, 6)
                    done += share
                    seg += f" E{share:.6f}"
                if k == 0 and "F" in v:
                    seg += f" F{v['F']:.0f}"
                out.append(seg)
            x, y = nx, ny
            continue
        if s.startswith(("G0 ", "G1 ")):
            for a, b in _NUM.findall(s.split(";", 1)[0]):
                if a == "X":
                    x = float(b)
                elif a == "Y":
                    y = float(b)
        out.append(s)
    return out


def read(path):
    p = Path(path)
    if p.suffix == ".3mf" or p.name.endswith(".gcode.3mf"):
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.startswith("Metadata/plate_") and n.endswith(".gcode"))
            return z.read(name).decode("utf-8", "replace").splitlines()
    return p.read_text(errors="replace").splitlines()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="a Bambu .gcode.3mf or .gcode")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    lines = convert(read(a.src))
    Path(a.out).write_text("\n".join(lines) + "\n")
    print(f"{a.out}: {sum(1 for s in lines if s == ';LAYER_CHANGE')} layers")


if __name__ == "__main__":
    main()
