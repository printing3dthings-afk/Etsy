#!/usr/bin/env python3
"""
generate_svg_designs.py

Generates complete SVG cut file bundles using gpt-image-1.
Each bundle = 20 designs × (design PNG + SVG trace + 3 product mockups).

Hardcoded rules applied to every design:
  - NO dates, NO years, NO "est.", NO specific numbers — universal buyer appeal
  - Maximum 4 flat colors, crisp edges, vector-art aesthetic
  - All designs work for Cricut Design Space and Silhouette Studio

Output structure per bundle:
  data/svg_bundles/{bundle_id}/
    SVG/            — 20 traced SVG cut files
    PNG/            — 20 high-res design PNGs (300 DPI reference)
    mockups/        — product lifestyle photos (t-shirt, tote, mug)
    listing_photos/ — 10 Etsy listing images
    {bundle_id}_SVG_Bundle.zip — buyer download (SVG + PNG + README)

Usage:
  python tools/generate_svg_designs.py western          # one bundle
  python tools/generate_svg_designs.py western floral_wreath
  python tools/generate_svg_designs.py --all            # all 5 bundles
  python tools/generate_svg_designs.py western --skip-mockups
"""

import re, base64, io, sys, json, zipfile, threading, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import vtracer, cairosvg

BUNDLES_DIR = Path("data/svg_bundles")
BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE = 2400
INPUT_MAX   = 1024


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── DESIGN CATALOG — 5 bundles × 20 designs ──────────────────────────────────
#
# Each bundle has:
#   "title"       — Etsy listing title
#   "style_guide" — injected into every design prompt in this bundle
#   "designs"     — 20 entries, each with "name" and "elements"
#
# RULE: No dates, no years, no "est.", no specific numbers in any design.
# Text must work for every buyer regardless of when they purchased.

