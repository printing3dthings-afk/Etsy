"""
apply_listing_updates.py
Writes Etsy listing descriptions (and extends short titles) into the
OnBrandCraftz shop_data.json data store.

Run:  python apply_listing_updates.py
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# LISTING UPDATES
# Keys are Etsy listing IDs (strings).
# Each value may contain:
#   "description" – full listing description (always present)
#   "title"       – only present when the original title was under 130 chars
#                   and needs extending to 130-140 chars
# ──────────────────────────────────────────────────────────────────────────────

LISTING_UPDATES = {

    # ══════════════════════════════════════════════════════════════════════════
    # WALL ART — DIGITAL DOWNLOADS
    # ══════════════════════════════════════════════════════════════════════════

    # 1. Italian Kitchen Print  (118 ch → extend)
    "4509597559": {
        "title": "Italian Kitchen Print | Olive Oil Pasta Wall Art | Foodie Kitchen Decor | Instant Download | Rustic Farmhouse",
        "description": """\
🍝 Turn your kitchen into a love letter to Italy — rustic, warm, and full of flavour!

This Italian Kitchen Print brings the charm of an old-world trattoria straight to your walls. Whether you're a home chef, a pasta devotee, or simply obsessed with olive oil, this foodie wall art is the perfect finishing touch for any kitchen or dining room.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Clean Italian kitchen illustration with olive oil, pasta, and rustic pantry motifs
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 2. Abstract Woman Portrait  (120 ch → extend)
    "4509596017": {
        "title": "Abstract Woman Portrait Print | Feminist Line Art Wall Decor | Botanical Face Art | Instant Download | Bedroom Art",
        "description": """\
🌿 Celebrate the beauty of femininity with flowing lines, botanical grace, and modern minimalist style.

This Abstract Woman Portrait Print is a sophisticated statement piece for any bedroom, living room, or office — a continuous line art illustration of a woman's face entwined with leaves and flowers that radiates quiet confidence.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Elegant black-and-white line art with botanical floral face detail
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 3. Tropical Leaves Print  (123 ch → extend)
    "4509600086": {
        "title": "Tropical Leaves Print | Bold Monstera Palm Wall Art | Botanical Jungle Decor | Instant Download | Boho Living Room",
        "description": """\
🌿 Bring the lush drama of a tropical jungle right into your living room — bold, vibrant, and endlessly refreshing.

This Tropical Leaves Print features oversized monstera and palm leaf artwork in rich, saturated greens that instantly transform any blank wall into a botanical paradise. Perfect for boho, mid-century modern, or maximalist interiors.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Bold monstera and palm leaf botanical illustration in vibrant tropical greens
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 4. Grand Canyon Print  (122 ch → extend)
    "4509593697": {
        "title": "Grand Canyon Print | Vintage National Park Poster Art | WPA Style Retro Wall Decor | Instant Download | Arizona Art",
        "description": """\
🏜️ Capture the epic grandeur of one of America's greatest natural wonders — in vintage WPA style that never goes out of fashion.

This Grand Canyon Print is a bold retro-style national park poster inspired by the iconic Works Progress Administration travel posters of the 1930s and 40s. Rich layered colours and dramatic canyon silhouettes make it a striking focal point for any living room, office, or travel-lover's home.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Vintage WPA-style retro national park poster illustration in rich sunset tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 5. Paris Skyline Print  (122 ch → extend)
    "4509593623": {
        "title": "Paris Skyline Print | Minimalist Eiffel Tower Line Art | City Wall Decor | Instant Download | Paris Gift Travel Art",
        "description": """\
🗼 Bring the romance of Paris home — clean, elegant, endlessly chic.

This Paris Skyline Print is a minimalist line art poster featuring the iconic Eiffel Tower and Parisian skyline in a sleek single-stroke style. The perfect wall art for Francophiles, travel dreamers, and anyone who believes every room looks better with a little Paris in it.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Clean minimalist Eiffel Tower and Paris city line art illustration
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 6. Vintage Botanical Print  (123 ch → extend)
    "4509593487": {
        "title": "Vintage Botanical Print | Antique Herbarium Wall Art | Latin Botanical Decor | Instant Download | Cottagecore Farmhouse",
        "description": """\
🌿 Step into a 19th-century apothecary's garden — timeless botanical beauty for modern walls.

This Vintage Botanical Print captures the meticulous detail of antique herbarium illustrations, complete with Latin plant names and fine-line scientific drawing style. A sophisticated choice for kitchens, libraries, studies, and anyone who loves the cottagecore or farmhouse aesthetic.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Antique-style botanical herbarium illustration with Latin plant name lettering
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 7. Abstract Brushstroke Print  (126 ch → extend)
    "4509598784": {
        "title": "Abstract Brushstroke Print | Blue Terracotta Modern Wall Art | Abstract Home Decor | Instant Download | Gallery Wall Art",
        "description": """\
🎨 Make a bold, modern statement — expressive brushstroke energy that transforms any room into a gallery.

This Abstract Brushstroke Print pairs moody blues with warm terracotta tones in a gestural, free-form composition that works beautifully in living rooms, bedrooms, home offices, or as part of a gallery wall. Contemporary, versatile, and endlessly stylish.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Modern abstract brushstroke art in blue and terracotta tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 8. Moon Phases Print  (119 ch → extend)
    "4509598660": {
        "title": "Moon Phases Print | Celestial Wall Art | Lunar Cycle Astronomy Decor | Instant Download | Boho Witchy Bedroom Poster",
        "description": """\
🌙 Follow the moon — a mystical, celestial print that brings cosmic energy into your sacred space.

This Moon Phases Print illustrates the full lunar cycle in gorgeous gold-on-dark detail, from new moon to full moon and back again. Perfect for boho bedrooms, meditation corners, astrology lovers, and anyone drawn to the witchy, celestial aesthetic that's everywhere right now.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Detailed lunar cycle moon phases illustration with gold and celestial accents
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 9. Minimalist Botanical Line Art  (134 ch ✓ — title fine)
    "4509259354": {
        "description": """\
🌿 Less is more — clean, modern botanical line art that elevates any wall with effortless grace.

This Minimalist Botanical Line Art Print is a refined black-and-white drawing of leaves and plant forms rendered in single, continuous strokes. It pairs beautifully with boho, Japandi, Scandi, and modern farmhouse interiors, and works perfectly on its own or as part of a gallery wall.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Minimalist black-and-white botanical line drawing — no colour fill, clean on white or cream paper
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 10. Watercolor Botanical Print  (134 ch ✓)
    "4509258700": {
        "description": """\
🌸 Soft, dreamy, and utterly gorgeous — watercolor botanical art that makes any room feel like a garden.

This Watercolor Botanical Print features loose, painterly flowers and foliage in the most delicate blush, sage, and cream tones. Ideal for nurseries, bedrooms, living rooms, and as a baby shower gift — anywhere you want a touch of gentle, feminine beauty.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Soft pastel watercolor floral botanical illustration — pink, blush, and sage tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 11. Checkerboard Floral Print  (130 ch ✓)
    "4509258172": {
        "description": """\
✨ Go bold or go home — a maximalist checkerboard floral that turns any wall into a conversation piece.

This Checkerboard Floral Print fuses classic pop art geometry with lush floral illustration for a look that's graphic, daring, and completely unforgettable. Perfect for maximalist bedrooms, eclectic living rooms, or anyone who refuses to blend in.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Bold checkerboard grid with high-contrast floral illustration overlay
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 12. Day of the Dead Skull Print  (135 ch ✓)
    "4509215145": {
        "description": """\
💀 Rich colour, wild pattern, zero apologies — sugar skull wall art that commands the room.

This Day of the Dead Skull Print is a vibrant, maximalist celebration of Día de Muertos iconography, packed with flowers, swirling patterns, and kaleidoscopic colour. A striking choice for eclectic living rooms, Halloween displays, or any space that wants a little dark magic.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Colourful maximalist sugar skull / Día de Muertos folk art illustration
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 13. Classic Muscle Car Print  (135 ch ✓)
    "4509219904": {
        "description": """\
🚗 Raw power, classic style, and the kind of wall art that makes every car guy stop in his tracks.

This Classic Muscle Car Print is a bold, high-contrast illustration of the legendary 1970 Chevelle SS — the perfect tribute to American muscle culture. Whether it's for a man cave, garage, workshop, or office, this print speaks the language of horsepower.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Bold muscle car illustration of the 1970 Chevelle SS in dramatic detail
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 14. Astronaut Space Print  (136 ch ✓)
    "4509214803": {
        "description": """\
🚀 Blast off into a universe of colour — cosmic wall art that sparks wonder in kids and adults alike.

This Astronaut Space Print features a brave little astronaut floating through a swirling nebula of violet, teal, and gold — a vivid, painterly space scene that's equally at home in a child's bedroom, a teen's room, or a sci-fi enthusiast's office.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Colourful astronaut and galaxy nebula illustration in vivid cosmic tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 15. Full Moon Ocean Print  (133 ch ✓)
    "4509219594": {
        "description": """\
🌊 Moody, magnetic, and mesmerising — moonlit ocean art that pulls you in like the tide.

This Full Moon Ocean Print captures the brooding beauty of a moonlit seascape — dark churning waves, a luminous full moon reflected on the water, and an atmosphere that's equal parts haunting and serene. Perfect for dark-aesthetic bedrooms, coastal living rooms, or witchy creative spaces.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Moody moonlit ocean seascape illustration in deep navy, silver, and midnight tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 16. Funny Dog Painting Print  (132 ch ✓)
    "4509214477": {
        "description": """\
🐶 Because every distinguished Golden Retriever deserves a pint — hilarious, gallery-worthy, impossibly charming.

This Funny Dog Painting Print reimagines the beloved Golden Retriever as a distinguished Old Masters portrait subject, sitting regally at a bar with a beer in paw. It's the perfect mix of fine art and absurdist humour — a guaranteed crowd-pleaser for dog lovers, pub enthusiasts, and anyone with a sense of humour.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Whimsical Old Masters-style Golden Retriever at bar oil painting illustration
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 17. Poppy Field Impressionist Print  (138 ch ✓)
    "4509214237": {
        "description": """\
🌺 Lose yourself in a sun-drenched meadow of orange poppies — impressionist beauty that glows off the wall.

This Poppy Field Impressionist Print channels the warmth and movement of Monet's flower fields, with vibrant coral-orange poppies dancing in loose, painterly brushstrokes. A romantic, colourful statement piece for living rooms, bedrooms, dining rooms, or any space that needs a burst of sun.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Impressionist-style poppy field painting in warm coral, orange, and meadow greens
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 18. Mountain Meadow Golden Hour Print  (138 ch ✓)
    "4509214051": {
        "description": """\
🏔️ Chase the golden hour forever — a breathtaking mountain meadow landscape that brings the outdoors inside.

This Mountain Meadow Golden Hour Print bathes a wildflower-filled valley and towering peaks in the warm amber glow of sunset, capturing the exact feeling of standing in the mountains as the last light hits the flowers. A stunning choice for nature lovers, hikers, and anyone who wants their living space to feel expansive and alive.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Golden hour mountain landscape with wildflower meadow in warm sunset tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 19. Japandi Tree and Sun Print  (133 ch ✓)
    "4509218860": {
        "description": """\
🌅 Find stillness in simplicity — Japandi wall art where minimalism meets the quiet beauty of nature.

This Japandi Tree and Sun Print distils the wabi-sabi philosophy into a single, serene image: a lone bare tree against a soft circular sun, rendered in warm earth tones and clean negative space. It's the perfect piece for Japandi, Scandi, or zen-inspired interiors where calm is the goal.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Zen minimalist Japandi tree and sun illustration in warm neutral earth tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 20. White Roses Oil Painting Print  (138 ch ✓)
    "4509213667": {
        "description": """\
🌹 Romance, elegance, and timeless beauty — white roses wall art that turns any bedroom into a sanctuary.

This White Roses Oil Painting Print is a lush, painterly study of creamy white roses in the style of the great floral masters — rich impasto texture, soft candlelight tones, and petals so delicate you can almost smell them. Ideal for cottagecore bedrooms, romantic living rooms, and anyone who believes flowers should always be in season.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Romantic impressionist-style white roses oil painting in soft cream and blush tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 21. She Believed She Could Print  (135 ch ✓)
    "4509213533": {
        "description": """\
✨ For every woman who dared — gold empowerment wall art that reminds you how powerful you really are.

This She Believed She Could Print is a bold, gold-toned motivational quote poster designed to inspire and uplift every single day. Perfect for bedrooms, home offices, dorm rooms, and girls' spaces — and a thoughtful gift for graduates, daughters, and every woman stepping into her power.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Bold gold empowerment quote typography on a clean, elegant background
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 22. Good Things Take Time Print  (137 ch ✓)
    "4509213345": {
        "description": """\
⏳ A gentle reminder for every ambitious, hard-working human: good things take time — and so do you.

This Good Things Take Time Print is a clean, modern minimalist typography poster that delivers its message with quiet confidence. Elegant enough for a home office, warm enough for a bedroom — it's the kind of daily affirmation that actually helps.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Minimalist motivational typography print in a clean, modern font
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 23. Mediterranean Window Print  (131 ch ✓)
    "4509218152": {
        "description": """\
🍋 Sun-drenched walls, the smell of lemons, the blue of the sea — Mediterranean kitchen art that transports you instantly.

This Mediterranean Window Print is a romantic oil-painting-style view through a whitewashed window frame: terracotta rooftops, cascading bougainvillea, teal water shimmering beyond, and a ledge of ripe Amalfi lemons. The ultimate kitchen or dining room art for anyone who dreams of the Italian coast.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Oil-painting-style Mediterranean window scene with Amalfi lemon and coastal view detail
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 24. Pampas Grass Print  (139 ch ✓)
    "4509193237": {
        "description": """\
🌾 Neutral, airy, and endlessly versatile — pampas grass wall art that belongs in every boho home.

This Pampas Grass Print captures the ethereal softness of dried pampas plumes in a muted, neutral palette that works with absolutely any interior: boho, minimalist, coastal, Scandi, or farmhouse. A forever piece for living rooms, bedrooms, and entryways.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Minimalist pampas grass illustration in warm neutral tones — beige, sand, and cream
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 25. Sage and Lavender Botanical Print  (119 ch → extend)
    "4509193231": {
        "title": "Sage and Lavender Botanical Print | Dusty Rose Wall Art | Watercolor Printable Art | Instant Download | Boho Bedroom Decor",
        "description": """\
🌿 Calm, grounded, and beautifully soft — sage and lavender botanical art that makes any room feel like a breath of fresh air.

This Sage and Lavender Botanical Print features a loose, dreamy watercolour arrangement of sage sprigs, dried lavender, and dusty rose blooms in a muted, earthy palette perfect for boho bedrooms, nurseries, bathrooms, and any space that craves quiet botanical beauty.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Watercolour botanical illustration of sage, lavender, and dusty rose in soft muted tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 26. Boho Wildflower Botanical Print  (117 ch → extend)
    "4509198434": {
        "title": "Boho Wildflower Botanical Print | Sage Green Wall Art | Watercolor Printable Art | Instant Download | Boho Bedroom Living Room",
        "description": """\
🌼 Wild, free, and beautifully imperfect — boho wildflower art that brings the meadow inside.

This Boho Wildflower Botanical Print is a loose, expressive watercolour arrangement of wildflowers, grasses, and foliage in soothing sage green, terracotta, and cream tones. It's the kind of art that feels both effortless and intentional — a natural fit for boho bedrooms, living rooms, or any wall that needs a little organic energy.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Loose watercolour wildflower botanical illustration in sage green, cream, and earth tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # 27. Eucalyptus Branch Print  (136 ch ✓)
    "4509198446": {
        "description": """\
🌿 Serene, sculptural, and always in style — eucalyptus botanical art that brings spa-like calm to any room.

This Eucalyptus Branch Print is a crisp, modern botanical illustration of silvery eucalyptus leaves and stems in sage green and cool grey tones. Minimalist enough for Scandi or Japandi interiors, warm enough for boho kitchens and bedrooms — it simply goes with everything.

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital file — 300 DPI, print-ready JPG and/or PDF
✅ Clean eucalyptus branch botanical illustration in sage green and silvery grey tones
✅ Instant download — files available immediately after purchase
✅ Print at home or at any local or online print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINT SIZES (fits standard frames)
━━━━━━━━━━━━━━━━━━━━━━━━
• 5×7" | 8×10" | 11×14" | 16×20" | 18×24" | 24×36"
• Print at home, Staples, FedEx Office, Canvera, Printful, or any local print shop
• Works with any home printer — matte or glossy paper both look great

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will I receive a physical print?
A: No — this is a digital download only. No physical item is shipped. You download and print yourself.

Q: What file format do I get?
A: High-resolution JPG and/or PDF files, ready to print.

Q: Can I resize this?
A: Yes! The files are high-resolution (300 DPI) and can be resized up or down for any standard frame size.

Q: Can I use this commercially?
A: This license is for personal use only. For commercial licensing, please message us.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.\
""",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 3D PRINTED PHYSICAL ITEMS
    # ══════════════════════════════════════════════════════════════════════════

    # 28. Desk Pen Holder  (129 ch → extend)
    "4507783049": {
        "title": "3D Printed Desk Pen Holder | Modern Desktop Organizer | Office Pencil Cup | Teacher Gift | Minimalist Desk Decor | USA Made",
        "description": """\
✏️ Tidy desk, clear mind — a sleek, modern pen holder that makes your workspace look like it has its act together.

This 3D Printed Desk Pen Holder is a minimalist cylindrical pencil cup designed to keep your pens, pencils, markers, and scissors right where you need them. Made to order in Indiana from high-quality PLA, it's a practical and stylish upgrade for any home office, classroom, or desk setup.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Holds standard pens, pencils, markers, scissors, and rulers
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Teachers and educators looking for a practical classroom gift
• Work-from-home professionals upgrading their desk setup
• Students and college dorm dwellers who want a tidy desk

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 29. Regular Can Koozie  (124 ch → extend)
    "4506562262": {
        "title": "3D Printed Regular Can Koozie | 12oz Standard Can Cooler Sleeve | Funny Beer Gift | 4th of July Party Favor | USA Ships Fast",
        "description": """\
🍺 Keep your beer cold and your personality hot — the 3D printed can koozie that's actually a conversation starter.

This 3D Printed Regular Can Koozie fits standard 12oz cans perfectly, keeping drinks cold longer while looking seriously cool. Made in Indiana from durable PLA with a distinctive geometric lattice design, it's a unique alternative to foam koozies — and a gift nobody else will have at the party.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Fits standard 12oz regular cans (Budweiser, Coors, PBR, etc.)
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Beer lovers and backyard BBQ hosts
• Groomsmen, bachelor party guests, and guys' night regulars
• 4th of July, summer parties, tailgates, and holiday gift exchanges

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 30. Skinny Can Koozie  (120 ch → extend)
    "4506555435": {
        "title": "3D Printed Skinny Can Koozie | 12oz Slim Can Cooler Sleeve | Unique Drinkware Gift | Funny Beer Tumbler | USA Ships Fast",
        "description": """\
🥂 Keep your hard seltzer, White Claw, or Truly cold in serious style — a slim can koozie like no other.

This 3D Printed Skinny Can Koozie is custom-sized for 12oz slim cans, hugging the can perfectly with a striking geometric lattice shell that looks great in photos and feels even better in hand. A unique gift for bachelorette parties, summer events, and the seltzer-obsessed people in your life.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Fits 12oz slim/skinny cans (White Claw, Truly, Vizzy, Bud Light Seltzer, etc.)
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Bachelorette party guests and bridal shower attendees
• Hard seltzer and craft beer lovers
• Summer party hosts and beach/pool day enthusiasts

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 31. Planter Pot  (125 ch → extend)
    "4506559866": {
        "title": "3D Printed Planter Pot | Modern Indoor Plant Pot | Minimalist Succulent Planter | Desk Plant Holder | Housewarming Gift USA",
        "description": """\
🌱 Give your little green friends the home they deserve — a modern, minimalist planter that's as good-looking as the plant inside it.

This 3D Printed Planter Pot is a clean, geometric indoor plant pot perfect for succulents, cacti, small herbs, or air plants. The modern design fits seamlessly into any interior style — boho, minimalist, Scandinavian, or contemporary — and makes a wonderful housewarming gift.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Ideal for succulents, small cacti, air plants, or herbs
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Plant parents and succulent collectors
• New homeowners and apartment dwellers looking for unique décor
• Coworkers, teachers, and anyone who appreciates a thoughtful desk gift

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 32. Tea Light Holder Set of 2  (128 ch → extend)
    "4506557906": {
        "title": "3D Printed Tea Light Holder Set of 2 | Boho Candle Holder | Modern Minimalist Home Decor | Multicolor Choice | Housewarming",
        "description": """\
🕯️ Set the mood, light the candles — boho tea light holders that make your home feel like a sanctuary.

This 3D Printed Tea Light Holder Set of 2 features a delicate geometric lattice design that casts beautiful light patterns on your walls when lit. The set pairs perfectly on a mantel, dining table, bookshelf, or windowsill — and comes in multiple colour options to match any décor scheme.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Set of 2 matching tea light holders — fits standard tea light candles
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• New homeowners and apartment decorators
• Candle enthusiasts and cozy home lovers
• Wedding guests, bridal showers, and housewarming parties

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 33. Can Koozie (slim, original listing)  (129 ch → extend)
    "4497769840": {
        "title": "3D Printed Can Koozie | Funny Beer Koozie | Slim Can Cooler Sleeve | Unique Drinkware Gift | Party Favor | Indiana USA Made",
        "description": """\
🍺 Unique, functional, and way cooler than a foam koozie — 3D printed can coolers handmade in Indiana.

This 3D Printed Can Koozie is a slim-can cooler sleeve crafted with a striking geometric lattice design that keeps drinks cold and looks amazing doing it. Whether it's for a party, a gift, or just because you deserve nice things, this is the can koozie upgrade you didn't know you needed.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Fits standard slim/skinny 12oz cans
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Beer and hard seltzer lovers who appreciate unique gifts
• Groomsmen, Father's Day, and birthday gifts for the guy who has everything
• Summer BBQ hosts, tailgaters, and backyard party enthusiasts

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 34. Geometric Table Lamp  (132 ch ✓)
    "4497392795": {
        "description": """\
💡 Light up your room with geometry — a handmade 3D printed table lamp that's as much art as it is light.

This 3D Printed Geometric Table Lamp casts a warm, patterned glow through its faceted geometric shell, creating a stunning ambient light effect that turns any bedroom, living room, or home office into something special. Handmade to order in Indiana, it's a truly one-of-a-kind piece.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Includes light kit (bulb and cord) — ready to plug in
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Interior design lovers and unique home décor collectors
• Bedroom and bedside lamp upgrades for any aesthetic
• Housewarming gifts, birthdays, and holiday gift-giving

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 35. Table Centerpiece  (131 ch ✓)
    "4497385915": {
        "description": """\
🏡 The table piece that starts conversations — a sculptural 3D printed centerpiece that looks custom-made for your home.

This 3D Printed Table Centerpiece is a modern boho sculpture designed to anchor your dining table, coffee table, or kitchen island with geometric elegance. Handmade to order in Indiana, it's the kind of unique, artisan piece you simply won't find at a big box store.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Approx. dimensions listed in photos — designed to sit flat on table surfaces
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• New homeowners and interior décor enthusiasts
• Boho, minimalist, and modern farmhouse home lovers
• Housewarming parties and wedding registry additions

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 36. Tea Light Candle Holder Set (second listing)  (136 ch ✓)
    "4492610660": {
        "description": """\
🕯️ Instant ambiance, zero effort — geometric tea light holders that make your home glow.

This 3D Printed Tea Light Candle Holder Set is a beautiful pair of modern geometric candle holders that scatter warm, patterned light across walls and surfaces when lit. Minimal, sculptural, and endlessly cozy — a perfect accent for any living room, bedroom, or dining table.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Fits standard tea light candles (included or easily sourced)
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Candle and cozy home enthusiasts
• Housewarming and bridal shower guests
• Anyone who loves warm, ambient home lighting

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 37. Mesh Table Lamp with Shade  (135 ch ✓)
    "4490472707": {
        "description": """\
🔆 Sculptural light meets modern minimalism — a 3D printed mesh lamp that's as stunning off as it is on.

This 3D Printed Mesh Table Lamp features an intricate woven mesh shade that creates soft, diffused light and beautiful shadow patterns across your walls. Includes the full light kit — just plug in and enjoy. Handmade to order in Indiana, this lamp is a true statement piece for any bedroom, desk, or living room.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Includes complete light kit (cord, socket, and bulb) — ready to use out of the box
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Minimalist and modern home décor collectors
• Bedroom nightstand and desk lamp upgraders
• Housewarming gifts and unique birthday presents

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 38. Coffee Bar Sign  (129 ch → extend)
    "4488666558": {
        "title": "3D Printed Coffee Bar Sign | Funny Cat Kitchen Decor | Ready to Brew Sign | Coffee Lover Gift | Cat Mom Gift | Housewarming",
        "description": """\
☕ Because your coffee bar deserves a sign as extra as your morning espresso — especially if a cat is involved.

This 3D Printed Coffee Bar Sign is a charming, funny kitchen wall sign that combines coffee culture with cat mom energy in the most delightful way. "Ready to Brew" (or your chosen phrase) in a playful font with a cute cat detail — perfect for coffee stations, kitchen shelves, or any wall that needs a little personality.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Wall-mountable sign with pre-drilled hanging holes
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Coffee lovers and home barista enthusiasts
• Cat moms and cat dads who love a good kitchen pun
• Housewarming parties and anyone setting up a coffee bar station

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 39. Ribbed Vase for Dried Flowers  (135 ch ✓)
    "4488532602": {
        "description": """\
🌾 Your pampas grass finally has the vase it deserves — matte, modern, and impossibly chic.

This 3D Printed Ribbed Vase is designed specifically for dried flowers, pampas grass, and decorative botanicals, with a tall ribbed silhouette and matte finish that looks right at home in any boho, minimalist, or modern interior. No water needed — just style.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Tall ribbed vase design ideal for dried pampas grass, dried flowers, and artificial stems
• Available in matte black and multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Boho and minimalist home décor lovers
• New homeowners and apartment decorators
• Housewarming gifts and shelf-styling enthusiasts

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe. Not suitable for fresh flowers with water.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

    # 40. Crystal Glow Lamp  (132 ch ✓)
    "4488477854": {
        "description": """\
💎 Crystalline light, geometric magic — a faceted glow lamp that makes your room look like a dream.

This 3D Printed Crystal Glow Lamp features a stunning multi-faceted geometric shell that refracts light into prismatic patterns, creating a mesmerising ambient glow perfect for bedrooms, meditation spaces, and aesthetic room setups. Handmade to order in Indiana — a truly one-of-a-kind piece.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 PRODUCT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Material: High-quality PLA filament — durable, lightweight, food-safe contact safe
• Faceted crystal-inspired geometric lamp shade with ambient glow effect
• Includes light kit — ready to plug in and use
• Available in multiple colors — choose at checkout
• Designed and printed in Indiana, USA
• Each piece is made to order — ships within 3–5 business days

━━━━━━━━━━━━━━━━━━━━━━━━
🎁 MAKES A GREAT GIFT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Aesthetic room and bedroom décor enthusiasts
• Crystal and gemstone lovers who want something functional
• Unique housewarming, birthday, and holiday gift recipients

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this made to order?
A: Yes — every piece is printed fresh for you after your order. Ships in 3–5 business days.

Q: What material is it made from?
A: High-quality PLA plastic — lightweight, durable, and available in multiple colors.

Q: Can I request a custom color?
A: Message us before ordering — we're happy to accommodate custom color requests if the filament is in stock.

Q: How do I clean it?
A: Hand wash with mild soap and water. Not dishwasher safe.

━━━━━━━━━━━━━━━━━━━━━━━━
📍 SHIPS FROM INDIANA, USA
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Handmade in the USA.\
""",
    },

}  # END LISTING_UPDATES


# ──────────────────────────────────────────────────────────────────────────────
# APPLY LOGIC
# ──────────────────────────────────────────────────────────────────────────────

STORE_PATH = Path("/home/user/Etsy/data/shop_data.json")
BACKUP_DIR = Path("/home/user/Etsy/data/backups")


def load_store():
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_store(data):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"shop_data_{ts}.json"
    shutil.copy(STORE_PATH, backup_path)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return backup_path


def apply_updates(data, updates):
    listings = data["listings"]
    # Build index by id for fast lookup
    id_to_idx = {l["id"]: i for i, l in enumerate(listings)}

    results = []
    for listing_id, changes in updates.items():
        if listing_id not in id_to_idx:
            results.append({"id": listing_id, "status": "NOT FOUND", "changes": []})
            continue

        idx = id_to_idx[listing_id]
        listing = listings[idx]
        applied = []

        if "description" in changes:
            listing["description"] = changes["description"]
            applied.append("description")

        if "title" in changes:
            old_title = listing.get("title", "")
            listing["title"] = changes["title"]
            applied.append(f"title ({len(old_title)}ch → {len(changes['title'])}ch)")

        results.append({
            "id": listing_id,
            "status": "UPDATED",
            "changes": applied,
            "title_preview": listing.get("title", "")[:70],
        })

    return results


def print_summary(results):
    updated = [r for r in results if r["status"] == "UPDATED"]
    not_found = [r for r in results if r["status"] == "NOT FOUND"]
    title_updated = [r for r in updated if any("title" in c for c in r["changes"])]
    desc_updated = [r for r in updated if "description" in r["changes"]]

    print("\n" + "=" * 65)
    print("  LISTING UPDATE SUMMARY")
    print("=" * 65)
    print(f"  Total listings processed : {len(results)}")
    print(f"  Successfully updated     : {len(updated)}")
    print(f"    ↳ Descriptions written : {len(desc_updated)}")
    print(f"    ↳ Titles extended      : {len(title_updated)}")
    if not_found:
        print(f"  NOT FOUND (skipped)      : {len(not_found)}")
    print("=" * 65)

    if title_updated:
        print("\n  TITLE EXTENSIONS:")
        for r in title_updated:
            change_str = " | ".join(c for c in r["changes"] if "title" in c)
            print(f"  [{r['id']}] {change_str}")
            print(f"    → {r['title_preview']}…")

    if not_found:
        print("\n  MISSING IDs:")
        for r in not_found:
            print(f"  [{r['id']}]")

    print("\n  Done. shop_data.json updated and backup saved.\n")


if __name__ == "__main__":
    print("Loading data store…")
    data = load_store()

    print(f"Applying {len(LISTING_UPDATES)} listing updates…")
    results = apply_updates(data, LISTING_UPDATES)

    print("Saving updated data store (backup created)…")
    backup = save_store(data)
    print(f"Backup written to: {backup}")

    print_summary(results)
