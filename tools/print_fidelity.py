#!/usr/bin/env python3
"""Print fidelity: does the slice keep the detail the model (and its renders) show?

    python3 tools/print_fidelity.py --part body.stl:#7A3E33 --part trim.stl:#EFE6D2 ...
    python3 tools/print_fidelity.py model.stl
    python3 tools/print_fidelity.py ... --overlay out.png     # render the misses

Scott, 2026-09-27: "We need to make sure the images that are produced can be
recreated in a print ... keep the quality and visual detail in the top of the
priority list."

A render shows the MODEL. The printer makes what the SLICER emits, and the two
part company in exactly the places a render makes look best: a raised detail
thinner than a bead is dropped by the slicer without a word, and an engraved
line narrower than a bead is closed over by the perimeters beside it. Neither
is an error anywhere else in the pipeline -- the mesh is valid, product_gate
passes, the slice has no supports -- and both are invisible in a render.

So this slices the real parts the way the P1S would (tools/virtual_printer.py,
one filament per colour part), rebuilds each layer's printed area from the
toolpath -- every extrusion as a bead of its own ;WIDTH: -- and compares it,
filament by filament, against the model's cross-section at the height the
slicer cut it:

  DROPPED  modelled, not printed. Only regions that reach the part's surface
           count; interior gaps are sparse infill and are meant to be there.
  FILLED   printed where the model has no material in that colour: a groove,
           gap or engraving the beads closed over, or one filament printing
           into another's part.

Both are reported as clusters followed across layers, with where they sit on
the model and how big they are, so a miss can be found and fixed in the .scad.

Honest limits: this is PrusaSlicer's toolpath (Bambu Studio is a fork; the
geometry decisions track closely, see virtual_printer.py), a bead is modelled
as a round-capped strip of its nominal width, and nothing thermal is modelled
-- a detail that is in the toolpath can still sag, string or blob.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import shapely
import trimesh
from shapely.geometry import MultiLineString, Polygon, MultiPolygon, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import virtual_printer  # noqa: E402

# Feature types that are not the part. Everything else -- perimeters, infill,
# gap fill, bridges, ironing -- is.
NOT_PART = {"Support material", "Support material interface", "Skirt/Brim",
            "Skirt", "Brim", "Wipe tower", "Custom", "Prime tower"}

# The outer bead is placed so its edge lands ON the model outline; the numbers
# below are what "on" means once G-code rounding (0.001mm) and a round-capped
# bead meeting a sharp model corner are allowed for.
TOL = 0.06          # mm of slack at every outline
REACH = 0.12        # mm a miss must extend past the other outline to count
MIN_AREA = 0.004    # mm^2 per layer below which a region is not reported
SURFACE = 0.3       # mm: a DROPPED region must come this close to the outline
BED_CENTRE = (128.0, 128.0)
PLANE = 0.09        # mm either side of the slicing plane a miss must hold
# What a miss has to be to need a look. Calibrated on the chapel Scott printed
# and called great on detail (2026-09-27): 157 misses, none wider than 0.4 mm
# or bigger than 0.6 mm3 -- rounded tower corners and block ends that do not
# show on the part. A dropped feature (the 0.1 mm rib) is lost across its
# whole width, so width and volume together catch it without the noise.
FLAG_WIDTH = 0.5    # mm
FLAG_VOLUME = 1.0   # mm3
# REACH, not an opening, separates noise from detail (2026-09-27). The first
# version opened every miss by 0.05 mm to remove the hairline slivers left
# along an outline -- and so deleted every feature under 0.1 mm wide, which is
# exactly the class of detail that fails. A sliver is thin AND shallow: it
# never gets more than TOL from the printed edge. A dropped rib is thin but
# deep. So a miss counts when some part of it lies REACH beyond the other
# outline, however thin it is.

_NUM = re.compile(r"([XYZE])([-+]?\d*\.?\d+)")


# ── G-code ────────────────────────────────────────────────────────────────
def parse_gcode(path):
    """Layers of printed beads: [{z, h, beads: {(tool, width): [polyline]}}]."""
    layers, cur = [], None
    x = y = z = 0.0
    e_last, rel = 0.0, False
    tool, ftype, width = 0, "", 0.42
    run, run_key = [], None

    def close_run():
        nonlocal run, run_key
        if cur is not None and len(run) >= 2 and run_key is not None:
            cur["beads"].setdefault(run_key, []).append(run)
        run, run_key = [], None

    with open(path, "r", errors="replace") as fh:
        for line in fh:
            if line[0] == ";":
                if line.startswith(";LAYER_CHANGE"):
                    close_run()
                    cur = {"z": None, "h": None, "beads": {}}
                    layers.append(cur)
                elif line.startswith(";Z:") and cur is not None:
                    cur["z"] = float(line[3:])
                elif line.startswith(";HEIGHT:") and cur is not None and cur["h"] is None:
                    # First HEIGHT after the change is the layer's own; later
                    # ones are bridges reporting their own thickness.
                    cur["h"] = float(line[8:])
                elif line.startswith(";TYPE:"):
                    close_run()
                    ftype = line[6:].strip()
                elif line.startswith(";WIDTH:"):
                    close_run()
                    width = float(line[7:])
                continue
            if line[0] == "T" and line[1:2].isdigit():
                close_run()
                tool = int(re.match(r"T(\d+)", line).group(1))
                continue
            if line.startswith("M83"):
                rel = True
                continue
            if line.startswith("M82"):
                rel = False
                continue
            if line.startswith("G92"):
                m = re.search(r"E([-+]?\d*\.?\d+)", line)
                if m:
                    e_last = float(m.group(1))
                continue
            if not (line.startswith("G1 ") or line.startswith("G0 ")):
                continue
            body = line.split(";", 1)[0]
            nx, ny, ne = x, y, None
            for a, v in _NUM.findall(body):
                v = float(v)
                if a == "X":
                    nx = v
                elif a == "Y":
                    ny = v
                elif a == "Z":
                    z = v
                else:
                    ne = v
            moved = nx != x or ny != y
            forward = ne is not None and ((ne > 1e-9) if rel else (ne > e_last + 1e-9))
            if ne is not None and not rel:
                e_last = ne
            if moved and forward and ftype not in NOT_PART and cur is not None:
                key = (tool, round(width, 3))
                if run and run_key == key and run[-1] == (x, y):
                    run.append((nx, ny))
                else:
                    close_run()
                    run, run_key = [(x, y), (nx, ny)], key
            elif moved:
                close_run()
            x, y = nx, ny
    close_run()
    return [L for L in layers if L["beads"] and L["z"] is not None]


def printed_area(beads):
    """{tool: Polygon} of everything that tool laid down on one layer."""
    per_tool = defaultdict(list)
    for (tool, w), runs in beads.items():
        per_tool[tool].append(MultiLineString(runs).buffer(w / 2.0, quad_segs=3))
    return {t: _valid(unary_union(g)) for t, g in per_tool.items()}


# ── model ─────────────────────────────────────────────────────────────────
def _load(path):
    m = trimesh.load(str(path), force="mesh")
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(tuple(m.geometry.values()))
    return m


def section(mesh, z):
    """The model's filled cross-section at height z, as shapely geometry.

    Two independent builds, united, because each has been caught dropping a
    loop the other keeps (2026-09-27):
      * trimesh's Path2D lost one of three loops touching at a corner -- the
        post office's parcel top, three gold quadrants meeting at the string;
      * GEOS's build_area lost a 0.05 mm rib joined to its wall, on some
        layers and not others.
    Both failures are MISSING area, never invented area, so the union is
    right wherever either is. Every miss is then confirmed against the mesh
    itself (see _confirmed), which catches anything both get wrong.
    """
    lines = trimesh.intersections.mesh_plane(mesh, [0, 0, 1], [0, 0, z])
    if lines is None or len(lines) == 0:
        return Polygon()
    segs = np.round(np.asarray(lines)[:, :, :2], 4)
    segs = segs[np.any(segs[:, 0] != segs[:, 1], axis=1)]
    if not len(segs):
        return Polygon()
    parts = [shapely.build_area(shapely.node(MultiLineString([q.tolist() for q in segs])))]
    try:
        sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sec is not None:
            T = np.eye(4)
            T[2, 3] = -z
            planar, _ = sec.to_2D(to_2D=T, check=False)
            parts += [shapely.make_valid(q) for q in planar.polygons_full if q.area > 0]
    except Exception:
        pass
    return _valid(unary_union([shapely.make_valid(q) for q in parts if not q.is_empty]))


def _confirmed(mesh, p, z, inside, n=5):
    """Ask the mesh directly: is this miss inside the model (dropped) or
    outside it (filled)? Majority of a few points spread over the region."""
    pts = [p.representative_point()]
    minx, miny, maxx, maxy = p.bounds
    rng = np.random.default_rng(0)
    tries = 0
    while len(pts) < n and tries < 60:
        tries += 1
        c = shapely.Point(rng.uniform(minx, maxx), rng.uniform(miny, maxy))
        if p.contains(c):
            pts.append(c)
    got = mesh.contains([[q.x, q.y, z] for q in pts])
    return (got.sum() if inside else (~got).sum()) * 2 > len(pts)


def _valid(g):
    """Snap to 1 micron and repair. The bakery's clapboard produced a section
    GEOS refused to difference ("TopologyException: side location conflict");
    a micron grid is a four-hundredth of a bead and removes it."""
    if g.is_empty:
        return g
    return shapely.make_valid(shapely.set_precision(g, 0.001))


def _parts(g):
    if g.is_empty:
        return []
    return list(g.geoms) if hasattr(g, "geoms") else [g]


def _reaches(p, far):
    """True when part of p lies outside `far` -- the other outline grown by REACH."""
    rest = p.difference(far)
    return not rest.is_empty and rest.area > 1e-5


# ── the comparison ────────────────────────────────────────────────────────
def compare(parts, workdir, supports=True, log=print):
    """parts: [(path, '#hex')]. Returns the report dict."""
    workdir = Path(workdir)
    meshes = [(_load(p), c.upper()) for p, c in parts]
    # One filament per distinct colour, numbered in first-seen order -- the
    # same rule tools/assemble_3mf.py writes into the 3MF it slices.
    slots = {}
    for _, c in meshes:
        slots.setdefault(c, len(slots))
    by_tool = defaultdict(list)
    for m, c in meshes:
        by_tool[slots[c]].append(m)
    tool_mesh = {t: trimesh.util.concatenate(ms) for t, ms in by_tool.items()}
    whole = trimesh.util.concatenate([m for m, _ in meshes])

    gcode = workdir / "fidelity.gcode"
    if len(slots) > 1:
        import assemble_3mf
        src = workdir / "fidelity_src.3mf"
        assemble_3mf.assemble(src, [[(Path(p), c) for p, c in parts]], "assembly")
        extra = virtual_printer.mmu_options(len(slots))
        # With a wipe tower, PrusaSlicer refuses to slice supports unless they
        # print from whichever filament is already loaded (0 = "current").
        extra.update({"support-material-extruder": "0",
                      "support-material-interface-extruder": "0"})
    else:
        src = Path(parts[0][0])
        extra = None
    # Pin where the slicer puts the part rather than inferring it afterwards.
    # Inferring it from the printed footprint's bounds was wrong by exactly the
    # thing this tool measures: when the outermost feature is a thin rib that
    # prints short, the whole model shifts toward it and every wall on that
    # side reads as a miss (2026-09-27, on the calibration block).
    extra = dict(extra or {}, center=f"{BED_CENTRE[0]},{BED_CENTRE[1]}")
    log(f"slicing {len(meshes)} part(s), {len(slots)} filament(s) ...")
    virtual_printer.slice_model(src, gcode, supports=supports, extra=extra)
    layers = parse_gcode(gcode)
    log(f"{len(layers)} layers parsed")

    # Where the slicer put the part. It re-centres on the bed, so the offset is
    # measured, not assumed: the printed footprint's bounds against the model's.
    lo, hi = whole.bounds[0], whole.bounds[1]
    off = np.array([BED_CENTRE[0] - (lo[0] + hi[0]) / 2, BED_CENTRE[1] - (lo[1] + hi[1]) / 2])
    z0 = lo[2]
    pts = np.array([xy for L in layers for runs in L["beads"].values() for r in runs for xy in r])
    seen = np.array([(pts[:, 0].min() + pts[:, 0].max()) / 2, (pts[:, 1].min() + pts[:, 1].max()) / 2])
    if np.abs(seen - off - (lo[:2] + hi[:2]) / 2).max() > 1.0:
        raise RuntimeError(
            f"the slice is not centred where it was asked to be (printed centre "
            f"{seen.round(2)}, model centre {((lo[:2] + hi[:2]) / 2 + off).round(2)}); "
            "every comparison would be offset, so stopping here")

    events = []          # (kind, tool, z_bottom, h, polygon in model XY)
    area_model = defaultdict(float)
    for li, L in enumerate(layers):
        h = L["h"] or 0.2
        zc = L["z"] - h / 2 + z0
        printed = {t: shapely.affinity.translate(g, -off[0], -off[1])
                   for t, g in printed_area(L["beads"]).items()}
        for t, m in tool_mesh.items():
            if not (m.bounds[0][2] < zc < m.bounds[1][2]):
                continue
            model = section(m, zc)
            got = printed.get(t, Polygon())
            if model.is_empty and got.is_empty:
                continue
            area_model[t] += model.area * h
            # A flat face lying ON the slicing plane is a tie: the slicer and
            # this section can land on opposite sides of it, and the chapel's
            # first report was mostly those -- whole floors "dropped" and sills
            # "filled" on exactly one layer. Only a miss that holds a little
            # above and below the plane is real, so compare against the model
            # present at both heights (dropped) or at either (filled).
            below, above = section(m, zc - PLANE), section(m, zc + PLANE)
            sure = _valid(model.intersection(below).intersection(above))
            maybe = _valid(unary_union([model, below, above]))
            dropped = sure.difference(got.buffer(TOL, quad_segs=3))
            if not dropped.is_empty:
                skin = model.boundary.buffer(SURFACE, quad_segs=2)
                far = got.buffer(REACH, quad_segs=3)
                for p in _parts(dropped):
                    if (p.area >= MIN_AREA and p.intersects(skin) and _reaches(p, far)
                            and _confirmed(m, p, zc, inside=True)):
                        events.append(("dropped", t, zc - h / 2, h, p))
            filled = got.difference(maybe.buffer(TOL, quad_segs=3))
            if not filled.is_empty:
                far = maybe.buffer(REACH, quad_segs=3)
                for p in _parts(filled):
                    if (p.area >= MIN_AREA and _reaches(p, far)
                            and _confirmed(m, p, zc, inside=False)):
                        events.append(("filled", t, zc - h / 2, h, p))
        if li % 100 == 0:
            log(f"  layer {li}/{len(layers)}")

    return _summarise(events, area_model, whole, slots, layers), events


def _where(c, bounds):
    """Plain-words location of a point on the model."""
    (x0, y0, z0), (x1, y1, z1) = bounds
    fx = (c[0] - x0) / max(x1 - x0, 1e-6)
    fy = (c[1] - y0) / max(y1 - y0, 1e-6)
    side = min((fy, "front"), (1 - fy, "back"), (fx, "left"), (1 - fx, "right"))[1]
    return side


def _summarise(events, area_model, whole, slots, layers):
    """Follow each miss up through the layers it spans."""
    colour_of = {v: k for k, v in slots.items()}
    clusters = []
    open_ = {}   # (kind, tool) -> list of clusters touched on the last layer
    for kind, t, zb, h, p in sorted(events, key=lambda e: e[2]):
        key = (kind, t)
        joined = None
        for c in open_.get(key, []):
            if abs(c["z1"] - zb) < 1e-3 + h * 1.01 and c["last"].buffer(0.3).intersects(p):
                joined = c
                break
        if joined is None:
            joined = {"kind": kind, "tool": t, "z0": zb, "z1": zb, "vol": 0.0,
                      "cx": 0.0, "cy": 0.0, "w": 0.0, "last": p, "layers": 0,
                      "width": 0.0, "polys": []}
            clusters.append(joined)
            open_.setdefault(key, []).append(joined)
        a = p.area
        joined["cx"] += p.centroid.x * a
        joined["cy"] += p.centroid.y * a
        joined["w"] += a
        joined["vol"] += a * h
        joined["z1"] = zb + h
        joined["last"] = p
        joined["layers"] += 1
        # Widest point of the miss: twice the largest inscribed radius.
        joined["width"] = max(joined["width"], 2 * _inscribed(p))
        joined["polys"].append((zb, h, p))
    out = []
    for c in clusters:
        cx, cy = c["cx"] / c["w"], c["cy"] / c["w"]
        out.append({
            "kind": c["kind"], "colour": colour_of[c["tool"]], "tool": c["tool"] + 1,
            "volume_mm3": round(c["vol"], 3),
            "z_mm": [round(c["z0"], 2), round(c["z1"], 2)], "layers": c["layers"],
            "at_xy": [round(cx, 1), round(cy, 1)],
            "side": _where((cx, cy), whole.bounds),
            "max_width_mm": round(c["width"], 2),
            "_polys": c["polys"],
        })
    for c in out:
        c["flag"] = c["max_width_mm"] >= FLAG_WIDTH or c["volume_mm3"] >= FLAG_VOLUME
    out.sort(key=lambda c: (not c["flag"], -c["volume_mm3"]))
    tot = defaultdict(float)
    for c in out:
        tot[c["kind"]] += c["volume_mm3"]
    vol = sum(area_model.values())
    return {
        "layers": len(layers),
        "model_volume_mm3": round(vol, 1),
        "dropped_mm3": round(tot["dropped"], 2),
        "filled_mm3": round(tot["filled"], 2),
        "flagged": sum(c["flag"] for c in out),
        "clusters": out,
    }


def _inscribed(p):
    """Radius of the largest circle inside p (cheap bound via distance)."""
    try:
        return shapely.maximum_inscribed_circle(p, tolerance=0.01).length
    except Exception:
        return 0.0


def misses_mesh(clusters, kind, grow=0.12, min_vol=0.0):
    """The misses as a solid you can render over the model."""
    meshes = []
    for c in clusters:
        if c["kind"] != kind or c["volume_mm3"] < min_vol:
            continue
        for zb, h, p in c["_polys"]:
            g = p.buffer(grow, quad_segs=2)
            for q in _parts(g):
                try:
                    m = trimesh.creation.extrude_polygon(q, h)
                    m.apply_translation([0, 0, zb])
                    meshes.append(m)
                except Exception:
                    continue
    return trimesh.util.concatenate(meshes) if meshes else None


def print_report(rep, top=15):
    print(f"\nPRINT FIDELITY  ({rep['layers']} layers, model {rep['model_volume_mm3']} mm3)")
    print(f"  dropped (modelled, not printed): {rep['dropped_mm3']} mm3")
    print(f"  filled  (printed, not modelled): {rep['filled_mm3']} mm3")
    print(f"  flagged for review (>= {FLAG_WIDTH} mm wide or >= {FLAG_VOLUME} mm3): {rep['flagged']}")
    shown = [c for c in rep["clusters"]][:top]
    if not shown:
        print("  no misses above the reporting floor")
    for c in shown:
        print(f"  {'FLAG ' if c['flag'] else '     '}{c['kind']:7s} {c['colour']} slot {c['tool']}  {c['volume_mm3']:8.3f} mm3  "
              f"z {c['z_mm'][0]}-{c['z_mm'][1]} ({c['layers']} layers)  "
              f"{c['side']} at {c['at_xy']}  up to {c['max_width_mm']} mm wide")
    n = len(rep["clusters"])
    if n > top:
        print(f"  ... {n - top} smaller")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mesh", nargs="?", help="a single-colour model")
    ap.add_argument("--part", action="append", default=[], metavar="PATH:#HEX",
                    help="a colour part; repeat once per part")
    ap.add_argument("--no-supports", action="store_true")
    ap.add_argument("--json", help="write the report here")
    ap.add_argument("--overlay", help="render the model with misses marked (PNG)")
    ap.add_argument("--keep", help="directory for the G-code and miss meshes")
    a = ap.parse_args(argv)
    parts = []
    for spec in a.part:
        path, _, col = spec.rpartition(":")
        parts.append((path, col if col.startswith("#") else "#" + col))
    if a.mesh:
        parts.append((a.mesh, "#999999"))
    if not parts:
        ap.error("give a mesh or at least one --part")

    work = Path(a.keep) if a.keep else Path(tempfile.mkdtemp(prefix="fidelity_"))
    work.mkdir(parents=True, exist_ok=True)
    rep, _ = compare(parts, work, supports=not a.no_supports)
    print_report(rep)
    if a.json:
        clean = dict(rep, clusters=[{k: v for k, v in c.items() if k != "_polys"}
                                    for c in rep["clusters"]])
        Path(a.json).write_text(json.dumps(clean, indent=1))
    if a.overlay:
        args = []
        for p, _ in parts:
            args += ["--part", f"{p}:0.78,0.76,0.72"]
        for kind, rgb in (("dropped", "0.90,0.10,0.10"), ("filled", "0.10,0.35,0.95")):
            m = misses_mesh(rep["clusters"], kind)
            if m is not None:
                f = work / f"{kind}.stl"
                m.export(str(f))
                args += ["--part", f"{f}:{rgb}"]
        import subprocess
        subprocess.run([sys.executable, str(Path(__file__).parent / "blender_render.py"),
                        *args, "-o", a.overlay, "--views", "--front=-y",
                        "--samples", "48", "--no-cache"], check=True)
    return rep


if __name__ == "__main__":
    main()
