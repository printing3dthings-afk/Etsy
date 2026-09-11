#!/usr/bin/env python3
"""
tools/print_check.py -- the checks tools/mesh_gate.py cannot do, via Blender's
own official 3D-Print Toolbox (`object_print3d_utils`, ships with Blender).

WHY THIS EXISTS (2026-09-11). mesh_gate covers build volume, watertightness,
winding, volume sign, body count, degenerate faces, terracing and overhang --
and has TWO BLIND SPOTS that matter for a printed part:

  SELF-INTERSECTION. A mesh whose surface passes through itself is watertight
  by every test mesh_gate makes. It gates PASSED. A slicer then has to guess
  which side is inside. Found on real shipped models here the first time this
  ran: tombstone_stone 11 intersecting faces, mochi_fox_organizer 38.

  WALL THICKNESS. The classic 3D-print check, and mesh_gate has nothing for
  it. Reported, never failed on -- carved lettering, fine relief and sharp
  detail legitimately measure "thin", so the number needs a person. Same
  treatment mesh_gate already gives overhang, for the same reason.

Both sliced without complaint in PrusaSlicer, so this is not a claim that
those parts are broken -- it is a claim that nothing was LOOKING. A check
that only reports what it already expected to find is not a gate.

Exit code is non-zero for non-manifold edges, bad contiguous edges, or
self-intersection. Thin/zero/sharp/overhang counts are reported only.

    python3 tools/print_check.py model.stl [--thickness 1.2] [--strict]
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPT = r'''
import bpy, addon_utils, sys, json
addon_utils.enable("object_print3d_utils", default_set=True)
from object_print3d_utils import report

path, thickness, angle = sys.argv[sys.argv.index("--")+1:][:3]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
ext = path.lower().rsplit(".", 1)[-1]
{"stl": bpy.ops.wm.stl_import, "obj": bpy.ops.wm.obj_import,
 "ply": bpy.ops.wm.ply_import}[ext](filepath=path)
o = bpy.context.view_layer.objects.active
# modifier/operator work refuses on multi-user data from a fresh import
o.data = o.data.copy()
bpy.ops.object.select_all(action='DESELECT')
o.select_set(True)
bpy.context.view_layer.objects.active = o
s = bpy.context.scene.print_3d
s.thickness_min = float(thickness)
s.angle_overhang = float(angle)
bpy.ops.mesh.print3d_check_all()
out, odd = {}, []
for msg, _payload in report.info():
    k, sep, v = msg.rpartition(":")
    try:
        if not sep: raise ValueError(msg)
        out[k.strip()] = int(v)
    except ValueError:
        # One unparseable entry must not abort every other check. Carry it back
        # so it is visible rather than silently dropped.
        odd.append(msg)
print("PRINT3D_JSON " + json.dumps({"counts": out, "unparsed": odd}))
'''

FAIL_KEYS = ("Non Manifold Edges", "Bad Contiguous Edges", "Intersect Face")


class PrintCheckError(Exception):
    pass


def check(mesh_path: Path, thickness: float = 1.2, overhang_deg: float = 45.0,
          timeout: int = 900) -> tuple[dict, list]:
    exe = shutil.which("blender")
    if not exe:
        raise PrintCheckError(
            "blender is not installed -- this wraps Blender's own 3D-Print "
            "Toolbox. apt-get install -y blender (~25MB).")
    mesh_path = Path(mesh_path)
    if not mesh_path.exists():
        raise PrintCheckError(f"mesh not found: {mesh_path}")
    if mesh_path.suffix.lower() not in (".stl", ".obj", ".ply"):
        raise PrintCheckError(
            f"unsupported extension {mesh_path.suffix!r}; this container's Blender "
            f"has no 3MF importer -- check the STL you exported alongside it.")
    sp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                         encoding="utf-8") as f:
            f.write(_SCRIPT)
            sp = Path(f.name)
        r = subprocess.run(
            [exe, "-b", "--python", str(sp), "--", str(mesh_path),
             str(thickness), str(90.0 - overhang_deg)],
            # errors="replace": a crash line or an odd filename byte must not
            # turn a decode error into an exit code that looks like a real
            # mesh failure.
            capture_output=True, text=True, errors="replace", timeout=timeout)
        m = re.search(r"PRINT3D_JSON (\{.*\})\s*$", (r.stdout or "") + (r.stderr or ""),
                      re.MULTILINE)
        if not m:
            raise PrintCheckError(
                f"blender exited {r.returncode} without reporting:\n"
                + ((r.stderr or r.stdout or "").strip()[-1500:]))
        payload = json.loads(m.group(1))
        counts, unparsed = payload["counts"], payload["unparsed"]
        # THE GATE'S OWN GATE. `bad` is only ever set from keys that are
        # PRESENT, so a report that silently lost them would print PASSED for a
        # mesh nothing actually checked -- reproduced: an empty report exits 0.
        # A missing required key is a tool failure, never a pass.
        missing = [k for k in FAIL_KEYS if k not in counts]
        if missing:
            raise PrintCheckError(
                "blender ran but did not report " + ", ".join(missing)
                + " -- refusing to call this a pass. "
                + (f"unparsed: {unparsed}" if unparsed else
                   "the 3D-Print Toolbox message format may have changed."))
        return counts, unparsed
    except subprocess.TimeoutExpired:
        raise PrintCheckError(f"timed out after {timeout}s -- a dense mesh makes "
                              f"the self-intersection test expensive")
    except (json.JSONDecodeError, KeyError, TypeError, OSError) as exc:
        raise PrintCheckError(f"could not read blender's report ({type(exc).__name__}: {exc})")
    finally:
        if sp is not None:
            sp.unlink(missing_ok=True)


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mesh")
    ap.add_argument("--thickness", type=float, default=1.2,
                    help="Minimum wall thickness in mm. Reported, not failed on.")
    ap.add_argument("--overhang", type=float, default=45.0,
                    help="Overhang angle from vertical, degrees. Reported only.")
    ap.add_argument("--strict", action="store_true",
                    help="Also exit non-zero when any thin wall is reported.")
    a = ap.parse_args()
    try:
        res, unparsed = check(Path(a.mesh), a.thickness, a.overhang)
    except PrintCheckError as exc:
        # exit 2 = the check could not be made. exit 1 = the mesh failed it.
        # Keeping these apart matters: a crash that exits 1 is indistinguishable
        # from a real defect to anything gating on the exit code.
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    bad = False
    print(f"{a.mesh}")
    for m in unparsed:
        print(f"  warn  unparsed report line: {m}")
    for k, v in res.items():
        hard = k in FAIL_KEYS
        flag = "FAIL" if (hard and v) else ("warn" if v else "ok  ")
        if hard and v:
            bad = True
        print(f"  {flag}  {k}: {v}")
    if a.strict and res.get("Thin Faces", 0):
        bad = True
    print("FAILED" if bad else "PASSED")
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    _cli()
