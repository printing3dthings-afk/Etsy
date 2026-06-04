#!/usr/bin/env python3
"""
Regenerate SVG designs for 4 bundles (Floral, Faith, Graduation, Mom Life).
Steps:
  1. Archive old SVGs
  2. Generate PNG designs via gpt-image-1
  3. Vectorize PNGs → SVGs using vtracer
  4. Run create_svg_product_heroes.py to rebuild hero/grid images and upload
"""

import sys
import os
import time
import json
import base64
import shutil
import subprocess
import urllib.request
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import vtracer
from PIL import Image

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
REPO_ROOT = Path(__file__).parent.parent

if not OPENAI_KEY:
    print("[FATAL] OPENAI_API_KEY not set in .env")
    sys.exit(1)

# ── Bundle Definitions ────────────────────────────────────────────────────────

BUNDLES = {
    "floral": {
        "svg_dir": REPO_ROOT / "data/svg_pack/SVG",
        "designs": [
            {
                "filename": "etsy_01_floral_wreath.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. Large detailed circular floral wreath "
                    "with roses, leaves, and wildflowers. Colorful sage green leaves (#8BA888) and dusty "
                    "rose blooms (#C47C8A) on pure white background. No text. Flat color art only — "
                    "absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean edges. "
                    "Pure white background. Square composition with 15% margin. Professional vinyl cutter "
                    "design quality."
                ),
            },
            {
                "filename": "etsy_02_sunflower_wreath.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Bloom & Grow' in elegant serif font "
                    "centered inside a sunflower wreath. Sunflowers in warm gold, green stems and leaves. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold "
                    "crisp clean edges. Color palette: warm gold #F5C030, sage green #8BA888. Pure white "
                    "background. Square composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "etsy_03_wildflower_bouquet.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Wildflower' in flowing script font with "
                    "a wildflower bouquet below. Pink, lavender, and green flowers with stems. Flat color "
                    "art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean "
                    "edges. Colors: pink #C47C8A, lavender #B8A0C8, sage green #8BA888. Pure white "
                    "background. Square composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "etsy_04_floral_heart.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. Large heart shape formed entirely from "
                    "roses and leaves. Dusty rose #C47C8A and sage green #8BA888 color scheme. No text. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold "
                    "crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "etsy_05_botanical_border.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'She Believed She Could So She Did' in "
                    "three lines of elegant script. Surrounded by botanical sprigs — leaves and small "
                    "flowers on each side. Colors: dusty rose #C47C8A script, sage green #8BA888 botanicals. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold "
                    "crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "etsy_06_mandala_bloom.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. Detailed circular mandala with floral petal "
                    "design. Dusty rose #C47C8A and sage green #8BA888 on white. Geometric floral pattern. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp "
                    "clean edges. Pure white background. Square composition with 15% margin. Professional "
                    "vinyl cutter design quality."
                ),
            },
            {
                "filename": "etsy_07_bloom_quote.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Bloom Where You Are Planted' in bold serif "
                    "font. Floral vine border wrapping the text. Colors: dusty rose #C47C8A, sage green #8BA888. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp "
                    "clean edges. Pure white background. Square composition with 15% margin. Professional "
                    "vinyl cutter design quality."
                ),
            },
            {
                "filename": "etsy_08_gather_floral.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Gather' in large rustic serif font with "
                    "botanical sprig decorations above and below. Simple sage green #8BA888 leaves. Flat "
                    "color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp "
                    "clean edges. Pure white background. Square composition with 15% margin. Professional "
                    "vinyl cutter design quality."
                ),
            },
            {
                "filename": "etsy_09_butterfly_floral.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. Large detailed butterfly with floral wing "
                    "pattern — flowers and leaves forming the wings. Sage green #8BA888 and dusty rose "
                    "#C47C8A. No text. Flat color art only — absolutely no gradients, no shadows, no "
                    "anti-aliasing. Bold crisp clean edges. Pure white background. Square composition with "
                    "15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "etsy_10_monogram_frame.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. Elegant square frame made of intertwined "
                    "botanical vines, roses, and leaves. Empty center for monogram. No text inside frame. "
                    "Colors: dusty rose #C47C8A roses, sage green #8BA888 leaves. Flat color art only — "
                    "absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean edges. Pure "
                    "white background. Square composition with 15% margin. Professional vinyl cutter "
                    "design quality."
                ),
            },
        ],
    },

    "faith": {
        "svg_dir": REPO_ROOT / "data/faith_pack/SVG",
        "designs": [
            {
                "filename": "faith_01_be_still.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Be Still' in large elegant calligraphy "
                    "script. Decorative cross below in antique gold. Navy text #1E3A5F, gold cross #C9A84C. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold "
                    "crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_02_faith_over_fear.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Faith Over Fear' in bold impactful block "
                    "letters. Sunburst rays radiating behind the text. Gold sunburst #C9A84C, navy text "
                    "#1E3A5F. Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. "
                    "Bold crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_03_blessed.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Blessed' in flowing ornate calligraphy. "
                    "Small decorative cross above and stars scattered around. Gold #C9A84C script, navy "
                    "#1E3A5F accents. Flat color art only — absolutely no gradients, no shadows, no "
                    "anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_04_grace_upon_grace.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Grace Upon Grace' centered in two lines "
                    "of elegant serif italic font. Thin decorative botanical line border surrounding it. "
                    "Deep navy #1E3A5F text, antique gold #C9A84C border. Flat color art only — absolutely "
                    "no gradients, no shadows, no anti-aliasing. Bold crisp clean edges. Pure white "
                    "background. Square composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_05_she_is_clothed.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'She Is Clothed in Strength & Dignity' "
                    "arranged in a circular arc badge style. Botanical wreath border. Navy #1E3A5F and gold "
                    "#C9A84C. Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. "
                    "Bold crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_06_with_god.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'With God All Things Are Possible' in "
                    "three-line layout. Bold cross in center background. Sunburst lines around cross. "
                    "Navy #1E3A5F and gold #C9A84C. Flat color art only — absolutely no gradients, no "
                    "shadows, no anti-aliasing. Bold crisp clean edges. Pure white background. Square "
                    "composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_07_joy.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Choose Joy' in large ornate calligraphy "
                    "script. Decorative star burst and dots scattered around the text. Gold #C9A84C accents, "
                    "navy #1E3A5F text. Flat color art only — absolutely no gradients, no shadows, no "
                    "anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_08_pray_first.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Pray First' in bold condensed font inside "
                    "a shield badge shape. Small praying hands silhouette below. Navy #1E3A5F badge, gold "
                    "#C9A84C text and details. Flat color art only — absolutely no gradients, no shadows, "
                    "no anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_09_amazing_grace.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Amazing Grace' in two lines of flowing "
                    "calligraphy. Small cross decorated with laurel leaves on each side. Navy #1E3A5F and "
                    "gold #C9A84C. Flat color art only — absolutely no gradients, no shadows, no "
                    "anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "faith_10_trust.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Trust His Plan' in clean modern sans "
                    "serif font. Compass rose illustration below the text. Navy #1E3A5F and gold #C9A84C. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold "
                    "crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
        ],
    },

    "graduation": {
        "svg_dir": REPO_ROOT / "data/grad_pack/SVG",
        "designs": [
            {
                "filename": "grad_01_class_of_2026.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Class of 2026' in large bold collegiate "
                    "block lettering. Graduation cap with tassel above. Royal blue cap #1E3A8A, gold tassel "
                    "#F5C030, bold black text. Flat color art only — absolutely no gradients, no shadows, "
                    "no anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_02_tassel_worth.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'The Tassel Was Worth The Hassle' in "
                    "curved arc text around graduation cap and diploma illustration. Gold #F5C030 and "
                    "royal blue #1E3A8A. Flat color art only — absolutely no gradients, no shadows, no "
                    "anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_03_future_bright.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'The Future Is Bright' in bold modern "
                    "font. Sunglasses icon below text — stylish sunglasses with star reflections. Royal "
                    "blue #1E3A8A and bright gold #F5C030. Flat color art only — absolutely no gradients, "
                    "no shadows, no anti-aliasing. Bold crisp clean edges. Pure white background. Square "
                    "composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_04_senior_2026.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Senior 2026' in large athletic block "
                    "letters. Stars and lightning bolt accent elements. Bold royal blue #1E3A8A and gold "
                    "#F5C030. Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. "
                    "Bold crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_05_she_did_it.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'She Did It' in large celebratory script "
                    "font. Confetti shapes and stars scattered around text. Royal blue #1E3A8A, gold "
                    "#F5C030, and black. Flat color art only — absolutely no gradients, no shadows, no "
                    "anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_06_grad_mode_on.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Grad Mode: ON' inside a bold hexagon "
                    "badge shape. Toggle switch ON design element below the text. Royal blue #1E3A8A "
                    "badge, bright gold #F5C030 text and toggle. Flat color art only — absolutely no "
                    "gradients, no shadows, no anti-aliasing. Bold crisp clean edges. Pure white "
                    "background. Square composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_07_level_unlocked.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Level Unlocked' in modern bold gaming-style "
                    "font. Achievement star or unlock icon. Bold and graphic. Royal blue #1E3A8A and bright "
                    "gold #F5C030. Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. "
                    "Bold crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_08_diploma_frame.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. Diploma scroll illustration with "
                    "'Congratulations Graduate' text on it. Ribbon bow on diploma. Classic collegiate "
                    "style. Royal blue #1E3A8A and gold #F5C030. Flat color art only — absolutely no "
                    "gradients, no shadows, no anti-aliasing. Bold crisp clean edges. Pure white "
                    "background. Square composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_09_next_chapter.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Next Chapter' in elegant script font. "
                    "Open book illustration below with pages turning. Royal blue #1E3A8A and gold "
                    "#F5C030. Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. "
                    "Bold crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "grad_10_congrats_grad.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Congrats Grad' in large bold banner "
                    "font. Ribbon banner design with star burst explosion. Festive gold #F5C030 and royal "
                    "blue #1E3A8A. Flat color art only — absolutely no gradients, no shadows, no "
                    "anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
        ],
    },

    "mom_life": {
        "svg_dir": REPO_ROOT / "data/mom_life_pack/SVG",
        "designs": [
            {
                "filename": "mom_01_blessed_mama.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Blessed Mama' in large flowing script. "
                    "Small heart with floral accent. Terracotta #E07850 script, mustard #F5C030 accent. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold "
                    "crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_02_coffee_chaos.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Coffee & Chaos' in bold retro font. "
                    "Coffee cup with steam swirls illustration. Terracotta #E07850 and cream. Flat color "
                    "art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean "
                    "edges. Pure white background. Square composition with 15% margin. Professional vinyl "
                    "cutter design quality."
                ),
            },
            {
                "filename": "mom_03_messy_bun.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Messy Bun & Getting Stuff Done' in retro "
                    "badge style with circle frame. Teal #3B8E8A badge background, cream text inside. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold "
                    "crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_04_boy_mom.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Boy Mom' in large bold text. Small "
                    "football and baseball icon decorations. Teal #3B8E8A and navy blue colors. Flat "
                    "color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp "
                    "clean edges. Pure white background. Square composition with 15% margin. Professional "
                    "vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_05_girl_mom.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Girl Mom' in large flowing script. Small "
                    "bow and heart decorations. Terracotta #E07850 palette. Flat color art only — "
                    "absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean edges. Pure "
                    "white background. Square composition with 15% margin. Professional vinyl cutter "
                    "design quality."
                ),
            },
            {
                "filename": "mom_06_mama_bear.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Mama Bear' with cute bear silhouette "
                    "above the text. Bold script font. Mustard yellow #F5C030 main color with dark brown "
                    "outline. Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. "
                    "Bold crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_07_soccer_mom.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Soccer Mom' inside a soccer ball shaped "
                    "circular badge. Black and white hexagon soccer ball pattern forming the badge border. "
                    "Bold sporty font. Teal #3B8E8A accents. Flat color art only — absolutely no gradients, "
                    "no shadows, no anti-aliasing. Bold crisp clean edges. Pure white background. Square "
                    "composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_08_minivan_mama.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Minivan Mama' in retro 1970s style font. "
                    "Small van silhouette below the text. Retro terracotta #E07850 and mustard #F5C030 "
                    "colors. Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. "
                    "Bold crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_09_tired_blessed.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Tired But Blessed' in two-line retro "
                    "layout. Stars and small heart accent elements. Teal #3B8E8A and mustard #F5C030. "
                    "Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold "
                    "crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_10_wine_time.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'It's Wine O'Clock Somewhere' in retro "
                    "font with wine glass silhouette. Deep terracotta #E07850 and cream. Flat color art "
                    "only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean edges. "
                    "Pure white background. Square composition with 15% margin. Professional vinyl cutter "
                    "design quality."
                ),
            },
            {
                "filename": "mom_11_fur_mama.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Fur Mama' in flowing script with paw "
                    "print heart design — paw prints forming a heart shape. Brown #8B6040 and cream "
                    "palette. Flat color art only — absolutely no gradients, no shadows, no anti-aliasing. "
                    "Bold crisp clean edges. Pure white background. Square composition with 15% margin. "
                    "Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_12_hot_mess.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Hot Mess Express' in bold condensed font "
                    "inside a train locomotive badge shape. Mustard #F5C030 and teal #3B8E8A. Flat color "
                    "art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean "
                    "edges. Pure white background. Square composition with 15% margin. Professional vinyl "
                    "cutter design quality."
                ),
            },
            {
                "filename": "mom_13_nap_time.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Nap Time is the Best Time' in flowing "
                    "retro script. Crescent moon and stars decoration. Teal #3B8E8A and cream. Flat color "
                    "art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean "
                    "edges. Pure white background. Square composition with 15% margin. Professional vinyl "
                    "cutter design quality."
                ),
            },
            {
                "filename": "mom_14_motherhood.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Motherhood: Powered by Love, Fueled by "
                    "Coffee' as circular text badge. Coffee cup illustration in center. Terracotta #E07850 "
                    "and mustard #F5C030. Flat color art only — absolutely no gradients, no shadows, no "
                    "anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_15_chaos_coordinator.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Chaos Coordinator' in bold font with "
                    "clipboard checklist icon. Terracotta #E07850 and mustard #F5C030. Flat color art "
                    "only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean "
                    "edges. Pure white background. Square composition with 15% margin. Professional "
                    "vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_16_plant_mama.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Plant Mama' in earthy script font. "
                    "Monstera leaf and small potted plant decoration. Sage green #8BA888 palette with "
                    "terracotta #E07850 pot. Flat color art only — absolutely no gradients, no shadows, "
                    "no anti-aliasing. Bold crisp clean edges. Pure white background. Square composition "
                    "with 15% margin. Professional vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_17_mom_tribe.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Mom Tribe' inside a sunburst circle "
                    "badge. Bold tribal-inspired font. Teal #3B8E8A and mustard gold #F5C030. Flat color "
                    "art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean "
                    "edges. Pure white background. Square composition with 15% margin. Professional vinyl "
                    "cutter design quality."
                ),
            },
            {
                "filename": "mom_18_super_mom.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Super Mom' in comic-book style bold "
                    "lettering with action star burst. Small lightning bolt and star accent shapes. Bold "
                    "and colorful: terracotta #E07850, mustard #F5C030, teal #3B8E8A. Flat color art "
                    "only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp clean "
                    "edges. Pure white background. Square composition with 15% margin. Professional "
                    "vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_19_raising_arrows.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Raising My Arrows' in elegant script. "
                    "Arrow decoration above and below the text. Teal #3B8E8A and mustard #F5C030. Flat "
                    "color art only — absolutely no gradients, no shadows, no anti-aliasing. Bold crisp "
                    "clean edges. Pure white background. Square composition with 15% margin. Professional "
                    "vinyl cutter design quality."
                ),
            },
            {
                "filename": "mom_20_mama_needs_coffee.svg",
                "prompt": (
                    "SVG cut file design for Cricut/Silhouette. 'Mama Needs Coffee' in large retro font. "
                    "Large coffee cup with steam swirls as main illustration above the text. Terracotta "
                    "#E07850 main color, cream white details. Flat color art only — absolutely no gradients, "
                    "no shadows, no anti-aliasing. Bold crisp clean edges. Pure white background. Square "
                    "composition with 15% margin. Professional vinyl cutter design quality."
                ),
            },
        ],
    },
}


