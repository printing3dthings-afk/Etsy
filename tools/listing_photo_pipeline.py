#!/usr/bin/env python3
"""
listing_photo_pipeline.py — Self-verifying lifestyle photo generator

THE standard pipeline for every listing photo, every product category.
Encodes every lesson from the June 2026 SS1001 session so photos come out
right the FIRST time, without human back-and-forth:

  FAILURE MODE                         → AUTOMATED COUNTERMEASURE
  1. Product physics wrong             → physics templates injected per product type
     (raised lettering on flat signs)
  2. Color drift                       → palette auto-EXTRACTED from the design file
     (navy bias from hardcoded colors)   and injected as hex constraints (never hand-typed)
  3. Hallucinated sibling products     → ALL design files passed as edit inputs;
                                          flat lays use pixel-perfect PIL paste instead
  4. Garbled small text                → text auto-extracted via vision model, injected
                                          as character-exact constraint, then VERIFIED
  5. Fine geometry mangled             → post-generation vision verification compares
     (stamp perforations)                render vs source; discrepancies fed back into
                                          an auto-retry (max 3); hard fails are reported
                                          so the scene can fall back to PIL or another design

Usage (library):
    from tools.listing_photo_pipeline import generate_verified_photo, build_flat_lay

    result = generate_verified_photo(
        design_paths=[Path("design.jpg")],
        scene_prompt="mounted on a cream plaster wall above a walnut console...",
        out_path=Path("photo_01.jpg"),
        physics="sign_flat",            # key into PHYSICS templates
    )
    # result.passed → bool; result.issues → unresolved discrepancies if any

Flat lays / collection shots (zero perspective → pixel-perfect, never AI-rendered):
    build_flat_lay(design_paths, layout, bg_prompt_or_path, out_path)
"""

import re, os, base64, io, json, sys
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

MOCKUP_SIZE   = 2400
INPUT_MAX_DIM = 1024
MAX_ATTEMPTS  = 3
EXTRACT_MODEL = "gpt-4o-mini"   # cheap, fine for reading text off a design
VERIFY_MODEL  = "gpt-4o"        # mini hallucinated rejections AND missed a real
                                # shape error in testing — verification needs 4o


# ── Product physics templates ─────────────────────────────────────────────────
# What the physical product actually looks like. Add new product types here.
PHYSICS = {
    # 3D-printed sign, printed FACE-DOWN on textured PEI plate
    "sign_flat": (
        "a thin flat 3D-printed panel (about 6mm thick) made from colored PLA "
        "filament, printed face-down on a textured build plate. The entire front "
        "face is PERFECTLY FLAT — the design is NOT raised, NOT embossed, NOT "
        "engraved; all colors are flush in a single smooth plane like an inlaid "
        "graphic, with a very fine uniform matte grain from the textured plate. "
        "FDM layer lines are visible only on the thin side edges."
    ),
    # Sublimation wrap on a 20oz skinny tumbler
    "tumbler_wrap": (
        "a 20oz skinny stainless steel tumbler with the design physically wrapped "
        "around the cylindrical body with proper curvature, subtle metallic "
        "highlights where the curved surface catches light, and the brushed "
        "stainless lid and base visible above and below the wrap."
    ),
    # Framed wall art print
    "framed_print": (
        "a paper art print displayed in a thin frame with a 2.5-3 inch white mat. "
        "The print surface is perfectly flat matte paper behind glass with a "
        "subtle natural reflection. The design fills the print area edge to edge."
    ),
    # Flat printed paper / card
    "flat_paper": (
        "a flat printed sheet of matte paper lying perfectly flat, the design "
        "printed edge to edge with accurate colors and crisp text."
    ),
    # Silver iPad Pro 12.9-inch showing a PDF planner on screen
    "ipad_lifestyle": (
        "a Silver Apple iPad Pro 12.9-inch. The tablet sits at a 30-degree angle "
        "with an Apple Pencil resting diagonally at the lower-right corner. The screen "
        "displays planner PDF content — the spread fills the screen edge-to-edge, "
        "screen brightness is natural (not blown-out), with a very subtle glass "
        "reflection band at the very top edge only. The iPad has its characteristic "
        "flat-edge aluminum form factor. The screen content must be sharp and legible."
    ),
    # Sticker sheets photographed overhead for sticker showcase
    "sticker_sheet_flat": (
        "PNG sticker sheets lying flat on a cream surface, photographed from directly "
        "overhead (straight top-down). The sheets have crisp clean edges, individual "
        "sticker designs are clearly legible, transparent areas between stickers reveal "
        "the cream surface beneath. A subtle drop shadow at each sheet edge."
    ),
    # FDM 3D-printed translucent lamp shade (Crystal Glow / Sculptural Mesh / Geometric Glow)
    "3d_print_lamp": (
        "an FDM 3D-printed lamp made from translucent PLA filament, lit from inside "
        "with a warm soft white LED glow that shines evenly through the shade walls. "
        "Copy the shade's surface pattern pixel-for-pixel from the attached source "
        "photo — do not substitute, simplify, smooth over, or swap in any other "
        "surface pattern; render only the exact perforations/cells/facets visible in "
        "that source image, with no added or invented texture. The shade has a "
        "matte, slightly frosted translucent finish — not glossy, not glass, not "
        "perfectly clear. Faint horizontal FDM layer lines are visible only when viewed "
        "close to the surface at a grazing angle. The lamp sits on its solid opaque "
        "matte plastic base (the same base color and shape as the source photo), which "
        "does not glow. No cracks, no warping, no support-material marks."
    ),
    # FDM 3D-printed vase (Ribbed Vase for Dried Flowers)
    "3d_print_vase": (
        "an FDM 3D-printed vase made from matte black PLA filament with continuous "
        "vertical ribbing/fluting running the full height of the body, exactly as "
        "shown in the source photo — never smooth, never glossy. The surface has a "
        "uniform matte, slightly satin sheen typical of PLA, with faint horizontal FDM "
        "layer lines visible only at a close grazing angle, not as a dominant texture. "
        "The vase is opaque and fully solid-colored black with no gradients, prints, or "
        "decals. Wall thickness and silhouette (bulbous body, narrower neck) match the "
        "source exactly."
    ),
    # FDM 3D-printed small desk holder (Minimalist Pen Holder / tea light holders)
    "3d_print_holder": (
        "a small FDM 3D-printed holder made from matte PLA filament. The exterior "
        "surface texture (organic pebbled cells, vertical fluting, or a corded/ribbed "
        "ring pattern — whichever exact pattern appears in the source photo) must be "
        "reproduced precisely, with no added or invented detail beyond what the source "
        "shows. The plastic is fully opaque with a uniform matte finish — never glossy, "
        "never transparent. Faint horizontal FDM layer lines are visible only at a "
        "close grazing angle on edges. Color is flat and solid exactly matching the "
        "source (no gradients, no printed graphics on the holder itself)."
    ),
    # FDM 3D-printed planter (Ribbed Planter Pot)
    "3d_print_planter": (
        "an FDM 3D-printed two-tone planter pot made from matte PLA filament: a cream/"
        "white upper section (including its printed smiley-face detail exactly as shown "
        "in the source photo) and a coral/red lower section standing on three short "
        "stubby legs. Both color sections are flat, solid, matte PLA — never glossy, "
        "never gradient-blended at the color seam. Faint horizontal FDM layer lines are "
        "visible only at a close grazing angle. No soil or plant is inside the pot "
        "unless the scene prompt explicitly adds one as a separate real-world prop."
    ),
}


