"""
Email Lead Magnet System — OnBrandCraftz

Strategy: Build an email list OUTSIDE of Etsy so you own the customer relationship.
Etsy controls your shop visibility; your email list is yours forever.

HOW IT WORKS:
  1. TikTok/Pinterest/Instagram bio links to a Mailchimp signup page
  2. Signup form offers "FREE Kawaii Planner Sticker Sheet — 40+ stickers!"
  3. On signup: automated welcome email sends the free sticker download link
  4. Weekly newsletter keeps subscribers engaged → drives repeat Etsy purchases
  5. New product launches → email list first → Etsy views spike → algorithm boost

SETUP STEPS:
  1. Go to mailchimp.com → create free account (500 contacts free)
  2. Create an Audience called "OnBrandCraftz VIP List"
  3. Create a signup form → copy the form URL
  4. Create an automation: "Welcome Email" triggered by new signup
  5. Paste the free sticker download link in the welcome email
  6. Set MAILCHIMP_API_KEY and MAILCHIMP_LIST_ID in .env

FREE STICKER SHEET (lead magnet):
  - Use one of the 5 sticker sheets from any planner pack
  - Host it on Google Drive or Dropbox with a public sharing link
  - Set LEAD_MAGNET_URL in .env pointing to that link

Usage:
  python tools/email_leadmagnet.py               # print full setup guide
  python tools/email_leadmagnet.py --templates   # print email templates
  python tools/email_leadmagnet.py --stats       # show list stats
"""
from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ── Config (from .env) ────────────────────────────────────────────────────────

MAILCHIMP_API_KEY   = os.getenv("MAILCHIMP_API_KEY", "")
MAILCHIMP_LIST_ID   = os.getenv("MAILCHIMP_LIST_ID", "")
LEAD_MAGNET_URL     = os.getenv("LEAD_MAGNET_URL", "")      # Google Drive / Dropbox public link
MAILCHIMP_SIGNUP_URL = os.getenv("MAILCHIMP_SIGNUP_URL", "") # Your audience signup form URL

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "Printing3dthings@outlook.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_NAME   = os.getenv("SENDER_NAME", "OnBrandCraftz")

# ── Email Templates ───────────────────────────────────────────────────────────

WELCOME_EMAIL_SUBJECT = "🎁 Your FREE Kawaii Sticker Sheet is here! (+ a little surprise)"