# ── Step 1: Archive old SVGs ──────────────────────────────────────────────────

def archive_old_svgs(svg_dir: Path, bundle_name: str):
    archive = svg_dir / "_archive"
    archive.mkdir(exist_ok=True)
    count = 0
    for f in svg_dir.glob("*.svg"):
        dest = archive / f.name
        shutil.move(str(f), str(dest))
        count += 1
    if count > 0:
        print(f"  Archived {count} old SVGs → {archive}")
    else:
        print(f"  No existing SVGs to archive in {svg_dir}")


# ── Step 2: Generate PNG via gpt-image-1 ─────────────────────────────────────

def generate_png(prompt: str, out_path: Path) -> bool:
    """Generate a 1024×1024 PNG via gpt-image-1. Returns True on success."""
    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "medium",
        "output_format": "png",
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_KEY}",
        },
        method="POST",
    )

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            out_path.write_bytes(img_bytes)
            print(f"    Generated PNG: {out_path.name} ({len(img_bytes)//1024} KB)")
            return True
        except Exception as e:
            print(f"    Attempt {attempt+1}/2 failed: {e}")
            if attempt == 0:
                # Simplified retry prompt
                short_prompt = prompt[:300] + " Flat color only. No gradients. White background."
                payload = json.dumps({
                    "model": "gpt-image-1",
                    "prompt": short_prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "medium",
                    "output_format": "png",
                }).encode()
                req = urllib.request.Request(
                    "https://api.openai.com/v1/images/generations",
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OPENAI_KEY}",
                    },
                    method="POST",
                )
                time.sleep(5)
    return False