BUNDLES = {

    # ── 1. WESTERN / COUNTRY ─────────────────────────────────────────────────
    "western": {
        "title": "Western SVG Bundle | 20 Country Cowgirl Cut Files | Cricut Silhouette | Instant Download",
        "niche": "western country cowgirl",
        "style_guide": {
            "aesthetic": "western cowgirl country rustic",
            "colors": "saddle brown, dusty sage green, golden yellow, warm tan — maximum 4 flat colors",
            "text_style": "bold western serif lettering or rustic hand-lettered script",
            "cut_elements": "cowboy hats, boots, horseshoes, lassos, sunflowers, cacti, lone stars, arrows, rope frames",
        },
        "designs": [
            {"id": "01", "name": "Wild Heart",      "elements": "wide-brim cowboy hat decorated with wildflowers tucked in hatband, 'WILD HEART' bold western lettering, rope lasso frame, small lone star and horseshoe accents"},
            {"id": "02", "name": "Yeehaw",           "elements": "oversized bold 'YEEHAW' western lettering arching over a horseshoe, sunflower accents on each side, starburst in background, small spur at bottom"},
            {"id": "03", "name": "Cowgirl Up",       "elements": "pair of cowboy boots with wildflowers and daisies growing from them, 'COWGIRL UP' in bold arch over boots, lasso rope decorative circle frame"},
            {"id": "04", "name": "Desert Rose",      "elements": "tall saguaro cactus with blooming roses wrapped around it, 'DESERT ROSE' in rustic lettering below, small arrow and star corner accents"},
            {"id": "05", "name": "Prairie Girl",     "elements": "wheat stalks and wildflowers fanning symmetrically, sunburst behind, 'PRAIRIE GIRL' bold lettering centered, tiny arrow chevrons below"},
            {"id": "06", "name": "Southern Soul",    "elements": "full magnolia blossom wreath ring with leaves and buds, 'SOUTHERN SOUL' elegant script inside the wreath, small star at top of ring"},
            {"id": "07", "name": "Rodeo Queen",      "elements": "ornate western crown decorated with horseshoe and rope, 'RODEO QUEEN' in bold arch, sunflower accents at base of crown, lasso swirl below"},
            {"id": "08", "name": "Boot Scootin",     "elements": "single tall cowboy boot with wildflowers and sunflowers spilling out the top, 'BOOT SCOOTIN' bold western font in a curved banner below"},
            {"id": "09", "name": "Blessed Country",  "elements": "simple cross centered, horseshoe arching over the top of the cross, wildflower sprigs on each side, 'BLESSED' in bold arch above"},
            {"id": "10", "name": "Howdy",            "elements": "giant bold 'HOWDY' taking up most of the frame, small cactus icon replacing the O, cowboy hat sitting on top of the H, star accents in corners"},
            {"id": "11", "name": "Free Spirit",      "elements": "dreamcatcher with long flowing feathers, 'FREE SPIRIT' script inside the dreamcatcher ring, small arrow accents on each side, tiny star dots"},
            {"id": "12", "name": "Ranch Wife",       "elements": "barn silhouette centered, large heart shape above the barn roof, wildflowers framing the sides, 'RANCH WIFE' in rustic lettering below"},
            {"id": "13", "name": "Country Roads",    "elements": "winding dirt road disappearing into the horizon, lone tree on each side, sun rays at the top, 'COUNTRY ROADS' curved lettering in an arch"},
            {"id": "14", "name": "Sunflower Farm",   "elements": "windmill centered and tall, two large sunflowers on each side of the windmill, simple fence rail at the bottom, 'SUNFLOWER FARM' banner below", "mono": True},
            {"id": "15", "name": "Wild and Free",    "elements": "large eagle in flight with wings spread wide, mountain silhouette below, 'WILD AND FREE' bold arch lettering above the eagle, star accents"},
            {"id": "16", "name": "Roping Hearts",    "elements": "lasso rope shaped into a large heart, lone star inside the rope heart, 'ROPING HEARTS' script banner below, small horseshoe at the top", "mono": True},
            {"id": "17", "name": "Simple Life",      "elements": "mason jar filled with wildflowers and sunflowers, small butterfly on the rim, 'SIMPLE LIFE' script on a banner ribbon below the jar"},
            {"id": "18", "name": "Good Ol Days",     "elements": "retro oval badge shape, sunburst rays filling the badge background, 'GOOD OL DAYS' bold retro font inside, small stars and checkered border", "mono": True},
            {"id": "19", "name": "True Grit",        "elements": "shield badge with crossed arrows inside, feathers hanging from the bottom of the shield, 'TRUE GRIT' bold carved font in the shield center", "mono": True},
            {"id": "20", "name": "Home Grown",       "elements": "symmetrical leaf and vine wreath ring, small garden trowel and seed packet inside the wreath, 'HOME GROWN' flowing script, tiny carrot and tomato icons"},
        ],
    },

    # ── 2. BOHO FLORAL WREATH ────────────────────────────────────────────────
    "floral_wreath": {
        "title": "Boho Floral Wreath SVG Bundle | 20 Botanical Cut Files | Cricut Silhouette | Instant Download",
        "niche": "boho botanical floral",
        "style_guide": {
            "aesthetic": "boho botanical cottagecore romantic",
            "colors": "dusty blush pink, muted sage green, warm terracotta, cream white — maximum 4 flat colors",
            "text_style": "elegant thin-stroke calligraphy script or delicate serif",
            "cut_elements": "peonies, roses, eucalyptus sprigs, lavender stems, daisies, wildflowers, butterflies, vines, leaves, botanical frames",
        },
        "designs": [
            {"id": "01", "name": "Gather Here",       "elements": "abundant circular wreath of peonies, eucalyptus, lavender, and daisies, 'gather here' elegant calligraphy script inside the ring, tiny butterfly at upper right"},
            {"id": "02", "name": "Wildflower Ring",   "elements": "loose circular ring of mixed wildflowers — coneflowers, black-eyed susans, baby's breath, and clover, small dragonfly accent, airy and open"},
            {"id": "03", "name": "Eucalyptus Crown",  "elements": "minimal elegant wreath of eucalyptus and olive branches only, no flowers, 'home' in simple thin script inside, very clean and modern botanical", "mono": True},
            {"id": "04", "name": "Sunflower Circle",  "elements": "bold sunflower wreath with six large sunflowers alternating with leaves, 'sunshine' small script at center, chunky petal definition for clean cutting"},
            {"id": "05", "name": "Lavender Dreams",   "elements": "circular wreath of lavender stems and small peony buds, two butterflies with open wings in the wreath, 'bloom' script centered inside"},
            {"id": "06", "name": "Garden Party",      "elements": "lush wreath of cabbage roses, ferns, and ranunculus with a flowing ribbon bow at the bottom, no text — purely decorative floral ring"},
            {"id": "07", "name": "Bloom Where Planted","elements": "wildflower wreath ring with roots showing at the bottom as if growing, 'bloom where you are planted' script arching inside the ring in two lines"},
            {"id": "08", "name": "She Blossoms",      "elements": "elegant rectangular botanical frame of roses, eucalyptus, and trailing vines at all four corners, 'she blossoms' calligraphy script centered inside frame"},
            {"id": "09", "name": "Flower Market",     "elements": "tall flower bucket or vase overflowing with mixed cut flowers — sunflowers, roses, tulips, wildflowers — 'flower market' script on a small banner ribbon"},
            {"id": "10", "name": "Pampas and Roses",  "elements": "boho circular wreath with fluffy pampas grass plumes alternating with open roses, dried leaves and small seed pods, 'wild' in thin script inside"},
            {"id": "11", "name": "Morning Glory",     "elements": "vine wreath with morning glory trumpet flowers and curling tendrils winding around the circle, small hummingbird at the top of the ring"},
            {"id": "12", "name": "Wild Garden",       "elements": "loose asymmetrical bouquet arranged in a circle — not a tight wreath but a natural pile of wildflowers with herbs and grass, tied with a ribbon at the bottom"},
            {"id": "13", "name": "Botanical Crown",   "elements": "floral crown arch (half-circle, open at the bottom) of roses, peonies, and trailing greenery — designed to sit on top of text or a monogram letter below", "mono": True},
            {"id": "14", "name": "Honey Bee Garden",  "elements": "wreath of clover flowers and honeycomb hexagons, two bees with detailed wings in the ring, 'sweet life' script centered inside, honeycomb pattern at top"},
            {"id": "15", "name": "Spring Forward",    "elements": "cheerful wreath of tulips, daffodils, and forsythia branches, one small robin bird perched at the bottom of the ring, no text — seasonal botanical"},
            {"id": "16", "name": "Dusty Blooms",      "elements": "dried flower wreath — preserved roses, cotton stems, dried grasses, and seed pods arranged in a round ring, muted palette, 'grateful' delicate script inside"},
            {"id": "17", "name": "Monogram Frame",    "elements": "symmetrical botanical frame with roses and eucalyptus at top corners and trailing vines down the sides, large empty center oval for a monogram letter, elegant", "mono": True},
            {"id": "18", "name": "Garden Gate",       "elements": "romantic arch of climbing roses over a garden gate, the gate is simple with a heart-shaped latch, trailing vines on each side pillar, no text", "mono": True},
            {"id": "19", "name": "Meadow Ring",       "elements": "airy meadow wreath of tall grasses, wildflowers, and small herbs at different heights, one dragonfly and one butterfly in the ring, very light and botanical"},
            {"id": "20", "name": "Forever Blooming",  "elements": "layered mandala-style floral design — a central rose surrounded by rings of petals, leaves, and small flowers getting larger outward, fully symmetrical, intricate", "mono": True},
        ],
    },

    # ── 3. MAMA / MOM LIFE SCRIPTS ───────────────────────────────────────────
    "mama_scripts": {
        "title": "Mama SVG Bundle | 20 Mom Life Cut Files | Cricut Silhouette | Instant Download",
        "niche": "mom life mama quotes",
        "style_guide": {
            "aesthetic": "modern hand-lettered minimalist with floral accents",
            "colors": "deep warm black for text, dusty mauve pink, sage green, cream white — maximum 4 flat colors",
            "text_style": "flowing brush script for main words, clean sans-serif or simple serif for secondary text",
            "cut_elements": "wildflower sprigs, daisy accents, small hearts, stars, leaf sprigs, decorative arches, ribbon banners",
            "forbidden": "NO dates, NO years, NO 'est.', NO specific numbers — universal appeal for all mamas",
        },
        "designs": [
            {"id": "01", "name": "Mama",              "elements": "'Mama' in large flowing brush script, 'always and forever' in small clean sans-serif below, three wildflower sprigs as accents, thin decorative arch above"},
            {"id": "02", "name": "Blessed Mama",      "elements": "'Blessed Mama' bold script in two lines, floral heart shape framing the text with roses and leaves, small cross accent at top"},
            {"id": "03", "name": "Mom Life",          "elements": "'Mom Life' large brush script, small coffee cup icon with steam beside the words, wildflower sprigs on each side, 'is the best life' smaller below"},
            {"id": "04", "name": "World's Best Mom",  "elements": "circular badge design with 'World's Best Mom' text around the outer ring, star burst in center, small trophy icon, laurel leaves at bottom of badge", "mono": True},
            {"id": "05", "name": "Motherhood",        "elements": "'Motherhood' in elegant tall script taking up full height, small botanical sprigs growing off the letters at top and bottom, clean and minimal"},
            {"id": "06", "name": "She is Strong",     "elements": "'She is Strong' in flowing script with 'and Fearless' on a second line, bold floral frame with roses and wildflowers surrounding the text"},
            {"id": "07", "name": "Mama Bear",         "elements": "cute mama bear silhouette with one small cub, pine trees and mountains in simple silhouette background, 'Mama Bear' bold arch lettering above", "mono": True},
            {"id": "08", "name": "Mom Boss",          "elements": "'Mom Boss' bold modern script, decorative crown above the text with small stars, 'getting it done' small italic below, lightning bolt accent"},
            {"id": "09", "name": "Love You to the Moon","elements": "crescent moon with wildflowers growing from it, 'Love You to the Moon' script flowing around the moon in an arch, small stars scattered"},
            {"id": "10", "name": "Favorite People",   "elements": "'My Favorite People Call Me Mom' in flowing script arranged in an oval shape, small heart in center, tiny flower and star accents around the oval edge", "mono": True},
            {"id": "11", "name": "Raising Good Humans","elements": "'Raising Good Humans' in bold clean brush script, two small heart accents, three wildflower sprigs below, simple and clean layout"},
            {"id": "12", "name": "Mom Fuel",          "elements": "large oversized coffee cup or mug with a heart on it, steam swirls forming the words 'Mom Fuel' above, small wildflowers at the mug base"},
            {"id": "13", "name": "Chaos Coordinator", "elements": "'Chaos Coordinator' in bold energetic lettering, small lightning bolts and star bursts scattered around, 'title: Mom' on a ribbon banner below", "mono": True},
            {"id": "14", "name": "Tired but Grateful","elements": "crescent moon and small stars at top, 'Tired but Grateful' in honest brush script, small coffee cup at bottom, wildflower sprig on each side"},
            {"id": "15", "name": "Girl Mama",         "elements": "'Girl Mama' in large script, decorative crown above with small hearts, bow ribbon accent below the text, wildflower sprigs, small butterfly"},
            {"id": "16", "name": "Boy Mama",          "elements": "'Boy Mama' in bold adventure-style script, small arrow accents on each side, tiny football or rocket icon, mountain silhouette, star accents"},
            {"id": "17", "name": "Bonus Mom",         "elements": "'Bonus Mom' in warm flowing script, large heart shape framing the text, small wildflowers and leaves inside the heart, 'extra love' tiny text below"},
            {"id": "18", "name": "Fur Mama",          "elements": "cute dog paw print with a small heart inside, 'Fur Mama' brush script beside or below the paw, small wildflower sprigs, dog bone accent"},
            {"id": "19", "name": "Plant Mama",        "elements": "small collection of houseplant silhouettes — pothos, monstera leaf, cactus, succulent — 'Plant Mama' brush script in an arch above the plants", "mono": True},
            {"id": "20", "name": "Cool Mom",          "elements": "'Cool Mom' in retro-modern bold script, small star and lightning bolt accents, sunglasses icon above the text, 'yeah I'm a cool mom' tiny script below"},
        ],
    },

    # ── 4. RETRO GROOVY ──────────────────────────────────────────────────────
    "retro_groovy": {
        "title": "Retro Groovy SVG Bundle | 20 Vintage 70s Cut Files | Cricut Silhouette | Instant Download",
        "niche": "retro groovy vintage 70s",
        "style_guide": {
            "aesthetic": "1970s retro groovy vintage psychedelic",
            "colors": "golden yellow, warm rust orange, deep sage green, cream white — maximum 4 flat colors, retro-muted palette",
            "text_style": "bold rounded bubble font, groovy retro lettering, or vintage psychedelic typography",
            "cut_elements": "wavy retro lines, sunbursts, peace signs, mushrooms, daisies, rainbows, smiley faces, psychedelic shapes",
            "forbidden": "NO dates, NO years, NO 'est.', NO specific numbers",
        },
        "designs": [
            {"id": "01", "name": "Stay Groovy",       "elements": "bold sunflower with peace sign inside, 'STAY GROOVY' retro bubble font in arch above, flowing wavy lines and small daisy accents around"},
            {"id": "02", "name": "Good Vibes Only",   "elements": "'GOOD VIBES ONLY' in large groovy rounded lettering, retro rainbow arc above the text, sunshine sun with face below, wavy borders"},
            {"id": "03", "name": "Far Out",           "elements": "retro oval badge with 'FAR OUT' bold psychedelic font inside, decorative mushroom and star accents, scalloped badge border, starburst background", "mono": True},
            {"id": "04", "name": "Peace Love Sunshine","elements": "large peace sign, 'PEACE LOVE SUNSHINE' groovy font arranged around the peace symbol, daisy flowers in each segment, sun rays around the border"},
            {"id": "05", "name": "Soul Shine",        "elements": "'SOUL SHINE' bold retro lettering with oversized sunflower replacing the O, wavy retro lines radiating outward, small mushroom and star accents"},
            {"id": "06", "name": "Flower Power",      "elements": "circular wreath made entirely of bold daisy flowers in retro style, 'FLOWER POWER' groovy font centered inside, small peace sign at top of ring"},
            {"id": "07", "name": "Cosmic Dreamer",    "elements": "retro astronaut helmet with a daisy reflected in the visor, 'COSMIC DREAMER' psychedelic arch font above, saturn planet and stars surrounding", "mono": True},
            {"id": "08", "name": "Electric Dreams",   "elements": "'ELECTRIC DREAMS' bold retro font, large lightning bolt replacing a letter, stars and small flowers scattered, wavy frame border, retro badge shape"},
            {"id": "09", "name": "Sunshine Always",   "elements": "large retro sun with face — eyes, smile — 'SUNSHINE ALWAYS' curved bold text around the sun's rays, small clouds at the corners"},
            {"id": "10", "name": "Groovy Baby",       "elements": "'GROOVY BABY' in massive bubble letters filling the entire frame, small mushroom sitting on top of a letter, daisy accents filling the letter counters"},
            {"id": "11", "name": "Chill Vibes",       "elements": "retro wave pattern at bottom, bold sun partially rising from the waves, 'CHILL VIBES' groovy lettering above, small smiley face and star accents"},
            {"id": "12", "name": "Magic Mushroom",    "elements": "large cute retro mushroom with polka dot cap, small stars and sparkles around it, 'MAGIC' script above on an arch, moon crescent behind the mushroom", "mono": True},
            {"id": "13", "name": "Together We Rise",  "elements": "retro raised fist silhouette surrounded by flowers and daisies, 'TOGETHER WE RISE' groovy bold lettering in arch above, wavy peace sign below"},
            {"id": "14", "name": "Born Wild",         "elements": "retro eagle with wings spread wide, 'BORN WILD' bold arch lettering above, lightning bolts on each side, star burst in background, retro badge border", "mono": True},
            {"id": "15", "name": "Ride the Wave",     "elements": "retro surfboard standing upright, large wave curling behind it, 'RIDE THE WAVE' groovy lettering in a curve, sun and small stars above"},
            {"id": "16", "name": "Rock and Roll",     "elements": "electric guitar silhouette, lightning bolt replacing the guitar neck, 'ROCK AND ROLL' bold retro font in arch, stars and music note accents", "mono": True},
            {"id": "17", "name": "Wild Child",        "elements": "retro diamond badge shape, small retro van inside the badge, 'WILD CHILD' groovy font around the badge edge, flower and star corner accents"},
            {"id": "18", "name": "Summer Lovin",      "elements": "retro frame of sun rays, 'SUMMER LOVIN' groovy font centered, large daisy on each side, small ice cream cone and wave icons at the bottom"},
            {"id": "19", "name": "Life is Groovy",    "elements": "retro rainbow arch at top, puffy cloud on each end of the rainbow, 'LIFE IS GROOVY' bubble font below the rainbow, small stars and hearts"},
            {"id": "20", "name": "Happy Camper",      "elements": "retro A-frame tent with a mushroom and campfire in front, 'HAPPY CAMPER' groovy arch lettering above, pine trees and stars framing the scene"},
        ],
    },

    # ── 5. DARK FLORAL GOTHIC ────────────────────────────────────────────────
    "dark_floral": {
        "title": "Dark Floral Gothic SVG Bundle | 20 Cut Files | Cricut Silhouette | Instant Download",
        "niche": "dark floral gothic feminine",
        "style_guide": {
            "aesthetic": "dark floral gothic feminine ornate dramatic",
            "colors": "deep black, burgundy wine red, dusty mauve, cream white — maximum 4 flat colors",
            "text_style": "bold gothic arch lettering, ornate serif, or dramatic brush script",
            "cut_elements": "dark roses, thorned vines, ornate frames, crescent moons, moths, ravens, skull accents, gothic arches, candles",
            "forbidden": "NO dates, NO years, NO 'est.', NO specific numbers",
        },
        "designs": [
            {"id": "01", "name": "She is Fierce",     "elements": "two large burgundy roses flanking an ornate gothic arch frame, 'SHE IS FIERCE' bold gothic lettering inside the frame, thorned stems, crescent moon at top, star corner accents"},
            {"id": "02", "name": "Wicked Bloom",      "elements": "decorative skull centered with roses blooming from the eye sockets and crown, thorned vines framing, 'WICKED BLOOM' bold arch font above, very ornate"},
            {"id": "03", "name": "Midnight Garden",   "elements": "crescent moon with dark roses and night-blooming flowers growing from it, two small bats in flight, 'MIDNIGHT GARDEN' elegant gothic script below the moon"},
            {"id": "04", "name": "Queen of Thorns",   "elements": "ornate crown made of twisted thorns and dark roses, 'QUEEN OF THORNS' bold gothic lettering below, roses flanking each side, thorned vine border"},
            {"id": "05", "name": "Dark Beauty",       "elements": "tall elegant ornate gothic frame shape, dark lilies and roses climbing up the frame sides, 'DARK BEAUTY' dramatic script inside the frame on a banner"},
            {"id": "06", "name": "Haunted Flora",     "elements": "twisted gothic vines forming a frame, dark flowers — black roses, night orchids — interspersed, two luna moths with detailed wings, no text — decorative", "mono": True},
            {"id": "07", "name": "Enchanted Rose",    "elements": "single perfect rose centered with magic sparkle stars radiating outward, 'ENCHANTED' dramatic script in an arch above, ornate flourish below the rose stem"},
            {"id": "08", "name": "Black Rose Society","elements": "horizontal banner ribbon at top with 'BLACK ROSE SOCIETY' carved gothic font, three black roses below the banner with thorned stems crossing, vine border"},
            {"id": "09", "name": "Thorns and Roses",  "elements": "perfectly symmetrical design — mirrored pair of roses with thorned stems that interweave in the center forming a diamond shape, no text, purely decorative"},
            {"id": "10", "name": "Dark Academia",     "elements": "stack of old books with a single rose bookmarked between them, candle dripping wax beside the books, 'DARK ACADEMIA' italic serif arch above, key accent"},
            {"id": "11", "name": "Witchy Blooms",     "elements": "crystal ball centered with dark roses reflected inside, crescent moon above the ball, 'WITCHY BLOOMS' script in an arch, small potion bottle and mushroom accents"},
            {"id": "12", "name": "Luna Moth",         "elements": "large symmetrical luna moth with detailed wing pattern, dark roses and fern fronds filling the lower wing space, moon disk behind the moth head, no text"},
            {"id": "13", "name": "Gothic Garden",     "elements": "ornate iron garden gate with roses climbing the iron bars, raven perched on top of the gate, 'GOTHIC GARDEN' lettering on a stone arch above the gate"},
            {"id": "14", "name": "Death Blooms",      "elements": "beautiful symmetrical botanical frame — dark roses, thorned vines, poisonous belladonna, and night flowers arranged ornately, no text — frame shape for customizing"},
            {"id": "15", "name": "Shadow and Light",  "elements": "sun and moon design split — left half crescent moon with roses, right half sun with roses — joined in the center, 'SHADOW AND LIGHT' gothic arch above"},
            {"id": "16", "name": "Thorn Crown",       "elements": "ornate crown made of twisted thorns, dark rose blooms emerging from between the thorns, dripping candle wax effect at base of crown, no text"},
            {"id": "17", "name": "Night Owl",         "elements": "detailed ornate owl perched on a gothic branch with dark roses, crescent moon behind the owl, 'NIGHT OWL' dramatic gothic font in arch above"},
            {"id": "18", "name": "Raven and Roses",   "elements": "raven in flight centered with wings spread, dark rose border framing the entire design, 'RAVEN' bold gothic font below, feather accents at bottom corners"},
            {"id": "19", "name": "Dark Forest",       "elements": "wolf howling silhouette, twisted gothic forest tree silhouettes on each side, full moon disk behind the wolf, 'DARK FOREST' arch lettering above"},
            {"id": "20", "name": "Femme Fatale",      "elements": "symmetrical design with dark roses framing a decorative mirror or frame shape, 'FEMME FATALE' elegant gothic script, lipstick mark accent, ornate flourishes"},
        ],
    },

}


