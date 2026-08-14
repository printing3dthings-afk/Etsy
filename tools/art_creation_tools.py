"""
Art Creation Tools — generates digital art and printable planner PDFs.

Stale docstring fixed 2026-07-22: image generation is gpt-image-1 (via
_generate_digital_art()'s own direct call) or, for the newer
generate_wall_art_master() path, any approved engine (gpt-image-1/gpt-image-2/
Gemini/Ideogram) routed through tools/image_gen.py's generate_image() — never
DALL-E 3, despite what this docstring said for a long time.

Requires for full functionality:
  OPENAI_API_KEY  — gpt-image-1/gpt-image-2 image generation
  Pillow          — image processing (pip install Pillow)
  reportlab       — PDF planner generation (pip install reportlab)

Without an OpenAI key the agent operates in "design-brief" mode: it saves a
detailed text concept that can be sent to any image-generation service manually.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path
from typing import Any

from tools.data_store import DataStore
from tools.idea_tools import SUBMIT_IDEA_DEFINITION, handle_submit_idea

DIGITAL_PRODUCTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "digital_products")
PRODUCT_FILES_DIR = os.path.join(DIGITAL_PRODUCTS_DIR, "product_files")

# ── Hand-painted medium system ────────────────────────────────────────────────
# When a product or pipeline entry has `hand_painted_medium` set to one of these
# keys, enrich_prompt_with_medium() wraps the base DALL-E prompt with authentic
# visual-language modifiers so the output looks like real hand-painted artwork.
# random_painting_medium() assigns a medium (or None = digital) at ~40% rate.

import random as _random

HAND_PAINTED_STYLES: dict[str, dict] = {
    "watercolor": {
        "label": "Watercolor",
        "prompt_prefix": (
            "Original-looking watercolor painting, authentic hand-painted artwork. "
        ),
        "prompt_suffix": (
            " Painted on cold-press watercolor paper — subtle grain and tooth visible "
            "throughout. Wet-on-wet blooms and soft color bleeds where washes meet. "
            "Granulation in heavier pigment pools. Unpredictable fluid edges — never "
            "sharp or mechanical. Transparent luminous washes layered for depth. "
            "Preserved white paper highlights. Happy accidents and small imperfections "
            "that only real watercolor has. Looks genuinely hand-painted, not digital."
        ),
        "title_suffix": "Watercolor Art Print",
        "medium_note": "Printed from an original hand-painted watercolor artwork",
        "extra_tags": ["watercolor art print", "watercolor painting", "hand painted art", "watercolor poster"],
    },
    "oil_painting": {
        "label": "Oil Painting",
        "prompt_prefix": (
            "Original-looking oil painting on canvas, authentic hand-painted artwork. "
        ),
        "prompt_suffix": (
            " Canvas weave texture visible through thin paint areas. Thick impasto "
            "brushstrokes with dimensional ridges catching light. Rich saturated color "
            "with deep velvety shadows and luminous highlights. Wet-into-wet color "
            "mixing at edge transitions. Palette knife marks in textured passages. "
            "Glazing layers creating translucent depth over dried underlayers. "
            "The surface reads as real oil paint on stretched canvas. "
            "Looks genuinely hand-painted, not digital."
        ),
        "title_suffix": "Oil Painting Print",
        "medium_note": "Printed from an original hand-painted oil painting",
        "extra_tags": ["oil painting print", "oil painting art", "canvas art print", "hand painted art"],
    },
    "acrylic": {
        "label": "Acrylic Painting",
        "prompt_prefix": (
            "Original-looking acrylic painting, authentic hand-painted artwork. "
        ),
        "prompt_suffix": (
            " Bold opaque color with visible brush texture throughout. Flat matte "
            "areas contrasting with expressive impasto marks. Clean graphic edges "
            "mixed with gestural passages. Acrylic paint body and slight sheen "
            "visible. Dried paint pooling at edges. Strong direct color — "
            "vibrant and immediate. Looks genuinely hand-painted with acrylics, not digital."
        ),
        "title_suffix": "Acrylic Art Print",
        "medium_note": "Printed from an original hand-painted acrylic artwork",
        "extra_tags": ["acrylic art print", "acrylic painting print", "hand painted art", "original art print"],
    },
    "gouache": {
        "label": "Gouache",
        "prompt_prefix": (
            "Original-looking gouache painting, authentic hand-painted artwork. "
        ),
        "prompt_suffix": (
            " Distinctive chalky matte finish of gouache paint — no gloss anywhere. "
            "Opaque flat color areas with clean graphic silhouettes. Subtle "
            "brushstroke texture in larger fields. Slight paint drag marks at edges. "
            "Dried paint texture and slight surface variation in color fields. "
            "Rich saturated palette but completely matte and velvety. "
            "Looks genuinely hand-painted with gouache, not digital."
        ),
        "title_suffix": "Gouache Art Print",
        "medium_note": "Printed from an original hand-painted gouache artwork",
        "extra_tags": ["gouache art print", "gouache painting print", "hand painted art", "flat art print"],
    },
    "ink_wash": {
        "label": "Ink Wash",
        "prompt_prefix": (
            "Original-looking ink wash painting, sumi-e inspired authentic hand-painted artwork. "
        ),
        "prompt_suffix": (
            " Fluid ink washes ranging from dilute pale gray to dense velvety black. "
            "Expressive gestural brushwork — confident fast strokes with dry-brush "
            "texture where the brush runs dry. Bleeding ink edges where wash meets "
            "damp paper. Rice paper or washi texture showing through thin washes. "
            "Negative space used deliberately. Spontaneous and uncontrived — the "
            "beauty of accidents and imperfect marks. Looks genuinely hand-painted "
            "with ink on paper, not digital."
        ),
        "title_suffix": "Ink Wash Print",
        "medium_note": "Printed from an original hand-painted ink wash artwork",
        "extra_tags": ["ink wash print", "sumi-e art print", "brush painting print", "hand painted art"],
    },
    "pastel": {
        "label": "Soft Pastel",
        "prompt_prefix": (
            "Original-looking soft pastel artwork, authentic hand-drawn pastel painting. "
        ),
        "prompt_suffix": (
            " Soft chalky blended pastel marks — colors merge with gentle transitions. "
            "Textured pastel paper grain visible throughout, especially in lighter "
            "areas. Powdery matte quality with layered pastel strokes. Light areas "
            "have a warm luminous glow from pigment catching paper texture. "
            "Edges are soft and blended, never sharp. Colors overlap and blend "
            "organically. Looks genuinely hand-drawn with soft pastels, not digital."
        ),
        "title_suffix": "Pastel Art Print",
        "medium_note": "Printed from an original hand-drawn soft pastel artwork",
        "extra_tags": ["pastel art print", "soft pastel print", "pastel painting print", "hand drawn art"],
    },
}

# Weighted draw: ~40% chance of a hand-painted medium, 60% stays digital (None).
_MEDIUM_POOL = (
    [None] * 60
    + ["watercolor"] * 15
    + ["oil_painting"] * 10
    + ["acrylic"] * 6
    + ["gouache"] * 5
    + ["ink_wash"] * 2
    + ["pastel"] * 2
)


def random_painting_medium(seed: int | None = None) -> str | None:
    """Return a random hand-painted medium name, or None (keep digital). ~40% painted."""
    rng = _random.Random(seed)
    return rng.choice(_MEDIUM_POOL)


def enrich_prompt_with_medium(base_prompt: str, medium: str | None) -> str:
    """Wrap base_prompt with hand-painted visual-language modifiers for the given medium."""
    if not medium or medium not in HAND_PAINTED_STYLES:
        return base_prompt
    style = HAND_PAINTED_STYLES[medium]
    return style["prompt_prefix"] + base_prompt + style["prompt_suffix"]


# ── Color scheme presets — 8 complete packages ────────────────────────────────
# Each scheme: theme, accent, bg, dark, mid, light (all normalized 0–1 RGB tuples)
COLOR_SCHEMES: dict[str, dict] = {
    "sage_cream": {
        "label":  "Sage & Cream",
        "theme":  (0.529, 0.659, 0.467),   # #87A878 sage green
        "accent": (0.788, 0.643, 0.298),   # #C9A84C warm gold
        "bg":     (0.980, 0.969, 0.945),   # #FAF7F2 warm cream
        "dark":   (0.14, 0.18, 0.13),
        "mid":    (0.43, 0.50, 0.41),
        "light":  (0.86, 0.90, 0.85),
    },
    "dusty_rose": {
        "label":  "Dusty Rose",
        "theme":  (0.769, 0.545, 0.624),   # #C48B9F
        "accent": (0.549, 0.482, 0.459),   # #8C7B75 warm gray
        "bg":     (0.980, 0.961, 0.941),   # #FAF5F0
        "dark":   (0.22, 0.16, 0.19),
        "mid":    (0.50, 0.42, 0.46),
        "light":  (0.91, 0.87, 0.89),
    },
    "midnight_navy": {
        "label":  "Midnight Navy",
        "theme":  (0.106, 0.165, 0.290),   # #1B2A4A deep navy
        "accent": (0.788, 0.643, 0.298),   # #C9A84C gold
        "bg":     (0.980, 0.982, 0.984),   # near white
        "dark":   (0.10, 0.10, 0.14),
        "mid":    (0.40, 0.42, 0.46),
        "light":  (0.87, 0.88, 0.90),
    },
    "terracotta": {
        "label":  "Terracotta & Forest",
        "theme":  (0.757, 0.482, 0.353),   # #C17B5A
        "accent": (0.290, 0.404, 0.255),   # #4A6741 forest green
        "bg":     (0.961, 0.929, 0.843),   # #F5ECD7 warm beige
        "dark":   (0.22, 0.15, 0.12),
        "mid":    (0.50, 0.40, 0.35),
        "light":  (0.91, 0.87, 0.83),
    },
    "lavender_dreams": {
        "label":  "Lavender Dreams",
        "theme":  (0.525, 0.400, 0.667),   # #8666AA muted purple
        "accent": (0.765, 0.694, 0.882),   # #C3B1E1 soft lavender
        "bg":     (0.977, 0.973, 0.988),   # very light lavender
        "dark":   (0.18, 0.14, 0.22),
        "mid":    (0.45, 0.41, 0.52),
        "light":  (0.89, 0.87, 0.93),
    },
    "dark_academia": {
        "label":  "Dark Academia",
        "theme":  (0.110, 0.110, 0.118),   # #1C1C1E near black
        "accent": (0.722, 0.451, 0.200),   # #B87333 copper
        "bg":     (0.961, 0.941, 0.910),   # #F5F0E8 aged cream
        "dark":   (0.10, 0.10, 0.12),
        "mid":    (0.38, 0.36, 0.33),
        "light":  (0.82, 0.80, 0.77),
    },
    "blush_gold": {
        "label":  "Blush & Gold",
        "theme":  (0.714, 0.384, 0.467),   # #B66277 deep blush
        "accent": (0.831, 0.686, 0.216),   # #D4AF37 gold
        "bg":     (0.996, 0.988, 0.992),   # near white with blush tint
        "dark":   (0.22, 0.16, 0.18),
        "mid":    (0.52, 0.44, 0.46),
        "light":  (0.93, 0.89, 0.91),
    },
    "minimal_mono": {
        "label":  "Minimal Monochrome",
        "theme":  (0.176, 0.176, 0.176),   # #2D2D2D charcoal
        "accent": (0.420, 0.447, 0.502),   # #6B7280 cool gray
        "bg":     (0.996, 0.996, 0.996),   # pure white
        "dark":   (0.12, 0.12, 0.12),
        "mid":    (0.42, 0.42, 0.42),
        "light":  (0.88, 0.88, 0.88),
    },
    # ── Sophisticated/editorial schemes (second tier — premium moody aesthetic) ─
    "mocha_latte": {
        "label":  "Mocha Latte",
        "theme":  (0.290, 0.180, 0.102),   # #4A2E1A chocolate brown
        "accent": (0.831, 0.769, 0.690),   # #D4C4B0 warm cream-taupe
        "bg":     (0.941, 0.918, 0.878),   # #F0EAE0 latte beige
        "dark":   (0.20, 0.12, 0.07),
        "mid":    (0.55, 0.42, 0.32),
        "light":  (0.90, 0.84, 0.78),
    },
    "wine_burgundy": {
        "label":  "Wine & Burgundy",
        "theme":  (0.545, 0.125, 0.251),   # #8B2040 deep wine
        "accent": (0.769, 0.522, 0.541),   # #C4858A dusty rose
        "bg":     (0.980, 0.941, 0.941),   # #FAF0F0 blush white
        "dark":   (0.25, 0.05, 0.10),
        "mid":    (0.55, 0.30, 0.35),
        "light":  (0.93, 0.87, 0.88),
    },
    "ice_blue": {
        "label":  "Ice Blue",
        "theme":  (0.545, 0.659, 0.769),   # #8BA8C4 powder blue
        "accent": (0.839, 0.890, 0.933),   # #D6E3EE light ice
        "bg":     (0.933, 0.957, 0.980),   # #EEF4FA very light blue
        "dark":   (0.22, 0.30, 0.38),
        "mid":    (0.48, 0.57, 0.66),
        "light":  (0.88, 0.91, 0.94),
    },
    "forest_deep": {
        "label":  "Deep Forest",
        "theme":  (0.165, 0.227, 0.165),   # #2A3A2A dark forest green
        "accent": (0.353, 0.431, 0.290),   # #5A6E4A sage olive
        "bg":     (0.941, 0.957, 0.933),   # #F0F4EE light sage
        "dark":   (0.10, 0.14, 0.10),
        "mid":    (0.35, 0.44, 0.35),
        "light":  (0.85, 0.90, 0.85),
    },
    # ── Fun / bold schemes ────────────────────────────────────────────────────
    "cotton_candy": {
        "label":  "Cotton Candy",
        "theme":  (0.871, 0.592, 0.776),   # #DE97C6 pink
        "accent": (0.580, 0.808, 0.933),   # #94CEEE sky blue
        "bg":     (0.996, 0.965, 0.988),   # #FEF6FC
        "dark":   (0.28, 0.16, 0.24),
        "mid":    (0.56, 0.42, 0.52),
        "light":  (0.94, 0.88, 0.92),
    },
    "bubblegum": {
        "label":  "Bubblegum",
        "theme":  (0.973, 0.341, 0.576),   # #F85793 hot pink
        "accent": (0.400, 0.867, 0.882),   # #66DDE1 cyan
        "bg":     (0.996, 0.933, 0.965),   # #FEEFF6
        "dark":   (0.26, 0.10, 0.18),
        "mid":    (0.58, 0.36, 0.50),
        "light":  (0.97, 0.88, 0.93),
    },
    "lemon_zest": {
        "label":  "Lemon Zest",
        "theme":  (0.220, 0.220, 0.100),   # near-black with yellow tint
        "accent": (0.949, 0.824, 0.063),   # #F2D210 bright yellow
        "bg":     (0.996, 0.992, 0.937),   # #FEFDED
        "dark":   (0.14, 0.14, 0.06),
        "mid":    (0.40, 0.40, 0.22),
        "light":  (0.94, 0.94, 0.84),
    },
    "neon_pop": {
        "label":  "Neon Pop",
        "theme":  (0.188, 0.188, 0.216),   # #303037 dark charcoal
        "accent": (0.976, 0.275, 0.573),   # #F94692 neon pink
        "bg":     (0.992, 0.980, 0.996),   # almost white
        "dark":   (0.12, 0.12, 0.16),
        "mid":    (0.40, 0.38, 0.44),
        "light":  (0.86, 0.84, 0.90),
    },
    "retro_sunset": {
        "label":  "Retro Sunset",
        "theme":  (0.843, 0.392, 0.196),   # #D76432 burnt orange
        "accent": (0.945, 0.714, 0.204),   # #F1B634 golden yellow
        "bg":     (0.988, 0.953, 0.910),   # #FCF3E8 warm cream
        "dark":   (0.22, 0.13, 0.08),
        "mid":    (0.52, 0.38, 0.28),
        "light":  (0.94, 0.86, 0.80),
    },
    "tropical": {
        "label":  "Tropical",
        "theme":  (0.043, 0.604, 0.576),   # #0B9A93 teal
        "accent": (0.957, 0.639, 0.165),   # #F4A32A mango
        "bg":     (0.929, 0.976, 0.973),   # #EDF9F8
        "dark":   (0.04, 0.22, 0.20),
        "mid":    (0.30, 0.55, 0.52),
        "light":  (0.82, 0.94, 0.93),
    },
    "spring_blossom": {
        "label":  "Spring Blossom",
        "theme":  (0.890, 0.467, 0.651),   # #E377A6 blossom pink
        "accent": (0.467, 0.761, 0.459),   # #77C275 fresh green
        "bg":     (0.996, 0.961, 0.980),   # #FEF5FB
        "dark":   (0.24, 0.14, 0.18),
        "mid":    (0.55, 0.40, 0.48),
        "light":  (0.96, 0.88, 0.93),
    },
    # ── Moody / dark schemes ──────────────────────────────────────────────────
    "midnight_purple": {
        "label":  "Midnight Purple",
        "theme":  (0.298, 0.157, 0.478),   # #4C287A deep purple
        "accent": (0.773, 0.620, 0.933),   # #C59EEE soft lavender
        "bg":     (0.976, 0.969, 0.992),   # #F9F7FD
        "dark":   (0.16, 0.10, 0.24),
        "mid":    (0.44, 0.36, 0.56),
        "light":  (0.88, 0.85, 0.94),
    },
    "deep_ocean": {
        "label":  "Deep Ocean",
        "theme":  (0.047, 0.310, 0.490),   # #0C4F7D ocean blue
        "accent": (0.200, 0.733, 0.667),   # #33BBAA teal
        "bg":     (0.929, 0.965, 0.984),   # #EEF6FB
        "dark":   (0.04, 0.18, 0.28),
        "mid":    (0.30, 0.52, 0.62),
        "light":  (0.82, 0.90, 0.95),
    },
    "art_deco_bk": {
        "label":  "Art Deco",
        "theme":  (0.067, 0.067, 0.067),   # #111 near black
        "accent": (0.831, 0.686, 0.216),   # #D4AF37 gold
        "bg":     (0.988, 0.984, 0.973),   # #FBF9F8 warm white
        "dark":   (0.06, 0.06, 0.06),
        "mid":    (0.35, 0.32, 0.28),
        "light":  (0.88, 0.86, 0.82),
    },
    "rosewood": {
        "label":  "Rosewood",
        "theme":  (0.537, 0.200, 0.259),   # #893342 deep rose
        "accent": (0.557, 0.416, 0.337),   # #8E6A56 warm wood
        "bg":     (0.984, 0.953, 0.945),   # #FBF3F1
        "dark":   (0.22, 0.10, 0.12),
        "mid":    (0.52, 0.34, 0.38),
        "light":  (0.93, 0.86, 0.88),
    },
    # ── Natural / earthy schemes ──────────────────────────────────────────────
    "peach_cream": {
        "label":  "Peach & Cream",
        "theme":  (0.890, 0.561, 0.416),   # #E38F6A peach
        "accent": (0.580, 0.341, 0.224),   # #945739 terracotta
        "bg":     (0.996, 0.953, 0.933),   # #FEF3EE
        "dark":   (0.28, 0.16, 0.10),
        "mid":    (0.56, 0.40, 0.32),
        "light":  (0.96, 0.88, 0.84),
    },
    "sky_breeze": {
        "label":  "Sky Breeze",
        "theme":  (0.388, 0.651, 0.878),   # #63A6E0 sky blue
        "accent": (0.996, 0.788, 0.388),   # #FEC963 sunny yellow
        "bg":     (0.937, 0.961, 0.984),   # #EFF5FB
        "dark":   (0.13, 0.22, 0.32),
        "mid":    (0.40, 0.54, 0.66),
        "light":  (0.84, 0.90, 0.95),
    },
    "autumn_harvest": {
        "label":  "Autumn Harvest",
        "theme":  (0.667, 0.278, 0.122),   # #AA471F pumpkin
        "accent": (0.839, 0.635, 0.204),   # #D6A234 harvest gold
        "bg":     (0.984, 0.961, 0.929),   # #FBF5ED
        "dark":   (0.22, 0.12, 0.06),
        "mid":    (0.52, 0.35, 0.24),
        "light":  (0.94, 0.87, 0.82),
    },
    "mint_chip": {
        "label":  "Mint Chip",
        "theme":  (0.231, 0.682, 0.565),   # #3BAD90 mint
        "accent": (0.290, 0.200, 0.157),   # #4A3328 chocolate
        "bg":     (0.929, 0.980, 0.965),   # #EDF9F7
        "dark":   (0.10, 0.20, 0.16),
        "mid":    (0.35, 0.55, 0.46),
        "light":  (0.82, 0.93, 0.89),
    },
    "ocean_mist": {
        "label":  "Ocean Mist",
        "theme":  (0.388, 0.620, 0.698),   # #639EB2 muted teal
        "accent": (0.843, 0.761, 0.647),   # #D7C2A5 sandy beige
        "bg":     (0.929, 0.957, 0.969),   # #EEF4F7
        "dark":   (0.16, 0.26, 0.30),
        "mid":    (0.42, 0.58, 0.64),
        "light":  (0.84, 0.90, 0.93),
    },
    # ── New requested themes ──────────────────────────────────────────────────
    "midnight_blue": {
        "label":  "Midnight Blue",
        "theme":  (0.106, 0.145, 0.408),   # #1B2568 true midnight blue
        "accent": (0.839, 0.886, 1.000),   # #D6E2FF soft blue-white
        "bg":     (0.941, 0.953, 0.984),   # #F0F3FB ice blue white
        "dark":   (0.06, 0.08, 0.22),
        "mid":    (0.35, 0.42, 0.62),
        "light":  (0.82, 0.86, 0.96),
    },
    "coral_peach": {
        "label":  "Coral Peach",
        "theme":  (0.992, 0.424, 0.286),   # #FD6C49 warm coral
        "accent": (1.000, 0.765, 0.506),   # #FFC381 peach gold
        "bg":     (1.000, 0.957, 0.937),   # #FFF4EF warm peach cream
        "dark":   (0.28, 0.13, 0.08),
        "mid":    (0.60, 0.38, 0.28),
        "light":  (0.97, 0.88, 0.84),
    },
    "sage_green": {
        "label":  "Sage Green",
        "theme":  (0.384, 0.549, 0.361),   # #62 8C5C eucalyptus sage
        "accent": (0.855, 0.914, 0.820),   # #DAE9D1 sage frost
        "bg":     (0.937, 0.969, 0.929),   # #EFF7ED light sage
        "dark":   (0.10, 0.20, 0.10),
        "mid":    (0.36, 0.52, 0.34),
        "light":  (0.84, 0.93, 0.82),
    },
}

# ── PLANNER TIER PRESETS ──────────────────────────────────────────────────────
PLANNER_TIERS: dict[int, dict] = {
    1: {
        "label":            "Starter",
        "badge":            "STARTER",
        "interactive":      False,
        "sections":         ["monthly", "weekly", "notes"],
        "calendar_integration": "none",
        "subtitle_default": "Printable PDF · Print at Home",
        "design_desc":      "Clean minimal design — ideal for printing and hand-writing.",
    },
    2: {
        "label":            "Digital Pro",
        "badge":            "DIGITAL PRO",
        "interactive":      True,
        "sections":         ["monthly", "monthly_review", "month_at_a_glance",
                             "weekly", "habit_tracker", "goals",
                             "budget", "meal_plan", "notes"],
        "calendar_integration": "none",
        "subtitle_default": "Fillable PDF · GoodNotes · Notability · Xodo",
        "design_desc":      "Polished interactive design — fillable fields, hyperlinks, all sections.",
    },
    3: {
        "label":            "Connected",
        "badge":            "CONNECTED",
        "interactive":      True,
        "sections":         ["monthly", "monthly_review", "month_at_a_glance",
                             "weekly", "habit_tracker", "goals",
                             "budget", "meal_plan", "notes"],
        "calendar_integration": "google",
        "subtitle_default": "Fillable PDF · Google Calendar Sync · GoodNotes · Notability",
        "design_desc":      "Premium integrated design — live calendar links, dot-grid pages, rich decorative elements.",
    },
}


# ── PLANNER STYLE PRESETS (5 per tier, personality + sections + color) ────────
_S_ALL = ["monthly", "monthly_review", "month_at_a_glance",
          "weekly", "habit_tracker", "goals", "budget", "meal_plan", "notes"]
_S_CORE = ["monthly", "weekly", "notes"]
_S_LIFE = ["monthly", "monthly_review", "weekly", "habit_tracker", "goals", "notes"]
_S_BUSI = ["monthly", "monthly_review", "month_at_a_glance", "weekly", "goals", "budget", "notes"]

PLANNER_STYLES: dict[str, dict] = {
    # ── TIER 1 — STARTER (print-friendly, 5 styles) ──────────────────────────
    "t1_classic": {
        "tier": 1, "name": "Classic Minimal",
        "color_scheme": "minimal_mono", "sections": _S_CORE,
        "design_variant": "minimal",
        "subtitle": "Printable PDF · Clean & Simple",
        "fun": False,
    },
    "t1_bold_fun": {
        "tier": 1, "name": "Bold & Bright",
        "color_scheme": "bubblegum", "sections": _S_CORE,
        "design_variant": "fun",
        "subtitle": "Printable PDF · Fun & Colorful",
        "fun": True,
    },
    "t1_botanical": {
        "tier": 1, "name": "Botanical Garden",
        "color_scheme": "spring_blossom", "sections": _S_CORE,
        "design_variant": "botanical",
        "subtitle": "Printable PDF · Nature Inspired",
        "fun": False,
    },
    "t1_student": {
        "tier": 1, "name": "Student Planner",
        "color_scheme": "sky_breeze",
        "sections": ["monthly", "weekly", "notes"],
        "design_variant": "student",
        "subtitle": "Printable PDF · Academic Planner",
        "fun": True,
    },
    "t1_retro": {
        "tier": 1, "name": "Retro Vibes",
        "color_scheme": "retro_sunset", "sections": _S_CORE,
        "design_variant": "retro",
        "subtitle": "Printable PDF · 70s Inspired",
        "fun": True,
    },
    # ── TIER 2 — DIGITAL PRO (fillable, 5 styles) ────────────────────────────
    "t2_executive": {
        "tier": 2, "name": "Executive Pro",
        "color_scheme": "midnight_navy", "sections": _S_BUSI,
        "design_variant": "premium",
        "subtitle": "Fillable PDF · Professional Planner",
        "fun": False,
    },
    "t2_wellness": {
        "tier": 2, "name": "Wellness Journal",
        "color_scheme": "lavender_dreams", "sections": _S_LIFE,
        "design_variant": "wellness",
        "subtitle": "Fillable PDF · Mind Body Soul",
        "fun": False,
    },
    "t2_creative": {
        "tier": 2, "name": "Creative Studio",
        "color_scheme": "retro_sunset", "sections": _S_ALL,
        "design_variant": "creative",
        "subtitle": "Fillable PDF · For Creative Minds",
        "fun": True,
    },
    "t2_family": {
        "tier": 2, "name": "Family Organizer",
        "color_scheme": "mint_chip",
        "sections": ["monthly", "monthly_review", "weekly", "meal_plan", "habit_tracker", "notes"],
        "design_variant": "fun",
        "subtitle": "Fillable PDF · Family Life Planner",
        "fun": True,
    },
    "t2_dark_luxe": {
        "tier": 2, "name": "Dark Luxe",
        "color_scheme": "dark_academia", "sections": _S_ALL,
        "design_variant": "premium",
        "subtitle": "Fillable PDF · Dark Academia Aesthetic",
        "fun": False,
    },
    # ── TIER 3 — CONNECTED (premium, 5 styles) ───────────────────────────────
    "t3_elite": {
        "tier": 3, "name": "Elite Premium",
        "color_scheme": "art_deco_bk", "sections": _S_ALL,
        "calendar_integration": "both",
        "design_variant": "ultra_premium",
        "subtitle": "Connected PDF · Google & Apple Calendar · Premium",
        "extras": ["color_selector", "vision_board", "mood_tracker", "sticker_pack"],
        "fun": False,
    },
    "t3_manifestation": {
        "tier": 3, "name": "Manifestation Journal",
        "color_scheme": "midnight_purple", "sections": _S_LIFE,
        "calendar_integration": "google",
        "design_variant": "spiritual",
        "subtitle": "Connected PDF · Manifest · Dream · Achieve",
        "extras": ["color_selector", "vision_board", "mood_tracker", "sticker_pack"],
        "fun": False,
    },
    "t3_boss": {
        "tier": 3, "name": "Business Boss",
        "color_scheme": "deep_ocean", "sections": _S_ALL,
        "calendar_integration": "both",
        "design_variant": "business",
        "subtitle": "Connected PDF · KPIs · Goals · Revenue Tracking",
        "extras": ["color_selector", "sticker_pack"],
        "fun": False,
    },
    "t3_rainbow_fun": {
        "tier": 3, "name": "Rainbow Party",
        "color_scheme": "bubblegum", "sections": _S_LIFE,
        "calendar_integration": "google",
        "design_variant": "rainbow_fun",
        "subtitle": "Connected PDF · Fun · Colorful · Joyful",
        "extras": ["color_selector", "mood_tracker", "sticker_pack"],
        "fun": True,
    },
    "t3_boho_luxe": {
        "tier": 3, "name": "Boho Luxe",
        "color_scheme": "terracotta", "sections": _S_ALL,
        "calendar_integration": "google",
        "design_variant": "botanical",
        "subtitle": "Connected PDF · Boho Aesthetic · Earthy Luxury",
        "extras": ["color_selector", "vision_board", "mood_tracker", "sticker_pack"],
        "fun": False,
    },
}


def _ensure_dirs() -> None:
    os.makedirs(PRODUCT_FILES_DIR, exist_ok=True)


def _next_product_id(store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    nums = [int(p["id"][2:]) for p in products if p["id"].startswith("DP") and p["id"][2:].isdigit()]
    return f"DP{max(nums, default=0) + 1:03d}"


# ── TOOL DEFINITIONS ──────────────────────────────────────────────────────────

def _get_design_references(tool_input: dict) -> str:
    refs_meta = Path("data/design_refs_meta.json")
    if not refs_meta.exists():
        return "No design references uploaded yet. The user has not provided style examples."
    try:
        meta = json.loads(refs_meta.read_text())
    except Exception:
        return "No design references available."
    if not meta:
        return "No design references uploaded yet."
    lines = [f"Found {len(meta)} design reference(s) uploaded by the shop owner:\n"]
    for i, ref in enumerate(meta, 1):
        desc = ref.get('description', 'No description provided')
        lines.append(f"{i}. {ref['filename']} ({ref.get('size_kb','?')} KB)")
        lines.append(f"   Style/Theme: {desc}")
        lines.append(f"   Uploaded: {ref.get('uploaded_at','')[:10]}")
    lines.append("\nUse these style descriptions to guide your art creation — match the aesthetic, color palette, and themes described.")
    return "\n".join(lines)


TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "create_art_concept",
        "description": (
            "Design a detailed art concept for a digital product. Saves the concept "
            "to the data store with status 'concept'. Returns the new product ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Product title for Etsy listing"},
                "product_type": {
                    "type": "string",
                    "enum": ["digital_art", "planner", "printable", "wall_art", "clipart"],
                    "description": "Type of digital product",
                },
                "concept": {
                    "type": "string",
                    "description": "Detailed art concept: style, colors, mood, subject, composition",
                },
                "target_audience": {"type": "string", "description": "Who will buy this (e.g. 'boho home decor lovers')"},
                "dimensions": {
                    "type": "string",
                    "description": "Target dimensions, e.g. '3000x3000px 300dpi' or 'A4 PDF'",
                    "default": "3000x3000px 300dpi",
                },
                "price": {"type": "number", "description": "Planned selling price in USD"},
                "art_style": {
                    "type": "string",
                    "description": "Shop style letter+name, e.g. 'A - Bold Flat Illustration' or 'G - Japandi Wabi-Sabi'. Use one of A/B/C/C2/D/E/F/G/H/I/J/K from the system prompt style library.",
                },
            },
            "required": ["title", "product_type", "concept", "target_audience", "price"],
        },
    },
    {
        "name": "generate_digital_art",
        "description": (
            "Generate the actual image file for a product using DALL-E 3. "
            "Requires OPENAI_API_KEY in .env. Updates product status to 'generated'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
                "dalle_prompt": {
                    "type": "string",
                    "description": "Refined DALL-E 3 prompt. Be specific: style, colors, composition, mood.",
                },
                "image_size": {
                    "type": "string",
                    "enum": ["1024x1024", "1536x1024", "1024x1536"],
                    "description": "1024x1024=square, 1536x1024=landscape, 1024x1536=portrait (best for wall art)",
                    "default": "1024x1536",
                },
                "quality": {
                    "type": "string",
                    "enum": ["standard", "high"],
                    "description": "high produces the most detailed images. Always use high for sellable products.",
                    "default": "high",
                },
            },
            "required": ["product_id", "dalle_prompt"],
        },
    },
    {
        "name": "create_digital_planner",
        "description": (
            "Generate a premium interactive PDF planner using reportlab. "
            "Creates a ready-to-sell digital planner with: a stunning cover page, "
            "hyperlinked side-tab navigation (GoodNotes/Notability/Xodo compatible), "
            "fillable text form fields, interactive checkboxes, "
            "monthly/weekly/daily/habit/goals/notes/budget/meal sections, "
            "optional monthly review + month-at-a-glance companion pages, "
            "and a 'How to Use' instruction page. "
            "Choose one of 12 curated color scheme packages."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
                "planner_title": {"type": "string", "description": "Planner title shown on the cover"},
                "planner_style": {
                    "type": "string",
                    "enum": [
                        "t1_classic", "t1_bold_fun", "t1_botanical", "t1_student", "t1_retro",
                        "t2_executive", "t2_wellness", "t2_creative", "t2_family", "t2_dark_luxe",
                        "t3_elite", "t3_manifestation", "t3_boss", "t3_rainbow_fun", "t3_boho_luxe",
                    ],
                    "description": (
                        "Planner style preset — auto-sets tier, color scheme, sections, and design. "
                        "TIER 1 (print-only): t1_classic=minimal mono, t1_bold_fun=bubblegum/fun, "
                        "t1_botanical=spring blossom/nature, t1_student=sky breeze/academic, t1_retro=retro sunset/70s. "
                        "TIER 2 (fillable PDF): t2_executive=navy/corporate, t2_wellness=lavender/mindful, "
                        "t2_creative=retro/artistic, t2_family=mint/family organizer, t2_dark_luxe=dark academia. "
                        "TIER 3 (connected+premium): t3_elite=art deco black/gold, "
                        "t3_manifestation=purple/spiritual+vision board, t3_boss=ocean blue/business KPIs, "
                        "t3_rainbow_fun=bubblegum/party+stickers, t3_boho_luxe=terracotta/earthy luxury. "
                        "Style auto-sets tier, color, sections. Any explicit param overrides the style."
                    ),
                },
                "color_scheme": {
                    "type": "string",
                    "enum": [
                        "sage_cream", "dusty_rose", "midnight_navy", "terracotta",
                        "lavender_dreams", "dark_academia", "blush_gold", "minimal_mono",
                        "mocha_latte", "wine_burgundy", "ice_blue", "forest_deep",
                        "cotton_candy", "bubblegum", "lemon_zest", "neon_pop",
                        "retro_sunset", "tropical", "spring_blossom",
                        "midnight_purple", "deep_ocean", "art_deco_bk", "rosewood",
                        "peach_cream", "sky_breeze", "autumn_harvest",
                        "mint_chip", "ocean_mist",
                        "midnight_blue", "coral_peach", "sage_green",
                    ],
                    "description": (
                        "30 color schemes. Neutral/classic: sage_cream, dusty_rose, midnight_navy, terracotta, "
                        "lavender_dreams, dark_academia, blush_gold, minimal_mono, mocha_latte, wine_burgundy, "
                        "ice_blue, forest_deep, ocean_mist. "
                        "Fun/bold: cotton_candy, bubblegum, lemon_zest, neon_pop, retro_sunset, tropical, "
                        "spring_blossom, sky_breeze, peach_cream, mint_chip, autumn_harvest. "
                        "Dark/premium: midnight_purple, deep_ocean, art_deco_bk, rosewood. "
                        "OnBrandCraftz planners: midnight_blue (DP1028), coral_peach (DP1029), sage_green. "
                        "Default: sage_cream."
                    ),
                    "default": "sage_cream",
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Add fillable PDF form fields and interactive checkboxes (always true for premium planners). Works in GoodNotes, Notability, Xodo, Adobe Reader, Preview.",
                    "default": True,
                },
                "planner_format": {
                    "type": "string",
                    "enum": ["letter", "a4"],
                    "description": "Page size. letter=8.5x11in (US standard), a4=210x297mm (international). Default: letter.",
                    "default": "letter",
                },
                "year": {
                    "type": "integer",
                    "description": "Planner year. Use 0 for undated (evergreen, outsells dated 3:1).",
                },
                "weekly_layout": {
                    "type": "string",
                    "enum": ["horizontal", "vertical", "lined", "hourly"],
                    "description": (
                        "Weekly page layout style. "
                        "horizontal=days stacked with per-day sections (richest, recommended), "
                        "vertical=7 day columns across the page, "
                        "lined=simple lined layout by day, "
                        "hourly=time-slot schedule per day. Default: horizontal."
                    ),
                    "default": "horizontal",
                },
                "planner_tier": {
                    "type": "integer",
                    "enum": [1, 2, 3],
                    "description": (
                        "Planner tier — sets all defaults (sections, interactivity, calendar, design level). "
                        "1=Starter: print-ready PDF, clean minimal design, monthly+weekly+notes, no form fields, lowest price. "
                        "2=Digital Pro: polished design, all sections, fully fillable fields, GoodNotes/Notability compatible, mid price. "
                        "3=Connected: premium dot-grid design, everything in 2 plus live Google & Apple Calendar links on every dated cell, highest price. "
                        "Any explicit param overrides the tier default."
                    ),
                },
                "calendar_integration": {
                    "type": "string",
                    "enum": ["none", "google", "apple", "both"],
                    "description": (
                        "Embed calendar shortcut links in daily/monthly pages. "
                        "google=Google Calendar links (works iOS + Android + web), "
                        "apple=Apple Calendar links via calshow: scheme (iOS/macOS only), "
                        "both=Google + Apple links side by side, "
                        "none=no integration. Only applies to dated planners (year != 0). Default: none."
                    ),
                    "default": "none",
                },
                "include_sections": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "monthly", "monthly_review", "month_at_a_glance",
                            "weekly", "daily",
                            "habit_tracker", "goals", "notes", "budget", "meal_plan",
                        ],
                    },
                    "description": (
                        "Sections to include. Premium full planner: "
                        "['monthly','monthly_review','month_at_a_glance','weekly','habit_tracker','goals','notes']. "
                        "monthly_review=end-of-month reflection page, "
                        "month_at_a_glance=overview with trends/priorities/achievements."
                    ),
                    "default": ["monthly", "weekly", "habit_tracker", "goals", "notes"],
                },
                "subtitle": {
                    "type": "string",
                    "description": "Subtitle on the cover, e.g. 'Undated · Fillable PDF · GoodNotes Compatible'.",
                },
                "tab_color": {
                    "type": "string",
                    "enum": ["scheme", "white", "light_pink", "brown", "olive", "black"],
                    "description": "Side navigation tab color. scheme=uses the color scheme's theme color (default), or choose: white, light_pink, brown, olive, black.",
                    "default": "scheme",
                },
                "cover_image_path": {
                    "type": "string",
                    "description": "Path to cover art from generate_digital_art. Embeds the image in the cover top panel for a premium handcrafted look.",
                },
            },
            "required": ["product_id", "planner_title"],
        },
    },
    {
        "name": "list_digital_products",
        "description": "List all digital products with their status, file info, and QC results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["all", "concept", "generated", "qc_pending", "approved", "rejected", "listed"],
                    "description": "Filter by product status",
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_digital_product",
        "description": "Get full details of a specific digital product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"}
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "update_product_status",
        "description": "Update the status of a digital product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["concept", "generated", "qc_pending", "approved", "rejected", "listed"],
                },
                "notes": {"type": "string", "description": "Optional notes about the status change"},
            },
            "required": ["product_id", "status"],
        },
    },
    {
        "name": "get_design_references",
        "description": "Get the list of design reference images uploaded by the shop owner. These images represent the style, color palette, and aesthetic the owner wants. Always call this BEFORE creating any new art to ensure your work matches their vision.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "create_size_bundle",
        "description": (
            "Generate a ZIP file containing the product's art image at 8 standard print sizes "
            "(8×8, 12×12, 24×24 square; 12×14, 16×20, 18×24, 24×36, 30×40 portrait), all JPEG "
            "at 300 DPI with a README. Call this after generate_digital_art — it produces the "
            "actual Etsy upload file buyers download. Top sellers always include all sizes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "create_frame_mockup",
        "description": (
            "Generate a framed wall-scene mockup image for an Etsy listing thumbnail. "
            "Composites the product art into a realistic frame with drop shadow against a "
            "painted wall background. Call after generate_digital_art. Create 2–3 mockups "
            "with different frame/wall combos for listing photos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
                "frame_style": {
                    "type": "string",
                    "enum": ["natural_wood", "barnwood", "walnut", "dark_walnut", "oak", "maple", "cherry",
                             "black", "white", "gold", "brushed_gold", "silver"],
                    "description": (
                        "Frame material. "
                        "natural_wood=medium warm oak; barnwood=rustic distressed reclaimed wood (cottagecore/farmhouse/Victorian pastoral); "
                        "walnut=rich dark brown modern; dark_walnut=near-black wood; oak=light Scandi; maple=warm golden light; cherry=warm red-brown; "
                        "black=matte modern; white=gallery/Scandi; gold=ornate traditional; brushed_gold=contemporary brass; silver=modern metal. "
                        "Match to art style: barnwood for pastoral/vintage/cottagecore/Old Masters; walnut for dark moody/celestial; "
                        "oak for botanical/Japandi/minimalist; brushed_gold for Mediterranean/luxury; silver for modern/sci-fi/graphic."
                    ),
                    "default": "natural_wood",
                },
                "wall_color": {
                    "type": "string",
                    "enum": ["warm_gray", "white", "cream", "dark", "sage", "terracotta", "dusty_blue"],
                    "description": "Wall background color. warm_gray is most versatile; dark for moody/celestial art; cream for farmhouse/botanical.",
                    "default": "warm_gray",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "create_room_composite",
        "description": (
            "Generate empty room background photos (via AI) then composite the REAL art file "
            "into each room at proper scale. This guarantees the listing photos show the EXACT "
            "same art as the download — never an AI re-imagination. Always use this instead of "
            "asking the AI to 'include the painting' in a room scene. "
            "Replaces the need for manually generated room settings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
                "frame_style": {
                    "type": "string",
                    "enum": ["natural_wood", "barnwood", "walnut", "dark_walnut", "oak", "maple", "cherry",
                             "black", "white", "gold", "brushed_gold", "silver"],
                    "description": "Frame to use in the room scenes.",
                    "default": "natural_wood",
                },
                "room_styles": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["kitchen_dining", "living_room", "entryway", "bedroom", "pub"]},
                    "description": "Which room types to generate. Default: kitchen_dining, living_room, entryway.",
                    "default": ["kitchen_dining", "living_room", "entryway"],
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "create_size_comparison",
        "description": (
            "Create a size guide photo showing the REAL art composited at 3 print sizes "
            "(8×10, 16×20, 24×36) side-by-side on a clean wall. Labels each size. "
            "Always use this for size comparison — never generate a size comparison with AI "
            "because the painting would differ from the download."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
                "frame_style": {
                    "type": "string",
                    "enum": ["natural_wood", "barnwood", "walnut", "dark_walnut", "oak", "maple", "cherry",
                             "black", "white", "gold", "brushed_gold", "silver"],
                    "default": "natural_wood",
                },
                "wall_color": {
                    "type": "string",
                    "enum": ["warm_gray", "white", "cream", "dark", "sage", "terracotta", "dusty_blue"],
                    "default": "warm_gray",
                },
            },
            "required": ["product_id"],
        },
    },
    SUBMIT_IDEA_DEFINITION,
]


# ── TOOL EXECUTOR ─────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "create_art_concept":
        return _create_art_concept(tool_input, store)
    if tool_name == "generate_digital_art":
        return _generate_digital_art(tool_input, store)
    if tool_name == "create_digital_planner":
        return _create_digital_planner(tool_input, store)
    if tool_name == "list_digital_products":
        return _list_digital_products(tool_input.get("status_filter", "all"), store)
    if tool_name == "get_digital_product":
        return _get_digital_product(tool_input["product_id"], store)
    if tool_name == "update_product_status":
        return _update_product_status(tool_input, store)
    elif tool_name == "get_design_references":
        return _get_design_references(tool_input)
    if tool_name == "create_size_bundle":
        return _create_size_bundle(tool_input, store)
    if tool_name == "create_frame_mockup":
        return _create_frame_mockup(tool_input, store)
    if tool_name == "create_room_composite":
        return _create_room_composite(tool_input, store)
    if tool_name == "create_size_comparison":
        return _create_size_comparison(tool_input, store)
    if tool_name == "submit_idea":
        return handle_submit_idea(tool_input)
    return f"Unknown art creation tool: {tool_name}"


# ── IMPLEMENTATIONS ───────────────────────────────────────────────────────────

def _create_art_concept(data: dict, store: DataStore) -> str:
    _ensure_dirs()
    product_id = _next_product_id(store)

    product: dict[str, Any] = {
        "id": product_id,
        "title": data["title"],
        "product_type": data["product_type"],
        "art_style": data.get("art_style", ""),
        "concept": data["concept"],
        "target_audience": data["target_audience"],
        "dimensions": data.get("dimensions", "3000x3000px 300dpi"),
        "price": data["price"],
        "status": "concept",
        "file_path": None,
        "file_format": None,
        "file_size_kb": None,
        "qc_status": None,
        "qc_notes": None,
        "etsy_listing_id": None,
        "created_at": str(date.today()),
        "updated_at": str(date.today()),
    }

    products = store.get("digital_products", default=[])
    products.append(product)
    store.set(products, "digital_products")
    store.save()

    return json.dumps({
        "success": True,
        "product_id": product_id,
        "title": product["title"],
        "status": "concept",
        "next_step": "Use generate_digital_art or create_digital_planner to produce the file.",
    }, indent=2)


def _generate_placeholder_art(data: dict, product: dict, store: DataStore) -> str:
    """Generate a styled PNG concept card using Pillow when no OpenAI key is set."""
    product_id = product["id"]
    file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.png")
    prompt = data["dalle_prompt"]
    title = product.get("title", product_id)

    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        W, H = 1024, 1024
        # Build a gradient background by drawing rows
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        # Soft purple-to-teal gradient
        for y in range(H):
            t = y / H
            r = int(80  + (30  - 80)  * t)
            g = int(60  + (140 - 60)  * t)
            b = int(140 + (160 - 140) * t)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Decorative circles
        for cx, cy, cr, alpha in [(150,150,200,40),(874,874,180,30),(512,200,120,25)]:
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill=(255,255,255,alpha))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

        # Card background
        margin = 60
        draw.rounded_rectangle([margin, margin, W-margin, H-margin],
                                radius=32, fill=(255, 255, 255, 0))
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([margin, margin, W-margin, H-margin],
                              radius=32, fill=(20, 20, 40, 180))
        img = Image.alpha_composite(img.convert("RGBA"), card).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Try to load a font, fall back to default
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
            font_body  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except Exception:
            font_title = ImageFont.load_default()
            font_body  = font_title
            font_small = font_title

        # Badge
        badge_text = "CONCEPT — AI ART PENDING"
        draw.rounded_rectangle([margin+20, margin+20, margin+320, margin+50],
                                radius=14, fill=(255, 180, 0))
        draw.text((margin+30, margin+24), badge_text, fill=(20,20,20), font=font_small)

        # Title
        y = margin + 75
        for line in textwrap.wrap(title, 28):
            draw.text((margin+30, y), line, fill=(255,255,255), font=font_title)
            y += 48

        # Divider
        y += 10
        draw.line([(margin+30, y), (W-margin-30, y)], fill=(255,200,100), width=2)
        y += 20

        # Prompt text
        draw.text((margin+30, y), "Design Concept:", fill=(180,220,255), font=font_small)
        y += 28
        for line in textwrap.wrap(prompt, 52)[:12]:
            draw.text((margin+30, y), line, fill=(220,220,220), font=font_body)
            y += 30

        # Footer
        draw.text((margin+30, H-margin-40),
                  f"OnBrandCraftz  •  {product_id}  •  Add OPENAI_API_KEY to generate real art",
                  fill=(150, 150, 180), font=font_small)

        img.save(file_path, "PNG")
        file_size_kb = os.path.getsize(file_path) // 1024

    except ImportError:
        # Pillow not available — write minimal 1×1 white PNG
        import struct, zlib
        def _png1x1():
            sig = b'\x89PNG\r\n\x1a\n'
            def chunk(name, data):
                c = zlib.crc32(name + data) & 0xffffffff
                return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)
            ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
            idat = zlib.compress(b'\x00\xff\xff\xff')
            return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
        with open(file_path, "wb") as f:
            f.write(_png1x1())
        file_size_kb = 1

    product["is_placeholder"] = True
    product["file_hash"] = None

    product["file_path"] = file_path
    product["file_format"] = "PNG"
    product["file_size_kb"] = file_size_kb
    product["status"] = "qc_pending"
    product["updated_at"] = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success": True,
        "product_id": product_id,
        "file_path": file_path,
        "file_size_kb": file_size_kb,
        "mode": "concept_card",
        "note": "Concept card created with Pillow. Add OPENAI_API_KEY to generate real AI art.",
        "status": "qc_pending",
        "next_step": "Send to Quality Check Agent for review. Add OPENAI_API_KEY for real art.",
    }, indent=2)


def _upscale_for_print(src_path: str, dst_path: str, target_px: int = 4500) -> None:
    """Upscale to print resolution with multi-pass sharpening for top Etsy quality."""
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        img = Image.open(src_path).convert("RGB")
        w, h = img.size

        # Multi-pass upscale: 2x steps prevent aliasing artifacts vs single large jump
        # Use min(img.size) so the SHORTEST side reaches target_px (QC requirement)
        while min(img.size) < target_px:
            scale = min(2.0, target_px / min(img.size))
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

        # Three-pass sharpening: recover LANCZOS softness → fine detail → final crisp
        img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=2))
        img = img.filter(ImageFilter.UnsharpMask(radius=0.6, percent=90,  threshold=1))
        img = img.filter(ImageFilter.UnsharpMask(radius=0.3, percent=50,  threshold=0))

        # Vibrancy + contrast boost for Etsy thumbnail pop (thumbnails compress heavily)
        img = ImageEnhance.Color(img).enhance(1.12)
        img = ImageEnhance.Contrast(img).enhance(1.08)
        img = ImageEnhance.Sharpness(img).enhance(1.15)

        # Save at 97% JPEG — noticeably better fine detail vs 95%, still well under 20 MB
        jpg_path = os.path.splitext(dst_path)[0] + ".jpg"
        img.save(jpg_path, "JPEG", quality=97, dpi=(300, 300), optimize=True)
        # If caller expected a different extension, also write there (no-op if same)
        if jpg_path != dst_path:
            import shutil as _shutil
            _shutil.move(jpg_path, dst_path)
    except ImportError:
        raise RuntimeError("Pillow is required for print upscaling — run: pip install Pillow")
    # Clean up raw file
    try:
        os.remove(src_path)
    except OSError:
        pass


# ── MULTI-SIZE BUNDLE ─────────────────────────────────────────────────────────

_BUNDLE_SIZES = [
    # (filename_prefix, width_inches, height_inches)
    ("8x8",   8,  8),
    ("12x12", 12, 12),
    ("24x24", 24, 24),
    ("12x14", 12, 14),
    ("16x20", 16, 20),
    ("18x24", 18, 24),
    ("24x36", 24, 36),
    ("30x40", 30, 40),
]
_BUNDLE_DPI = 300


def _create_size_bundle(data: dict, store: DataStore) -> str:
    import zipfile
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        return json.dumps({"error": "Pillow required — run: pip install Pillow"})

    product_id = data["product_id"]
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})
    src = product.get("file_path")
    if not src or not os.path.exists(src):
        return json.dumps({"error": "No image file found. Call generate_digital_art first."})

    master = Image.open(src).convert("RGB")

    # Upscale master to 6000px short side (covers up to 20×30" at true 300 DPI)
    target_px = 6000
    while min(master.size) < target_px:
        scale = min(2.0, target_px / min(master.size))
        master = master.resize(
            (int(master.width * scale), int(master.height * scale)), Image.LANCZOS
        )
    master = master.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))

    bundle_dir = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_bundle_tmp")
    os.makedirs(bundle_dir, exist_ok=True)

    created: list[tuple[str, str]] = []
    for prefix, win, hin in _BUNDLE_SIZES:
        tw, th = win * _BUNDLE_DPI, hin * _BUNDLE_DPI
        src_r = master.width / master.height
        tgt_r = tw / th

        if src_r > tgt_r + 0.02:
            cw = int(master.height * tgt_r)
            x0 = (master.width - cw) // 2
            crop = master.crop((x0, 0, x0 + cw, master.height))
        elif src_r < tgt_r - 0.02:
            ch = int(master.width / tgt_r)
            y0 = (master.height - ch) // 2
            crop = master.crop((0, y0, master.width, y0 + ch))
        else:
            crop = master

        sized = crop.resize((tw, th), Image.LANCZOS)
        sized = sized.filter(ImageFilter.UnsharpMask(radius=0.6, percent=80, threshold=1))
        fname = f"{prefix}in_300dpi.jpg"
        sized.save(os.path.join(bundle_dir, fname), "JPEG",
                   quality=97, dpi=(_BUNDLE_DPI, _BUNDLE_DPI), optimize=True)
        created.append((fname, f"{win}×{hin} inches"))

    zip_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_allsizes.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        readme = (
            f"OnBrandCraftz — Print-Ready Digital Download\n"
            f"{'=' * 48}\n"
            f"Product: {product.get('title', product_id)}\n\n"
            f"FILES INCLUDED ({len(created)} sizes, all 300 DPI JPEG):\n\n"
            + "".join(f"  • {fname}  →  {desc}\n" for fname, desc in created)
            + "\n\nPRINTING: Select the file matching your frame size.\n"
            "Set print dimensions to the file's inches at 300 DPI / best quality.\n"
            "Recommended print labs: Mpix, Nations Photo Lab, Printful, Canva Print.\n\n"
            "Thank you for your purchase!\n"
        )
        zf.writestr("READ_ME_FIRST.txt", readme)
        for fname, _ in created:
            zf.write(os.path.join(bundle_dir, fname), fname)

    import shutil as _shutil
    _shutil.rmtree(bundle_dir, ignore_errors=True)

    product["bundle_zip_path"] = zip_path
    product["bundle_sizes"] = [f"{w}x{h}" for _, w, h in _BUNDLE_SIZES]
    product["updated_at"] = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success": True,
        "product_id": product_id,
        "zip_path": zip_path,
        "sizes_included": [f"{w}×{h}in" for _, w, h in _BUNDLE_SIZES],
        "note": "ZIP ready — upload this as the Etsy digital download file.",
    }, indent=2)


# ── FRAME MOCKUP ──────────────────────────────────────────────────────────────

_FRAME_PALETTES = {
    # Keys: base/hi/lo colors, grain type, frame_w (molding px), mat_w (mat px), bevel px
    # ── Original 4 ──
    "natural_wood": {"base": (139, 100, 48), "hi": (180, 138, 75), "lo": (82, 58, 22),  "grain": "wood",     "frame_w": 36, "mat_w": 16, "bevel": 14},
    "black":        {"base": (30,  27,  24),  "hi": (55,  48,  40),  "lo": (14,  12,  10), "grain": "flat",  "frame_w": 22, "mat_w": 16, "bevel": 10},
    "white":        {"base": (238, 235, 230), "hi": (255, 255, 255), "lo": (190, 185, 178), "grain": "flat", "frame_w": 14, "mat_w": 26, "bevel": 6},
    "gold":         {"base": (175, 138, 48),  "hi": (220, 185, 88),  "lo": (110, 84,  22),  "grain": "metal","frame_w": 44, "mat_w": 20, "bevel": 18},
    # ── Real-world wood frames ──
    "barnwood":     {"base": (72,  50,  30),  "hi": (105, 78,  52),  "lo": (32,  20,  10),  "grain": "barnwood","frame_w": 54, "mat_w": 0,  "bevel": 20},
    "walnut":       {"base": (90,  58,  30),  "hi": (128, 88,  50),  "lo": (50,  30,  12),  "grain": "wood",  "frame_w": 32, "mat_w": 16, "bevel": 12},
    "dark_walnut":  {"base": (48,  30,  15),  "hi": (75,  50,  28),  "lo": (22,  12,  5),   "grain": "wood",  "frame_w": 28, "mat_w": 14, "bevel": 12},
    "oak":          {"base": (190, 152, 88),  "hi": (222, 188, 128), "lo": (140, 108, 55),  "grain": "wood",  "frame_w": 14, "mat_w": 22, "bevel": 6},
    "maple":        {"base": (210, 175, 110), "hi": (238, 210, 155), "lo": (165, 130, 72),  "grain": "wood",  "frame_w": 14, "mat_w": 22, "bevel": 6},
    "cherry":       {"base": (148, 72,  45),  "hi": (188, 108, 72),  "lo": (90,  40,  20),  "grain": "wood",  "frame_w": 26, "mat_w": 16, "bevel": 10},
    # ── Modern / metal frames ──
    "brushed_gold": {"base": (185, 155, 75),  "hi": (228, 198, 120), "lo": (128, 102, 40),  "grain": "brushed","frame_w": 16, "mat_w": 20, "bevel": 8},
    "silver":       {"base": (172, 178, 185), "hi": (215, 220, 225), "lo": (115, 120, 128), "grain": "brushed","frame_w": 12, "mat_w": 22, "bevel": 6},
}
_WALL_PALETTES = {
    "warm_gray":   (215, 208, 198),
    "white":       (248, 246, 244),
    "cream":       (238, 230, 215),
    "dark":        (48,  42,  38),
    "sage":        (182, 196, 180),
    "terracotta":  (210, 185, 165),
    "dusty_blue":  (185, 198, 212),
}


def _create_frame_mockup(data: dict, store: DataStore) -> str:
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    except ImportError:
        return json.dumps({"error": "Pillow required — run: pip install Pillow"})

    product_id = data["product_id"]
    frame_style = data.get("frame_style", "natural_wood")
    wall_key    = data.get("wall_color", "warm_gray")

    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})
    src = product.get("file_path")
    if not src or not os.path.exists(src):
        return json.dumps({"error": "No image file found. Call generate_digital_art first."})

    pal      = _FRAME_PALETTES.get(frame_style, _FRAME_PALETTES["natural_wood"])
    wall_rgb = _WALL_PALETTES.get(wall_key, _WALL_PALETTES["warm_gray"])

    art = Image.open(src).convert("RGB")
    aw, ah = art.size

    # Scale art so its longest side = 920px inside the mockup
    scale = 920 / max(aw, ah)
    art   = art.resize((int(aw * scale), int(ah * scale)), Image.LANCZOS)
    aw, ah = art.size

    FRAME_W = pal.get("frame_w", 44)   # molding width — per frame style
    MAT_W   = pal.get("mat_w",   18)   # white mat — per frame style
    BEVEL   = pal.get("bevel",    7)   # bevel depth

    total_w = aw + 2 * (MAT_W + FRAME_W)
    total_h = ah + 2 * (MAT_W + FRAME_W)

    canvas_w = total_w + 420
    canvas_h = total_h + 440

    # ── Wall background (subtle top-to-bottom gradient) ──
    canvas = Image.new("RGB", (canvas_w, canvas_h), wall_rgb)
    draw   = ImageDraw.Draw(canvas)
    for y in range(canvas_h):
        fade = int(y / canvas_h * 28)
        c    = tuple(max(0, v - fade) for v in wall_rgb)
        draw.line([(0, y), (canvas_w, y)], fill=c)

    # ── Drop shadow (gaussian-blurred rectangle offset below-right) ──
    cx0 = (canvas_w - total_w) // 2
    cy0 = (canvas_h - total_h) // 2
    shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    sd.rectangle([cx0 + 16, cy0 + 20, cx0 + total_w + 16, cy0 + total_h + 20],
                 fill=(0, 0, 0, 145))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=24))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow_layer).convert("RGB")

    # ── Frame body ──
    draw = ImageDraw.Draw(canvas)
    fx0, fy0 = cx0, cy0
    fx1, fy1 = cx0 + total_w, cy0 + total_h
    draw.rectangle([fx0, fy0, fx1, fy1], fill=pal["base"])

    # Bevel: top/left lighter (highlight), bottom/right darker (shadow)
    for b in range(BEVEL):
        t = 1.0 - b / BEVEL
        hi = tuple(int(pal["base"][i] + (pal["hi"][i] - pal["base"][i]) * t) for i in range(3))
        lo = tuple(int(pal["base"][i] + (pal["lo"][i] - pal["base"][i]) * t) for i in range(3))
        draw.line([(fx0+b, fy0+b), (fx1-b, fy0+b)], fill=hi)   # top
        draw.line([(fx0+b, fy0+b), (fx0+b, fy1-b)], fill=hi)   # left
        draw.line([(fx0+b, fy1-b), (fx1-b, fy1-b)], fill=lo)   # bottom
        draw.line([(fx1-b, fy0+b), (fx1-b, fy1-b)], fill=lo)   # right

    # ── White mat ──
    mx0, my0 = fx0 + FRAME_W, fy0 + FRAME_W
    mx1, my1 = fx1 - FRAME_W, fy1 - FRAME_W
    draw.rectangle([mx0, my0, mx1, my1], fill=(250, 247, 242))
    for s in range(5):   # inner mat shadow suggests depth
        v = 215 - s * 14
        draw.rectangle([mx0+s, my0+s, mx1-s, my1-s], outline=(v, v-2, v-5))

    # ── Paste art ──
    ax0, ay0 = mx0 + MAT_W, my0 + MAT_W
    canvas.paste(art, (ax0, ay0))

    # ── Subtle diagonal glare over art (top-left catch-light) ──
    glare = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
    gd    = ImageDraw.Draw(glare)
    for y in range(ah):
        p = y / ah
        if p < 0.30:
            alpha = int((0.30 - p) / 0.30 * 20)
            gd.line([(0, y), (aw, y)], fill=(255, 255, 255, alpha))
    glare = glare.filter(ImageFilter.GaussianBlur(radius=4))
    art_r = Image.alpha_composite(art.convert("RGBA"), glare).convert("RGB")
    canvas.paste(art_r, (ax0, ay0))

    # ── Final contrast boost for Etsy thumbnail pop ──
    canvas = ImageEnhance.Contrast(canvas).enhance(1.06)

    mockup_path = os.path.join(
        PRODUCT_FILES_DIR, f"{product_id}_mockup_{frame_style}_{wall_key}.jpg"
    )
    canvas.save(mockup_path, "JPEG", quality=95, dpi=(150, 150), optimize=True)

    mockups = product.get("mockup_paths", [])
    if mockup_path not in mockups:
        mockups.append(mockup_path)
    product["mockup_paths"] = mockups
    product["updated_at"]   = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success": True,
        "product_id": product_id,
        "mockup_path": mockup_path,
        "frame_style": frame_style,
        "wall_color": wall_key,
        "note": "Mockup ready — use as Etsy listing thumbnail image.",
    }, indent=2)


# ── ROOM COMPOSITE + SIZE COMPARISON ─────────────────────────────────────────

def _render_framed_art_rgba(art_img: Any, frame_style: str, long_side_px: int,
                            ambient_rgb: tuple = (215, 208, 198)) -> tuple:
    """Render art in a photorealistic frame on a transparent RGBA canvas.
    ambient_rgb: sampled wall color used to tint the frame to match room lighting.
    Returns (RGBA PIL Image, (art_x0, art_y0, art_x1, art_y1)).
    """
    import random
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

    pal = _FRAME_PALETTES.get(frame_style, _FRAME_PALETTES["natural_wood"])

    aw, ah = art_img.size
    scale = long_side_px / max(aw, ah)
    art = art_img.resize((int(aw * scale), int(ah * scale)), Image.LANCZOS)
    aw, ah = art.size

    FRAME_W = pal.get("frame_w", 48)   # molding width — per frame style
    MAT_W   = pal.get("mat_w",   16)   # white mat — per frame style
    BEVEL   = pal.get("bevel",   18)   # depth of 3-D bevel on molding face
    PAD     = 60                        # transparent bleed for shadow

    total_w = aw + 2 * (MAT_W + FRAME_W)
    total_h = ah + 2 * (MAT_W + FRAME_W)
    cw, ch  = total_w + PAD * 2, total_h + PAD * 2

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    # ── Realistic drop shadow (two-layer: hard contact + soft cast) ──
    for offset, blur, alpha in [(10, 6, 90), (18, 28, 60)]:
        s = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        sd = ImageDraw.Draw(s)
        sd.rectangle([PAD + offset, PAD + offset,
                      PAD + total_w + offset, PAD + total_h + offset],
                     fill=(0, 0, 0, alpha))
        s = s.filter(ImageFilter.GaussianBlur(radius=blur))
        canvas = Image.alpha_composite(canvas, s)

    draw = ImageDraw.Draw(canvas)
    fx0, fy0 = PAD, PAD
    fx1, fy1 = PAD + total_w, PAD + total_h

    # ── Frame base fill ──
    base = pal["base"]
    draw.rectangle([fx0, fy0, fx1, fy1], fill=(*base, 255))

    # ── Wood grain texture (natural_wood only; gold/black/white get subtle variation) ──
    fw_px = fx1 - fx0
    fh_px = fy1 - fy0
    rng = random.Random(42)   # deterministic seed so grain is repeatable
    grain_layer = Image.new("RGBA", (fw_px, fh_px), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain_layer)

    grain_type = pal.get("grain", "flat")

    if grain_type == "wood":
        # Horizontal fiber lines with slight brightness variation and waviness
        y = 0
        while y < fh_px:
            step   = rng.randint(2, 5)
            bright = rng.randint(-22, 18)
            r2 = max(0, min(255, base[0] + bright))
            g2 = max(0, min(255, base[1] + int(bright * 0.7)))
            b2 = max(0, min(255, base[2] + int(bright * 0.4)))
            alpha = rng.randint(55, 120)
            pts = []
            cx = 0
            wy = y + rng.randint(-1, 1)
            while cx <= fw_px:
                wy += rng.uniform(-0.3, 0.3)
                pts.append((cx, wy))
                cx += 40
            if len(pts) >= 2:
                gd.line(pts, fill=(r2, g2, b2, alpha), width=step)
            y += step

    elif grain_type == "barnwood":
        # Wide bold grain lines, high contrast — reclaimed/aged wood character
        y = 0
        while y < fh_px:
            step   = rng.randint(2, 8)
            bright = rng.randint(-38, 28)
            r2 = max(0, min(255, base[0] + bright))
            g2 = max(0, min(255, base[1] + int(bright * 0.8)))
            b2 = max(0, min(255, base[2] + int(bright * 0.6)))
            alpha = rng.randint(80, 170)
            pts = []
            cx = 0
            wy = y + rng.randint(-2, 2)
            while cx <= fw_px:
                wy += rng.uniform(-0.6, 0.6)
                pts.append((cx, wy))
                cx += 30
            if len(pts) >= 2:
                gd.line(pts, fill=(r2, g2, b2, alpha), width=step)
            y += step
        # Deep pitting/distress marks: short dark vertical scratches
        for _ in range(rng.randint(20, 40)):
            sx = rng.randint(0, fw_px)
            sy = rng.randint(0, fh_px)
            length = rng.randint(6, 22)
            dark = rng.randint(100, 160)
            gd.line([(sx, sy), (sx + rng.randint(-2, 2), sy + length)],
                    fill=(10, 6, 2, dark), width=rng.randint(1, 2))

    elif grain_type == "brushed":
        # Fine horizontal parallel lines — brushed metal / brushed gold texture
        for y in range(0, fh_px, 2):
            bright = rng.randint(-18, 18)
            r2 = max(0, min(255, base[0] + bright))
            g2 = max(0, min(255, base[1] + int(bright * 0.9)))
            b2 = max(0, min(255, base[2] + int(bright * 0.8)))
            alpha = rng.randint(35, 90)
            gd.line([(0, y), (fw_px, y)], fill=(r2, g2, b2, alpha), width=1)
        # Occasional brighter reflection streak
        for _ in range(rng.randint(2, 5)):
            sy = rng.randint(0, fh_px)
            for i in range(3):
                a = max(0, 70 - i * 24)
                gd.line([(0, sy + i), (fw_px, sy + i)], fill=(255, 255, 255, a))

    elif grain_type == "metal":
        # Gold/silver — subtle diagonal sheen with horizontal micro-lines
        for y in range(0, fh_px, 3):
            bright = rng.randint(-12, 12)
            r2 = max(0, min(255, base[0] + bright))
            g2 = max(0, min(255, base[1] + int(bright * 0.85)))
            b2 = max(0, min(255, base[2] + int(bright * 0.5)))
            gd.line([(0, y), (fw_px, y)], fill=(r2, g2, b2, 50))

    else:
        # flat: subtle brightness flicker only
        for y in range(0, fh_px, 4):
            bright = rng.randint(-8, 8)
            r2 = max(0, min(255, base[0] + bright))
            g2 = max(0, min(255, base[1] + bright))
            b2 = max(0, min(255, base[2] + bright))
            gd.line([(0, y), (fw_px, y)], fill=(r2, g2, b2, 40))

    grain_layer = grain_layer.filter(ImageFilter.GaussianBlur(radius=0.6))
    canvas.paste(grain_layer, (fx0, fy0), grain_layer)

    # ── 3-D Bevel molding — wide face with realistic lighting ratios ──
    draw = ImageDraw.Draw(canvas)
    for b in range(BEVEL):
        t = (1.0 - b / BEVEL) ** 1.4   # power curve: bright near edge, rapid falloff
        hi = tuple(int(base[i] + (pal["hi"][i] - base[i]) * t) for i in range(3)) + (255,)
        lo = tuple(int(base[i] + (pal["lo"][i] - base[i]) * t) for i in range(3)) + (255,)
        draw.line([(fx0+b, fy0+b), (fx1-b, fy0+b)], fill=hi, width=1)   # top highlight
        draw.line([(fx0+b, fy0+b), (fx0+b, fy1-b)], fill=hi, width=1)   # left highlight
        draw.line([(fx0+b, fy1-b), (fx1-b, fy1-b)], fill=lo, width=1)   # bottom shadow
        draw.line([(fx1-b, fy0+b), (fx1-b, fy1-b)], fill=lo, width=1)   # right shadow

    # ── Specular highlight: bright glancing reflection on top-left molding face ──
    spec_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    sp = ImageDraw.Draw(spec_layer)
    for i in range(8):
        a = max(0, 55 - i * 7)
        sp.line([(fx0 + BEVEL + i, fy0 + 2), (fx0 + BEVEL + i, fy1 - 2)],
                fill=(255, 255, 255, a))
        sp.line([(fx0 + 2, fy0 + BEVEL + i), (fx1 - 2, fy0 + BEVEL + i)],
                fill=(255, 255, 255, a))
    spec_layer = spec_layer.filter(ImageFilter.GaussianBlur(radius=2))
    canvas = Image.alpha_composite(canvas, spec_layer)
    draw = ImageDraw.Draw(canvas)

    # ── Ambient light tint: blend wall color temperature into frame (8%) ──
    ar, ag, ab = ambient_rgb
    for i in range(3):
        tint_c = (int(base[i] * 0.92 + (ar, ag, ab)[i] * 0.08),) * 1
    # Apply tint as a semi-transparent overlay on the frame rect only
    tint_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    tl = ImageDraw.Draw(tint_layer)
    tl.rectangle([fx0, fy0, fx1, fy1],
                 fill=(int(ar * 0.08 + base[0] * 0.92),
                       int(ag * 0.08 + base[1] * 0.92),
                       int(ab * 0.08 + base[2] * 0.92), 25))
    canvas = Image.alpha_composite(canvas, tint_layer)
    draw = ImageDraw.Draw(canvas)

    # ── White mat with deep inner shadow recess ──
    mx0, my0 = fx0 + FRAME_W, fy0 + FRAME_W
    mx1, my1 = fx1 - FRAME_W, fy1 - FRAME_W
    draw.rectangle([mx0, my0, mx1, my1], fill=(252, 249, 244, 255))
    for s in range(8):
        v = 200 - s * 12
        draw.rectangle([mx0+s, my0+s, mx1-s, my1-s], outline=(v, v-1, v-3, 255))

    # ── Inner frame edge: dark lip where frame meets mat ──
    draw.rectangle([mx0, my0, mx1, my1], outline=(80, 72, 60, 200), width=1)

    # ── Paste art with glass-glare overlay ──
    ax0, ay0 = mx0 + MAT_W, my0 + MAT_W
    art_rgba = art.convert("RGBA")
    glare = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glare)
    # Diagonal band of soft reflected light (upper-left corner)
    for y in range(ah):
        p = y / ah
        if p < 0.22:
            a = int((0.22 - p) / 0.22 * 16)
            gd.line([(0, y), (aw, y)], fill=(255, 255, 255, a))
    glare = glare.filter(ImageFilter.GaussianBlur(radius=5))
    art_rgba = Image.alpha_composite(art_rgba, glare)
    canvas.paste(art_rgba, (ax0, ay0), art_rgba)

    return canvas, (ax0, ay0, ax0 + aw, ay0 + ah)


def _fetch_image_bytes(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
    output_format: str = "jpeg",
) -> bytes | None:
    """Call OpenAI image generation and return raw image bytes, or None on failure."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        import base64 as _b64
        body = json.dumps({
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": 1,
            "output_format": output_format,
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
        item = result["data"][0]
        if item.get("b64_json"):
            return _b64.b64decode(item["b64_json"])
        if item.get("url"):
            with urllib.request.urlopen(item["url"], timeout=30) as r:
                return r.read()
    except Exception:
        pass
    return None


_ROOM_BG_PROMPTS: dict[str, str] = {
    "kitchen_dining": (
        "Interior design photography of a bright Mediterranean kitchen and dining area. "
        "Camera pulled back to show the full back wall — furniture sits in the lower third only. "
        "Wooden dining table with rattan chairs, bowl of lemons, terracotta tile floor, cream walls. "
        "COMPOSITION: the back wall occupies the top 60% of the image as a large empty surface. "
        "The wall is COMPLETELY BLANK — no art, no frames, no shelves, no hooks, nothing. "
        "Furniture and floor occupy only the bottom 40%. Pottery Barn catalog. Photorealistic."
    ),
    "living_room": (
        "Interior design photography of an elevated transitional living room, warm and polished. "
        "Cream linen sofa with warm gold and sage green throw pillows, marble or stone coffee table, "
        "ceramic table lamp, olive tree in a terracotta pot, Persian-style area rug, warm hardwood floor. "
        "White walls with subtle wainscoting panel molding detail. Large window with natural light on the left. "
        "Camera pulled back so sofa and furniture sit in the lower 45% of the frame. "
        "COMPOSITION: the wall behind the sofa fills the top 50% of the image as a large empty surface. "
        "The wall is COMPLETELY BLANK — no art, no frames, no pictures, nothing on the wall at all. "
        "Furniture occupies only the lower portion. Pottery Barn / RH catalog quality. Photorealistic."
    ),
    "entryway": (
        "Interior design photography of a bright home entryway. "
        "Camera straight-on so the back wall dominates the upper 65% of the frame. "
        "Small white console table at the very bottom of the image, glass vase with white flowers, "
        "jute runner on hardwood floor, white wainscoting on lower walls. "
        "COMPOSITION: the wall above the console table fills the top 60% as a large empty surface. "
        "The wall is COMPLETELY BLANK — no art, no frames, no pictures, nothing on the wall. "
        "Console table sits along the bottom edge only. Coastal Living style. Photorealistic."
    ),
    "bedroom": (
        "Interior design photography of a serene minimalist boho bedroom, bright and airy. "
        "Low natural wood platform bed with white linen star-print bedding, slightly rumpled. "
        "Exposed dark wooden ceiling beam, sheer white floor-length curtains letting in soft morning light. "
        "Small wooden hairpin-leg side table with a round white ceramic vase holding dried pampas grass. "
        "White textured area rug on light wood floor. Pure white walls. "
        "Camera pulled back — bed and furniture sit in the lower 50% of the frame only. "
        "COMPOSITION: the wall above the headboard fills the top 45% as a large, completely empty surface. "
        "The wall is COMPLETELY BLANK — no art, no frames, no pictures, nothing on the wall. "
        "Bright, clean, neutral — Pottery Barn / Restoration Hardware catalog quality. Photorealistic."
    ),
    "pub": (
        "Interior photography of a warm upscale English pub or whiskey bar. "
        "Rich dark walnut wood paneling covering the walls — vertical raised panels with chair rail molding. "
        "Polished dark wood bar top with warm amber light reflected across its surface. "
        "Brass picture-rail picture light mounted above where the art will hang, casting a focused warm downward beam. "
        "Rows of amber whiskey bottles and glassware on open wood shelves slightly out of focus in background. "
        "Round leather-topped dark metal bar stools along the bar below the art. "
        "Warm amber incandescent pendant lighting overhead, supplemented by the picture light. "
        "Patrons visible in extreme soft-focus background — warm and lively atmosphere. "
        "Camera positioned straight on — the dark walnut paneled wall fills the upper 55% of the frame as a large empty surface. "
        "COMPOSITION: the wall above the bar is COMPLETELY BLANK — no art, no frames, nothing on the wall. "
        "Bar and stools occupy only the lower 45%. Warm amber and honey wood tones throughout. Photorealistic."
    ),
}

# Shadow bleed padding used inside _render_framed_art_rgba
_FRAME_RGBA_PAD = 52


def _scan_clear_wall_zone(room_img: Any) -> tuple[float, float]:
    """
    Detect where the clear wall ends and furniture begins by scanning brightness + variance.
    Returns (wall_top_frac, furniture_top_frac) as fractions of image height.
    """
    from PIL import ImageFilter
    w, h = room_img.size
    blurred = room_img.filter(ImageFilter.GaussianBlur(radius=5))

    xs = [int(w * f) for f in (0.2, 0.35, 0.5, 0.65, 0.8)]
    row_bright: list[float] = []
    row_var:    list[float] = []
    for y in range(h):
        vals = [(blurred.getpixel((x, y))[0] + blurred.getpixel((x, y))[1] + blurred.getpixel((x, y))[2]) / 3
                for x in xs]
        avg = sum(vals) / len(vals)
        var = sum((v - avg) ** 2 for v in vals) / len(vals)
        row_bright.append(avg)
        row_var.append(var)

    # Reference: top 15% (ceiling / plain wall area)
    ref_h = max(1, int(h * 0.15))
    ref_b = sum(row_bright[:ref_h]) / ref_h
    ref_v = max(1.0, sum(row_var[:ref_h]) / ref_h)

    bright_thresh = ref_b * 0.83   # 17% darker = likely furniture/objects
    var_thresh    = ref_v * 6.0    # 6× more varied = furniture detail

    furniture_frac = 0.68  # fallback
    win = 10
    for y in range(int(h * 0.15), int(h * 0.90) - win):
        ahead_b = row_bright[y: y + win]
        ahead_v = row_var[y: y + win]
        if sum(1 for b in ahead_b if b < bright_thresh) >= 6:
            furniture_frac = y / h
            break
        if sum(1 for v in ahead_v if v > var_thresh) >= 5:
            furniture_frac = y / h
            break

    return 0.04, furniture_frac


def _create_room_composite(data: dict, store: DataStore) -> str:
    """Generate empty room backgrounds via AI, then composite the real art file into each."""
    try:
        from PIL import Image, ImageEnhance
        import io
    except ImportError:
        return json.dumps({"error": "Pillow required"})

    product_id  = data["product_id"]
    frame_style = data.get("frame_style", "natural_wood")
    room_styles = data.get("room_styles", ["kitchen_dining", "living_room", "entryway"])

    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})
    src = product.get("file_path")
    if not src or not os.path.exists(src):
        return json.dumps({"error": "No image file. Call generate_digital_art first."})

    art_img = Image.open(src).convert("RGB")
    ROOM_PX = 1024
    PAD     = _FRAME_RGBA_PAD          # shadow bleed around the framed RGBA image
    FRAME_MAT_TOTAL = 2 * (48 + 16)   # 2×(FRAME_W + MAT_W) = 128px added to art dims

    # Per-room max frame width as fraction of room image — entryway kept smaller
    _ROOM_MAX_FRAC = {
        "kitchen_dining": 0.50,
        "living_room":    0.50,
        "entryway":       0.36,
        "bedroom":        0.48,
        "pub":            0.52,
    }

    saved: list[dict] = []
    for room_key in room_styles:
        prompt    = _ROOM_BG_PROMPTS.get(room_key, _ROOM_BG_PROMPTS["living_room"])
        img_bytes = _fetch_image_bytes(prompt, size="1024x1024")
        if not img_bytes:
            saved.append({"room": room_key, "error": "image generation failed"})
            continue

        room_bg = Image.open(io.BytesIO(img_bytes)).convert("RGBA").resize(
            (ROOM_PX, ROOM_PX), Image.LANCZOS
        )
        room_rgb = room_bg.convert("RGB")

        # Detect clear wall zone above furniture
        wall_top_f, furn_top_f = _scan_clear_wall_zone(room_rgb)
        wall_top_px = int(ROOM_PX * wall_top_f)
        furn_top_px = int(ROOM_PX * furn_top_f)

        # Sample ambient wall color from the center of the clear wall zone
        sample_y = (wall_top_px + furn_top_px) // 2
        sample_y = min(sample_y, ROOM_PX - 1)
        wall_samples = [room_rgb.getpixel((int(ROOM_PX * x), sample_y))
                        for x in (0.3, 0.4, 0.5, 0.6, 0.7)]
        ambient = tuple(sum(s[c] for s in wall_samples) // len(wall_samples) for c in range(3))

        # Available height for the VISIBLE frame; leave 5% gap above furniture
        avail_h = (furn_top_px - int(ROOM_PX * 0.05)) - (wall_top_px + int(ROOM_PX * 0.04))
        avail_h = max(120, avail_h)

        max_frac = _ROOM_MAX_FRAC.get(room_key, 0.50)
        target_vis_fh = int(avail_h * 0.90)
        art_long = min(int(ROOM_PX * max_frac), max(80, target_vis_fh - FRAME_MAT_TOTAL))

        framed, _ = _render_framed_art_rgba(art_img, frame_style, art_long, ambient_rgb=ambient)
        fw, fh    = framed.size

        # Visible frame bounds within the RGBA image: [PAD .. fh-PAD]
        vis_fh = fh - 2 * PAD   # actual visible frame height (no shadow bleed)
        vis_fw = fw - 2 * PAD

        # Center visible frame vertically in the wall zone
        wall_center_px = (wall_top_px + furn_top_px) / 2
        vis_top_y  = int(wall_center_px - vis_fh / 2)
        vis_top_y  = max(wall_top_px + 10, vis_top_y)
        # Ensure visible frame bottom stays above furniture with margin
        max_vis_bottom = furn_top_px - int(ROOM_PX * 0.04)
        if vis_top_y + vis_fh > max_vis_bottom:
            vis_top_y = max(wall_top_px + 10, max_vis_bottom - vis_fh)

        # Convert visible top to paste position (accounting for PAD bleed)
        py = vis_top_y - PAD
        px = (ROOM_PX - fw) // 2

        room_bg.paste(framed, (px, py), framed)
        final = ImageEnhance.Contrast(room_bg.convert("RGB")).enhance(1.04)

        out = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_room_{room_key}_{frame_style}.jpg")
        final.save(out, "JPEG", quality=93, optimize=True)
        saved.append({"room": room_key, "path": out})

    paths = [s["path"] for s in saved if "path" in s]
    product["room_composite_paths"] = paths
    product["updated_at"]           = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success":   True,
        "product_id": product_id,
        "composites": saved,
        "note": "Room settings use the REAL art file composited in — identical to the download.",
    }, indent=2)