# ── Per-product style anchors (paste identically into every prompt in a batch) ─
# "Style DNA" ensures all 10 listing photos look shot in the same session.
# Based on OpenAI research: lowest-cost consistency = identical style anchor string
# injected into every prompt (no seed parameter exists in gpt-image-1).
STYLE_ANCHORS: dict[str, str] = {
    "DP1026": (
        "STYLE DNA — apply to every photo in this batch: "
        "bright airy editorial Etsy lifestyle photography. "
        "Lavender purple (#8666AA) accent props. Cream linen desk surface. "
        "Soft diffused window light from the LEFT, warm white balance 5000K, "
        "gentle shadows to the RIGHT. 50mm lens equivalent, eye-level camera angle, "
        "slight depth of field on background. "
        "No hands, no people, no text overlays, no studio equipment. "
        "Mood: cozy, aspirational, feminine, kawaii."
    ),
    "DP1027": (
        "STYLE DNA — apply to every photo in this batch: "
        "bright airy Etsy lifestyle photography, student desk aesthetic. "
        "Cotton candy pink (#DE97C6) and sky-blue (#97C6DE) accent props. "
        "Light cream desk surface. Soft bright natural light from the LEFT, "
        "slightly cool-white balance. 50mm lens equivalent, slightly elevated "
        "20-degree camera angle, slight depth of field on background. "
        "No hands, no people, no text overlays, no studio equipment. "
        "Mood: fun, energetic, back-to-school, kawaii."
    ),
    "DP1028": (
        "STYLE DNA — apply to every photo in this batch: "
        "clean professional Etsy lifestyle photography. "
        "Deep royal blue (#1B2568) and ice-blue (#7BA7C2) accent props. "
        "Dark navy or cream desk surface. Bright clean natural light from the LEFT, "
        "neutral-cool white balance. 50mm lens equivalent, eye-level angle, "
        "minimal depth-of-field variation — everything reasonably sharp. "
        "No hands, no people, no text overlays, no studio equipment. "
        "Mood: professional, trustworthy, focused, premium."
    ),
    "DP1029": (
        "STYLE DNA — apply to every photo in this batch: "
        "bright energetic Etsy lifestyle photography. "
        "Warm coral (#FD6C49) and peach-gold (#F5B878) accent props. "
        "Warm cream or light wood desk surface. Bright warm morning light from "
        "the LEFT, warm-white balance. 50mm lens equivalent, slightly elevated "
        "20-degree angle, slight depth of field on background. "
        "No hands, no people, no text overlays, no studio equipment. "
        "Mood: energetic, motivating, wellness-forward, warm."
    ),
}


