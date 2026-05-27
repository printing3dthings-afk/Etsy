"""
Etsy post-purchase messaging & coupon strategy for OnBrandCraftz.

THREE automated touchpoints that drive reviews and repeat buyers:

  1. Post-purchase thank-you message  — sent automatically after every order
     → Delivers download instructions + asks for review (review ask #1)

  2. Abandoned cart / favorited coupon — Etsy sends 10% off after buyer saves item
     → Set up in: Shop Manager → Marketing → Sales & Discounts → Abandoned Cart

  3. Post-delivery follow-up coupon   — 15% off in a follow-up message
     → Set up in: Shop Manager → Marketing → Sales & Discounts → Thank You

Research: Products with 5+ reviews sell 270% more than products with zero.
These three touchpoints are the fastest path to the Star Seller badge.

Usage:
  python tools/etsy_messages.py           # print all message templates
  python tools/etsy_messages.py --setup   # print Etsy setup instructions
"""
from __future__ import annotations

# ── Message Templates ─────────────────────────────────────────────────────────

# Sent immediately after purchase (Etsy: Shop Manager → Settings → Info & Appearance → Message to buyers)
POST_PURCHASE_MESSAGE = """\
Hi {buyer_name}! ✨

Thank you SO much for your order — you're going to love it! 🌸

━━━━━━━━━━━━━━━━━━━━━━━
📥 HOW TO DOWNLOAD YOUR FILES
━━━━━━━━━━━━━━━━━━━━━━━
1. Go to Etsy.com → Account → Purchases and Reviews
2. Click "Download Files" next to your order
3. Save the ZIP file to your device, then unzip it
   → You'll find your PDF planner + sticker pack ZIP inside

━━━━━━━━━━━━━━━━━━━━━━━
📱 OPENING IN GOODNOTES 6
━━━━━━━━━━━━━━━━━━━━━━━
1. Open GoodNotes 6 → tap the + button → Import
2. Select your PDF file → it opens as a new notebook
3. Tap any text field to start typing — all fields are fillable!
4. For stickers: tap Elements → Stickers → + → import the 5 PNG sheets
   Your stickers appear in your library and can be dragged onto any page ✨

━━━━━━━━━━━━━━━━━━━━━━━
📧 NEED HELP?
━━━━━━━━━━━━━━━━━━━━━━━
Reply to this message anytime — I'm happy to help!
Email: Printing3dthings@outlook.com

If you love your planner, a review means the world to a small shop like mine 💕
It only takes 30 seconds: Etsy → Purchases and Reviews → Leave a Review

Thank you again! Happy planning! 🌟
— OnBrandCraftz
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
— Jesse
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
