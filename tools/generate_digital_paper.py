#!/usr/bin/env python3
"""
generate_digital_paper.py
Generates seamless decorative background paper patterns for OnBrandCraftz
digital paper packs — sold on Etsy for use in Canva, GoodNotes, Cricut,
and scrapbooking.

Each theme produces 5 pattern JPEGs (3600×3600px, 300 DPI) plus a ZIP.
A listing_data.json is written per theme for Etsy publishing.

Usage:
    python tools/generate_digital_paper.py              # all 60 files
    python tools/generate_digital_paper.py --theme lavender  # one theme
    python tools/generate_digital_paper.py --preview    # list what would be created

PIL / standard library only — no external dependencies.
"""

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent.parent.resolve()
OUTPUT_DIR = BASE / "data" / "digital_products" / "digital_paper"

# ---------------------------------------------------------------------------
# Image specs
# ---------------------------------------------------------------------------
SIZE = 3600          # pixels (12 in × 300 DPI)
JPEG_QUALITY = 95
DPI = (300, 300)

# ---------------------------------------------------------------------------
# Brand color themes  (from CLAUDE.md)
# ---------------------------------------------------------------------------
THEMES = {
    "lavender_dreams": {
        "display_name": "Lavender Dreams",
        "primary":  "#8666AA",
        "accent":   "#C4A8D4",
        "neutral":  "#FAF7FF",
    },
    "cotton_candy": {
        "display_name": "Cotton Candy",
        "primary":  "#DE97C6",
        "accent":   "#97C6DE",
        "neutral":  "#FFF6FC",
    },
    "midnight_blue": {
        "display_name": "Midnight Blue",
        "primary":  "#1B2568",
        "accent":   "#7BA7C2",
        "neutral":  "#F0F5FF",
    },
    "coral_peach": {
        "display_name": "Coral Peach",
        "primary":  "#FD6C49",
        "accent":   "#F5B878",
        "neutral":  "#FFF8F4",
    },
    "cherry_blossom": {
        "display_name": "Cherry Blossom",
        "primary":  "#F4A7B9",
        "accent":   "#F9D0DB",
        "neutral":  "#FFF5F7",
    },
    "sage_garden": {
        "display_name": "Sage Garden",
        "primary":  "#8BA888",
        "accent":   "#C8DDB5",
        "neutral":  "#F6F8F2",
    },
    "celestial_night": {
        "display_name": "Celestial Night",
        "primary":  "#1E1B4B",
        "accent":   "#C9A84C",
        "neutral":  "#F0EEF8",
    },
    "mocha_latte": {
        "display_name": "Mocha Latte",
        "primary":  "#8B5E3C",
        "accent":   "#D4A96A",
        "neutral":  "#FDF8F0",
    },
    "mermaidcore": {
        "display_name": "Mermaidcore",
        "primary":  "#4ABFBF",
        "accent":   "#B8A9D9",
        "neutral":  "#F0FAFF",
    },
    "ocean_breeze": {
        "display_name": "Ocean Breeze",
        "primary":  "#3B8E8A",
        "accent":   "#7EC8C8",
        "neutral":  "#F0FAFA",
    },
    "sunflower_studio": {
        "display_name": "Sunflower Studio",
        "primary":  "#F4C430",
        "accent":   "#4A7C59",
        "neutral":  "#FFFDF0",
    },
    "matcha_serenity": {
        "display_name": "Matcha Serenity",
        "primary":  "#6B8F5E",
        "accent":   "#B8CC8E",
        "neutral":  "#F7F9F3",
    },
}