# ── 10-slot scene templates for standard planner listing photos ───────────────
# Each entry matches one Etsy listing photo slot from the CLAUDE.md photo plan.
# Use {color_theme}, {accent_color}, {spread_description} as fill-in tokens.
# "physics" key maps to the PHYSICS dict above.
PLANNER_SCENE_TEMPLATES: dict[str, dict] = {

    "slot_01_hero": {
        "description": "Hero lifestyle — iPad at 30° on desk, planner spread visible (THUMBNAIL)",
        "physics": "ipad_lifestyle",
        "scene": (
            "SUBJECT: Silver iPad Pro 12.9-inch at a 30-degree angle, screen showing "
            "{spread_description}. iPad fills center 65% of frame.\n"
            "SURFACE: cream linen-textured desk, slight fabric weave visible.\n"
            "FOREGROUND: Apple Pencil resting diagonally at lower-right of iPad.\n"
            "BACKGROUND (clustered upper-right, 3 props max): steaming ceramic latte "
            "in a white mug, a small eucalyptus sprig in a ceramic bud vase, "
            "two {accent_color} washi tape rolls.\n"
            "LIGHTING: soft diffused window light from the LEFT, warm white balance "
            "5000K, gentle shadow falling to the RIGHT. No harsh highlights on screen.\n"
            "CAMERA: 50mm lens equivalent, eye-level angle, slight depth of field on "
            "background props, sharp focus on screen.\n"
            "DEPTH LAYERS: Apple Pencil (foreground) → iPad screen (midground) → "
            "latte mug + vase + washi tape (background).\n"
            "CONSTRAINT: The image contains ONLY the iPad, Apple Pencil, and the 3 "
            "background props listed above. No other objects. No hands. No people. "
            "No text overlays. No watermarks. No studio lighting equipment visible."
        ),
    },

    "slot_02_whats_included": {
        "description": "What's Included flat lay — iPad + sticker sheets on cream background",
        "physics": "flat_paper",
        "scene": (
            "SUBJECT: overhead product flat lay, straight top-down camera.\n"
            "SURFACE: light cream background with subtle linen texture.\n"
            "LEFT SIDE: silver iPad Pro showing the planner PDF open to its cover — "
            "{spread_description} fills the screen.\n"
            "RIGHT SIDE: 3 kawaii PNG sticker sheets fanned slightly at 15-degree "
            "angles, individual sticker designs clearly legible.\n"
            "CENTER (3 props max between iPad and sticker sheets): a thin {accent_color} "
            "ribbon bow, an uncapped fine-tip pen, a tiny dried flower sprig.\n"
            "LIGHTING: soft even overhead diffused light, subtle shadow depth, no harsh "
            "highlights on screen glass. Even, bright, no color cast.\n"
            "CAMERA: directly overhead, 50mm equivalent, no tilt, perfect top-down view.\n"
            "CONSTRAINT: ONLY the items listed above are in frame. No text overlays — "
            "callouts ('104 pages', '200+ stickers') are added in Canva AFTER generation. "
            "No hands. No people. No extra objects."
        ),
    },

    "slot_03_monthly": {
        "description": "Monthly calendar spread in-app preview",
        "physics": "ipad_lifestyle",
        "scene": (
            "SUBJECT: Silver iPad Pro 12.9-inch at a 15-degree angle on a cream desk, "
            "positioned slightly above the surface. Screen shows a full monthly calendar "
            "spread in {color_theme}: kawaii illustrated header with month name, "
            "5-row grid calendar with fillable day cells, small kawaii icon decorations "
            "in corners, color-coded section navigation tabs on the right edge.\n"
            "FOREGROUND: Apple Pencil cap visible at left edge of frame.\n"
            "BACKGROUND: minimal — a thin washi tape strip at top-right, corner of a notebook.\n"
            "LIGHTING: bright clean natural light from the LEFT, warm-white balance.\n"
            "CAMERA: 50mm equivalent, slightly elevated 20-degree angle, sharp focus on screen.\n"
            "CONSTRAINT: iPad fills 70% of frame. ONLY iPad + Apple Pencil cap + washi tape "
            "strip + notebook corner. No text overlays. No hands."
        ),
    },

    "slot_04_weekly": {
        "description": "Weekly spread in-app preview",
        "physics": "ipad_lifestyle",
        "scene": (
            "SUBJECT: Silver iPad Pro 12.9-inch lying nearly flat on a light wood desk "
            "surface, camera at 20-degree elevated angle. Screen shows a horizontal "
            "weekly spread in {color_theme}: 7 column headers MON–SUN in kawaii font, "
            "time-block rows for morning/afternoon/evening per day, a notes column on "
            "the right, all fields blank and fillable, section tabs on right edge.\n"
            "FOREGROUND: a fine-tip pen resting to the right of the iPad.\n"
            "BACKGROUND: small to-do note pad at upper-left.\n"
            "LIGHTING: bright even natural daylight from the LEFT. Clean, no shadows on screen.\n"
            "CAMERA: 50mm equivalent, 20-degree elevated angle, sharp focus on entire screen.\n"
            "CONSTRAINT: iPad fills 72% of frame. ONLY iPad + pen + note pad. "
            "No hands. No text overlays."
        ),
    },

    "slot_05_stickers": {
        "description": "Sticker library showcase — 3 sticker sheets fan arrangement",
        "physics": "sticker_sheet_flat",
        "scene": (
            "SUBJECT: overhead flat lay, straight top-down camera.\n"
            "SURFACE: clean cream background — bright, even, no visible texture.\n"
            "THREE large kawaii PNG sticker sheets in a loose fan formation with slight "
            "overlap at 15-degree angles: "
            "Sheet 1 (planner & stationery — miniature notebooks, pens, stars, washi tape, "
            "coffee cups), "
            "Sheet 2 (cozy lifestyle — candles, mugs, open books, fairy lights, sleeping cat), "
            "Sheet 3 (seasonal — cherry blossoms, pumpkins, snowflakes, valentines). "
            "PNG transparent areas show cream background clearly. "
            "Individual sticker designs are sharp and legible.\n"
            "SCATTERED: 5–6 individual stickers loose around the sheets as if recently placed.\n"
            "LIGHTING: even bright overhead diffused light, sharp focus, minimal shadows.\n"
            "CAMERA: directly overhead, 50mm equivalent, straight top-down, no tilt.\n"
            "CONSTRAINT: ONLY the 3 sticker sheets + 5–6 loose individual stickers. "
            "No other objects. No hands. No text overlays."
        ),
    },

    "slot_06_how_to": {
        "description": "GoodNotes 3-step import how-to graphic",
        "physics": "flat_paper",
        "scene": (
            "SUBJECT: clean instructional graphic, overhead view.\n"
            "SURFACE: very light cream or white background.\n"
            "THREE sequential iPad screen mockup frames arranged LEFT to RIGHT, equal "
            "spacing, each in a subtle rectangular drop-shadow frame:\n"
            "  LEFT (Step 1): GoodNotes 6 app open — Elements side panel visible, "
            "Stickers tab highlighted, a clearly visible green '+' button.\n"
            "  CENTER (Step 2): iOS file picker — 3 PNG files listed, blue checkmarks on each.\n"
            "  RIGHT (Step 3): GoodNotes planner page open, a small kawaii sticker in "
            "{accent_color} being dragged onto a weekly spread.\n"
            "ABOVE EACH FRAME: a filled circle numbered 1, 2, 3 in {accent_color} with white number.\n"
            "STYLE: clean infographic layout, equal spacing, flat illustration feel.\n"
            "LIGHTING: even overhead studio light, no shadows on screens.\n"
            "CAMERA: directly overhead, all elements in focus.\n"
            "CONSTRAINT: ONLY the 3 iPad mockup frames + numbered circles. "
            "No text labels (added in Canva after). No hands."
        ),
    },

    "slot_07_compatibility": {
        "description": "App compatibility graphic — 5 app icons around central PDF icon",
        "physics": "flat_paper",
        "scene": (
            "SUBJECT: clean flat graphic, slight overhead view.\n"
            "SURFACE: soft cream background with very subtle dot-grid texture.\n"
            "CENTER: a large planner PDF file icon in {color_theme} palette "
            "(document shape with 'PDF' badge at bottom-right corner).\n"
            "SURROUNDING CENTER in a circular arrangement at equal spacing — "
            "five rounded square app icons:\n"
            "  GoodNotes (green icon), Notability (red-orange), "
            "PDF Expert (blue), Xodo (teal), Adobe Acrobat (dark red).\n"
            "Each icon has a small white checkmark badge at its bottom-right corner.\n"
            "CONNECTING: thin {accent_color} dashed lines from each app icon to the center PDF icon.\n"
            "STYLE: flat illustration, clean geometric, icons correctly proportioned and recognizable.\n"
            "LIGHTING: even flat studio light, no shadows.\n"
            "CAMERA: 5-degree overhead tilt, all elements sharp.\n"
            "CONSTRAINT: ONLY the center PDF icon + 5 app icons + dashed lines. "
            "No text labels (added in Canva after). No hands. No people."
        ),
    },

    "slot_08_cover_beauty": {
        "description": "Kawaii cover close-up beauty shot — iPad screen fills 78% of frame",
        "physics": "ipad_lifestyle",
        "scene": (
            "SUBJECT: iPad Pro screen filling 78% of the frame, straight-on angle. "
            "Screen shows the full kawaii illustrated planner cover in {color_theme}: "
            "the illustrated kawaii character or scene, elegant title typography, "
            "the year 2026, decorative border elements — all crisp and perfectly sharp.\n"
            "BACKGROUND: extreme shallow depth of field, blurred {accent_color} "
            "fabric or silk surface behind the iPad — a soft color wash only.\n"
            "LIGHTING: even bright studio-style light, anti-glare on screen, "
            "screen content perfectly exposed — not blown out, not too dark.\n"
            "CAMERA: straight-on angle (5 degrees off perpendicular), "
            "85mm telephoto equivalent, shallow depth of field on background only.\n"
            "CONSTRAINT: ONLY iPad screen fills frame. NO props. NO background objects "
            "except blurred fabric color wash. No hands. No text overlays."
        ),
    },

    "slot_09_habit_tracker": {
        "description": "Habit tracker page — cozy evening desk with Apple Pencil",
        "physics": "ipad_lifestyle",
        "scene": (
            "SUBJECT: Silver iPad Pro 12.9-inch at a relaxed 30-degree angle on a warm "
            "wooden desk. Screen shows the Habit Tracker page in {color_theme}: "
            "a 31-row grid with habit name columns on the left, approximately 12 rows "
            "filled with colored checkmarks or dots, kawaii star/moon icon decorations "
            "in the header, 'HABIT TRACKER' title visible in kawaii font at top.\n"
            "FOREGROUND: Apple Pencil resting beside the iPad.\n"
            "BACKGROUND (upper-right, 2 props max): a blank sticky note, "
            "a {accent_color} highlighter pen uncapped.\n"
            "LIGHTING: warm desk lamp light from the UPPER-RIGHT, cozy amber tone, "
            "soft evening atmosphere, shadows fall LEFT and DOWN.\n"
            "CAMERA: 50mm equivalent, 30-degree elevated angle, sharp focus on screen.\n"
            "CONSTRAINT: ONLY iPad + Apple Pencil + sticky note + highlighter. "
            "No hands. No text overlays. No other objects."
        ),
    },

    "slot_10_specialty": {
        "description": "Product-specific specialty page (budget / study / fitness / etc.)",
        "physics": "ipad_lifestyle",
        "scene": "{specialty_prompt}",
        "notes": "Use SPECIALTY_PROMPTS[product_id] to fill {specialty_prompt} before calling.",
    },
}


