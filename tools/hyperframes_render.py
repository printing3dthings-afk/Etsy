#!/usr/bin/env python3
"""
tools/hyperframes_render.py -- thin subprocess wrapper around the HyperFrames
CLI (heygen-com/hyperframes, npm package `hyperframes`).

HyperFrames renders a composition defined as HTML (data-start/data-duration
attributes for timing, GSAP/CSS/WAAPI for animation) into a real MP4 via
headless Chrome (Puppeteer) + ffmpeg. This is a Node.js CLI tool, not a pip
package -- NOT bundled in the Railway server image by default. Needs:
  - Node.js 22+ (this shop's dev/CI image already has it)
  - ffmpeg (apt package `ffmpeg`)
  - Chrome Headless Shell, fetched once via `npx hyperframes browser ensure`
    (~115MB download, cached under ~/.cache/hyperframes/chrome/)
check_hyperframes_available() / render_composition() both fail with a clear,
actionable error rather than a bare subprocess crash when any of these are
missing, per this repo's error-handling convention (api-conventions.md:
"never a bare exception ... raise ... with specific, actionable text").

Added 2026-08-14 alongside tools/openscad_render.py, after Scott reviewed a
batch of open-source tooling and asked to implement whichever fit this
codebase's existing pattern: Claude writes real source (HTML/GSAP here,
OpenSCAD there), a subprocess renders it deterministically. This is a
DIFFERENT, more flexible tool than the existing `generate_video` (main.py) --
that one is a fixed Ken Burns pan-zoom slideshow with 4 preset styles pulled
from an existing Etsy listing's photos; this one lets Claude author a real
animated composition (kinetic typography, layered reveals, branded intros)
when the preset styles aren't enough. Real product photos are passed in via
`media_files` and referenced by the composition's own <img>/<video> src --
never an AI-generated stand-in, same cardinal rule as every other listing
asset in this shop.

Verified end-to-end 2026-08-14 (ffmpeg + Chrome Headless Shell installed by
hand for this check): a real GSAP fade-in title composition rendered a
genuine 1080x1920 H.264 MP4; a real product-photo <img> reference rendered
correctly via a copied-in media file; a malformed composition (no GSAP
timeline, no data-duration) failed with the CLI's own detailed, actionable
error ("Composition has zero duration ... Fix: add data-duration=...")
rather than a silent/bare failure.

Standalone: python3 tools/hyperframes_render.py --check
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_HYPERFRAMES_JSON = json.dumps({
    "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
    "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
    "media": {"autoProxy": True},
})

_TELEMETRY_OFF_ENV = {"HYPERFRAMES_NO_TELEMETRY": "1", "DO_NOT_TRACK": "1", "HYPERFRAMES_SKIP_SKILLS": "1"}


class HyperframesError(Exception):
    """Raised for any HyperFrames failure -- missing dependency, a malformed
    composition, or a non-zero/empty-output render. Callers should surface
    str(exc) directly; it's already specific and actionable (matching the
    OpenSCADError/FileContentError pattern used elsewhere in this codebase)."""


def _hyperframes_cmd() -> list[str]:
    """Prefer a globally-installed `hyperframes` binary (no per-call registry
    check, faster and works offline) -- falls back to `npx --yes hyperframes`
    (auto-fetches from npm on first use, ~1-15s overhead depending on cache
    state) when nothing is installed globally. Either way this never silently
    does nothing -- render_composition's real subprocess call surfaces
    whichever path was actually used in its own error messages."""
    exe = shutil.which("hyperframes")
    if exe:
        return [exe]
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", "hyperframes"]
    return []


def check_hyperframes_available() -> tuple[bool, str]:
    """(is_available, version_or_error). Never raises. Fast, local-only
    checks (no subprocess spawn, no network) -- doesn't confirm the npm
    package itself resolves, only that the prerequisites for it to work are
    present. A real render call surfaces any deeper problem with its own
    clear error."""
    missing = []
    if not shutil.which("node"):
        missing.append("Node.js 22+ (apt/nvm/nodesource — not a pip package)")
    if not (shutil.which("hyperframes") or shutil.which("npx")):
        missing.append("npx (ships with Node.js) or a global `npm install -g hyperframes`")
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg (apt package `ffmpeg`)")
    if missing:
        return False, f"hyperframes needs {', '.join(missing)} installed on this deploy."

    chrome_cache = Path.home() / ".cache" / "hyperframes" / "chrome"
    if not chrome_cache.exists() or not any(chrome_cache.iterdir()):
        return False, (
            "Chrome Headless Shell hasn't been fetched yet on this deploy. Run "
            "`npx hyperframes browser ensure` once (one-time ~115MB download, cached after)."
        )
    return True, "hyperframes ready (Node.js, ffmpeg, Chrome Headless Shell all present)"


def render_composition(
    html_source: str,
    output_path: Path,
    media_files: dict[str, str | Path] | None = None,
    resolution: str | None = None,
    fps: int | None = None,
    quality: str = "standard",
    timeout: int = 300,
) -> Path:
    """Render a literal HTML/GSAP composition to a real MP4.

    html_source is a complete index.html per HyperFrames' composition format:
    a root element with data-composition-id/data-start/data-duration (or a
    GSAP timeline registered on window.__timelines[id] for auto-inferred
    duration), child elements marked class="clip" with their own
    data-start/data-duration/data-track-index. See CLAUDE.md's "Animated
    Video Compositions (HyperFrames)" section for the exact template this
    shop uses, or `npx hyperframes docs` for the full authoring reference.

    media_files maps a relative path AS REFERENCED IN html_source's src
    attributes (e.g. "assets/photo1.jpg") to a real file on disk -- each is
    copied into the throwaway project directory before rendering, so a real
    delivered product photo can be composited into the video (never an
    AI-generated stand-in, matching every other listing asset in this shop).

    Raises HyperframesError with a specific, actionable message on any
    failure: missing dependency, a missing media file, a timeout (a
    malformed composition -- e.g. no GSAP timeline AND no data-duration --
    is a REAL observed hang risk, confirmed during development; this
    function's own timeout is the safety net, not just defensive
    boilerplate), a non-zero render exit (HyperFrames' own stderr is
    preserved verbatim -- it gives precise, actionable fixes like "add
    data-duration to your root element"), or an empty/zero-byte output.
    """
    available, info = check_hyperframes_available()
    if not available:
        raise HyperframesError(info)

    cmd_prefix = _hyperframes_cmd()
    if not cmd_prefix:
        raise HyperframesError("neither a global `hyperframes` binary nor `npx` was found.")

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="hyperframes_project_") as td:
        project = Path(td)
        (project / "hyperframes.json").write_text(_HYPERFRAMES_JSON, encoding="utf-8")
        (project / "index.html").write_text(html_source, encoding="utf-8")

        for rel_name, src in (media_files or {}).items():
            src_path = Path(src)
            if not src_path.exists():
                raise HyperframesError(f"media file not found: {src_path} (referenced as {rel_name!r})")
            dest = project / rel_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)

        cmd = cmd_prefix + ["render", str(project), "-o", str(output_path), "--quiet"]
        if resolution:
            cmd += ["--resolution", resolution]
        if fps:
            cmd += ["--fps", str(fps)]
        if quality:
            cmd += ["--quality", quality]

        env = dict(os.environ)
        env.update(_TELEMETRY_OFF_ENV)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            raise HyperframesError(
                f"hyperframes render timed out after {timeout}s -- a composition missing a "
                f"GSAP timeline AND a data-duration attribute on its root element is a known "
                f"cause of this (the runtime can't infer when the video ends); double-check "
                f"the composition has one or the other before retrying"
            )

        if result.returncode != 0:
            raise HyperframesError(
                f"hyperframes render exited {result.returncode}: "
                f"{(result.stderr or result.stdout or 'no output').strip()[-2000:]}"
            )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise HyperframesError(
                f"hyperframes exited 0 but produced no/empty output at {output_path}. "
                f"stderr: {(result.stderr or '').strip()[-1000:]}"
            )
        return output_path


def _cli() -> None:
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Render an HTML/GSAP composition to MP4, or check availability.")
    ap.add_argument("html_file", nargs="?", help="Path to a composition index.html")
    ap.add_argument("-o", "--output", help="Output MP4 path")
    ap.add_argument("--resolution", help="portrait/landscape/square (see HyperFrames --help for full list)")
    ap.add_argument("--quality", default="standard", choices=["draft", "standard", "high"])
    ap.add_argument("--check", action="store_true", help="Just check whether hyperframes is ready")
    args = ap.parse_args()

    if args.check or not args.html_file:
        available, info = check_hyperframes_available()
        print(f"{'available' if available else 'NOT available'}: {info}")
        raise SystemExit(0 if available else 1)

    html_source = Path(args.html_file).read_text(encoding="utf-8")
    output = Path(args.output or Path(args.html_file).with_suffix(".mp4"))
    try:
        render_composition(html_source, output, resolution=args.resolution, quality=args.quality)
    except HyperframesError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"rendered -> {output}")


if __name__ == "__main__":
    _cli()