WELCOME_EMAIL_HTML = """\
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">

<div style="text-align: center; padding: 20px 0;">
  <h1 style="color: #8666AA; font-size: 28px;">✨ Welcome to OnBrandCraftz VIP! ✨</h1>
  <p style="font-size: 16px; color: #666;">You just joined the most kawaii planning community on the internet 🌸</p>
</div>

<hr style="border: 1px solid #E8E0F0; margin: 20px 0;">

<h2 style="color: #8666AA;">🎁 Here's your FREE sticker sheet!</h2>
<p>As promised — your exclusive <strong>Kawaii Planner Sticker Pack (40+ stickers!)</strong> is ready to download:</p>

<div style="text-align: center; margin: 30px 0;">
  <a href="{lead_magnet_url}"
     style="background-color: #8666AA; color: white; padding: 16px 32px; text-decoration: none;
            border-radius: 8px; font-size: 18px; font-weight: bold; display: inline-block;">
    📥 DOWNLOAD YOUR FREE STICKERS
  </a>
</div>

<p style="font-size: 14px; color: #888;">
  <strong>How to use in GoodNotes 6:</strong><br>
  Elements → Stickers → + → select the PNG file → drag onto any page, unlimited times! ✨
</p>

<hr style="border: 1px solid #E8E0F0; margin: 20px 0;">

<h2 style="color: #8666AA;">🌸 What to expect as a VIP member</h2>
<ul style="line-height: 1.8; font-size: 15px;">
  <li>🆕 <strong>New product launches</strong> — you get early access before they go live</li>
  <li>💰 <strong>Exclusive VIP discounts</strong> — coupons just for subscribers (never shared publicly)</li>
  <li>🎨 <strong>Free downloads</strong> — bonus sticker sheets, cover designs, and templates</li>
  <li>📱 <strong>GoodNotes tips & tricks</strong> — get the most out of your digital planner</li>
</ul>

<p style="font-size: 15px;">Emails go out <strong>once a week</strong> — never spammy, always worth opening. 💕</p>

<hr style="border: 1px solid #E8E0F0; margin: 20px 0;">

<h2 style="color: #8666AA;">🛍️ Ready to start planning?</h2>
<p>Here's the full collection — all kawaii planners include a matching sticker pack:</p>

<table style="width: 100%; border-collapse: collapse; font-size: 14px;">
  <tr style="background: #F5F0FF;">
    <td style="padding: 10px; border: 1px solid #E0D8F0;"><strong>✨ Ultimate Life Planner</strong><br>104 pages · Lavender Dreams</td>
    <td style="padding: 10px; border: 1px solid #E0D8F0; text-align: center;">$14.99</td>
  </tr>
  <tr>
    <td style="padding: 10px; border: 1px solid #E0D8F0;"><strong>🎓 Student Planner</strong><br>90 pages · Cotton Candy</td>
    <td style="padding: 10px; border: 1px solid #E0D8F0; text-align: center;">$9.99</td>
  </tr>
  <tr style="background: #F5F0FF;">
    <td style="padding: 10px; border: 1px solid #E0D8F0;"><strong>💰 Budget Planner</strong><br>102 pages · Midnight Blue</td>
    <td style="padding: 10px; border: 1px solid #E0D8F0; text-align: center;">$12.99</td>
  </tr>
  <tr>
    <td style="padding: 10px; border: 1px solid #E0D8F0;"><strong>🏃 Fitness Planner</strong><br>91 pages · Coral Peach</td>
    <td style="padding: 10px; border: 1px solid #E0D8F0; text-align: center;">$12.99</td>
  </tr>
</table>

<div style="text-align: center; margin: 25px 0;">
  <a href="https://www.etsy.com/shop/onbrandcraftz"
     style="background-color: #F96B00; color: white; padding: 14px 28px; text-decoration: none;
            border-radius: 8px; font-size: 16px; font-weight: bold; display: inline-block;">
    🛍️ SHOP ONBRANDCRAFTZ ON ETSY
  </a>
</div>

<div style="text-align: center; margin: 10px 0;">
  <p style="font-size: 13px; color: #888;">
    Use code <strong>VIP10</strong> for 10% off your first order! 🎁
  </p>
</div>

<hr style="border: 1px solid #E8E0F0; margin: 20px 0;">

<p style="font-size: 13px; color: #aaa; text-align: center;">
  You're getting this because you signed up for OnBrandCraftz VIP updates.<br>
  <a href="*|UNSUB|*" style="color: #aaa;">Unsubscribe</a> anytime — no hard feelings! 🌸<br><br>
  © OnBrandCraftz · Printing3dthings@outlook.com
</p>

</body>
</html>
"""

WELCOME_EMAIL_PLAIN = """\
✨ Welcome to OnBrandCraftz VIP! ✨

Here's your FREE Kawaii Sticker Sheet (40+ stickers):
{lead_magnet_url}

How to use in GoodNotes 6:
Elements → Stickers → + → select the PNG → drag onto any page!

As a VIP member you'll receive:
• Early access to new product launches
• Exclusive VIP-only discount codes
• Free bonus sticker sheets and downloads
• GoodNotes tips & tricks

Shop the full collection:
https://www.etsy.com/shop/onbrandcraftz

Use code VIP10 for 10% off your first order!

— Jesse at OnBrandCraftz 🌸
Printing3dthings@outlook.com

Unsubscribe: *|UNSUB|*
"""

# ── Weekly Newsletter Templates ───────────────────────────────────────────────

