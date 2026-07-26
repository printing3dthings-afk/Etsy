#!/usr/bin/env python3
"""
Generate New Sticker Sheet
===========================
Generates a new unique kawaii sticker sheet via gpt-image-1. The sheet is
saved for review before being processed into the sticker pack pipeline.

Usage:
  python tools/gen_sticker_sheet.py                        # interactive
  python tools/gen_sticker_sheet.py --theme "summer beach"
  python tools/gen_sticker_sheet.py --pid DP1026 --sheet 10
"""
import os, sys, argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
_env_path = _ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from tools.image_gen import generate_image, SQUARE

DP_BASE_DIR = _ROOT / "data" / "digital_products" / "product_files"

DEFAULT_STYLE = (
    "A kawaii sticker sheet on a SOLID FLAT WHITE background. "
    "16–20 individual kawaii stickers arranged in a grid with clear spacing "
    "between each sticker. Each sticker has: thick black outlines, pastel "
    "colors, cute facial expressions, rounded shapes. The stickers should be "
    "varied in size and shape. Style: Japanese kawaii illustration, "
    "flat color fills, no gradients, no shadows, clean vector-like art. "
    "High resolution, 1024x1024px."
)

THEME_PROMPTS = {
    "daily planner": "Daily planner icons: coffee cup, notebook, pen, clock, checklist, calendar, sticky notes, laptop, headphones, plant, water bottle, snack, to-do list, star reward, heart",
    "self care": "Self care and wellness: face mask, bubble bath, candle, tea cup, yoga pose, meditation, journal, flowers, sleeping mask, moon, crystals, affirmation card, sunrise, cozy blanket",
    "food": "Cute food items: sushi, ramen bowl, boba tea, donut, pizza slice, ice cream cone, cupcake, avocado, pancakes, cookie, lollipop, watermelon, taco, french fries, milk carton",
    "weather": "Weather and seasons: sun, cloud, rainbow, rain drops, snowflake, umbrella, lightning bolt, wind, cherry blossom, autumn leaf, icicle, thermometer, tornado, fog, starry night",
    "animals": "Cute animals: cat, dog, bunny, panda, fox, owl, penguin, bear, koala, duck, hamster, hedgehog, frog, butterfly, bee",
    "school": "School supplies: backpack, pencil, eraser, ruler, globe, microscope, calculator, books, apple, graduation cap, trophy, paintbrush, scissors, glue, notebook",
    "fitness": "Fitness and health: running shoes, dumbbells, yoga mat, water bottle, apple, heart rate, jump rope, bicycle, trophy, stopwatch, salad, smoothie, headband, medal, protein shake",
    "travel": "Travel icons: airplane, suitcase, passport, camera, map, compass, palm tree, sunglasses, beach ball, postcard, train, hot air balloon, tent, campfire, mountains",
}


def generate_sheet(theme: str = "", pid: str = "", sheet_num: int = 1) -> Path:
    """Generate a single sticker sheet and save it."""
    if theme and theme.lower() in THEME_PROMPTS:
        theme_detail = THEME_PROMPTS[theme.lower()]
        prompt = f"{DEFAULT_STYLE}\n\nTheme: {theme}. Sticker subjects: {theme_detail}"
    elif theme:
        prompt = f"{DEFAULT_STYLE}\n\nTheme: {theme}."
    else:
        prompt = DEFAULT_STYLE + "\n\nTheme: assorted kawaii daily life stickers."

    if pid:
        out_dir = DP_BASE_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{pid.upper()}_sticker_sheet_{sheet_num}.png"
    else:
        out_dir = _ROOT / "data" / "digital_products" / "sticker_drafts"
        out_dir.mkdir(parents=True, exist_ok=True)
        # Use a timestamp-based name for drafts
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = (theme or "kawaii").replace(" ", "_")[:30]
        out_path = out_dir / f"sticker_sheet_{safe_theme}_{ts}.png"

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Sticker Sheet Generator")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    print(f"  Theme:  {theme or 'assorted kawaii'}")
    print(f"  Output: {out_path.name}")
    if pid:
        print(f"  PID:    {pid.upper()} sheet #{sheet_num}")
    print(f"\n  Generating via gpt-image-1 (this takes 15-30 seconds)...\n")

    try:
        result = generate_image(prompt, out_path, size=SQUARE, quality="high",
                                output_format="png")
        size_kb = result.stat().st_size / 1024
        print(f"  ✓ Generated: {result.name} ({size_kb:.0f} KB)")
        print(f"  ✓ Saved to:  {result}")
        print(f"\n  NEXT STEPS:")
        print(f"    1. Review the sheet visually")
        print(f"    2. If approved, run process_sticker_sheets.py to strip")
        print(f"       background and segment individual stickers")
        if pid:
            print(f"    3. Then rebuild_sticker_pack.py --pid {pid.upper()}")
        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return result
    except Exception as e:
        print(f"  ✗ Generation failed: {e}")
        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a new kawaii sticker sheet via gpt-image-1")
    parser.add_argument('--theme', default='',
                        help=f"Theme name or description. Built-in: {', '.join(THEME_PROMPTS)}")
    parser.add_argument('--pid', default='',
                        help="Product ID (e.g. DP1026) to save as a numbered sheet")
    parser.add_argument('--sheet', type=int, default=1,
                        help="Sheet number when using --pid (default: 1)")
    parser.add_argument('--list-themes', action='store_true',
                        help="List available built-in themes")
    args = parser.parse_args()

    if args.list_themes:
        print("\nAvailable themes:")
        for name, desc in THEME_PROMPTS.items():
            print(f"  {name:15s} — {desc[:70]}...")
        return

    generate_sheet(theme=args.theme, pid=args.pid, sheet_num=args.sheet)


if __name__ == '__main__':
    main()
