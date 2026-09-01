#!/usr/bin/env python3
"""
tools/blender_render.py -- headless Blender (GPLv3-compatible-use, system
binary, apt package `blender`) studio-lit review renders of a mesh file
(STL/OBJ/PLY -- whatever bpy's importers cover; NOT 3MF, see below).

Added 2026-09-01 per Scott's standing complaint about print quality
("some of your prints are too blocky... not enough real look to them") and
his own reposted collage naming Blender as one of the tools worth adding.
This is NOT a modeling tool -- OpenSCAD (openscad_render.py) stays the one
and only place .scad source gets written and meshes get produced, per this
shop's whole parametric-design pattern. This is purely a REVIEW step: turn
a finished STL into a realistically lit, shadowed, floor-contacted product
photo BEFORE calling a design done, the same "look at the actual output"
discipline this shop already applies to AI listing photos and to
render_openscad_model's own PNG preview.

Why this exists alongside openscad_render.py's own PNG preview: OpenSCAD's
preview is a flat, unlit, single-material orthographic-feeling view -- it
has repeatedly hidden real surface defects in this project (the cap's
shoulder seam survived twelve corrections partly because the flat preview
never cast a shadow that would have revealed it; a 53-degree overhang that
looked "fine" in preview only showed its droop on a REAL print). A studio
three-point-lit render with a floor and contact shadows is a much closer
proxy for "how will this actually look," without needing a real printer.

NOT for listing photos. CLAUDE.md's hard rule is that every Etsy listing
photo comes from an approved AI image engine (gpt-image-1/1.5/2, Gemini,
Ideogram, Grok) generated FROM the real product file -- this tool is for
Claude's own design review before a model is ever called finished, not a
substitute for that pipeline. Don't wire this into any listing/photo path
without Scott's explicit sign-off first.

3MF note: this container's Blender (4.0.2, apt) has no bundled 3MF
importer (confirmed live -- addon_utils lists none, and bpy.ops has no
*_3mf operator). Render from STL/OBJ; use openscad_render.py's fmt="3mf"
separately for the actual customer/Scott deliverable file, not for this.

Standalone: python3 tools/blender_render.py --check
            python3 tools/blender_render.py model.stl -o review.png
            python3 tools/blender_render.py model.stl -o review.png \
                --color 0.75,0.55,0.85 --azimuth 35 --elevation 28
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BLENDER_APT_PACKAGE = "blender"

_SCENE_SCRIPT = r'''
import bpy, sys, math, mathutils

argv = sys.argv[sys.argv.index("--")+1:]
stl_path, out_path, r, g, b, az_deg, el_deg, samples, res = argv
r, g, b = float(r), float(g), float(b)
az, el = math.radians(float(az_deg)), math.radians(float(el_deg))
samples = int(samples)
res = int(res)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

ext = stl_path.lower().rsplit(".", 1)[-1]
if ext == "stl":
    bpy.ops.wm.stl_import(filepath=stl_path)
elif ext == "obj":
    bpy.ops.wm.obj_import(filepath=stl_path)
elif ext == "ply":
    bpy.ops.wm.ply_import(filepath=stl_path)
else:
    raise SystemExit(f"unsupported mesh extension for Blender import: {ext}")

objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not objs:
    raise SystemExit("import produced no mesh objects -- check the input file")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = "part"

bpy.context.view_layer.update()
bb = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
cx = (min(xs) + max(xs)) / 2
cy = (min(ys) + max(ys)) / 2
size = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)
minz = min(zs)
obj.location.x -= cx
obj.location.y -= cy
obj.location.z -= minz

mat = bpy.data.materials.new("review_material")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
bsdf.inputs["Roughness"].default_value = 0.35
if "Specular IOR Level" in bsdf.inputs:
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
obj.data.materials.clear()
obj.data.materials.append(mat)

bpy.ops.mesh.primitive_plane_add(size=size * 6, location=(0, 0, 0))
floor = bpy.context.active_object
fmat = bpy.data.materials.new("floor")
fmat.use_nodes = True
fmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.93, 0.92, 0.90, 1)
fmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
floor.data.materials.append(fmat)

dist = size * 2.6
cam_x = dist * math.cos(el) * math.sin(az)
cam_y = -dist * math.cos(el) * math.cos(az)
cam_z = dist * math.sin(el) + size * 0.15
bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
cam = bpy.context.active_object
target = mathutils.Vector((0, 0, size * 0.28))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam
cam.data.lens = 85

def add_area(name, loc, energy, sz, target):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.active_object
    l.name = name
    l.data.energy = energy
    l.data.size = sz
    d = target - l.location
    l.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return l

o = mathutils.Vector((0, 0, size * 0.3))
scale = size / 60.0
add_area("key",  (size * 1.8, -size * 1.6, size * 2.2), 900 * scale, size * 0.9, o)
add_area("fill", (-size * 2.0, -size * 0.6, size * 1.2), 250 * scale, size * 1.2, o)
add_area("rim",  (0, size * 2.2, size * 1.6), 500 * scale, size * 0.9, o)

world = bpy.context.scene.world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.97, 0.97, 0.98, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = samples
scene.cycles.use_denoising = False  # this apt build has no OIDN -- confirmed live, errors if enabled
scene.render.resolution_x = res
scene.render.resolution_y = res
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print("BLENDER_RENDER_OK", out_path)
'''


class BlenderRenderError(Exception):
    """Raised for any Blender failure -- missing binary, bad/empty mesh
    input, or a non-zero render. Callers should surface str(exc) directly
    (matches OpenSCADError's convention in openscad_render.py)."""


def check_blender_available() -> tuple[bool, str]:
    """(is_available, version_or_error). Never raises."""
    exe = shutil.which("blender")
    if not exe:
        return False, (
            f"blender is not installed. Install it with "
            f"`apt-get install -y {BLENDER_APT_PACKAGE}` -- it's a system binary "
            f"(~25MB + deps via apt), not a pip package."
        )
    try:
        result = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=15)
        version = (result.stdout or result.stderr or "").splitlines()[0].strip()
        return True, version or "blender (version unknown)"
    except Exception as exc:  # noqa: BLE001
        return False, f"blender found at {exe} but --version failed: {exc}"


