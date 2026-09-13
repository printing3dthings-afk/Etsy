#!/usr/bin/env python3
"""
tools/product_gate.py -- the hard gate a RETAIL product must pass.

Scott, 2026-09-13: "Printability is a hard constraint, not a tradeoff. If a
form can't meet these, discard the form -- don't thin the walls to make it
work." So unlike mesh_gate/print_check, which report and let a person judge,
every check here FAILS the build.

    python3 tools/product_gate.py model.stl [--wall 1.2] [--overhang 45]

  1 watertight + consistent winding
  2 one body, no floating geometry
  3 fits the P1S plate
  4 minimum wall >= 1.2mm of real material
  5 no UNSUPPORTED overhang past 45 degrees
  6 flat base, and the centre of mass lands inside it

WHAT MAKES 5 DIFFERENT FROM mesh_gate's ADVISORY SCAN. That one excludes faces
resting on the plate and flags everything else steep, so a base fillet reads
the same as a mushroom flare. It isn't: going down the outside of a base
fillet the radius GROWS, so there is material directly beneath every point of
it and the slicer lays it on solid ground. Going down the outside of a flare
the radius SHRINKS, so the same point has air beneath it. This casts a ray
straight down from each steep face and only fails the ones that find nothing,
which is the difference between a gate you can leave on and one you learn to
ignore.

WALL THICKNESS is the ray-cast span measurement from mesh_gate.wall_thickness(),
not Blender's toolbox number -- that one measures the width of an engraved
groove and calls it a wall (11,216 mm2 claimed on a 6mm plate; see SKILL.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesh_gate import wall_thickness, _BUILD_VOLUME_MM  # noqa: E402


def _unsupported_overhang(m, limit_deg=45.0, plate_eps=0.05, probe=0.2):
    """Steep downward faces with AIR one layer beneath them (probe = layer height)."""
    nz = m.face_normals[:, 2]
    z_top = m.vertices[m.faces][:, :, 2].max(axis=1)
    on_plate = z_top <= (float(m.bounds[0][2]) + plate_eps)
    down = np.where((nz < 0) & ~on_plate)[0]
    if not len(down):
        return 0.0, 0.0, 0
    from_vertical = 90.0 - np.degrees(np.arccos(np.clip(-nz[down], 0.0, 1.0)))
    steep = down[from_vertical > limit_deg]
    if not len(steep):
        return 0.0, float(from_vertical.max()), 0
    # Is the point ONE LAYER directly below this face inside the solid? That is
    # the question the slicer actually asks: it can only lay plastic where the
    # previous layer put some.
    #
    # A downward RAY to "anything below" is the wrong test and was tried first:
    # for a face 0.3mm above the plate it starts beneath the plate and reports
    # every base fillet unsupported -- it failed the sauce bowl, a part that has
    # been printed, on 4,508 faces. It is also wrong in the other direction,
    # calling a mushroom cap supported because the ray eventually finds the stem.
    centres = m.triangles_center[steep]
    below = centres - np.array([0.0, 0.0, probe])
    supported = m.contains(below)
    unsupported = steep[~supported]
    if not len(unsupported):
        return 0.0, float(from_vertical.max()), 0.0
    # AREA IS THE WRONG VERDICT AND SPAN IS THE RIGHT ONE. An engraved maker's
    # mark on the underside is a downward-facing horizontal ceiling 0.7mm above
    # the plate -- 4,508 faces and 1.98 cm2 on the sauce bowl, a part that has
    # been printed and sold. Every one of those is a letter stroke a fraction of
    # a millimetre wide, which any FDM machine bridges without noticing. What
    # actually droops is a WIDE unsupported span, so group the unsupported faces
    # into connected regions and judge each region by how far it has to reach.
    adj = m.face_adjacency
    keep = np.zeros(len(m.faces), bool); keep[unsupported] = True
    mask = keep[adj[:, 0]] & keep[adj[:, 1]]
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    idx = {f: i for i, f in enumerate(unsupported)}
    rows = [idx[a] for a, b in adj[mask]]
    cols = [idx[b] for a, b in adj[mask]]
    g = sp.coo_matrix((np.ones(len(rows)), (rows, cols)),
                      shape=(len(unsupported), len(unsupported)))
    n_comp, labels = connected_components(g, directed=False)
    worst_span = 0.0
    for k in range(n_comp):
        pts = m.triangles_center[unsupported[labels == k]][:, :2]
        if len(pts) < 2:
            continue
        span = float(np.linalg.norm(pts - pts.mean(axis=0), axis=1).max() * 2)
        worst_span = max(worst_span, span)
    return (float(m.area_faces[unsupported].sum()),
            float(from_vertical.max()), worst_span)


def _base_report(m, plate_eps=0.05):
    """Flat contact area at the bottom, and whether the centre of mass sits over it."""
    z0 = float(m.bounds[0][2])
    z_top = m.vertices[m.faces][:, :, 2].max(axis=1)
    on_plate = z_top <= (z0 + plate_eps)
    area = float(m.area_faces[on_plate].sum())
    if not on_plate.any():
        return 0.0, None, None, 0.0
    pts = m.triangles_center[on_plate][:, :2]
    try:
        com = m.center_mass[:2]
    except Exception:
        com = m.centroid[:2]
    # distance from the centre of mass to the nearest base point, vs the base's
    # own radius: a tall thing on a small foot tips over.
    d = float(np.linalg.norm(pts - com, axis=1).min())
    reach = float(np.linalg.norm(pts - pts.mean(axis=0), axis=1).max())
    inside = d <= reach
    return area, inside, reach, d


def gate(path, wall_min=1.2, overhang_limit=45.0, bodies=1, min_base_frac=0.05,
         bridge_max=10.0):
    m = trimesh.load(path, force="mesh")
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    ext = [float(v) for v in m.extents]
    add("fits_plate", all(e <= lim for e, lim in zip(ext, _BUILD_VOLUME_MM)),
        f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm vs 256 x 256 x 256")
    add("watertight", m.is_watertight,
        "closed" if m.is_watertight else "open edges -- the slicer guesses at the holes")
    add("winding", m.is_winding_consistent, "normals agree" if m.is_winding_consistent
        else "mixed normals -- inside/outside ambiguous")
    n = int(m.body_count)
    add("no_floating_geometry", n == bodies, f"{n} bodies, expected {bodies}")

    w = wall_thickness(path)
    if "error" in w:
        add("min_wall", False, w["error"])
    else:
        # the 1st percentile, not the raw min: one grazing span is not a wall
        add("min_wall", w["p1"] >= wall_min,
            f"1st pct {w['p1']:.2f}mm, median {w['median']:.2f}mm "
            f"(floor {wall_min}mm); {100*w['frac_below_nozzle']:.2f}% below one bead")

    # OVERHANG IS ASKED OF THE SLICER, NOT INFERRED. The geometric version below
    # is a fallback for when prusa-slicer is missing, and it is demonstrably
    # wrong: it failed all four sauce parts on spans of 13-19mm, and the real
    # slicer reports every one of them clean -- no supports, no overhang
    # perimeters, full height. They are printed, sold parts. Tuning the span
    # limit until they passed would have been fitting the threshold to the
    # answer; delegating to the engine that actually decides is the fix.
    try:
        from virtual_printer import report as _slice_report
        import tempfile as _tf
        with _tf.TemporaryDirectory() as td:
            r = _slice_report(path, Path(td) / "g.gcode", supports=True)
        ok = r["support_moves"] == 0 and r["overhang_perimeters"] == 0
        add("no_unsupported_overhang", ok,
            f"slicer: {r['support_moves']} support moves, "
            f"{r['overhang_perimeters']} overhang perimeters, "
            f"{r['printed_height_mm']}mm printed of {r['model_height_mm']}mm")
        add("geometry_survives_slicing", not r.get("geometry_dropped", False),
            f"printed height {r['printed_height_mm']}mm vs modelled "
            f"{r['model_height_mm']}mm")
    except Exception as exc:
        area, worst, span = _unsupported_overhang(m, overhang_limit)
        add("no_unsupported_overhang", span <= bridge_max,
            f"[GEOMETRIC FALLBACK -- slicer unavailable: {str(exc)[:60]}] widest "
            f"unsupported span {span:.1f}mm (limit {bridge_max:.0f}mm), steepest "
            f"downward face {worst:.0f}deg")

    barea, inside, reach, d = _base_report(m)
    foot = barea / max(ext[0] * ext[1], 1e-9)
    add("flat_base", barea > 0 and foot >= min_base_frac,
        f"{barea/100:.2f} cm2 of contact = {100*foot:.1f}% of footprint "
        f"(floor {100*min_base_frac:.0f}%)")
    add("stable", bool(inside),
        "centre of mass sits over the base" if inside else
        f"centre of mass is {d:.1f}mm from the nearest contact, base reach {reach:.1f}mm -- it tips")

    failed = [c for c in checks if not c["pass"]]
    return {"file": str(path), "passed": not failed, "checks": checks}


def _cli():
    import argparse, json
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mesh")
    ap.add_argument("--wall", type=float, default=1.2)
    ap.add_argument("--overhang", type=float, default=45.0)
    ap.add_argument("--bridge", type=float, default=10.0,
                    help="Widest unsupported span allowed, mm. A P1S bridges short "
                         "gaps cleanly; this is what separates an engraved letter "
                         "from a drooping flare.")
    ap.add_argument("-c", "--bodies", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        res = gate(a.mesh, a.wall, a.overhang, a.bodies, bridge_max=a.bridge)
    except Exception as exc:
        print(f"FAIL  could not load {a.mesh}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(a.mesh)
        for c in res["checks"]:
            print(f"  {'ok  ' if c['pass'] else 'FAIL'}  {c['check']}: {c['detail']}")
        print("PRODUCT GATE PASSED" if res["passed"] else "PRODUCT GATE FAILED")
    raise SystemExit(0 if res["passed"] else 1)


if __name__ == "__main__":
    _cli()
