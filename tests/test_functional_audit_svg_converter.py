"""Functional audit: tools/svg_converter.py's convert_to_svg().

Verifies that tracing a small, genuinely flat-color synthetic PNG (the kind
of clean source art an SS-series SVG pack design should be) produces an SVG
with a sane, small number of unique fill colors and path elements -- roughly
matching the input's real complexity -- rather than the "traced raster"
blowup CLAUDE.md's SS-Series quality gate describes (500+ fills, 600-900
paths, 475-750KB). Also checks the "color" mode's viewBox/width/height
rewrite (the 3x-upscale-then-rescale-back step) reports the ORIGINAL image
dimensions, not the 3x trace-space dimensions -- a mismatch here would ship
an SVG that renders 3x too large in any consumer that trusts width/height
over viewBox.

No DB, no network, no Etsy/Anthropic/OpenAI calls -- convert_to_svg() is
pure image processing (PIL + vtracer, both real installed deps here), so
this test exercises the real function directly. DB_PATH / APP_SECRET_TOKEN
are still set before importing `main` per this repo's test convention, in
case any future edit to this test needs the full server import.
"""
import io
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402  (import for harness parity; not otherwise used)

from svg_converter import convert_to_svg  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


# CLAUDE.md SS-Series SVG pack quality thresholds, mirrored here as the bar
# a clean-vector-producing trace should easily clear on a trivial input:
#   Unique fill colors per SVG: <= 20
#   Path elements per SVG: <= 200
#   File size per SVG: <= 150 KB
MAX_FILLS = 20
MAX_PATHS = 200
MAX_SIZE_KB = 150


def _make_three_color_png() -> bytes:
    """300x300 PNG: red background, blue square, green circle -- exactly 3
    flat colors, no gradients, no noise. The simplest possible non-trivial
    input for a "does tracing stay proportionate to real complexity" check."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (300, 300), (255, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 150, 150], fill=(0, 0, 255))
    d.ellipse([160, 160, 260, 260], fill=(0, 200, 0))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _make_solid_png() -> bytes:
    """100x100 single flat color -- the minimal case: should trace to
    exactly 1 fill, 1 path."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), (10, 200, 90))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _fills_and_paths(svg: str):
    fills = set(re.findall(r'fill="(#[0-9a-fA-F]{3,8}|[a-zA-Z]+)"', svg))
    paths = len(re.findall(r"<path", svg))
    return fills, paths


def test_unknown_mode_raises_value_error():
    try:
        convert_to_svg(_make_solid_png(), mode="not_a_real_mode")
        check(False, "convert_to_svg accepted an unknown mode without raising")
    except ValueError:
        pass
    except Exception as e:
        check(False, f"expected ValueError for unknown mode, got {type(e).__name__}: {e}")


def test_three_color_image_all_modes_stay_proportionate():
    data = _make_three_color_png()
    for mode in ("color", "bw", "silhouette"):
        svg = convert_to_svg(data, mode=mode)
        check(isinstance(svg, str) and svg.startswith("<?xml"), f"[{mode}] output is not an SVG/XML string")

        fills, paths = _fills_and_paths(svg)
        size_kb = len(svg.encode("utf-8")) / 1024

        check(
            len(fills) <= MAX_FILLS,
            f"[{mode}] {len(fills)} unique fill colors on a 3-flat-color input exceeds "
            f"CLAUDE.md's SS-Series hard threshold of {MAX_FILLS} -- traced-raster-style blowup",
        )
        check(
            paths <= MAX_PATHS,
            f"[{mode}] {paths} <path> elements on a 3-shape flat-color input exceeds "
            f"CLAUDE.md's SS-Series hard threshold of {MAX_PATHS} -- traced-raster-style blowup",
        )
        check(
            size_kb <= MAX_SIZE_KB,
            f"[{mode}] output is {size_kb:.1f}KB, exceeds CLAUDE.md's SS-Series hard threshold "
            f"of {MAX_SIZE_KB}KB for a trivial 3-color input",
        )
        # The real defect class CLAUDE.md describes is not just "over the hard
        # cap" but "wildly inflated relative to real complexity" -- a 3-shape
        # input producing e.g. 40 fills would pass the raw <=20 cap's neighbor
        # gates elsewhere but still be structurally wrong for THIS input.
        check(
            len(fills) <= 6,
            f"[{mode}] {len(fills)} unique fills for a genuinely 3-flat-color input is not "
            f"proportionate to the real input complexity (expected roughly 1-4)",
        )
        check(
            paths <= 12,
            f"[{mode}] {paths} paths for a 3-shape flat-color input is not proportionate to "
            f"the real input complexity (expected roughly 1-6)",
        )


def test_solid_color_image_minimal_output():
    data = _make_solid_png()
    for mode in ("color", "bw", "silhouette"):
        svg = convert_to_svg(data, mode=mode)
        fills, paths = _fills_and_paths(svg)
        check(len(fills) <= 2, f"[{mode}] solid single-color input produced {len(fills)} fills, expected 1-2")
        check(paths <= 3, f"[{mode}] solid single-color input produced {paths} paths, expected 1-3")


def test_color_mode_reports_original_dimensions_not_3x_trace_space():
    # "color" mode traces at 3x resolution internally, then must rewrite the
    # SVG's width/height back down to the original image's pixel size while
    # keeping the viewBox in 3x trace-space. A regression here (e.g. leaving
    # width/height at 3x, or leaving viewBox at 1x) would make the SVG render
    # at the wrong physical size in any consumer honoring width/height.
    data = _make_three_color_png()  # 300x300 source
    svg = convert_to_svg(data, mode="color")

    m = re.search(r'<svg[^>]*\bwidth="(\d+)"\s+height="(\d+)"', svg)
    check(m is not None, "could not find width/height attributes on the <svg> root element")
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        check((w, h) == (300, 300), f"expected width/height=(300,300) (original size), got {(w, h)}")

    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    check(vb is not None, "could not find viewBox attribute on the <svg> root element")
    if vb:
        vw, vh = int(vb.group(1)), int(vb.group(2))
        check((vw, vh) == (900, 900), f"expected viewBox 900x900 (3x trace space for a 300x300 source), got {(vw, vh)}")


def test_bw_and_silhouette_modes_do_not_get_viewbox_rewrite():
    # Only "color" mode does the 3x-upscale trick; bw/silhouette trace at
    # native resolution, so their SVG should already report the real size
    # without needing any post-hoc dimension rewrite.
    data = _make_three_color_png()
    for mode in ("bw", "silhouette"):
        svg = convert_to_svg(data, mode=mode)
        m = re.search(r'<svg[^>]*\bwidth="(\d+)"\s*(?:pt)?"?', svg)
        # vtracer's raw output width attr format can vary; just sanity-check
        # no "900" (3x) leaked into a bw/silhouette output for a 300px input.
        check("900" not in svg.split(">", 1)[0], f"[{mode}] unexpected 3x dimension leaked into svg root tag")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback

            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print(
        "FUNCTIONAL AUDIT TESTS OK -- convert_to_svg() produces fill/path counts "
        "proportionate to real input complexity (well under CLAUDE.md's SS-Series "
        "hard thresholds) for flat-color synthetic PNGs, and the color-mode "
        "3x-trace viewBox/width/height rewrite reports correct original dimensions."
    )


if __name__ == "__main__":
    run()
