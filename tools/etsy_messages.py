"""
Etsy post-purchase messaging & coupon strategy for OnBrandCraftz.

THREE automated touchpoints that drive reviews and repeat buyers:

  1. Post-purchase thank-you message  — sent automatically after every order
     → Personalized per product type + review ask (review ask #1)

  2. Abandoned cart / favorited coupon — Etsy sends 10% off after buyer saves item
     → Set up in: Shop Manager → Marketing → Sales & Discounts → Abandoned Cart

  3. Post-delivery follow-up coupon   — 15% off in a follow-up message
     → Set up in: Shop Manager → Marketing → Sales & Discounts → Thank You

Research: Products with 5+ reviews sell 270% more than products with zero.
These three touchpoints are the fastest path to the Star Seller badge.

SET UP THE MESSAGE TO BUYERS:
  Etsy.com → Shop Manager → Settings → Info & Appearance → "Message to Buyers"
  Use POST_PURCHASE_MESSAGE_DIGITAL for a digital-products-only shop,
  or POST_PURCHASE_MESSAGE_UNIVERSAL if you sell both digital and physical.

Usage:
  python tools/etsy_messages.py           # print all message templates
  python tools/etsy_messages.py --setup   # print Etsy setup instructions
"""
from __future__ import annotations

# ── Message Templates ─────────────────────────────────────────────────────────

# ★ UNIVERSAL — works for every product type (digital planners, stickers, wall art, 3D prints)
# Paste this into: Etsy → Shop Manager → Settings → Info & Appearance → Message to Buyers
POST_PURCHASE_MESSAGE = """\
Hi {buyer_name},

Thank you so much for your order — it genuinely means the world to me!

I'm a small one-person shop and every single purchase helps me keep creating, \
so thank you for choosing OnBrandCraftz.

━━━━━━━━━━━━━━━━━━━━━━━━━━
FOR DIGITAL DOWNLOADS
━━━━━━━━━━━━━━━━━━━━━━━━━━
Your files are ready right now!
1. Go to Etsy.com → Account → Purchases and Reviews
2. Click "Download Files" next to your order
3. Save + unzip — your PDF and sticker pack are inside

Opening in GoodNotes 6? Tap + → Import → select your PDF.
For stickers: Elements → Stickers → + → import the 5 PNG sheets.
Your stickers live in your library forever and can be dragged onto any page!

━━━━━━━━━━━━━━━━━━━━━━━━━━
FOR 3D PRINTED ORDERS
━━━━━━━━━━━━━━━━━━━━━━━━━━
Your item is being printed now and I'll send tracking as soon as it ships!
Every piece is printed to order just for you — quality checked before it leaves.

━━━━━━━━━━━━━━━━━━━━━━━━━━
NEED ANYTHING?
━━━━━━━━━━━━━━━━━━━━━━━━━━
Just reply here and I'll get back to you fast — usually same day!

And if you love what you got, a quick review would make my whole week.
Etsy → Purchases and Reviews → Leave a Review (takes 30 seconds!)

Thank you again, {buyer_name} — enjoy every bit of it!
— Scott @ OnBrandCraftz
"""

# ── PRODUCT-SPECIFIC PERSONALIZED MESSAGES ───────────────────────────────────
# Used by order_notifier.py to generate per-order custom messages.
# These are sent manually by the shop owner via Etsy's message system.

PERSONAL_MESSAGE_DIGITAL_PLANNER = """\
Hi {buyer_name}! 🌸

Just wanted to send you a personal note — thank you SO much for picking up \
{product_title}! I put a lot of love into designing it and I really hope it \
helps you stay organized and feel good every single day. 💕

A couple of quick tips to get the most out of it:
• Open it in GoodNotes 6 or Notability for the best experience
• Import the sticker PNG sheets into your Elements/Stickers library first
• The side tabs are hyperlinked — tap any tab to jump to that section instantly
• Every page has a 🏠 HOME button that brings you back to the dashboard

If anything feels confusing or something isn't working, just reply here — \
I'm always happy to help and I check messages every day!

Enjoy your new planner, {first_name}! 🌟
— Scott @ OnBrandCraftz
"""

