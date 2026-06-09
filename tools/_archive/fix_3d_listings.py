"""
One-shot script: rewrites titles, tags, and descriptions for all 13 3D printed
Etsy listings. Run from the project root: python tools/fix_3d_listings.py
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

# ── Shared description blocks ────────────────────────────────────────────────

_MADE_BLOCK = """
━━━━━━━━━━━━━━━━━━━━━━━━
✨ HOW IT'S MADE
━━━━━━━━━━━━━━━━━━━━━━━━
Each piece is 3D printed to order on our Bambu Lab P1S — a professional-grade
enclosed printer used by print farms worldwide. We use quality filaments and
dialed-in settings on every production run. Minor layer variation is a natural
characteristic of 3D printing and adds to its handmade character.
""".strip()

_SHOP_BLOCK = """
━━━━━━━━━━━━━━━━━━━━━━━━
💛 FROM OUR SMALL SHOP
━━━━━━━━━━━━━━━━━━━━━━━━
OnBrandCraftz is a small family-run shop. Every item is printed to order with care.
If anything is ever not right, message us — we make it right, always.
""".strip()

_COPYRIGHT = """
━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. All designs are original or licensed for commercial resale.
""".strip()

_CUSTOM_COLOR_FAQ = (
    "Q: Can I get a different color?\n"
    "A: Yes! Message us before purchasing with your color request. We stock a wide "
    "range of filament colors and can usually accommodate custom requests at no extra charge."
)

_SHIPPING_FAQ = (
    "Q: How long does shipping take?\n"
    "A: Items are printed to order and ship within 3–5 business days. Standard shipping "
    "adds 3–5 days (USPS First Class / Priority)."
)

# ── Listing definitions ──────────────────────────────────────────────────────

LISTINGS = [

    # ── 1. Desk Pen Holder ────────────────────────────────────────────────────
    {
        "listing_id": 4507783049,
        "title": "3D Printed Desk Pen Holder | Modern Minimalist Desk Organizer | Office Decor | Pencil Holder",
        "tags": [
            "desk pen holder",       # 15
            "pencil holder desk",    # 18
            "desk organizer gift",   # 19
            "3d printed decor",      # 16
            "modern desk decor",     # 17
            "home office gift",      # 15
            "desk accessories",      # 16
            "minimalist office",     # 17
            "teacher gift idea",     # 17
            "pencil cup holder",     # 17
            "back to school",        # 14
            "desk storage gift",     # 17
            "office pen holder",     # 17
        ],
        "description": """\
Keep your desk tidy and your style on point — this modern 3D printed desk pen holder is the minimalist organizer your workspace deserves.

Handmade to order in our small shop using quality PLA filament on a professional-grade Bambu Lab P1S printer. Clean geometric lines look great on any desk — home office, classroom, or studio.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Desk Pen Holder
✅ Dimensions: ~90 × 90 × 100 mm (~3.5 × 3.5 × 4 in)
✅ Material: PLA / PLA+ (matte or silk finish)
✅ Holds: pens, pencils, markers, scissors, stylus, ruler
✅ Message us for custom color before purchasing

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in PLA+ for a smooth, clean surface. Available in matte or silk finish
(silk has a premium sheen). Each piece is inspected before shipping.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Wipe clean with a dry or lightly damp cloth
• Do not submerge in water or put in dishwasher
• Keep away from heat sources above 60°C / 140°F (windowsills in direct sun)

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is it sturdy?
A: Yes — PLA+ is rigid and holds its shape well under normal desk use.