def _create_size_comparison(data: dict, store: DataStore) -> str:
    """Composite the real art at 3 print sizes on a clean wall for a size guide photo."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    except ImportError:
        return json.dumps({"error": "Pillow required"})

    product_id  = data["product_id"]
    frame_style = data.get("frame_style", "natural_wood")
    wall_key    = data.get("wall_color", "warm_gray")

    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})
    src = product.get("file_path")
    if not src or not os.path.exists(src):
        return json.dumps({"error": "No image file. Call generate_digital_art first."})

    art_img  = Image.open(src).convert("RGB")
    wall_rgb = _WALL_PALETTES.get(wall_key, _WALL_PALETTES["warm_gray"])

    CW, CH = 1500, 1020

    # Wall gradient
    canvas = Image.new("RGB", (CW, CH), wall_rgb)
    draw   = ImageDraw.Draw(canvas)
    for y in range(CH):
        fade = int(y / CH * 32)
        c    = tuple(max(0, v - fade) for v in wall_rgb)
        draw.line([(0, y), (CW, y)], fill=c)

    # Baseboard strip at bottom
    board_y = CH - 56
    for y in range(board_y, CH):
        t = (y - board_y) / (CH - board_y)
        c = tuple(max(0, int(v * (1 - t * 0.18))) for v in wall_rgb)
        draw.line([(0, y), (CW, y)], fill=c)
    draw.line([(0, board_y), (CW, board_y)], fill=tuple(max(0, v - 38) for v in wall_rgb), width=2)

    # Three frame sizes: long side as fraction of canvas width
    SIZE_SPECS = [
        ("8×10\"",  int(CW * 0.165)),
        ("16×20\"", int(CW * 0.295)),
        ("24×36\"", int(CW * 0.43)),
    ]

    frames = [(label, *_render_framed_art_rgba(art_img, frame_style, ls)) for label, ls in SIZE_SPECS]

    total_fw = sum(frm.size[0] for _, frm, _ in frames)
    GAP      = (CW - total_fw) // (len(frames) + 1)
    BOTTOM_Y = int(CH * 0.82)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except Exception:
        font = ImageFont.load_default()

    x = GAP
    canvas_rgba = canvas.convert("RGBA")
    label_positions: list[tuple] = []

    for label, framed, _ in frames:
        fw, fh = framed.size
        py     = max(10, BOTTOM_Y - fh)
        canvas_rgba.paste(framed, (x, py), framed)
        label_positions.append((label, x + fw // 2, BOTTOM_Y + 16))
        x += fw + GAP

    canvas = canvas_rgba.convert("RGB")
    draw   = ImageDraw.Draw(canvas)
    for label, lx, ly in label_positions:
        tw = draw.textlength(label, font=font) if hasattr(draw, "textlength") else 80
        draw.text((lx - tw // 2 + 1, ly + 1), label, font=font, fill=(180, 174, 165))
        draw.text((lx - tw // 2,     ly),     label, font=font, fill=(75,  68,  58))

    canvas = ImageEnhance.Contrast(canvas).enhance(1.05)

    out = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_size_comparison_{frame_style}.jpg")
    canvas.save(out, "JPEG", quality=93, optimize=True)

    product["size_comparison_path"] = out
    product["updated_at"]           = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success":    True,
        "product_id": product_id,
        "path":       out,
        "note":       "Size comparison uses the REAL art composited at 3 print sizes.",
    }, indent=2)


def generate_wall_art_master(product_id: str, prompt: str, engine: str | None = None,
                              hand_painted_medium: str | None = None) -> str:
    """Generate + upscale a print-ready master JPG for product_id, saved to
    PRODUCT_FILES_DIR/{product_id}.jpg -- the exact path build_wallart_product.py
    already checks for (see its own docstring). Adapted from
    _generate_digital_art() below (2026-07-22, Create-screen "+ new one" new-art
    flow) but decoupled from that function's DataStore/product-record
    bookkeeping: this is called with a product_id Scott typed himself (no
    existing "product" record to look up or mint), and routes through
    tools/image_gen.py's generate_image() (engine-validated against the
    approved list, same as every other AI image call in this app) instead of
    _generate_digital_art()'s raw-urllib gpt-image-1-only call.

    Raises ImageGenError (propagated from image_gen.generate_image) or
    RuntimeError (from _upscale_for_print if Pillow is missing) on failure --
    the caller (build_wallart_product.py) is expected to let this exit
    non-zero rather than silently continue with no source art.

    (2026-07-30) Routed through goal_loop.run_until_goal() -- generate, then
    one vision QA pass (image_gen.verify_original_art()) checking for garbled
    baked-in text, a broken multi-panel collage, or wrong subject matter, with
    up to one retry using the specific failures as corrective feedback. This
    was previously a single-shot generate-and-hope call with zero automated
    quality check, unlike the listing-photo pipeline's already-proven
    verify+retry pattern this reuses. If it never passes within the attempt
    budget, the last attempt is still used (never raises for a QA miss --
    a real generation error still raises) but a loud warning is printed so a
    human reviewing the build log knows to double-check it; this matches the
    existing needs_visual_qc:true flag _produce_build_product() already
    surfaces to Scott for any wall-art build that generated new AI art.

    (2026-07-31) Skips the QA pass entirely (single generate call, no retry)
    when GEMINI_API_KEY isn't configured, rather than entering the goal loop --
    verify_original_art() needs its own Gemini key independent of whichever
    engine generated the image, and without this guard a missing key would
    masquerade as an ordinary QA failure: retried uselessly with a "fix this"
    correction the model can't act on, then still shipped unverified anyway.
    See image_gen.gemini_key_available()'s docstring for the full mechanism."""
    from tools.image_gen import generate_image, PORTRAIT, gemini_key_available
    from tools import image_gen as _image_gen
    from tools.goal_loop import run_until_goal
    _ensure_dirs()
    final_prompt = enrich_prompt_with_medium(prompt, hand_painted_medium)
    raw_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_raw.png")

    def _generate(correction: str) -> str:
        generate_image(final_prompt + correction, raw_path, size=PORTRAIT, quality="high",
                        output_format="png", engine=engine)
        return raw_path

    def _verify(candidate_path: str) -> dict:
        return _image_gen.verify_original_art(candidate_path, final_prompt)

    if gemini_key_available():
        result = run_until_goal(_generate, _verify, max_attempts=2)
        if not result.passed:
            print(f"[generate_wall_art_master] ⚠ {product_id}: automated art QA did not "
                  f"pass after {result.attempts} attempt(s): {result.issues}. Using the last "
                  f"generated image anyway -- review it before publishing.", flush=True)
    else:
        print(f"[generate_wall_art_master] ⚠ {product_id}: GEMINI_API_KEY not set -- "
              f"skipping automated art QA (no verification pass run). Set it to enable "
              f"garbled-text/wrong-subject checks. Review this image before publishing.",
              flush=True)
        _generate("")

    file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.jpg")
    _upscale_for_print(raw_path, file_path, target_px=3000)  # Gate 1: >=3000px short edge
    return file_path