# Per-product specialty page prompts for slot 10
SPECIALTY_PROMPTS: dict[str, str] = {
    "DP1026": (
        "SUBJECT: Silver iPad Pro 12.9-inch at 15-degree angle on a clean cream desk. "
        "Screen shows the Budget Tracker page in lavender theme (#8666AA): income row "
        "at top labeled 'INCOME', expense category rows below (HOUSING, FOOD, TRANSPORT, "
        "ENTERTAINMENT), total and savings fields at bottom, some cells filled with "
        "example dollar amounts.\n"
        "FOREGROUND: a small calculator to the right of the iPad.\n"
        "BACKGROUND: a coin purse, a ceramic coffee mug (2 props).\n"
        "LIGHTING: bright clean natural light from the LEFT. 50mm equivalent, eye-level.\n"
        "CONSTRAINT: ONLY iPad + calculator + coin purse + mug. No hands. No text overlays."
    ),
    "DP1027": (
        "SUBJECT: Silver iPad Pro 12.9-inch at 15-degree angle on a light cream desk. "
        "Screen shows a weekly class & study schedule in cotton candy pink (#DE97C6): "
        "class time blocks color-coded by subject, assignment due dates labeled in cells, "
        "study session blocks visible.\n"
        "FOREGROUND: a pencil case partially open to the right of iPad.\n"
        "BACKGROUND: a set of 3 colored highlighters, corner of a textbook spine (2 props).\n"
        "LIGHTING: bright clean daylight from the LEFT. 50mm equivalent, 20-degree angle.\n"
        "CONSTRAINT: ONLY iPad + pencil case + highlighters + textbook corner. No hands."
    ),
    "DP1028": (
        "SUBJECT: Silver iPad Pro 12.9-inch at 15-degree angle on a dark navy desk. "
        "Screen shows the Monthly Budget Breakdown in Midnight Blue (#1B2568): income "
        "section at top with dollar amounts, expense categories below (HOUSING, GROCERIES, "
        "UTILITIES, DINING, SAVINGS), balance calculation field at bottom, some cells "
        "filled with example dollar values.\n"
        "FOREGROUND: a small calculator.\n"
        "BACKGROUND: a dark blue pen, a minimalist coin purse (2 props).\n"
        "LIGHTING: clean cool-toned daylight from the LEFT. 50mm equivalent, eye-level.\n"
        "CONSTRAINT: ONLY iPad + calculator + pen + coin purse. No hands. No text overlays."
    ),
    "DP1029": (
        "SUBJECT: Silver iPad Pro 12.9-inch at 15-degree angle on a warm cream surface. "
        "Screen shows the Weekly Fitness + Meal Planner in Coral Peach (#FD6C49): "
        "workout type and duration fields with example entries (RUNNING, YOGA, WEIGHTS), "
        "water intake tracker bubbles (8 cups, some filled), mood checkboxes ticked, "
        "meal plan grid with example meals (OATMEAL, CHICKEN SALAD, PASTA).\n"
        "FOREGROUND: a protein shaker bottle beside the iPad.\n"
        "BACKGROUND: a pair of white earbuds in their case, a small succulent (2 props).\n"
        "LIGHTING: bright warm morning light from the LEFT. 50mm equivalent, 20-degree angle.\n"
        "CONSTRAINT: ONLY iPad + shaker + earbuds + succulent. No hands. No text overlays."
    ),
}