NEWSLETTER_TEMPLATES = {
    "new_product_launch": {
        "subject": "🆕 New in the shop: {product_name} is here! (VIP gets first look)",
        "headline": "Something new just dropped ✨",
        "body": """\
Hi {first_name}!

Big news — {product_name} just went live in the shop, and as a VIP subscriber you're the FIRST to know! 🎉

{product_description}

✅ {pages} pages of beautiful kawaii planning
✅ Matching sticker pack (200+ stickers) included
✅ Works in GoodNotes, Notability, and all PDF apps
✅ Instant download — available right after purchase

For the next 48 hours, use code {launch_code} for {discount}% off.

[SHOP NOW button → Etsy listing URL]

Happy planning! 🌸
— Jesse at OnBrandCraftz""",
    },

    "weekly_tips": {
        "subject": "📱 3 GoodNotes tricks that changed how I plan ✨",
        "headline": "GoodNotes tips from a planner obsessive 🌸",
        "body": """\
Hi {first_name}!

This week I've been geeking out on GoodNotes productivity tricks. Here are 3 that genuinely changed how I plan:

🌟 TIP 1: The "Elements" sticker library is a game-changer
Instead of importing stickers one by one, import all 5 PNG sheets from your planner's sticker pack at once.
They stay in your library forever and you can drag ANY sticker onto ANY page, unlimited times.

🌟 TIP 2: Use the "Add Link" tool to make your own navigation
In GoodNotes, tap and hold on any image → Add Link → link to another page. Create your own custom tabs!

🌟 TIP 3: Duplicate pages instead of starting fresh each week
Tap the thumbnail → Duplicate → your layout, any stickers you placed, all come with it.

Want the full planner system I use every day? It's in the shop 👇

[SHOP PLANNERS → etsy.com/shop/onbrandcraftz]

Talk soon! ✨
— Jesse""",
    },

    "flash_sale": {
        "subject": "⚡ 24-HOUR SALE — {discount}% off everything (ends tonight!)",
        "headline": "Flash sale — today only! ⚡",
        "body": """\
Hi {first_name}!

Quick one — I'm running a 24-hour flash sale and VIP subscribers get it first 🎉

🎁 Use code {coupon_code} for {discount}% off ANYTHING in the shop
⏰ Expires: {expiry} (24 hours from now)

What's in the shop:
• Ultimate Life Planner (104 pages) — $14.99 → ${discounted_price_life}
• Student Planner (90 pages) — $9.99 → ${discounted_price_student}
• Budget Planner (102 pages) — $12.99 → ${discounted_price_budget}
• Fitness Planner (91 pages) — $12.99 → ${discounted_price_fitness}
• All 4 Planners Bundle — $39.99 → ${discounted_price_bundle}

[SHOP NOW → etsy.com/shop/onbrandcraftz]

Don't wait — this one expires fast! 💕
— Jesse at OnBrandCraftz""",
    },

    "free_sticker_bonus": {
        "subject": "🎁 Surprise gift inside — a free sticker sheet just for you!",
        "headline": "VIP exclusive: bonus stickers! 🎨",
        "body": """\
Hi {first_name}!

I was designing new sticker sheets this week and I made extra 😄

Here's a bonus sticker sheet — completely free, just for being on this list:

[DOWNLOAD FREE STICKERS → {bonus_sticker_url}]

These are {sticker_theme} themed — {sticker_count} stickers total, works in GoodNotes, Notability, and any PDF app.

If you don't have one of our planners yet, this is a perfect preview of what's included in every purchase 🌸

Happy planning!
— Jesse""",
    },
}

# ── Mailchimp Integration ─────────────────────────────────────────────────────

def add_subscriber_mailchimp(email: str, first_name: str = "", last_name: str = "") -> dict:
    """Add a subscriber to Mailchimp audience via API."""
    if not MAILCHIMP_API_KEY or not MAILCHIMP_LIST_ID:
        return {"error": "MAILCHIMP_API_KEY and MAILCHIMP_LIST_ID must be set in .env"}

    try:
        import urllib.request
        import urllib.error
        import base64
        import hashlib

        # Extract datacenter from API key (e.g., "us21" from "abc123-us21")
        dc = MAILCHIMP_API_KEY.split("-")[-1]
        base_url = f"https://{dc}.api.mailchimp.com/3.0"

        subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
        url = f"{base_url}/lists/{MAILCHIMP_LIST_ID}/members/{subscriber_hash}"

        payload = json.dumps({
            "email_address": email,
            "status": "subscribed",
            "merge_fields": {
                "FNAME": first_name,
                "LNAME": last_name,
            },
        }).encode("utf-8")

        credentials = base64.b64encode(f"anystring:{MAILCHIMP_API_KEY}".encode()).decode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            },
            method="PUT",
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return {"success": True, "email": email, "status": result.get("status")}

    except Exception as e:
        return {"error": str(e), "email": email}