# ── Step 3: Vectorize PNG → SVG ───────────────────────────────────────────────

def png_to_svg(png_path: Path, svg_path: Path) -> bool:
    """Preprocess PNG and vectorize to SVG. Returns True on success."""
    try:
        # Pre-process: quantize to flat colors for cleaner vectorization
        img = Image.open(str(png_path)).convert("RGB")

        # Quantize to max 8 colors to get flat-color regions
        img_q = img.quantize(colors=8, method=Image.Quantize.FASTOCTREE).convert("RGB")

        # Save preprocessed PNG
        proc_path = png_path.parent / (png_path.stem + "_proc.png")
        img_q.save(str(proc_path))

        # Vectorize with vtracer
        vtracer.convert_image_to_svg_py(
            str(proc_path),
            str(svg_path),
            colormode="color",
            hierarchical="stacked",
            mode="spline",
            filter_speckle=4,
            color_precision=6,
            layer_difference=16,
            corner_threshold=60,
            length_threshold=4.0,
            splice_threshold=45,
            path_precision=3,
        )

        # Clean up temp file
        proc_path.unlink(missing_ok=True)

        if svg_path.exists() and svg_path.stat().st_size > 100:
            print(f"    SVG: {svg_path.name} ({svg_path.stat().st_size // 1024} KB)")
            return True
        else:
            print(f"    [ERROR] SVG output empty or missing: {svg_path}")
            return False

    except Exception as e:
        print(f"    [ERROR] vtracer failed on {png_path.name}: {e}")
        # Try to clean up proc file if it exists
        try:
            proc_path = png_path.parent / (png_path.stem + "_proc.png")
            proc_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False