def _generate_digital_art(data: dict, store: DataStore) -> str:
    _ensure_dirs()
    product_id = data["product_id"]
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return _generate_placeholder_art(data, product, store)

    try:
        import base64
        # Map size: portrait default for wall art, cap invalid legacy sizes
        raw_size = data.get("image_size", "1024x1536")
        valid_sizes = {"1024x1024", "1536x1024", "1024x1536"}
        size = raw_size if raw_size in valid_sizes else "1024x1536"

        # Apply hand-painted medium enrichment if set on product or in call data
        base_prompt = data["dalle_prompt"]
        medium = data.get("hand_painted_medium") or product.get("hand_painted_medium")
        final_prompt = enrich_prompt_with_medium(base_prompt, medium)

        request_body = json.dumps({
            "model": "gpt-image-1",
            "prompt": final_prompt,
            "size": size,
            "quality": "high",
            "n": 1,
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=request_body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())

        img_data = result["data"][0].get("b64_json") or result["data"][0].get("url")
        raw_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_raw.png")

        if result["data"][0].get("b64_json"):
            with open(raw_path, "wb") as f:
                f.write(base64.b64decode(img_data))
        else:
            with urllib.request.urlopen(img_data, timeout=60) as _r:
                with open(raw_path, "wb") as _f:
                    _f.write(_r.read())

        # Upscale + sharpen for print quality; output is JPEG (smaller, still print-quality)
        file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.jpg")
        _upscale_for_print(raw_path, file_path, target_px=3000)

        file_size_kb = os.path.getsize(file_path) // 1024

        import hashlib as _hashlib
        with open(file_path, "rb") as _hf:
            product["file_hash"] = _hashlib.sha256(_hf.read()).hexdigest()
        product["is_placeholder"] = False

        product["file_path"] = file_path
        product["file_format"] = "JPEG"
        product["file_size_kb"] = file_size_kb
        product["status"] = "qc_pending"
        product["updated_at"] = str(date.today())
        if medium:
            product["hand_painted_medium"] = medium
        _save_product(product, store)

        result_payload: dict = {
            "success": True,
            "product_id": product_id,
            "file_path": file_path,
            "file_size_kb": file_size_kb,
            "dimensions": "3000px min-side JPEG 95% @ 300 DPI (print-ready)",
            "status": "qc_pending",
            "next_step": "Send to Quality Check Agent for review.",
        }
        if medium:
            style_info = HAND_PAINTED_STYLES[medium]
            result_payload["hand_painted_medium"] = medium
            result_payload["medium_label"] = style_info["label"]
            result_payload["title_suffix"] = style_info["title_suffix"]
            result_payload["extra_tags"] = style_info["extra_tags"]
        return json.dumps(result_payload, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return json.dumps({"error": f"Image API error {e.code}: {error_body}"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _create_digital_planner(data: dict, store: DataStore) -> str:
    _ensure_dirs()
    product_id = data["product_id"]
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})

    def _blend(rgb, factor):
        return tuple(c + (1.0 - c) * factor for c in rgb)

    # ── page setup ────────────────────────────────────────────────────────────
    try:
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.pagesizes import A4, LETTER
        from reportlab.lib.colors import Color
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
    except ImportError:
        brief_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_planner_spec.txt")
        with open(brief_path, "w") as f:
            f.write(f"PLANNER SPEC: {data['planner_title']}\nInstall: pip install reportlab\n")
        product["file_path"] = brief_path
        product["status"] = "concept"
        product["updated_at"] = str(date.today())
        _save_product(product, store)
        return json.dumps({"warning": "reportlab not installed.", "action_needed": "pip install reportlab"}, indent=2)

    import calendar as cal_mod
    from datetime import date as dt_date, timedelta, datetime as _dt

    fmt = data.get("planner_format", "letter")
    PW, PH = LETTER if fmt == "letter" else A4

    ML = MR = 36.0
    MT = MB = 32.0
    CW = PW - ML - MR
    CH = PH - MT - MB

    # nav tab dimensions (right-side stacked tabs)
    TAB_W  = 28.0
    TAB_H  = 18.0
    TAB_GAP = 1.5
    TAB_X   = PW - TAB_W - 2.0

    # ── Resolve style → tier → explicit params (each layer overrides the last) ─
    _style_key  = data.get("planner_style", "")
    _style_conf = PLANNER_STYLES.get(_style_key, {})
    _default_tier = 3 if data.get("interactive", True) else 1
    _tier_num   = int(data.get("planner_tier", _style_conf.get("tier", _default_tier)))
    _tier_conf  = PLANNER_TIERS.get(_tier_num, {})
    _design     = _tier_num if _tier_num in (1, 2, 3) else 3
    _variant    = _style_conf.get("design_variant", "standard")
    _extras     = _style_conf.get("extras", [])
    if _design == 3 and "sticker_pack" not in _extras:
        _extras = list(_extras) + ["sticker_pack"]
    _is_fun     = _style_conf.get("fun", False)

    # Color scheme: style → explicit param → tier default → "sage_cream"
    _style_scheme   = _style_conf.get("color_scheme", "sage_cream")
    scheme_key      = data.get("color_scheme", _style_scheme)
    if scheme_key not in COLOR_SCHEMES:
        scheme_key = "sage_cream"
    cs    = COLOR_SCHEMES[scheme_key]
    T     = cs["theme"]
    A     = cs["accent"]
    BG    = cs["bg"]
    DARK  = cs["dark"]
    MID   = cs["mid"]
    LIGHT = cs["light"]
    WHITE = (1.0, 1.0, 1.0)
    TL    = _blend(T, 0.82)
    TM    = _blend(T, 0.50)
    AL    = _blend(A, 0.75)
    BGL   = _blend(BG, -0.03) if BG[0] > 0.5 else _blend(BG, 0.15)

    is_interactive = data.get("interactive",
                               _tier_conf.get("interactive", True))
    planner_year   = data.get("year", dt_date.today().year)
    undated        = (planner_year == 0)
    if undated:
        planner_year = dt_date.today().year

    _style_sects    = _style_conf.get("sections",
                       _tier_conf.get("sections",
                       ["monthly", "weekly", "habit_tracker", "goals", "notes"]))
    sections        = data.get("include_sections", _style_sects)
    weekly_layout   = data.get("weekly_layout", "horizontal")
    cal_integration = data.get("calendar_integration",
                                _style_conf.get("calendar_integration",
                                _tier_conf.get("calendar_integration", "none")))
    title    = data["planner_title"]
    subtitle = data.get("subtitle",
                         _style_conf.get("subtitle",
                         _tier_conf.get("subtitle_default", "")))

    # Tab color override (5 options: scheme default, white, light_pink, brown, olive, black)
    _TAB_COLOR_MAP = {
        "white":      (0.96, 0.96, 0.96),
        "light_pink": (0.949, 0.769, 0.808),
        "brown":      (0.545, 0.416, 0.322),
        "olive":      (0.431, 0.482, 0.290),
        "black":      (0.110, 0.110, 0.118),
    }
    _tab_color_key = data.get("tab_color", "scheme")
    _TAB_OVERRIDE  = _TAB_COLOR_MAP.get(_tab_color_key)  # None means use scheme T

    MONTHS     = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
    DAYS_SHORT = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
    DAYS_LONG  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.pdf")
    c = pdf_canvas.Canvas(file_path, pagesize=(PW, PH))
    c.setTitle(title)
    c.setAuthor("OnBrandCraftz")
    c.setSubject(f"Digital Planner — {cs['label']} color scheme")
    c.setCreator("OnBrandCraftz Planner Design Agent")

    # ── Register custom fonts (Poppins) ───────────────────────────────────────
    _FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
    _FONT_MAP = {}
    try:
        from reportlab.pdfbase import pdfmetrics as _pm
        from reportlab.pdfbase.ttfonts import TTFont as _TTF
        _font_files = {
            "Poppins":          "Poppins-Regular.ttf",
            "Poppins-Bold":     "Poppins-Bold.ttf",
            "Poppins-SemiBold": "Poppins-SemiBold.ttf",
            "Poppins-Italic":   "Poppins-Italic.ttf",
        }
        for _fn, _ff in _font_files.items():
            _fp = os.path.join(_FONTS_DIR, _ff)
            if os.path.exists(_fp):
                _pm.registerFont(_TTF(_fn, _fp))
                _FONT_MAP[_fn] = _fn
        # Register family so bold/italic substitution works
        if "Poppins" in _FONT_MAP and "Poppins-Bold" in _FONT_MAP:
            from reportlab.pdfbase.pdfmetrics import registerFontFamily
            registerFontFamily("Poppins",
                normal="Poppins", bold="Poppins-Bold",
                italic="Poppins-Italic" if "Poppins-Italic" in _FONT_MAP else "Poppins",
                boldItalic="Poppins-Bold")
    except Exception:
        pass

    # Font name resolver: prefer Poppins, fall back to Helvetica variants
    def _fn(variant="regular"):
        v = variant.lower()
        if v in ("bold", "b"):
            return _FONT_MAP.get("Poppins-Bold", "Helvetica-Bold")
        if v in ("semibold", "sb"):
            return _FONT_MAP.get("Poppins-SemiBold", _FONT_MAP.get("Poppins-Bold", "Helvetica-Bold"))
        if v in ("italic", "i"):
            return _FONT_MAP.get("Poppins-Italic", "Helvetica-Oblique")
        return _FONT_MAP.get("Poppins", "Helvetica")

    # ── Color helper for acroForm (needs reportlab Color objects) ─────────────
    def _col(rgb): return Color(rgb[0], rgb[1], rgb[2])

    # ── Drawing helpers ───────────────────────────────────────────────────────
    def fill(rgb):   c.setFillColorRGB(*rgb)
    def stroke(rgb): c.setStrokeColorRGB(*rgb)
    def lw(w):       c.setLineWidth(w)
    def font(name, size):
        # Allow shorthand aliases so all existing call-sites work unchanged
        _alias = {
            "Helvetica":         _fn("regular"),
            "Helvetica-Bold":    _fn("bold"),
            "Helvetica-Oblique": _fn("italic"),
            "Helvetica-BoldOblique": _fn("bold"),
        }
        c.setFont(_alias.get(name, name), size)

    def rect(x, y, w, h, f=None, s=None, lwidth=0.5, radius=0):
        if lwidth: lw(lwidth)
        if f: fill(f)
        if s: stroke(s)
        if radius:
            c.roundRect(x, y, w, h, radius, fill=1 if f else 0, stroke=1 if s else 0)
        else:
            c.rect(x, y, w, h, fill=1 if f else 0, stroke=1 if s else 0)

    def hline(x1, x2, y, color=None, width=0.5):
        lw(width); stroke(color or LIGHT)
        c.line(x1, y, x2, y)

    def vline(x, y1, y2, color=None, width=0.5):
        lw(width); stroke(color or LIGHT)
        c.line(x, y1, x, y2)

    def circle(cx, cy, r, f=None, s=None, lwidth=0.5):
        if lwidth: lw(lwidth)
        if f: fill(f)
        if s: stroke(s)
        c.circle(cx, cy, r, fill=1 if f else 0, stroke=1 if s else 0)

    def page_bg():
        rect(0, 0, PW, PH, f=BG)
        if _design == 1:
            rect(0, 0, 3, PH, f=_blend(T, 0.55))
        elif _design == 3:
            # Tier 3: subtle full-page dot grid
            _dp = 20; _dr = 0.42
            _gx = ML + _dp
            while _gx <= PW - MR - TAB_W - 4:
                _gy = MB + _dp
                while _gy <= PH - MT - _dp:
                    circle(_gx, _gy, _dr, f=LIGHT)
                    _gy += _dp
                _gx += _dp
            rect(0, 0, 3, PH, f=A)

        # ── Variant-specific page decorations ────────────────────────────────
        if _variant == "botanical":
            # Tiny leaf motifs in two corners
            for _lx, _ly, _flip in [(ML+6, PH-MT-10, 1), (ML+6, MB+10, -1)]:
                for _i in range(4):
                    _lbx = _lx + _i * 6; _lby = _ly
                    c.saveState()
                    c.translate(_lbx, _lby)
                    c.scale(1, _flip)
                    c.setFillColorRGB(*_blend(T, 0.55))
                    c.setLineWidth(0.3)
                    c.setStrokeColorRGB(*_blend(T, 0.4))
                    p = c.beginPath()
                    p.moveTo(0, 0); p.curveTo(4, 5, 6, 8, 3, 10)
                    p.curveTo(1, 8, -2, 5, 0, 0)
                    c.drawPath(p, fill=1, stroke=0)
                    c.restoreState()
        elif _variant in ("fun", "rainbow_fun"):
            # Small decorative circles scattered in margins
            import random as _r; _rng = _r.Random(42)
            for _ in range(6):
                _rx = ML/2 - 4 + _rng.random() * 20
                _ry = MB + _rng.random() * (PH - MT - MB)
                _rr = 2 + _rng.random() * 4
                _rc = [T, A, AL, TM][int(_rng.random()*4)]
                circle(_rx, _ry, _rr, f=_blend(_rc, 0.6))
        elif _variant == "spiritual":
            # Small star motifs in right margin
            _star_x = PW - MR/2 - 2
            for _si in range(5):
                _star_y = MB + 60 + _si * ((PH - MT - MB - 120) / 4)
                font("Helvetica-Bold", 7); fill(_blend(A, 0.55))
                c.drawCentredString(_star_x, _star_y, "*")
        elif _variant in ("premium", "ultra_premium"):
            # Thin double-rule inside top margin for refined look
            hline(ML, PW - MR - TAB_W - 4, PH - MT + 10, _blend(A, 0.35), 0.3)
            hline(ML, PW - MR - TAB_W - 4, PH - MT + 13, _blend(A, 0.20), 0.2)

    def page_footer(label=""):
        hline(ML, PW - MR - TAB_W - 4, MB - 6, LIGHT, 0.4)

        # Back-to-index pill button
        _bw = 50; _bh = 14; _bx = ML; _by = MB - 22
        _btn_fill = _blend(T, 0.90) if _design == 1 else _blend(T, 0.85)
        rect(_bx, _by, _bw, _bh, f=_btn_fill, radius=3)
        font("Helvetica-Bold", 6.5); fill(T)
        c.drawCentredString(_bx + _bw / 2, _by + 4, "‹ INDEX")
        c.linkAbsolute("Back to Index", "index",
                       (_bx, _by, _bx + _bw, _by + _bh))

        # HOME button (links to dashboard overview page)
        _hw = 44; _hx = _bx + _bw + 5
        rect(_hx, _by, _hw, _bh, f=_blend(A, 0.75), radius=3)
        font("Helvetica-Bold", 6.5); fill(DARK)
        c.drawCentredString(_hx + _hw / 2, _by + 4, "🏠 HOME")
        c.linkAbsolute("Back to Home", "dashboard",
                       (_hx, _by, _hx + _hw, _by + _bh))

        # Persistent STICKERS panel button — always visible on every page (Tier 3)
        if _design == 3 and "sticker_pack" in _extras:
            _sw = 80; _sx = _bx + _bw + 6; _sy = _by
            # Gradient-like effect: two layered rects
            rect(_sx, _sy, _sw, _bh, f=_blend(A, 0.30), radius=5)
            rect(_sx + 1, _sy + 1, _sw - 2, _bh - 2, f=T, radius=4)
            font("Helvetica-Bold", 6.5); fill(WHITE)
            c.drawCentredString(_sx + _sw / 2, _sy + 3.5, "✨  STICKERS")
            _sticker_js = (
                # Category menu
                'var cats=['
                '"  \U0001F534  PRIORITY & TASKS",'
                '"  \U0001F4C5  EVENTS & DATES",'
                '"  \U0001F497  WELLNESS & MOOD",'
                '"  \U0001F393  SCHOOL & STUDY",'
                '"  \U0001F4AA  MOTIVATION"'
                '];'
                'var catIdx=app.popupMenu(cats);'
                'if(catIdx<0)return;'
                'var lists=['
                # 0 PRIORITY
                '["! IMPORTANT","!! URGENT","⏰ DEADLINE","\U0001F4CB MEETING",'
                '"✓ TO-DO","\U0001F6CD ERRANDS","\U0001F525 BUSY DAY",'
                '"\U0001F4DE CALL","✉ EMAIL","\U0001F4B3 PAY BILL",'
                '"\U0001F6D2 TO BUY","⏳ DUE TODAY","⭐ PRIORITY",'
                '"\U0001F4CC PIN THIS","\U0001F512 BLOCKED","❗ REMINDER"],'
                # 1 EVENTS
                '["\U0001F382 BIRTHDAY!","\U0001F4C6 APPT","✈ VACAY!",'
                '"\U0001F48C ANNIVERSARY","\U0001F4f8 MEMORIES","\U0001F381 GIFT DUE",'
                '"\U0001F91D EVENT","\U0001F3e0 FAMILY TIME","\U0001F506 HOLIDAY",'
                '"\U0001F3c6 GOAL MET!","✅ DONE!","⭐ WIN!",'
                '"\U0001F4dd PLAN","\U0001F514 REMEMBER","\U0001F4B8 BILL DUE","\U0001F31f MILESTONE"],'
                # 2 WELLNESS
                '["\U0001F60d AMAZING","\U0001F642 GOOD","\U0001F610 OKAY",'
                '"\U0001F614 LOW","\U0001F4a7 WATER","\U0001F634 SLEEP WELL",'
                '"\U0001F3cb WORKOUT","\U0001F64f GRATEFUL","\U0001F9d8 CALM",'
                '"⚡ HIGH ENERGY","\U0001F957 MEALS","\U0001F33f SELF CARE",'
                '"\U0001F48a MEDS","❤ SELF LOVE","\U0001F31e SUNSHINE","\U0001F9e0 MINDFUL"],'
                # 3 SCHOOL
                '["\U0001F4da STUDY","\U0001F4dd NOTES","\U0001F9ea TEST DAY",'
                '"\U0001F4e5 SUBMIT","⏰ DUE DATE","✅ REVIEWED",'
                '"\U0001F4ac PRESENT","\U0001F4bb ONLINE","\U0001F3af FOCUS!",'
                '"\U0001F6ab NO PHONE","\U0001F4da READ","✍ WRITE",'
                '"\U0001F4c8 PROGRESS","\U0001F31f GREAT WORK","\U0001F3c5 ACHIEVEMENT","\U0001F680 LEVEL UP"],'
                # 4 MOTIVATION
                '["\U0001F680 YOU GOT THIS","\U0001F4aa STRONG",'
                '"\U0001F31f SHINE","\U0001F525 ON FIRE",'
                '"\U0001F3af CRUSHED IT","\U0001F4cf GROWTH",'
                '"\U0001F49c BELIEVE","✨ MAGIC DAY",'
                '"\U0001F334 FRESH START","\U0001F30a GO WITH IT",'
                '"\U0001F308 NEW CHAPTER","\U0001F64c YES!",'
                '"\U0001F31b GLOW UP","\U0001F4ab DREAM BIG",'
                '"❤ BE KIND","\U0001F3b6 GOOD VIBES"]'
                '];'
                'var stkIdx=app.popupMenu(lists[catIdx]);'
                'if(stkIdx<0)return;'
                'var lbl=lists[catIdx][stkIdx];'
                # Colors per category: coral, sky, sage, lilac, gold
                'var fc=[["RGB",1.0,0.88,0.85],["RGB",0.85,0.93,1.0],'
                '["RGB",0.88,0.97,0.88],["RGB",0.93,0.88,1.0],["RGB",1.0,0.96,0.82]];'
                'var sc=[["RGB",0.85,0.38,0.32],["RGB",0.28,0.52,0.82],'
                '["RGB",0.28,0.62,0.38],["RGB",0.55,0.32,0.80],["RGB",0.80,0.62,0.18]];'
                'var pg=this.pageNum;'
                'var ph=this.getPageHeight(pg);'
                'var pw=this.getPageWidth(pg);'
                'try{'
                'var a=this.addAnnot({'
                'type:"FreeText",page:pg,'
                'rect:[pw*0.33,ph*0.45,pw*0.67,ph*0.57],'
                'contents:lbl,'
                'fillColor:fc[catIdx],'
                'strokeColor:sc[catIdx],'
                'textColor:["RGB",0.08,0.08,0.12],'
                'textSize:11,alignment:1'
                '});'
                'if(a)app.alert("✨ Sticker added! Drag it anywhere you like.",1);'
                '}catch(e){'
                'app.alert("Tap the STICKERS button to add a label sticker to this page.\\n\\nWorks in: Adobe Acrobat Reader, Acrobat Pro, PDF Expert, and Xodo.\\n\\nGoodNotes users: screenshot the Sticker Sheet page to use as a custom sticker library.",1);'
                '}'
            )
            # Always add page-nav link first (works in ALL viewers including GoodNotes)
            c.linkAbsolute("Sticker Library", "sticker_picker",
                           (_sx, _sy, _sx + _sw, _sy + _bh))
            # Then overlay JS link on top (Acrobat users get popup menu instead)
            _js_button(_sx, _sy, _sw, _bh, _sticker_js)

        font("Helvetica", 6); fill(MID)
        if label:
            c.drawCentredString((PW - TAB_W) / 2, MB - 16, label)
        c.drawRightString(PW - MR - TAB_W - 6, MB - 16, "OnBrandCraftz")

    # ── Navigation tab bookmark registry ─────────────────────────────────────
    # We build this list in order; each entry is (label, bookmark_key)
    NAV_TABS: list[tuple[str, str]] = []
    if "monthly" in sections:
        for m in MONTHS:
            NAV_TABS.append((m[:3].upper(), f"month_{m[:3].lower()}"))
    if "weekly"       in sections: NAV_TABS.append(("WK",    "weekly_start"))
    if "habit_tracker"in sections: NAV_TABS.append(("HABIT", "habits"))
    if "goals"        in sections: NAV_TABS.append(("GOALS", "goals"))
    if "budget"       in sections: NAV_TABS.append(("BUDG",  "budget"))
    if "meal_plan"    in sections: NAV_TABS.append(("MEAL",  "meal_plan"))
    if "notes"        in sections: NAV_TABS.append(("NOTES", "notes"))

    def draw_nav_tabs(active_bm=None):
        """Draw side navigation tabs on every interior page."""
        start_y = PH - MT - 20
        for i, (label, bm) in enumerate(NAV_TABS):
            ty = start_y - i * (TAB_H + TAB_GAP)
            if ty < MB:
                break
            is_active = (bm == active_bm)
            base_tc   = _TAB_OVERRIDE if _TAB_OVERRIDE else T
            tab_color = base_tc if is_active else _blend(base_tc, 0.68)
            text_color = WHITE if is_active else _blend(WHITE, 0.25)
            rect(TAB_X, ty, TAB_W, TAB_H, f=tab_color, radius=3)
            c.saveState()
            c.translate(TAB_X + TAB_W / 2, ty + TAB_H / 2)
            c.rotate(90)
            font("Helvetica-Bold", 5.5)
            fill(text_color)
            c.drawCentredString(0, -2, label)
            c.restoreState()
            # Clickable internal link
            c.linkAbsolute(label, bm, (TAB_X, ty, TAB_X + TAB_W, ty + TAB_H))

    # ── Fillable field helpers ────────────────────────────────────────────────
    _field_counter = [0]

    def text_field(x, y, w, h, name_hint="field", multiline=False, font_size=9):
        if not is_interactive:
            rect(x, y, w, h, s=_blend(LIGHT, -0.05), lwidth=0.4, radius=1)
            return
        _field_counter[0] += 1
        fname = f"{product_id}_{name_hint}_{_field_counter[0]}"
        flags = "multiline" if multiline else ""
        c.acroForm.textfield(
            name=fname,
            tooltip=name_hint.replace("_", " ").title(),
            x=x, y=y, width=w, height=h,
            borderStyle="solid",
            borderWidth=0.5,
            borderColor=_col(_blend(T, 0.88)),
            fillColor=_col(_blend(T, 0.975)),
            textColor=_col(DARK),
            fontSize=font_size,
            forceBorder=True,
            fieldFlags=flags,
        )

    def checkbox_field(x, y, size=9, name_hint="cb"):
        if not is_interactive:
            rect(x, y, size, size, s=_blend(LIGHT, -0.05), lwidth=0.5, radius=1.5)
            return
        _field_counter[0] += 1
        fname = f"{product_id}_{name_hint}_{_field_counter[0]}"
        c.acroForm.checkbox(
            name=fname,
            tooltip="Check when complete",
            x=x, y=y,
            size=size,
            borderWidth=0.6,
            borderColor=_col(MID),
            fillColor=_col(BG),
            textColor=_col(T),
            buttonStyle="check",
            forceBorder=True,
        )

    # ── Sticker-picker JavaScript infrastructure (Tier 3 only) ───────────────
    # Hidden AcroForm text fields store: which page + cell rect the ★ was tapped on.
    # JavaScript on each sticker button reads these, places an annotation, and returns.
    _stk_pg = f"__stk_pg_{product_id}"   # 0-indexed page number (-1 = none selected)
    _stk_x  = f"__stk_x_{product_id}"
    _stk_y  = f"__stk_y_{product_id}"
    _stk_w  = f"__stk_w_{product_id}"
    _stk_h  = f"__stk_h_{product_id}"

    def _make_hidden_field(fname, val="-1"):
        """1×1 invisible text field used as a JS-accessible state variable."""
        c.acroForm.textfield(
            name=fname, value=val,
            x=1, y=1, width=2, height=2,
            borderStyle='solid',
            borderColor=_col(WHITE), fillColor=_col(WHITE), textColor=_col(WHITE),
            fontSize=1, forceBorder=False,
        )

    def _js_button(cx, cy, cw, ch, js_code):
        """Overlay an invisible Link annotation with a JavaScript action.
        Link annotations fire JS reliably in Acrobat Reader, Acrobat Pro, PDF Expert,
        and Xodo — no AcroForm registration needed.
        Returns True on success, False on fallback."""
        try:
            from reportlab.pdfbase.pdfdoc import (
                PDFDictionary, PDFString, PDFArray, PDFnumber, PDFName,
            )
            js_act = PDFDictionary()
            js_act['S'] = PDFName('JavaScript')
            js_act['JS'] = PDFString(js_code)
            link = PDFDictionary()
            link['Type']    = PDFName('Annot')
            link['Subtype'] = PDFName('Link')
            link['Rect']    = PDFArray([float(cx), float(cy),
                                        float(cx + cw), float(cy + ch)])
            link['Border']  = PDFArray([PDFnumber(0), PDFnumber(0), PDFnumber(0)])
            link['A']       = js_act
            c._addAnnotation(link)
            return True
        except Exception:
            return False

    # ── COVER PAGE ───────────────────────────────────────────────────────────
    def draw_cover():
        c.bookmarkPage("cover")
        c.addOutlineEntry("Cover", "cover", level=0)

        cx       = PW / 2
        split_y  = PH * 0.375
        top_h    = PH - split_y

        rect(0, 0, PW, PH, f=BG)

        # ── Apply cover art if provided ───────────────────────────────────────
        cover_img_path = data.get("cover_image_path") or ""
        full_page_cover = bool(data.get("full_page_cover", False))
        use_art = cover_img_path and os.path.exists(cover_img_path)
        if use_art and full_page_cover:
            # Full-page kawaii illustration cover — fills entire page
            try:
                c.drawImage(ImageReader(cover_img_path), 0, 0, PW, PH,
                            preserveAspectRatio=False)
                # Light vignette at very bottom for title readability
                c.saveState()
                c.setFillAlpha(0.45); c.setFillColorRGB(*BG)
                c.rect(0, 0, PW, PH * 0.18, fill=1, stroke=0)
                c.setFillAlpha(1.0); c.restoreState()
                c.showPage()
                return  # Full-page cover is complete — skip tier drawing
            except Exception:
                full_page_cover = False
        elif use_art:
            try:
                c.drawImage(ImageReader(cover_img_path), 0, split_y, PW, top_h,
                            preserveAspectRatio=False)
                c.setFillAlpha(0.18); c.setFillColorRGB(*T)
                c.rect(0, split_y, PW, top_h, fill=1, stroke=0)
                c.setFillAlpha(1.0)
            except Exception:
                use_art = False

        # ══════════════════════════════════════════════════════════════════════
        # TIER 1 — CLEAN MINIMAL COVER
        # ══════════════════════════════════════════════════════════════════════
        if _design == 1:
            if not use_art:
                rect(0, split_y, PW, top_h, f=T)
                # Single small accent circle in upper-right
                circle(PW - 30, PH - 30, 55, f=_blend(T, 0.22))

            # Thin top bar
            rect(0, PH - 4, PW, 4, f=A)
            # Accent stripe at split
            rect(0, split_y - 4, PW, 4, f=A)

            # Title — large and centered
            font("Helvetica-Bold", 42); fill(WHITE)
            words = title.split()
            title_cy = split_y + top_h * 0.52
            if len(title) <= 22:
                c.drawCentredString(cx, title_cy + 6, title)
                txt_bot = title_cy - 14
            else:
                mid = len(words) // 2
                c.drawCentredString(cx, title_cy + 28, " ".join(words[:mid]))
                c.drawCentredString(cx, title_cy - 4,  " ".join(words[mid:]))
                txt_bot = title_cy - 20
            hline(cx - 55, cx + 55, txt_bot - 12, _blend(WHITE, 0.35), 0.6)
            if subtitle:
                font("Helvetica", 10); fill(_blend(WHITE, 0.55))
                c.drawCentredString(cx, txt_bot - 27, subtitle.upper())

            # Year badge
            badge_label = "UNDATED" if undated else str(planner_year)
            rect(cx - 38, split_y + 18, 76, 20, f=A, radius=4)
            font("Helvetica-Bold", 10); fill(DARK)
            c.drawCentredString(cx, split_y + 18 + 6, badge_label)

            # Bottom — section list as plain dot-separated text
            tl_y = split_y - 24
            font("Helvetica", 8.5); fill(MID)
            c.drawCentredString(cx, tl_y, "plan with purpose  \xb7  live with intention")
            hline(cx - 50, cx + 50, tl_y - 10, A, 0.7)
            _sec_labels = {
                "monthly": "Monthly", "weekly": "Weekly", "notes": "Notes",
                "habit_tracker": "Habits", "goals": "Goals",
                "budget": "Budget", "meal_plan": "Meals",
                "monthly_review": "Review", "month_at_a_glance": "At a Glance",
            }
            sec_text = "  ·  ".join(_sec_labels.get(s, s.title()) for s in sections)
            font("Helvetica", 8); fill(MID)
            c.drawCentredString(cx, tl_y - 28, sec_text)

        # ══════════════════════════════════════════════════════════════════════
        # TIER 2 — POLISHED TWO-TONE COVER (current design)
        # ══════════════════════════════════════════════════════════════════════
        elif _design == 2:
            if not use_art:
                rect(0, split_y, PW, top_h, f=T)
                circle(PW + 8, PH + 8, PW * 0.48, f=_blend(T, 0.17))
                circle(-12, split_y + 55, 80, f=_blend(T, 0.20))
                circle(ML + 15, PH - MT - 16, 11, f=A)
                circle(ML + 36, PH - MT - 16,  5, f=AL)
                circle(ML + 15, PH - MT - 40,  5, f=_blend(A, 0.55))
                for i in range(3):
                    hline(ML + 50, ML + 100, PH - MT - 12 - i * 8,
                          _blend(WHITE, 0.30), 0.5)
                dp = 9; dr = 0.55
                gx = ML + 4; gy0 = split_y + 18; gy1 = split_y + int(top_h * 0.22)
                while gx <= PW - ML:
                    gy = gy0
                    while gy <= gy1:
                        circle(gx, gy, dr, f=_blend(T, 0.28))
                        gy += dp
                    gx += dp
            rect(0, PH - 6, PW, 6, f=A)
            title_cy = split_y + top_h * 0.545
            font("Helvetica-Bold", 44); fill(WHITE)
            words = title.split()
            if len(title) <= 22:
                c.drawCentredString(cx, title_cy + 8, title); txt_bot = title_cy - 16
            else:
                mid = len(words) // 2
                c.drawCentredString(cx, title_cy + 30, " ".join(words[:mid]))
                c.drawCentredString(cx, title_cy - 4,  " ".join(words[mid:]))
                txt_bot = title_cy - 22
            hline(cx - 68, cx + 68, txt_bot - 13, _blend(WHITE, 0.42), 0.7)
            if subtitle:
                font("Helvetica", 10); fill(_blend(WHITE, 0.60))
                c.drawCentredString(cx, txt_bot - 29, subtitle.upper())
            badge_label = "UNDATED" if undated else str(planner_year)
            bw = 80; bh = 22
            rect(cx - bw/2, split_y + 22, bw, bh, f=A, radius=5)
            font("Helvetica-Bold", 11); fill(DARK)
            c.drawCentredString(cx, split_y + 22 + 7, badge_label)
            rect(0, split_y - 5, PW, 5, f=A); rect(0, split_y - 8, PW, 2, f=AL)
            tl_y = split_y - 28
            font("Helvetica", 9); fill(MID)
            c.drawCentredString(cx, tl_y, "plan with purpose  \xb7  live with intention")
            hline(cx - 58, cx + 58, tl_y - 11, A, 0.9)
            hline(cx - 40, cx + 40, tl_y - 15, AL, 0.5)
            inside_y = tl_y - 33
            font("Helvetica-Bold", 7); fill(T)
            c.drawCentredString(cx, inside_y, "INSIDE THIS PLANNER")
            _sec_labels = {
                "monthly": "Monthly Overview", "weekly": "Weekly Planning",
                "habit_tracker": "Habit Tracker", "goals": "Goals & Vision",
                "notes": "Notes Pages", "daily": "Daily Pages",
                "budget": "Budget Tracker", "meal_plan": "Meal Planning",
                "monthly_review": "Monthly Review",
                "month_at_a_glance": "Month at a Glance",
            }
            tags = [_sec_labels.get(s, s.replace("_", " ").title()) for s in sections]
            tag_h = 14; tpad = 8; tgap = 5
            font("Helvetica", 7)
            tag_widths = [c.stringWidth(t, "Helvetica", 7) + tpad * 2 for t in tags]
            max_row_w = PW - ML * 2
            rows: list = []; row: list = []; row_w = 0.0
            for tag, tw in zip(tags, tag_widths):
                gap = tgap if row else 0
                if row_w + gap + tw > max_row_w and row:
                    rows.append(row); row = [(tag, tw)]; row_w = tw
                else:
                    row.append((tag, tw)); row_w += gap + tw
            if row:
                rows.append(row)
            ty = inside_y - 16
            for ri, row in enumerate(rows[:3]):
                total_w = sum(tw for _, tw in row) + tgap * (len(row) - 1)
                rx = cx - total_w / 2; ry = ty - ri * (tag_h + 5)
                for tag, tw in row:
                    rect(rx, ry - tag_h + 2, tw, tag_h, f=_blend(T, 0.87), radius=4)
                    font("Helvetica", 7); fill(T)
                    c.drawString(rx + tpad, ry - 4, tag)
                    rx += tw + tgap

        # ══════════════════════════════════════════════════════════════════════
        # TIER 3 — PREMIUM CONNECTED COVER
        # ══════════════════════════════════════════════════════════════════════
        else:
            if not use_art:
                rect(0, split_y, PW, top_h, f=T)
                # Large primary arc — upper-right
                circle(PW + 14, PH + 14, PW * 0.52, f=_blend(T, 0.16))
                # Second overlapping arc — lower-right of block
                circle(PW + 5, split_y + 60, PW * 0.28, f=_blend(T, 0.20))
                # Medium circle — lower-left for balance
                circle(-18, split_y + 70, 95, f=_blend(T, 0.18))
                # Accent dot cluster
                circle(ML + 16, PH - MT - 16, 13, f=A)
                circle(ML + 40, PH - MT - 14,  6, f=AL)
                circle(ML + 16, PH - MT - 44,  6, f=_blend(A, 0.55))
                for i in range(4):
                    hline(ML + 56, ML + 115, PH - MT - 10 - i * 8,
                          _blend(WHITE, 0.28), 0.5)
                # Rich dot grid across entire top block
                dp = 8; dr = 0.6
                gx = ML + 4; gy0 = split_y + 16; gy1 = split_y + int(top_h * 0.38)
                while gx <= PW - ML:
                    gy = gy0
                    while gy <= gy1:
                        circle(gx, gy, dr, f=_blend(T, 0.26))
                        gy += dp
                    gx += dp
                # Diagonal accent band (upper-left)
                for i in range(6):
                    hline(0, ML + 30 + i * 8, PH - MT - 28 - i * 12,
                          _blend(A, 0.22), 0.4)
            # Premium top bar
            rect(0, PH - 7, PW, 7, f=A)
            rect(0, PH - 10, PW, 2, f=AL)

            # Title
            title_cy = split_y + top_h * 0.545
            font("Helvetica-Bold", 44); fill(WHITE)
            words = title.split()
            if len(title) <= 22:
                c.drawCentredString(cx, title_cy + 8, title); txt_bot = title_cy - 16
            else:
                mid = len(words) // 2
                c.drawCentredString(cx, title_cy + 30, " ".join(words[:mid]))
                c.drawCentredString(cx, title_cy - 4,  " ".join(words[mid:]))
                txt_bot = title_cy - 22
            hline(cx - 72, cx + 72, txt_bot - 13, _blend(WHITE, 0.45), 0.8)
            if subtitle:
                font("Helvetica", 10); fill(_blend(WHITE, 0.62))
                c.drawCentredString(cx, txt_bot - 29, subtitle.upper())

            # Year badge + CONNECTED badge side by side
            badge_label = "UNDATED" if undated else str(planner_year)
            bw = 78; bh = 22
            tier_badge = "CONNECTED"
            tbw = 86
            total_bw = bw + 8 + tbw
            bx0 = cx - total_bw / 2
            rect(bx0, split_y + 22, bw, bh, f=A, radius=5)
            font("Helvetica-Bold", 11); fill(DARK)
            c.drawCentredString(bx0 + bw/2, split_y + 22 + 7, badge_label)
            rect(bx0 + bw + 8, split_y + 22, tbw, bh, f=_blend(A, 0.60), radius=5)
            font("Helvetica-Bold", 9.5); fill(WHITE)
            c.drawCentredString(bx0 + bw + 8 + tbw/2, split_y + 22 + 7, tier_badge)

            # Premium split stripe (double)
            rect(0, split_y - 6, PW, 6, f=A)
            rect(0, split_y - 10, PW, 3, f=AL)
            rect(0, split_y - 13, PW, 2, f=_blend(A, 0.45))

            # Bottom section
            tl_y = split_y - 30
            font("Helvetica", 9); fill(MID)
            c.drawCentredString(cx, tl_y, "plan with purpose  \xb7  live with intention")
            hline(cx - 62, cx + 62, tl_y - 11, A, 0.9)
            hline(cx - 42, cx + 42, tl_y - 15, AL, 0.5)
            inside_y = tl_y - 33
            font("Helvetica-Bold", 7); fill(T)
            c.drawCentredString(cx, inside_y, "INSIDE THIS PLANNER")
            _sec_labels = {
                "monthly": "Monthly Overview", "weekly": "Weekly Planning",
                "habit_tracker": "Habit Tracker", "goals": "Goals & Vision",
                "notes": "Notes Pages", "daily": "Daily Pages",
                "budget": "Budget Tracker", "meal_plan": "Meal Planning",
                "monthly_review": "Monthly Review",
                "month_at_a_glance": "Month at a Glance",
            }
            tags = [_sec_labels.get(s, s.replace("_", " ").title()) for s in sections]
            if cal_integration in ("google", "both"):
                tags.append("Google Calendar")
            if cal_integration in ("apple", "both"):
                tags.append("Apple Calendar")
            tag_h = 14; tpad = 8; tgap = 5
            font("Helvetica", 7)
            tag_widths = [c.stringWidth(t, "Helvetica", 7) + tpad * 2 for t in tags]
            max_row_w = PW - ML * 2
            rows: list = []; row: list = []; row_w = 0.0
            for tag, tw in zip(tags, tag_widths):
                gap = tgap if row else 0
                if row_w + gap + tw > max_row_w and row:
                    rows.append(row); row = [(tag, tw)]; row_w = tw
                else:
                    row.append((tag, tw)); row_w += gap + tw
            if row:
                rows.append(row)
            ty = inside_y - 16
            for ri, row in enumerate(rows[:3]):
                total_w = sum(tw for _, tw in row) + tgap * (len(row) - 1)
                rx = cx - total_w / 2; ry = ty - ri * (tag_h + 5)
                for ti2, (tag, tw) in enumerate(row):
                    # Calendar tags get accent color, others get theme color
                    is_cal = tag in ("Google Calendar", "Apple Calendar")
                    pill_f = _blend(A, 0.80) if is_cal else _blend(T, 0.87)
                    pill_c = DARK if is_cal else T
                    rect(rx, ry - tag_h + 2, tw, tag_h, f=pill_f, radius=4)
                    font("Helvetica-Bold" if is_cal else "Helvetica", 7); fill(pill_c)
                    c.drawString(rx + tpad, ry - 4, tag)
                    rx += tw + tgap

        # ── Shared footer (all tiers) ─────────────────────────────────────────
        font("Helvetica", 7); fill(_blend(MID, 0.50))
        c.drawCentredString(cx, MB + 8,
                            "OnBrandCraftz  \xb7  Digital Download  \xb7  Personal Use")

        # Hidden state fields for sticker picker JS (created once on cover page)
        if _design == 3 and "sticker_pack" in _extras:
            for _fn, _fv in [(_stk_pg, "-1"), (_stk_x, "0"),
                              (_stk_y, "0"), (_stk_w, "0"), (_stk_h, "0")]:
                _make_hidden_field(_fn, _fv)

        c.showPage()

    # ── HOW TO USE PAGE ──────────────────────────────────────────────────────
    def draw_how_to_use():
        c.bookmarkPage("how_to_use")
        c.addOutlineEntry("How to Use", "how_to_use", level=0)
        page_bg()
        rect(0, 0, PW, PH, f=BG)

        # Header
        rect(0, PH - MT - 50, PW, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawCentredString(PW / 2, PH - MT - 34, "HOW TO USE THIS PLANNER")
        rect(0, PH - MT - 54, PW, 4, f=A)

        y = PH - MT - 80
        cx = PW / 2

        steps = [
            ("📱", "Open in Your Favorite App",
             "Works in GoodNotes 5/6, Notability, Noteshelf, Xodo (free), PDF Expert, and Adobe Reader.\n"
             "iPad users: GoodNotes or Notability give the best annotation experience."),
            ("🔗", "Use the Navigation Tabs",
             "Tap any colored tab on the right side of every page to jump instantly\n"
             "to that section. Month tabs jump to monthly views, HABIT to your tracker, etc."),
            ("✏️", "Fill In Your Information",
             "Tap any outlined text box to type directly into the planner.\n"
             "All fields are fillable — goals, notes, priorities, intentions, and more."),
            ("✅", "Use the Interactive Checkboxes",
             "Habit tracker checkboxes are clickable — tap to mark your habits complete.\n"
             "To-do checkboxes work the same way throughout."),
            ("🖨️", "Print It Out (Optional)",
             "Export to PDF and print at home or at a local print shop.\n"
             "Recommended: 100% scale, color, letter or A4 size."),
        ]

        step_h = (y - MB - 20) / len(steps)
        for i, (icon, heading, detail) in enumerate(steps):
            sy = y - i * step_h
            # Number circle
            circle(ML + 14, sy - 16, 13, f=T)
            font("Helvetica-Bold", 11); fill(WHITE)
            c.drawCentredString(ML + 14, sy - 20, str(i + 1))
            # Icon + heading
            font("Helvetica-Bold", 11); fill(T)
            c.drawString(ML + 34, sy - 13, heading)
            # Detail lines
            font("Helvetica", 8.5); fill(MID)
            for li, line in enumerate(detail.split("\n")):
                c.drawString(ML + 34, sy - 26 - li * 13, line.strip())
            # Separator
            if i < len(steps) - 1:
                hline(ML + 28, PW - MR - 4, sy - step_h + 8, LIGHT, 0.4)

        page_footer("HOW TO USE")
        c.showPage()

    # ── WELCOME / SETUP PAGE ─────────────────────────────────────────────────
    def draw_welcome_page():
        c.bookmarkPage("welcome")
        c.addOutlineEntry("Welcome & Setup", "welcome", level=0)
        rect(0, 0, PW, PH, f=BG)
        if _design == 3:
            _dp = 20; _dr = 0.38
            _gx = ML + _dp
            while _gx <= PW - MR - TAB_W - 4:
                _gy = MB + _dp
                while _gy <= PH - MT - _dp:
                    circle(_gx, _gy, _dr, f=LIGHT)
                    _gy += _dp
                _gx += _dp

        cx = PW / 2
        content_w = CW - TAB_W - 4

        # ── Header bar ──────────────────────────────────────────────────────
        rect(0, PH - MT - 54, PW - TAB_W - 2, 54 + MT, f=T)
        rect(0, PH - MT - 54, 7, 54 + MT, f=A)
        rect(0, PH - MT - 58, PW - TAB_W - 2, 4, f=A)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 18, PH - MT - 32, f"Welcome to {title}")
        font("Helvetica", 8.5); fill(_blend(WHITE, 0.50))
        c.drawString(ML + 18, PH - MT - 47, "OnBrandCraftz  ·  Printing3dthings@outlook.com")

        y = PH - MT - 84

        # ── DOWNLOAD YOUR FILES ─────────────────────────────────────────────
        rect(ML, y - 2, content_w, 20, f=_blend(T, 0.88), radius=3)
        font("Helvetica-Bold", 8.5); fill(T)
        c.drawString(ML + 10, y + 5, "📥  HOW TO DOWNLOAD YOUR FILES")
        y -= 22

        download_steps = [
            "Go to your Etsy account → Purchases & Reviews",
            "Find this order → click Download Files",
            "Save the PDF and the Sticker Pack ZIP to your device",
        ]
        for i, step in enumerate(download_steps):
            circle(ML + 12, y - 6, 8, f=T)
            font("Helvetica-Bold", 7); fill(WHITE)
            c.drawCentredString(ML + 12, y - 8.5, str(i + 1))
            font("Helvetica", 8); fill(DARK)
            c.drawString(ML + 26, y - 10, step)
            y -= 18

        y -= 10

        # ── GOODNOTES / NOTABILITY SETUP ────────────────────────────────────
        rect(ML, y - 2, content_w, 20, f=_blend(A, 0.50), radius=3)
        font("Helvetica-Bold", 8.5); fill(DARK)
        c.drawString(ML + 10, y + 5, "📱  OPEN IN GOODNOTES 6 OR NOTABILITY")
        y -= 22

        app_steps = [
            "GoodNotes 6: tap + (New Document) → Import → select the PDF",
            "Notability: tap + → Import → select the PDF from Files",
            "iPad tip: use the Files app to access your Downloads folder",
        ]
        for i, step in enumerate(app_steps):
            circle(ML + 12, y - 6, 8, f=_blend(A, 0.80))
            font("Helvetica-Bold", 7); fill(WHITE)
            c.drawCentredString(ML + 12, y - 8.5, str(i + 1))
            font("Helvetica", 8); fill(DARK)
            c.drawString(ML + 26, y - 10, step)
            y -= 18

        y -= 10

        # ── STICKER PACK SETUP ──────────────────────────────────────────────
        rect(ML, y - 2, content_w, 20, f=_blend(T, 0.88), radius=3)
        font("Helvetica-Bold", 8.5); fill(T)
        c.drawString(ML + 10, y + 5, "🎨  IMPORT YOUR STICKER PACK")
        y -= 22

        sticker_steps = [
            "Unzip the Sticker Pack ZIP file on your device",
            "GoodNotes 6: Elements (◇) → Stickers → + → select all 5 PNG sheets",
            "Stickers appear in your library — drag onto any page, unlimited times!",
        ]
        for i, step in enumerate(sticker_steps):
            circle(ML + 12, y - 6, 8, f=T)
            font("Helvetica-Bold", 7); fill(WHITE)
            c.drawCentredString(ML + 12, y - 8.5, str(i + 1))
            font("Helvetica", 8); fill(DARK)
            c.drawString(ML + 26, y - 10, step)
            y -= 18

        y -= 16

        # ── Compatible apps ─────────────────────────────────────────────────
        font("Helvetica-Bold", 7); fill(MID)
        c.drawString(ML, y, "WORKS WITH:")
        y -= 12
        apps_row = ["GoodNotes 6", "Notability", "PDF Expert", "Xodo", "Acrobat Reader", "Print-ready"]
        apps_x = ML
        for app in apps_row:
            _aw = c.stringWidth(app, _fn("regular"), 7.5) + 12
            rect(apps_x, y - 12, _aw, 14, f=_blend(T, 0.88), radius=3)
            font("Helvetica", 7.5); fill(T)
            c.drawString(apps_x + 6, y - 8, app)
            apps_x += _aw + 5
            if apps_x > ML + content_w - 80:
                break

        y -= 26

        # ── Dashboard button ────────────────────────────────────────────────
        _dbw = 160; _dbh = 24; _dbx = cx - _dbw / 2; _dby = y - _dbh
        rect(_dbx, _dby, _dbw, _dbh, f=T, radius=6)
        font("Helvetica-Bold", 9); fill(WHITE)
        c.drawCentredString(cx, _dby + 8, "GO TO PLANNER DASHBOARD  →")
        c.linkAbsolute("Dashboard", "dashboard", (_dbx, _dby, _dbx + _dbw, _dby + _dbh))

        # ── Support footer ──────────────────────────────────────────────────
        font("Helvetica", 7); fill(MID)
        c.drawCentredString(cx, MB + 6,
            "Questions? Email Printing3dthings@outlook.com  ·  OnBrandCraftz on Etsy")

        draw_nav_tabs("welcome")
        c.showPage()

    # ── DASHBOARD / HOME PAGE ────────────────────────────────────────────────
    def draw_dashboard_page():
        c.bookmarkPage("dashboard")
        c.addOutlineEntry("Dashboard", "dashboard", level=0)
        rect(0, 0, PW, PH, f=BG)
        if _design == 3:
            _dp = 20; _dr = 0.38
            _gx = ML + _dp
            while _gx <= PW - MR - TAB_W - 4:
                _gy = MB + _dp
                while _gy <= PH - MT - _dp:
                    circle(_gx, _gy, _dr, f=LIGHT)
                    _gy += _dp
                _gx += _dp

        cx = PW / 2
        content_w = CW - TAB_W - 4

        # ── Header bar ──────────────────────────────────────────────────────
        rect(0, PH - MT - 60, PW - TAB_W - 2, 60 + MT, f=T)
        rect(0, PH - MT - 60, 7, 60 + MT, f=A)
        rect(0, PH - MT - 64, PW - TAB_W - 2, 4, f=A)

        year_tag = "UNDATED" if undated else str(planner_year)
        font("Helvetica-Bold", 24); fill(WHITE)
        c.drawString(ML + 18, PH - MT - 36, title)
        font("Helvetica", 8.5); fill(_blend(WHITE, 0.55))
        c.drawString(ML + 18, PH - MT - 54,
                     f"{cs['label']}  ·  {year_tag}  ·  OnBrandCraftz")

        y = PH - MT - 86

        # ── Section navigation buttons grid ─────────────────────────────────
        _DASH_SECTIONS = []
        if "monthly" in sections or "weekly" in sections:
            _DASH_SECTIONS.append(("📅", "Year Overview",  "yearly"))
        if "monthly" in sections:
            _DASH_SECTIONS.append(("🗓", "Monthly",        "month_jan"))
        if "monthly_review" in sections:
            _DASH_SECTIONS.append(("🔁", "Monthly Review", "monthly_review_0"))
        if "month_at_a_glance" in sections:
            _DASH_SECTIONS.append(("👁", "Month at a Glance", "month_glance_0"))
        if "weekly" in sections:
            _DASH_SECTIONS.append(("📋", "Weekly Planner", "weekly_start"))
        if "habit_tracker" in sections:
            _DASH_SECTIONS.append(("✅", "Habit Tracker",  "habits"))
        if "goals" in sections:
            _DASH_SECTIONS.append(("🎯", "Goals",          "goals"))
        if "budget" in sections:
            _DASH_SECTIONS.append(("💰", "Budget",         "budget"))
        if "meal_plan" in sections:
            _DASH_SECTIONS.append(("🥗", "Meal Planner",   "meal_plan"))
        if "notes" in sections:
            _DASH_SECTIONS.append(("📝", "Notes",          "notes"))
        if "sticker_pack" in _extras:
            _DASH_SECTIONS.append(("✨", "Sticker Library","sticker_picker"))
        _DASH_SECTIONS.append(("📖", "How to Use",     "how_to_use"))
        _DASH_SECTIONS.append(("📑", "Index",          "index"))

        cols = 3
        btn_w = (content_w - (cols - 1) * 8) / cols
        btn_h = 38
        gutter = 8

        for idx, (icon, label_txt, bm) in enumerate(_DASH_SECTIONS):
            col = idx % cols
            row = idx // cols
            bx = ML + col * (btn_w + gutter)
            by = y - row * (btn_h + gutter) - btn_h
            if by < MB + 30:
                break

            # Button background — alternate theme shades
            btn_bg = _blend(T, 0.88) if idx % 2 == 0 else _blend(A, 0.55)
            rect(bx, by, btn_w, btn_h, f=btn_bg, radius=6)
            # Left accent stripe
            rect(bx, by, 4, btn_h, f=T, radius=2)

            # Icon + label
            font("Helvetica-Bold", 13); fill(T)
            c.drawString(bx + 12, by + btn_h * 0.56, icon)
            font("Helvetica-Bold", 8); fill(DARK)
            c.drawString(bx + 30, by + btn_h * 0.56, label_txt)
            font("Helvetica", 6.5); fill(MID)
            c.drawString(bx + 30, by + btn_h * 0.25, "tap to jump →")

            # Clickable link
            c.linkAbsolute(label_txt, bm, (bx, by, bx + btn_w, by + btn_h))

        # ── Bottom instruction strip ─────────────────────────────────────────
        font("Helvetica", 7); fill(MID)
        c.drawCentredString(cx, MB + 10,
            "Tap any button to jump to that section  ·  Use ‹ INDEX or 🏠 HOME in the footer to return here")

        draw_nav_tabs("dashboard")
        c.showPage()

    # ── YEARLY OVERVIEW ──────────────────────────────────────────────────────
    def draw_yearly_overview():
        c.bookmarkPage("yearly")
        c.addOutlineEntry("Year at a Glance", "yearly", level=0)
        page_bg()

        year_label = "AT A GLANCE" if undated else f"{planner_year} AT A GLANCE"
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 8, PH - MT - 34, year_label)
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        avail_w = CW - TAB_W - 4
        cell_w = avail_w / 4 - 5
        y = PH - MT - 60
        cell_h = (y - MB - 12) / 3 - 8

        for i, month_name in enumerate(MONTHS):
            col = i % 4
            row = i // 4
            x0 = ML + col * (cell_w + 6)
            y0 = y - row * (cell_h + 10) - cell_h

            rect(x0, y0, cell_w, cell_h, f=WHITE, s=LIGHT, lwidth=0.5, radius=4)
            rect(x0, y0 + cell_h - 18, cell_w, 18, f=T, radius=4)
            font("Helvetica-Bold", 7.5); fill(WHITE)
            c.drawCentredString(x0 + cell_w/2, y0 + cell_h - 13, month_name[:3].upper())

            mini_dw = cell_w / 7
            for d, dn in enumerate(["M","T","W","T","F","S","S"]):
                font("Helvetica", 5); fill(TM if d < 5 else T)
                c.drawCentredString(x0 + d * mini_dw + mini_dw/2, y0 + cell_h - 27, dn)

            if not undated:
                cal = cal_mod.monthcalendar(planner_year, i + 1)
                for ri, week in enumerate(cal):
                    for di, day in enumerate(week):
                        if not day: continue
                        dx = x0 + di * mini_dw + mini_dw/2
                        dy = y0 + cell_h - 38 - ri * max((cell_h - 40) / max(len(cal),1), 8)
                        font("Helvetica", 4.5)
                        fill(T if di >= 5 else DARK)
                        c.drawCentredString(dx, dy, str(day))

        draw_nav_tabs("yearly")
        page_footer("YEAR AT A GLANCE")
        c.showPage()

    # ── MONTHLY PAGE ─────────────────────────────────────────────────────────
    def draw_monthly_page(month_idx):
        month_name = MONTHS[month_idx]
        month_num  = month_idx + 1
        bm = f"month_{month_name[:3].lower()}"
        c.bookmarkPage(bm)
        c.addOutlineEntry(month_name, bm, level=1)
        page_bg()

        content_w = CW - TAB_W - 4

        # Header — modern: cream bg + large theme-colored month name + accent stripe
        year_str = "" if undated else str(planner_year)
        rect(0, PH - MT - 56, PW - TAB_W - 2, 56 + MT, f=BG)
        # Thin accent top bar
        rect(0, PH - MT - 4, PW - TAB_W - 2, 4 + MT, f=T)
        # Large month name in theme color
        font("Helvetica-Bold", 32); fill(T)
        c.drawString(ML + 10, PH - MT - 38, month_name)
        # Year in mid-gray beside it
        if year_str:
            font("Helvetica", 13); fill(MID)
            mw = c.stringWidth(month_name, "Helvetica-Bold", 32)
            c.drawString(ML + 10 + mw + 8, PH - MT - 28, year_str)
        # Accent pill — day-of-week hint
        rect(ML + 10, PH - MT - 52, 42, 10, f=_blend(A, 0.55), radius=4)
        font("Helvetica-Bold", 5.5); fill(WHITE)
        c.drawCentredString(ML + 31, PH - MT - 45, "MONTHLY PLANNER")
        # Bottom accent stripe
        rect(0, PH - MT - 57, PW - TAB_W - 2, 2, f=_blend(T, 0.65))

        top_y     = PH - MT - 60
        notes_h   = 145
        cal_area  = top_y - MB - notes_h - 12
        day_h_row = 22
        num_rows  = 6
        row_h     = (cal_area - day_h_row) / num_rows
        col_w     = content_w / 7

        # Day headers — modern pill style
        for di, dn in enumerate(DAYS_SHORT):
            x0 = ML + di * col_w
            bg = T if di >= 5 else _blend(T, 0.70)
            rect(x0 + 1, top_y - day_h_row + 1, col_w - 2, day_h_row - 2, f=bg, radius=3)
            font("Helvetica-Bold", 7); fill(WHITE)
            c.drawCentredString(x0 + col_w/2, top_y - day_h_row + 6, dn)

        # Calendar grid
        if not undated:
            cal = cal_mod.monthcalendar(planner_year, month_num)
        else:
            # Generic 5-week undated calendar skeleton
            cal = [[0]*7 for _ in range(5)]

        for ri in range(num_rows):
            for di in range(7):
                cx0 = ML + di * col_w
                cy0 = top_y - day_h_row - (ri+1) * row_h
                # Weekend cells: very subtle tint; weekday cells: clean BG
                bg = _blend(T, 0.955) if di >= 5 else BG
                rect(cx0, cy0, col_w, row_h, f=bg, s=_blend(T, 0.80), lwidth=0.4, radius=2)

                day_num = 0
                if not undated and ri < len(cal):
                    day_num = cal[ri][di]

                # Button strip height at top of each cell
                _hdr_btn_h = 11
                _hdr_btn_y = cy0 + row_h - _hdr_btn_h - 1
                _btn_right  = cx0 + col_w - 2

                if day_num:
                    # Day number in a small circle bubble
                    _circle_r = 7
                    _circle_cx = cx0 + 10
                    _circle_cy = cy0 + row_h - 10
                    _day_bg = T if di >= 5 else _blend(T, 0.82)
                    circle(_circle_cx, _circle_cy, _circle_r, f=_day_bg)
                    font("Helvetica-Bold", 6); fill(WHITE)
                    c.drawCentredString(_circle_cx, _circle_cy - 2.5, str(day_num))

                    # ✨ Sticker button in cell header (Tier 3 only)
                    # Tapping it shows the category popup and places a sticker on THIS cell
                    if _design == 3 and "sticker_pack" in _extras:
                        sk = 13
                        sk_x = _btn_right - sk; sk_y = _hdr_btn_y - 1
                        # Gradient-like pill: soft accent fill + colored dot
                        rect(sk_x, sk_y, sk, sk, f=_blend(A, 0.75), radius=3)
                        font("Helvetica-Bold", 7); fill(WHITE)
                        c.drawCentredString(sk_x + sk / 2, sk_y + 3, "✨")
                        _cell_x = float(cx0 + 1)
                        _cell_y = float(cy0 + 4)
                        _cell_w = float(col_w - 2)
                        _cell_h = float(row_h - 18)
                        # JS: popup menu → place sticker directly in the cell
                        _js_cell = (
                            'var cats=["PRIORITY & TASKS","EVENTS & DATES",'
                            '"WELLNESS & MOOD","SCHOOL & WORK","MOTIVATION"];'
                            'var catIdx=app.popupMenu(cats);'
                            'if(catIdx<0)return;'
                            'var lists=['
                            '["! IMPORTANT","!! URGENT","⏰ DEADLINE","◈ MEETING",'
                            '"✓ TO-DO","◎ ERRANDS","🔥 BUSY DAY","◉ FOCUS",'
                            '"☎ CALL","✉ EMAIL","🛒 TO BUY","$ PAY BILL",'
                            '"📌 REMINDER","🚫 BLOCKED","👁 REVIEW","→ SUBMIT"],'
                            '["🎂 BIRTHDAY!","📅 APPT","✈ VACAY!","♥ ANNIV.",'
                            '"📷 MEMORIES","🎁 GIFT DUE","🎉 EVENT","🏡 FAMILY",'
                            '"⭐ HOLIDAY","🏆 GOAL MET!","✅ DONE!","⭐ WIN!",'
                            '"📝 PLAN","🌟 MILESTONE","💳 BILL DUE","🌙 NEW MOON"],'
                            '["😍 AMAZING","😊 GOOD","😐 OKAY","💜 LOW",'
                            '"💧 WATER","😴 SLEPT WELL","💪 WORKOUT","🙏 GRATEFUL",'
                            '"🧘 CALM","⚡ HIGH ENERGY","🥗 MEALS","🌸 SELF CARE",'
                            '"💊 MEDS","❤ SELF LOVE","☀ SUNSHINE","🌿 MINDFUL"],'
                            '["📚 STUDY","📝 NOTES","🧪 TEST","📤 SUBMIT",'
                            '"⏰ DUE DATE","✅ REVIEWED","🎤 PRESENT","💻 ONLINE",'
                            '"🎯 FOCUS!","🚫 NO PHONE","📖 READ","✍ WRITE",'
                            '"📈 PROGRESS","🌟 GREAT WORK","🏅 ACHIEVEMENT","🚀 LEVEL UP"],'
                            '["💪 YOU GOT THIS","🔥 STRONG","✨ SHINE","🔥 ON FIRE",'
                            '"🏆 CRUSHED IT","📈 GROWTH","💫 BELIEVE","✨ MAGIC DAY",'
                            '"🌱 FRESH START","🌊 GO WITH IT","📖 NEW CHAPTER","🙌 YES!",'
                            '"💅 GLOW UP","💭 DREAM BIG","❤ BE KIND","🎶 GOOD VIBES"]'
                            '];'
                            'var stkIdx=app.popupMenu(lists[catIdx]);'
                            'if(stkIdx<0)return;'
                            'var lbl=lists[catIdx][stkIdx];'
                            'var fc=[["RGB",1.0,0.88,0.85],["RGB",0.85,0.95,1.0],'
                            '["RGB",0.88,0.97,0.88],["RGB",0.90,0.88,1.0],["RGB",1.0,0.97,0.82]];'
                            'var sc=[["RGB",0.85,0.35,0.30],["RGB",0.25,0.55,0.85],'
                            '["RGB",0.25,0.65,0.38],["RGB",0.55,0.35,0.82],["RGB",0.82,0.62,0.15]];'
                            f'var pg=this.pageNum;'
                            f'try{{'
                            f'this.addAnnot({{type:"FreeText",page:pg,'
                            f'rect:[{_cell_x:.1f},{_cell_y:.1f},'
                            f'{_cell_x + _cell_w:.1f},{_cell_y + _cell_h:.1f}],'
                            f'contents:lbl,'
                            f'fillColor:fc[catIdx],strokeColor:sc[catIdx],'
                            f'textColor:["RGB",0.08,0.08,0.12],textSize:8,alignment:1}});}}'
                            f'catch(e){{'
                            f'app.alert("Sticker works in Acrobat, PDF Expert & Xodo.",1);}}'
                        )
                        if not _js_button(sk_x, sk_y, sk, sk, _js_cell):
                            c.linkAbsolute("Add Sticker", "sticker_picker",
                                           (sk_x, sk_y, sk_x + sk, sk_y + sk))
                        _btn_right -= sk + 2

                    # Google Calendar button
                    if cal_integration in ("google", "both") and not undated:
                        gcal_day = (f"https://calendar.google.com/calendar/r"
                                    f"/day/{planner_year}/{month_num}/{day_num}")
                        gcal_add = (f"https://calendar.google.com/calendar/r"
                                    f"/eventedit?dates={planner_year}{month_num:02d}{day_num:02d}"
                                    f"/{planner_year}{month_num:02d}{day_num:02d}")
                        c.linkURL(gcal_day, (cx0, cy0 + row_h - 14, cx0 + 18, cy0 + row_h))
                        bs = 11; bx = _btn_right - bs; by = _hdr_btn_y
                        rect(bx, by, bs, bs, f=_blend(A, 0.78), radius=2)
                        font("Helvetica-Bold", 6); fill(DARK)
                        c.drawCentredString(bx + bs / 2, by + 3, "G")
                        c.linkURL(gcal_add, (bx, by, bx + bs, by + bs))
                        _btn_right -= bs + 2

                    # Apple Calendar button
                    if cal_integration in ("apple", "both") and not undated:
                        _secs = int((_dt(planner_year, month_num, day_num)
                                     - _dt(2001, 1, 1)).total_seconds())
                        abs_ = 11; abx = _btn_right - abs_; aby = _hdr_btn_y
                        rect(abx, aby, abs_, abs_, f=_blend(T, 0.78), radius=2)
                        font("Helvetica-Bold", 5.5); fill(WHITE)
                        c.drawCentredString(abx + abs_ / 2, aby + 3, "A")
                        c.linkURL(f"calshow:{_secs}", (abx, aby, abx + abs_, aby + abs_))

                # Fillable event text area — ALWAYS added to every cell (undated AND dated)
                if is_interactive and row_h > 14:
                    _tf_top = row_h - (14 if day_num else 4)
                    text_field(cx0 + 2, cy0 + 2, col_w - 4, _tf_top - 2,
                               f"month_{month_num}_cell_{ri}_{di}", font_size=6)

        cal_bottom = top_y - day_h_row - num_rows * row_h

        # Notes below calendar
        notes_y_top = cal_bottom - 8
        col2_w  = (content_w - 8) / 2
        col2_x2 = ML + col2_w + 8

        for col_x, col_label in [(ML, "MONTHLY GOALS"), (col2_x2, "NOTES & HIGHLIGHTS")]:
            font("Helvetica-Bold", 7); fill(T)
            c.drawString(col_x, notes_y_top, col_label)
            field_h = notes_y_top - MB - 12
            if field_h > 10:
                text_field(col_x, MB + 8, col2_w, field_h,
                           f"month_{month_num}_{col_label[:4].lower()}", multiline=True)

        draw_nav_tabs(bm)
        page_footer(f"{month_name.upper()}  {year_str}".strip())
        c.showPage()

    # ── WEEKLY PAGE ──────────────────────────────────────────────────────────
    _weekly_page_count = [0]

    def draw_weekly_page(week_num_or_label, start_date=None):
        is_first = (_weekly_page_count[0] == 0)
        _weekly_page_count[0] += 1
        bm = "weekly_start" if is_first else f"week_{week_num_or_label}"
        if is_first:
            c.bookmarkPage("weekly_start")
            c.addOutlineEntry("Weekly Planning", "weekly_start", level=0)
        page_bg()
        content_w = CW - TAB_W - 4

        if undated or start_date is None:
            week_label = f"WEEK {week_num_or_label:02d}" if isinstance(week_num_or_label, int) else str(week_num_or_label)
            date_label = "Date:  ___ / ___ / ___"
        else:
            end_date   = start_date + timedelta(days=6)
            week_label = f"WEEK {week_num_or_label:02d}"
            date_label = f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"

        # Header
        rect(0, PH - MT - 46, PW - TAB_W - 2, 46 + MT, f=T)
        font("Helvetica-Bold", 20); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 30, week_label)
        font("Helvetica", 10); fill(_blend(WHITE, 0.35))
        c.drawRightString(PW - TAB_W - 10, PH - MT - 30, date_label)
        rect(0, PH - MT - 50, PW - TAB_W - 2, 4, f=A)

        top_y    = PH - MT - 54
        sched_w  = content_w * 0.62
        sidebar_w = content_w - sched_w - 8
        sidebar_x = ML + sched_w + 8
        day_h    = (top_y - MB) / 7
        line_clr = _blend(LIGHT, -0.05)

        # Tier 1: full-width writing area (no sidebar)
        # Tier 2/3: 62% schedule + sidebar
        _use_sidebar = (_design >= 2)
        _actual_sched_w = sched_w if _use_sidebar else content_w

        for di, day_name in enumerate(DAYS_LONG):
            dy_top = top_y - di * day_h
            dy_bot = dy_top - day_h
            is_weekend = di >= 5
            hdr_h = 17 if _design >= 2 else 14

            bg_hdr = TM if is_weekend else T
            rect(ML, dy_top - hdr_h, _actual_sched_w, hdr_h, f=bg_hdr)
            font("Helvetica-Bold", 7.5); fill(WHITE)
            c.drawString(ML + 6, dy_top - 12, day_name.upper())

            if not undated and start_date:
                day_date = start_date + timedelta(days=di)
                font("Helvetica", 7); fill(_blend(WHITE, 0.3))
                c.drawRightString(ML + _actual_sched_w - 6, dy_top - 12,
                                  day_date.strftime("%b %d"))

                # Tier 3: ✨ sticker button in day header — popup menu, no page nav
                if _design == 3 and "sticker_pack" in _extras:
                    _day_lbl_w = c.stringWidth(day_name.upper(), _fn("bold"), 7.5)
                    sk = 12; sk_x = ML + 8 + _day_lbl_w + 4; sk_y = dy_top - hdr_h + 2
                    if sk_x + sk < ML + _actual_sched_w - 50:
                        rect(sk_x, sk_y, sk, sk, f=_blend(A, 0.70), radius=3)
                        font("Helvetica-Bold", 7); fill(WHITE)
                        c.drawCentredString(sk_x + sk / 2, sk_y + 3, "✨")
                        _wk_x = float(ML + 2)
                        _wk_y = float(dy_bot + 2)
                        _wk_w = float(_actual_sched_w - 4)
                        _wk_h = float(day_h - hdr_h - 6)
                        _js_wk = (
                            'var cats=["PRIORITY & TASKS","EVENTS & DATES",'
                            '"WELLNESS & MOOD","SCHOOL & WORK","MOTIVATION"];'
                            'var ci=app.popupMenu(cats);if(ci<0)return;'
                            'var ls=['
                            '["! IMPORTANT","!! URGENT","⏰ DEADLINE","◈ MEETING","✓ TO-DO","🔥 BUSY DAY","📌 REMINDER","→ SUBMIT"],'
                            '["🎂 BIRTHDAY!","📅 APPT","✈ VACAY!","🎉 EVENT","🏆 GOAL MET!","✅ DONE!","🌟 MILESTONE","📝 PLAN"],'
                            '["😍 AMAZING","😊 GOOD","💪 WORKOUT","🙏 GRATEFUL","💧 WATER","😴 SLEPT WELL","🌸 SELF CARE","❤ SELF LOVE"],'
                            '["📚 STUDY","📝 NOTES","⏰ DUE DATE","🎯 FOCUS!","✅ REVIEWED","🚀 LEVEL UP","🏅 ACHIEVEMENT","📈 PROGRESS"],'
                            '["💪 YOU GOT THIS","✨ SHINE","🏆 CRUSHED IT","💫 BELIEVE","🌱 FRESH START","🙌 YES!","💭 DREAM BIG","🎶 GOOD VIBES"]'
                            '];'
                            'var si=app.popupMenu(ls[ci]);if(si<0)return;'
                            'var lbl=ls[ci][si];'
                            'var fc=[["RGB",1.0,0.88,0.85],["RGB",0.85,0.95,1.0],'
                            '["RGB",0.88,0.97,0.88],["RGB",0.90,0.88,1.0],["RGB",1.0,0.97,0.82]];'
                            'var sc=[["RGB",0.85,0.35,0.30],["RGB",0.25,0.55,0.85],'
                            '["RGB",0.25,0.65,0.38],["RGB",0.55,0.35,0.82],["RGB",0.82,0.62,0.15]];'
                            f'var pg=this.pageNum;'
                            f'try{{this.addAnnot({{type:"FreeText",page:pg,'
                            f'rect:[{_wk_x:.1f},{_wk_y:.1f},'
                            f'{_wk_x + _wk_w * 0.5:.1f},{_wk_y + _wk_h:.1f}],'
                            f'contents:lbl,fillColor:fc[ci],strokeColor:sc[ci],'
                            f'textColor:["RGB",0.08,0.08,0.12],textSize:9,alignment:1}});}}'
                            f'catch(e){{app.alert("Works in Acrobat, PDF Expert & Xodo.",1);}}'
                        )
                        if not _js_button(sk_x, sk_y, sk, sk, _js_wk):
                            c.linkAbsolute("Add Sticker", "sticker_picker",
                                           (sk_x, sk_y, sk_x + sk, sk_y + sk))

                # Tier 3: "+" button in day header → Google Calendar add event
                if _design == 3 and cal_integration in ("google", "both"):
                    gcal_date = day_date.strftime("%Y%m%d")
                    gcal_add  = (f"https://calendar.google.com/calendar/r"
                                 f"/eventedit?dates={gcal_date}/{gcal_date}")
                    bs = 12; bx = ML + _actual_sched_w - bs - 22; by = dy_top - hdr_h + 2
                    rect(bx, by, bs, bs, f=A, radius=3)
                    font("Helvetica-Bold", 7); fill(DARK)
                    c.drawCentredString(bx + bs/2, by + 4, "+")
                    c.linkURL(gcal_add, (bx, by, bx + bs, by + bs))

            # Fillable / lined day area
            field_h = day_h - hdr_h - 2
            if field_h > 6:
                if _design == 1:
                    # Tier 1: simple lined rows
                    line_y = dy_top - hdr_h - 10
                    while line_y > dy_bot + 4:
                        hline(ML + 8, ML + _actual_sched_w - 4, line_y, LIGHT, 0.3)
                        line_y -= 10
                else:
                    text_field(ML + 2, dy_bot + 2, _actual_sched_w - 4, field_h,
                               f"week_{week_num_or_label}_day{di}",
                               multiline=True, font_size=8)

            if di < 6:
                hline(ML, ML + _actual_sched_w, dy_bot, LIGHT, 0.4)
            circle(ML + 3, dy_top - hdr_h - (day_h - hdr_h)/2, 2, f=bg_hdr)

        # ── Right sidebar (tier 2 and 3 only) ────────────────────────────────
        if _use_sidebar:
            sb_y = top_y

            def sidebar_section(label, field_h, name_hint):
                nonlocal sb_y
                font("Helvetica-Bold", 7); fill(T)
                c.drawString(sidebar_x, sb_y - 11, label.upper())
                text_field(sidebar_x, sb_y - 11 - field_h, sidebar_w, field_h,
                           name_hint, multiline=True, font_size=8)
                sb_y -= field_h + 18

            sidebar_section("TOP PRIORITIES", 75, f"week_{week_num_or_label}_priorities")
            sidebar_section("NOTES", 90, f"week_{week_num_or_label}_notes")

            # Tier 3: "Open week in Google Calendar" button in sidebar
            if _design == 3 and not undated and start_date and cal_integration in ("google", "both"):
                wk_url = (f"https://calendar.google.com/calendar/r"
                          f"/week/{start_date.year}/{start_date.month}/{start_date.day}")
                rect(sidebar_x, sb_y - 22, sidebar_w, 20, f=A, radius=4)
                font("Helvetica-Bold", 6.5); fill(DARK)
                c.drawCentredString(sidebar_x + sidebar_w/2, sb_y - 22 + 6,
                                    "OPEN WEEK IN GOOGLE CAL")
                c.linkURL(wk_url, (sidebar_x, sb_y - 22, sidebar_x + sidebar_w, sb_y - 2))
                sb_y -= 30

            # Habit mini-tracker
            habit_y = sb_y - 14
            font("Helvetica-Bold", 7); fill(MID)
            c.drawString(sidebar_x, habit_y + 2, "HABITS")
            for hi in range(5):
                hx = sidebar_x + hi * (sidebar_w / 5)
                checkbox_field(hx + 2, habit_y - 14, 10,
                               f"week_{week_num_or_label}_habit{hi}")
                font("Helvetica", 5.5); fill(MID)
                c.drawCentredString(hx + 7, habit_y - 22, str(hi + 1))

            # Water tracker circles
            water_y = habit_y - 34
            font("Helvetica-Bold", 7); fill(MID)
            c.drawString(sidebar_x, water_y, "WATER")
            for wi in range(8):
                wx = sidebar_x + wi * (sidebar_w / 8)
                circle(wx + 5, water_y - 10, 4, s=_blend(T, 0.45), lwidth=0.7)

        draw_nav_tabs("weekly_start")
        page_footer(f"WEEK  {week_num_or_label}")
        c.showPage()

    # ── HABIT TRACKER ────────────────────────────────────────────────────────
    def draw_habit_tracker():
        c.bookmarkPage("habits")
        c.addOutlineEntry("Habit Tracker", "habits", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 34, "HABIT TRACKER")
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        y         = PH - MT - 60
        n_habits  = 12
        n_days    = 31
        label_w   = 105
        cell_w    = (content_w - label_w) / n_days
        hdr_h     = 22
        cell_h    = (y - MB - 40 - hdr_h) / n_habits

        palette = [T, A, TM, AL, _blend(T, 0.35), _blend(A, 0.45),
                   _blend(T, 0.55), _blend(A, 0.65), T, A, TM, AL]

        # Column headers
        for di in range(n_days):
            dx = ML + label_w + di * cell_w
            if di % 7 >= 5:
                rect(dx, MB + 38, cell_w, y - MB - 38 - hdr_h, f=_blend(T, 0.95))
            font("Helvetica-Bold", 6); fill(T if di % 7 >= 5 else MID)
            c.drawCentredString(dx + cell_w/2, y - hdr_h + 7, str(di + 1))

        hline(ML, ML + content_w, y - hdr_h, T, 1.2)

        # Habit rows
        for hi in range(n_habits):
            row_y    = y - hdr_h - (hi+1) * cell_h
            row_clr  = palette[hi]
            row_bg   = BG if hi % 2 == 0 else _blend(LIGHT, 0.5)
            rect(ML, row_y, content_w, cell_h, f=row_bg)

            # Habit name field (clickable label + fillable field)
            pill_h = min(cell_h - 4, 16)
            rect(ML + 2, row_y + (cell_h - pill_h)/2, label_w - 8, pill_h, f=row_clr, radius=3)
            font("Helvetica-Bold", 7); fill(WHITE)
            c.drawString(ML + 7, row_y + (cell_h - pill_h)/2 + 4, f"Habit {hi + 1}")

            # Interactive checkboxes for each day
            for di in range(n_days):
                dx     = ML + label_w + di * cell_w
                cb_s   = min(cell_w - 2, cell_h - 4)
                cb_x   = dx + (cell_w - cb_s) / 2
                cb_y   = row_y + (cell_h - cb_s) / 2
                checkbox_field(cb_x, cb_y, cb_s, f"habit_{hi+1}_day{di+1}")

            hline(ML, ML + content_w, row_y, LIGHT, 0.3)

        # Column header
        rect(ML, y - hdr_h, label_w, hdr_h, f=T)
        font("Helvetica-Bold", 7.5); fill(WHITE)
        c.drawString(ML + 7, y - hdr_h + 7, "HABIT")
        rect(ML, MB + 38, content_w, y - MB - 38, s=_blend(T, 0.4), lwidth=0.8)

        # Month name fillable field at bottom
        font("Helvetica-Bold", 7); fill(MID)
        c.drawString(ML + label_w + 2, MB + 24, "MONTH:")
        text_field(ML + label_w + 50, MB + 18, 90, 16, "habit_month", font_size=9)

        draw_nav_tabs("habits")
        page_footer("HABIT TRACKER")
        c.showPage()

    # ── GOALS PAGE ───────────────────────────────────────────────────────────
    def draw_goals_page():
        c.bookmarkPage("goals")
        c.addOutlineEntry("Goals & Vision", "goals", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 34, "GOALS & VISION")
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        # Decorative circles
        circle(PW - TAB_W - 22, PH - MT - 18, 55, f=_blend(A, 0.88))
        circle(PW - TAB_W + 8,  PH - MT - 78, 30, f=_blend(T, 0.90))

        y = PH - MT - 70

        # Word of the year
        font("Helvetica-Bold", 8); fill(T)
        c.drawString(ML, y, "MY WORD OF THE YEAR")
        y -= 6
        text_field(ML, y - 28, content_w, 28, "word_of_year", font_size=14)
        y -= 42

        # Top 3 goals
        font("Helvetica-Bold", 9); fill(DARK)
        c.drawString(ML, y, "MY TOP 3 GOALS")
        y -= 12
        for gi in range(3):
            box_h = 64
            circle(ML + 14, y - box_h/2 + 10, 13, f=T)
            font("Helvetica-Bold", 12); fill(WHITE)
            c.drawCentredString(ML + 14, y - box_h/2 + 6, str(gi + 1))
            # Three labeled sub-fields
            sub_labels = [("GOAL", 20), ("WHY IT MATTERS", 18), ("FIRST STEP", 18)]
            sy = y - 4
            for slabel, sh in sub_labels:
                font("Helvetica", 6.5); fill(MID)
                c.drawString(ML + 32, sy - 8, slabel)
                text_field(ML + 32, sy - 8 - sh, content_w - 32, sh, f"goal_{gi+1}_{slabel[:4].lower()}", font_size=8)
                sy -= sh + 6
            y -= box_h + 10

        # Intentions / affirmations
        font("Helvetica-Bold", 8); fill(T)
        c.drawString(ML, y, "AFFIRMATIONS & INTENTIONS")
        y -= 10
        remaining_h = y - MB - 4
        if remaining_h > 20:
            text_field(ML, MB + 4, content_w, remaining_h, "affirmations", multiline=True, font_size=9)

        draw_nav_tabs("goals")
        page_footer("GOALS & VISION")
        c.showPage()

    # ── BUDGET PAGE ──────────────────────────────────────────────────────────
    def draw_budget_page():
        c.bookmarkPage("budget")
        c.addOutlineEntry("Budget Tracker", "budget", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 34, "BUDGET TRACKER")
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        y = PH - MT - 70
        col_half = content_w / 2 - 4
        col2_x   = ML + col_half + 8

        for col_x, section_title in [(ML, "INCOME"), (col2_x, "EXPENSES")]:
            font("Helvetica-Bold", 8.5); fill(T)
            c.drawString(col_x, y, section_title)
            sy = y - 14
            for row in range(8):
                font("Helvetica", 7.5); fill(MID)
                c.drawString(col_x, sy - 10, "Item:")
                text_field(col_x + 28, sy - 14, col_half - 72, 14, f"{section_title.lower()}_name_{row}", font_size=8)
                c.drawString(col_x + col_half - 40, sy - 10, "$")
                text_field(col_x + col_half - 32, sy - 14, 30, 14, f"{section_title.lower()}_amt_{row}", font_size=8)
                hline(col_x, col_x + col_half, sy - 16, LIGHT, 0.4)
                sy -= 22

            # Total row
            rect(col_x, sy - 18, col_half, 18, f=_blend(T, 0.9), radius=3)
            font("Helvetica-Bold", 8); fill(T)
            c.drawString(col_x + 4, sy - 12, "TOTAL  $")
            text_field(col_x + 48, sy - 15, col_half - 54, 14, f"{section_title.lower()}_total", font_size=9)
            sy -= 28

        # Net balance
        net_y = y - 8 * 22 - 44
        rect(ML, net_y - 24, content_w, 24, f=T, radius=4)
        font("Helvetica-Bold", 10); fill(WHITE)
        c.drawString(ML + 8, net_y - 16, "NET BALANCE:  $")
        text_field(ML + 100, net_y - 20, 100, 16, "net_balance", font_size=10)

        draw_nav_tabs("budget")
        page_footer("BUDGET TRACKER")
        c.showPage()

    # ── MEAL PLAN PAGE ───────────────────────────────────────────────────────
    def draw_meal_plan_page():
        c.bookmarkPage("meal_plan")
        c.addOutlineEntry("Meal Planning", "meal_plan", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 34, "MEAL PLANNER")
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        y = PH - MT - 62
        meal_labels = ["BREAKFAST","LUNCH","DINNER","SNACKS"]
        meal_colors = [T, A, TM, AL]
        day_col_w   = content_w / 7
        row_h       = (y - MB - 40) / (len(meal_labels) + 1)

        # Day headers
        for di, day in enumerate(["MON","TUE","WED","THU","FRI","SAT","SUN"]):
            dx = ML + di * day_col_w
            bg = TM if di < 5 else T
            rect(dx, y - 20, day_col_w, 20, f=bg)
            font("Helvetica-Bold", 7.5); fill(WHITE)
            c.drawCentredString(dx + day_col_w/2, y - 14, day)

        # Meal rows
        for mi, (meal_label, meal_color) in enumerate(zip(meal_labels, meal_colors)):
            row_y_top = y - 20 - (mi+1) * row_h
            # Row label
            rect(ML - 2, row_y_top - row_h, 38, row_h, f=meal_color, radius=2)
            c.saveState(); c.translate(ML + 17, row_y_top - row_h / 2); c.rotate(90)
            font("Helvetica-Bold", 6.5); fill(WHITE)
            c.drawCentredString(0, -2, meal_label)
            c.restoreState()
            # Day cells
            for di in range(7):
                dx = ML + di * day_col_w
                text_field(dx + 1, row_y_top - row_h + 1, day_col_w - 2, row_h - 2,
                           f"meal_{mi}_{di}", multiline=True, font_size=7)
                if di < 6:
                    vline(dx + day_col_w, row_y_top - row_h, row_y_top, LIGHT, 0.3)
            hline(ML, ML + content_w, row_y_top - row_h, LIGHT, 0.4)

        # Grocery list
        gl_y = y - 20 - (len(meal_labels)+1) * row_h - 8
        font("Helvetica-Bold", 8); fill(T)
        c.drawString(ML, gl_y, "GROCERY LIST")
        remaining = gl_y - MB - 4
        if remaining > 15:
            text_field(ML, MB + 4, content_w, remaining - 10, "grocery_list", multiline=True, font_size=8)

        draw_nav_tabs("meal_plan")
        page_footer("MEAL PLANNER")
        c.showPage()

    # ── TABLE OF CONTENTS (hyperlinked) ─────────────────────────────────────
    def draw_index_page():
        c.bookmarkPage("index")
        c.addOutlineEntry("Index", "index", level=0)
        page_bg()
        content_w = CW - TAB_W - 4

        # Header bar
        rect(ML, PH - MT - 44, content_w, 44, f=T)
        rect(ML, PH - MT - 44, 4, 44, f=A)
        font("Helvetica-Bold", 18); fill(WHITE)
        c.drawString(ML + 14, PH - MT - 28, "TABLE OF CONTENTS")
        font("Helvetica", 7.5); fill(_blend(WHITE, 0.45))
        c.drawRightString(ML + content_w, PH - MT - 28, "tap any item to jump there ›")

        # ── Build groups — only for sections that are actually in this planner ─
        index_groups: list[tuple[str, list]] = []

        if "monthly" in sections or "weekly" in sections:
            index_groups.append(("Year at a Glance", [("Calendar Overview", "yearly")]))

        if "monthly" in sections:
            index_groups.append(("Monthly Pages",
                                  [(m, f"month_{m[:3].lower()}") for m in MONTHS]))

        if "weekly" in sections:
            index_groups.append(("Weekly Pages", [("Weekly Planner", "weekly_start")]))

        if "habit_tracker" in sections:
            index_groups.append(("Habit Tracker", [("Habit Tracker", "habits")]))

        if "goals" in sections:
            index_groups.append(("Goals & Vision",
                                  [("Goals & Vision Board", "goals")]))

        if "budget" in sections:
            index_groups.append(("Budget & Finance", [
                ("Budget Tracker",    "budget"),
                ("Spending Overview", "budget"),
                ("Savings Tracker",   "budget"),
            ]))

        if "meal_plan" in sections:
            index_groups.append(("Meal Planning", [
                ("Weekly Meal Planner", "meal_plan"),
                ("Grocery List",        "meal_plan"),
            ]))

        if "monthly_review" in sections:
            index_groups.append(("Monthly Review",
                                  [("Monthly Review", "monthly_review_0")]))

        if "month_at_a_glance" in sections:
            index_groups.append(("Month at a Glance",
                                  [("Month at a Glance", "month_glance_0")]))

        if "notes" in sections:
            index_groups.append(("Notes & Journal", [
                ("Dot-Grid Notes", "notes"),
                ("Free Notes",     "notes"),
            ]))

        # ── Layout constants ──────────────────────────────────────────────────
        col_w   = content_w / 2 - 6
        col2_x  = ML + col_w + 12
        y       = PH - MT - 62
        col     = 0
        xs      = [ML, col2_x]
        GHH     = 18    # group header height
        ROW_H   = 14    # entry row height
        ROW_PAD = 3     # row top padding

        for group_name, entries in index_groups:
            needed = GHH + len(entries) * ROW_H + 10
            if y - needed < MB + 20:
                if col == 0:
                    col = 1; y = PH - MT - 62
                else:
                    break
            x = xs[col]

            # Group header pill
            rect(x, y - GHH + 4, col_w, GHH, f=_blend(T, 0.87), radius=3)
            font("Helvetica-Bold", 7.5); fill(T)
            c.drawString(x + 8, y - GHH + 8, group_name.upper())
            y -= GHH + 2

            for ei, (entry_label, entry_bm) in enumerate(entries):
                if y < MB + 20:
                    if col == 0:
                        col = 1; y = PH - MT - 62 - GHH - 2
                    else:
                        break
                    x = xs[col]

                # Alternating row background
                row_fill = _blend(T, 0.97) if ei % 2 == 0 else _blend(T, 0.93)
                rect(x, y - ROW_H + ROW_PAD, col_w, ROW_H, f=row_fill)

                # Entry text — theme color signals it is clickable
                font("Helvetica", 8); fill(T)
                c.drawString(x + 10, y - ROW_H + ROW_PAD + 4, entry_label)

                # Right-side chevron
                font("Helvetica-Bold", 9); fill(_blend(T, 0.50))
                c.drawRightString(x + col_w - 6, y - ROW_H + ROW_PAD + 3, "›")

                # Clickable link covering the entire row
                c.linkAbsolute(entry_label, entry_bm,
                               (x, y - ROW_H + ROW_PAD,
                                x + col_w, y + ROW_PAD))
                y -= ROW_H

            y -= 8  # gap between groups

        page_footer("Table of Contents")
        draw_nav_tabs("index")
        c.showPage()

    # ── MONTHLY REVIEW PAGE ──────────────────────────────────────────────────
    def draw_monthly_review(month_idx=0):
        c.bookmarkPage(f"monthly_review_{month_idx}")
        page_bg()
        content_w = CW - TAB_W - 4
        month_name = MONTHS[month_idx % 12] if not undated else ""
        hdr_label = f"{month_name.upper()} REVIEW" if month_name else "MONTHLY REVIEW"

        rect(ML, PH - MT - 44, content_w, 44, f=T)
        rect(ML, PH - MT - 44, 4, 44, f=A)
        font("Helvetica-Bold", 16); fill(WHITE)
        c.drawString(ML + 14, PH - MT - 28, hdr_label)
        font("Helvetica", 8); fill(_blend(WHITE, 0.35))
        c.drawRightString(ML + content_w, PH - MT - 28, "Reflect · Review · Reset")

        y = PH - MT - 60
        col_gap = 6
        half_w = (content_w - col_gap) / 2

        def review_field(label, field_h, name, x=ML, w=None):
            nonlocal y
            fw = w or content_w
            font("Helvetica-Bold", 7); fill(T)
            c.drawString(x, y, label.upper())
            hline(x, x + fw, y - 2, A, 0.8)
            y -= 4
            text_field(x, y - field_h, fw, field_h, name, multiline=True, font_size=8)
            y -= field_h + 14

        review_field("Monthly Memories", 52, f"rev_{month_idx}_memories")
        review_field("Gratitude & Highlights", 44, f"rev_{month_idx}_gratitude")
        review_field("Challenges & Lessons Learned", 44, f"rev_{month_idx}_challenges")

        # Two-column row
        save_y = y
        review_field("What Went Well", 60, f"rev_{month_idx}_well", ML, half_w)
        col2_y = save_y
        y = col2_y
        review_field("To Remove / Change", 60, f"rev_{month_idx}_remove", ML + half_w + col_gap, half_w)

        review_field("Next Month — Action Items", 48, f"rev_{month_idx}_actions")

        # Habit mini-circles row
        font("Helvetica-Bold", 7); fill(MID)
        c.drawString(ML, y + 2, "HABIT CHECK")
        for hi in range(12):
            cx = ML + 14 + hi * (content_w - 14) / 12
            circle(cx, y - 8, 6, s=_blend(T, 0.4), f=BG, lwidth=0.8)
            font("Helvetica", 5.5); fill(MID)
            c.drawCentredString(cx, y - 10, str(hi + 1))

        page_footer(hdr_label)
        draw_nav_tabs(f"monthly_review_{month_idx}")
        c.showPage()

    # ── MONTH AT A GLANCE PAGE ────────────────────────────────────────────────
    def draw_month_at_a_glance(month_idx=0):
        c.bookmarkPage(f"month_glance_{month_idx}")
        page_bg()
        content_w = CW - TAB_W - 4
        month_name = MONTHS[month_idx % 12] if not undated else ""
        hdr_label = f"{month_name.upper()} AT A GLANCE" if month_name else "MONTH AT A GLANCE"

        rect(ML, PH - MT - 44, content_w, 44, f=A)
        rect(ML, PH - MT - 44, 4, 44, f=T)
        font("Helvetica-Bold", 15); fill(WHITE)
        c.drawString(ML + 14, PH - MT - 28, hdr_label)

        y = PH - MT - 60
        left_w = content_w * 0.48
        right_w = content_w - left_w - 8
        right_x = ML + left_w + 8

        def glance_field(label, field_h, name, x=ML, w=None):
            nonlocal y
            fw = w or left_w
            font("Helvetica-Bold", 7); fill(T)
            c.drawString(x, y, label.upper())
            hline(x, x + fw, y - 2, _blend(T, 0.4), 0.6)
            y -= 4
            text_field(x, y - field_h, fw, field_h, name, multiline=True, font_size=8)
            y -= field_h + 12

        glance_field("Trends This Month", 40, f"gl_{month_idx}_trends")
        glance_field("Goals", 44, f"gl_{month_idx}_goals")
        glance_field("Top Priorities", 40, f"gl_{month_idx}_priorities")
        glance_field("Achievements", 40, f"gl_{month_idx}_achieve")

        # Right column
        ry = PH - MT - 60
        for label, fh, name in [
            ("Important Days", 72, f"gl_{month_idx}_days"),
            ("To-Do List", 60, f"gl_{month_idx}_todo"),
            ("Notes", 52, f"gl_{month_idx}_notes"),
        ]:
            font("Helvetica-Bold", 7); fill(T)
            c.drawString(right_x, ry, label.upper())
            hline(right_x, right_x + right_w, ry - 2, _blend(T, 0.4), 0.6)
            ry -= 4
            text_field(right_x, ry - fh, right_w, fh, name, multiline=True, font_size=8)
            ry -= fh + 12

        page_footer(hdr_label)
        draw_nav_tabs(f"month_glance_{month_idx}")
        c.showPage()

    # ── NOTES PAGE ───────────────────────────────────────────────────────────
    def draw_notes_page(page_num=1):
        bm = "notes" if page_num == 1 else f"notes_{page_num}"
        if page_num == 1:
            c.bookmarkPage("notes")
            c.addOutlineEntry("Notes", "notes", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(ML, PH - MT - 40, content_w, 40, f=_blend(T, 0.90))
        rect(ML, PH - MT - 40, 5, 40, f=T)
        font("Helvetica-Bold", 18); fill(T)
        c.drawString(ML + 16, PH - MT - 26, "NOTES")
        font("Helvetica", 8); fill(MID)
        c.drawRightString(ML + content_w, PH - MT - 26, f"{page_num}")

        # Dot grid (iconic planner aesthetic)
        dot_sp = 14; dot_r = 0.85
        sx = ML + dot_sp; sy = PH - MT - 58; ey = MB + 22
        x = sx
        while x <= ML + content_w - dot_sp:
            y = sy
            while y >= ey:
                circle(x, y, dot_r, f=LIGHT)
                y -= dot_sp
            x += dot_sp

        rect(ML, ey, 2, sy - ey + dot_sp, f=_blend(T, 0.72))

        # Large fillable text area over the dot grid (transparent fill)
        text_field(ML + dot_sp, ey, content_w - dot_sp, sy - ey, f"notes_{page_num}", multiline=True, font_size=10)

        draw_nav_tabs("notes")
        page_footer(f"NOTES  {page_num}")
        c.showPage()

    # ── COLOR SCHEME SELECTOR PAGE ───────────────────────────────────────────
    def draw_color_selector_page():
        c.bookmarkPage("color_themes")
        c.addOutlineEntry("Color Themes", "color_themes", level=0)
        page_bg()
        content_w = CW - TAB_W - 4

        rect(0, PH - MT - 48, PW - TAB_W - 2, 48 + MT, f=T)
        rect(0, PH - MT - 48, 5, 48 + MT, f=A)
        font("Helvetica-Bold", 18); fill(WHITE)
        c.drawString(ML + 14, PH - MT - 30, "COLOR THEMES")
        font("Helvetica", 7.5); fill(_blend(WHITE, 0.45))
        c.drawRightString(PW - TAB_W - 10, PH - MT - 30,
                          "This planner is available in all themes shown below")
        rect(0, PH - MT - 52, PW - TAB_W - 2, 4, f=A)

        note_y = PH - MT - 62
        font("Helvetica", 7); fill(MID)
        c.drawCentredString((PW - TAB_W) / 2, note_y,
                            "Order any color theme by leaving your preference at checkout · OnBrandCraftz")

        # Grid: 5 columns
        cols = 5; pad = 7
        sw = (content_w - pad * (cols + 1)) / cols
        sh = sw * 1.25
        sx0 = ML + pad
        sy0 = note_y - 14

        schemes_list = list(COLOR_SCHEMES.items())
        for i, (key, sch) in enumerate(schemes_list):
            ci = i % cols; ri = i // cols
            x = sx0 + ci * (sw + pad)
            y_top = sy0 - ri * (sh + pad + 12)
            y_bot = y_top - sh

            # Mini planner-cover preview
            split = sh * 0.40
            rect(x, y_bot, sw, split, f=sch["bg"])
            rect(x, y_bot + split, sw, sh - split, f=sch["theme"])
            rect(x, y_bot + split - 1.5, sw, 2.5, f=sch["accent"])
            # Mini title lines
            rect(x + sw*0.15, y_bot + sh*0.68, sw*0.70, 2, f=_blend(sch["theme"], 0.55))
            rect(x + sw*0.25, y_bot + sh*0.60, sw*0.50, 1.5, f=_blend(sch["theme"], 0.45))
            # Border (thicker if current scheme)
            is_cur = (key == scheme_key)
            rect(x, y_bot, sw, sh, s=T if is_cur else _blend(LIGHT, -0.05),
                 lwidth=1.4 if is_cur else 0.3)
            # Label
            font("Helvetica-Bold" if is_cur else "Helvetica", 5.5)
            fill(T if is_cur else DARK)
            c.drawCentredString(x + sw/2, y_bot - 7, sch["label"])

        page_footer("Color Themes")
        draw_nav_tabs()
        c.showPage()

    # ── VISION BOARD PAGE ────────────────────────────────────────────────────
    def draw_vision_board_page():
        c.bookmarkPage("vision_board")
        c.addOutlineEntry("Vision Board", "vision_board", level=0)
        page_bg()
        content_w = CW - TAB_W - 4

        rect(0, PH - MT - 48, PW - TAB_W - 2, 48 + MT, f=T)
        rect(0, PH - MT - 48, 5, 48 + MT, f=A)
        font("Helvetica-BoldOblique", 20); fill(WHITE)
        c.drawString(ML + 14, PH - MT - 30, "VISION BOARD")
        font("Helvetica", 7.5); fill(_blend(WHITE, 0.40))
        c.drawRightString(PW - TAB_W - 10, PH - MT - 30, "dream it · plan it · live it")
        rect(0, PH - MT - 52, PW - TAB_W - 2, 4, f=A)

        top_y = PH - MT - 60
        # Intention banner
        font("Helvetica-BoldOblique", 8); fill(T)
        c.drawCentredString(ML + content_w/2, top_y - 4, "MY INTENTION FOR THIS YEAR")
        text_field(ML, top_y - 28, content_w, 18, "vision_intention",
                   multiline=False, font_size=9)

        # Four decorative photo frames in 2×2 grid
        gutter = 10; top_frames_y = top_y - 38
        fw = (content_w - gutter) / 2
        fh = fw * 0.72
        frame_defs = [
            (ML,        top_frames_y - fh, fw, fh, "DREAM"),
            (ML+fw+gutter, top_frames_y - fh, fw, fh, "ACHIEVE"),
            (ML,        top_frames_y - fh*2 - gutter, fw, fh, "BECOME"),
            (ML+fw+gutter, top_frames_y - fh*2 - gutter, fw, fh, "ATTRACT"),
        ]
        for fx, fy, fw2, fh2, lbl in frame_defs:
            rect(fx, fy, fw2, fh2, f=_blend(T, 0.94))
            rect(fx, fy, fw2, fh2, s=_blend(T, 0.35), lwidth=0.7)
            rect(fx+4, fy+4, fw2-8, fh2-8, s=_blend(A, 0.50), lwidth=0.4)
            font("Helvetica-BoldOblique", 9); fill(_blend(T, 0.45))
            c.drawCentredString(fx + fw2/2, fy + fh2/2 - 2, lbl)
            font("Helvetica", 6); fill(_blend(T, 0.55))
            c.drawCentredString(fx + fw2/2, fy + fh2/2 - 13, "Add photo · sketch · collage here")

        # Affirmation field
        aff_y = top_frames_y - fh*2 - gutter - 14
        if aff_y > MB + 30:
            font("Helvetica-Bold", 7); fill(T)
            c.drawString(ML, aff_y, "MY DAILY AFFIRMATION")
            text_field(ML, aff_y - 22, content_w, 16, "vision_affirmation",
                       multiline=False, font_size=9)

        page_footer("VISION BOARD")
        draw_nav_tabs()
        c.showPage()

    # ── MOOD TRACKER PAGE ────────────────────────────────────────────────────
    def draw_mood_tracker_page():
        c.bookmarkPage("mood_tracker")
        c.addOutlineEntry("Mood Tracker", "mood_tracker", level=0)
        page_bg()
        content_w = CW - TAB_W - 4

        rect(0, PH - MT - 48, PW - TAB_W - 2, 48 + MT, f=T)
        rect(0, PH - MT - 48, 5, 48 + MT, f=A)
        font("Helvetica-Bold", 18); fill(WHITE)
        c.drawString(ML + 14, PH - MT - 30, "ANNUAL MOOD TRACKER")
        rect(0, PH - MT - 52, PW - TAB_W - 2, 4, f=A)

        # Mood legend
        moods = [
            ("AMAZING",  A),
            ("GOOD",     _blend(A, 0.55)),
            ("OKAY",     _blend(T, 0.55)),
            ("LOW",      _blend(T, 0.35)),
            ("ROUGH",    (0.72, 0.40, 0.40)),
        ]
        leg_y = PH - MT - 62; lx = ML + 4
        font("Helvetica-Bold", 6.5); fill(DARK)
        c.drawString(lx, leg_y, "COLOR KEY:")
        lx += 50
        for m_label, m_color in moods:
            circle(lx + 5, leg_y + 2, 5, f=m_color)
            font("Helvetica", 6); fill(DARK)
            c.drawString(lx + 13, leg_y - 1, m_label)
            lx += 13 + c.stringWidth(m_label, "Helvetica", 6) + 8

        # 12-month circle grid
        row_h   = (PH - MT - 74 - MB - 16) / 12
        circ_r  = min(5.5, (row_h - 4) / 2)
        sp      = (content_w - 38) / 31   # spacing per day
        top_y2  = PH - MT - 74

        for mi, mname in enumerate(MONTHS):
            ry = top_y2 - mi * row_h - row_h / 2
            font("Helvetica-Bold", 6.5); fill(T)
            c.drawString(ML + 2, ry - 2, mname[:3].upper())
            days_in = (cal_mod.monthrange(planner_year, mi+1)[1]
                       if not undated else 31)
            for di in range(days_in):
                dx = ML + 38 + di * sp + sp/2
                circle(dx, ry, circ_r, s=_blend(T, 0.38), lwidth=0.4)
                font("Helvetica", 4.5); fill(_blend(T, 0.55))
                c.drawCentredString(dx, ry - 2, str(di + 1))

        page_footer("ANNUAL MOOD TRACKER")
        draw_nav_tabs()
        c.showPage()

    # ── STICKER PICKER PAGE (interactive, linked from every calendar page) ──────
    import math as _math

    # ── Pastel kawaii palette ─────────────────────────────────────────────────
    _STK_G  = (0.20, 0.72, 0.40)   # mint green
    _STK_Y  = (0.95, 0.78, 0.15)   # sunshine yellow
    _STK_R  = (0.95, 0.35, 0.45)   # coral pink-red
    _STK_P  = (0.68, 0.45, 0.92)   # soft violet
    _STK_O  = (0.98, 0.58, 0.28)   # warm peach-orange
    _STK_B  = (0.38, 0.72, 0.95)   # sky blue
    _STK_PK = (0.98, 0.50, 0.72)   # bubblegum pink
    _STK_TL = (0.20, 0.80, 0.78)   # teal mint
    _STK_GD = (0.88, 0.68, 0.18)   # gold
    _STK_LV = (0.75, 0.58, 0.95)   # lavender

    # shape key: "star" | "heart" | "circle" | "pill" | "speech"
    _STICKER_CATEGORIES = [
        ("PRIORITY & TASKS", _STK_R, [
            ("IMPORTANT",   _STK_R,   "star"),   ("URGENT",    _STK_O,   "speech"),
            ("DEADLINE",    _STK_O,   "circle"),  ("MEETING",   _STK_B,   "pill"),
            ("TO-DO",       _STK_B,   "pill"),    ("ERRANDS",   _STK_G,   "pill"),
            ("BUSY DAY",    _STK_O,   "star"),    ("FOCUS",     T,        "circle"),
            ("CALL",        _STK_TL,  "pill"),    ("EMAIL",     _STK_B,   "pill"),
            ("TO BUY",      _STK_G,   "pill"),    ("PAY BILL",  _STK_R,   "speech"),
            ("REMINDER",    _STK_O,   "circle"),  ("REVIEW",    T,        "pill"),
            ("SUBMIT",      _STK_G,   "pill"),    ("BLOCKED",   _STK_R,   "pill"),
        ]),
        ("EVENTS & DATES", _STK_Y, [
            ("BIRTHDAY!",   _STK_PK,  "star"),    ("APPT",      _STK_B,   "pill"),
            ("VACAY!",      _STK_B,   "speech"),  ("ANNIVERSARY",_STK_PK, "heart"),
            ("MEMORIES",    _STK_P,   "circle"),  ("GIFT DUE",  _STK_PK,  "pill"),
            ("EVENT",       T,        "star"),     ("FAMILY",    _STK_Y,   "heart"),
            ("HOLIDAY",     _STK_Y,   "star"),    ("GOAL MET!", _STK_G,   "speech"),
            ("DONE!",       _STK_G,   "circle"),  ("WIN!",      _STK_Y,   "star"),
            ("PLAN",        _STK_B,   "pill"),    ("MILESTONE", _STK_GD,  "star"),
            ("BILL DUE",    _STK_R,   "pill"),    ("NEW MOON",  _STK_LV,  "circle"),
        ]),
        ("WELLNESS & MOOD", _STK_P, [
            ("AMAZING",     _STK_Y,   "star"),    ("GOOD",      _STK_G,   "circle"),
            ("OKAY",        _STK_B,   "circle"),  ("LOW",       _STK_LV,  "heart"),
            ("WATER",       _STK_B,   "circle"),  ("SLEPT WELL",_STK_LV,  "circle"),
            ("WORKOUT",     _STK_G,   "speech"),  ("GRATEFUL",  _STK_Y,   "heart"),
            ("CALM",        _STK_TL,  "circle"),  ("HIGH ENERGY",_STK_O,  "star"),
            ("MEALS",       _STK_G,   "pill"),    ("SELF CARE", _STK_PK,  "heart"),
            ("MEDS",        _STK_B,   "pill"),    ("SELF LOVE", _STK_PK,  "heart"),
            ("SUNSHINE",    _STK_Y,   "star"),    ("MINDFUL",   _STK_TL,  "circle"),
        ]),
        ("SCHOOL & WORK", _STK_B, [
            ("STUDY",       _STK_B,   "speech"),  ("NOTES",     T,        "pill"),
            ("TEST DAY",    _STK_R,   "circle"),  ("SUBMIT",    _STK_G,   "pill"),
            ("DUE DATE",    _STK_R,   "star"),    ("REVIEWED",  _STK_G,   "circle"),
            ("PRESENT",     _STK_O,   "speech"),  ("ONLINE",    _STK_B,   "pill"),
            ("FOCUS!",      T,        "star"),     ("NO PHONE",  _STK_R,   "circle"),
            ("READ",        _STK_P,   "pill"),    ("WRITE",     T,        "pill"),
            ("PROGRESS",    _STK_G,   "speech"),  ("GREAT WORK",_STK_Y,   "star"),
            ("ACHIEVEMENT", _STK_GD,  "star"),    ("LEVEL UP",  _STK_O,   "speech"),
        ]),
        ("MOTIVATION", _STK_GD, [
            ("YOU GOT THIS",_STK_O,   "speech"),  ("STRONG",    _STK_R,   "star"),
            ("SHINE",       _STK_Y,   "star"),    ("ON FIRE",   _STK_O,   "star"),
            ("CRUSHED IT",  _STK_G,   "speech"),  ("GROWTH",    _STK_G,   "circle"),
            ("BELIEVE",     _STK_P,   "heart"),   ("MAGIC DAY", _STK_LV,  "star"),
            ("FRESH START", _STK_TL,  "circle"),  ("GO WITH IT",_STK_B,   "speech"),
            ("NEW CHAPTER", _STK_P,   "pill"),    ("YES!",      _STK_Y,   "circle"),
            ("GLOW UP",     _STK_PK,  "star"),    ("DREAM BIG", _STK_LV,  "heart"),
            ("BE KIND",     _STK_PK,  "heart"),   ("GOOD VIBES",_STK_Y,   "speech"),
        ]),
        ("FUNCTIONAL PLANNING", T, [
            ("THIS WEEK",   T,        "pill"),    ("MONTHLY",   A,        "pill"),
            ("HABIT TRACK", _STK_G,   "pill"),    ("DON'T FORGET",_STK_O, "speech"),
            ("TOP 3",       _STK_GD,  "star"),    ("BRAIN DUMP",_STK_P,   "pill"),
            ("CHECKLIST",   _STK_B,   "circle"),  ("NEXT STEPS",_STK_TL,  "pill"),
            ("IN PROGRESS", _STK_O,   "pill"),    ("COMPLETE ✓",_STK_G,   "pill"),
            ("NO SPEND",    _STK_TL,  "circle"),  ("PAYDAY! 🎉",_STK_GD,  "star"),
            ("NOTES",       MID,      "pill"),    ("ACTION",    T,        "speech"),
            ("PRIORITY!",   _STK_R,   "star"),    ("TODAY",     A,        "circle"),
        ]),
        ("WIDGET TRACKERS", _STK_TL, [
            ("MOOD 😊",     _STK_Y,   "star"),    ("WATER 💧",  _STK_B,   "circle"),
            ("SLEEP 🌙",    _STK_LV,  "circle"),  ("ENERGY ⚡", _STK_O,   "star"),
            ("STEPS 👟",    _STK_G,   "pill"),    ("WORKOUT ✓", _STK_TL,  "circle"),
            ("GRATEFUL ♡", _STK_PK,  "heart"),   ("STREAK 🔥", _STK_O,   "star"),
            ("FOCUS 🍅",    _STK_R,   "circle"),  ("WINS 🏆",   _STK_GD,  "star"),
            ("MEDS 💊",     _STK_B,   "pill"),    ("MEALS 🥗",  _STK_G,   "circle"),
            ("WEIGHT",      _STK_TL,  "circle"),  ("JOURNAL",   _STK_LV,  "pill"),
            ("SELF CARE",   _STK_PK,  "heart"),   ("REFLECT",   _STK_P,   "pill"),
        ]),
    ]

    # ── Kawaii drawing primitives ─────────────────────────────────────────────
    def _kawaii_face(face_cx, face_cy, size):
        """Dot eyes, curved smile, pink blush cheeks."""
        eye_r = max(1.2, size * 0.07)
        # Eyes
        c.setFillColorRGB(0.08, 0.08, 0.12); c.setLineWidth(0)
        c.circle(face_cx - size * 0.16, face_cy + size * 0.06, eye_r, fill=1, stroke=0)
        c.circle(face_cx + size * 0.16, face_cy + size * 0.06, eye_r, fill=1, stroke=0)
        # Blush ovals
        c.saveState()
        c.setFillColorRGB(0.98, 0.68, 0.74); c.setFillAlpha(0.60)
        bx = size * 0.22; by = size * 0.06; bw = size * 0.13; bh = size * 0.07
        c.ellipse(face_cx - bx - bw, face_cy - by - bh,
                  face_cx - bx + bw, face_cy - by + bh, fill=1, stroke=0)
        c.ellipse(face_cx + bx - bw, face_cy - by - bh,
                  face_cx + bx + bw, face_cy - by + bh, fill=1, stroke=0)
        c.setFillAlpha(1.0); c.restoreState()
        # Smile arc
        c.setStrokeColorRGB(0.08, 0.08, 0.12)
        c.setLineWidth(max(0.5, size * 0.055)); c.setLineCap(1)
        p = c.beginPath()
        p.moveTo(face_cx - size * 0.13, face_cy - size * 0.01)
        p.curveTo(face_cx - size * 0.07, face_cy - size * 0.15,
                  face_cx + size * 0.07, face_cy - size * 0.15,
                  face_cx + size * 0.13, face_cy - size * 0.01)
        c.drawPath(p, fill=0, stroke=1); c.setLineCap(0)

    def _star_pts(cx, cy, r_out, r_in, n=5):
        pts = []
        for i in range(n * 2):
            r = r_out if i % 2 == 0 else r_in
            a = _math.pi * (i / n) - _math.pi / 2
            pts.append((cx + r * _math.cos(a), cy + r * _math.sin(a)))
        return pts

    def _draw_shape_path(shape, cx, cy, r, outline_extra=0):
        """Draw filled+stroked shape. Returns (approx face_cx, face_cy, face_size)."""
        re = r + outline_extra
        if shape == "star":
            p = c.beginPath()
            for i, (px, py) in enumerate(_star_pts(cx, cy, re, re * 0.44)):
                p.moveTo(px, py) if i == 0 else p.lineTo(px, py)
            p.close(); c.drawPath(p, fill=1, stroke=1 if outline_extra == 0 else 0)
            return cx, cy + r * 0.08, r * 0.52
        elif shape == "heart":
            s = re * 0.58
            p = c.beginPath()
            p.moveTo(cx, cy - s)
            p.curveTo(cx - s * 1.9, cy - s * 0.2, cx - s * 1.9, cy + s * 1.0, cx, cy + s * 0.6)
            p.curveTo(cx + s * 1.9, cy + s * 1.0, cx + s * 1.9, cy - s * 0.2, cx, cy - s)
            p.close(); c.drawPath(p, fill=1, stroke=1 if outline_extra == 0 else 0)
            return cx, cy + s * 0.1, s * 0.80
        elif shape == "speech":
            # Rounded rect + small triangle at bottom-left
            rr = re * 0.22
            p = c.beginPath()
            p.moveTo(cx - re + rr, cy + re)
            p.lineTo(cx + re - rr, cy + re)
            p.curveTo(cx + re, cy + re, cx + re, cy + re, cx + re, cy + re - rr)
            p.lineTo(cx + re, cy - re * 0.4 + rr)
            p.curveTo(cx + re, cy - re * 0.4, cx + re, cy - re * 0.4, cx + re - rr, cy - re * 0.4)
            p.lineTo(cx - re * 0.1, cy - re * 0.4)
            p.lineTo(cx - re * 0.35, cy - re * 0.8)  # tail point
            p.lineTo(cx - re * 0.55, cy - re * 0.4)
            p.lineTo(cx - re + rr, cy - re * 0.4)
            p.curveTo(cx - re, cy - re * 0.4, cx - re, cy - re * 0.4, cx - re, cy - re * 0.4 + rr)
            p.lineTo(cx - re, cy + re - rr)
            p.curveTo(cx - re, cy + re, cx - re, cy + re, cx - re + rr, cy + re)
            p.close(); c.drawPath(p, fill=1, stroke=1 if outline_extra == 0 else 0)
            return cx, cy + re * 0.15, re * 0.62
        else:  # circle
            c.circle(cx, cy, re, fill=1, stroke=1 if outline_extra == 0 else 0)
            return cx, cy, re * 0.72

    def _draw_kawaii_sticker(sx, sy, sw, sh, lbl, col, shape="pill",
                              sticker_page_mode=False):
        """Kawaii sticker: white outline → pastel fill → black border → face → label → JS."""
        cx = sx + sw / 2
        cy = sy + sh * 0.54   # center shifted up a bit to leave room for label
        r = min(sw, sh * 0.88) * 0.44

        is_pill = shape == "pill"

        if is_pill:
            # White outline box
            c.setFillColorRGB(1, 1, 1); c.setLineWidth(0)
            c.roundRect(sx - 3, sy - 1, sw + 6, sh + 4, (sh + 4) * 0.28, fill=1, stroke=0)
            # Pastel fill + dark outline
            c.setFillColorRGB(*_blend(col, 0.80))
            c.setStrokeColorRGB(*_blend(col, 0.15))
            c.setLineWidth(1.2)
            c.roundRect(sx, sy, sw, sh, sh * 0.28, fill=1, stroke=1)
            # Bold label text centered
            fs = min(7.5, sw / max(1, len(lbl)) * 1.6)
            font("Helvetica-Bold", fs); fill(_blend(col, 0.08))
            c.drawCentredString(cx, sy + sh * 0.34, lbl)
        else:
            # White outline shape (extra=3)
            c.setFillColorRGB(1, 1, 1); c.setLineWidth(0)
            _draw_shape_path(shape, cx, cy, r + 3, outline_extra=3)
            # Colored fill shape
            c.setFillColorRGB(*_blend(col, 0.78))
            c.setStrokeColorRGB(*_blend(col, 0.18))
            c.setLineWidth(1.0)
            fce_cx, fce_cy, fce_sz = _draw_shape_path(shape, cx, cy, r)
            # Kawaii face (skip for very small stickers)
            if r > 9:
                _kawaii_face(fce_cx, fce_cy, fce_sz)
            # Label below shape
            label_y = sy + 3
            fs = min(6.5, sw / max(1, len(lbl)) * 1.5)
            font("Helvetica-Bold", fs); fill(_blend(col, 0.10))
            c.drawCentredString(cx, label_y, lbl)

        # JS overlay — popup → place FreeText annotation on page
        _r, _g, _b = col[0], col[1], col[2]
        _lr = min(1.0, _r * 0.45 + 0.55)
        _lg = min(1.0, _g * 0.45 + 0.55)
        _lb = min(1.0, _b * 0.45 + 0.55)
        _safe = lbl.replace('"', "'")

        if sticker_page_mode:
            _js = (
                f'var pg=parseInt(this.getField("{_stk_pg}").value);'
                f'if(isNaN(pg)||pg<0){{'
                f'app.alert("Tap the \\u2728 button on any planner page first!",3);return;}}'
                f'var cx=parseFloat(this.getField("{_stk_x}").value);'
                f'var cy=parseFloat(this.getField("{_stk_y}").value);'
                f'var cw=parseFloat(this.getField("{_stk_w}").value);'
                f'var ch=parseFloat(this.getField("{_stk_h}").value);'
                f'try{{this.addAnnot({{type:"FreeText",page:pg,'
                f'rect:[cx,cy,cx+cw,cy+ch],'
                f'contents:"{_safe}",'
                f'fillColor:["RGB",{_lr:.3f},{_lg:.3f},{_lb:.3f}],'
                f'strokeColor:["RGB",{_r:.3f},{_g:.3f},{_b:.3f}],'
                f'textColor:["RGB",{_r*0.25:.3f},{_g*0.25:.3f},{_b*0.25:.3f}],'
                f'textSize:10,alignment:1}});'
                f'this.getField("{_stk_pg}").value="-1";'
                f'this.pageNum=pg;}}catch(e){{}}'
            )
        else:
            _js = (
                f'var pg=this.pageNum;'
                f'var ph=this.getPageHeight(pg);var pw=this.getPageWidth(pg);'
                f'try{{this.addAnnot({{type:"FreeText",page:pg,'
                f'rect:[pw*0.33,ph*0.44,pw*0.67,ph*0.58],'
                f'contents:"{_safe}",'
                f'fillColor:["RGB",{_lr:.3f},{_lg:.3f},{_lb:.3f}],'
                f'strokeColor:["RGB",{_r:.3f},{_g:.3f},{_b:.3f}],'
                f'textColor:["RGB",{_r*0.25:.3f},{_g*0.25:.3f},{_b*0.25:.3f}],'
                f'textSize:11,alignment:1}});'
                f'app.alert("\\u2728 Sticker added! Drag it anywhere.",1);'
                f'}}catch(e){{app.alert("Works in Acrobat Reader, PDF Expert & Xodo.",1);}}'
            )
        if not _js_button(sx, sy, sw, sh + 4, _js):
            c.linkAbsolute(f"Sticker: {lbl}", "sticker_picker",
                           (sx, sy, sx + sw, sy + sh))

    # ── DALL-E sticker sheet image generation ────────────────────────────────
    # Prepended to every sheet prompt for style + layout consistency
    _STICKER_STYLE_ANCHOR = (
        "STYLE DNA — apply to every sticker on this sheet: "
        "Premium kawaii flat illustration clipart. "
        "Each sticker has a THICK solid black outline 4-5px with NO gaps anywhere. "
        "Luminous soft pastel color fills. Kawaii face (large glossy dot eyes with a white "
        "catchlight dot, pink blush cheek ovals, tiny smile arc) on every object sticker. "
        "BACKGROUND: Pure #FFFFFF white throughout — absolutely zero cream, off-white, gray, "
        "or gradients in the background. "
        "LAYOUT: Stickers scattered naturally on the page — NOT in a grid, NOT in rows. "
        "Every sticker is completely isolated with minimum 50px of pure white space on "
        "all four sides. NO two stickers touch or overlap each other. "
        "CONSTRAINT: Every sticker has a complete 360° closed outline with no open edges. "
        "No sticker is cut off at the page edge. No watermarks. No page border. "
        "NOW DRAW THE FOLLOWING STICKERS FOR THIS SHEET:\n"
    )

    _STICKER_SHEET_PROMPTS = [
        # Sheet 1 — Functional Planning (headers, checklists, labels)
        ("Kawaii functional planner sticker sheet, pure white background. "
         "20-22 individual illustrated kawaii stickers loosely arranged — not in a grid. "
         "Every sticker: VERY THICK black outline (4px), pastel fills, kawaii faces on object stickers. "
         "This sheet focuses on PLANNING FUNCTIONALITY — things planners write every day. "
         "Include these sticker types: "
         "(1) HERO — a wide banner ribbon sticker reading 'THIS WEEK' in bold kawaii lettering, "
         "pastel theme color background, star accents, center of page, large; "
         "(2) banner sticker 'MONTHLY GOALS' with arrow pointing right; "
         "(3) banner sticker 'HABIT TRACKER' with checkmark icon; "
         "(4) banner sticker 'DON'T FORGET' in coral/orange with exclamation kawaii face; "
         "(5) three open square checkboxes in a vertical strip labeled 'TO DO'; "
         "(6) five open square checkboxes strip labeled 'CHECKLIST'; "
         "(7) priority star flag sticker '★ PRIORITY' in gold; "
         "(8) urgent arrow sticker '!! URGENT' in red-coral; "
         "(9) due date clock sticker '⏰ DUE DATE' in teal; "
         "(10) meeting calendar pin sticker 'MEETING' in sky blue; "
         "(11) 'NOTES' label banner in lavender with pencil icon; "
         "(12) 'BRAIN DUMP' label with zigzag border, fun purple; "
         "(13) 'TOP 3' label with three stars in gold/pink; "
         "(14) 'IN PROGRESS' pill label with arrow in mint green; "
         "(15) 'COMPLETE ✓' pill label with checkmark in sage green; "
         "(16) 'NO SPEND DAY' label with piggy bank icon in mint; "
         "(17) 'PAYDAY! 🎉' celebration banner in gold; "
         "(18) 'SELF CARE' heart banner in blush pink; "
         "(19) small date dot — a filled circle with number '15' for undated planners; "
         "(20) washi tape strip design — horizontal decorative strip with floral pattern. "
         "Style: premium kawaii flat illustration, thick outlines, soft pastel palette matching planner theme, "
         "white glow drop-shadow. Pure white background. NO extra text beyond labels shown. NO watermarks."),
        # Sheet 2 — Widget Trackers (drop-in tracker widgets)
        ("Kawaii tracker widget sticker sheet, pure white background. "
         "12-15 individual illustrated planner widget stickers loosely arranged — not in a grid. "
         "These are FUNCTIONAL TRACKER WIDGETS — self-contained mini-trackers a planner user drops "
         "onto any open page space to track habits, moods, water, sleep, and energy. "
         "Every widget has: THICK black outline (3-4px), pastel fills, kawaii accents. "
         "Include these widgets: "
         "(1) HERO — MOOD TRACKER widget (large, center): a 5-bubble horizontal row with tiny kawaii faces "
         "from sad (blue tear) to happy (yellow star eyes), labeled 'MOOD TODAY', larger than others; "
         "(2) WATER INTAKE tracker: 8 droplet shapes in a 2×4 grid, empty outlines to fill in, "
         "labeled 'DAILY WATER 💧'; "
         "(3) SLEEP TRACKER: 4 moon phase icons (new moon → crescent → half → full) "
         "in a row, labeled 'SLEEP QUALITY 🌙'; "
         "(4) ENERGY LEVEL: 5 lightning bolt icons in ascending size, labeled 'ENERGY ⚡'; "
         "(5) WEEKLY HABIT STREAK: 7 circle bubbles labeled MON TUE WED THU FRI SAT SUN, "
         "to color in when done, labeled 'HABIT STREAK'; "
         "(6) STEPS COUNTER: simple rectangle widget with shoe icon, number field, "
         'labeled "STEPS TODAY 👟"; '
         "(7) GRATITUDE LOG: small widget with 3 blank lined rows and heart icon, "
         "labeled 'GRATEFUL FOR ♡'; "
         "(8) DAILY WINS: 3 trophy/star bullet rows, labeled 'TODAY'S WINS 🏆'; "
         "(9) WORKOUT LOG: dumbbell icon + type/duration fields, labeled 'WORKOUT ✓'; "
         "(10) FOCUS TIMER: Pomodoro-style tomato icon with 25-min circle, labeled 'FOCUS 🍅'; "
         "(11) WEEKLY SUMMARY: small box widget with Revenue/Spend/Saved fields for budget users; "
         "(12) MOOD + ENERGY COMBO: side-by-side smiley + lightning in one compact widget. "
         "Style: premium kawaii flat illustration, rounded widget borders, pastel fills, "
         "drop shadows, clear label typography. Pure white background. NO watermarks."),
        # Sheet 3 — Planner girl & stationery objects
        ("Kawaii planner girl stationery sticker clipart sheet, pure white background. "
         "18-20 individual adorable illustrated stickers loosely arranged on the page — "
         "NOT in a grid, scattered naturally like a real premium sticker sheet you'd peel off. "
         "Every sticker: VERY THICK black outline (4px), pastel watercolor-style fills, "
         "kawaii face (large glossy dot eyes with white catchlight, pink blush ovals, tiny smile arc). "
         "Stickers include: "
         "(1) kawaii planner notebook, open, pastel lilac cover, small kawaii face on cover, "
         "golden pen clipped on side, floating sparkle stars around it — CENTER HERO sticker, larger; "
         "(2) tall pastel pink travel mug with heart pattern sleeve, steam wisps that form a tiny heart, face; "
         "(3) cute girl silhouette holding a giant pencil — planner girl icon in pastel outfit; "
         "(4) lavender zippered pencil pouch with golden zipper, colorful pencils peeking out, kawaii face; "
         "(5) pastel blue ink fountain pen with golden nib, face, ink drop shape below; "
         "(6) stack of 3 colorful notebooks (pink, mint, yellow), kawaii face on top one; "
         "(7) washi tape dispenser roll in teal/pink stripe, face on tape wheel; "
         "(8) pastel pink rectangular eraser, two blue stripes, cute face; "
         "(9) pink sticky note pad with golden crown icon, face on pad; "
         "(10) bright yellow 6-point star with sparkle rays, face in center, large blush cheeks; "
         "(11) pastel mint green scissors with golden screw pivot, face on handle; "
         "(12) round pink clock face, golden roman numerals, kawaii sleepy face; "
         "(13) a floating heart with wings, pastel red, tiny kawaii face, sparkles; "
         "(14) purple glitter tube mascara/highlighter pen with star cap, face; "
         "(15) transparent rectangular ruler with pink gradient, kawaii face; "
         "(16) mint blue paint palette with 8 rainbow paint dots, smiling face; "
         "(17) golden trophy cup with star, pastel yellow, kawaii face on cup; "
         "(18) small green succulent in a pink polka-dot pot, face on pot. "
         "Style: premium Japanese kawaii chibi illustration, very thick outlines, luminous pastel fills, "
         "tiny white drop-shadow behind every sticker. Pure white background. NO text. NO watermarks."),
        # Sheet 2 — Cozy lifestyle
        ("Kawaii cozy lifestyle sticker clipart sheet, pure white background. "
         "18-20 individual illustrated stickers loosely arranged on the page, not in a grid. "
         "Every sticker has VERY THICK black outline (4px), soft pastel colors, "
         "kawaii face (glossy dot eyes, pink blush cheeks, tiny smile) on all object stickers. "
         "Stickers include: "
         "(1) large kawaii ceramic mug filled with hot cocoa, marshmallows peeking out, "
         "steam wisps, face on mug — HERO sticker, larger than rest; "
         "(2) open book with golden ribbon bookmark, face on cover pages, tiny hearts drifting up; "
         "(3) lit pillar candle, warm amber glow halo, dripping wax, kawaii face on candle body; "
         "(4) cozy chunky knit blanket folded in soft cream/blush colors, kawaii face peeking from fold; "
         "(5) vintage-style kettle in pastel blue with floral decal, steam from spout, face; "
         "(6) string of fairy lights looping across, each bulb has a tiny smiley dot face; "
         "(7) small macaron pastel pink and mint, kawaii face on macaron top; "
         "(8) fluffy tabby cat curled up sleeping, kawaii face, tiny 'zzz' letters; "
         "(9) pastel pink bath bomb fizzing in water, sparkle bubbles, face; "
         "(10) cozy socks pair — one bunny face, one bear face on the cuffs; "
         "(11) succulent terrarium glass globe with 3 small plants, face on globe; "
         "(12) honey jar with wooden dipper, golden drip, kawaii face on jar; "
         "(13) small diffuser/oil burner with glowing flame, swirling aromatherapy wisps, face; "
         "(14) reading glasses with heart-shaped frames, kawaii face reflected in lens; "
         "(15) pastel popcorn box with striped pattern, smiling face; "
         "(16) little music note triple-cluster — three notes with tiny faces; "
         "(17) cinnamon roll pastry, icing swirl, kawaii face in center; "
         "(18) rainy window pane with water drops, rainbow outside, kawaii cloud face in corner. "
         "Style: premium kawaii flat illustration, thick outlines, warm cozy pastel palette, "
         "tiny white glow drop-shadow. Pure white background. NO text. NO watermarks."),
        # Sheet 3 — Seasonal & holiday
        ("Kawaii seasonal holiday sticker clipart sheet, pure white background. "
         "18-20 individual illustrated stickers loosely arranged on the page, not in a grid. "
         "Every sticker has VERY THICK black outline (4px), vivid pastel colors, "
         "kawaii face (glossy dot eyes, pink blush, smile) on main stickers. "
         "Include stickers for all four seasons and key holidays: "
         "SPRING: (1) large pastel pink cherry blossom branch — HERO, center, larger; "
         "(2) yellow daffodil bouquet in blue vase, face on vase; "
         "(3) pastel rainbow arc with fluffy cloud ends, face in rainbow center; "
         "(4) Easter egg trio in blue/purple/pink with dot patterns, tiniest faces; "
         "(5) kawaii bee on a flower, striped yellow body, tiny face, heart antennae; "
         "SUMMER: (6) round smiling sun with alternating short/long rays, face, blush; "
         "(7) kawaii watermelon slice, black seed dots as tiny eyes, pink flesh; "
         "(8) pastel ice cream cone with two scoops (strawberry + mint), face on cone; "
         "(9) sunflower head, brown center with kawaii face, yellow petals; "
         "AUTUMN/FALL: (10) cute pumpkin, orange, green stem, kawaii face (not scary); "
         "(11) golden autumn leaf trio — maple, oak, birch — warm orange/red/yellow; "
         "(12) acorn with kawaii face, stripey brown hat; "
         "(13) steaming pumpkin spice latte cup with autumn sleeve, face, whipped cream top; "
         "WINTER/HOLIDAY: (14) round snowflake shape in ice blue, 6-pointed, kawaii face in center; "
         "(15) Christmas ornament ball, deep red with gold cap, white swirl, face; "
         "(16) pastel snowman — carrot nose, scarf, button eyes replaced with kawaii dot eyes + blush; "
         "(17) Valentine's Day big puffy heart in pastel red-pink, kawaii face, sparkles; "
         "(18) festive gift box with bow, pastel purple/teal, face on box, sparkle stars around it. "
         "Style: premium kawaii chibi illustration, thick outlines, vivid but still pastel fills, "
         "tiny white drop-shadow. Pure white background. NO text. NO watermarks."),
    ]

    def _load_or_gen_sticker_img(sheet_num: int) -> str | None:
        """Load cached DALL-E sticker sheet image or generate a new one."""
        cache_path = os.path.join(PRODUCT_FILES_DIR,
                                  f"{product_id}_sticker_sheet_{sheet_num}.jpg")
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 20_000:
            return cache_path
        prompt = _STICKER_STYLE_ANCHOR + _STICKER_SHEET_PROMPTS[sheet_num - 1]
        try:
            img_bytes = _fetch_image_bytes(
                prompt, size="1536x1536", quality="high", output_format="jpeg"
            )
            if img_bytes and len(img_bytes) > 10_000:
                with open(cache_path, "wb") as _f:
                    _f.write(img_bytes)
                return cache_path
        except Exception:
            pass
        return None

    def draw_sticker_picker_page():
        """Two-page kawaii sticker library: DALL-E illustrated sheets embedded full-page."""
        content_w = CW - TAB_W - 4
        hdr_h = 44

        # ── JS popup for Acrobat users who click a sticker area ──────────────
        _popup_js = (
            'var cats=["PRIORITY & TASKS","EVENTS & DATES",'
            '"WELLNESS & MOOD","SCHOOL & WORK","MOTIVATION"];'
            'var ci=app.popupMenu(cats);if(ci<0)return;'
            'var ls=['
            '["IMPORTANT","URGENT","DEADLINE","MEETING","TO-DO","ERRANDS","BUSY DAY","FOCUS","CALL","EMAIL","TO BUY","PAY BILL","REMINDER","BLOCKED","REVIEW","SUBMIT"],'
            '["BIRTHDAY!","APPT","VACAY!","ANNIVERSARY","MEMORIES","GIFT DUE","EVENT","FAMILY","HOLIDAY","GOAL MET!","DONE!","WIN!","PLAN","MILESTONE","BILL DUE","NEW MOON"],'
            '["AMAZING","GOOD","OKAY","LOW","WATER","SLEPT WELL","WORKOUT","GRATEFUL","CALM","HIGH ENERGY","MEALS","SELF CARE","MEDS","SELF LOVE","SUNSHINE","MINDFUL"],'
            '["STUDY","NOTES","TEST DAY","SUBMIT","DUE DATE","REVIEWED","PRESENT","ONLINE","FOCUS!","NO PHONE","READ","WRITE","PROGRESS","GREAT WORK","ACHIEVEMENT","LEVEL UP"],'
            '["YOU GOT THIS","STRONG","SHINE","ON FIRE","CRUSHED IT","GROWTH","BELIEVE","MAGIC DAY","FRESH START","GO WITH IT","NEW CHAPTER","YES!","GLOW UP","DREAM BIG","BE KIND","GOOD VIBES"]'
            '];'
            'var si=app.popupMenu(ls[ci]);if(si<0)return;'
            'var lbl=ls[ci][si];'
            'var fc=[["RGB",1.0,0.88,0.85],["RGB",0.85,0.95,1.0],'
            '["RGB",0.88,0.97,0.88],["RGB",0.90,0.88,1.0],["RGB",1.0,0.97,0.82]];'
            'var sc=[["RGB",0.85,0.35,0.30],["RGB",0.25,0.55,0.85],'
            '["RGB",0.25,0.65,0.38],["RGB",0.55,0.35,0.82],["RGB",0.82,0.62,0.15]];'
            'var pg=this.pageNum;var ph=this.getPageHeight(pg);var pw=this.getPageWidth(pg);'
            'try{this.addAnnot({type:"FreeText",page:pg,'
            'rect:[pw*0.33,ph*0.44,pw*0.67,ph*0.58],'
            'contents:lbl,fillColor:fc[ci],strokeColor:sc[ci],'
            'textColor:["RGB",0.08,0.08,0.12],textSize:11,alignment:1});'
            'app.alert("\\u2728 Sticker added! Drag it anywhere.",1);'
            '}catch(e){app.alert("Works in Adobe Acrobat Reader, PDF Expert & Xodo.",1);}'
        )

        for pg_idx in range(5):
            bm = "sticker_picker" if pg_idx == 0 else f"sticker_picker_{pg_idx + 1}"
            c.bookmarkPage(bm)
            if pg_idx == 0:
                c.addOutlineEntry("✨ Sticker Library", bm, level=0)
            else:
                sheet_names = ["", "Widget Trackers", "Planner & Stationery",
                               "Cozy Lifestyle", "Seasonal & Holiday"]
                c.addOutlineEntry(f"✨ Stickers — {sheet_names[pg_idx]}", bm, level=1)

            # ── Cream page background ─────────────────────────────────────────
            rect(0, 0, PW, PH, f=(0.998, 0.996, 0.992))
            # Subtle small dot grid
            for _gx in range(int(ML), int(PW - TAB_W), 16):
                for _gy in range(int(MB + 8), int(PH - 38), 16):
                    circle(_gx, _gy, 0.45, f=_blend(T, 0.70))

            # ── Header ────────────────────────────────────────────────────────
            rect(0, PH - hdr_h, PW - TAB_W - 2, hdr_h, f=T)
            rect(0, PH - hdr_h - 2, PW - TAB_W - 2, 2, f=A)
            rect(0, PH - hdr_h, 7, hdr_h, f=A)
            _sheet_subtitles = ["Functional Planning", "Widget Trackers",
                                "Planner & Stationery", "Cozy Lifestyle", "Seasonal & Holiday"]
            font("Helvetica-Bold", 22); fill(WHITE)
            c.drawString(ML + 12, PH - hdr_h + 14,
                         f"✨  Kawaii Sticker Library — {_sheet_subtitles[pg_idx]}")
            font("Helvetica", 8); fill(_blend(WHITE, 0.32))
            c.drawRightString(PW - TAB_W - 12, PH - hdr_h + 28,
                              f"Page {pg_idx + 1} of 5")

            # ── How-to pills ──────────────────────────────────────────────────
            tip_y = PH - hdr_h - 7
            for _icon, _tip in [
                ("Acrobat / Xodo → ",
                 "Tap ✨ STICKERS button in footer on any page → menu pops up → sticker drops on page → drag it anywhere"),
                ("GoodNotes / Notability → ",
                 "Screenshot this page → open your app → import as Custom Sticker Sheet → drag onto any page"),
            ]:
                rect(ML, tip_y - 11, content_w, 14, f=_blend(A, 0.80), radius=5)
                font("Helvetica-Bold", 6); fill(T)
                _iw = c.stringWidth(_icon, _fn("bold"), 6)
                c.drawString(ML + 6, tip_y - 3, _icon)
                font("Helvetica", 6); fill(DARK)
                c.drawString(ML + 6 + _iw, tip_y - 3, _tip)
                tip_y -= 17

            # ── Main sticker image area ───────────────────────────────────────
            img_top = tip_y - 4
            img_bot = MB + 24
            img_h = img_top - img_bot

            img_path = _load_or_gen_sticker_img(pg_idx + 1)

            if img_path:
                # Embed DALL-E sticker sheet image full-width
                try:
                    c.drawImage(ImageReader(img_path),
                                ML, img_bot, content_w, img_h,
                                preserveAspectRatio=True, anchor="c")

                    # Thin rounded frame around image
                    rect(ML - 1, img_bot - 1, content_w + 2, img_h + 2,
                         s=_blend(T, 0.60), lwidth=0.8, radius=6)

                    # Invisible 4×5 JS grid overlay so Acrobat users can click
                    # any sticker area and get the popup menu
                    _gcols = 5; _grows = 4
                    _gw = content_w / _gcols
                    _gh = img_h / _grows
                    for _gr in range(_grows):
                        for _gc in range(_gcols):
                            _bx = ML + _gc * _gw
                            _by = img_bot + _gr * _gh
                            _js_button(_bx, _by, _gw, _gh, _popup_js)
                except Exception:
                    img_path = None

            if not img_path:
                # ── Programmatic kawaii fallback ──────────────────────────────
                cats_on_page = (_STICKER_CATEGORIES[0:2] if pg_idx == 0 else
                                _STICKER_CATEGORIES[2:4] if pg_idx == 1 else
                                _STICKER_CATEGORIES[4:])
                n_cats = len(cats_on_page)
                avail_h = img_h
                cat_h = (avail_h - 6 * (n_cats - 1)) / n_cats

                for ci, (cat_name, cat_color, stickers) in enumerate(cats_on_page):
                    cat_top = img_top - ci * (cat_h + 6)
                    rect(ML, cat_top - 18, content_w, 18, f=_blend(cat_color, 0.22), radius=7)
                    rect(ML, cat_top - 18, 5, 18, f=cat_color, radius=3)
                    font("Helvetica-Bold", 8.5); fill(_blend(cat_color, 0.05))
                    c.drawString(ML + 14, cat_top - 13, cat_name.upper())

                    stk_cols = 8; stk_gap = 5
                    sw = (content_w - stk_gap * (stk_cols - 1)) / stk_cols
                    row_h = cat_h - 22
                    sh = min(row_h - 4, sw * 1.10)
                    stk_top = cat_top - 22

                    for si, (lbl, col, shape) in enumerate(stickers):
                        ic = si % stk_cols; ir = si // stk_cols
                        sx = ML + ic * (sw + stk_gap)
                        sy = stk_top - ir * (sh + stk_gap + 2) - sh
                        if sy < img_bot + 4:
                            break
                        _draw_kawaii_sticker(sx, sy, sw, sh, lbl, col, shape,
                                             sticker_page_mode=True)

            page_footer(f"STICKER LIBRARY · Page {pg_idx + 1}")
            draw_nav_tabs()
            c.showPage()

    def draw_sticker_pack_page(pack_idx=1):
        """Single-category kawaii sticker page for Tier 1/2 styles."""
        bm = f"stickers_{pack_idx}"
        c.bookmarkPage(bm)
        if pack_idx == 1:
            c.addOutlineEntry("Sticker Pack", bm, level=0)
        else:
            c.addOutlineEntry(f"Sticker Pack {pack_idx}", bm, level=1)
        # Cream background for clean sticker look
        rect(0, 0, PW, PH, f=(0.995, 0.993, 0.988))
        content_w = CW - TAB_W - 4

        cat_idx = (pack_idx - 1) % len(_STICKER_CATEGORIES)
        cat_name, cat_color, stickers = _STICKER_CATEGORIES[cat_idx]

        rect(0, PH - MT - 48, PW - TAB_W - 2, 48 + MT, f=T)
        rect(0, PH - MT - 48, 7, 48 + MT, f=cat_color)
        font("Helvetica-Bold", 20); fill(WHITE)
        c.drawString(ML + 14, PH - MT - 30, f"✨  {cat_name}")
        font("Helvetica", 7); fill(_blend(WHITE, 0.38))
        c.drawRightString(PW - TAB_W - 10, PH - MT - 30,
                          "Screenshot → import as custom sticker sheet in GoodNotes / Notability")
        rect(0, PH - MT - 52, PW - TAB_W - 2, 4, f=cat_color)

        cols = 4; gutter = 14
        sw = (content_w - gutter * (cols - 1)) / cols
        sh = sw * 1.15
        sy0 = PH - MT - 68

        for si, (lbl, col, shape) in enumerate(stickers[:16]):
            ci = si % cols; ri = si // cols
            sx = ML + ci * (sw + gutter)
            sy = sy0 - ri * (sh + gutter) - sh
            if sy < MB + 20:
                break
            _draw_kawaii_sticker(sx, sy, sw, sh, lbl, col, shape, sticker_page_mode=False)

        page_footer(f"STICKER PACK · {cat_name}")
        draw_nav_tabs()
        c.showPage()

    # ── CALENDAR SYNC GUIDE (tier 3 only) ────────────────────────────────────
    def draw_calendar_sync_page():
        c.bookmarkPage("cal_sync")
        c.addOutlineEntry("Calendar Sync Guide", "cal_sync", level=0)
        page_bg()
        content_w = CW - TAB_W - 4

        # Header
        rect(0, PH - MT - 54, PW - TAB_W - 2, 54 + MT, f=T)
        rect(0, PH - MT - 54, 5, 54 + MT, f=A)
        font("Helvetica-Bold", 20); fill(WHITE)
        c.drawString(ML + 14, PH - MT - 34, "CALENDAR SYNC GUIDE")
        font("Helvetica", 8.5); fill(_blend(WHITE, 0.45))
        c.drawRightString(PW - TAB_W - 10, PH - MT - 34, "Google Calendar · Apple Calendar")
        rect(0, PH - MT - 58, PW - TAB_W - 2, 4, f=A)

        y = PH - MT - 80
        steps = [
            ("TAP A DATE TO VIEW IT",
             "Every dated cell in the monthly calendar is a live link. Tap the "
             "date number (e.g. 12) to open that day directly in Google Calendar "
             "— works on iPhone, Android, Mac, and PC."),
            ('TAP "+" TO ADD AN EVENT',
             'Each day cell has a small + button in the bottom-right corner. '
             "Tap it to open Google Calendar's New Event screen pre-filled "
             "with that date — ready for you to type the event details."),
            ("WEEKLY CALENDAR BUTTON",
             "On each weekly page, tap OPEN WEEK IN GOOGLE CAL in the sidebar "
             "to see your full week schedule alongside your planner notes."),
            ("WORKS ON ALL DEVICES",
             "Google Calendar links open in any browser. On iPhone or Android, "
             "install the free Google Calendar app for the best experience. "
             "The A button in each cell opens Apple Calendar on iOS and macOS."),
            ("SYNC BOTH CALENDARS",
             "To use both: add your Google account to iOS Settings → Calendar → "
             "Accounts. Your Google events will then appear in Apple Calendar "
             "and both apps stay in sync automatically."),
        ]

        for i, (heading, body) in enumerate(steps):
            if y < MB + 50:
                break
            # Step circle
            circle(ML + 11, y - 5, 10, f=A)
            font("Helvetica-Bold", 7.5); fill(DARK)
            c.drawCentredString(ML + 11, y - 7, str(i + 1))
            # Heading
            font("Helvetica-Bold", 9.5); fill(T)
            c.drawString(ML + 28, y - 1, heading)
            y -= 17
            # Body — simple word-wrap
            font("Helvetica", 8); fill(DARK)
            words = body.split(); line = ""; max_w = content_w - 34
            for w in words:
                test = (line + " " + w).strip()
                if c.stringWidth(test, "Helvetica", 8) <= max_w:
                    line = test
                else:
                    c.drawString(ML + 28, y, line); y -= 11; line = w
            if line:
                c.drawString(ML + 28, y, line); y -= 11
            y -= 14

        # Big Google Calendar button at the bottom
        gcal_main = "https://calendar.google.com"
        bw2 = 180; bh2 = 26; bx2 = (PW - TAB_W) / 2 - bw2 / 2; by2 = MB + 28
        rect(bx2, by2, bw2, bh2, f=A, radius=6)
        font("Helvetica-Bold", 10); fill(DARK)
        c.drawCentredString(bx2 + bw2/2, by2 + 9, "OPEN GOOGLE CALENDAR")
        c.linkURL(gcal_main, (bx2, by2, bx2 + bw2, by2 + bh2))

        page_footer("Calendar Sync Guide")
        draw_nav_tabs()
        c.showPage()

    # ── ASSEMBLE ──────────────────────────────────────────────────────────────
    page_count = 0
    draw_cover();          page_count += 1
    draw_welcome_page();   page_count += 1
    draw_dashboard_page(); page_count += 1
    draw_index_page();     page_count += 1
    draw_how_to_use();     page_count += 1
    if cal_integration in ("google", "apple", "both"):
        draw_calendar_sync_page(); page_count += 1
    if "color_selector" in _extras:
        draw_color_selector_page(); page_count += 1
    if "vision_board" in _extras:
        draw_vision_board_page(); page_count += 1
    if "mood_tracker" in _extras:
        draw_mood_tracker_page(); page_count += 1

    if "monthly" in sections or "weekly" in sections:
        draw_yearly_overview(); page_count += 1

    if "monthly" in sections:
        for mi in range(12):
            draw_monthly_page(mi); page_count += 1
            if "month_at_a_glance" in sections:
                draw_month_at_a_glance(mi); page_count += 1
            if "monthly_review" in sections:
                draw_monthly_review(mi); page_count += 1

    if "weekly" in sections:
        if undated:
            for wn in range(1, 53):
                draw_weekly_page(wn); page_count += 1
        else:
            from datetime import date as dt_date, timedelta
            first_day = dt_date(planner_year, 1, 1)
            start = first_day - timedelta(days=first_day.weekday())
            if start.year < planner_year:
                start += timedelta(weeks=1)
            wn = 1
            while start.year <= planner_year and wn <= 52:
                draw_weekly_page(wn, start); page_count += 1
                start += timedelta(weeks=1); wn += 1

    if "habit_tracker" in sections:
        draw_habit_tracker(); page_count += 1

    if "goals" in sections:
        draw_goals_page(); page_count += 1

    if "budget" in sections:
        draw_budget_page(); page_count += 1

    if "meal_plan" in sections:
        draw_meal_plan_page(); page_count += 1

    if "notes" in sections:
        for ni in range(4):
            draw_notes_page(ni + 1); page_count += 1

    if "sticker_pack" in _extras:
        if _design == 3:
            # Tier 3: unified interactive picker -- draw_sticker_picker_page() itself
            # writes 5 real pages (one per sticker sheet: Functional Planning, Widget
            # Trackers, Planner & Stationery, Cozy Lifestyle, Seasonal & Holiday --
            # its own `for pg_idx in range(5): ... c.showPage()` loop), so crediting
            # only +1 here undercounted the function's returned "pages" metadata by 4
            # against the real PDF (2026-08-13 functional audit, CLAUDE.md Quality
            # Gate rule "page counts... match the description exactly").
            draw_sticker_picker_page(); page_count += 5
        else:
            # Tier 1/2: three separate screenshottable sticker pack pages
            for _pi in range(1, 6):
                draw_sticker_pack_page(_pi); page_count += 1

    c.save()
    file_size_kb = os.path.getsize(file_path) // 1024

    import hashlib as _hashlib
    with open(file_path, "rb") as _hf:
        product["file_hash"] = _hashlib.sha256(_hf.read()).hexdigest()
    product["is_placeholder"] = False
    product["file_path"]      = file_path
    product["file_format"]    = "PDF"
    product["file_size_kb"]   = file_size_kb
    product["status"]         = "qc_pending"
    product["color_scheme"]   = scheme_key
    product["interactive"]    = is_interactive
    product["updated_at"]     = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success":       True,
        "product_id":    product_id,
        "file_path":     file_path,
        "file_size_kb":  file_size_kb,
        "pages":         page_count,
        "sections":      sections,
        "interactive":   is_interactive,
        "color_scheme":  cs["label"],
        "format":        fmt,
        "status":        "qc_pending",
        "features": [
            "Hyperlinked side navigation tabs (GoodNotes/Notability compatible)",
            "Fillable PDF form fields for all text areas",
            "Interactive checkboxes in habit tracker",
            "PDF bookmarks and outline for table of contents",
            "How to Use instruction page",
        ] if is_interactive else ["Print-ready layout", "PDF bookmarks/outline"],
        "next_step": "Send to Quality Check Agent for review. Then run generate_listing_content for SEO.",
    }, indent=2)