def send_welcome_email(to_email: str, first_name: str = "") -> dict:
    """Send the lead magnet welcome email via SMTP."""
    if not SMTP_PASSWORD:
        return {"error": "SMTP_PASSWORD not set in .env"}
    if not LEAD_MAGNET_URL:
        return {"error": "LEAD_MAGNET_URL not set in .env — add Google Drive/Dropbox link for free sticker sheet"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = WELCOME_EMAIL_SUBJECT
        msg["From"]    = f"{SENDER_NAME} <{SMTP_USER}>"
        msg["To"]      = to_email

        greeting = f"Hi {first_name}!" if first_name else "Hi!"
        plain = WELCOME_EMAIL_PLAIN.format(lead_magnet_url=LEAD_MAGNET_URL)
        html  = WELCOME_EMAIL_HTML.format(lead_magnet_url=LEAD_MAGNET_URL)

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html,  "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        return {"success": True, "to": to_email, "subject": WELCOME_EMAIL_SUBJECT}

    except Exception as e:
        return {"error": str(e), "to": to_email}


def get_mailchimp_stats() -> dict:
    """Get audience stats from Mailchimp API."""
    if not MAILCHIMP_API_KEY or not MAILCHIMP_LIST_ID:
        return {"error": "MAILCHIMP_API_KEY and MAILCHIMP_LIST_ID not configured"}

    try:
        import urllib.request
        import base64

        dc = MAILCHIMP_API_KEY.split("-")[-1]
        url = f"https://{dc}.api.mailchimp.com/3.0/lists/{MAILCHIMP_LIST_ID}"
        credentials = base64.b64encode(f"anystring:{MAILCHIMP_API_KEY}".encode()).decode()

        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Basic {credentials}"},
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            stats = data.get("stats", {})
            return {
                "list_name":         data.get("name"),
                "total_subscribers": data.get("stats", {}).get("member_count", 0),
                "open_rate":         f"{stats.get('open_rate', 0)*100:.1f}%",
                "click_rate":        f"{stats.get('click_rate', 0)*100:.1f}%",
                "unsubscribe_rate":  f"{stats.get('unsubscribe_rate', 0)*100:.2f}%",
                "signup_form_url":   MAILCHIMP_SIGNUP_URL or "(set MAILCHIMP_SIGNUP_URL in .env)",
            }
    except Exception as e:
        return {"error": str(e)}


# ── Setup Guide ───────────────────────────────────────────────────────────────

SETUP_GUIDE = """
╔══════════════════════════════════════════════════════════════════════╗
║         OnBrandCraftz — Email Lead Magnet Setup Guide               ║
╚══════════════════════════════════════════════════════════════════════╝

WHY THIS MATTERS
━━━━━━━━━━━━━━━
• Etsy can delist your shop tomorrow — your email list is yours forever
• Email has 40× higher ROI than social media (DMA research)
• A list of 1,000 engaged buyers = ~$200–$400 per newsletter send
• External traffic to Etsy (from your email) = algorithmic ranking boost
• New product launch → email list first → 50+ views in hour 1 → Etsy promotes it

STEP 1 — CREATE YOUR MAILCHIMP ACCOUNT (FREE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to: mailchimp.com → Sign Up Free
2. Free plan: up to 500 contacts, 1,000 emails/month — enough to start
3. Create an Audience called: "OnBrandCraftz VIP List"
4. Under Audience → Signup Forms → create a hosted form
5. Copy the signup form URL → add to MAILCHIMP_SIGNUP_URL in .env

STEP 2 — SET UP YOUR FREE STICKER LEAD MAGNET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Pick one of the 5 sticker sheets from DP1026 (or create a special "free" sheet)
   File location: data/digital_products/product_files/DP1026_sticker_pack.zip
2. Upload the PNG file to Google Drive → Right-click → Share → "Anyone with link"
3. Copy the public link → add to LEAD_MAGNET_URL in .env
4. Test the link in an incognito browser — make sure it downloads without login

STEP 3 — SET UP MAILCHIMP WELCOME AUTOMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Mailchimp → Automations → Classic Automations → Welcome new subscribers
2. Trigger: "Signs up for your audience"
3. Paste the WELCOME_EMAIL_HTML content from this script (run --templates flag)
4. Customize the download button URL with your LEAD_MAGNET_URL
5. Activate the automation

STEP 4 — ADD YOUR SIGNUP LINK TO EVERYWHERE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• TikTok bio: "Get FREE Kawaii Stickers → [Mailchimp signup link]"
• Pinterest bio: same
• Instagram bio: same (use linktree if you have multiple links)
• Etsy shop announcement: "🎁 Join our VIP list for a free sticker sheet → [link]"
• Every TikTok video CTA: "Link in bio for your free sticker pack!"

STEP 5 — CONFIGURE .env
━━━━━━━━━━━━━━━━━━━━━━━
Add these lines to your .env file:

  MAILCHIMP_API_KEY=your_mailchimp_api_key_here
  MAILCHIMP_LIST_ID=your_audience_list_id_here
  MAILCHIMP_SIGNUP_URL=https://mailchimp.com/your-signup-form-url
  LEAD_MAGNET_URL=https://drive.google.com/your-sticker-sheet-link

STEP 6 — FIRST NEWSLETTER SCHEDULE (WEEK-BY-WEEK)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Week 1: Welcome series (automated — done from Step 3)
• Week 2: GoodNotes tips email (use the 'weekly_tips' template)
• Week 3: Free bonus sticker drop (use 'free_sticker_bonus' template)
• Week 4: Soft pitch — "Here's our full planner collection" (use 'new_product_launch')
• Week 5+: Repeat cycle — tips → freebie → product → tips → flash sale

SIGN-UP FORM COPY (paste into Mailchimp form editor)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Headline:  🎁 Get a FREE Kawaii Sticker Sheet (40+ stickers!)
  Subtext:   Join 1,000+ kawaii planner lovers. Get exclusive discounts,
             free downloads, and GoodNotes tips — delivered weekly.
  Button:    YES, SEND ME MY FREE STICKERS! 🌸
  Fine print: No spam ever. Unsubscribe anytime.

VIP COUPON CODE TO CREATE IN ETSY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Code: VIP10
Discount: 10% off
Type: Permanent (for new subscribers only — honor system)
Where to create: Shop Manager → Marketing → Sales & Discounts → Create Offer → Custom

EXPECTED GROWTH TRAJECTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━
• Month 1:   10–50 subscribers (TikTok starting to grow)
• Month 3:   100–300 subscribers (consistent posting + Etsy traffic)
• Month 6:   500–1,000 subscribers (first viral TikTok typically hits here)
• Month 12:  2,000–5,000 subscribers (self-reinforcing flywheel)

At 1,000 subscribers sending one newsletter per month:
  Average open rate 25% = 250 opens
  Average 5% click-to-Etsy = 12–15 shop visits per send
  Average 10% purchase from clicks = 1–2 sales per newsletter
  That's $10–$30 revenue from ONE email per month
  → At 5,000 subscribers: $50–$150 per send, every month, from your list
"""

# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import sys

    if "--templates" in sys.argv:
        print("=" * 70)
        print("WELCOME EMAIL — HTML VERSION")
        print("(Paste into Mailchimp Welcome Automation → Email → HTML editor)")
        print("=" * 70)
        print(WELCOME_EMAIL_HTML)
        print()
        print("=" * 70)
        print("WELCOME EMAIL — PLAIN TEXT VERSION")
        print("=" * 70)
        print(WELCOME_EMAIL_PLAIN)
        print()
        print("=" * 70)
        print("NEWSLETTER TEMPLATES (use these for weekly sends)")
        print("=" * 70)
        for name, tmpl in NEWSLETTER_TEMPLATES.items():
            print(f"\n── {name.upper().replace('_', ' ')} ──")
            print(f"Subject: {tmpl['subject']}")
            print(f"Headline: {tmpl['headline']}")
            print("Body:")
            print(tmpl["body"])
        return

    if "--stats" in sys.argv:
        print("Fetching Mailchimp stats...")
        stats = get_mailchimp_stats()
        print(json.dumps(stats, indent=2))
        return

    if "--test-email" in sys.argv:
        idx = sys.argv.index("--test-email")
        if idx + 1 < len(sys.argv):
            to = sys.argv[idx + 1]
            print(f"Sending test welcome email to {to}...")
            result = send_welcome_email(to, first_name="Tester")
            print(json.dumps(result, indent=2))
        else:
            print("Usage: python tools/email_leadmagnet.py --test-email you@example.com")
        return

    print(SETUP_GUIDE)
    print()
    print("Available commands:")
    print("  python tools/email_leadmagnet.py                # this setup guide")
    print("  python tools/email_leadmagnet.py --templates    # print email templates")
    print("  python tools/email_leadmagnet.py --stats        # Mailchimp subscriber stats")
    print("  python tools/email_leadmagnet.py --test-email you@example.com")


if __name__ == "__main__":
    main()
