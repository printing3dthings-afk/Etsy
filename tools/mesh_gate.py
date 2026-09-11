#!/usr/bin/env python3
"""Pass/fail gate for an exported mesh, run BEFORE it goes to a slicer or to Scott.

    python3 tools/mesh_gate.py openscad_models/sauce_bowl.stl
    python3 tools/mesh_gate.py model.stl --components 4 --json
    python3 tools/mesh_gate.py model.stl --overhang        # adds the 55-degree scan

Exit code 0 = every check passed, 1 = at least one FAIL. INFO lines never fail.

Written 2026-09-06. These exact trimesh checks had been retyped by hand for every
model in the openscad_models/ tree (five in one session alone), which is how the
sauce bowl's cavity came within 0.09mm of breaching its own exterior before anyone
looked: an ad-hoc check only catches what the person remembered to type that day.
The checks themselves are not novel -- having ONE committed thing that returns a
non-zero exit code is the point.

Component count is an argument, not a constant: a print-in-place hinge is legitimately
multi-body, while a one-piece bowl showing 2 components means a cutter broke through.
Only the caller knows which it is, so the default of 1 is a floor, not an assumption.
"""
import argparse
import json
import sys

import numpy as np
import trimesh

# Bambu Lab P1S, per CLAUDE.md. A model over this cannot be printed at all, which is
# a harder failure than any geometry defect -- it is checked first for that reason.
_BUILD_VOLUME_MM = (256.0, 256.0, 256.0)

# Technique 35: 55 degrees is the STRUCTURAL limit, NOT the surface-quality one (a
# visible free surface wants 40 or under). Overhang is reported, never failed on, and
# that is deliberate: the first version failed all three of this shop's verified,
# already-sliced models, and every flagged face on the sauce tray turned out to be the
# 0.7mm-deep ceiling of the engraved maker's mark on its underside -- a bridge that
# short prints on any FDM machine. The angle alone cannot separate that from a real
# unsupported span, so the z range is printed and a human makes the call. A gate that
# cries wolf on good models is worse than no gate.
_OVERHANG_LIMIT_DEG = 55.0


def _load(path):
    m = trimesh.load(path, force="mesh")
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(tuple(m.geometry.values()))
    return m


def _overhang_report(m, plate_eps=0.05):
    """Unsupported downward-facing area beyond the structural limit.

    Technique 38: an outward-flaring overhang's normal points DOWN (nz < 0). Getting
    this sign backwards makes the scan silently find nothing on the exact geometry it
    exists to catch.

    Faces resting ON the build plate must be excluded or the scan is useless: the flat
    underside of any model is a perfectly downward face at the worst possible angle, so
    including it flagged all three verified, already-sliced models here at once (the
    sauce bowl's own 158 cm2 base). The plate supports those faces -- an overhang is
    only an overhang if there is air beneath it.
    """
    nz = m.face_normals[:, 2]
    z_top = m.vertices[m.faces][:, :, 2].max(axis=1)
    on_plate = z_top <= (float(m.bounds[0][2]) + plate_eps)
    down = (nz < 0) & ~on_plate
    if not down.any():
        return 0.0, 0.0, None
    # Measured from VERTICAL, the way a slicer states its limit: 0 = a sheer wall
    # (always printable), 90 = a flat ceiling with air under it (never printable).
    # arccos(-nz) gives the angle from HORIZONTAL, so this is its complement -- getting
    # that one subtraction wrong inverts the test into flagging the safest surfaces,
    # which is what it did against all three verified models before this line was fixed.
    from_horizontal = np.degrees(np.arccos(np.clip(-nz[down], 0.0, 1.0)))
    from_vertical = 90.0 - from_horizontal
    over = from_vertical > _OVERHANG_LIMIT_DEG
    areas = m.area_faces[down]
    if not over.any():
        return 0.0, float(from_vertical.max()), None
    z = m.triangles_center[np.where(down)[0][over]][:, 2]
    return float(areas[over].sum()), float(from_vertical.max()), (float(z.min()), float(z.max()))