# ── Prompt templates ──────────────────────────────────────────────────────────
#
# Two templates:
#   DESIGN_PROMPT_TEMPLATE      — multi-color designs (up to 4 flat colors)
#   MONO_DESIGN_PROMPT_TEMPLATE — single-color black on white (classic vinyl cut style)
#
# Each design in BUNDLES may carry "mono": True to use the monochrome template.
# Target: ~4-5 mono designs per 20-design bundle (roughly half/half per CLAUDE.md
# instruction: mix makes the grid more interesting and mirrors real Etsy SVG bundles).

DESIGN_PROMPT_TEMPLATE = """\
Professional SVG cut file design for Cricut and Silhouette cutting machines, \
{aesthetic} style.

Design concept — {name}: {elements}

Style requirements (MUST follow exactly for cut file compatibility):
- Crisp clean edges throughout — NO soft gradients, NO blurs, NO glow effects
- Maximum 4 flat colors: {colors}
- Bold outline stroke (2–3px) around all design elements for clean cutting
- Clean negative space — all shapes clearly defined and separable
- Centered composition with even white space border on all sides
- Square 1:1 format, high contrast vector illustration aesthetic
- {text_style}
- NO dates, NO years, NO 'est.', NO specific numbers anywhere in the design
- No photographic effects, no drop shadows, no textures — pure flat graphic art
- Design must be readable and cuttable at 4 inches wide\
"""

