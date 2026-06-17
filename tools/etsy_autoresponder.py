#!/usr/bin/env python3
"""
etsy_autoresponder.py

Reads new Etsy buyer messages, classifies each question with Claude Haiku,
drafts a personalized reply, then emails you a daily digest for approval.

Run daily (add to crontab alongside health_check):
  0 8 * * * cd /home/user/Etsy && python tools/etsy_autoresponder.py >> data/pipeline_log.txt 2>&1

Send an approved draft:
  python tools/etsy_autoresponder.py --send <conversation_id>

Send ALL pending drafts at once:
  python tools/etsy_autoresponder.py --send-all
"""

import json
import os
import sys
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Parse .env manually — never use load_dotenv()
# Guarded: Railway has no .env file at all (env vars are injected directly by
# the platform), only Scott's local checkout does. Without this guard the
# script crashes with FileNotFoundError before it ever reaches a live Etsy
# call -- diagnosed 2026-06-17 when wiring this into the live server's daily
# background loop (see ops_runbook.md).
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

import anthropic
from etsy_api import EtsyAPIClient, EtsyAPIError

DRAFTS_DIR   = Path("data/message_drafts")
SENT_LOG     = Path("data/message_drafts/sent_log.json")
SHOP_EMAIL   = os.getenv("SMTP_USER", "Printing3dthings@outlook.com")
SHOP_NAME    = "OnBrandCraftz"
REVIEW_DAYS  = 2  # look back this many days for new messages

DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Question categories and template replies ──────────────────────────────────

QUESTION_TYPES = {
    "download":    "buyer can't find or access their download link",
    "goodnotes":   "how to import stickers or use the planner in GoodNotes",
    "apps":        "which apps are compatible (GoodNotes, Notability, Acrobat, etc.)",
    "print":       "whether they can print the file at home or a print shop",
    "sharing":     "whether they can share the file with someone else",
    "cant_open":   "file won't open or is corrupted",
    "format":      "what file format is included or what's in the download",
    "refund":      "requesting a refund or replacement",
    "custom":      "requesting a custom or personalized version",
    "compliment":  "happy message, thank-you, or positive feedback",
    "other":       "question that doesn't fit any of the above",
}

