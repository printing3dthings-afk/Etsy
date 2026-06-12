#!/usr/bin/env python3
"""
Generate high-quality flat 2D design images for SS1001 Vol 2 using gpt-image-1.

Each design matches one of the original 5 AI concept signs:
  07 — Banner (Main): navy background, gold AMERICA, cream 250, red stripes
  08 — Burst (Artdeco): navy disc, 24 gold sunburst rays, cream 250 in center
  09 — Seal (Medallion): cream disc, navy eagle + ring text, navy 250
  10 — Shield: cream pentagon, navy eagle, gold AMERICA ribbon, red stars + 250
  11 — Stamp: cream rectangle with perforations, navy Liberty, red AMERICA 250

Output: preview.jpg in each design folder (replaces programmatic composite).
These previews drive listing photos 06, 09, 10 and inform images.edit lifestyle shots.
"""

from __future__ import annotations
import base64
import io
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from PIL import Image

client = OpenAI()

ROOT = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"

# Style anchor — applied to every prompt
STYLE = (
    "Flat 2D vector graphic illustration. Absolutely no gradients, no drop shadows, "
    "no photography, no 3D rendering effects. Exactly four flat solid colors: "
    "dark navy blue (#1B3A68), deep patriotic red (#B22234), antique gold (#C9A84C), "
    "and warm cream (#F5EDD0). Crisp, clean color boundaries. "
    "Professional commercial sign design. Square format 1:1."
)

DESIGNS = [
    {
        "folder": "07_america250_banner_4c",
        "name": "Banner (Main)",
        "prompt": (
            "Flat 2D patriotic sign graphic. Horizontal rectangle, wider than tall. "
            "Background: solid dark navy blue. "
            "Layout top-to-bottom: "
            "(1) Thin antique-gold decorative outer border frame. "
            "(2) Deep red horizontal band across the full top. "
            "(3) 'AMERICA' in very large bold antique-gold block letters, centered. "
            "(4) Thin antique-gold rule line. "
            "(5) '250' in enormous bold cream/off-white Anton-style numerals — this is the dominant element, filling most of the central height. "
            "(6) Thin red accent line. "
            "(7) '1776  –  2026' in cream letters, small, centered. "
            "(8) Deep red horizontal band across the full bottom. "
            "A single antique-gold 5-pointed star centered between AMERICA and 250. "
            + STYLE
        ),
    },
    {
        "folder": "08_america250_burst_4c",
        "name": "Burst (Artdeco Sunburst)",
        "prompt": (
            "Flat 2D patriotic sign graphic. Perfect circle disc shape. "
            "Background of the disc: solid dark navy blue. "
            "24 antique-gold sunburst rays radiating outward from a central circle to the edge. "
            "Rays are tall narrow wedge/triangle shapes, evenly spaced, with thin navy gaps between each ray. "
            "Central inner circle (no rays — solid navy background): "
            "  - 'AMERICA' in bold antique-gold letters, small, at the top of the inner circle. "
            "  - Very large bold '250' in cream/off-white numerals, centered and dominant. "
            "  - '1776  ·  2026' in small antique-gold text below the 250. "
            "Thin antique-gold ring border separates the inner circle from the rays. "
            "Art Deco patriotic style. "
            + STYLE
        ),
    },
    {
        "folder": "09_america250_seal_4c",
        "name": "Seal (Medallion)",
        "prompt": (
            "Flat 2D patriotic sign graphic. Perfect circle — official government seal style. "
            "Background: warm cream/parchment fills the full circle. "
            "Outer thick navy-blue ring: 'UNITED STATES OF AMERICA' text curves along the inner top arc in cream letters. "
            "13 small 5-pointed cream stars evenly spaced inside the ring. "
            "Inside the ring: American bald eagle silhouette in solid navy blue, wings fully spread wide, facing right, centered in the upper half. "
            "Below eagle: very large bold '250' in dark navy, centered. "
            "'ANNIVERSARY' in small navy below that. "
            "'1776  ·  2026' in small navy below that. "
            "Thin navy decorative rule lines between text sections. "
            "Official American medallion / presidential seal aesthetic. "
            + STYLE
        ),
    },
    {
        "folder": "10_america250_shield_4c",
        "name": "Shield (Eagle Shield)",
        "prompt": (
            "Flat 2D patriotic sign graphic. Classic heraldic shield shape: flat top, curved sides tapering to a point at the bottom. "
            "Background: warm cream/parchment fills the full shield. "
            "Thick dark-navy border follows the shield perimeter. "
            "Near the top inside: a row of 7 small solid deep-red 5-pointed stars. "
            "Below stars: American bald eagle silhouette in solid dark navy, wings spread fully wide, facing right, centered. "
            "Across the middle of the shield: a wide horizontal ribbon/banner in antique gold. 'AMERICA' text in dark navy centered inside the gold ribbon. "
            "Below the ribbon: large bold '250' in deep red, centered. "
            "'1776  ·  2026' in small navy text near the bottom point. "
            "Heraldic patriotic shield aesthetic. "
            + STYLE
        ),
    },
    {
        "folder": "11_america250_stamp_4c",
        "name": "Stamp (Liberty Stamp)",
        "prompt": (
            "Flat 2D patriotic sign graphic. Classic US postage stamp shape: upright rectangle with a row of evenly-spaced small circular perforation teeth along all 4 edges (like real stamp perforations). "
            "Background: warm cream/parchment. "
            "Dark navy thick stamp border inside the perforations. "
            "'UNITED STATES' in bold navy text at the top inside. "
            "Thin navy horizontal rule line below. "
            "Center: Statue of Liberty full-body silhouette in solid dark navy — torch raised in right arm, tablet in left arm, seven-pointed crown, flowing draped robe, stepped rectangular pedestal. Tall, centered, fills most of the vertical space. "
            "Below the Liberty figure: 'AMERICA' in large bold deep-red letters. "
            "'250' in large bold deep-red numerals below that. "
            "At the very bottom: 'FOREVER' in small antique-gold letters. "
            "Classic American postage stamp aesthetic. "
            + STYLE
        ),
    },
]


def generate_design(design: dict) -> None:
    folder = DESIGNS_DIR / design["folder"]
    folder.mkdir(parents=True, exist_ok=True)
    out_path = folder / "preview.jpg"

    print(f"  Generating {design['name']}...")

    result = client.images.generate(
        model="gpt-image-1",
        prompt=design["prompt"],
        size="1024x1024",
        quality="high",
        n=1,
    )

    raw = base64.b64decode(result.data[0].b64_json)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    # Save at 4× resolution for listing use
    img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
    img.save(out_path, "JPEG", quality=94)
    print(f"    ✓ {out_path.stat().st_size // 1024} KB → {out_path}")


def main() -> None:
    which = __import__("sys").argv[1:]   # e.g. "07" "08" to regenerate individual designs

    print("SS1001 Vol 2 — High-Quality Design Generation (gpt-image-1)")
    print("=" * 60)

    for d in DESIGNS:
        num = d["folder"][:2]
        if which and num not in which:
            continue
        try:
            generate_design(d)
        except Exception as e:
            import traceback
            print(f"  ERROR {d['name']}: {e}")
            traceback.print_exc()

    print("=" * 60)
    print("Done. Run generate_ss1001_photos.py to rebuild listing photos.")


if __name__ == "__main__":
    main()