MONO_DESIGN_PROMPT_TEMPLATE = """\
Professional SVG cut file design for Cricut and Silhouette cutting machines, \
{aesthetic} style.

Design concept — {name}: {elements}

Style requirements (MUST follow exactly for cut file compatibility):
- Clean single-color black design on pure white background. No colors. Bold black art, white background.
- Crisp clean edges throughout — NO soft gradients, NO blurs, NO glow effects, NO gray tones
- Bold outline stroke (2–3px) around all design elements for clean vinyl cutting
- Clean negative space — all shapes clearly defined and separable
- Centered composition with even white space border on all sides
- Square 1:1 format, high contrast black-and-white vector illustration aesthetic
- {text_style}
- NO dates, NO years, NO 'est.', NO specific numbers anywhere in the design
- No photographic effects, no drop shadows, no textures — pure flat black graphic art
- Design must be readable and cuttable at 4 inches wide\
"""

MOCKUP_PROMPTS = {

    "tshirt": """\
This image is a flat SVG cut file design — {description}.

Place this exact design as a vinyl heat-transfer print centered on the chest of a \
{shirt_color} classic crew-neck t-shirt. Produce a single photorealistic product \
photograph at professional Etsy catalog quality.

Requirements:
— EXACT design colors and graphic elements preserved accurately on the fabric
— Design centered on chest, approximately 9–10 inches wide
— T-shirt lies perfectly flat on a {surface} surface (flat lay photography)
— Sleeves spread naturally to both sides, shirt relaxed and unwrinkled except natural folds
— Fabric shows natural cotton texture and slight fold shadow
— Photography: soft even overhead diffused light, clean background, subtle fabric shadow for depth

Style: bright clean catalog flat lay photography, square 1:1 composition. \
Design sharp and perfectly readable. Completely photorealistic. \
No hands, no mannequin, no text overlays, no props — just the shirt.\
""",

    "tote": """\
This image is a flat SVG cut file design — {description}.

Place this exact design as a vinyl or screen-print on the front of a natural \
canvas tote bag. Produce a single photorealistic product photograph at professional catalog quality.

Requirements:
— EXACT design colors and graphic elements preserved accurately
— Design centered on bag front, approximately 8–9 inches wide
— Tote bag stands upright on a {surface} surface, handles at the top falling naturally open
— Canvas woven texture clearly visible on the bag fabric
— One simple lifestyle prop: a dried wildflower stem leaning against the bag, or jute twine tied at handle
— Photography: soft natural side-light from the left, warm white balance, gentle shadow to right

Style: lifestyle editorial product photography, clean and bright. Square 1:1 composition. \
Design sharp and readable. Completely photorealistic. No hands, no text overlays.\
""",

    "mug": """\
This image is a flat SVG cut file design — {description}.

Place this exact design as a vinyl decal applied to the side of a clean white \
11oz ceramic coffee mug. Produce a single photorealistic product photograph at professional catalog quality.

Requirements:
— EXACT design colors and graphic elements preserved accurately, with natural cylinder curvature
— Design centered on mug side, facing camera directly, handle facing right
— Mug sits on a {surface} surface, slight ceramic gloss and shine visible
— One small lifestyle prop beside the mug: a small plant sprig or single dried flower stem
— Photography: soft window light from left, warm white balance, gentle shadow to right

Style: cozy editorial lifestyle photography, Etsy bestseller quality. Square 1:1 composition. \
Design sharp and readable on mug surface. Completely photorealistic. No hands, no text overlays.\
""",

}