def generate_planner_listing_photos(
    product_id: str,
    pdf_cover_path: Path,
    pdf_spread_paths: dict[str, Path],
    sticker_sheet_paths: list[Path],
    output_dir: Path,
    client=None,
) -> dict[str, "PhotoResult"]:
    """Generate all 10 standard listing photos for a digital planner product.

    Args:
        product_id: e.g. "DP1026"
        pdf_cover_path: path to the cover PDF page (rendered as PNG/JPG)
        pdf_spread_paths: dict with keys "monthly", "weekly", "habit", "specialty"
                          pointing to rendered PNG images of those planner pages
        sticker_sheet_paths: list of 3 PNG sticker sheet files
        output_dir: where to save photo_01_hero.jpg … photo_10_specialty.jpg
        client: optional pre-built OpenAI client (created fresh if omitted)

    Returns:
        dict mapping slot key → PhotoResult (result.passed, result.out_path, result.issues)
    """
    client = client or _client()
    anchor = STYLE_ANCHORS.get(product_id, "")
    output_dir.mkdir(parents=True, exist_ok=True)

    accent_map = {
        "DP1026": "lavender purple", "DP1027": "cotton candy pink",
        "DP1028": "ice blue",        "DP1029": "coral peach",
    }
    color_theme_map = {
        "DP1026": "Lavender Dreams (purple #8666AA with soft lavender accents)",
        "DP1027": "Cotton Candy (bubblegum pink #DE97C6 with sky blue #97C6DE accents)",
        "DP1028": "Midnight Blue (#1B2568 deep royal blue with ice-blue #7BA7C2 accents)",
        "DP1029": "Coral Peach (#FD6C49 warm coral with peach-gold #F5B878 accents)",
    }
    accent_color = accent_map.get(product_id, "accent")
    color_theme  = color_theme_map.get(product_id, "the product color theme")
    spread_desc  = f"a beautifully designed kawaii planner spread in {color_theme}"

    slot_order = [
        ("slot_01_hero",          "photo_01_hero.jpg",
            [pdf_spread_paths.get("monthly", pdf_cover_path)], "ipad_lifestyle"),
        ("slot_02_whats_included","photo_02_included.jpg",
            [pdf_cover_path], "flat_paper"),
        ("slot_03_monthly",       "photo_03_monthly.jpg",
            [pdf_spread_paths.get("monthly", pdf_cover_path)], "ipad_lifestyle"),
        ("slot_04_weekly",        "photo_04_weekly.jpg",
            [pdf_spread_paths.get("weekly", pdf_cover_path)], "ipad_lifestyle"),
        ("slot_05_stickers",      "photo_05_stickers.jpg",
            (sticker_sheet_paths or [pdf_cover_path])[:3], "sticker_sheet_flat"),
        ("slot_06_how_to",        "photo_06_howto.jpg",
            [pdf_cover_path], "flat_paper"),
        ("slot_07_compatibility", "photo_07_compat.jpg",
            [pdf_cover_path], "flat_paper"),
        ("slot_08_cover_beauty",  "photo_08_cover.jpg",
            [pdf_cover_path], "ipad_lifestyle"),
        ("slot_09_habit_tracker", "photo_09_habit.jpg",
            [pdf_spread_paths.get("habit", pdf_cover_path)], "ipad_lifestyle"),
        ("slot_10_specialty",     "photo_10_specialty.jpg",
            [pdf_spread_paths.get("specialty", pdf_cover_path)], "ipad_lifestyle"),
    ]

    results: dict[str, PhotoResult] = {}

    for slot_key, filename, design_paths, physics_key in slot_order:
        template = PLANNER_SCENE_TEMPLATES.get(slot_key, {})
        raw_scene = template.get("scene", "")

        if slot_key == "slot_10_specialty":
            scene = SPECIALTY_PROMPTS.get(product_id, raw_scene)
        else:
            scene = raw_scene.format(
                spread_description=spread_desc,
                color_theme=color_theme,
                accent_color=accent_color,
                specialty_prompt="",
            )

        full_scene = scene + ("\n\n" + anchor if anchor else "")

        valid_paths = [Path(p) for p in design_paths if p and Path(p).exists()]
        if not valid_paths:
            print(f"  ⚠ Skipping {slot_key} — no valid design file found")
            results[slot_key] = PhotoResult(False, None, 0, ["design file not found"])
            continue

        print(f"\n📸 [{slot_key}] → {filename}")
        results[slot_key] = generate_verified_photo(
            design_paths=valid_paths,
            scene_prompt=full_scene,
            out_path=output_dir / filename,
            physics=physics_key,
            client=client,
        )

    passed = sum(1 for r in results.values() if r.passed)
    total  = len(results)
    print(f"\n{'✅' if passed==total else '⚠️'} {passed}/{total} photos generated → {output_dir}")
    return results


