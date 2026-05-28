#!/usr/bin/env python3
"""
Generate new unique illustrated sticker sheets for each planner.
One sheet at a time — show for approval before proceeding.

Usage:
  python tools/gen_sticker_sheet.py --pid DP1026 --sheet 6
"""
import os, sys, json, base64, urllib.request, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

# ── Sticker sheet prompts per planner ────────────────────────────────────────
# Each sheet: 20-25 distinct kawaii illustrated sticker items
# Style: thick black outline, soft pastel colors, white background,
#        cute facial expressions, scattered layout (not a grid)

SHEET_PROMPTS = {
    'DP1026': {
        6: {
            'name': 'Self-Care & Wellness',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel colors with lavender and purple accents. "
                "Stickers include: a round bath bomb with sparkles and a happy face, a green face mask sheet with cute eyes, a small purple amethyst crystal cluster, "
                "a sprig of lavender with a smiling face, a jade roller with rosy cheeks, a small pink yoga mat rolled up, a round tin of bath salts, "
                "a essential oil dropper bottle in purple, a fluffy cloud-shaped sleep mask with closed eyes, a meditation cushion with a serene face, "
                "a pair of cozy fuzzy socks with hearts, a small herbal tea sachet on a string, a lit aromatherapy candle in a glass jar with a tiny face, "
                "a tiny journal with a heart lock, a small flower crown of daisies, a pink rose in bloom, a moon-shaped soap bar, "
                "a face serum bottle with a sparkle, a warm heating pad with a smiley face, a calming sleep tea mug with ZZZs. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Transparent-looking white background."
            ),
        },
        7: {
            'name': 'Affirmations & Milestones',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel colors with gold and lavender accents. "
                "Stickers include: a golden trophy cup with a star on it and a happy face, a shooting star with sparkle trail, a gold laurel wreath circle, "
                "a magic wand with a star tip sparkling, a hot air balloon with a smiling sun pattern, a small rocket ship blasting off, "
                "a colorful confetti popper bursting, a glowing lightbulb with a cute face, a purple graduation mortarboard cap, "
                "a ribbon award badge that says 'YOU DID IT' in tiny text, a gold medal on a ribbon, an open book with sparkles coming out, "
                "a rainbow arching over fluffy clouds, a heart with little wings, a star cluster with one big center star, "
                "a tiny mountaintop with a flag planted, a crystal gem shaped like a heart, a cheerful sun with rays and a big smile, "
                "a colorful birthday balloon bunch, a four-leaf clover with a happy face. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        8: {
            'name': 'Moon & Celestial',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel lavender, navy and gold colors. "
                "Stickers include: a crescent moon with a sleepy face and small star earring, a full moon with big kawaii eyes and rosy cheeks, "
                "a shooting star with a golden trail, a Saturn-like planet with rings and a happy face, a fluffy cloud with a comet passing through, "
                "a small telescope pointing at stars, a crystal ball on a tiny stand with a galaxy inside, a dream catcher with feathers and beads, "
                "a night owl sitting on a branch with big sleepy eyes, a constellation of dots connected by thin lines in a recognizable shape, "
                "a sun and moon yin-yang style charm, a small glass bottle with a galaxy inside, a star cluster with a big winking star, "
                "a cozy night sky with three stars and a moon, a small aurora ribbon in pink and teal, "
                "a celestial eye with lashes and a star pupil, a tiny hourglass with star sand, a wishing fountain coin with a star, "
                "a cloud with lightning and stars, a lunar calendar circle showing moon phases. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        9: {
            'name': 'Plants & Botanical',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel green, lavender and earth tone colors. "
                "Stickers include: a round terra cotta pot with a smiling succulent, a big monstera leaf with a sleepy face, "
                "a round cactus with pink flowers and rosy cheeks, a tiny mushroom with red cap and white spots and a happy face, "
                "a sunflower with big kawaii eyes, a small daisy bouquet tied with a bow, a green watering can with a flower spout, "
                "a red and white toadstool on green grass, a curling fern frond with a soft expression, a small bonsai tree in a rectangular pot, "
                "a garden snail with a flower-patterned shell, a fuzzy bumblebee with heart-shaped wings, a flower crown of wildflowers, "
                "a seed packet envelope with flower illustration, a small honey jar with a bee on the label, "
                "a sprig of mint leaves with a fresh face, a clover patch with one four-leaf clover, "
                "a hanging air plant in a glass terrarium, a tiny garden trowel with a dirt patch, a morning glory vine with purple flowers. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        10: {
            'name': 'Sweet Treats & Celebration',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel pink, lavender and sweet colors. "
                "Stickers include: a birthday cake slice with a lit candle and a happy face, a tower of three colorful macarons, "
                "a swirled lollipop on a stick with a smiling face, a pink heart-shaped donut with sprinkles, "
                "a strawberry shortcake with a cream topping, a golden croissant with rosy cheeks, "
                "a boba tea cup with a wide straw and a kawaii face on the cup, a round white mochi with a cherry on top, "
                "a round cookie with pink icing and rainbow sprinkles, a swirled soft-serve ice cream cone, "
                "a small layered pudding cup with a cherry, a glass candy jar filled with colorful sweets, "
                "a berry smoothie cup with a straw and a smile, a stack of three fluffy pancakes with syrup dripping, "
                "a slice of cheesecake with a berry, a cupcake with lavender frosting and a star, "
                "a chocolate bar broken in pieces with a happy face, a round waffle with honey and a bee, "
                "a small pie with a star vent on top, a festive confetti cake pop on a stick. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        11: {
            'name': 'Cozy Home',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft warm lavender and cream home decor colors. "
                "Stickers include: a small bookshelf with colorful books and a plant on top, a cozy armchair with a pillow and a sleeping cat, "
                "a record player with a vinyl disc spinning and musical notes, a small easel with a canvas painting on it, "
                "a window frame with a plant on the sill and sun shining through, a string of polaroid photos on a line with mini clips, "
                "a welcome doormat with a flower, a lantern with a glowing candle inside, a cozy desk lamp with a round shade, "
                "a round photo frame with a bow on top, a basket with yarn and knitting needles, a vintage globe on a small stand, "
                "a small vintage suitcase with stickers on it, a floating shelf with small plants and books, "
                "a teapot on a tray with a matching cup, a bread loaf fresh from the oven in a pan, "
                "a cuckoo clock with tiny bird coming out, a decorative wreath of flowers on a door, "
                "a cozy hammock strung between two points, a snow globe with a tiny house scene inside. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
    },
    # DP1027, DP1028, DP1029 prompts will be added after DP1026 is approved
}


def gen_sticker_sheet(pid, sheet_num):
    info = SHEET_PROMPTS[pid][sheet_num]
    name = info['name']
    prompt = info['prompt']

    out_path = os.path.join(ART_DIR, f'{pid}_sticker_sheet_{sheet_num}.jpg')
    print(f"\nGenerating {pid} Sheet {sheet_num}: {name}")
    print(f"Output: {out_path}")

    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
        "output_format": "jpeg"
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"  Saved: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
            return out_path
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(20)
            else:
                print(f"  FAILED: {e}")
                return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', required=True)
    parser.add_argument('--sheet', type=int, required=True)
    args = parser.parse_args()
    gen_sticker_sheet(args.pid, args.sheet)