# Per-bundle mockup settings
BUNDLE_MOCKUP_SETTINGS = {
    "western":       {"shirt_color": "washed denim blue",  "surface": "light warm oak wood",    "mockups": ["tshirt", "tote"]},
    "floral_wreath": {"shirt_color": "soft sage green",    "surface": "cream linen cloth",       "mockups": ["tshirt", "tote", "mug"]},
    "mama_scripts":  {"shirt_color": "heather gray",       "surface": "warm white marble",       "mockups": ["tshirt", "mug"]},
    "retro_groovy":  {"shirt_color": "vintage washed cream","surface": "warm oak wood surface",  "mockups": ["tshirt", "tote"]},
    "dark_floral":   {"shirt_color": "washed black",       "surface": "dark slate stone surface","mockups": ["tshirt", "tote"]},
}


# ── Core generation functions ─────────────────────────────────────────────────

def generate_design_png(client, bundle_id: str, design: dict, bundle_cfg: dict, out_dir: Path) -> Path | None:
    sg = bundle_cfg["style_guide"]
    if design.get("mono"):
        prompt = MONO_DESIGN_PROMPT_TEMPLATE.format(
            aesthetic=sg["aesthetic"],
            name=design["name"],
            elements=design["elements"],
            text_style=sg["text_style"],
        )
    else:
        prompt = DESIGN_PROMPT_TEMPLATE.format(
            aesthetic=sg["aesthetic"],
            name=design["name"],
            elements=design["elements"],
            colors=sg["colors"],
            text_style=sg["text_style"],
        )

    png_path = out_dir / "PNG" / f"{bundle_id}_{design['id']}_{design['name'].lower().replace(' ','_')}.png"
    if png_path.exists():
        print(f"  [SKIP] {png_path.name} already exists")
        return png_path

    for attempt in range(1, 4):
        try:
            r = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024",
                quality="high",
                output_format="png",
                n=1,
            )
            img_bytes = base64.b64decode(r.data[0].b64_json)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img.save(png_path, "PNG")
            print(f"    ✓ PNG: {png_path.name}")
            return png_path
        except Exception as e:
            print(f"    Attempt {attempt} failed (design PNG): {e}")
            if attempt < 3:
                time.sleep(2 ** attempt)
    return None


