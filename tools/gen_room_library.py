#!/usr/bin/env python3
"""
gen_room_library.py — Generate the OnBrandCraftz 25-room background library.

Generates empty room backgrounds for use as compositing targets in lifestyle photos.
All rooms follow the 4-layer formula and 2026 interior design trends.
Upper 65%+ of every room is always clear wall for art placement.

Usage:
    python tools/gen_room_library.py                    # generate missing rooms only
    python tools/gen_room_library.py --force            # regenerate all rooms
    python tools/gen_room_library.py --id warm_office   # regenerate one specific room
    python tools/gen_room_library.py --list             # print room catalog and exit

Output: data/digital_products/product_files/empty_rooms/<room_id>.jpg
        data/knowledge_base/room_library.json  (metadata, updated on every run)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root or from tools/ directly
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from tools.image_gen import generate_image, SQUARE, ImageGenError  # noqa: E402

ROOMS_DIR = _ROOT / "data" / "digital_products" / "product_files" / "empty_rooms"
LIBRARY_JSON = _ROOT / "data" / "knowledge_base" / "room_library.json"

# Style anchor — pasted into every prompt for batch consistency
_STYLE_ANCHOR = (
    "Photorealistic interior photography. Bright editorial lifestyle photography style. "
    "35mm lens, eye-level angle. No people, no hands, no text, no art on any wall, "
    "no watermarks, no studio equipment visible. "
    "Upper 65% of the back wall is completely bare and empty — no shelves, no frames, "
    "no objects, no artwork hung on the wall."
)

# ─── Room Definitions ──────────────────────────────────────────────────────────
# Each entry:
#   id          : filename stem (output: <id>.jpg)
#   name        : human label
#   category    : living_room | bedroom | office | kitchen_dining | entryway | specialty
#   aesthetic   : 2026 design aesthetic name
#   art_styles  : list of art types that look best here
#   lighting    : one of "soft_window" | "warm_ambient" | "clean_bright" | "golden_hour"
#   prompt      : full gpt-image-1 generation prompt
# ──────────────────────────────────────────────────────────────────────────────

ROOMS: list[dict] = [

    # ─── LIVING ROOMS ─────────────────────────────────────────────────────────

    {
        "id": "coastal_living",
        "name": "Coastal Living Room",
        "category": "living_room",
        "aesthetic": "coastal",
        "art_styles": ["ocean_coastal", "landscape", "botanical", "abstract", "watercolor_floral"],
        "lighting": "clean_bright",
        "note": "EXISTING — skip regeneration unless --force used",
        "prompt": (
            "Photorealistic coastal living room interior photography. Soft blue-white "
            "plaster wall. A slipcovered cream linen sofa with two blue-stripe cushions "
            "and a natural rattan side table holding a small sea glass dish. "
            "Bleached oak driftwood-style floors. Sheer white curtain at the left edge "
            "suggesting a window. A small white ceramic vase with dried lavender. "
            "Bright breezy natural daylight, fresh cool-balanced white balance, "
            "light airy atmosphere. "
            "Upper 65% of the back wall is completely bare — no art, no shelves. "
            "35mm lens, eye-level. Coastal, fresh, summery. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "warm_living",
        "name": "Warm Boho Living Room",
        "category": "living_room",
        "aesthetic": "warm_boho",
        "art_styles": ["watercolor_floral", "abstract", "botanical", "landscape", "animal_portrait"],
        "lighting": "soft_window",
        "note": "EXISTING — skip regeneration unless --force used",
        "prompt": (
            "Photorealistic living room interior photography. Warm cream textured plaster wall, "
            "a boucle fabric sofa with sage green and terracotta throw pillows, natural oak "
            "hardwood floors, a rattan side table with a small terracotta ceramic pot and "
            "trailing pothos plant. A woven jute rug under the sofa. "
            "Soft diffused natural window light from the left, warm white balance, gentle "
            "shadow to the right, morning atmosphere. "
            "Upper 65% of the back wall is completely empty and plain — no art, no shelves. "
            "35mm lens, eye-level, wide shot. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "japandi_living",
        "name": "Japandi Living Room",
        "category": "living_room",
        "aesthetic": "japandi",
        "art_styles": ["minimalist_line_art", "zen", "abstract", "landscape", "celestial"],
        "lighting": "clean_bright",
        "prompt": (
            "Photorealistic Japandi living room interior photography. Soft white linen wall "
            "with very subtle plaster texture. Low-profile natural light oak sofa platform with "
            "cream linen cushions and a single stone-grey throw, legs barely visible above a "
            "light ash hardwood floor. A small round travertine coffee table. One large white "
            "ceramic vase with dried pampas grass beside the sofa. A single warm-toned "
            "beeswax taper candle in a matte black holder on the coffee table. "
            "Bright clean natural daylight from the left, cool-neutral white balance, "
            "even illumination across the wall. "
            "Upper 65% of the back wall is completely plain and bare — no art, no objects. "
            "35mm lens, eye-level. Calm, minimal, serene atmosphere. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "moody_living",
        "name": "Moody Dark Living Room",
        "category": "living_room",
        "aesthetic": "dark_moody",
        "art_styles": ["dark_moody", "celestial", "animal_portrait", "abstract", "landscape"],
        "lighting": "warm_ambient",
        "prompt": (
            "Photorealistic moody living room interior photography. Deep navy blue-green "
            "textured limewash wall. A dark charcoal velvet sofa with two oversized cushions "
            "in burgundy and forest green. Dark walnut hardwood floors. A low dark walnut "
            "coffee table with a single thick pillar candle and a dark hardcover art book. "
            "A small brass floor lamp beside the sofa casting warm amber glow upward. "
            "Evening atmosphere, warm amber and dim ambient lighting, intimate mood, "
            "long soft shadows. "
            "Upper 65% of the back wall is completely bare — no art, no shelves, no decor. "
            "35mm lens, eye-level. Dramatic, moody, sophisticated. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "cottage_living",
        "name": "English Cottage Living Room",
        "category": "living_room",
        "aesthetic": "english_cottage",
        "art_styles": ["botanical", "landscape", "animal_portrait", "watercolor_floral", "food_art"],
        "lighting": "warm_ambient",
        "prompt": (
            "Photorealistic English cottage living room interior photography. Warm off-white "
            "slightly textured plaster wall with a subtle aged quality. A deep cushioned linen "
            "sofa in warm oat color with printed botanical cushions and a tartan throw. "
            "Natural cherry wood floor partially covered by a faded Persian-style wool rug. "
            "A low vintage wooden coffee table with a small stack of hardcover books and a "
            "ceramic mug. Dried flower stems in a small earthenware vase beside the sofa. "
            "Warm afternoon light from a window at the right, golden-warm white balance, "
            "soft directional shadow to the left. Cozy, lived-in, traditional. "
            "Upper 65% of the back wall is completely bare — no shelves, no art, no frames. "
            "35mm lens, eye-level. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "maximalist_living",
        "name": "Curated Maximalist Living Room",
        "category": "living_room",
        "aesthetic": "curated_maximalism",
        "art_styles": ["abstract", "portrait", "colorful", "pop_art", "landscape"],
        "lighting": "soft_window",
        "prompt": (
            "Photorealistic curated maximalist living room interior photography. Warm terracotta "
            "limewash wall. A plush curved cream bouclé sofa with layered cushions in mustard, "
            "rust, and blush pink. A vintage rattan-and-brass coffee table with a stacked "
            "collection of art books and a terracotta vase. A trailing pothos plant in a "
            "woven basket at one end. Warm oak herringbone parquet floors. "
            "Soft diffused window light from the upper left, warm white balance, gentle "
            "shadows, golden morning atmosphere. Collected, layered, intentional. "
            "Upper 65% of the back wall is completely empty — no art, no shelves. "
            "35mm lens, eye-level, slightly wider shot to show sofa width. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "biophilic_living",
        "name": "Biophilic Living Room",
        "category": "living_room",
        "aesthetic": "biophilic",
        "art_styles": ["botanical", "landscape", "abstract", "watercolor_floral", "nature_scenes"],
        "lighting": "soft_window",
        "prompt": (
            "Photorealistic biophilic living room interior photography. Sage green matte "
            "painted wall with subtle texture. A linen sofa in warm cream with fern green "
            "throw pillows. Natural oak floors. A large floor-standing monstera deliciosa "
            "in a terracotta pot at the left edge. A smaller trailing pothos on a wooden "
            "plant stand to the right. A round oak coffee table with a small ceramic "
            "succulent planter and a smooth river stone. "
            "Bright natural morning light diffused through a window from the left, "
            "fresh cool-warm balanced white balance, even bright illumination. "
            "Upper 65% of the sage green wall is completely bare — no art, no objects. "
            "35mm lens, eye-level. Fresh, verdant, alive. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "art_deco_living",
        "name": "Art Deco Living Room",
        "category": "living_room",
        "aesthetic": "art_deco",
        "art_styles": ["geometric", "abstract", "pop_art", "bold_graphic", "celestial"],
        "lighting": "warm_ambient",
        "prompt": (
            "Photorealistic Art Deco living room interior photography. Deep cream with very "
            "subtle warm gold-tinted wallpaper texture on the back wall. A low-profile dark "
            "charcoal velvet sofa with gold-tipped tapered wooden legs. A round brass and "
            "black glass coffee table. A single tall brass floor lamp with a black shade "
            "casting warm directional light. A geometric patterned wool rug in charcoal and "
            "cream on dark herringbone parquet floors. "
            "Evening ambience, warm amber lamp light from upper right, soft ceiling ambient "
            "fill light, intimate and glamorous atmosphere. "
            "Upper 65% of the back wall is completely bare — no art, no shelves, no objects. "
            "35mm lens, eye-level. Sophisticated, dramatic, 1920s-inspired modern. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    # ─── BEDROOMS ─────────────────────────────────────────────────────────────

    {
        "id": "warm_bedroom",
        "name": "Warm Minimal Bedroom",
        "category": "bedroom",
        "aesthetic": "warm_minimal",
        "art_styles": ["watercolor_floral", "botanical", "abstract", "celestial", "line_art"],
        "lighting": "warm_ambient",
        "note": "EXISTING — skip regeneration unless --force used",
        "prompt": (
            "Photorealistic bedroom interior photography. Off-white linen wall, low platform "
            "bed frame in natural light oak with cream linen bedding and two soft pillows, "
            "a small ceramic bedside lamp emitting warm amber glow, a trailing pothos plant "
            "on a windowsill. Evening atmosphere, warm ambient light, shadows soft. "
            "Upper 65% of the far wall is completely bare and empty — no art, no decor. "
            "35mm lens, eye-level. Japandi aesthetic. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "japandi_bedroom",
        "name": "Japandi Bedroom",
        "category": "bedroom",
        "aesthetic": "japandi",
        "art_styles": ["minimalist_line_art", "zen", "abstract", "nature_silhouette", "botanical"],
        "lighting": "clean_bright",
        "prompt": (
            "Photorealistic Japandi bedroom interior photography. Soft white plaster wall, "
            "very subtle texture. Ultra-low platform bed in pale ash wood, cream and warm "
            "white linen bedding layered with a stone-grey waffle knit throw. A single white "
            "ceramic bud vase with one dried stem on the natural wood nightstand. Pale ash "
            "hardwood floor. A single white ceramic table lamp with warm soft light. "
            "Bright, clean, even natural daylight from a window to the left, "
            "cool-white balanced, serene morning atmosphere. "
            "Upper 65% of the back wall is completely plain and empty — no frames, no shelves. "
            "35mm lens, eye-level. Deeply calm, minimal, uncluttered. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "romantic_bedroom",
        "name": "Romantic Maximalist Bedroom",
        "category": "bedroom",
        "aesthetic": "romantic_maximalist",
        "art_styles": ["watercolor_floral", "abstract", "portrait", "celestial", "botanical"],
        "lighting": "warm_ambient",
        "prompt": (
            "Photorealistic romantic bedroom interior photography. Warm dusty rose matte "
            "painted wall. Upholstered velvet headboard in deep blush pink with a high "
            "footboard bed, piled with cream linen bedding, a floral embroidered cushion, "
            "and a silk throw in soft gold. Two ceramic bedside lamps with warm amber "
            "glow. A small bundle of dried roses in a hammered brass vase on the nightstand. "
            "Warm amber evening lighting from both side lamps, soft and intimate, "
            "no harsh shadows. Romantic, aspirational, feminine. "
            "Upper 65% of the back wall is completely bare — no frames, no art, no shelves. "
            "35mm lens, eye-level. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "dark_bedroom",
        "name": "Dark Moody Bedroom",
        "category": "bedroom",
        "aesthetic": "dark_moody",
        "art_styles": ["dark_moody", "celestial", "abstract", "landscape", "animal_portrait"],
        "lighting": "warm_ambient",
        "prompt": (
            "Photorealistic dark moody bedroom interior photography. Deep forest green "
            "matte painted wall. Dark walnut wood bed frame with charcoal linen bedding, "
            "a cream knit throw at the foot, and two black cylindrical ceramic lamps "
            "on wooden nightstands emitting warm amber glow. A single brass taper candle "
            "holder with an unlit candle on the left nightstand. Dark oak herringbone floors. "
            "Very warm amber lighting from side lamps, intimate evening atmosphere, "
            "gentle glow only — no overhead light, shadows falling naturally. Moody, "
            "sophisticated, deeply atmospheric. "
            "Upper 65% of the back wall is completely bare — no art, no frames, no objects. "
            "35mm lens, eye-level. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "boho_bedroom",
        "name": "Boho Bedroom",
        "category": "bedroom",
        "aesthetic": "boho",
        "art_styles": ["watercolor_floral", "abstract", "celestial", "botanical", "landscape"],
        "lighting": "soft_window",
        "prompt": (
            "Photorealistic boho bedroom interior photography. Warm ivory textured plaster "
            "wall. A rattan-framed circular headboard bed with cream and terracotta striped "
            "cotton bedding, layers of fringed boho cushions in rust and dusty pink. "
            "A hanging macramé wall accessory to the far side — NOT directly behind the "
            "bed, but to the side edge of the frame. A dried pampas grass arrangement "
            "in a clay vase on a low rattan nightstand. "
            "Soft warm natural morning light from the left window, golden-warm white balance. "
            "Upper 65% of the back wall is completely empty — no art, no frames. "
            "35mm lens, eye-level. Warm, wanderlust, free-spirited. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "coastal_bedroom",
        "name": "Coastal Bedroom",
        "category": "bedroom",
        "aesthetic": "coastal",
        "art_styles": ["ocean_coastal", "botanical", "abstract", "watercolor_floral", "landscape"],
        "lighting": "soft_window",
        "prompt": (
            "Photorealistic coastal bedroom interior photography. Pale sea-blue painted wall, "
            "very soft blue-grey tone. White washed driftwood-style bed frame with crisp "
            "white linen bedding and a single coastal blue stripe throw. Bleached oak "
            "floors. A white ceramic lamp on a white painted nightstand with a small "
            "sea glass dish and a dried lavender sprig. "
            "Bright breezy natural morning light from a window to the left, "
            "cool-bright white balance, fresh airy atmosphere. "
            "Upper 65% of the back wall is completely bare — no art, no frames, no objects. "
            "35mm lens, eye-level. Light, calm, fresh coastal. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    # ─── HOME OFFICES / STUDIES ────────────────────────────────────────────────

    {
        "id": "coastal_office",
        "name": "Coastal Office",
        "category": "office",
        "aesthetic": "coastal",
        "art_styles": ["ocean_coastal", "botanical", "abstract", "typography", "minimalist"],
        "lighting": "clean_bright",
        "note": "EXISTING — skip regeneration unless --force used",
        "prompt": (
            "Photorealistic home office interior photography. Warm white wall with subtle "
            "linen texture, a light oak floating desk, a matte black adjustable lamp, "
            "a small succulent in a white ceramic pot, minimal books stacked flat. "
            "Bright clean natural daylight from a window on the left, cool-neutral "
            "white balance, even illumination. "
            "Upper 60% of the back wall is completely empty and blank. 50mm lens, eye-level. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "warm_office",
        "name": "Warm Minimal Office",
        "category": "office",
        "aesthetic": "warm_minimal",
        "art_styles": ["typography", "abstract", "botanical", "minimalist", "motivational"],
        "lighting": "soft_window",
        "prompt": (
            "Photorealistic home office interior photography. Warm cream-white wall, "
            "subtle plaster texture. A wide natural walnut wood desk with a matte black "
            "desk lamp, a small potted snake plant in a terracotta pot, a leather-bound "
            "notebook and an uncapped fountain pen. A natural linen upholstered office "
            "chair. Warm oak parquet flooring. "
            "Soft diffused natural window light from the left, warm white balance, "
            "gentle shadow to the right, productive morning atmosphere. "
            "Upper 65% of the back wall is completely plain — no shelves, no art. "
            "35mm lens, eye-level. Clean, focused, aspirational. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "dark_academia_study",
        "name": "Dark Academia Study",
        "category": "office",
        "aesthetic": "dark_academia",
        "art_styles": ["typography", "dark_moody", "portrait", "landscape", "celestial"],
        "lighting": "warm_ambient",
        "prompt": (
            "Photorealistic dark academia study interior photography. Warm deep charcoal-brown "
            "painted wall, slightly aged plaster feel. A heavy dark mahogany desk with "
            "a green banker's lamp emitting warm amber glow, a stack of thick hardcover books "
            "with leather spines, a glass ink bottle, and a brass letter opener. "
            "A dark leather tufted desk chair. Dark oak floors with a deep burgundy and "
            "navy Persian rug. One brass candlestick with warm light. "
            "Evening atmosphere, warm amber lamp light only, intimate academic mood, "
            "rich directional shadows. "
            "Upper 65% of the back wall is completely bare — no shelves, no frames, no books "
            "on the wall — only the floor and desk have objects. "
            "35mm lens, eye-level. Intellectual, moody, Victorian library. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "biophilic_office",
        "name": "Biophilic Office",
        "category": "office",
        "aesthetic": "biophilic",
        "art_styles": ["botanical", "abstract", "landscape", "nature_scenes", "typography"],
        "lighting": "clean_bright",
        "prompt": (
            "Photorealistic biophilic home office interior photography. Soft sage green "
            "matte painted wall. A light oak floating desk with a small fiddle-leaf fig "
            "plant in a terracotta pot at one corner, a white ceramic mug, and a clean "
            "notebook. A modern white mesh office chair. Warm oak floor. A trailing "
            "pothos on a small floating shelf to the far side (not on the back wall). "
            "Bright clean natural daylight from a window overhead or to the left, "
            "fresh cool-balanced white balance, even illumination. "
            "Upper 65% of the sage green back wall is completely bare — no art, no shelves. "
            "35mm lens, eye-level. Productive, fresh, nature-connected. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "modern_office",
        "name": "Clean Modern Office",
        "category": "office",
        "aesthetic": "modern_minimal",
        "art_styles": ["geometric", "abstract", "typography", "minimalist", "bold_graphic"],
        "lighting": "clean_bright",
        "prompt": (
            "Photorealistic clean modern home office interior photography. Crisp white flat "
            "painted wall. A sleek white lacquered floating desk with absolutely nothing on "
            "it except a matte white ceramic pen holder with two pens and a tiny white cube "
            "planter. A white molded ergonomic chair. White polished concrete floor. "
            "Bright even studio-style natural daylight, pure neutral-white color temperature, "
            "zero shadows, clean and clinical but aspirational. "
            "Upper 65% of the back wall is completely bare and empty — no art, no objects. "
            "50mm lens, slightly above eye-level. Ultra-clean, tech-forward, minimalist. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    # ─── KITCHEN / DINING ─────────────────────────────────────────────────────

    {
        "id": "rustic_kitchen",
        "name": "Rustic Farmhouse Kitchen",
        "category": "kitchen_dining",
        "aesthetic": "farmhouse_rustic",
        "art_styles": ["food_art", "botanical", "watercolor_floral", "typography", "landscape"],
        "lighting": "soft_window",
        "prompt": (
            "Photorealistic rustic farmhouse kitchen interior photography. Warm cream "
            "plaster wall. A large reclaimed wood dining table with turned legs, four "
            "natural linen-cushion Shaker chairs partially visible. A terracotta pot "
            "with fresh herbs (rosemary, thyme) on the table, a ceramic olive oil jug, "
            "and a folded linen cloth. Warm waxed stone tile floors. "
            "Soft natural morning light from a window to the left, warm golden white "
            "balance, gentle shadow. "
            "Upper 65% of the back wall is completely bare — no shelves, no art, "
            "no open cabinets, just plain plaster. "
            "35mm lens, eye-level. Warm, homey, gathering-place atmosphere. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "modern_dining",
        "name": "Modern Dining Room",
        "category": "kitchen_dining",
        "aesthetic": "modern_warm",
        "art_styles": ["abstract", "geometric", "food_art", "landscape", "typography"],
        "lighting": "warm_ambient",
        "prompt": (
            "Photorealistic modern dining room interior photography. Soft warm greige "
            "painted wall. A round marble-top dining table with a brushed brass base, "
            "two modern rounded wooden dining chairs with cream boucle cushions visible. "
            "A low modern bowl pendant light fixture of woven rattan hanging over the "
            "table, emitting warm ambient glow. A single ceramic vase with one dried "
            "flower stem on the table. Warm pale oak herringbone floors. "
            "Warm pendant and ambient evening light, golden-warm white balance. "
            "Upper 65% of the back wall is completely plain — no art, no shelves. "
            "35mm lens, eye-level. Sophisticated, intimate, gathering. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "french_kitchen",
        "name": "French Bistro Kitchen",
        "category": "kitchen_dining",
        "aesthetic": "french_bistro",
        "art_styles": ["food_art", "watercolor_floral", "typography", "botanical", "landscape"],
        "lighting": "soft_window",
        "prompt": (
            "Photorealistic French bistro-style kitchen interior photography. Aged warm "
            "cream-yellow plaster wall. A classic wooden bistro table with a small ceramic "
            "pitcher holding fresh lavender, a small rattan basket with baguette visible, "
            "a ceramic espresso cup. Terracotta tile floor. Copper pot on a small shelf "
            "mounted to the side wall — NOT the back wall. "
            "Warm soft natural morning light from a window, golden-warm white balance, "
            "charming, rustic, Provençal atmosphere. "
            "Upper 65% of the cream plaster back wall is completely bare — no art, no shelves. "
            "35mm lens, eye-level. Warm, charming, European kitchen. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    # ─── ENTRYWAY / HALLWAY ───────────────────────────────────────────────────

    {
        "id": "modern_entryway",
        "name": "Modern Entryway",
        "category": "entryway",
        "aesthetic": "modern_minimal",
        "art_styles": ["abstract", "typography", "geometric", "minimalist", "botanical"],
        "lighting": "clean_bright",
        "prompt": (
            "Photorealistic modern entryway interior photography. Clean white flat painted "
            "wall. A slim natural oak console table with tapered black metal legs, a single "
            "round black ceramic vase with one dried palm frond, and a small white tray "
            "with keys. A round marble-framed mirror mounted low on the side wall to the "
            "right — NOT on the back wall. Light oak engineered floors. "
            "Bright clean even natural daylight from overhead or slightly left, "
            "cool-neutral white balance, fresh and welcoming. "
            "Upper 65% of the back wall is completely bare and plain — no art, no mirror on it. "
            "35mm lens, eye-level slightly above. Clean, contemporary, new-home feel. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "cottage_entryway",
        "name": "Cottage Entryway",
        "category": "entryway",
        "aesthetic": "english_cottage",
        "art_styles": ["botanical", "landscape", "watercolor_floral", "typography", "animal_portrait"],
        "lighting": "soft_window",
        "prompt": (
            "Photorealistic English cottage entryway interior photography. Warm cream-white "
            "plaster wall with very subtle aged texture. A small painted sage green console "
            "table with a small ceramic vase of dried hydrangeas in blush and ivory. "
            "A braided jute mat on aged honey-toned hardwood floors. A vintage brass "
            "coat hook mounted on the side wall to the right — NOT on the back wall. "
            "Soft warm natural morning light filtering gently, warm white balance, "
            "welcoming, homey, traditional. "
            "Upper 65% of the back wall is completely bare and plain — no hooks, no coat hangers, "
            "no art on the back wall itself. "
            "35mm lens, eye-level. Warm, welcoming, cottage first impression. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    {
        "id": "japandi_entryway",
        "name": "Japandi Entryway",
        "category": "entryway",
        "aesthetic": "japandi",
        "art_styles": ["minimalist_line_art", "zen", "abstract", "botanical", "nature_scenes"],
        "lighting": "clean_bright",
        "prompt": (
            "Photorealistic Japandi entryway interior photography. Soft warm white smooth "
            "plaster wall, minimal texture. A slim low natural bamboo console with a single "
            "tall matte white ceramic vase with a dried single branch of cherry blossom. "
            "Pale ash hardwood floors. A natural sisal doormat. "
            "Bright clean natural daylight from above, neutral-warm white balance, "
            "calm, welcoming, breath of fresh air. "
            "Upper 65% of the back wall is completely bare and empty — no art, no objects. "
            "35mm lens, eye-level. Serene, clean, first-impression calm. "
            f"{_STYLE_ANCHOR}"
        ),
    },

    # ─── SPECIALTY ────────────────────────────────────────────────────────────

    {
        "id": "reading_nook",
        "name": "Cozy Reading Nook",
        "category": "specialty",
        "aesthetic": "cozy_cottage",
        "art_styles": ["typography", "abstract", "botanical", "landscape", "dark_moody"],
        "lighting": "warm_ambient",
        "prompt": (
            "Photorealistic cozy reading nook interior photography. Warm cream-ivory plaster "
            "wall. A deep overstuffed linen armchair in warm oat cream with a chunky knit "
            "throw draped over one arm and a small decorative cushion. A round wooden "
            "side table beside the chair holding a ceramic mug with steam, a small "
            "hardcover book open face-down, and a beeswax candle in a small glass holder. "
            "Warm narrow beam floor lamp behind the chair casting golden upward glow. "
            "Warm oak hardwood floor. Evening atmosphere, warm amber lamp light, "
            "intimate and inviting. "
            "Upper 65% of the back wall is completely bare and empty — no shelves, no art. "
            "35mm lens, slightly above eye-level looking down into the nook. "
            "Deeply cozy, aspirational, 'I want to be in this chair' feeling. "
            f"{_STYLE_ANCHOR}"
        ),
    },

]

# ──────────────────────────────────────────────────────────────────────────────

_EXISTING_IDS = {"coastal_living", "warm_living", "warm_bedroom", "coastal_office"}


def _save_library_json() -> None:
    """Write room metadata (without full prompts for brevity) to room_library.json."""
    LIBRARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    catalog = {}
    for r in ROOMS:
        catalog[r["id"]] = {
            "name": r["name"],
            "category": r["category"],
            "aesthetic": r["aesthetic"],
            "art_styles": r["art_styles"],
            "lighting": r["lighting"],
            "file": f"empty_rooms/{r['id']}.jpg",
            "note": r.get("note", ""),
        }
    with open(LIBRARY_JSON, "w") as fh:
        json.dump(catalog, fh, indent=2)
    print(f"  Room library metadata saved → {LIBRARY_JSON}")


def _generate_room(r: dict, force: bool) -> bool:
    """Generate one room. Returns True if generated, False if skipped."""
    out = ROOMS_DIR / f"{r['id']}.jpg"
    if out.exists() and not force:
        print(f"  [skip] {r['id']}.jpg already exists")
        return False
    print(f"  [gen]  {r['id']} — {r['name']} ...")
    try:
        generate_image(
            prompt=r["prompt"],
            out_path=out,
            size=SQUARE,
            quality="medium",  # backgrounds are always composited — medium is sufficient
        )
        print(f"         saved {out.stat().st_size // 1024}KB → {out.name}")
        return True
    except ImageGenError as exc:
        print(f"  [ERR]  {r['id']}: {exc}")
        return False


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="Regenerate all rooms, even existing ones")
    ap.add_argument("--id", metavar="ROOM_ID", help="Regenerate one specific room by ID")
    ap.add_argument("--list", action="store_true", help="Print room catalog and exit")
    args = ap.parse_args(argv)

    if args.list:
        print(f"\n{'ID':<25} {'CATEGORY':<15} {'AESTHETIC':<25} STATUS")
        print("-" * 80)
        for r in ROOMS:
            out = ROOMS_DIR / f"{r['id']}.jpg"
            status = "EXISTS" if out.exists() else "missing"
            print(f"{r['id']:<25} {r['category']:<15} {r['aesthetic']:<25} {status}")
        print(f"\nTotal: {len(ROOMS)} rooms")
        return

    ROOMS_DIR.mkdir(parents=True, exist_ok=True)

    if args.id:
        target = next((r for r in ROOMS if r["id"] == args.id), None)
        if not target:
            print(f"ERROR: no room with id={args.id!r}. Use --list to see valid IDs.")
            sys.exit(1)
        _generate_room(target, force=True)
        _save_library_json()
        return

    generated = 0
    skipped = 0
    for r in ROOMS:
        force_this = args.force
        if r["id"] in _EXISTING_IDS and not args.force:
            # Protect existing rooms from accidental regeneration
            force_this = False
        result = _generate_room(r, force=force_this)
        if result:
            generated += 1
        else:
            skipped += 1

    _save_library_json()
    print(f"\nDone — {generated} generated, {skipped} skipped.")
    print(f"Room library: {ROOMS_DIR}")


if __name__ == "__main__":
    main()