# CLI alias → theme key mapping (partial match on display_name or key)
THEME_ALIASES = {
    "lavender":   "lavender_dreams",
    "cotton":     "cotton_candy",
    "candy":      "cotton_candy",
    "midnight":   "midnight_blue",
    "coral":      "coral_peach",
    "peach":      "coral_peach",
    "cherry":     "cherry_blossom",
    "blossom":    "cherry_blossom",
    "sage":       "sage_garden",
    "garden":     "sage_garden",
    "celestial":  "celestial_night",
    "night":      "celestial_night",
    "mocha":      "mocha_latte",
    "latte":      "mocha_latte",
    "mermaid":    "mermaidcore",
    "ocean":      "ocean_breeze",
    "breeze":     "ocean_breeze",
    "sunflower":  "sunflower_studio",
    "studio":     "sunflower_studio",
    "matcha":     "matcha_serenity",
    "serenity":   "matcha_serenity",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def new_canvas(neutral_hex: str) -> Image.Image:
    return Image.new("RGB", (SIZE, SIZE), hex_to_rgb(neutral_hex))


# ---------------------------------------------------------------------------
# Pattern generators
# ---------------------------------------------------------------------------

def make_polka_dots(primary: str, neutral: str) -> Image.Image:
    """
    Evenly spaced grid of circles in primary color on neutral background.
    Dot diameter ≈ 60px, spacing ≈ 180px (20 columns × 20 rows).
    """
    img = new_canvas(neutral)
    draw = ImageDraw.Draw(img)
    color = hex_to_rgb(primary)

    spacing = 180
    radius = 30
    offset = spacing // 2  # centre-first dot at half-spacing so pattern tiles

    x = offset
    while x < SIZE + radius:
        y = offset
        while y < SIZE + radius:
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=color,
            )
            y += spacing
        x += spacing

    return img


def make_diagonal_stripes(primary: str, accent: str, neutral: str) -> Image.Image:
    """
    Alternating diagonal stripes: primary / accent / primary / accent …
    Stripe width ≈ 90px measured perpendicular to the stripe direction (45°).
    We tile by iterating over a diagonal coordinate.
    """
    img = new_canvas(neutral)
    draw = ImageDraw.Draw(img)
    c_primary = hex_to_rgb(primary)
    c_accent  = hex_to_rgb(accent)

    stripe_width = 90          # px, perpendicular width
    colors = [c_primary, c_accent]

    # Draw parallelogram-shaped stripes by column of pixels
    # For diagonal stripes at 45°, pixel (x,y) belongs to stripe:
    #   stripe_index = floor((x + y) / stripe_width)
    # We pre-build each row as a list of colors for speed.
    # Using putpixel for full accuracy at this size is too slow (3600×3600).
    # Instead we draw a wide set of diagonal parallelograms.

    # Tile range: -SIZE to 2*SIZE covers all 45° bands through the canvas.
    num_stripes = (2 * SIZE) // stripe_width + 2
    for i in range(num_stripes):
        color = colors[i % 2]
        d_start = i * stripe_width - SIZE
        d_end   = d_start + stripe_width
        # A band where (x + y) is in [d_start, d_end) maps to a diagonal stripe.
        # Draw as a filled polygon: four corners of the parallelogram.
        poly = [
            (d_start,       0),
            (d_end,         0),
            (d_end - SIZE,  SIZE),
            (d_start - SIZE, SIZE),
        ]
        draw.polygon(poly, fill=color)

    return img


def _star_polygon(cx: float, cy: float, outer_r: float, inner_r: float,
                  n_points: int = 5) -> list[tuple[float, float]]:
    """
    Compute 2*n_points vertices for a star polygon.
    The first outer point points straight up (rotation = -90°).
    """
    pts = []
    for i in range(2 * n_points):
        angle = math.pi * i / n_points - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def make_tiny_stars(primary: str, accent: str, neutral: str) -> Image.Image:
    """
    Scattered 5-pointed star shapes in primary (large) and accent (small).
    Uses a deterministic pseudo-random scatter seeded by theme for reproducibility.
    """
    img = new_canvas(neutral)
    draw = ImageDraw.Draw(img)
    c_primary = hex_to_rgb(primary)
    c_accent  = hex_to_rgb(accent)

    # Deterministic positions using a simple LCG seeded from primary hex.
    seed = int(primary.lstrip("#"), 16)

    def lcg(s: int) -> tuple[float, int]:
        s = (1664525 * s + 1013904223) & 0xFFFFFFFF
        return s / 0xFFFFFFFF, s

    # Large stars: ~80 scattered across the canvas
    s = seed
    for _ in range(80):
        v, s = lcg(s); cx = v * SIZE
        v, s = lcg(s); cy = v * SIZE
        v, s = lcg(s); outer_r = 22 + v * 18   # 22–40 px
        inner_r = outer_r * 0.42
        pts = _star_polygon(cx, cy, outer_r, inner_r)
        draw.polygon(pts, fill=c_primary)

    # Small accent stars: ~120
    for _ in range(120):
        v, s = lcg(s); cx = v * SIZE
        v, s = lcg(s); cy = v * SIZE
        v, s = lcg(s); outer_r = 10 + v * 10   # 10–20 px
        inner_r = outer_r * 0.42
        pts = _star_polygon(cx, cy, outer_r, inner_r)
        draw.polygon(pts, fill=c_accent)

    return img


