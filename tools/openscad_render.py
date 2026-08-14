#!/usr/bin/env python3
"""
tools/openscad_render.py -- thin subprocess wrapper around the OpenSCAD CLI.

OpenSCAD (openscad.org, GPLv2) renders a parametric .scad script into a real
3D mesh (STL/OFF/3MF/etc). This is a system binary, not a pip package --
NOT bundled in the Railway server image by default (apt package `openscad`,
~2021.01 at time of writing). check_openscad_available() / render_scad()
both fail with a clear, actionable error rather than a bare
FileNotFoundError/CalledProcessError when it's missing, per this repo's
error-handling convention (api-conventions.md: "never a bare exception ...
raise ... with specific, actionable text").

Added 2026-08-14 per Scott's request after reviewing a batch of open-source
3D tooling (TRELLIS, Blender, Meshroom, FreeCAD, OpenSCAD) -- OpenSCAD was
the one that actually fits this codebase's existing pattern: Claude writes
a script, a subprocess renders it deterministically, resizable by changing
one parameter -- the same shape every generator in this shop already uses
(generate_planner.py, generate_wall_calendar.py, svg_converter.py), just
for genuinely 3D (non-flat) physical products instead of flat PDFs/SVGs.
Feeds the existing `3d_print_physical` catalog category (see
_KNOWN_CATEGORIES, tools/api_server/main.py) -- Scott prints the STL
himself on the Bambu P1S; nothing produced here is a customer-facing
digital download, and nothing here ever touches Etsy.

Standalone: python3 tools/openscad_render.py --check
            python3 tools/openscad_render.py model.scad -o out.stl -D size=40
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OPENSCAD_APT_PACKAGE = "openscad"
_SUPPORTED_FORMATS = {"stl", "off", "amf", "3mf", "csg", "png"}


class OpenSCADError(Exception):
    """Raised for any OpenSCAD failure -- missing binary, bad script syntax,
    or a non-zero/empty-output render. Callers should surface str(exc)
    directly; it's already a specific, actionable message, not a generic
    wrapper (matches the FileContentError/EtsyAPIError pattern used
    elsewhere in this codebase)."""


def check_openscad_available() -> tuple[bool, str]:
    """(is_available, version_or_error). Never raises -- safe to call as a
    pre-flight check before attempting a render, the same shape as
    generate_print_sizes.py's has_source_art check in main.py."""
    exe = shutil.which("openscad")
    if not exe:
        return False, (
            f"openscad is not installed. Install it with "
            f"`apt-get install -y {OPENSCAD_APT_PACKAGE}` (or `brew install openscad` "
            f"locally) -- it's a system binary, not a pip package, so it isn't in "
            f"requirements.txt and won't appear after a plain `pip install`."
        )
    try:
        result = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10)
        version = (result.stdout or result.stderr or "").strip()
        return True, version or "openscad (version unknown)"
    except Exception as exc:  # noqa: BLE001
        return False, f"openscad found at {exe} but `--version` failed: {exc}"


def render_scad(
    scad_source: str,
    output_path: Path,
    params: dict | None = None,
    fmt: str = "stl",
    timeout: int = 120,
) -> Path:
    """Render literal OpenSCAD source to a mesh file. Writes scad_source to a
    throwaway temp .scad file (OpenSCAD has no "render from stdin" mode),
    shells out to `openscad -o <output> -D key=value ... <input.scad>` as an
    argv list (never shell=True -- no shell-injection surface even though
    scad_source/params both ultimately come from a chat request), and
    returns output_path on success.

    params values are passed through OpenSCAD's -D command-line variable
    override VERBATIM -- each must already be a real OpenSCAD literal (a
    bare number, an explicitly-quoted string like '"hello"', true/false, or
    a vector like [1,2,3]). This function does not guess-and-add quotes for
    you, since auto-quoting a numeric override would silently turn it into
    a string and break the script; the caller (Claude, writing the .scad
    source in the same tool call) already knows each variable's real type.

    Raises OpenSCADError with a specific, actionable message on any failure:
    binary missing, bad syntax (OpenSCAD's own stderr is preserved verbatim
    -- it's usually a precise line number), a timeout, or an empty/zero-byte
    output (OpenSCAD can exit 0 while producing nothing on a script whose
    geometry resolves to an empty solid, e.g. a difference() that removes
    everything -- a silent-success trap this function refuses to pass along
    as one, matching this repo's "never a silent swallow" rule).
    """
    fmt = fmt.lower().lstrip(".")
    if fmt not in _SUPPORTED_FORMATS:
        raise OpenSCADError(f"unsupported output format {fmt!r} -- choose one of {sorted(_SUPPORTED_FORMATS)}")

    available, info = check_openscad_available()
    if not available:
        raise OpenSCADError(info)
    exe = shutil.which("openscad")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".scad", delete=False, encoding="utf-8") as f:
        f.write(scad_source)
        scad_path = Path(f.name)

    try:
        cmd = [exe, "-o", str(output_path)]
        for key, value in (params or {}).items():
            cmd += ["-D", f"{key}={value}"]
        cmd.append(str(scad_path))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise OpenSCADError(
                f"openscad render timed out after {timeout}s -- the script may be too "
                f"complex (high $fn, deeply nested CSG) or stuck; try a lower resolution first"
            )
        if result.returncode != 0:
            raise OpenSCADError(
                f"openscad exited {result.returncode} rendering to {fmt}: "
                f"{(result.stderr or result.stdout or 'no output').strip()[-2000:]}"
            )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise OpenSCADError(
                f"openscad exited 0 but produced no/empty output at {output_path} -- "
                f"check the script for geometry that resolves to nothing (e.g. an empty "
                f"difference()). stderr: {(result.stderr or '').strip()[-1000:]}"
            )
        return output_path
    finally:
        scad_path.unlink(missing_ok=True)


def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Render an OpenSCAD (.scad) file to a mesh, or check availability.")
    ap.add_argument("scad_file", nargs="?", help="Path to a .scad script")
    ap.add_argument("-o", "--output", help="Output file path (extension picks the format if -f is omitted)")
    ap.add_argument("-f", "--format", help="Output format, e.g. stl/3mf/off (default: from -o's extension)")
    ap.add_argument("-D", "--define", action="append", default=[], metavar="key=value",
                     help="Variable override, repeatable, e.g. -D size=40")
    ap.add_argument("--check", action="store_true", help="Just check whether openscad is installed")
    args = ap.parse_args()

    if args.check or not args.scad_file:
        available, info = check_openscad_available()
        print(f"{'available' if available else 'NOT available'}: {info}")
        raise SystemExit(0 if available else 1)

    scad_source = Path(args.scad_file).read_text(encoding="utf-8")
    params = dict(kv.split("=", 1) for kv in args.define)
    output = Path(args.output or Path(args.scad_file).with_suffix(".stl"))
    fmt = args.format or output.suffix.lstrip(".")
    try:
        render_scad(scad_source, output, params=params, fmt=fmt)
    except OpenSCADError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"rendered -> {output}")


if __name__ == "__main__":
    _cli()