# Absolute, anchored to this file's own location (mirrors tools/image_gen.py's
# _BASE_DIR/_ENV_PATH pattern) — NOT a bare relative "*.env*" open. .env is
# gitignored and does not exist at all in the deployed Railway container, so a
# relative open() only ever worked by coincidence of the process's cwd; it broke
# outright the first time this ran live (FileNotFoundError: [Errno 2] ... '.env'
# — the Create-screen "Generate Lifestyle Photo" crash, 2026-07-14).
_BASE_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = _BASE_DIR / ".env"


def load_env() -> dict:
    """Real credentials, preferring already-set process env vars (how the
    deployed server actually gets them) over parsing .env (a local-dev-only
    convenience file that isn't present in production)."""
    env = dict(os.environ)
    if _ENV_PATH.exists():
        with open(_ENV_PATH) as f:
            for line in f:
                m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
                if m:
                    env.setdefault(m.group(1), m.group(2))
    return env


def _client():
    import openai
    return openai.OpenAI(api_key=load_env()["OPENAI_API_KEY"])


def _prep(path: Path, max_dim: int = INPUT_MAX_DIM) -> io.BytesIO:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = min(max_dim / w, max_dim / h, 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


def _b64(path_or_img) -> str:
    if isinstance(path_or_img, (str, Path)):
        img = Image.open(path_or_img).convert("RGB")
    else:
        img = path_or_img
    img.thumbnail((768, 768), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


# ── Step 1: auto-extract palette (kills color drift) ─────────────────────────
def extract_palette(design_path: Path, n: int = 5) -> list[str]:
    """Dominant colors as hex strings, extracted from the actual file."""
    img = Image.open(design_path).convert("RGB").resize((200, 200))
    quantized = img.quantize(colors=n, method=Image.MEDIANCUT).convert("RGB")
    colors = sorted(quantized.getcolors(200 * 200) or [], reverse=True)[:n]
    return ["#%02X%02X%02X" % c for _, c in colors]


# ── Step 1b: measure canvas facts (kills shape/background judgment errors) ───
def canvas_facts(design_path: Path) -> str:
    """Ground-truth facts about the design file, measured programmatically."""
    img = Image.open(design_path).convert("RGB")
    w, h = img.size
    shape = "square" if abs(w - h) / max(w, h) < 0.05 else f"{w}:{h} rectangular"
    # Background = median of the four corner patches
    px = []
    for cx, cy in [(10, 10), (w - 11, 10), (10, h - 11), (w - 11, h - 11)]:
        patch = img.crop((cx - 8, cy - 8, cx + 8, cy + 8)).resize((1, 1))
        px.append(patch.getpixel((0, 0)))
    bg = tuple(sorted(c[i] for c in px)[len(px) // 2] for i in range(3))
    return (f"the design file canvas is {shape}, and its background color "
            f"(at the canvas corners/edges) is #%02X%02X%02X" % bg)


# ── Step 2: auto-extract text (kills garbled lettering) ──────────────────────
def extract_text(client, design_path: Path) -> str:
    """Every piece of text on the design, read by a vision model once."""
    resp = client.chat.completions.create(
        model=EXTRACT_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text":
                    "List every piece of text visible in this design, exactly as "
                    "written, character for character, one item per line. "
                    "Output only the text items, nothing else."},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{_b64(design_path)}"}},
            ],
        }],
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


# ── Step 3: verification (the automated eyeball) ─────────────────────────────
def verify_render(client, design_paths: list[Path], render: Image.Image,
                  physics_desc: str = "", facts: str = "") -> dict:
    """Compare render against source design(s). Returns {pass: bool, issues: [...]}"""
    content = [{"type": "text", "text":
        "You are a product-photo QA inspector. The FIRST image(s) are the "
        "real product design file(s) a customer downloads. The LAST image is a "
        "marketing lifestyle photo that must show the design faithfully.\n\n"
        f"The physical product is: {physics_desc}\n"
        "Appearance traits described there (e.g. fine matte surface grain, panel "
        "thickness, side edges, metallic lid) are INTENDED and are NOT defects.\n\n"
        "FAIL only on MATERIAL fidelity errors:\n"
        "1. TEXT: any word/number that is wrong, garbled, missing, or invented "
        "(character-level check on dates and small print)\n"
        "2. COLORS: a region changed to a different hue category (e.g. cream became "
        "navy, green became blue). Lighting tint, white balance, mild exposure or "
        "saturation shifts from scene lighting are NORMAL and pass.\n"
        "3. ELEMENTS: missing, added, or redesigned design elements (borders, stars, "
        "icons, edge details)\n"
        f"4. SHAPE — use these measured ground-truth facts, do not judge by eye:\n"
        f"{facts}\n"
        "Fail SHAPE only if the photo's product face clearly contradicts those "
        "facts (e.g. facts say square canvas but the panel is cut into a circle "
        "or the background color region is absent).\n"
        "5. SURFACE: individual letters/shapes sticking UP out of the face as 3D "
        "embossing. The panel itself having thickness, a drop shadow, or the "
        "described surface grain is NORMAL and passes.\n\n"
        "Perspective, viewing angle, scale, lighting, shadows, and scene context "
        "are NEVER issues.\n"
        "IMPORTANT: only report an issue if you can see it CLEARLY and are confident. "
        "If you are uncertain whether something is an issue, do NOT report it — "
        "uncertain observations are not defects.\n"
        'Respond with ONLY JSON: {"pass": true/false, "issues": ["specific issue", ...]}'}]
    for dp in design_paths:
        content.append({"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{_b64(dp)}"}})
    content.append({"type": "image_url", "image_url": {
        "url": f"data:image/jpeg;base64,{_b64(render)}"}})

    resp = client.chat.completions.create(
        model=VERIFY_MODEL,
        messages=[{"role": "user", "content": content}],
        max_tokens=400,
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.M).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"pass": False, "issues": [f"verifier returned unparseable: {raw[:200]}"]}