PERSONAL_MESSAGE_WALL_ART = """\
Hi {buyer_name}! 🎨

Thank you so much for your order of {product_title} — I hope you absolutely \
love it on your wall! It's one of my favorites. 💕

To get the best print quality:
• Take the file to any print shop or upload to Canva Print, Printful, or Walgreens
• Choose your frame size FIRST, then ask them to print to match
• "Fit to page" or "fill page" gives the cleanest result
• 300 DPI means it'll look sharp at any size up to 24×36"

If you ever need a different size or want a custom color version, just message \
me — I love doing custom work! 🌸

Thank you again, {first_name}! Enjoy it!
— Scott @ OnBrandCraftz
"""

PERSONAL_MESSAGE_3D_PRINT = """\
Hi {buyer_name}! 🎉

Thank you for your order of {product_title}! I'm printing it now on my Bambu \
Lab P1S and making sure it comes out perfect before it ships. 🙏

A few things to know:
• Most orders ship within 2–4 business days
• I'll send your tracking number as soon as it's on its way
• Everything is printed to order just for you — no pre-made inventory here!

If you have any special requests (color swap, size tweak, etc.) message me \
NOW before it prints and I'll do my best to accommodate! 🌟

Thanks so much, {first_name}!
— Scott @ OnBrandCraftz
"""

PERSONAL_MESSAGE_STICKER_PACK = """\
Hi {buyer_name}! ✨

Thank you for grabbing {product_title} — sticker packs are honestly my \
favorite things to design! I hope you have SO much fun with them. 🌸

Quick how-to for GoodNotes 6:
1. Unzip the download and find the 5 PNG sheet files
2. In GoodNotes: tap the Elements button (diamond icon) → Stickers tab → +
3. Select all 5 PNG files — they'll load into your library instantly
4. Drag any sticker onto any page, unlimited times, forever! ✨

For Notability: use Photo Stickers → import the PNGs.
For Acrobat/Xodo: the built-in STICKERS button in the PDF footer works too!

Enjoy them, {first_name}! 💕
— Scott @ OnBrandCraftz
"""

# Fallback for any product type not matched above
PERSONAL_MESSAGE_GENERIC = """\
Hi {buyer_name}! 🌸

Just a quick personal note to say THANK YOU for your order of {product_title}! \
It means so much to me as a small shop owner. 💕

I hope you absolutely love it! If you have any questions at all, just reply \
here and I'll get back to you same day.

And if you're happy with your purchase, leaving a review would make my whole \
week — it really does make a difference for small shops like mine. 🌟

Thanks again, {first_name}!
— Scott @ OnBrandCraftz
"""

# Etsy auto-sends this to favorited/cart-saved items (set up in Etsy dashboard)
ABANDONED_CART_COUPON_MESSAGE = """\
Hi {buyer_name}! 👋

I noticed you were looking at {item_title} — I hope you loved it! ✨

As a thank-you for your interest, here's a special 10% off code just for you:

🎁 Coupon code: {coupon_code}
Expires: 48 hours

Use it at checkout → https://www.etsy.com/shop/onbrandcraftz

If you have any questions before buying, just reply and I'll answer right away!

— OnBrandCraftz 🌸
"""

# Sent after delivery confirmation (set up as "Thank You" discount in Etsy)
POST_DELIVERY_FOLLOWUP = """\
Hi {buyer_name}! 🌸

I hope you're loving your {item_title}! ✨

If you're enjoying it, I'd be SO grateful for a quick review — it helps small shops like mine more than you know:
👉 Etsy → Purchases and Reviews → Leave a Review (takes 30 seconds!)

And as a thank-you for your purchase, here's 15% off your next order:

🎁 Coupon code: {coupon_code}
(valid for 30 days — use it on anything in the shop!)

New products drop regularly — check back anytime 💕
https://www.etsy.com/shop/onbrandcraftz

Thank you again for supporting OnBrandCraftz! 🙏
— Scott
"""

