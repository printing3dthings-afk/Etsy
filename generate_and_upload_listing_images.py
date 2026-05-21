#!/usr/bin/env python3
"""
Generate complete Etsy listing photo packages for DP1026-DP1029 and upload them.
Also assigns each listing to the 'Digital Planners' shop section.
"""

import os
import sys
import json
import urllib.request
import base64
import time

# ── Load .env ────────────────────────────────────────────────────────────────
with open("/home/user/Etsy/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_DIR = "/home/user/Etsy/data/digital_products/product_files"

sys.path.insert(0, "/home/user/Etsy")
from tools.etsy_api import EtsyAPIClient

client = EtsyAPIClient()

# ── Image generation ─────────────────────────────────────────────────────────

def generate_image(prompt: str, out_path: str) -> bool:
    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "medium",
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        img_bytes = base64.b64decode(data["data"][0]["b64_json"])
        with open(out_path, "wb") as f:
            f.write(img_bytes)
        print(f"  [GEN] {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
        return True
    except Exception as e:
        print(f"  [ERR] generate_image {os.path.basename(out_path)}: {e}")
        return False

# ── PDF rendering ─────────────────────────────────────────────────────────────

import fitz  # PyMuPDF

def render_pdf_page(pdf_path: str, page_index: int, out_path: str, zoom: float = 2.0) -> bool:
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_index]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        pix.save(out_path)
        doc.close()
        print(f"  [PDF] {os.path.basename(out_path)} (page {page_index+1})")
        return True
    except Exception as e:
        print(f"  [ERR] render_pdf_page {os.path.basename(out_path)}: {e}")
        return False

def find_page_by_outline(pdf_path: str, keyword: str) -> int | None:
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    doc.close()
    for level, title, page_num in toc:
        if keyword.lower() in title.lower():
            return page_num - 1  # 0-indexed
    return None

# ── Upload helper ─────────────────────────────────────────────────────────────

def upload_image(listing_id, image_path: str, rank: int) -> bool:
    try:
        result = client.upload_listing_image(listing_id, image_path, rank=rank)
        print(f"  [UP]  rank={rank} {os.path.basename(image_path)} → image_id={result.get('listing_image_id', '?')}")
        return True
    except Exception as e:
        print(f"  [ERR] upload rank={rank} {os.path.basename(image_path)}: {e}")
        return False

# ── Planner configs ───────────────────────────────────────────────────────────

PLANNERS = {
    "DP1026": {
        "listing_id": 4509179201,
        "color": "lavender/purple (Lavender Dreams)",
        "theme": "ultimate life planner with budget and meal planning",
        "style_adj": "soft lavender and purple tones",
        "needs": [6, 7, 8, 9, 10],  # ranks needed
        "has_budget": True,
        "has_meal": True,
    },
    "DP1027": {
        "listing_id": 4509184958,
        "color": "cotton candy pink and sky blue",
        "theme": "student and school planner with study schedule",
        "style_adj": "soft pink and blue cotton candy tones",
        "needs": list(range(2, 11)),  # ranks 2-10
        "has_budget": False,
        "has_meal": False,
    },
    "DP1028": {
        "listing_id": 4509184962,
        "color": "midnight blue and ice blue",
        "theme": "budget and finance planner with income/expense tracking",
        "style_adj": "deep midnight blue and cool ice blue tones",
        "needs": list(range(2, 11)),
        "has_budget": True,
        "has_meal": False,
    },
    "DP1029": {
        "listing_id": 4509184968,
        "color": "coral peach and warm gold",
        "theme": "fitness and wellness planner with workout and habit tracking",
        "style_adj": "warm coral peach and golden tones",
        "needs": list(range(2, 11)),
        "has_budget": False,
        "has_meal": True,
    },
}

# Page indices from TOC analysis (0-indexed):
PAGE_INDICES = {
    "DP1026": {
        "monthly": 5,    # January = page 6 → index 5
        "weekly":  41,   # Weekly Planning = page 42 → index 41
        "habit":   93,   # Habit Tracker = page 94 → index 93
        "goals":   94,   # Goals & Vision = page 95 → index 94
        "budget":  95,   # Budget Tracker = page 96 → index 95
    },
    "DP1027": {
        "monthly": 5,    # January = page 6 → index 5
        "weekly":  29,   # Weekly Planning = page 30 → index 29
        "habit":   81,   # Habit Tracker = page 82 → index 81
        "goals":   82,   # Goals & Vision = page 83 → index 82
    },
    "DP1028": {
        "monthly": 5,
        "weekly":  41,
        "goals":   93,   # Goals & Vision = page 94 → index 93
        "budget":  94,   # Budget Tracker = page 95 → index 94
    },
    "DP1029": {
        "monthly": 5,
        "weekly":  29,
        "habit":   81,
        "goals":   82,   # Goals & Vision
        "meal":    83,   # Meal Planning
    },
}

# ── Prompt builders ────────────────────────────────────────────────────────────

def make_prompts(pid: str, cfg: dict) -> dict:
    color = cfg["color"]
    theme = cfg["theme"]
    adj = cfg["style_adj"]
    has_budget = cfg["has_budget"]
    has_meal = cfg["has_meal"]

    # goals/budget label for image 10
    if has_budget:
        goals_label = "goals and budget tracker"
    elif has_meal:
        goals_label = "goals and meal planner"
    else:
        goals_label = "goals and vision pages"

    prompts = {
        "02_whats_included": (
            f"Clean product flat-lay photograph on a cozy light wood desk. "
            f"Shows: one large planner-style PDF file icon, three PNG sticker sheet thumbnails "
            f"fanned out beside it, small kawaii sticker accents scattered around. "
            f"Color palette: {color}. "
            f"Pastel kawaii aesthetic, bright and airy Etsy shop style. "
            f"No text. Square format. Professional product photography."
        ),
        "05_sticker_library": (
            f"Three kawaii sticker sheets displayed side by side on a pure white background. "
            f"Sheet 1 shows planner stationery stickers: notebooks, pens, stars, washi tape, coffee cups. "
            f"Sheet 2 shows cozy lifestyle stickers: mugs, candles, books, fairy lights, sleeping cat. "
            f"Sheet 3 shows seasonal stickers: cherry blossoms, pumpkins, snowflakes, hearts. "
            f"Color palette inspired by {color}, transparent PNG style, kawaii cute illustration style. "
            f"Bright, clean, professional. Square format."
        ),
        "06_sticker_how_to": (
            f"Pastel kawaii infographic showing 3 numbered steps to import stickers into GoodNotes. "
            f"Step 1: Download and unzip the sticker pack (shows ZIP file icon). "
            f"Step 2: Open GoodNotes Elements, tap Stickers tab, tap + to import (shows iPad icon). "
            f"Step 3: Drag stickers onto any planner page unlimited times (shows cute planner page with sticker). "
            f"Title at top: '3 Easy Steps to Use Your Stickers'. "
            f"Color palette: {color}, kawaii cute font and icons, soft pastel background. "
            f"Square format, clean infographic design."
        ),
        "07_app_compatibility": (
            f"Clean digital product infographic on white/cream background. "
            f"Central icon: a planner document. "
            f"Surrounding it in a circle: GoodNotes icon, Notability icon, PDF Expert icon, Xodo icon, Adobe Acrobat icon. "
            f"Soft pastel connecting lines. "
            f"Label below central icon: 'Works with your favorite apps'. "
            f"Small kawaii star and heart accents. {adj} color accents. "
            f"Professional, clean, Etsy-ready square format."
        ),
        "08_cover_closeup": (
            f"Close-up photo of a Silver iPad Pro 12.9 inch on a cozy desk, "
            f"screen filling most of the frame, showing a beautiful kawaii digital planner cover page. "
            f"The cover has a kawaii illustrated character, {adj}, decorative floral and star borders. "
            f"Apple Pencil resting on the screen edge. "
            f"Background slightly blurred: ceramic mug, a small plant, soft natural window light. "
            f"Style: bright, warm, cozy Etsy lifestyle photography. Square crop. High detail."
        ),
    }
    return prompts

# ── Main execution ─────────────────────────────────────────────────────────────

summary = {}  # pid → {rank: status}

for pid, cfg in PLANNERS.items():
    listing_id = cfg["listing_id"]
    needs = cfg["needs"]
    img_dir = os.path.join(BASE_DIR, f"{pid}_listing_images")
    pdf_path = os.path.join(BASE_DIR, f"{pid}.pdf")
    pages = PAGE_INDICES[pid]

    print(f"\n{'='*60}")
    print(f"Processing {pid} (listing {listing_id})")
    print(f"  Needs ranks: {needs}")
    print(f"{'='*60}")

    summary[pid] = {}
    prompts = make_prompts(pid, cfg)

    # ── Step 1: Render PDF pages ───────────────────────────────────────────

    # Map rank → (page_type, page_index, filename)
    pdf_renders = []

    if "monthly" in pages:
        if pid == "DP1026":
            # DP1026 needs rank 6 = monthly
            if 6 in needs:
                pdf_renders.append((6, pages["monthly"], "06_monthly_spread.jpg"))
        else:
            if 3 in needs:
                pdf_renders.append((3, pages["monthly"], "03_monthly_spread.jpg"))

    if "weekly" in pages:
        if pid == "DP1026":
            if 7 in needs:
                pdf_renders.append((7, pages["weekly"], "07_weekly_spread.jpg"))
        else:
            if 4 in needs:
                pdf_renders.append((4, pages["weekly"], "04_weekly_spread.jpg"))

    if "habit" in pages:
        if pid == "DP1026":
            if 9 in needs:
                pdf_renders.append((9, pages["habit"], "09_habit_tracker.jpg"))
        else:
            if 9 in needs:
                pdf_renders.append((9, pages["habit"], "09_habit_tracker.jpg"))

    # Goals/budget page (rank 10)
    if 10 in needs:
        if "budget" in pages:
            pdf_renders.append((10, pages["budget"], "10_goals_budget.jpg"))
        elif "goals" in pages:
            pdf_renders.append((10, pages["goals"], "10_goals_budget.jpg"))
        elif "meal" in pages:
            pdf_renders.append((10, pages["meal"], "10_goals_budget.jpg"))

    print(f"\n  --- PDF renders ---")
    for rank, page_idx, fname in pdf_renders:
        out_path = os.path.join(img_dir, fname)
        ok = render_pdf_page(pdf_path, page_idx, out_path)
        summary[pid][rank] = "rendered" if ok else "render_failed"

    # ── Step 2: Generate DALL-E images ─────────────────────────────────────

    dalle_map = {
        2: ("02_whats_included.jpg", prompts.get("02_whats_included")),
        5: ("05_sticker_library.jpg", prompts.get("05_sticker_library")),
        6: ("06_sticker_how_to.jpg", prompts.get("06_sticker_how_to")) if pid != "DP1026" else None,
        7: ("07_app_compatibility.jpg", prompts.get("07_app_compatibility")) if pid != "DP1026" else None,
        8: ("08_cover_closeup.jpg", prompts.get("08_cover_closeup")),
    }

    # For DP1026 renaming: its DALL-E needs are at ranks 8 only (06/07 are PDF-rendered monthly/weekly)
    # Let me re-check: DP1026 needs ranks 6,7,8,9,10
    # Per spec: 06=monthly_spread(PDF), 07=weekly_spread(PDF), 08=cover_closeup(DALL-E), 09=habit(PDF), 10=goals(PDF)
    # For DP1027-1029: ranks 2-10
    # 02=whats_included(DALL-E), 03=monthly(PDF), 04=weekly(PDF), 05=sticker_library(DALL-E)
    # 06=sticker_how_to(DALL-E), 07=app_compatibility(DALL-E), 08=cover_closeup(DALL-E)
    # 09=habit_tracker(PDF), 10=goals_budget(PDF)

    if pid == "DP1026":
        dalle_tasks = []
        if 8 in needs:
            dalle_tasks.append((8, "08_cover_closeup.jpg", prompts["08_cover_closeup"]))
    else:
        dalle_tasks = []
        if 2 in needs:
            dalle_tasks.append((2, "02_whats_included.jpg", prompts["02_whats_included"]))
        if 5 in needs:
            dalle_tasks.append((5, "05_sticker_library.jpg", prompts["05_sticker_library"]))
        if 6 in needs:
            dalle_tasks.append((6, "06_sticker_how_to.jpg", prompts["06_sticker_how_to"]))
        if 7 in needs:
            dalle_tasks.append((7, "07_app_compatibility.jpg", prompts["07_app_compatibility"]))
        if 8 in needs:
            dalle_tasks.append((8, "08_cover_closeup.jpg", prompts["08_cover_closeup"]))

    print(f"\n  --- DALL-E generations ---")
    for rank, fname, prompt in dalle_tasks:
        out_path = os.path.join(img_dir, fname)
        ok = generate_image(prompt, out_path)
        summary[pid][rank] = "generated" if ok else "gen_failed"
        time.sleep(1)  # polite rate limiting

    # ── Step 3: Upload all new images ─────────────────────────────────────
    print(f"\n  --- Uploading to Etsy listing {listing_id} ---")

    # Build upload list: rank → filename
    if pid == "DP1026":
        upload_map = {
            6: "06_monthly_spread.jpg",
            7: "07_weekly_spread.jpg",
            8: "08_cover_closeup.jpg",
            9: "09_habit_tracker.jpg",
            10: "10_goals_budget.jpg",
        }
    else:
        upload_map = {
            2: "02_whats_included.jpg",
            3: "03_monthly_spread.jpg",
            4: "04_weekly_spread.jpg",
            5: "05_sticker_library.jpg",
            6: "06_sticker_how_to.jpg",
            7: "07_app_compatibility.jpg",
            8: "08_cover_closeup.jpg",
            9: "09_habit_tracker.jpg",
            10: "10_goals_budget.jpg",
        }

    for rank, fname in sorted(upload_map.items()):
        img_path = os.path.join(img_dir, fname)
        if not os.path.exists(img_path):
            print(f"  [SKIP] rank={rank} {fname} — file not found")
            summary[pid][rank] = "missing"
            continue
        ok = upload_image(listing_id, img_path, rank)
        if ok:
            summary[pid][rank] = summary[pid].get(rank, "ok") + "+uploaded"
        else:
            summary[pid][rank] = summary[pid].get(rank, "?") + "+upload_failed"
        time.sleep(0.5)

# ── Assign shop sections ───────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("Assigning listings to 'Digital Planners' shop section...")
print(f"{'='*60}")

try:
    section_id = client.get_or_create_section("Digital Planners")
    print(f"  Found/created section ID: {section_id}")

    for pid, cfg in PLANNERS.items():
        listing_id = cfg["listing_id"]
        try:
            client.update_listing(listing_id, {"shop_section_id": section_id})
            print(f"  [OK]  {pid} (listing {listing_id}) → section {section_id}")
            summary[pid]["section"] = "assigned"
        except Exception as e:
            print(f"  [ERR] {pid}: {e}")
            summary[pid]["section"] = f"failed: {e}"
except Exception as e:
    print(f"  [ERR] get_or_create_section: {e}")

# ── Summary table ──────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"{'PID':<8} {'Listing ID':<14} {'Ranks uploaded':<30} {'Section'}")
print("-"*70)
for pid, cfg in PLANNERS.items():
    s = summary.get(pid, {})
    ranks = [str(r) for r in sorted(k for k in s.keys() if isinstance(k, int))]
    sec = s.get("section", "not assigned")
    print(f"{pid:<8} {str(cfg['listing_id']):<14} {', '.join(ranks):<30} {sec}")

print("\nDone!")