TEMPLATES = {
    "download": """\
Hi {name}! 😊

Your download is ready — here's how to grab it:

1. Log into Etsy and go to **Purchases & Reviews** (click your account icon → Purchases & Reviews)
2. Find your OnBrandCraftz order and click **Download Files**
3. Save the ZIP or PDF to your device — it's there instantly!

If you're on the Etsy app, tap the order → **Download** button at the bottom.

Let me know if you have any trouble and I'll be happy to help! 🌸""",

    "goodnotes": """\
Hi {name}! 😊

Here's how to get everything set up in GoodNotes 6:

**For the planner:**
1. Download the PDF from your Etsy purchases
2. Open GoodNotes → tap the **+** button → **Import** → select the PDF
3. The planner will open with all tabs and links working!

**For stickers:**
1. Unzip the sticker pack
2. In GoodNotes, tap the **Elements** button (diamond icon in the toolbar)
3. Tap **Stickers** → tap **+** → select all 5 PNG files
4. Your stickers are now in your library — drag any onto any page, unlimited times ✨

Let me know if you get stuck anywhere!""",

    "apps": """\
Hi {name}! 😊

Great news — your planner works across all the popular apps:

★ **GoodNotes 6** (iPad, iPhone, Mac) — best experience, all tabs and links work
★ **Notability** (iPad, iPhone) — fully compatible
★ **PDF Expert** by Readdle — all fillable fields work
★ **Xodo PDF Reader** — free and works great
★ **Adobe Acrobat Reader** — works on Windows, Mac, iOS, Android (the STICKERS button works here too!)
★ **Print** — works at home or any print shop

Just open the PDF in any of these and you're good to go! Let me know if you need help with a specific one 🌸""",

    "print": """\
Hi {name}! 😊

Absolutely — the planner is print-ready! Here are your options:

**At home:** Open the PDF, hit Print, and choose US Letter (8.5×11") paper. Color printing gives the best look, but it works in black and white too.

**At a print shop:** Staples, Office Depot, FedEx Office, and local copy shops can all print it. Just bring the PDF on a USB or email it to yourself. Ask for "full color, US Letter, single-sided."

The file is already formatted perfectly for printing — no resizing needed 🌸""",

    "sharing": """\
Hi {name}! 😊

The license included with your purchase is for **personal use** — that means one person (you!). Each person who wants to use the planner would need their own copy.

If you'd like a second copy for someone as a gift, I'd be happy to help — just let me know! 🌸

I really appreciate you asking — it means a lot to small creators like me 💜""",

    "cant_open": """\
Hi {name}! 😊

Sorry to hear you're having trouble! Let's get this sorted quickly:

1. **Try a different app** — sometimes a PDF viewer is the issue. Download **Adobe Acrobat Reader** (free) and try opening it there
2. **Re-download the file** — go to Etsy → Purchases & Reviews → Download Files → download again (sometimes the first download gets interrupted)
3. **Check the file name ends in .pdf or .zip** — if it shows a different extension, let me know

If none of those work, reply with what device and app you're using and I'll walk you through it step by step! I'll make sure you get access to your files 🌸""",

    "format": """\
Hi {name}! 😊

Here's exactly what's in your download:

📄 **Planner PDF (2026 dated version)** — fillable, hyperlinked, interactive tabs
📄 **Planner PDF (undated version)** — same layout, no year dates, works any time
🎨 **Sticker Pack ZIP** — 5 PNG sticker sheets with 200+ kawaii stickers

All files are US Letter size (8.5×11"), fully fillable, and work in GoodNotes, Notability, PDF Expert, Xodo, and Adobe Acrobat Reader.

Let me know if you have any other questions! 🌸""",

    "refund": """\
Hi {name}! 😊

I'm sorry to hear your experience wasn't what you hoped for — I want to make sure every customer is happy!

Could you tell me a little more about what happened? For example:
- Were you unable to open or use the files?
- Was there a compatibility issue with your app?
- Was the product different from what you expected?

I'd love to help resolve this first — most issues can be fixed quickly! If we can't sort it out, I'll absolutely take care of you. Just send me the details and we'll go from there 🌸""",

    "custom": """\
Hi {name}! 😊

Thanks so much for reaching out about a custom order! I love working on personalized projects.

Could you share a little more about what you're looking for?
- What type of product (planner, SVG bundle, wall art)?
- Any specific colors, themes, or text you have in mind?
- Any deadline or timeline?

Once I know more, I can let you know what's possible and give you a quote. Looking forward to hearing your ideas! 🌸""",

    "compliment": """\
Hi {name}! 😊

Thank you so much — this genuinely made my day! 💜 I put a lot of love into every design and it means the world to hear that it's making your planning more fun.

If you ever have a moment to leave a review on Etsy, it helps this little shop more than you know. And if you ever need anything, I'm always here!

Happy planning! 🌸""",

    "other": None,  # Claude generates the full reply for unknown types
}


# ── Core functions ────────────────────────────────────────────────────────────

def _load_sent_log() -> set:
    if SENT_LOG.exists():
        return set(json.loads(SENT_LOG.read_text()).get("sent_ids", []))
    return set()

def _save_sent_log(sent_ids: set) -> None:
    SENT_LOG.write_text(json.dumps({"sent_ids": list(sent_ids)}, indent=2))

def _load_drafts() -> dict:
    """Load today's draft file."""
    draft_file = DRAFTS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_drafts.json"
    if draft_file.exists():
        return json.loads(draft_file.read_text())
    return {}

def _save_drafts(drafts: dict) -> None:
    draft_file = DRAFTS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_drafts.json"
    draft_file.write_text(json.dumps(drafts, indent=2))