def trace_to_svg(png_path: Path, svg_path: Path) -> Path | None:
    if svg_path.exists():
        return svg_path
    try:
        img = Image.open(png_path).convert("RGBA").resize((800, 800), Image.LANCZOS)
        tmp = svg_path.parent / f"_tmp_{png_path.stem}.png"
        img.save(tmp, "PNG")
        vtracer.convert_image_to_svg_py(
            str(tmp), str(svg_path),
            colormode="color", hierarchical="stacked", mode="spline",
            filter_speckle=4, color_precision=6, layer_difference=16,
            corner_threshold=60, length_threshold=4.0, max_iterations=10,
            splice_threshold=45, path_precision=3,
        )
        tmp.unlink(missing_ok=True)
        print(f"    ✓ SVG: {svg_path.name} ({svg_path.stat().st_size//1024} KB)")
        return svg_path
    except Exception as e:
        print(f"    ✗ SVG trace failed: {e}")
        return None


def generate_mockup(client, design: dict, design_img: Image.Image, mockup_id: str,
                    bundle_id: str, bundle_cfg: dict, out_dir: Path) -> Path | None:
    settings = BUNDLE_MOCKUP_SETTINGS[bundle_id]
    description = design["elements"][:200]

    prompt = MOCKUP_PROMPTS[mockup_id].format(
        description=description,
        shirt_color=settings["shirt_color"],
        surface=settings["surface"],
    )

    out_path = out_dir / "mockups" / f"{bundle_id}_{design['id']}_{design['name'].lower().replace(' ','_')}_{mockup_id}.jpg"
    if out_path.exists():
        print(f"  [SKIP] {out_path.name}")
        return out_path

    dw, dh = design_img.size
    scale = min(INPUT_MAX / dw, INPUT_MAX / dh, 1.0)
    resized = design_img.resize((int(dw * scale), int(dh * scale)), Image.LANCZOS) if scale < 1.0 else design_img

    buf = io.BytesIO()
    resized.save(buf, "PNG")
    buf.seek(0)

    for attempt in range(1, 4):
        try:
            r = client.images.edit(
                model="gpt-image-1",
                image=("design.png", buf, "image/png"),
                prompt=prompt,
                size="1024x1024",
                quality="high",
                output_format="png",
            )
            buf.seek(0)
            result = Image.open(io.BytesIO(base64.b64decode(r.data[0].b64_json))).convert("RGB")
            result = result.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)
            result.save(out_path, "JPEG", quality=95, dpi=(300, 300))
            print(f"    ✓ {mockup_id}: {out_path.name}")
            return out_path
        except Exception as e:
            print(f"    Attempt {attempt} failed ({mockup_id} mockup): {e}")
            if attempt < 3:
                time.sleep(2 ** attempt)
            buf.seek(0)
    return None