# ── Main entry: generate with auto-verify + auto-retry ────────────────────────
@dataclass
class PhotoResult:
    passed: bool
    out_path: Path | None
    attempts: int = 0
    issues: list = field(default_factory=list)


def generate_verified_photo(
    design_paths: list[Path],
    scene_prompt: str,
    out_path: Path,
    physics: str = "sign_flat",
    max_attempts: int = MAX_ATTEMPTS,
    client=None,
) -> PhotoResult:
    client = client or _client()
    design_paths = [Path(p) for p in design_paths]
    for p in design_paths:
        if not p.exists():
            raise FileNotFoundError(p)

    # Pre-extract ground truth from the actual files (never hand-typed)
    palette_lines, text_lines, fact_lines = [], [], []
    for i, dp in enumerate(design_paths, 1):
        palette = extract_palette(dp)
        palette_lines.append(f"Design {i} palette (exact): {', '.join(palette)}")
        text = extract_text(client, dp)
        text_lines.append(f"Design {i} contains exactly this text:\n{text}")
        fact_lines.append(f"FACT (measured): for design {i}, {canvas_facts(dp)}. "
                          "The product face is this FULL canvas — same outer shape, "
                          "same background color, edge to edge.")
    print(f"  Extracted palette + text from {len(design_paths)} design(s)")

    n = len(design_paths)
    base_prompt = (
        f"{'This image is' if n == 1 else f'These {n} images are'} the flat design "
        f"graphic{'s' if n > 1 else ''} of a product. Render a single photorealistic "
        f"product photograph where the design appears as {PHYSICS[physics]}\n\n"
        f"Scene: {scene_prompt}\n\n"
        "FIDELITY REQUIREMENTS (most important):\n"
        "- The EXACT design from the input image(s) appears on the product — same "
        "composition, same elements, same edge details. Do not redesign, simplify, "
        "restyle, or invent anything.\n"
        "- The product keeps the FULL canvas of the design including its background "
        "color: a square design file = a square product face, edge to edge. Never "
        "cut the design out into a circle or silhouette shape.\n"
        + "\n".join(fact_lines) + "\n"
        + "\n".join(palette_lines) + "\n"
        + "\n".join(text_lines) + "\n"
        "Every text item must be reproduced character-for-character.\n\n"
        "Photography: professional Etsy product listing photography, square "
        "composition, no text overlays, no hands, no people, no watermarks. "
        "Completely photorealistic."
    )

    # The generate → verify-against-source → feed-corrections-back → retry loop
    # lives in tools/goal_loop.py (run_until_goal). This function just supplies
    # the three product-specific pieces: how to generate a render, how to verify
    # it against the source designs, and what to do with a rejected render.
    from goal_loop import run_until_goal

    # Image engine is swappable (gpt-image-1 deprecates 2026-10-23). Default stays
    # OpenAI; set IMAGE_ENGINE=gemini to drive this same self-verifying loop with
    # Nano Banana (gemini-2.5-flash-image), which is stronger at keeping the exact
    # product across scenes. The verify + retry loop below is engine-agnostic.
    _img_engine = os.getenv("IMAGE_ENGINE", "openai").lower().strip()

    def _generate(correction: str) -> "Image.Image":
        prompt = base_prompt + correction
        print(f"  generating (engine={_img_engine})...")
        if _img_engine == "gemini":
            import image_gen
            raw = image_gen._gemini_edit_bytes(prompt, list(design_paths))
            return Image.open(io.BytesIO(raw)).convert("RGB")
        images = [(f"design_{i}.png", _prep(dp), "image/png")
                  for i, dp in enumerate(design_paths, 1)]
        resp = client.images.edit(
            model="gpt-image-1",
            image=images if n > 1 else images[0],
            prompt=prompt,
            size="1024x1024",
            quality="high",
            input_fidelity="high",
            output_format="png",
        )
        return Image.open(io.BytesIO(
            base64.b64decode(resp.data[0].b64_json))).convert("RGB")

    def _verify(render: "Image.Image") -> dict:
        print("    verifying against source design(s)...")
        return verify_render(client, design_paths, render, PHYSICS[physics],
                             "\n".join(fact_lines))

    def _on_reject(attempt: int, render: "Image.Image", issues: list) -> None:
        reject = out_path.parent.parent / "_rejects" / f"{out_path.stem}_reject{attempt}.jpg"
        reject.parent.mkdir(parents=True, exist_ok=True)
        render.save(reject, "JPEG", quality=90)
        print(f"    ✗ verification failed: {issues}")
        print(f"      rejected render saved for audit: {reject}")

    result = run_until_goal(_generate, _verify, max_attempts=max_attempts,
                            on_reject=_on_reject)

    if result.passed:
        final = result.output.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        final.save(out_path, "JPEG", quality=95, dpi=(300, 300))
        print(f"  ✓ PASSED verification (attempt {result.attempts}) → {out_path}")
        return PhotoResult(True, out_path, result.attempts, [])

    print(f"  ✗ FAILED after {result.attempts} attempts. Issues: {result.issues}")
    print("    → Fall back to pixel-perfect flat lay, or swap to a design that "
          "renders reliably (avoid tiny text / fine repeating geometry).")
    return PhotoResult(False, None, result.attempts, result.issues)