Q: Is it heavy enough not to tip over?
A: Yes — the base is solid and weighted enough for pens and pencils. For very
heavy items like scissors or rulers, we recommend a slightly larger size (message us).

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 2. Regular Can Koozie (Standard 12oz) ─────────────────────────────────
    {
        "listing_id": 4506562262,
        "title": "3D Printed Can Koozie | 12oz Standard Can Cooler Sleeve | Beer Koozie Gift | BBQ Party",
        "tags": [
            "can koozie 12oz",       # 15
            "beer can koozie",       # 15
            "can cooler sleeve",     # 17
            "3d printed gift",       # 15
            "party favor gift",      # 16
            "beer lover gift",       # 15
            "can holder gift",       # 15
            "tailgate gift",         # 13
            "bbq party gift",        # 14
            "groomsmen gift",        # 14
            "husband gift idea",     # 17
            "beer accessories",      # 16
            "novelty koozie",        # 14
        ],
        "description": """\
Keep your beer cold and your style cool — this 3D printed can koozie is the standout gift for every beer lover, BBQ, or tailgate.

Designed in a fun cooler jug style with a built-in handle. Fits standard 12oz cans (Bud Light, Coors, Budweiser, Busch, etc.). Printed to order in our small shop.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Can Koozie (standard 12oz)
✅ Dimensions: 88 × 87 × 116 mm (~3.5 × 3.5 × 4.6 in)
✅ Fits: all standard 12oz cans (does NOT fit slim/tall cans — see our slim koozie listing)
✅ Material: PLA (Silk PLA upgrade available — message us)
✅ Built-in handle and drop-in detent fit

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in quality PLA filament. Lightweight, rigid, and reusable. Silk PLA finish
available on request for a premium metallic sheen at no extra charge.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Hand wash only — do not put in dishwasher
• Do not microwave
• Keep away from prolonged direct heat

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Does it keep drinks cold?
A: It provides mild insulation through the wall thickness. For maximum cold retention,
pre-chill the koozie before use.

Q: Will it fit a White Claw or slim can?
A: No — this fits standard 12oz cans only. For slim cans (White Claw, Red Bull,
Truly), see our Skinny Can Koozie listing.

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 3. Skinny Can Koozie ──────────────────────────────────────────────────
    {
        "listing_id": 4506555435,
        "title": "3D Printed Skinny Can Koozie | Slim Can Cooler Sleeve | White Claw Koozie | Insulated",
        "tags": [
            "skinny can koozie",     # 18
            "slim can koozie",       # 15
            "white claw koozie",     # 17
            "seltzer can koozie",    # 19
            "hard seltzer gift",     # 17
            "slim can cooler",       # 15
            "can koozie gift",       # 15
            "bachelorette gift",     # 17
            "bridesmaid gift",       # 15
            "pool party gift",       # 15
            "girls night gift",      # 16
            "insulated koozie",      # 16
            "summer drink gift",     # 17
        ],
        "description": """\
Your slim cans deserve a koozie too — this 3D printed skinny can koozie keeps White Claws, Red Bulls, and Truly's cold in a grip-friendly flexible sleeve.

Designed with an integrated air-gap insulation layer built into the geometry. Fits all 12oz slim cans (57mm body diameter). Made to order in our small shop in flexible PLA.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Skinny Can Koozie
✅ Fits: 12oz slim cans — White Claw, Red Bull, Truly, Michelob Ultra, High Noon
✅ Dimensions: ~57mm OD × ~125mm tall (interior)
✅ Material: Flexible PLA (grippy, slightly bendy — not rigid)
✅ Insulation: built-in air-gap layer for improved cold retention

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in flexible PLA — slightly softer than standard PLA, which makes it easy to
squeeze cans in and gives a comfortable grip. The air gap is modeled directly into
the wall geometry for real insulation (not just decoration).

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Hand wash only — do not put in dishwasher
• Do not microwave
• Store flat or upright — avoid crushing

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will it fit a standard 12oz (Bud Light, Coors, etc.)?
A: No — this fits slim/sleek cans only. For standard 12oz cans, see our Regular Can
Koozie listing.

Q: Is it reusable?
A: Yes — rinse, dry, and reuse. The flexible PLA is durable for everyday use.

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 4. Planter Pot ───────────────────────────────────────────────────────
    {
        "listing_id": 4506559866,
        "title": "3D Printed Planter Pot | Modern Indoor Plant Pot | Boho Home Decor | Succulent Planter",
        "tags": [
            "3d printed planter",    # 18
            "modern plant pot",      # 16
            "indoor planter pot",    # 18
            "succulent planter",     # 17
            "small plant pot",       # 15
            "desk plant holder",     # 17
            "boho planter pot",      # 16
            "plant lover gift",      # 16
            "minimalist planter",    # 18
            "home decor planter",    # 18
            "herb planter pot",      # 16
            "windowsill planter",    # 18
            "office plant pot",      # 16
        ],
        "description": """\
Give your plants a home they'll love — this modern 3D printed planter pot brings clean geometric style to any shelf, windowsill, or desk.

Printed in PETG for moisture resistance. The mid-century modern ribbed design creates the visual illusion of a pot nestled inside another, with uniform interior width from top to bottom. Perfect for succulents, cacti, herbs, and small houseplants.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Planter Pot
✅ Dimensions: 149 × 149 × 110 mm (~5.9 × 5.9 × 4.3 in) | Interior depth ~101 mm
✅ Material: PETG (moisture-resistant)
✅ No drainage hole (use for succulents, cacti, or with a plastic liner)
✅ Available with drainage hole — message us before purchasing

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in PETG for superior moisture resistance versus standard PLA. PETG won't warp
or soften from occasional watering. For water-holding plants, we recommend using
a plastic liner insert or a thin layer of sealant on the interior.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Wipe exterior with a damp cloth
• Avoid leaving standing water inside for extended periods without a liner
• Safe for succulents and cacti with minimal watering

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is it waterproof?
A: PETG is moisture-resistant but not fully waterproof due to the layer structure.
For water-retaining plants, use a plastic liner inside or apply a thin interior sealant.

Q: What size plants fit?
A: Works well for 3–4 inch nursery pot plants, small succulents, herbs, and cacti.

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 5. Tea Light Holder Set of 2 ─────────────────────────────────────────
    {
        "listing_id": 4506557906,
        "title": "3D Printed Tea Light Holder Set of 2 | Boho Candle Holder | Multicolor Choice | Home Decor",
        "tags": [
            "tea light holder",      # 16
            "candle holder set",     # 17
            "boho candle holder",    # 18
            "3d printed candle",     # 17
            "tealight holder set",   # 18
            "home decor gift",       # 14
            "boho home decor",       # 14
            "candle holder gift",    # 18
            "table decor gift",      # 16
            "housewarming gift",     # 17
            "centerpiece candle",    # 18
            "cozy home decor",       # 14
            "boho candle set",       # 15
        ],
        "description": """\
Set the mood with a pair of modern boho candle holders — these 3D printed tea light holders add warm, cozy ambiance to any room, shelf, or table setting.

Sold as a set of 2. Dual-use design: one side holds a standard tea light, the other holds a taper candle. Choose your color at checkout or message us for a custom color. Each holder is printed to order in our small shop.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 2× 3D Printed Tea Light Holders
✅ Fits: standard 38–40mm tea light candles (bottom side) OR taper candles (top side)
✅ Material: PLA (decorative / LED use) or PETG (real-flame use — message us)
✅ Choice of colors — message us with your preference

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Default material is PLA — ideal for LED/electric tea lights and decorative use.
For real-flame tea lights or taper candles, we print in PETG which handles the ambient
warmth from a live flame without deforming. Message us to specify PETG before ordering.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Wipe clean with a dry cloth
• Never leave burning candles unattended
• PLA version: use with LED/battery tea lights only
• PETG version: compatible with short-burn real wax tea lights

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Can I use real candles?
A: PLA holders are for LED/electric tea lights only. Order the PETG version (message us)
for real-flame use.

Q: Can I get them in different colors (one of each)?
A: Absolutely — just message us with which two colors you'd like.

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 6. Funny Can Koozie (Puffer Jacket) ──────────────────────────────────
    {
        "listing_id": 4497769840,
        "title": "3D Printed Funny Can Koozie | Puffer Jacket Beer Koozie | Novelty Gift | 12oz Can Cooler",
        "tags": [
            "puffer koozie",         # 13
            "funny can koozie",      # 16
            "novelty beer gift",     # 17
            "funny beer gift",       # 15
            "joke koozie gift",      # 16
            "beer lover gift",       # 15
            "white elephant gift",   # 19
            "gag gift for him",      # 16
            "groomsmen gift",        # 14
            "secret santa gift",     # 17
            "can cooler gift",       # 15
            "birthday gift him",     # 17
            "funny office gift",     # 17
        ],
        "description": """\
Your beer is not going outside without its puffer jacket — this 3D printed puffer jacket can koozie is the most hilarious gift for any beer lover.

Modeled after a miniature puffer jacket complete with puffed panels and built-in handle. Fits standard 12oz cans. The hollow wall panels actually provide mild insulation — fashion AND function. Printed in Silk PLA for a premium sheen that makes the puffer look even more dramatic.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Puffer Jacket Can Koozie
✅ Fits: standard 12oz cans (Bud Light, Coors, Budweiser, etc.)
✅ Does NOT fit slim cans (White Claw, Red Bull) — see our Skinny Koozie listing
✅ Material: Silk PLA (shiny, premium finish)
✅ Built-in handle for easy carrying

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in Silk PLA for a high-shine metallic-looking finish. The 4-wall puffer panel
construction is rigid and holds the jacket silhouette perfectly. The hollow void
panels provide real mild insulation as a bonus.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Hand wash only with mild soap — do not dishwasher
• Do not microwave
• The puffer panels are hollow — do not crush or compress forcefully

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is it a gag gift or actually useful?
A: Both! It legitimately holds your 12oz can and provides mild insulation.
The real value is the absolutely ridiculous look on someone's face when they open it.

Q: What color options are available?
A: Default is Silk Silver. Message us for other Silk PLA colors (gold, copper, black,
blue, rose gold).

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 7. Geometric Table Lamp ───────────────────────────────────────────────
    {
        "listing_id": 4497392795,
        "title": "3D Printed Geometric Table Lamp | Modern Home Decor Accent Light | Desk Lamp | Boho Gift",
        "tags": [
            "geometric table lamp",  # 20 ✅
            "3d printed lamp",       # 15
            "modern table lamp",     # 17
            "desk lamp decor",       # 14
            "home accent lamp",      # 16
            "nightstand lamp",       # 15
            "geometric lamp",        # 14
            "boho desk lamp",        # 14
            "housewarming gift",     # 17
            "bedroom lamp decor",    # 18
            "ambient light decor",   # 19
            "modern home decor",     # 17
            "lamp gift idea",        # 14
        ],
        "description": """\
Cast warm geometric shadows across your room — this modern 3D printed geometric table lamp is the statement accent light your desk, nightstand, or shelf has been missing.

Printed in translucent/white filament so light diffuses softly through the faceted walls. Pairs with the Bambu Lab wired lamp kit (required — see FAQ). Each lamp is printed to order in our small shop.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Geometric Lamp Shade
✅ Material: Translucent PLA or PETG (light-diffusing)
✅ Compatible with: Bambu Lab wired lamp kit (not included — see FAQ)
✅ Cord and bulb: not included (lamp kit contains both)
✅ Custom color available on request

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in translucent or white PLA/PETG so the warm light glows through the wall and
casts a soft patterned shadow. The geometric facets create a dramatic shadow-play effect
on the surrounding walls in a dimmed room.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Dust with a soft dry cloth
• Use only with LED bulbs rated for the lamp kit (typically ≤10W)
• Do not cover with fabric or place near flammable materials

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: What lamp kit do I need?
A: The Bambu Lab Wired Lamp Kit (~$15–20, available on the Bambu Lab website or Amazon).
The shade fits the base precisely — no glue or hardware modification needed.

Q: Can I use a different lamp base?
A: The shade is designed for the Bambu Lab kit. Message us if you have a different base
and we can discuss sizing options.

Q: What room is it best for?
A: Desk, nightstand, shelf, or reading nook. Looks especially dramatic in a dimmed room
where the shadow pattern plays across the wall.

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 8. Table Centerpiece (Boho Arch) ──────────────────────────────────────
    {
        "listing_id": 4497385915,
        "title": "3D Printed Boho Table Centerpiece | Arch Decor Set | Dining Room Decor | Wood Look Gift",
        "tags": [
            "boho table decor",      # 16
            "boho centerpiece",      # 16
            "dining table decor",    # 18
            "3d printed decor",      # 16
            "wood look decor",       # 14
            "arch wall decor",       # 15
            "boho shelf decor",      # 16
            "arch decor set",        # 14
            "housewarming gift",     # 17
            "boho home decor",       # 14
            "rustic table decor",    # 18
            "modern boho decor",     # 17
            "livingroom decor",      # 16
        ],
        "description": """\
Add a sculptural boho moment to your dining table, shelf, or mantle — this 3D printed rainbow arch centerpiece set brings a warm wood-look texture to any space without cutting down a single tree.

Comes as a set of 3 nested arch sizes for a curated layered arrangement. Printed in wood-fill PLA for authentic grain texture and warmth. Each set is printed to order in our small shop.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Set of 3 Arch Centerpieces (Large, Medium, Small)
✅ Large: 225 × 200 × 12 mm | Medium: 160 × 150 × 12 mm | Small: 98 × 95 × 12 mm
✅ Material: Wood-fill PLA (authentic wood grain texture)
✅ Use as: dining table centerpiece, shelf decor, mantle accent, or wall art
✅ Custom color or solid PLA available on request

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in wood-fill PLA — a composite filament that contains real wood fiber, giving
each piece a natural grain texture and warm matte finish. No two pieces have identical
grain patterns. Can be lightly sanded and stained for a fully custom wood finish.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Dust with a dry cloth
• Avoid moisture — wood-fill PLA can swell slightly if soaked
• Do not sand without protective mask (wood composite dust)

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Does it really look like wood?
A: Yes — wood-fill PLA has real wood fiber embedded in the filament. The surface has
a natural grain texture and can be lightly stained. It's the closest 3D printing gets
to real wood without a saw.

Q: Can I hang it on the wall?
A: Yes — the flat back and lightweight design make it easy to hang with a small nail
or Command strip (not included).

Q: Can I get it in a non-wood color?
A: Yes — message us for solid PLA color options (white, black, terracotta, sage green).

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, shipping=_SHIPPING_FAQ,
            shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 9. Tea Light Candle Holder Set (textured / fuzzy skin) ───────────────
    {
        "listing_id": 4492610660,
        "title": "3D Printed Tea Light Candle Holder Set | Boho Textured Candleholder | Home Decor Gift",
        "tags": [
            "tea light holder",      # 16
            "boho candle holder",    # 18
            "candle holder set",     # 17
            "3d printed candle",     # 17
            "tealight candle set",   # 18
            "boho home decor",       # 14
            "housewarming gift",     # 17
            "candle lover gift",     # 17
            "table centerpiece",     # 17
            "bedroom decor gift",    # 18
            "cozy home decor",       # 14
            "modern candle hold",    # 18
            "minimalist candle",     # 17
        ],
        "description": """\
Create a cozy, textured ambiance — this 3D printed boho tea light candle holder set brings an organic, handcrafted feel to any room with its unique fuzzy surface texture.

Each holder features a soft fuzzy-skin surface that catches candlelight beautifully and adds tactile warmth. Fits standard 38–40mm tea lights. Sold as a set. Printed to order in our small shop.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Set of 3D Printed Tea Light Candle Holders
✅ Fits: standard 38–40 mm tea lights
✅ Texture: fuzzy/organic surface finish (unique to 3D printing — adds boho warmth)
✅ Material: PLA+ (LED use) or PLA Marble (for a premium stone-like look)
✅ Custom color available — message us

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed with fuzzy-skin surface mode enabled — a slicer technique that creates a soft,
slightly textured outer surface that looks and feels organic and handcrafted.
Available in PLA Marble (our top pick for the boho look) or any PLA+ color.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Use with LED/electric tea lights only (PLA version)
• Dust gently — the textured surface can collect fine dust
• Wipe with a barely damp cloth; let dry fully before use

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Can I use real wax tea lights?
A: PLA is for LED/electric tea lights only. Message us to upgrade to PETG if you want
to use real-flame wax tea lights.

Q: What is the fuzzy texture — is it flocking or felt?
A: It's achieved through a 3D printing technique called fuzzy skin — the printer
makes tiny surface movements to create a slightly rough, soft-feeling surface. It's
purely the filament material, no coatings or additives.

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 10. Mesh Table Lamp ──────────────────────────────────────────────────
    {
        "listing_id": 4490472707,
        "title": "3D Printed Mesh Table Lamp with Shade | Geometric Bedside Lamp | Modern Home Decor Light",
        "tags": [
            "mesh table lamp",       # 14
            "geometric lamp shade",  # 20 ✅
            "bedside table lamp",    # 18
            "3d printed lamp",       # 15
            "lampshade decor",       # 15
            "modern lamp shade",     # 17
            "ambient light lamp",    # 18
            "boho lamp decor",       # 15
            "bedroom lamp gift",     # 17
            "home decor lamp",       # 14
            "nightstand lamp",       # 15
            "desk lamp decor",       # 14
            "housewarming gift",     # 17
        ],
        "description": """\
Let the light dance through the lattice — this 3D printed mesh table lamp casts intricate warm shadow patterns across your walls and creates the perfect reading-nook or nightstand ambiance.

The organic open-lattice mesh diffuses light softly while projecting a web of geometric shadows at night. Requires a standard E27 lamp socket and cord (not included — available at any hardware store for ~$8–12). Printed to order in our small shop.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Mesh Lamp Shade
✅ Dimensions: ~160 × 160 × 242 mm (~6.3 × 6.3 × 9.5 in) — scalable on request
✅ Material: Translucent PLA or PETG (light-diffusing)
✅ Bulb socket: standard E27 (40mm thread) — cord + bulb NOT included
✅ Recommended bulb: Edison/warm LED E27, ≤10W

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in translucent PLA or PETG using an open-lattice structure — no solid infill.
This means the light passes freely through the mesh walls and creates rich shadow
patterns at night. The organic lattice has a handcrafted woven appearance.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Dust with a soft brush — the open lattice can collect fine dust
• Use only with LED bulbs ≤10W to minimize heat buildup
• Do not place near flammable materials

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: What lamp cord / socket do I need?
A: A standard E27 pendant lamp cord with socket (~$8–12 at any hardware store or Amazon).
The shade slides over the socket and sits securely.

Q: Can I use it as a pendant (hanging) lamp?
A: Yes — it works as both a table lamp (on a base) and a pendant (hanging cord). The
open top and bottom make it easy to configure either way.

Q: What bulb should I use?
A: A warm-white LED Edison bulb (E27, 4–8W) gives the best shadow effect. Avoid
high-wattage or cool-white bulbs — warm light makes the shadows beautiful.

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 11. Coffee Bar Cat Sign ───────────────────────────────────────────────
    {
        "listing_id": 4488666558,
        "title": "3D Printed Coffee Bar Sign | Funny Cat Kitchen Decor | Cat Mom Gift | Wall Art Sign",
        "tags": [
            "coffee bar sign",       # 15
            "cat kitchen decor",     # 17
            "funny kitchen sign",    # 18
            "coffee lover gift",     # 17
            "cat lover gift",        # 14
            "kitchen wall decor",    # 18
            "coffee bar decor",      # 16
            "funny cat sign",        # 14
            "home coffee decor",     # 17
            "cat wall art sign",     # 16
            "funny wall decor",      # 16
            "coffee bar gift",       # 15
            "cat mom gift",          # 13
        ],
        "description": """\
Because your coffee bar deserves a cat and a little attitude — this 3D printed funny coffee bar sign is the perfect addition to any kitchen, coffee nook, or home café.

Printed in two colors using our multi-color AMS system for bold, layered text and graphics. Lightweight and easy to hang. Made to order in our small shop.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Coffee Bar Sign (cat design)
✅ Two-tone color (see photos for current colorway — message us for custom color combo)
✅ Mounting: small mounting hole on back for nail or Command hook (not included)
✅ Material: PLA (2-color)
✅ Scalable size — message us if you want a larger or smaller version

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in two-color PLA using our Bambu Lab AMS system — this means the text and
graphic layer colors are cleanly distinct with no painting or post-processing. Crisp,
bold results every time.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Wipe with a dry cloth
• Keep away from direct steam or prolonged moisture (kitchen steam over time)
• If dust collects in the lettering crevices, use a soft toothbrush

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Can I get a custom color combo?
A: Yes! Message us before purchasing with your preferred background and text colors.
We stock a wide range of PLA colors.

Q: Can I get a different coffee-related saying instead?
A: Send us a message — we can often customize the text for a small fee depending
on the complexity of the lettering.

Q: How do I hang it?
A: There's a small mounting hole on the back. Use a nail, pushpin, or small Command
hook (not included).

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, shipping=_SHIPPING_FAQ,
            shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 12. Ribbed Vase ──────────────────────────────────────────────────────
    {
        "listing_id": 4488532602,
        "title": "3D Printed Ribbed Vase for Dried Flowers | Matte Black Boho Vase | Modern Home Decor",
        "tags": [
            "ribbed vase boho",      # 16
            "dried flower vase",     # 17
            "boho vase decor",       # 14
            "matte black vase",      # 16
            "3d printed vase",       # 15
            "modern boho vase",      # 16
            "pampas grass vase",     # 17
            "flower vase gift",      # 16
            "decorative vase",       # 15
            "minimalist vase",       # 15
            "boho shelf decor",      # 16
            "housewarming gift",     # 17
            "living room decor",     # 17
        ],
        "description": """\
The perfect home for your pampas grass, dried botanicals, and eucalyptus — this 3D printed ribbed matte black vase is the boho accent your shelf has been waiting for.

Weighted base with a modeling clay interior weight for stability with tall dried flower arrangements. Clean vertical ribbing catches light beautifully. Printed to order in matte black PLA in our small shop.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Ribbed Vase
✅ Dimensions: ~195 mm tall × 75 mm diameter (~7.7 × 3 in)
✅ Material: Matte black PLA
✅ Weighted base (modeling clay interior weight for stability)
✅ For dried flowers, pampas grass, and artificial botanicals only (not waterproof)

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in matte black PLA — the matte finish looks premium straight off the printer with
no post-processing. The vertical ribbing is clean and consistent. A modeling clay weight
is added to the base interior post-print for stability with tall, top-heavy arrangements.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• For dried/artificial flowers only — not waterproof
• Dust with a dry cloth
• Do not add water directly — the vase is not sealed

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Can I put fresh flowers in it?
A: No — this vase is for dried/artificial flowers only. It is not waterproof.
For fresh flowers with water, message us about a sealed PETG version.

Q: Will it tip over with tall pampas grass?
A: The modeling clay base weight keeps it stable for most standard pampas grass and
dried botanical arrangements up to ~24 inches tall.

Q: Can I get it in a different color?
A: Yes — matte white, terracotta, sage green, and blush pink are popular alternatives.
Message us before purchasing.

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, shipping=_SHIPPING_FAQ,
            shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },

    # ── 13. Crystal Glow Lamp ─────────────────────────────────────────────────
    {
        "listing_id": 4488477854,
        "title": "3D Printed Crystal Glow Lamp | Faceted RGB Geometric Table Lamp | Boho Bedroom Decor",
        "tags": [
            "crystal glow lamp",     # 17
            "rgb crystal lamp",      # 16
            "faceted table lamp",    # 18
            "3d printed lamp",       # 15
            "crystal night light",   # 19
            "led crystal lamp",      # 16
            "crystal home decor",    # 18
            "rgb night light",       # 15
            "boho crystal lamp",     # 17
            "bedroom night lamp",    # 18
            "crystal decor gift",    # 18
            "housewarming gift",     # 17
            "modern crystal lamp",   # 19
        ],
        "description": """\
Watch the room come alive with prismatic color — this 3D printed faceted crystal glow lamp is the most magical night light you've ever owned.

Translucent PETG crystal formations sit over a wireless RGB puck light (required — see FAQ) and transform any color into a dramatic, faceted crystal glow. No wiring. No complicated setup. Just sit the crystals over the puck and tap the remote.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1× 3D Printed Crystal Lamp Shade (faceted crystal formations)
✅ Material: PETG Translucent Clear (allows RGB light to pass through crystal facets)
✅ Works with: Bambu Lab Wireless RGB Puck Light (not included — see FAQ)
✅ No wiring required — crystals sit directly over the puck light

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 MATERIAL & QUALITY
━━━━━━━━━━━━━━━━━━━━━━━━
Printed in PETG Translucent Clear — the faceted crystal surfaces refract and diffuse
the RGB light for a prismatic effect. The crystals are rigid and stable. Each print
has natural slight variation in clarity that enhances the gem-like appearance.

{made}

━━━━━━━━━━━━━━━━━━━━━━━━
🧼 CARE INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━
• Wipe with a dry or slightly damp cloth
• Do not submerge in water
• The puck light is electronic — follow its manufacturer care instructions

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: What RGB puck light do I need?
A: The Bambu Lab Wireless RGB Puck Light (~$15–20, available on the Bambu Lab website
or Amazon). The crystal shade sits directly over it — no tools or modification needed.

Q: Can I use a different LED puck light?
A: Possibly — message us with the diameter of your puck light and we can confirm
compatibility or adjust the print size.

Q: How do I change colors?
A: The Bambu Lab RGB puck has a remote control and app. Tap through solid colors,
fading modes, and breathing effects — the crystals show every color beautifully.

Q: Is it safe for a bedroom/kid's room?
A: Yes — the puck light runs cool (LED) and the PETG shade does not conduct heat.
Safe for nightstand use.

{color}

{shipping}

{shop}

{copyright}""".format(
            made=_MADE_BLOCK, color=_CUSTOM_COLOR_FAQ,
            shipping=_SHIPPING_FAQ, shop=_SHOP_BLOCK, copyright=_COPYRIGHT),
    },
]

# ── Runner ────────────────────────────────────────────────────────────────────

def main():
    client = EtsyAPIClient()
    total = len(LISTINGS)
    ok = 0
    failed = []

    for i, item in enumerate(LISTINGS, 1):
        lid = item["listing_id"]
        title_preview = item["title"][:60]
        print(f"[{i}/{total}] Updating {lid} — {title_preview}...")
        try:
            client.update_listing(lid, {
                "title": item["title"],
                "tags": item["tags"],
                "description": item["description"],
            })
            print(f"  ✅ Done")
            ok += 1
        except EtsyAPIError as e:
            print(f"  ❌ FAILED: {e}")
            failed.append((lid, str(e)))
        # Etsy rate limit: be polite
        if i < total:
            time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"Results: {ok}/{total} updated successfully")
    if failed:
        print("Failed listings:")
        for lid, err in failed:
            print(f"  {lid}: {err}")

if __name__ == "__main__":
    main()