# ── Listing photo builder ─────────────────────────────────────────────────────

def build_hero_grid(png_paths: list[Path], out_path: Path, cols: int = 5) -> Path:
    """Assemble all design PNGs into a 4×5 hero grid for Etsy listing photo 1."""
    cell = 480
    rows = (len(png_paths) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, rows * cell), (250, 248, 245))

    for i, p in enumerate(png_paths):
        img = Image.open(p).convert("RGB").resize((cell - 4, cell - 4), Image.LANCZOS)
        x = (i % cols) * cell + 2
        y = (i // cols) * cell + 2
        canvas.paste(img, (x, y))

    grid = canvas.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)
    grid.save(out_path, "JPEG", quality=95, dpi=(300, 300))
    print(f"  ✓ Hero grid: {out_path.name}")
    return out_path


def build_spotlight_grid(png_paths: list[Path], out_path: Path, count: int = 4) -> Path:
    """2×2 grid of the first 4 designs for listing photo 2."""
    cell = MOCKUP_SIZE // 2
    canvas = Image.new("RGB", (MOCKUP_SIZE, MOCKUP_SIZE), (250, 248, 245))
    for i, p in enumerate(png_paths[:count]):
        img = Image.open(p).convert("RGB").resize((cell - 6, cell - 6), Image.LANCZOS)
        x = (i % 2) * cell + 3
        y = (i // 2) * cell + 3
        canvas.paste(img, (x, y))
    canvas.save(out_path, "JPEG", quality=95, dpi=(300, 300))
    print(f"  ✓ Spotlight grid: {out_path.name}")
    return out_path


def build_listing_photos(png_paths: list[Path], mockup_dir: Path, listing_dir: Path) -> list[Path]:
    """Assemble 10 Etsy listing photos from generated assets."""
    listing_dir.mkdir(parents=True, exist_ok=True)
    photos = []

    # Photo 1 — hero grid of all 20 designs
    p = listing_dir / "01_all_designs_grid.jpg"
    photos.append(build_hero_grid(png_paths, p))

    # Photo 2 — spotlight 2×2 of first 4 designs
    p = listing_dir / "02_spotlight_designs.jpg"
    photos.append(build_spotlight_grid(png_paths, p))

    # Photos 3–8 — product mockups (pick best available)
    mockup_files = sorted(mockup_dir.glob("*.jpg"))
    t_shirts = [m for m in mockup_files if "tshirt" in m.name]
    totes    = [m for m in mockup_files if "tote" in m.name]
    mugs     = [m for m in mockup_files if "mug" in m.name]

    slot = 3
    for src_list, label in [(t_shirts, "tshirt"), (totes, "tote"), (mugs, "mug")]:
        for i, src in enumerate(src_list[:2]):
            dst = listing_dir / f"{slot:02d}_{label}_{i+1}.jpg"
            dst.write_bytes(src.read_bytes())
            photos.append(dst)
            slot += 1
            if slot > 9:
                break
        if slot > 9:
            break

    # Photo 10 — second 4-design spotlight (designs 5–8)
    p = listing_dir / "10_more_designs.jpg"
    photos.append(build_spotlight_grid(png_paths[4:8], p))

    return photos


# ── ZIP builder ───────────────────────────────────────────────────────────────

README_TEMPLATE = """\
{bundle_name}
{count} SVG Cut File Designs — OnBrandCraftz

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• SVG/ folder — {count} SVG files for Cricut and Silhouette
• PNG/ folder — {count} high-resolution PNG files (300 DPI)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPATIBLE SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Cricut Design Space
✓ Silhouette Studio
✓ Adobe Illustrator
✓ Inkscape (free)
✓ Canva Pro

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cricut:  Upload SVG → Cricut Design Space → resize to project size → cut
Silhouette: File → Open → select SVG → adjust and cut
Iron-on vinyl: Mirror your design before cutting!
Heat transfer vinyl (HTV): Follow your vinyl manufacturer's temperature guide

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LICENSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Personal use — unlimited personal projects
✓ Small commercial use — sell finished physical items you make (up to 100 units/design)
✗ Not for resale as digital files
✗ Not for use in Print-on-Demand (POD) platforms
✗ Not for sharing, redistributing, or sublicensing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUESTIONS?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email: Printing3dthings@outlook.com
Shop:  etsy.com/shop/onbrandcraftz

Thank you for your purchase! Please leave a review — it helps our small shop grow.
"""


def build_zip(bundle_id: str, bundle_cfg: dict, svg_paths: list[Path],
              png_paths: list[Path], out_dir: Path) -> Path:
    zip_path = out_dir / f"OnBrandCraftz_{bundle_id}_SVG_Bundle.zip"
    readme = README_TEMPLATE.format(
        bundle_name=bundle_cfg["title"],
        count=len(svg_paths),
    )
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", readme)
        for p in svg_paths:
            zf.write(p, f"SVG/{p.name}")
        for p in png_paths:
            zf.write(p, f"PNG/{p.name}")
    kb = zip_path.stat().st_size // 1024
    print(f"  ✓ ZIP: {zip_path.name} ({kb} KB)")
    return zip_path


# ── Main bundle runner ────────────────────────────────────────────────────────

def run_bundle(client, bundle_id: str, skip_mockups: bool = False):
    bundle_cfg = BUNDLES[bundle_id]
    print(f"\n{'='*60}")
    print(f"  Bundle: {bundle_id} — {bundle_cfg['title'][:50]}")
    print(f"{'='*60}\n")

    # Directory structure
    out_dir = BUNDLES_DIR / bundle_id
    (out_dir / "SVG").mkdir(parents=True, exist_ok=True)
    (out_dir / "PNG").mkdir(parents=True, exist_ok=True)
    (out_dir / "mockups").mkdir(parents=True, exist_ok=True)
    (out_dir / "listing_photos").mkdir(parents=True, exist_ok=True)

    png_paths = []
    svg_paths = []

    # Generate all 20 designs — parallel threads (4 at a time to avoid rate limits)
    designs = bundle_cfg["designs"]
    batch_size = 4

    for batch_start in range(0, len(designs), batch_size):
        batch = designs[batch_start:batch_start + batch_size]
        batch_results = [None] * len(batch)

        def gen_design(i, design, result_list=batch_results):
            png = generate_design_png(client, bundle_id, design, bundle_cfg, out_dir)
            result_list[i] = png

        threads = [threading.Thread(target=gen_design, args=(i, d)) for i, d in enumerate(batch)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        png_paths.extend([r for r in batch_results if r])
        time.sleep(1)  # brief pause between batches

    # Trace all PNGs to SVG — sequential (CPU-bound, fast)
    print(f"\n  Tracing {len(png_paths)} designs to SVG...")
    for png_path in png_paths:
        svg_path = out_dir / "SVG" / (png_path.stem + ".svg")
        result = trace_to_svg(png_path, svg_path)
        if result:
            svg_paths.append(result)

    if not skip_mockups:
        # Generate mockups — parallel, 3 at a time
        print(f"\n  Generating mockups...")
        mockup_types = BUNDLE_MOCKUP_SETTINGS[bundle_id]["mockups"]

        mockup_queue = []
        for design in designs:
            design_name = design["name"].lower().replace(" ", "_")
            png_path = out_dir / "PNG" / f"{bundle_id}_{design['id']}_{design_name}.png"
            if not png_path.exists():
                continue
            design_img = Image.open(png_path).convert("RGB")
            for mockup_id in mockup_types:
                mockup_queue.append((design, design_img.copy(), mockup_id))

        batch_size_m = 3
        for batch_start in range(0, len(mockup_queue), batch_size_m):
            batch = mockup_queue[batch_start:batch_start + batch_size_m]
            threads = [
                threading.Thread(
                    target=generate_mockup,
                    args=(client, design, img, mid, bundle_id, bundle_cfg, out_dir)
                )
                for design, img, mid in batch
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            time.sleep(1)

    # Build listing photos
    print(f"\n  Building listing photos...")
    build_listing_photos(png_paths, out_dir / "mockups", out_dir / "listing_photos")

    # Build ZIP
    print(f"\n  Building buyer ZIP...")
    build_zip(bundle_id, bundle_cfg, svg_paths, png_paths, out_dir)

    # Save manifest
    manifest = {
        "bundle_id": bundle_id,
        "title": bundle_cfg["title"],
        "niche": bundle_cfg["niche"],
        "design_count": len(png_paths),
        "svg_count": len(svg_paths),
        "zip_path": str(out_dir / f"OnBrandCraftz_{bundle_id}_SVG_Bundle.zip"),
        "listing_photos_dir": str(out_dir / "listing_photos"),
        "status": "ready_to_publish",
    }
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n  ✓ Bundle complete: {bundle_id}")
    print(f"    {len(png_paths)} designs | {len(svg_paths)} SVGs | {out_dir}")
    return manifest


def main():
    args = sys.argv[1:]
    skip_mockups = "--skip-mockups" in args
    args = [a for a in args if not a.startswith("--")]

    if not args:
        print("Usage: python tools/generate_svg_designs.py <bundle_id> [bundle_id ...]")
        print("       python tools/generate_svg_designs.py --all")
        print(f"\nAvailable bundles: {', '.join(BUNDLES.keys())}")
        return

    run_all = "--all" in sys.argv[1:]
    target_ids = list(BUNDLES.keys()) if run_all else args

    invalid = [b for b in target_ids if b not in BUNDLES]
    if invalid:
        print(f"Unknown bundles: {invalid}")
        return

    env = load_env()
    import openai
    client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])

    for bundle_id in target_ids:
        run_bundle(client, bundle_id, skip_mockups=skip_mockups)

    print("\n✓ All bundles complete.")


if __name__ == "__main__":
    main()