def make_grid(accent: str, neutral: str) -> Image.Image:
    """
    Thin grid lines (crosshatch) in accent color on neutral background.
    Grid cell ≈ 120px; line width = 2px.
    """
    img = new_canvas(neutral)
    draw = ImageDraw.Draw(img)
    color = hex_to_rgb(accent)
    line_width = 2
    cell = 120

    # Vertical lines
    x = 0
    while x <= SIZE:
        draw.line([(x, 0), (x, SIZE)], fill=color, width=line_width)
        x += cell

    # Horizontal lines
    y = 0
    while y <= SIZE:
        draw.line([(0, y), (SIZE, y)], fill=color, width=line_width)
        y += cell

    return img


def _heart_polygon(cx: float, cy: float, size: float) -> list[tuple[float, float]]:
    """
    Approximate a heart shape as a closed polygon via parametric sampling.
    Uses the standard heart curve:
        x = 16 sin³(t)
        y = 13 cos(t) - 5 cos(2t) - 2 cos(3t) - cos(4t)
    Scaled and centred at (cx, cy).
    """
    pts = []
    n = 40  # polygon resolution
    for i in range(n):
        t = 2 * math.pi * i / n
        hx = 16 * math.sin(t) ** 3
        hy = -(13 * math.cos(t)
               - 5 * math.cos(2 * t)
               - 2 * math.cos(3 * t)
               - math.cos(4 * t))
        # hx in [-16, 16], hy in [-13, ~17] — normalise to [-1, 1]
        pts.append((cx + hx / 16 * size, cy + hy / 17 * size))
    return pts


def make_scattered_hearts(primary: str, accent: str, neutral: str) -> Image.Image:
    """
    Small heart shapes in primary and accent colors scattered on neutral.
    """
    img = new_canvas(neutral)
    draw = ImageDraw.Draw(img)
    c_primary = hex_to_rgb(primary)
    c_accent  = hex_to_rgb(accent)

    seed = int(accent.lstrip("#"), 16)

    def lcg(s: int) -> tuple[float, int]:
        s = (1664525 * s + 1013904223) & 0xFFFFFFFF
        return s / 0xFFFFFFFF, s

    s = seed
    # Primary hearts: ~70
    for _ in range(70):
        v, s = lcg(s); cx = v * SIZE
        v, s = lcg(s); cy = v * SIZE
        v, s = lcg(s); size = 22 + v * 20   # 22–42 px
        pts = _heart_polygon(cx, cy, size)
        draw.polygon(pts, fill=c_primary)

    # Accent hearts: ~90 (smaller)
    for _ in range(90):
        v, s = lcg(s); cx = v * SIZE
        v, s = lcg(s); cy = v * SIZE
        v, s = lcg(s); size = 12 + v * 14   # 12–26 px
        pts = _heart_polygon(cx, cy, size)
        draw.polygon(pts, fill=c_accent)

    return img


# ---------------------------------------------------------------------------
# Pattern dispatch
# ---------------------------------------------------------------------------
PATTERNS: dict[str, callable] = {
    "polka_dots":        lambda p, a, n: make_polka_dots(p, n),
    "diagonal_stripes":  lambda p, a, n: make_diagonal_stripes(p, a, n),
    "tiny_stars":        lambda p, a, n: make_tiny_stars(p, a, n),
    "grid_crosshatch":   lambda p, a, n: make_grid(a, n),
    "scattered_hearts":  lambda p, a, n: make_scattered_hearts(p, a, n),
}


# ---------------------------------------------------------------------------
# Listing data
# ---------------------------------------------------------------------------