def _terrace_report(m, layer_h=0.20, extr=0.42, flat_cutoff=50.0):
    """Upward-facing area whose slope is too shallow to hide a layer step.

    2026-09-08, from the first real printed sauce bowl. Its top face was a
    paraboloid rising 5.5mm over 95mm of radius, and it came off the plate
    ringed with 27 concentric terraces. Every check here passed it: the mesh
    was watertight, one body, in the envelope, and had no overhang. Nothing
    looked at whether a surface was shallow enough to STAIR-STEP.

    A surface of gradient g steps sideways by layer_h/g every layer. Under one
    extrusion the step blends away; much above it, it reads as a ring. So the
    band that matters is bounded at BOTH ends: below one bead is invisible, and
    a "terrace" wider than flat_cutoff means the surface is effectively flat --
    one clean top surface, which is the thing to aim for, not a defect. A
    genuinely flat face has gradient ~0 and lands outside the band by design.
    """
    n = m.face_normals
    up = n[:, 2] > 0.5
    if not up.any():
        return 0.0, 0.0
    grad = np.hypot(n[up, 0], n[up, 1]) / n[up, 2]
    with np.errstate(divide="ignore"):
        width = np.where(grad > 0, layer_h / np.maximum(grad, 1e-12), np.inf)
    stepped = (width > extr) & (width < flat_cutoff)
    if not stepped.any():
        return 0.0, 0.0
    areas = m.area_faces[up]
    return float(areas[stepped].sum()), float(width[stepped].max())