def render_review(
    mesh_path: Path,
    output_path: Path,
    color: tuple[float, float, float] = (0.8, 0.8, 0.82),
    azimuth: float = 35.0,
    elevation: float = 28.0,
    samples: int = 96,
    resolution: int = 1200,
    timeout: int = 300,
) -> Path:
    """Render a studio-lit three-quarter product photo of mesh_path (STL/
    OBJ/PLY) to output_path (PNG). Three-point area lighting, a matte
    plastic material in `color` (0-1 RGB), a floor plane for contact
    shadows, Cycles at `samples` (denoising forced off -- this container's
    Blender build has no OpenImageDenoiser, confirmed live: enabling it
    raises "Build without OpenImageDenoiser" and aborts the render).

    azimuth/elevation are degrees around the model (0 azimuth = camera on
    -Y looking toward +Y; increasing azimuth rotates the camera around Z).
    Defaults give a three-quarter hero angle that has worked well in
    practice -- override for a specific detail (e.g. azimuth=180 for a
    from-behind view, elevation=75 for a near-top-down check).

    Raises BlenderRenderError with an actionable message on any failure:
    binary missing, unsupported mesh extension, empty/missing mesh, a
    timeout, or a zero-byte output.
    """
    mesh_path = Path(mesh_path)
    if not mesh_path.exists():
        raise BlenderRenderError(f"mesh file not found: {mesh_path}")
    if mesh_path.suffix.lower() not in (".stl", ".obj", ".ply"):
        raise BlenderRenderError(
            f"unsupported mesh extension {mesh_path.suffix!r} -- this container's Blender "
            f"has no bundled 3MF importer (confirmed live); use .stl/.obj/.ply. For a 3MF "
            f"deliverable, render that separately via openscad_render.py's fmt='3mf'."
        )

    available, info = check_blender_available()
    if not available:
        raise BlenderRenderError(info)
    exe = shutil.which("blender")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(_SCENE_SCRIPT)
        script_path = Path(f.name)

    try:
        cmd = [
            exe, "-b", "--python", str(script_path), "--",
            str(mesh_path), str(output_path),
            str(color[0]), str(color[1]), str(color[2]),
            str(azimuth), str(elevation), str(samples), str(resolution),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise BlenderRenderError(
                f"blender render timed out after {timeout}s -- try lower `samples` or "
                f"`resolution` first (each ~doubling of samples roughly doubles render time)"
            )
        if result.returncode != 0 or "BLENDER_RENDER_OK" not in (result.stdout or ""):
            raise BlenderRenderError(
                f"blender exited {result.returncode} without a successful render: "
                f"{(result.stderr or result.stdout or 'no output').strip()[-2000:]}"
            )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise BlenderRenderError(
                f"blender exited 0 but produced no/empty output at {output_path}"
            )
        return output_path
    finally:
        script_path.unlink(missing_ok=True)


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Render a studio-lit review photo of a mesh file via headless Blender.")
    ap.add_argument("mesh_file", nargs="?", help="Path to a .stl/.obj/.ply mesh")
    ap.add_argument("-o", "--output", help="Output PNG path")
    ap.add_argument("--color", default="0.8,0.8,0.82", help="R,G,B 0-1 material color, e.g. 0.75,0.55,0.85")
    ap.add_argument("--azimuth", type=float, default=35.0)
    ap.add_argument("--elevation", type=float, default=28.0)
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--resolution", type=int, default=1200)
    ap.add_argument("--check", action="store_true", help="Just check whether blender is installed")
    args = ap.parse_args()

    if args.check or not args.mesh_file:
        available, info = check_blender_available()
        print(f"{'available' if available else 'NOT available'}: {info}")
        raise SystemExit(0 if available else 1)

    output = Path(args.output or Path(args.mesh_file).with_suffix(".review.png"))
    color = tuple(float(x) for x in args.color.split(","))
    try:
        render_review(Path(args.mesh_file), output, color=color,
                       azimuth=args.azimuth, elevation=args.elevation,
                       samples=args.samples, resolution=args.resolution)
    except BlenderRenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"rendered -> {output}")


if __name__ == "__main__":
    _cli()