def build_listing_data(theme_key: str, theme: dict) -> dict:
    name = theme["display_name"]
    return {
        "theme_key":   theme_key,
        "title":       (
            f"{name} Digital Paper Pack | Scrapbook Paper Printable "
            f"| GoodNotes Background | Instant Download"
        ),
        "price":       4.99,
        "tags": [
            "digital paper",
            "scrapbook paper",
            "printable paper",
            "digital background",
            "goodnotes background",
            "instant download",
            "digital paper pack",
            "scrapbook digital",
            "pattern paper",
            "digital planner paper",
        ],
        "files_included": [f"pattern_{p}.jpg" for p in PATTERNS],
        "color_theme": {
            "primary": theme["primary"],
            "accent":  theme["accent"],
            "neutral": theme["neutral"],
        },
    }


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def generate_theme(theme_key: str, theme: dict, verbose: bool = True) -> list[Path]:
    """Generate all 5 patterns for one theme. Returns list of generated JPEG paths."""
    theme_dir = OUTPUT_DIR / theme_key
    theme_dir.mkdir(parents=True, exist_ok=True)

    p = theme["primary"]
    a = theme["accent"]
    n = theme["neutral"]

    generated: list[Path] = []

    for pattern_name, fn in PATTERNS.items():
        out_path = theme_dir / f"pattern_{pattern_name}.jpg"
        if verbose:
            print(f"  [{theme['display_name']}] {pattern_name} ...", end=" ", flush=True)

        img = fn(p, a, n)
        img.save(str(out_path), "JPEG", quality=JPEG_QUALITY, dpi=DPI)
        generated.append(out_path)

        if verbose:
            size_kb = out_path.stat().st_size // 1024
            print(f"saved ({size_kb} KB)")

    # Write listing_data.json
    listing_path = theme_dir / "listing_data.json"
    with listing_path.open("w", encoding="utf-8") as fh:
        json.dump(build_listing_data(theme_key, theme), fh, indent=2)
    if verbose:
        print(f"  [{theme['display_name']}] listing_data.json written")

    # Build ZIP
    zip_path = OUTPUT_DIR / f"{theme_key}_paper_pack.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for jpeg_path in generated:
            zf.write(jpeg_path, jpeg_path.name)
        zf.write(listing_path, listing_path.name)
    if verbose:
        zip_kb = zip_path.stat().st_size // 1024
        print(f"  [{theme['display_name']}] ZIP → {zip_path.name} ({zip_kb} KB)")

    return generated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def resolve_theme(alias: str) -> str | None:
    """Return the canonical theme key for an alias/partial name, or None."""
    alias_lower = alias.lower()
    # Exact key match
    if alias_lower in THEMES:
        return alias_lower
    # Alias table
    if alias_lower in THEME_ALIASES:
        return THEME_ALIASES[alias_lower]
    # Partial substring match on key or display_name
    for key, meta in THEMES.items():
        if alias_lower in key or alias_lower in meta["display_name"].lower():
            return key
    return None


def cmd_preview() -> None:
    total = len(THEMES) * len(PATTERNS)
    print(f"Would generate {total} JPEG files across {len(THEMES)} themes:\n")
    for theme_key, meta in THEMES.items():
        theme_dir = OUTPUT_DIR / theme_key
        print(f"  {meta['display_name']}  →  {theme_dir}/")
        for pattern_name in PATTERNS:
            print(f"    pattern_{pattern_name}.jpg  (3600×3600 px, JPEG q95)")
        zip_path = OUTPUT_DIR / f"{theme_key}_paper_pack.zip"
        print(f"    {theme_key}_paper_pack.zip\n")
    print(f"Total output directory: {OUTPUT_DIR}")


def cmd_generate(theme_filter: str | None) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if theme_filter:
        key = resolve_theme(theme_filter)
        if key is None:
            print(f"ERROR: Unknown theme '{theme_filter}'.", file=sys.stderr)
            print(f"Available themes: {', '.join(THEMES)}", file=sys.stderr)
            sys.exit(1)
        themes_to_run = {key: THEMES[key]}
    else:
        themes_to_run = THEMES

    total_files = 0
    total_bytes = 0

    for theme_key, theme in themes_to_run.items():
        print(f"\n── {theme['display_name']} ──")
        generated = generate_theme(theme_key, theme)
        total_files += len(generated)
        total_bytes += sum(p.stat().st_size for p in generated)

    # Summary
    total_mb = total_bytes / (1024 * 1024)
    zip_count = len(themes_to_run)
    print(f"\n{'='*50}")
    print(f"Done.")
    print(f"  JPEG files generated : {total_files}")
    print(f"  ZIPs created         : {zip_count}")
    print(f"  Total JPEG size      : {total_mb:.1f} MB")
    print(f"  Output directory     : {OUTPUT_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate digital paper packs for OnBrandCraftz Etsy shop."
    )
    parser.add_argument(
        "--theme",
        metavar="NAME",
        help="Generate only one theme (partial name accepted, e.g. 'lavender')",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="List what would be created without generating anything",
    )
    args = parser.parse_args()

    if args.preview:
        cmd_preview()
    else:
        cmd_generate(args.theme)


if __name__ == "__main__":
    main()