def gate(path, expected_components=1, check_overhang=False):
    m = _load(path)
    ext = [float(v) for v in m.extents]
    checks = []

    def add(name, passed, detail, fatal=True):
        checks.append({"check": name, "pass": bool(passed), "detail": detail,
                       "level": "FAIL" if fatal else "INFO"})

    fits = all(e <= lim + 1e-6 for e, lim in zip(ext, _BUILD_VOLUME_MM))
    add("fits_build_volume", fits,
        f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm vs P1S 256 x 256 x 256")

    add("watertight", m.is_watertight,
        "closed surface" if m.is_watertight else "open edges -- the slicer will guess at the holes")

    add("winding_consistent", m.is_winding_consistent,
        "normals agree" if m.is_winding_consistent else "mixed normals -- inside/outside is ambiguous")

    vol = float(m.volume) if m.is_volume else 0.0
    add("positive_volume", vol > 0, f"{vol / 1000.0:.2f} cm3")

    n_comp = int(m.body_count)
    add("component_count", n_comp == expected_components,
        f"{n_comp} separate bodies, expected {expected_components}")

    degenerate = int((m.area_faces <= 1e-12).sum())
    add("no_degenerate_faces", degenerate == 0, f"{degenerate} zero-area faces")

    area, worst = _terrace_report(m)
    add("terracing", True,
        f"{area / 100.0:.2f} cm2 of upward surface too shallow to hide a layer step "
        f"(worst terrace {worst:.2f} mm)" if area else "no shallow upward surface",
        fatal=False)

    if check_overhang:
        area, worst, zr = _overhang_report(m)
        where = f", z {zr[0]:.2f}-{zr[1]:.2f} mm" if zr else ""
        add("overhang", True,
            f"{area / 100.0:.2f} cm2 past {_OVERHANG_LIMIT_DEG:.0f} deg from vertical "
            f"(worst {worst:.1f} deg{where})", fatal=False)

    failed = [c for c in checks if not c["pass"] and c["level"] == "FAIL"]
    return {"file": path, "passed": not failed, "checks": checks,
            "bbox_mm": [round(e, 2) for e in ext]}


def gate_cutter(cutter_path, target_path, expect_multi_body=None):
    """Gate a boolean CUTTER against the TARGET it will be subtracted from.

    Exists because every check here is a failure that actually happened, most
    of them twice, and each was written down as prose that then got skipped at
    the moment of use. Prose does not run; this does.

    The findings behind each check (measured, see BLENDER_REFERENCE.md section 2):
      open cutter        -> result silently NON-MANIFOLD (172 open edges) and
                            its volume went UP
      flipped normals    -> silent NO-OP: target volume identical to 4 decimals,
                            face count changed, every gate still clean
      degenerate cutter  -> result silently non-manifold (2 open edges)
      no bbox overlap    -> a no-op, not an error. Cost an hour today: a cutter
                            placed from the target's bounding box instead of its
                            real surface simply missed it
      cutter encloses    -> the one legitimate empty result (A minus B where
                            B contains A). Catch it here, not after the boolean
      many bodies        -> a scattered/instanced cloud self-intersects, and
                            with use_self=False the Exact solver removed 100%
                            of a 112,183 mm3 stone and left 223 faces
    """
    c = _load(cutter_path)
    t = _load(target_path)
    checks = []

    def add(name, passed, detail, fatal=True):
        checks.append({"check": name, "pass": bool(passed), "detail": detail,
                       "level": "FAIL" if fatal else "INFO"})

    add("cutter_watertight", c.is_watertight,
        "closed" if c.is_watertight else
        "OPEN -- an open cutter makes the RESULT non-manifold even though the target went in clean")

    add("cutter_winding", c.is_winding_consistent,
        "normals agree" if c.is_winding_consistent else "mixed normals -- inside/outside is ambiguous")

    cvol = float(c.volume) if c.is_volume else 0.0
    if cvol > 0:
        vol_detail = f"{cvol / 1000.0:.3f} cm3"
    elif not c.is_watertight:
        # An open mesh has no meaningful signed volume. Saying "flipped normals"
        # here would send the reader after the wrong defect.
        vol_detail = "no enclosed volume -- follows from the open surface above, not a separate defect"
    else:
        vol_detail = (f"{cvol / 1000.0:.3f} cm3 -- FLIPPED NORMALS cut nothing and change "
                      f"the mesh anyway, silently")
    add("cutter_positive_volume", cvol > 0, vol_detail)

    deg = int((c.area_faces <= 1e-12).sum())
    add("cutter_no_degenerate_faces", deg == 0, f"{deg} zero-area faces")

    cb, tb = c.bounds, t.bounds
    overlap = all(cb[0][i] < tb[1][i] and tb[0][i] < cb[1][i] for i in range(3))
    add("bbox_overlaps_target", overlap,
        "cutter and target overlap" if overlap else
        "NO OVERLAP -- this boolean is a silent no-op; the cutter misses the target entirely")

    encloses = all(cb[0][i] <= tb[0][i] and cb[1][i] >= tb[1][i] for i in range(3))
    add("cutter_does_not_enclose_target", not encloses,
        "cutter is smaller than the target" if not encloses else
        "cutter ENCLOSES the target -- the difference is correctly EMPTY, which is "
        "almost always a placement or scale bug, not a Blender bug")

    bodies = int(c.body_count)
    if expect_multi_body is None:
        expect_multi_body = bodies > 1
    add("self_intersection_risk", True,
        (f"{bodies} bodies -- an instanced/scattered cloud. Set use_self=True on the "
         f"boolean (Blender) or expect a wrong result; run tools/print_check.py on the "
         f"cutter for the real self-intersection count"
         if bodies > 1 else "single body"),
        fatal=False)

    vol_ratio = (cvol / float(t.volume)) if (t.is_volume and t.volume > 0 and cvol > 0) else 0.0
    add("removal_scale", True,
        f"cutter is {vol_ratio * 100:.1f}% of target volume (upper bound on what it can remove)",
        fatal=False)

    failed = [x for x in checks if not x["pass"] and x["level"] == "FAIL"]
    return {"cutter": cutter_path, "target": target_path,
            "passed": not failed, "checks": checks,
            "cutter_bbox_mm": [round(float(v), 2) for v in c.extents],
            "target_bbox_mm": [round(float(v), 2) for v in t.extents]}


def main():
    ap = argparse.ArgumentParser(description="Pre-slice mesh gate (P1S).")
    ap.add_argument("mesh")
    ap.add_argument("-c", "--components", type=int, default=1,
                    help="Expected separate bodies (default 1; raise it for print-in-place assemblies)")
    ap.add_argument("--overhang", action="store_true", help="Also scan for unprintable overhangs")
    ap.add_argument("--cutter-for", metavar="TARGET",
                    help="Treat the mesh as a boolean CUTTER and gate it against TARGET "
                         "before running the boolean. Checks the failures that silently "
                         "produce a wrong result: open/flipped/degenerate cutter, a cutter "
                         "that misses the target, and one that encloses it.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    try:
        res = (gate_cutter(a.mesh, a.cutter_for) if a.cutter_for
               else gate(a.mesh, a.components, a.overhang))
    except Exception as exc:
        # A mesh that will not even load is a gate failure, never a stack trace the
        # caller has to interpret.
        if a.json:
            print(json.dumps({"file": a.mesh, "passed": False, "error": str(exc)}, indent=2))
        else:
            print(f"FAIL  could not load {a.mesh}: {exc}")
        sys.exit(1)

    if a.json:
        print(json.dumps(res, indent=2))
    else:
        if a.cutter_for:
            print(f"cutter {a.mesh}  [{' x '.join(f'{v:g}' for v in res['cutter_bbox_mm'])} mm]")
            print(f"target {a.cutter_for}  [{' x '.join(f'{v:g}' for v in res['target_bbox_mm'])} mm]")
        else:
            print(f"{a.mesh}  [{' x '.join(f'{v:g}' for v in res['bbox_mm'])} mm]")
        for c in res["checks"]:
            if not c["pass"]:
                tag = c["level"] + "  "
            elif c["level"] == "INFO":
                tag = "note"
            else:
                tag = "ok  "
            print(f"  {tag}  {c['check']}: {c['detail']}")
        print("PASSED" if res["passed"] else "FAILED")
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