# ── Flat lays: zero perspective → pixel-perfect PIL, never AI-rendered ────────
def build_flat_lay(
    design_paths: list[Path],
    layout: list[tuple[int, int, int]],   # (x, y, size) per design on 2400px canvas
    background: Path | str,               # cached bg image path OR generation prompt
    out_path: Path,
    client=None,
) -> PhotoResult:
    if isinstance(background, Path) and background.exists():
        bg = Image.open(background).convert("RGB").resize(
            (MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)
    else:
        client = client or _client()
        print("  Generating flat-lay background...")
        resp = client.images.generate(
            model="gpt-image-1", prompt=str(background),
            size="1024x1024", quality="high", output_format="png")
        bg = Image.open(io.BytesIO(
            base64.b64decode(resp.data[0].b64_json))).convert("RGB")
        bg = bg.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)

    canvas = bg.convert("RGBA")
    for dp, (x, y, size) in zip(design_paths, layout):
        design = Image.open(dp).convert("RGB").resize((size, size), Image.LANCZOS)
        radius = size // 60
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, size - 1, size - 1], radius=radius, fill=255)
        panel = Image.new("RGBA", (size, size))
        panel.paste(design, (0, 0))
        panel.putalpha(mask)
        pad = size // 12
        shadow = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle(
            [pad, pad, pad + size - 1, pad + size - 1], radius=radius, fill=(0, 0, 0, 90))
        shadow = shadow.filter(ImageFilter.GaussianBlur(size // 80))
        off = size // 90
        canvas.alpha_composite(shadow, (x - pad + off, y - pad + off))
        canvas.alpha_composite(panel, (x, y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "JPEG", quality=95, dpi=(300, 300))
    print(f"  ✓ Flat lay saved (pixel-perfect): {out_path}")
    return PhotoResult(True, out_path, 1, [])


if __name__ == "__main__":
    print(__doc__)
