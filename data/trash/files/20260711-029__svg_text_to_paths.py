#!/usr/bin/env python3
"""
Convert SVG <text> elements to <path> outlines.

Required for commercial SVG bundles so that:
  1. Fonts render correctly on every buyer's machine (no local font path deps)
  2. Cricut Design Space / Silhouette Studio can cut the text as paths

Usage:
  python tools/svg_text_to_paths.py data/mom_life_pack/SVG data/mom_life_pack/SVG_paths
  python tools/svg_text_to_paths.py data/groovy_pack/SVG   data/groovy_pack/SVG_paths
"""
import os, sys, re, math
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

FONT_MAP = {
    "BebasNeue":      "/usr/local/share/fonts/BebasNeue-Regular.ttf",
    "GreatVibes":     "/usr/local/share/fonts/GreatVibes-Regular.ttf",
    "Cormorant":      "/usr/local/share/fonts/CormorantGaramond-Bold.ttf",
    "CormorantItalic":"/usr/local/share/fonts/CormorantGaramond-BoldItalic.ttf",
    "DancingScript":  "/usr/local/share/fonts/DancingScript-Bold.ttf",
    "Tangerine":      "/usr/local/share/fonts/Tangerine-Bold.ttf",
    "Cinzel":         "/usr/local/share/fonts/Cinzel-Regular.ttf",
    "Oswald":         "/usr/local/share/fonts/Oswald-Bold.ttf",
    "Montserrat":     "/usr/local/share/fonts/Montserrat-Bold.ttf",
}

_cache = {}

def load_font(css_name):
    if css_name not in _cache:
        path = FONT_MAP.get(css_name)
        if path and os.path.exists(path):
            _cache[css_name] = TTFont(path)
        else:
            _cache[css_name] = None
    return _cache[css_name]


def text_to_paths(x, y, text, font_css, size, fill, anchor="middle", letter_spacing=0):
    """Return SVG path elements representing the text, or None if font unavailable."""
    font = load_font(font_css)
    if not font:
        return None

    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    scale = float(size) / upm

    # ---- Calculate total advance for anchor ----
    total_adv = 0.0
    for ch in text:
        code = ord(ch)
        if code in cmap:
            total_adv += glyph_set[cmap[code]].width * scale
        else:
            total_adv += size * 0.3
    # letter-spacing is added between characters (n-1 gaps, but we add after each)
    total_adv += letter_spacing * len(text)

    if anchor == "middle":
        cur_x = float(x) - total_adv / 2.0
    elif anchor == "end":
        cur_x = float(x) - total_adv
    else:
        cur_x = float(x)

    # ---- Render each glyph ----
    parts = []
    for ch in text:
        code = ord(ch)
        if code not in cmap:
            cur_x += float(size) * 0.3 + letter_spacing
            continue

        glyph_name = cmap[code]
        glyph = glyph_set[glyph_name]

        pen = SVGPathPen(glyph_set)
        glyph.draw(pen)
        d = pen.getCommands()

        if d:
            # Font y-axis points up; SVG y-axis points down → negate y scale
            parts.append(
                f'<path d="{d}" fill="{fill}" '
                f'transform="translate({cur_x:.3f},{float(y):.3f}) '
                f'scale({scale:.6f},{-scale:.6f})"/>'
            )

        cur_x += glyph.width * scale + letter_spacing

    return "<g>" + "".join(parts) + "</g>" if parts else None


def _attr(attrs_str, name, default=""):
    m = re.search(rf'\b{re.escape(name)}="([^"]*)"', attrs_str)
    return m.group(1) if m else default


def convert_svg(src_path, dst_path):
    with open(src_path, "r", encoding="utf-8") as f:
        svg = f.read()

    # Remove <defs>…</defs> block (contains the broken @font-face rules)
    svg = re.sub(r"<defs>.*?</defs>", "", svg, flags=re.DOTALL)

    # Replace every <text …>content</text>
    text_re = re.compile(r"<text\s([^>]*)>(.*?)</text>", re.DOTALL)

    failures = []

    def replace_text(m):
        attrs = m.group(1)
        content = m.group(2)

        # Unescape XML entities in text content
        content = (content.replace("&amp;", "&")
                          .replace("&lt;", "<")
                          .replace("&gt;", ">")
                          .replace("&quot;", '"')
                          .replace("&apos;", "'"))

        x = _attr(attrs, "x", "400")
        y = _attr(attrs, "y", "400")
        anchor = _attr(attrs, "text-anchor", "start")
        raw_family = _attr(attrs, "font-family", "BebasNeue").split(",")[0].strip().strip("'\"")
        size_str = _attr(attrs, "font-size", "20")
        fill = _attr(attrs, "fill", "#000000")
        ls_str = _attr(attrs, "letter-spacing", "0")

        try:
            font_size = float(size_str)
            ls = float(ls_str) if ls_str else 0.0
            result = text_to_paths(
                float(x), float(y), content, raw_family,
                font_size, fill, anchor, ls
            )
            if result:
                return result
        except Exception as e:
            failures.append(f"{os.path.basename(src_path)}: {content!r} → {e}")

        return m.group(0)  # keep original on failure

    svg = text_re.sub(replace_text, svg)

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(svg)

    return failures


def convert_directory(src_dir, dst_dir):
    src = Path(src_dir)
    dst = Path(dst_dir)
    dst.mkdir(parents=True, exist_ok=True)

    all_failures = []
    count = 0
    for svg_file in sorted(src.glob("*.svg")):
        out_file = dst / svg_file.name
        failures = convert_svg(str(svg_file), str(out_file))
        all_failures.extend(failures)
        count += 1
        print(f"  ✓ {svg_file.name}")

    print(f"\n✅ Converted {count} SVGs → {dst_dir}")
    if all_failures:
        print(f"⚠️  {len(all_failures)} conversion warnings:")
        for f in all_failures:
            print(f"   • {f}")
    return len(all_failures)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/svg_text_to_paths.py <src_dir> <dst_dir>")
        sys.exit(1)
    errors = convert_directory(sys.argv[1], sys.argv[2])
    sys.exit(1 if errors else 0)