# ── Coupon Codes to Create in Etsy Dashboard ─────────────────────────────────

COUPONS_TO_CREATE = [
    {
        "name": "Abandoned Cart Coupon",
        "code": "COMEBACK10",
        "discount": "10% off",
        "when": "Auto-sent when buyer favorites or adds to cart and doesn't buy within 24 hours",
        "etsy_path": "Shop Manager → Marketing → Sales & Discounts → Create Offer → Abandoned Cart",
        "expires": "48 hours after sent",
    },
    {
        "name": "Thank You / Repeat Buyer Coupon",
        "code": "THANKYOU15",
        "discount": "15% off",
        "when": "Auto-sent after order is marked delivered",
        "etsy_path": "Shop Manager → Marketing → Sales & Discounts → Create Offer → Thank You",
        "expires": "30 days",
    },
    {
        "name": "Bundle Discount",
        "code": "BUNDLE20",
        "discount": "20% off orders of 2+ items",
        "when": "Manually share or put in shop announcement",
        "etsy_path": "Shop Manager → Marketing → Sales & Discounts → Create Offer → Volume Discount",
        "expires": "Permanent",
    },
]

# ── Etsy Setup Instructions ───────────────────────────────────────────────────

SETUP_INSTRUCTIONS = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — SET UP POST-PURCHASE MESSAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Etsy.com → Shop Manager → Settings
2. Click "Info & Appearance"
3. Scroll to "Message to Buyers"
4. Paste the POST_PURCHASE_MESSAGE text
5. Save

This message goes to EVERY buyer automatically at checkout.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — SET UP ABANDONED CART COUPON (COMEBACK10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Shop Manager → Marketing → Sales & Discounts
2. Click "Create Offer"
3. Select "Abandoned Cart" offer type
4. Set discount: 10% off
5. Set time delay: 24 hours
6. Etsy sends automatically — no manual work needed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — SET UP THANK YOU COUPON (THANKYOU15)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Shop Manager → Marketing → Sales & Discounts
2. Click "Create Offer"
3. Select "Thank You" offer type
4. Set discount: 15% off
5. Set expiry: 30 days
6. Etsy sends automatically after delivery

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — ENABLE RICH PINS ON PINTEREST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Shop Manager → Marketing → Pinterest
2. Click "Enable Rich Pins"
3. Done — all future pins will automatically show price + availability

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHY THIS MATTERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Products with 5+ reviews sell 270% more than products with 0
• Abandoned cart coupons recover ~15% of lost carts on average
• Thank-you coupons are the #1 repeat-buyer driver
• Star Seller badge (needs 4.8+ reviews) boosts ALL listings in search

Once you have 5 reviews on a listing → turn on $5/day Etsy Ads for that listing only.
"""

# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import sys
    if "--setup" in sys.argv:
        print(SETUP_INSTRUCTIONS)
        return

    print("=" * 60)
    print("POST-PURCHASE MESSAGE (paste into Etsy → Settings → Message to Buyers)")
    print("=" * 60)
    print(POST_PURCHASE_MESSAGE)

    print("=" * 60)
    print("ABANDONED CART MESSAGE (Etsy sends automatically — for reference)")
    print("=" * 60)
    print(ABANDONED_CART_COUPON_MESSAGE)

    print("=" * 60)
    print("POST-DELIVERY FOLLOW-UP (Etsy sends automatically — for reference)")
    print("=" * 60)
    print(POST_DELIVERY_FOLLOWUP)

    print("=" * 60)
    print("COUPONS TO CREATE IN ETSY DASHBOARD")
    print("=" * 60)
    for c in COUPONS_TO_CREATE:
        print(f"\n  {c['name']}")
        print(f"  Code:     {c['code']}")
        print(f"  Discount: {c['discount']}")
        print(f"  Trigger:  {c['when']}")
        print(f"  Path:     {c['etsy_path']}")

    print("\n\nRun with --setup for step-by-step Etsy setup instructions.")


if __name__ == "__main__":
    main()