# ── Main processing loop ──────────────────────────────────────────────────────

def process_bundle(bundle_key: str, bundle: dict) -> dict:
    """Process one bundle. Returns stats dict."""
    svg_dir = bundle["svg_dir"]
    designs = bundle["designs"]

    print(f"\n{'=' * 60}")
    print(f"Bundle: {bundle_key.upper()} ({len(designs)} designs)")
    print(f"SVG dir: {svg_dir}")
    print("=" * 60)

    # Ensure directory exists
    svg_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Archive old SVGs
    print("\nStep 1: Archiving old SVGs …")
    archive_old_svgs(svg_dir, bundle_key)

    # Temp dir for PNGs
    tmp_dir = Path("/tmp") / f"svg_gen_{bundle_key}"
    tmp_dir.mkdir(exist_ok=True)

    stats = {"generated_png": 0, "vectorized": 0, "failed_png": [], "failed_svg": []}

    # Step 2 + 3: Generate PNG then vectorize each design
    for i, design in enumerate(designs):
        filename = design["filename"]
        prompt = design["prompt"]
        svg_path = svg_dir / filename
        png_path = tmp_dir / filename.replace(".svg", ".png")

        print(f"\n  [{i+1}/{len(designs)}] {filename}")

        # Generate PNG
        if not png_path.exists():
            ok = generate_png(prompt, png_path)
        else:
            print(f"    PNG already exists, reusing: {png_path.name}")
            ok = True

        if not ok:
            stats["failed_png"].append(filename)
            print(f"    [SKIP] PNG generation failed for {filename}")
            continue

        stats["generated_png"] += 1

        # Vectorize PNG → SVG
        ok = png_to_svg(png_path, svg_path)
        if ok:
            stats["vectorized"] += 1
        else:
            stats["failed_svg"].append(filename)

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    return stats


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SVG Bundle Regeneration — All 4 Bundles")
    print("=" * 60)

    all_stats = {}

    for bundle_key, bundle in BUNDLES.items():
        stats = process_bundle(bundle_key, bundle)
        all_stats[bundle_key] = stats

    # Print summary
    print(f"\n{'=' * 60}")
    print("GENERATION SUMMARY")
    print("=" * 60)
    total_designs = sum(len(b["designs"]) for b in BUNDLES.values())
    total_generated = sum(s["generated_png"] for s in all_stats.values())
    total_vectorized = sum(s["vectorized"] for s in all_stats.values())

    for bundle_key, stats in all_stats.items():
        n = len(BUNDLES[bundle_key]["designs"])
        print(f"  {bundle_key:15s}: {stats['vectorized']}/{n} SVGs created")
        if stats["failed_png"]:
            print(f"    PNG failures: {stats['failed_png']}")
        if stats["failed_svg"]:
            print(f"    SVG failures: {stats['failed_svg']}")

    print(f"\n  Total: {total_vectorized}/{total_designs} SVGs generated")

    if total_vectorized == 0:
        print("\n[FATAL] No SVGs generated — aborting hero/grid rebuild")
        sys.exit(1)

    # Step 4: Run hero/grid rebuild
    print(f"\n{'=' * 60}")
    print("Step 4: Running create_svg_product_heroes.py …")
    print("=" * 60)

    result = subprocess.run(
        ["python3", "tools/create_svg_product_heroes.py"],
        capture_output=False,
        text=True,
        cwd=str(REPO_ROOT),
    )

    if result.returncode != 0:
        print(f"\n[ERROR] create_svg_product_heroes.py exited with code {result.returncode}")
    else:
        print("\n[OK] create_svg_product_heroes.py completed successfully")

    print("\nDone.")


if __name__ == "__main__":
    main()
