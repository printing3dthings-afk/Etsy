#!/usr/bin/env python3
"""
tools/blender_model.py -- author real geometry in headless Blender, the way
tools/openscad_render.py authors it in OpenSCAD.

WHEN TO REACH FOR THIS INSTEAD OF OpenSCAD (Scott's standing call,
2026-09-11: "if it's something that you know would do better in blender use
it and vice versa"). The choice is mine to make per design, and the line is
not about which tool is nicer -- it is about what the shape IS:

  OpenSCAD, and it is not close: anything DIMENSIONED. Mechanical parts,
  snap-fits, threads, boxes, shelves, organizers, signs, plates, anything a
  customer's measurement has to fit, anything that must stay resizable by
  changing one number. CGAL booleans are reliable; Blender's documented
  ones are not (bug T66593, and a SHARP remesh handed this repo a
  non-watertight mesh on its first real attempt, 2026-09-11).

  Blender, and equally not close: a form with NO describable swept, lofted
  or revolved profile. True organic double-curvature -- a creature, a
  sculpted figure, a soft blobby character. CSG cannot express those, and
  the cost of pretending otherwise is written all over
  mochi_fox_organizer.scad: three separate failed attempts to place ONE eye
  recess, because a hull-chain's real surface cannot be predicted from its
  control points and had to be measured out of an exported mesh each time.

  The hybrid, when a design is both: Blender builds the organic shell,
  OpenSCAD does the dimensioned cuts on the imported STL. Never the reverse
  -- do not run Blender booleans over an OpenSCAD-built structure.

THE CONTRACT. You write a Python script that builds geometry with bpy and
leaves it in the scene; this wrapper clears the scene first, injects PARAMS,
then joins every mesh object, triangulates, CHECKS THE RESULT IS WATERTIGHT,
and exports. The manifold check is the point: non-manifold output is
Blender's characteristic failure, the way a silently-ignored module is
OpenSCAD's, so this refuses a bad mesh and deletes it rather than handing
back something a gate would have to catch later.

Three bpy traps this wrapper already handles, each of which cost a failed
run when found (Blender 4.0.2):
  - bpy.ops attribute access is LAZY, so hasattr(bpy.ops.wm, "stl_export")
    returns True for an operator that does not exist. 4.0.2 has
    wm.stl_import but export is still export_mesh.stl -- not symmetric.
  - modifier_apply refuses with "Modifiers cannot be applied to multi-user
    data" on a freshly imported mesh; the datablock needs copying first.
  - the importer does not reliably leave its object active AND selected.

Standalone:  python3 tools/blender_model.py model.py -o out.stl -D size=40
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BLENDER_APT_PACKAGE = "blender"


class BlenderModelError(Exception):
    pass


_PREAMBLE = '''
import bpy, bmesh, sys, math, mathutils, json

_argv = sys.argv[sys.argv.index("--")+1:]
OUT_PATH = _argv[0]
PARAMS = json.loads(_argv[1])

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for _d in (bpy.data.meshes, bpy.data.metaballs, bpy.data.textures):
    for _x in list(_d):
        _d.remove(_x)

def solo(o):
    """Make o the single active+selected object with single-user mesh data --
    the state modifier_apply and most operators actually require."""
    bpy.ops.object.select_all(action='DESELECT')
    if o.data is not None and o.data.users > 1:
        o.data = o.data.copy()
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    return o

def bake(o):
    """Apply location/rotation/scale into the mesh so the object sits at identity.

    DO THIS TO ANYTHING THAT WILL BE JOINED OR USED AS A BOOLEAN CUTTER. join()
    keeps only the ACTIVE object's transform and rewrites everyone else into its
    frame -- so a cutter cloud whose first member carried a rotation ends up
    with that rotation applied to the whole cloud about the origin. Cost here:
    11 face recesses placed by raycast, each one correct, collectively swung out
    to x -35.6..38.7 and the boolean then subtracted the entire model (0 tris).
    Baking first makes join() a pure merge with nothing left to reinterpret.
    """
    solo(o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o

def join_all(objs, name=None):
    """Bake every object, then join. The bake is not optional -- see bake()."""
    for o in objs:
        bake(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    if name:
        o.name = name
    return solo(o)

def apply_all(o):
    solo(o)
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    return o
'''

_EPILOGUE = '''
_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not _objs:
    print("MODEL_ERR no mesh objects in the scene"); raise SystemExit(3)
bpy.ops.object.select_all(action='DESELECT')
for _o in _objs:
    _o.select_set(True)
bpy.context.view_layer.objects.active = _objs[0]
if len(_objs) > 1:
    bpy.ops.object.join()
_obj = bpy.context.view_layer.objects.active
solo(_obj)
if "tri_final" not in [m.name for m in _obj.modifiers]:
    _obj.modifiers.new("tri_final", 'TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier="tri_final")

_bm = bmesh.new(); _bm.from_mesh(_obj.data)
_open = len([e for e in _bm.edges if not e.is_manifold])
_loose = len([v for v in _bm.verts if not v.link_edges])
_bm.free()
bpy.ops.export_mesh.stl(filepath=OUT_PATH)
print("MODEL_STATS " + json.dumps({
    "tris": len(_obj.data.polygons), "verts": len(_obj.data.vertices),
    "nonmanifold_edges": _open, "loose_verts": _loose,
}))
print("MODEL_OK")
'''


def check_blender_available() -> tuple[bool, str]:
    exe = shutil.which("blender")
    if not exe:
        return False, (f"blender is not installed. Install it with "
                       f"apt-get install -y {BLENDER_APT_PACKAGE} (~25MB).")
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return False, f"blender found at {exe} but --version failed: {exc}"
    return True, (r.stdout or r.stderr or "").strip().splitlines()[0]


def build_model(script_src: str, output_path: Path, params: dict | None = None,
                timeout: int = 900, allow_nonmanifold: bool = False) -> dict:
    """Run script_src in headless Blender and export the result to output_path
    (.stl). Returns the stats dict. Raises BlenderModelError on any failure,
    including a non-watertight result unless allow_nonmanifold is set."""
    available, info = check_blender_available()
    if not available:
        raise BlenderModelError(info)
    exe = shutil.which("blender")

    output_path = Path(output_path)
    if output_path.suffix.lower() != ".stl":
        raise BlenderModelError(
            f"output must be .stl, got {output_path.suffix!r} -- this container's "
            f"Blender 4.0.2 exports STL via export_mesh.stl and has no 3MF exporter."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.unlink(missing_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(_PREAMBLE + "\n" + script_src + "\n" + _EPILOGUE)
        script_path = Path(f.name)
    try:
        cmd = [exe, "-b", "--python", str(script_path), "--",
               str(output_path), json.dumps(params or {})]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise BlenderModelError(
                f"blender timed out after {timeout}s -- a remesh at too fine a voxel "
                f"size or too many metaball elements are the usual causes")
        out = (r.stdout or "") + (r.stderr or "")
        if "MODEL_OK" not in out:
            raise BlenderModelError(
                f"blender exited {r.returncode} without completing the model:\n"
                + out.strip()[-2500:])
        stats = json.loads(out.split("MODEL_STATS ", 1)[1].splitlines()[0])
        # Anything the model script printed itself. Without this the guarded
        # failures below swallow print() debugging, which cost a whole cycle the
        # first time one fired -- an error that hides the evidence is worse than
        # the error.
        said = "\n".join(l for l in out.splitlines()
                          if l.startswith(("PROBE", "INFO", "WARN", "DEBUG")))
        # Echo the script's own prints ALWAYS, not only on a guarded failure.
        # Hiding them on success cost two debugging cycles: a run that returned
        # 12 triangles looked like a success and swallowed every PROBE line
        # explaining why.
        if said:
            print(said, file=sys.stderr)
        said = ("\nscript output:\n" + said) if said else ""
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise BlenderModelError(f"no/empty mesh written to {output_path}")
        # An empty result is not a "built" model. The first real use of this
        # wrapper returned tris=0 and it still printed success, because the
        # manifold check passes trivially on nothing -- a guard that only looks
        # for its expected failure mode will wave through every other one.
        if stats["tris"] == 0:
            output_path.unlink(missing_ok=True)
            raise BlenderModelError(
                "the script produced an EMPTY mesh (0 triangles). Usual causes: a "
                "Boolean DIFFERENCE whose cutter swallowed the whole object or had "
                "inverted normals, or a smoothing modifier that collapsed the mesh. "
                "Build without the boolean first and check the triangle count, then "
                "add one operation back at a time." + said)
        if stats["nonmanifold_edges"] and not allow_nonmanifold:
            # Blender's characteristic failure. Delete it: leaving a
            # plausible-looking STL on disk is worse than failing, because the
            # next command to touch that path gets a broken model with no
            # warning attached (same reasoning as openscad_render.py).
            output_path.unlink(missing_ok=True)
            raise BlenderModelError(
                f"result is NOT watertight: {stats['nonmanifold_edges']} open edges. "
                f"This is Blender's characteristic failure, not a fluke -- a SHARP "
                f"remesh produced exactly this on its first real use here. Prefer "
                f"VOXEL remesh, avoid Boolean modifiers, and check that every "
                f"metaball/primitive actually overlaps its neighbour. Mesh deleted; "
                f"pass allow_nonmanifold=True only to inspect a known-bad result." + said)
        return stats
    finally:
        script_path.unlink(missing_ok=True)


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Author geometry in headless Blender.")
    ap.add_argument("script", nargs="?", help="Python file building geometry with bpy")
    ap.add_argument("-o", "--output", help="Output .stl path")
    ap.add_argument("-D", "--define", action="append", default=[], metavar="K=V",
                    help="A PARAMS entry; values are parsed as JSON, else kept as a string")
    ap.add_argument("--allow-nonmanifold", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check or not args.script:
        ok, info = check_blender_available()
        print(f"{'available' if ok else 'NOT available'}: {info}")
        raise SystemExit(0 if ok else 1)
    params = {}
    for d in args.define:
        k, _, v = d.partition("=")
        try:
            params[k] = json.loads(v)
        except json.JSONDecodeError:
            params[k] = v
    out = Path(args.output or Path(args.script).with_suffix(".stl"))
    try:
        stats = build_model(Path(args.script).read_text(), out, params,
                            timeout=args.timeout,
                            allow_nonmanifold=args.allow_nonmanifold)
    except BlenderModelError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"built -> {out}  {stats}")


if __name__ == "__main__":
    _cli()
