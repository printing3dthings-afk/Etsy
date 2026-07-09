"""Photo/reference-image -> SVG conversion for the Studio "SVG Converter" tool.

Wraps vtracer (already a pinned dependency in requirements.txt) with three tuned
parameter presets. The parameter sets themselves are ported from an earlier,
undeployed prototype (command_center.py's /api/convert-svg) rather than re-derived
from scratch -- that tuning work was already done and validated there.

None of these modes guarantee a clean-vector result usable as-is in a 3D-print
SVG pack (see etsy_api.check_svg_quality / _validate_svgs_in_zip for the real
gate) -- a traced photo is fundamentally different from a hand-drawn vector, and
"color"/"bw" modes in particular can produce hundreds of paths on a busy source
image. "silhouette" mode (aggressive speckle filtering, binary colormode) is the
best starting point for a result that might pass the gate, but the caller should
always run check_svg_quality() on the output and show the real number, not assume.
"""
from __future__ import annotations

import io
import re

MAX_TRACE_SIDE = 2000  # vtracer is slow on 4K+ inputs; downscale before tracing

_MODES = ("color", "bw", "silhouette")


def convert_to_svg(image_bytes: bytes, mode: str = "color") -> str:
    """Convert raster image bytes to an SVG string. mode is one of "color",
    "bw", "silhouette". Raises ValueError for an unknown mode, and whatever
    vtracer/PIL raise on a genuinely unreadable image."""
    if mode not in _MODES:
        raise ValueError(f"unknown mode {mode!r}, expected one of {_MODES}")

    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))

    if max(img.size) > MAX_TRACE_SIDE:
        ratio = MAX_TRACE_SIDE / max(img.size)
        img = img.resize(
            (max(1, int(img.width * ratio)), max(1, int(img.height * ratio))),
            Image.LANCZOS,
        )
    width, height = img.size

    if mode == "bw":
        return _trace(
            img.convert("RGB"),
            colormode="binary", hierarchical="cutout", mode="spline",
            filter_speckle=4, color_precision=8, layer_difference=16,
            corner_threshold=60, length_threshold=4.0,
            max_iterations=10, splice_threshold=45, path_precision=8,
        )

    if mode == "silhouette":
        return _trace(
            img.convert("RGB"),
            colormode="binary", hierarchical="cutout", mode="spline",
            filter_speckle=16, color_precision=8, layer_difference=16,
            corner_threshold=60, length_threshold=4.0,
            max_iterations=10, splice_threshold=45, path_precision=6,
        )

    # "color" -- two-pass pipeline: a quantized flat-color pass, then a
    # median-filtered 3x-upscaled pass so vtracer fits smoother bezier curves.
    # Only the second pass's SVG is kept; the first pass exists in the
    # original prototype purely as a quantization step, not as usable output
    # on its own, so it's reproduced here for parity but discarded.
    _trace(  # quantized pass -- intentionally unused result, kept for parity
        img.convert("RGB"),
        colormode="color", hierarchical="stacked", mode="spline",
        filter_speckle=16, color_precision=4, layer_difference=22,
        corner_threshold=80, length_threshold=8.0,
        max_iterations=10, splice_threshold=45, path_precision=8,
    )

    img_med = img.convert("RGB").filter(_median_filter())
    w3, h3 = width * 3, height * 3
    img_3x = img_med.resize((w3, h3), Image.NEAREST)
    svg_str = _trace(
        img_3x,
        colormode="color", hierarchical="stacked", mode="spline",
        filter_speckle=4, color_precision=4, layer_difference=22,
        corner_threshold=85, length_threshold=24,
        max_iterations=10, splice_threshold=45, path_precision=8,
    )
    # Paths were traced in 3x space; redeclare the SVG's viewBox/display size
    # so it renders at the original photo's dimensions, not 3x too large.
    svg_str = re.sub(
        r"<svg[^>]*>",
        f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {w3} {h3}" width="{width}" height="{height}">',
        svg_str, count=1,
    )
    return svg_str


def _median_filter():
    from PIL import ImageFilter
    return ImageFilter.MedianFilter(3)


def _trace(img, **params) -> str:
    import vtracer
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return vtracer.convert_raw_image_to_svg(buf.getvalue(), img_format="png", **params)
