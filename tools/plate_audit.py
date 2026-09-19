#!/usr/bin/env python3
"""Check every viewer plate against the P1S's real printable area.

    python3 tools/plate_audit.py                     # audit all 72 plates
    python3 tools/plate_audit.py sundial mushroom    # just those
    python3 tools/plate_audit.py --json              # machine-readable

Exits non-zero if any plate has geometry the P1S could not actually lay down.

WHERE THE NUMBERS COME FROM. Not from memory -- from Bambu's own shipped
slicer profiles, read 2026-09-19:

  resources/profiles/BBL/machine/fdm_bbl_3dp_001_common.json
      printable_area      0x0, 256x0, 256x256, 0x256
  resources/profiles/BBL/machine/Bambu Lab P1S 0.4 nozzle.json
      bed_exclude_area    0x0, 18x0, 18x28, 0x28

So the P1S's origin is the FRONT-LEFT corner of the plate, the usable square
is the full 256x256, and an 18 x 28 mm rectangle in that front-left corner is
reserved -- it is where the toolhead parks and wipes, and Bambu Studio will
not let an object sit there. The common profile reserves a bigger L-shaped
region; the P1S overrides it with the smaller rectangle, which is why the
override is the one this reads.

WHY THE INDEX BBOX IS THE WRONG THING TO CHECK. tools/viewer/jobs/index.js
carries one bbox per plate and it includes the skirt and the wipe tower, both
of which sit well outside the part. Checking that number flags 29 of 72 plates
as misaligned, and nearly every one of them is a false alarm. This decodes the
toolpath and splits it by feature type instead, so a part that fits is not
reported just because its skirt is wide -- and a skirt that genuinely runs off
the front of the plate is reported as exactly that, separately from the part.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gcode_to_mesh import _decode, load_payload  # noqa: E402

BED = 256.0
EXCLUDE = (0.0, 0.0, 18.0, 28.0)   # P1S bed_exclude_area, front-left corner

SKIRT = "Skirt/Brim"
WIPE = "Wipe tower"
# The part's own outline. Centring has to be judged against this and not
# against every extrusion on the plate: support material only grows on the
# overhanging side, so part-plus-supports sits 1-3 mm off the outline's
# middle on 24 of these plates and every one of them is correctly arranged.
OUTLINE = ("External perimeter", "Perimeter", "Overhang perimeter")

# Bambu Studio's auto-arrange puts a single object in the middle of the plate.
# Half a bead of drift is rounding in the 0.01mm payload quantisation; a
# centimetre is a plate somebody moved and did not re-centre.
CENTRE_TOL = 1.0


def _bbox(pts, polys, keep):
    # `if keep else polys` here was a real bug: an empty set is falsy, so a
    # plate with no wipe tower got the whole toolpath's bbox reported as its
    # wipe tower and failed the audit against its own skirt.
    sel = polys[np.isin(polys[:, 0], list(keep))]
    if not len(sel):
        return None
    idx = np.concatenate([np.arange(s, s + n) for _, s, n in sel])
    p = pts[idx]
    return [float(p[:, 0].min()), float(p[:, 1].min()),
            float(p[:, 0].max()), float(p[:, 1].max())]


def audit(path: Path) -> dict:
    payload = load_payload(path)
    pts = _decode(payload["pts"], np.int16).reshape(-1, 2).astype(float) / 100.0
    polys = _decode(payload["polys"], np.int32).reshape(-1, 3)
    types = payload["types"]

    present = set(int(t) for t in np.unique(polys[:, 0]))
    skirt = {i for i in present if types[i] == SKIRT}
    wipe = {i for i in present if types[i] == WIPE}
    part = present - skirt - wipe
    outline = {i for i in present if types[i] in OUTLINE}

    out = {
        "plate": path.stem,
        "name": payload.get("name", path.stem),
        "part": _bbox(pts, polys, part),
        "skirt": _bbox(pts, polys, skirt),
        "wipe": _bbox(pts, polys, wipe),
        "outline": _bbox(pts, polys, outline),
        "errors": [],
        "warnings": [],
    }

    def off_plate(box, what):
        if box is None:
            return
        if box[0] < 0 or box[1] < 0 or box[2] > BED or box[3] > BED:
            return ("%s runs off the plate: x %.2f..%.2f  y %.2f..%.2f "
                    "(plate is 0..%.0f both ways)"
                    % (what, box[0], box[2], box[1], box[3], BED))

    err = off_plate(out["part"], "the part")
    if err:
        out["errors"].append(err)
    err = off_plate(out["wipe"], "the wipe tower")
    if err:
        out["errors"].append(err)
    # A skirt off the edge does not wreck the part, but it is the machine
    # being asked to extrude past its own bed, and it means the part is too
    # close to the edge to run a skirt at all.
    err = off_plate(out["skirt"], "the skirt")
    if err:
        out["warnings"].append(err + " -- print this one with the skirt off")

    for box, what in ((out["part"], "the part"), (out["wipe"], "the wipe tower")):
        if box is None:
            continue
        if box[0] < EXCLUDE[2] and box[1] < EXCLUDE[3]:
            out["errors"].append(
                "%s reaches into the reserved front-left corner "
                "(%.0f x %.0f mm): starts at x %.2f, y %.2f"
                % (what, EXCLUDE[2], EXCLUDE[3], box[0], box[1]))

    if out["outline"]:
        cx = (out["outline"][0] + out["outline"][2]) / 2
        cy = (out["outline"][1] + out["outline"][3]) / 2
        out["centre"] = [round(cx, 2), round(cy, 2)]
        out["centre_offset"] = round(max(abs(cx - BED / 2), abs(cy - BED / 2)), 2)
        # Multi-colour plates carry a wipe tower, and arrange centres the
        # part-plus-tower group, not the part -- so an off-centre part is
        # correct there and flagging it would be noise.
        if out["centre_offset"] > CENTRE_TOL and not out["wipe"]:
            out["warnings"].append(
                "part is %.2f mm off the middle of the plate (centre %.2f, %.2f)"
                % (out["centre_offset"], cx, cy))
    if out["part"]:
        out["size"] = [round(out["part"][2] - out["part"][0], 2),
                       round(out["part"][3] - out["part"][1], 2)]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plates", nargs="*", help="plate ids (default: all of them)")
    ap.add_argument("--jobs", default="tools/viewer/jobs", type=Path)
    ap.add_argument("--json", action="store_true", help="dump the full report")
    a = ap.parse_args(argv)

    if a.plates:
        paths = [a.jobs / (p if p.endswith(".js") else p + ".js") for p in a.plates]
    else:
        paths = sorted(p for p in a.jobs.glob("*.js") if p.stem != "index")

    reports = []
    for p in paths:
        if not p.exists():
            print("no such plate: %s" % p, file=sys.stderr)
            return 2
        reports.append(audit(p))

    if a.json:
        print(json.dumps(reports, indent=2))
    else:
        for r in reports:
            if not r["errors"] and not r["warnings"]:
                continue
            print("%s  (%s)" % (r["plate"], r["name"]))
            if r.get("size"):
                print("    part %.1f x %.1f mm" % tuple(r["size"]))
            for e in r["errors"]:
                print("    FAIL  " + e)
            for w in r["warnings"]:
                print("    warn  " + w)

    bad = [r for r in reports if r["errors"]]
    warned = [r for r in reports if r["warnings"]]
    print("\n%d plates audited against the P1S printable area "
          "(0..256 mm, %0.f x %0.f mm front-left corner reserved)"
          % (len(reports), EXCLUDE[2], EXCLUDE[3]))
    print("%d cannot print as arranged, %d with warnings"
          % (len(bad), len(warned)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
