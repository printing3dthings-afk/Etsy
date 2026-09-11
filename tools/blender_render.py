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
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BLENDER_APT_PACKAGE = "blender"

_SCENE_SCRIPT = r'''
import bpy, sys, math, mathutils

import json

argv = sys.argv[sys.argv.index("--")+1:]
parts_json, out_path, az_deg, el_deg, samples, res, lens = argv
# [[path, [r,g,b]], ...] -- one entry is the ordinary single-colour case.
parts = json.loads(parts_json)
az, el = math.radians(float(az_deg)), math.radians(float(el_deg))
samples = int(samples)
res = int(res)
lens = float(lens)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

def _import(path):
    before = {o.name for o in bpy.context.scene.objects}
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "stl":
        bpy.ops.wm.stl_import(filepath=path)
    elif ext == "obj":
        bpy.ops.wm.obj_import(filepath=path)
    elif ext == "ply":
        bpy.ops.wm.ply_import(filepath=path)
    else:
        raise SystemExit(f"unsupported mesh extension for Blender import: {ext}")
    fresh = [o for o in bpy.context.scene.objects
             if o.name not in before and o.type == 'MESH']
    if not fresh:
        raise SystemExit(f"import produced no mesh objects from {path}")
    # One FILE is one colour region, so its own sub-objects get joined; separate
    # files never are, which is the whole point of the multi-part path.
    for o in fresh:
        o.select_set(True)
    bpy.context.view_layer.objects.active = fresh[0]
    if len(fresh) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active

built = []
for idx, (path, rgb) in enumerate(parts):
    bpy.ops.object.select_all(action='DESELECT')
    o = _import(path)
    o.name = f"part{idx}"
    mat = bpy.data.materials.new(f"filament{idx}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.5
    o.data.materials.clear()
    o.data.materials.append(mat)
    built.append(o)

# Frame the parts TOGETHER and shift them all by the same offset. Centring each
# one on its own bounding box would slide the pieces out of register with each
# other -- they are one object cut into colour regions, not separate models.
bpy.context.view_layer.update()
xs = []; ys = []; zs = []
for o in built:
    for c in o.bound_box:
        v = o.matrix_world @ mathutils.Vector(c)
        xs.append(v.x); ys.append(v.y); zs.append(v.z)
cx = (min(xs) + max(xs)) / 2
cy = (min(ys) + max(ys)) / 2
size = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)
minz = min(zs)
for o in built:
    o.location.x -= cx
    o.location.y -= cy
    o.location.z -= minz
obj = built[0]

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
# 85mm is a flattering product-shot lens and it CROPS A TALL PART -- the
# framing is dist = size*2.6 off the largest dimension, which does not
# account for how much of the silhouette a long axis fills at that focal
# length. Every render of a 118mm-tall model in this session lost its top.
cam.data.lens = lens

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


# --- render cache -----------------------------------------------------------
# A Cycles review render is 50-90s at the defaults and nothing skipped an
# unchanged one -- several were burned this session re-rendering the same mesh
# at a camera angle that was only wrong once. Keys on the real CONTENT of every
# mesh (not mtime, which a re-export bumps even when the geometry is identical)
# plus every parameter that changes a pixel.
_CACHE_SUFFIX = ".rendercache"


def _render_key(parts, color, azimuth, elevation, samples, resolution, lens) -> str | None:
    h = hashlib.sha256()
    try:
        for path, col in parts:
            pth = Path(path)
            h.update(str(pth.name).encode())
            h.update(pth.read_bytes())
            h.update(repr(tuple(col) if col is not None else None).encode())
    except OSError:
        return None
    h.update(repr((tuple(color), azimuth, elevation, samples, resolution, lens)).encode())
    return h.hexdigest()


def render_review(
    mesh_path: Path | list | tuple,
    output_path: Path,
    color: tuple[float, float, float] = (0.8, 0.8, 0.82),
    azimuth: float = 35.0,
    elevation: float = 28.0,
    samples: int = 96,
    resolution: int = 1200,
    lens: float = 85.0,
    timeout: int = 300,
    use_cache: bool = True,
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
    # mesh_path is either one mesh (the original single-colour call) or a list
    # of (path, (r,g,b)) pairs -- one per filament. Added 2026-09-11: this shop
    # sells genuinely multi-colour prints (the whole SS-series pipeline is about
    # which region gets which AMS slot) and a review renderer that can only show
    # one colour cannot answer "what does this look like printed".
    if isinstance(mesh_path, (list, tuple)):
        parts = [(Path(p), tuple(c)) for p, c in mesh_path]
        if not parts:
            raise BlenderRenderError("no parts given -- pass at least one (path, rgb) pair")
    else:
        parts = [(Path(mesh_path), tuple(color))]
    for mp, _ in parts:
        if not mp.exists():
            raise BlenderRenderError(f"mesh file not found: {mp}")
        if mp.suffix.lower() not in (".stl", ".obj", ".ply"):
            raise BlenderRenderError(
                f"unsupported mesh extension {mp.suffix!r} -- this container's Blender "
                f"has no bundled 3MF importer (confirmed live); use .stl/.obj/.ply. For a 3MF "
                f"deliverable, render that separately via openscad_render.py's fmt='3mf'."
            )

    available, info = check_blender_available()
    if not available:
        raise BlenderRenderError(info)
    exe = shutil.which("blender")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    key = _render_key(parts, color, azimuth, elevation, samples, resolution, lens) if use_cache else None
    meta_path = output_path.with_suffix(output_path.suffix + _CACHE_SUFFIX)
    if key:
        try:
            if (output_path.exists() and output_path.stat().st_size > 0
                    and json.loads(meta_path.read_text()).get("key") == key):
                return output_path
        except (OSError, ValueError):
            pass

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(_SCENE_SCRIPT)
        script_path = Path(f.name)

    try:
        import json as _json
        spec = _json.dumps([[str(mp), [float(c[0]), float(c[1]), float(c[2])]]
                            for mp, c in parts])
        cmd = [
            exe, "-b", "--python", str(script_path), "--",
            spec, str(output_path),
            str(azimuth), str(elevation), str(samples), str(resolution), str(lens),
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
        # Only after every success check above, so a hit can never stand in for
        # a render that failed or produced nothing.
        if key:
            try:
                meta_path.write_text(json.dumps({"key": key}))
            except OSError:
                pass
        return output_path
    finally:
        script_path.unlink(missing_ok=True)


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Render a studio-lit review photo of a mesh file via headless Blender.")
    ap.add_argument("mesh_file", nargs="?", help="Path to a .stl/.obj/.ply mesh")
    ap.add_argument("--part", action="append", default=[], metavar="PATH:R,G,B",
                    help="A colour region: mesh path, then its filament colour. "
                         "Repeat once per filament. Parts keep their own "
                         "coordinates so they stay in register.")
    ap.add_argument("-o", "--output", help="Output PNG path")
    ap.add_argument("--color", default="0.8,0.8,0.82", help="R,G,B 0-1 material color, e.g. 0.75,0.55,0.85")
    ap.add_argument("--azimuth", type=float, default=35.0)
    ap.add_argument("--elevation", type=float, default=28.0)
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--resolution", type=int, default=1200)
    ap.add_argument("--lens", type=float, default=85.0,
                    help="Camera focal length in mm. Lower to fit a tall part -- the "
                         "default 85 crops anything much taller than it is wide.")
    ap.add_argument("--no-cache", action="store_true",
                    help="Re-render even if an identical previous render is cached. The key "
                         "covers every mesh's real content plus colour, angle, samples, "
                         "resolution and lens, so any real change already misses it.")
    ap.add_argument("--check", action="store_true", help="Just check whether blender is installed")
    args = ap.parse_args()

    if args.check or not (args.mesh_file or args.part):
        available, info = check_blender_available()
        print(f"{'available' if available else 'NOT available'}: {info}")
        raise SystemExit(0 if available else 1)

    if args.part:
        parts = []
        for spec in args.part:
            # rsplit, not split: a Windows-style path can contain a colon, the
            # colour never can.
            path, _, rgb = spec.rpartition(":")
            if not path or rgb.count(",") != 2:
                print(f"ERROR: --part wants PATH:R,G,B, got {spec!r}", file=sys.stderr)
                raise SystemExit(2)
            parts.append((path, tuple(float(x) for x in rgb.split(","))))
        target = parts
        first = Path(parts[0][0])
    else:
        target = Path(args.mesh_file)
        first = target
    output = Path(args.output or first.with_suffix(".review.png"))
    color = tuple(float(x) for x in args.color.split(","))
    try:
        render_review(target, output, color=color,
                       azimuth=args.azimuth, elevation=args.elevation,
                       samples=args.samples, resolution=args.resolution,
                       lens=args.lens, use_cache=not args.no_cache)
    except BlenderRenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"rendered -> {output}")


if __name__ == "__main__":
    _cli()