def _list_digital_products(status_filter: str, store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    if status_filter != "all":
        products = [p for p in products if p.get("status") == status_filter]
    summary = [
        {
            "id": p["id"],
            "title": p["title"],
            "type": p["product_type"],
            "status": p["status"],
            "format": p.get("file_format"),
            "price": p["price"],
            "qc_status": p.get("qc_status"),
            "created_at": p.get("created_at", ""),
        }
        for p in products
    ]
    return json.dumps({"products": summary, "count": len(summary)}, indent=2)


def _get_digital_product(product_id: str, store: DataStore) -> str:
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})
    return json.dumps(product, indent=2)


def _update_product_status(data: dict, store: DataStore) -> str:
    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Product {data['product_id']} not found"})
    old_status = product["status"]
    product["status"] = data["status"]
    if data.get("notes"):
        product["status_notes"] = data["notes"]
    product["updated_at"] = str(date.today())
    _save_product(product, store)
    return json.dumps({"success": True, "product_id": data["product_id"],
                       "previous_status": old_status, "new_status": data["status"]}, indent=2)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _find_product(product_id: str, store: DataStore) -> dict | None:
    products = store.get("digital_products", default=[])
    return next((p for p in products if p["id"] == product_id), None)


def _save_product(product: dict, store: DataStore) -> None:
    products = store.get("digital_products", default=[])
    for i, p in enumerate(products):
        if p["id"] == product["id"]:
            products[i] = product
            break
    store.set(products, "digital_products")
    store.save()
