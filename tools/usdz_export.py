#!/usr/bin/env python3
"""
tools/usdz_export.py -- write a USDZ next to a mesh so it opens in iOS Quick Look.

WHY (2026-09-13, Scott's request). Tapping a .usdz in the iOS Files app opens it
rotatable, full screen, with no app and no import step. STL and 3MF do not do
that. For reviewing a print on a phone, that removes the whole "open an app,
navigate to the file" step, which is what actually kills the habit.

BLENDER 4.0.2 CANNOT DO THIS. Ubuntu's build ships with no USD support at all --
`bpy.ops.wm.usd_export` does not exist (confirmed live, the op list is empty).
An official blender.org build (5.x) is required. Point BLENDER_USD at one, or
let the module find a `blender` on PATH that actually has the operator.

THREE THINGS THAT ARE WRONG BY DEFAULT AND ARE FIXED HERE:

1. `convert_scene_units='MILLIMETERS'` is the trap. It ASSUMES the Blender scene
   is in metres, so it multiplies the geometry by 1000 AND writes
   metersPerUnit=0.001. Those cancel: a 212mm bowl lands in AR as a 212 METRE
   bowl (measured). This shop's meshes are already authored numerically in mm,
   so the geometry is scaled by 0.001 here and exported as plain METERS.
2. Blender is Z-up; USD and Quick Look are Y-up. Without convert_orientation
   every model lies on its side.
3. The exporter bundles the world material as an EXR texture even with
   export_materials=False -- a near-black `color_0C0C0C.exr`, which renders the
   model as a dark blob. convert_world_material=False is what actually drops it.

Verified on sauce_bowl.stl: geometry round-trips exactly (35,796 triangles,
volume 308960.223 identical), and the exported stage reports upAxis=Y,
metersPerUnit=1.0, real-world extent 212.3 x 22.2 x 189.9 mm against the STL's
212.3 x 189.9 x 22.1 (Y/Z swap is the Y-up conversion, as intended).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPT = r'''
import bpy, sys, json
args = json.loads(sys.argv[sys.argv.index("--") + 1])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
IMPORTERS = {".stl": bpy.ops.wm.stl_import, ".obj": bpy.ops.wm.obj_import,
             ".ply": bpy.ops.wm.ply_import}
for src in args["inputs"]:
    IMPORTERS[src.lower()[src.rfind("."):]](filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not objs:
    print("USDZ_ERR nothing imported"); raise SystemExit(3)
# Preview decimation. A USDZ is for LOOKING at on a phone, never for printing --
# the STL/3MF next to it is the print file. Uncapped, drapery_vase would ship a
# 261k-triangle package that is slow to open on a handset for detail no phone
# screen can resolve. Small models are left exactly alone.
cap = args.get("max_tris", 0)
if cap:
    total = sum(len(o.data.polygons) for o in objs)
    if total > cap:
        for o in objs:
            bpy.context.view_layer.objects.active = o
            m = o.modifiers.new("dec", "DECIMATE")
            m.ratio = max(0.02, cap / total)
            bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
    o.scale = (0.001, 0.001, 0.001)      # mm -> metres; see module docstring
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.wm.usd_export(
    filepath=args["output"],
    export_materials=False,
    convert_world_material=False,        # else a near-black EXR ships with it
    convert_scene_units='METERS',
    convert_orientation=True,            # Blender Z-up -> USD/Quick Look Y-up
    export_global_up_selection='Y',
    export_global_forward_selection='NEGATIVE_Z',
)
try:
    from pxr import Usd, UsdGeom
    st = Usd.Stage.Open(args["output"])
    mpu = UsdGeom.GetStageMetersPerUnit(st)
    sz = UsdGeom.BBoxCache(0, ['default']).ComputeWorldBound(
        st.GetPseudoRoot()).ComputeAlignedRange().GetSize()
    print("USDZ_OK " + json.dumps({
        "up": str(UsdGeom.GetStageUpAxis(st)), "meters_per_unit": mpu,
        "mm": [round(s * mpu * 1000, 1) for s in sz],
        "tris": sum(len(o.data.loop_triangles) for o in objs
                    if o.data.calc_loop_triangles() is None or True)}))
except Exception as exc:
    print("USDZ_OK " + json.dumps({"note": f"stage not re-read: {exc}"}))
'''


class USDZError(Exception):
    pass


def find_blender_with_usd() -> str | None:
    """A `blender` on PATH is not enough -- Ubuntu's has no USD at all."""
    for cand in (os.environ.get("BLENDER_USD"), shutil.which("blender")):
        if not cand or not Path(cand).exists():
            continue
        try:
            r = subprocess.run(
                [cand, "-b", "--python-expr",
                 "import bpy;print('HASUSD', hasattr(bpy.ops.wm,'usd_export') "
                 "and 'usd_export' in dir(bpy.ops.wm))"],
                capture_output=True, text=True, timeout=180)
            if "HASUSD True" in (r.stdout or ""):
                return cand
        except Exception:
            continue
    return None