def classify_message(text: str) -> tuple[str, str]:
    """Use Claude Haiku to classify the buyer's question. Returns (type, reasoning)."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    categories = "\n".join(f"- {k}: {v}" for k, v in QUESTION_TYPES.items())
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": (
                f"Classify this Etsy buyer message into exactly one category.\n\n"
                f"Categories:\n{categories}\n\n"
                f"Message: \"{text}\"\n\n"
                f"Reply with ONLY the category key (one word, no punctuation)."
            ),
        }],
    )
    category = resp.content[0].text.strip().lower()
    if category not in QUESTION_TYPES:
        category = "other"
    return category, QUESTION_TYPES[category]


def generate_reply(buyer_name: str, question_type: str, original_message: str,
                   product_name: str = "") -> str:
    """Generate a personalized draft reply."""
    template = TEMPLATES.get(question_type)
    if template:
        return template.format(name=buyer_name.split()[0] if buyer_name else "there")

    # For "other" / unrecognized types, use Claude to generate a full reply
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=350,
        messages=[{
            "role": "user",
            "content": (
                f"You are a friendly Etsy shop owner at {SHOP_NAME}, which sells kawaii digital planners, "
                f"SVG cut files, and printable wall art. A customer named {buyer_name} sent this message:\n\n"
                f"\"{original_message}\"\n\n"
                f"Write a warm, helpful reply in 3-5 sentences. Be friendly, use 1-2 relevant emojis. "
                f"End with 'Let me know if you need anything else! 🌸'"
            ),
        }],
    )
    return resp.content[0].text.strip()


def _send_smtp(subject: str, body_html: str, body_text: str) -> None:
    """Send email via Outlook SMTP."""
    smtp_host = os.getenv("SMTP_HOST", "smtp-mail.outlook.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = SHOP_EMAIL
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, SHOP_EMAIL, msg.as_string())


def send_digest_email(drafts: dict, unresolved: list) -> None:
    """Email digest of draft replies and unresolved messages."""
    today = datetime.now().strftime("%B %d, %Y")
    draft_count = len(drafts)
    unresolve_count = len(unresolved)

    if draft_count == 0 and unresolve_count == 0:
        print("No new messages — no digest sent.")
        return

    # Build HTML email
    draft_rows = ""
    for cid, d in drafts.items():
        draft_rows += f"""
        <div style="border:1px solid #e0d6ff;border-radius:8px;padding:16px;margin-bottom:16px;">
          <p style="margin:0 0 4px 0;font-size:12px;color:#888;">Conversation #{cid} — {d['buyer_name']} — <em>{d['question_type']}</em></p>
          <p style="margin:0 0 8px 0;background:#f9f5ff;padding:10px;border-radius:4px;font-style:italic;">"{d['buyer_message']}"</p>
          <p style="margin:0 0 12px 0;white-space:pre-wrap;font-size:14px;">{d['draft_reply']}</p>
          <code style="background:#1a1a2e;color:#e0d0ff;padding:8px 12px;border-radius:4px;display:block;font-size:13px;">
            python tools/etsy_autoresponder.py --send {cid}
          </code>
        </div>"""

    unresolved_rows = ""
    for u in unresolved:
        unresolved_rows += f"""
        <div style="border:1px solid #ffe0e0;border-radius:8px;padding:12px;margin-bottom:12px;">
          <p style="margin:0 0 4px 0;font-size:12px;color:#888;">Conversation #{u['conversation_id']} — {u['buyer_name']}</p>
          <p style="margin:0;font-style:italic;">"{u['buyer_message']}"</p>
        </div>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;padding:20px;color:#333;">
      <h2 style="color:#8666AA;">📬 OnBrandCraftz — Message Digest — {today}</h2>
      <p>{draft_count} draft repl{'y' if draft_count == 1 else 'ies'} ready to send &nbsp;·&nbsp;
         {unresolve_count} message{'s' if unresolve_count != 1 else ''} need{'s' if unresolve_count == 1 else ''} review</p>
      <p>To send all drafts at once: <code>python tools/etsy_autoresponder.py --send-all</code></p>
      <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
      {'<h3 style="color:#8666AA;">✅ Ready to Send</h3>' + draft_rows if draft_rows else ''}
      {'<h3 style="color:#cc4444;">⚠️ Needs Manual Reply</h3>' + unresolved_rows if unresolved_rows else ''}
    </body></html>"""

    text_parts = [f"OnBrandCraftz Message Digest — {today}", ""]
    for cid, d in drafts.items():
        text_parts += [
            f"--- Conversation #{cid} | {d['buyer_name']} | {d['question_type']} ---",
            f"Buyer: {d['buyer_message']}",
            f"Draft: {d['draft_reply']}",
            f"Send:  python tools/etsy_autoresponder.py --send {cid}",
            "",
        ]
    for u in unresolved:
        text_parts += [
            f"--- NEEDS REVIEW: Conversation #{u['conversation_id']} | {u['buyer_name']} ---",
            f"Message: {u['buyer_message']}", "",
        ]

    try:
        _send_smtp(
            subject=f"📬 Etsy Messages — {draft_count} drafts ready ({today})",
            body_html=html,
            body_text="\n".join(text_parts),
        )
        print(f"Digest emailed to {SHOP_EMAIL}")
    except Exception as e:
        print(f"Email send failed: {e}")
        print("--- DIGEST (text fallback) ---")
        print("\n".join(text_parts))


# ── Main actions ──────────────────────────────────────────────────────────────

def run() -> None:
    """Fetch new messages, classify, draft replies, email digest."""
    etsy = EtsyAPIClient()
    sent_ids = _load_sent_log()
    drafts: dict = {}
    unresolved: list = []

    cutoff_ts = int((datetime.now() - timedelta(days=REVIEW_DAYS)).timestamp())

    print(f"Fetching conversations from last {REVIEW_DAYS} days...")
    try:
        data = etsy.get_messages(limit=50)
    except EtsyAPIError as e:
        print(f"Could not fetch messages: {e}")
        return

    conversations = data.get("results", [])
    print(f"Found {len(conversations)} conversations")

    for convo in conversations:
        cid = str(convo.get("conversation_id", ""))
        if not cid:
            continue

        # Skip already-sent conversations
        if cid in sent_ids:
            continue

        last_modified = convo.get("last_modified_timestamp", 0)
        if last_modified < cutoff_ts:
            continue

        # Get the buyer's latest message (from buyer, not shop)
        messages = convo.get("messages", [])
        buyer_messages = [
            m for m in messages
            if m.get("from_user_id") != convo.get("shop_user_id")
        ]
        if not buyer_messages:
            continue

        latest = max(buyer_messages, key=lambda m: m.get("creation_tsz", 0))
        buyer_text = latest.get("body", "").strip()
        if not buyer_text:
            continue

        buyer_name = convo.get("buyer_name", "Customer")
        print(f"  Processing #{cid} from {buyer_name}: {buyer_text[:60]}...")

        question_type, _ = classify_message(buyer_text)

        if question_type == "refund" or question_type == "other":
            unresolved.append({
                "conversation_id": cid,
                "buyer_name": buyer_name,
                "buyer_message": buyer_text,
                "question_type": question_type,
            })
            continue

        draft = generate_reply(buyer_name, question_type, buyer_text)
        drafts[cid] = {
            "conversation_id": cid,
            "buyer_name": buyer_name,
            "buyer_message": buyer_text,
            "question_type": question_type,
            "draft_reply": draft,
            "created_at": datetime.now().isoformat(),
        }

    _save_drafts(drafts)

    print(f"\n{len(drafts)} drafts written, {len(unresolved)} flagged for manual review")
    send_digest_email(drafts, unresolved)


def send_draft(conversation_id: str) -> None:
    """Send an approved draft reply."""
    drafts = _load_drafts()
    if conversation_id not in drafts:
        # Try searching all draft files
        for f in sorted(DRAFTS_DIR.glob("*_drafts.json"), reverse=True):
            d = json.loads(f.read_text())
            if conversation_id in d:
                drafts = d
                break
    if conversation_id not in drafts:
        print(f"No draft found for conversation {conversation_id}")
        return

    draft = drafts[conversation_id]
    etsy = EtsyAPIClient()
    try:
        etsy.send_message(int(conversation_id), draft["draft_reply"])
        print(f"✓ Sent reply to {draft['buyer_name']} (#{conversation_id})")
        sent_ids = _load_sent_log()
        sent_ids.add(conversation_id)
        _save_sent_log(sent_ids)
    except EtsyAPIError as e:
        print(f"Failed to send: {e}")


def send_all_drafts() -> None:
    """Send all pending drafts from today's draft file."""
    drafts = _load_drafts()
    if not drafts:
        print("No drafts found for today.")
        return
    sent_ids = _load_sent_log()
    etsy = EtsyAPIClient()
    for cid, draft in drafts.items():
        if cid in sent_ids:
            print(f"  Skipping #{cid} — already sent")
            continue
        try:
            etsy.send_message(int(cid), draft["draft_reply"])
            print(f"  ✓ Sent to {draft['buyer_name']} (#{cid})")
            sent_ids.add(cid)
        except EtsyAPIError as e:
            print(f"  ✗ Failed #{cid}: {e}")
    _save_sent_log(sent_ids)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--send-all" in args:
        send_all_drafts()
    elif "--send" in args:
        idx = args.index("--send")
        if idx + 1 >= len(args):
            print("Usage: python tools/etsy_autoresponder.py --send <conversation_id>")
            sys.exit(1)
        send_draft(args[idx + 1])
    else:
        run()