def export_usdz(inputs, output_path, timeout: int = 900, max_tris: int = 40000) -> dict:
    exe = find_blender_with_usd()
    if not exe:
        raise USDZError(
            "no Blender with USD export found. Ubuntu's blender 4.0.2 is built "
            "without USD (bpy.ops.wm.usd_export does not exist). Download an "
            "official build from download.blender.org and set BLENDER_USD to it.")
    inputs = [str(Path(p)) for p in (inputs if isinstance(inputs, (list, tuple)) else [inputs])]
    for p in inputs:
        if not Path(p).exists():
            raise USDZError(f"input not found: {p}")
        if Path(p).suffix.lower() not in (".stl", ".obj", ".ply"):
            raise USDZError(f"unsupported input {Path(p).suffix!r}; Blender has no 3MF "
                            f"importer -- build the USDZ from the model's STL part(s)")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(_SCRIPT)
        sp = Path(f.name)
    try:
        r = subprocess.run(
            [exe, "-b", "--python", str(sp), "--",
             json.dumps({"inputs": inputs, "output": str(output_path), "max_tris": max_tris})],
            capture_output=True, text=True, errors="replace", timeout=timeout)
        out = (r.stdout or "") + (r.stderr or "")
        if "USDZ_OK" not in out:
            raise USDZError(f"blender exited {r.returncode} without exporting:\n"
                            + out.strip()[-1500:])
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise USDZError(f"blender reported success but wrote nothing to {output_path}")
        line = [l for l in out.splitlines() if l.startswith("USDZ_OK")][-1]
        return json.loads(line[len("USDZ_OK "):] or "{}")
    except subprocess.TimeoutExpired:
        raise USDZError(f"timed out after {timeout}s")
    finally:
        sp.unlink(missing_ok=True)


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("inputs", nargs="*", help="One or more .stl/.obj/.ply to put in one USDZ")
    ap.add_argument("-o", "--output", help="Output .usdz (default: alongside the first input)")
    ap.add_argument("--max-tris", type=int, default=40000,
                    help="Decimate the PREVIEW above this triangle count (0 = never). The "
                         "STL/3MF beside it stays the print file; this is only for viewing.")
    ap.add_argument("--check", action="store_true", help="Report whether a USD-capable Blender exists")
    a = ap.parse_args()
    if a.check:
        exe = find_blender_with_usd()
        print(f"USD-capable blender: {exe}" if exe else
              "no USD-capable blender (Ubuntu's 4.0.2 has none -- set BLENDER_USD)")
        raise SystemExit(0 if exe else 1)
    if not a.inputs:
        ap.error("give at least one input mesh")
    out = Path(a.output) if a.output else Path(a.inputs[0]).with_suffix(".usdz")
    try:
        info = export_usdz(a.inputs, out, max_tris=a.max_tris)
    except USDZError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    mm = info.get("mm")
    print(f"{out}  {out.stat().st_size // 1024} KB"
          + (f"  {mm[0]} x {mm[1]} x {mm[2]} mm  up={info.get('up')}" if mm else ""))


if __name__ == "__main__":
    _cli()
