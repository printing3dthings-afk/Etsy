"""
Art Creation Tools — generates digital art (DALL-E 3) and printable planner PDFs.

Requires for full functionality:
  OPENAI_API_KEY  — DALL-E 3 image generation
  Pillow          — image processing (pip install Pillow)
  reportlab       — PDF planner generation (pip install reportlab)

Without an OpenAI key the agent operates in "design-brief" mode: it saves a
detailed text concept that can be sent to any image-generation service manually.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path
from typing import Any

from tools.data_store import DataStore
from tools.idea_tools import SUBMIT_IDEA_DEFINITION, handle_submit_idea

DIGITAL_PRODUCTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "digital_products")
PRODUCT_FILES_DIR = os.path.join(DIGITAL_PRODUCTS_DIR, "product_files")


def _ensure_dirs() -> None:
    os.makedirs(PRODUCT_FILES_DIR, exist_ok=True)


def _next_product_id(store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    nums = [int(p["id"][2:]) for p in products if p["id"].startswith("DP") and p["id"][2:].isdigit()]
    return f"DP{max(nums, default=0) + 1:03d}"


# ── TOOL DEFINITIONS ──────────────────────────────────────────────────────────

def _get_design_references(tool_input: dict) -> str:
    refs_meta = Path("data/design_refs_meta.json")
    if not refs_meta.exists():
        return "No design references uploaded yet. The user has not provided style examples."
    try:
        meta = json.loads(refs_meta.read_text())
    except Exception:
        return "No design references available."
    if not meta:
        return "No design references uploaded yet."
    lines = [f"Found {len(meta)} design reference(s) uploaded by the shop owner:\n"]
    for i, ref in enumerate(meta, 1):
        desc = ref.get('description', 'No description provided')
        lines.append(f"{i}. {ref['filename']} ({ref.get('size_kb','?')} KB)")
        lines.append(f"   Style/Theme: {desc}")
        lines.append(f"   Uploaded: {ref.get('uploaded_at','')[:10]}")
    lines.append("\nUse these style descriptions to guide your art creation — match the aesthetic, color palette, and themes described.")
    return "\n".join(lines)


TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "create_art_concept",
        "description": (
            "Design a detailed art concept for a digital product. Saves the concept "
            "to the data store with status 'concept'. Returns the new product ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Product title for Etsy listing"},
                "product_type": {
                    "type": "string",
                    "enum": ["digital_art", "planner", "printable", "wall_art", "clipart"],
                    "description": "Type of digital product",
                },
                "concept": {
                    "type": "string",
                    "description": "Detailed art concept: style, colors, mood, subject, composition",
                },
                "target_audience": {"type": "string", "description": "Who will buy this (e.g. 'boho home decor lovers')"},
                "dimensions": {
                    "type": "string",
                    "description": "Target dimensions, e.g. '3000x3000px 300dpi' or 'A4 PDF'",
                    "default": "3000x3000px 300dpi",
                },
                "price": {"type": "number", "description": "Planned selling price in USD"},
            },
            "required": ["title", "product_type", "concept", "target_audience", "price"],
        },
    },
    {
        "name": "generate_digital_art",
        "description": (
            "Generate the actual image file for a product using DALL-E 3. "
            "Requires OPENAI_API_KEY in .env. Updates product status to 'generated'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
                "dalle_prompt": {
                    "type": "string",
                    "description": "Refined DALL-E 3 prompt. Be specific: style, colors, composition, mood.",
                },
                "image_size": {
                    "type": "string",
                    "enum": ["1024x1024", "1536x1024", "1024x1536"],
                    "description": "1024x1024=square, 1536x1024=landscape, 1024x1536=portrait (best for wall art)",
                    "default": "1024x1536",
                },
                "quality": {
                    "type": "string",
                    "enum": ["standard", "high"],
                    "description": "high produces the most detailed images. Always use high for sellable products.",
                    "default": "high",
                },
            },
            "required": ["product_id", "dalle_prompt"],
        },
    },
    {
        "name": "create_digital_planner",
        "description": (
            "Generate a professional PDF planner using reportlab. "
            "Creates a ready-to-sell digital planner with cover, monthly views, "
            "weekly spreads, daily pages, and habit trackers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
                "planner_title": {"type": "string", "description": "Planner title shown on the cover"},
                "theme_color": {
                    "type": "string",
                    "description": "Primary hex color, e.g. '#8B5CF6' for purple",
                    "default": "#6B7280",
                },
                "accent_color": {
                    "type": "string",
                    "description": "Accent hex color, e.g. '#F59E0B' for gold",
                    "default": "#9CA3AF",
                },
                "year": {
                    "type": "integer",
                    "description": "Planner year (default: current year)",
                },
                "include_sections": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["monthly", "weekly", "daily", "habit_tracker", "notes", "goals"],
                    },
                    "description": "Sections to include in the planner",
                    "default": ["monthly", "weekly", "habit_tracker", "notes"],
                },
            },
            "required": ["product_id", "planner_title"],
        },
    },
    {
        "name": "list_digital_products",
        "description": "List all digital products with their status, file info, and QC results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["all", "concept", "generated", "qc_pending", "approved", "rejected", "listed"],
                    "description": "Filter by product status",
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_digital_product",
        "description": "Get full details of a specific digital product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"}
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "update_product_status",
        "description": "Update the status of a digital product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["concept", "generated", "qc_pending", "approved", "rejected", "listed"],
                },
                "notes": {"type": "string", "description": "Optional notes about the status change"},
            },
            "required": ["product_id", "status"],
        },
    },
    {
        "name": "get_design_references",
        "description": "Get the list of design reference images uploaded by the shop owner. These images represent the style, color palette, and aesthetic the owner wants. Always call this BEFORE creating any new art to ensure your work matches their vision.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    SUBMIT_IDEA_DEFINITION,
]


# ── TOOL EXECUTOR ─────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "create_art_concept":
        return _create_art_concept(tool_input, store)
    if tool_name == "generate_digital_art":
        return _generate_digital_art(tool_input, store)
    if tool_name == "create_digital_planner":
        return _create_digital_planner(tool_input, store)
    if tool_name == "list_digital_products":
        return _list_digital_products(tool_input.get("status_filter", "all"), store)
    if tool_name == "get_digital_product":
        return _get_digital_product(tool_input["product_id"], store)
    if tool_name == "update_product_status":
        return _update_product_status(tool_input, store)
    elif tool_name == "get_design_references":
        return _get_design_references(tool_input)
    if tool_name == "submit_idea":
        return handle_submit_idea(tool_input)
    return f"Unknown art creation tool: {tool_name}"


# ── IMPLEMENTATIONS ───────────────────────────────────────────────────────────

def _create_art_concept(data: dict, store: DataStore) -> str:
    _ensure_dirs()
    product_id = _next_product_id(store)

    product: dict[str, Any] = {
        "id": product_id,
        "title": data["title"],
        "product_type": data["product_type"],
        "concept": data["concept"],
        "target_audience": data["target_audience"],
        "dimensions": data.get("dimensions", "3000x3000px 300dpi"),
        "price": data["price"],
        "status": "concept",
        "file_path": None,
        "file_format": None,
        "file_size_kb": None,
        "qc_status": None,
        "qc_notes": None,
        "etsy_listing_id": None,
        "created_at": str(date.today()),
        "updated_at": str(date.today()),
    }

    products = store.get("digital_products", default=[])
    products.append(product)
    store.set(products, "digital_products")
    store.save()

    return json.dumps({
        "success": True,
        "product_id": product_id,
        "title": product["title"],
        "status": "concept",
        "next_step": "Use generate_digital_art or create_digital_planner to produce the file.",
    }, indent=2)


def _generate_placeholder_art(data: dict, product: dict, store: DataStore) -> str:
    """Generate a styled PNG concept card using Pillow when no OpenAI key is set."""
    product_id = product["id"]
    file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.png")
    prompt = data["dalle_prompt"]
    title = product.get("title", product_id)

    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        W, H = 1024, 1024
        # Build a gradient background by drawing rows
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        # Soft purple-to-teal gradient
        for y in range(H):
            t = y / H
            r = int(80  + (30  - 80)  * t)
            g = int(60  + (140 - 60)  * t)
            b = int(140 + (160 - 140) * t)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Decorative circles
        for cx, cy, cr, alpha in [(150,150,200,40),(874,874,180,30),(512,200,120,25)]:
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill=(255,255,255,alpha))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

        # Card background
        margin = 60
        draw.rounded_rectangle([margin, margin, W-margin, H-margin],
                                radius=32, fill=(255, 255, 255, 0))
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([margin, margin, W-margin, H-margin],
                              radius=32, fill=(20, 20, 40, 180))
        img = Image.alpha_composite(img.convert("RGBA"), card).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Try to load a font, fall back to default
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
            font_body  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except Exception:
            font_title = ImageFont.load_default()
            font_body  = font_title
            font_small = font_title

        # Badge
        badge_text = "CONCEPT — AI ART PENDING"
        draw.rounded_rectangle([margin+20, margin+20, margin+320, margin+50],
                                radius=14, fill=(255, 180, 0))
        draw.text((margin+30, margin+24), badge_text, fill=(20,20,20), font=font_small)

        # Title
        y = margin + 75
        for line in textwrap.wrap(title, 28):
            draw.text((margin+30, y), line, fill=(255,255,255), font=font_title)
            y += 48

        # Divider
        y += 10
        draw.line([(margin+30, y), (W-margin-30, y)], fill=(255,200,100), width=2)
        y += 20

        # Prompt text
        draw.text((margin+30, y), "Design Concept:", fill=(180,220,255), font=font_small)
        y += 28
        for line in textwrap.wrap(prompt, 52)[:12]:
            draw.text((margin+30, y), line, fill=(220,220,220), font=font_body)
            y += 30

        # Footer
        draw.text((margin+30, H-margin-40),
                  f"OnBrandCraftz  •  {product_id}  •  Add OPENAI_API_KEY to generate real art",
                  fill=(150, 150, 180), font=font_small)

        img.save(file_path, "PNG")
        file_size_kb = os.path.getsize(file_path) // 1024

    except ImportError:
        # Pillow not available — write minimal 1×1 white PNG
        import struct, zlib
        def _png1x1():
            sig = b'\x89PNG\r\n\x1a\n'
            def chunk(name, data):
                c = zlib.crc32(name + data) & 0xffffffff
                return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)
            ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
            idat = zlib.compress(b'\x00\xff\xff\xff')
            return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
        with open(file_path, "wb") as f:
            f.write(_png1x1())
        file_size_kb = 1

    product["is_placeholder"] = True
    product["file_hash"] = None

    product["file_path"] = file_path
    product["file_format"] = "PNG"
    product["file_size_kb"] = file_size_kb
    product["status"] = "qc_pending"
    product["updated_at"] = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success": True,
        "product_id": product_id,
        "file_path": file_path,
        "file_size_kb": file_size_kb,
        "mode": "concept_card",
        "note": "Concept card created with Pillow. Add OPENAI_API_KEY to generate real AI art.",
        "status": "qc_pending",
        "next_step": "Send to Quality Check Agent for review. Add OPENAI_API_KEY for real art.",
    }, indent=2)


def _upscale_for_print(src_path: str, dst_path: str, target_px: int = 4500) -> None:
    """Upscale to print resolution with multi-pass sharpening for top Etsy quality."""
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        img = Image.open(src_path).convert("RGB")
        w, h = img.size

        # Multi-pass upscale: 2x steps prevent aliasing artifacts vs single large jump
        while max(img.size) < target_px:
            scale = min(2.0, target_px / max(img.size))
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

        # Two-pass unsharp mask: first pass recovers LANCZOS softness, second sharpens detail
        img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
        img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=80,  threshold=1))

        # Subtle vibrancy and contrast boost (Etsy thumbnails compress heavily)
        img = ImageEnhance.Color(img).enhance(1.08)
        img = ImageEnhance.Contrast(img).enhance(1.05)
        img = ImageEnhance.Sharpness(img).enhance(1.1)

        # 300 DPI metadata — required for print-on-demand buyers
        img.save(dst_path, "PNG", dpi=(300, 300), optimize=False)
    except ImportError:
        import shutil
        shutil.copy2(src_path, dst_path)
    # Clean up raw file
    try:
        os.remove(src_path)
    except OSError:
        pass


def _generate_digital_art(data: dict, store: DataStore) -> str:
    _ensure_dirs()
    product_id = data["product_id"]
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return _generate_placeholder_art(data, product, store)

    try:
        import base64
        # Map size: portrait default for wall art, cap invalid legacy sizes
        raw_size = data.get("image_size", "1024x1536")
        valid_sizes = {"1024x1024", "1536x1024", "1024x1536"}
        size = raw_size if raw_size in valid_sizes else "1024x1536"

        request_body = json.dumps({
            "model": "gpt-image-1",
            "prompt": data["dalle_prompt"],
            "size": size,
            "quality": "high",
            "n": 1,
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=request_body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())

        img_data = result["data"][0].get("b64_json") or result["data"][0].get("url")
        raw_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_raw.png")

        if result["data"][0].get("b64_json"):
            with open(raw_path, "wb") as f:
                f.write(base64.b64decode(img_data))
        else:
            urllib.request.urlretrieve(img_data, raw_path)

        # Upscale + sharpen for print quality
        file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.png")
        _upscale_for_print(raw_path, file_path, target_px=3000)

        file_size_kb = os.path.getsize(file_path) // 1024

        import hashlib as _hashlib
        with open(file_path, "rb") as _hf:
            product["file_hash"] = _hashlib.sha256(_hf.read()).hexdigest()
        product["is_placeholder"] = False

        product["file_path"] = file_path
        product["file_format"] = "PNG"
        product["file_size_kb"] = file_size_kb
        product["status"] = "qc_pending"
        product["updated_at"] = str(date.today())
        _save_product(product, store)

        return json.dumps({
            "success": True,
            "product_id": product_id,
            "file_path": file_path,
            "file_size_kb": file_size_kb,
            "dimensions": "3000x3000px (upscaled for print quality)",
            "status": "qc_pending",
            "next_step": "Send to Quality Check Agent for review.",
        }, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return json.dumps({"error": f"Image API error {e.code}: {error_body}"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _create_digital_planner(data: dict, store: DataStore) -> str:
    _ensure_dirs()
    product_id = data["product_id"]
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})

    try:
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm, mm
    except ImportError:
        brief_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_planner_spec.txt")
        sections = data.get("include_sections", ["monthly", "weekly", "habit_tracker", "notes"])
        with open(brief_path, "w") as f:
            f.write(f"PLANNER SPECIFICATION: {data['planner_title']}\n")
            f.write(f"Theme Color: {data.get('theme_color', '#6B7280')}\n")
            f.write(f"Sections: {', '.join(sections)}\n")
            f.write("Install reportlab: pip install reportlab\n")
        product["file_path"] = brief_path
        product["status"] = "concept"
        product["updated_at"] = str(date.today())
        _save_product(product, store)
        return json.dumps({"warning": "reportlab not installed.", "action_needed": "pip install reportlab"}, indent=2)

    import calendar as cal_mod
    from datetime import date as dt_date, timedelta

    planner_year  = data.get("year", dt_date.today().year)
    sections      = data.get("include_sections", ["monthly", "weekly", "habit_tracker", "goals", "notes"])
    title         = data["planner_title"]
    theme_hex     = data.get("theme_color",  "#5C6BC0").lstrip("#")
    accent_hex    = data.get("accent_color", "#F9A825").lstrip("#")

    def _rgb(h):
        return int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255

    def _blend(rgb, factor):
        """Blend color toward white by factor (0=original, 1=white)."""
        return tuple(c + (1.0 - c) * factor for c in rgb)

    T  = _rgb(theme_hex)    # theme
    A  = _rgb(accent_hex)   # accent
    TL = _blend(T, 0.82)    # theme very light (background tints)
    TM = _blend(T, 0.55)    # theme medium
    AL = _blend(A, 0.78)    # accent light
    DARK  = (0.12, 0.12, 0.16)
    MID   = (0.42, 0.42, 0.46)
    LIGHT = (0.88, 0.88, 0.90)
    WHITE = (1.0,  1.0,  1.0)

    PW, PH = A4   # 595.28 × 841.89 pt
    ML = MR = 36.0   # left/right margin
    MB = 36.0        # bottom margin
    MT = 36.0        # top margin
    CW = PW - ML - MR   # content width  ≈ 523 pt
    CH = PH - MT - MB   # content height ≈ 770 pt

    MONTHS = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
    DAYS_SHORT  = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
    DAYS_LONG   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.pdf")
    c = pdf_canvas.Canvas(file_path, pagesize=A4)

    # ── drawing helpers ──────────────────────────────────────────────────────

    def fill(rgb):   c.setFillColorRGB(*rgb)
    def stroke(rgb): c.setStrokeColorRGB(*rgb)
    def lw(w):       c.setLineWidth(w)
    def font(name, size): c.setFont(name, size)

    def rect(x, y, w, h, f=None, s=None, lwidth=0.5, radius=0):
        if lwidth: lw(lwidth)
        if f: fill(f)
        if s: stroke(s)
        if radius:
            c.roundRect(x, y, w, h, radius, fill=1 if f else 0, stroke=1 if s else 0)
        else:
            c.rect(x, y, w, h, fill=1 if f else 0, stroke=1 if s else 0)

    def hline(x1, x2, y, color=LIGHT, width=0.5):
        lw(width); stroke(color)
        c.line(x1, y, x2, y)

    def vline(x, y1, y2, color=LIGHT, width=0.5):
        lw(width); stroke(color)
        c.line(x, y1, x, y2)

    def text_c(x, y, txt, color=DARK):
        fill(color); c.drawCentredString(x, y, str(txt))

    def text_l(x, y, txt, color=DARK):
        fill(color); c.drawString(x, y, str(txt))

    def text_r(x, y, txt, color=DARK):
        fill(color); c.drawRightString(x, y, str(txt))

    def circle(cx, cy, r, f=None, s=None, lwidth=0.5):
        if lwidth: lw(lwidth)
        if f: fill(f)
        if s: stroke(s)
        c.circle(cx, cy, r, fill=1 if f else 0, stroke=1 if s else 0)

    def page_footer(page_label=""):
        """Consistent footer on every interior page."""
        y = MB - 16
        hline(ML, PW - MR, MB - 8, LIGHT, 0.4)
        font("Helvetica", 6.5); fill(MID)
        c.drawString(ML, y, f"{title}  •  {planner_year}")
        if page_label:
            c.drawCentredString(PW / 2, y, page_label)
        c.drawRightString(PW - MR, y, "OnBrandCraftz")

    def section_header(label, y_top, color=None):
        """Full-width colored header bar returning new y below it."""
        bar_h = 32
        clr = color or T
        rect(ML, y_top - bar_h, CW, bar_h, f=clr)
        font("Helvetica-Bold", 13); fill(WHITE)
        c.drawString(ML + 10, y_top - bar_h + 10, label.upper())
        return y_top - bar_h - 6

    def checkbox(x, y, size=7):
        """Drawn checkbox (rounded square) for interactive feel."""
        rect(x, y, size, size, s=MID, lwidth=0.6, radius=1.5)

    # ── COVER PAGE ──────────────────────────────────────────────────────────

    def draw_cover():
        # Background
        rect(0, 0, PW, PH, f=WHITE)

        # Top color block (62% of page)
        top_h = PH * 0.62
        rect(0, PH - top_h, PW, top_h, f=T)

        # Decorative large circle (bottom-right of color block, partially cut off)
        circle(PW + 30, PH - top_h + 20, 160, f=_blend(T, 0.18))
        # Small decorative circles
        circle(ML + 40, PH - top_h + 110, 28, f=A)
        circle(ML + 90, PH - top_h + 65,  16, f=_blend(A, 0.4))
        circle(PW - ML - 30, PH - 28,     22, f=TL)

        # Thin horizontal accent lines at bottom of color block
        rect(0, PH - top_h - 4, PW, 4,  f=A)
        rect(0, PH - top_h - 10, PW, 3, f=_blend(A, 0.5))

        # Title text (centered in top block)
        cx = PW / 2
        # Large title
        title_words = title.split()
        font("Helvetica-Bold", 42)
        # Try single line, fall back to two lines
        try_line = title if len(title) <= 22 else None
        if try_line:
            fill(WHITE)
            c.drawCentredString(cx, PH - top_h / 2 + 20, try_line)
        else:
            mid = len(title_words) // 2
            line1 = " ".join(title_words[:mid])
            line2 = " ".join(title_words[mid:])
            fill(WHITE)
            c.drawCentredString(cx, PH - top_h / 2 + 32, line1)
            c.drawCentredString(cx, PH - top_h / 2 + 32 - 50, line2)

        # Year badge
        badge_w, badge_h = 90, 28
        rect(cx - badge_w/2, PH - top_h / 2 - 30, badge_w, badge_h, f=A, radius=5)
        font("Helvetica-Bold", 14); fill(DARK)
        c.drawCentredString(cx, PH - top_h / 2 - 30 + 9, str(planner_year))

        # Bottom section tagline
        tagline_y = PH - top_h - 80
        font("Helvetica", 11); fill(MID)
        c.drawCentredString(cx, tagline_y, "plan with purpose  ·  live with intention")

        # Thin accent rule under tagline
        hline(cx - 80, cx + 80, tagline_y - 12, A, 1.2)

        # Sections list (what's inside)
        y = tagline_y - 45
        font("Helvetica-Bold", 8); fill(MID)
        c.drawCentredString(cx, y, "INSIDE THIS PLANNER")
        y -= 14
        font("Helvetica", 9); fill(MID)
        section_labels = {
            "monthly": "Monthly Overview", "weekly": "Weekly Planning",
            "habit_tracker": "Habit Tracker", "goals": "Goals & Vision",
            "notes": "Notes Pages", "daily": "Daily Pages",
        }
        included = [section_labels.get(s, s.title()) for s in sections]
        c.drawCentredString(cx, y, "  ·  ".join(included))

        # Footer
        font("Helvetica", 7); fill(_blend(MID, 0.3))
        c.drawCentredString(cx, MB + 8, "OnBrandCraftz  ·  Digital Download  ·  Personal & Commercial Use")

        c.showPage()

    # ── YEARLY OVERVIEW ─────────────────────────────────────────────────────

    def draw_yearly_overview():
        rect(0, 0, PW, PH, f=WHITE)
        y = section_header(f"{planner_year} at a glance", PH - MT)

        cell_w = CW / 4 - 4
        cell_h = (y - MB - 20) / 3 - 6

        for i, month_name in enumerate(MONTHS):
            col = i % 4
            row = i // 4
            x0 = ML + col * (cell_w + 5.5)
            y0 = y - row * (cell_h + 8) - cell_h

            # Mini month box
            rect(x0, y0, cell_w, cell_h, s=LIGHT, lwidth=0.5, radius=3)
            # Month header
            rect(x0, y0 + cell_h - 16, cell_w, 16, f=T, radius=3)
            font("Helvetica-Bold", 7.5); fill(WHITE)
            c.drawCentredString(x0 + cell_w/2, y0 + cell_h - 11, month_name.upper()[:3])

            # Day-of-week header
            mini_dw = cell_w / 7
            for d, dn in enumerate(["M","T","W","T","F","S","S"]):
                font("Helvetica", 5.5)
                fill(MID if d < 5 else T)
                c.drawCentredString(x0 + d * mini_dw + mini_dw/2, y0 + cell_h - 25, dn)

            # Calendar numbers
            month_num = i + 1
            cal = cal_mod.monthcalendar(planner_year, month_num)
            for ri, week in enumerate(cal):
                for di, day in enumerate(week):
                    if day == 0:
                        continue
                    dx = x0 + di * mini_dw + mini_dw/2
                    dy = y0 + cell_h - 35 - ri * ((cell_h - 36) / max(len(cal), 1))
                    font("Helvetica", 5); fill(T if di >= 5 else DARK)
                    c.drawCentredString(dx, dy, str(day))

        page_footer("YEARLY OVERVIEW")
        c.showPage()

    # ── MONTHLY PAGE ────────────────────────────────────────────────────────

    def draw_monthly_page(month_idx):
        month_name = MONTHS[month_idx]
        month_num  = month_idx + 1
        rect(0, 0, PW, PH, f=WHITE)

        # Header bar
        rect(0, PH - MT - 48, PW, 48 + MT, f=T)
        font("Helvetica-Bold", 26); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 32, month_name.upper())
        font("Helvetica", 14); fill(_blend(WHITE, 0.35))
        c.drawRightString(PW - MR - 10, PH - MT - 32, str(planner_year))

        # Accent strip below header
        rect(0, PH - MT - 52, PW, 4, f=A)

        top_y    = PH - MT - 56   # below header + strip
        cal_top  = top_y - 2
        day_h    = 24             # day-name row height
        # Calendar area: leave 140pt at bottom for notes
        notes_h  = 155
        cal_area = cal_top - MB - notes_h - 10
        num_rows = 6
        row_h    = (cal_area - day_h) / num_rows
        col_w    = CW / 7

        # Day name headers
        for di, dn in enumerate(DAYS_SHORT):
            x0 = ML + di * col_w
            bg = TM if di < 5 else T
            rect(x0, cal_top - day_h, col_w, day_h, f=bg)
            font("Helvetica-Bold", 8); fill(WHITE)
            c.drawCentredString(x0 + col_w/2, cal_top - day_h + 8, dn)

        # Build calendar grid
        cal = cal_mod.monthcalendar(planner_year, month_num)
        for ri in range(num_rows):
            row_y_top = cal_top - day_h - ri * row_h
            for di in range(7):
                cx0 = ML + di * col_w
                cy0 = row_y_top - row_h
                bg = _blend(T, 0.94) if di >= 5 else WHITE
                rect(cx0, cy0, col_w, row_h, f=bg, s=LIGHT, lwidth=0.4)
                if ri < len(cal):
                    day_num = cal[ri][di]
                    if day_num:
                        font("Helvetica-Bold", 9)
                        fill(T if di >= 5 else DARK)
                        c.drawString(cx0 + 5, row_y_top - 14, str(day_num))

        cal_bottom = cal_top - day_h - num_rows * row_h

        # Thin bottom rule
        hline(ML, ML + CW, cal_bottom - 4, LIGHT, 0.5)

        # Notes section (2 columns)
        notes_y_top = cal_bottom - 12
        col2_w  = (CW - 8) / 2
        col2_x2 = ML + col2_w + 8

        for col_x, col_label in [(ML, "MONTHLY GOALS"), (col2_x2, "NOTES & HIGHLIGHTS")]:
            # Label
            font("Helvetica-Bold", 7.5); fill(T)
            c.drawString(col_x, notes_y_top, col_label)
            # Lines
            line_y = notes_y_top - 16
            n_lines = int((notes_y_top - MB - 16) / 14)
            for _ in range(n_lines):
                hline(col_x, col_x + col2_w, line_y, LIGHT, 0.5)
                line_y -= 14

        page_footer(f"{month_name.upper()} {planner_year}")
        c.showPage()

    # ── WEEKLY PAGE ─────────────────────────────────────────────────────────

    def draw_weekly_page(week_num, start_date):
        end_date = start_date + timedelta(days=6)
        rect(0, 0, PW, PH, f=WHITE)

        # Header
        rect(0, PH - MT - 44, PW, 44 + MT, f=T)
        font("Helvetica-Bold", 18); fill(WHITE)
        week_label = f"WEEK {week_num:02d}"
        c.drawString(ML + 10, PH - MT - 28, week_label)
        date_label = f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"
        font("Helvetica", 10); fill(_blend(WHITE, 0.3))
        c.drawRightString(PW - MR - 10, PH - MT - 28, date_label)
        rect(0, PH - MT - 47, PW, 3, f=A)

        top_y    = PH - MT - 52
        # Left schedule area (65%)
        sched_w  = CW * 0.64
        sidebar_w = CW - sched_w - 8
        sidebar_x = ML + sched_w + 8

        day_h    = (top_y - MB) / 7
        line_color = (0.91, 0.91, 0.93)

        for di, (day_name, day_date) in enumerate(
            [(DAYS_LONG[d], start_date + timedelta(days=d)) for d in range(7)]
        ):
            dy_top = top_y - di * day_h
            dy_bot = dy_top - day_h
            is_weekend = di >= 5

            # Day header strip
            hdr_h = 18
            bg = TM if is_weekend else T
            rect(ML, dy_top - hdr_h, sched_w, hdr_h, f=bg)
            font("Helvetica-Bold", 8); fill(WHITE)
            c.drawString(ML + 6, dy_top - 13, day_name.upper())
            font("Helvetica", 7.5); fill(_blend(WHITE, 0.25))
            c.drawRightString(ML + sched_w - 6, dy_top - 13, day_date.strftime("%b %d"))

            # Writing lines
            n_lines = 3
            line_spacing = (day_h - hdr_h - 4) / n_lines
            for li in range(n_lines):
                ly = dy_top - hdr_h - 4 - li * line_spacing - line_spacing * 0.6
                hline(ML + 4, ML + sched_w - 4, ly, line_color, 0.4)

            # Left border accent dot
            circle(ML + 3, dy_top - hdr_h - (day_h - hdr_h)/2, 2.5, f=bg)

            # Day separator
            if di < 6:
                hline(ML, ML + sched_w, dy_bot, LIGHT, 0.5)

        # Right sidebar
        sb_y = top_y

        def sidebar_box(label, height, icon=""):
            nonlocal sb_y
            # Label
            font("Helvetica-Bold", 7.5); fill(T)
            c.drawString(sidebar_x, sb_y - 12, (icon + " " + label).strip().upper())
            # Box outline
            rect(sidebar_x, sb_y - 12 - height, sidebar_w, height, s=LIGHT, lwidth=0.5, radius=2)
            # Lines inside
            n = max(2, int(height / 14) - 1)
            for i in range(n):
                ly = sb_y - 12 - height + (i + 1) * (height / (n + 1))
                hline(sidebar_x + 4, sidebar_x + sidebar_w - 4, ly, line_color, 0.4)
            sb_y -= (height + 20)

        sidebar_box("TOP PRIORITIES", 80)
        sidebar_box("NOTES", 110)

        # Habit mini-tracker (bottom of sidebar)
        habit_y = MB + 45
        font("Helvetica-Bold", 7); fill(MID)
        c.drawString(sidebar_x, habit_y + 18, "HABITS")
        for hi in range(5):
            hx = sidebar_x + hi * (sidebar_w / 5) + 2
            checkbox(hx, habit_y, 9)
            font("Helvetica", 5.5); fill(MID)
            c.drawCentredString(hx + 4.5, habit_y - 7, str(hi + 1))

        # Water tracker
        water_y = habit_y + 30
        font("Helvetica-Bold", 7); fill(MID)
        c.drawString(sidebar_x, water_y, "WATER")
        for wi in range(8):
            wx = sidebar_x + wi * (sidebar_w / 8)
            circle(wx + 4, water_y - 10, 3.5, s=_blend(T, 0.5), lwidth=0.6)

        page_footer(f"WEEK {week_num}")
        c.showPage()

    # ── HABIT TRACKER ────────────────────────────────────────────────────────

    def draw_habit_tracker():
        rect(0, 0, PW, PH, f=WHITE)
        y = section_header("Habit Tracker", PH - MT)

        n_habits = 10
        n_days   = 31
        label_w  = 110
        cell_w   = (CW - label_w) / n_days
        hdr_h    = 22
        cell_h   = (y - MB - 40 - hdr_h) / n_habits

        # Column headers (day numbers)
        for di in range(n_days):
            dx = ML + label_w + di * cell_w
            # Alternate column shading for weekends (approximate)
            if di % 7 >= 5:
                rect(dx, MB + 40, cell_w, y - MB - 40, f=_blend(T, 0.95))
            font("Helvetica-Bold", 6.5)
            fill(T if di % 7 >= 5 else MID)
            c.drawCentredString(dx + cell_w/2, y - hdr_h + 6, str(di + 1))

        # Header divider
        hline(ML, ML + CW, y - hdr_h, T, 1.0)
        hline(ML, ML + CW, y - hdr_h - 1, AL, 0.5)

        # Habit rows
        palette = [T, A, _blend(T, 0.35), _blend(A, 0.4), TM,
                   _blend(T, 0.6), AL, _blend(A, 0.25), T, A]
        for hi in range(n_habits):
            row_y = y - hdr_h - (hi + 1) * cell_h
            row_color = palette[hi % len(palette)]

            # Row background alternation
            if hi % 2 == 0:
                rect(ML, row_y, CW, cell_h, f=_blend(WHITE, 0.0))
            else:
                rect(ML, row_y, CW, cell_h, f=_blend(LIGHT, 0.5))

            # Habit label pill
            pill_h = min(cell_h - 4, 18)
            rect(ML + 2, row_y + (cell_h - pill_h)/2, label_w - 8, pill_h, f=row_color, radius=3)
            font("Helvetica-Bold", 7); fill(WHITE)
            c.drawString(ML + 8, row_y + (cell_h - pill_h)/2 + 5, f"Habit {hi + 1}")

            # Day checkboxes
            for di in range(n_days):
                dx = ML + label_w + di * cell_w
                box_size = min(cell_w - 3, cell_h - 5)
                box_x = dx + (cell_w - box_size) / 2
                box_y = row_y + (cell_h - box_size) / 2
                rect(box_x, box_y, box_size, box_size, s=_blend(row_color, 0.35), lwidth=0.5, radius=1.5)

            # Row separator
            hline(ML, ML + CW, row_y, LIGHT, 0.3)

        # Label column header
        rect(ML, y - hdr_h, label_w, hdr_h, f=T)
        font("Helvetica-Bold", 8); fill(WHITE)
        c.drawString(ML + 8, y - hdr_h + 7, "HABIT")

        # Outer border
        rect(ML, MB + 40, CW, y - MB - 40, s=_blend(T, 0.4), lwidth=0.8)

        page_footer("HABIT TRACKER")
        c.showPage()

    # ── GOALS PAGE ──────────────────────────────────────────────────────────

    def draw_goals_page():
        rect(0, 0, PW, PH, f=WHITE)
        y = section_header("Goals & Vision", PH - MT)

        # Decorative circles top-right
        circle(PW - ML - 20, PH - MT - 20, 55, f=_blend(A, 0.88))
        circle(PW - ML + 10, PH - MT - 80, 30, f=_blend(T, 0.9))

        # Word of the year
        font("Helvetica-Bold", 8); fill(T)
        c.drawString(ML, y - 18, "MY WORD OF THE YEAR")
        rect(ML, y - 18 - 34, CW, 34, s=LIGHT, lwidth=0.5, radius=3)
        y -= 68

        # Top 3 goals with numbered boxes
        font("Helvetica-Bold", 9); fill(DARK)
        c.drawString(ML, y, "MY TOP 3 GOALS FOR THE YEAR")
        y -= 14
        for gi in range(3):
            box_h = 58
            # Number circle
            circle(ML + 14, y - box_h/2 + 8, 12, f=T)
            font("Helvetica-Bold", 11); fill(WHITE)
            c.drawCentredString(ML + 14, y - box_h/2 + 4, str(gi + 1))
            # Goal box
            rect(ML + 30, y - box_h, CW - 30, box_h, s=LIGHT, lwidth=0.5, radius=3)
            # Label lines inside
            font("Helvetica", 7.5); fill(MID)
            c.drawString(ML + 38, y - 13, "GOAL")
            hline(ML + 30, ML + CW, y - 14, LIGHT, 0.4)
            c.drawString(ML + 38, y - 28, "WHY IT MATTERS")
            hline(ML + 30, ML + CW, y - 29, LIGHT, 0.4)
            c.drawString(ML + 38, y - 43, "FIRST STEP")
            y -= box_h + 12

        # Affirmations section
        font("Helvetica-Bold", 8); fill(T)
        c.drawString(ML, y, "AFFIRMATIONS & INTENTIONS")
        y -= 14
        n_lines = int((y - MB) / 16)
        for _ in range(n_lines):
            hline(ML, ML + CW, y, LIGHT, 0.5)
            y -= 16

        page_footer("GOALS & VISION")
        c.showPage()

    # ── NOTES PAGE ──────────────────────────────────────────────────────────

    def draw_notes_page(page_num=1):
        rect(0, 0, PW, PH, f=WHITE)

        # Minimal header
        rect(ML, PH - MT - 38, CW, 38, f=_blend(T, 0.92))
        rect(ML, PH - MT - 38, 5, 38, f=T)
        font("Helvetica-Bold", 16); fill(T)
        c.drawString(ML + 16, PH - MT - 25, "NOTES")
        font("Helvetica", 8); fill(MID)
        c.drawRightString(ML + CW, PH - MT - 25, f"page {page_num}")

        # Dot grid (professional planner staple)
        dot_spacing = 14
        dot_r = 0.8
        start_x = ML + dot_spacing
        start_y = PH - MT - 38 - 16
        end_y   = MB + 20
        x = start_x
        while x <= ML + CW - dot_spacing:
            y = start_y
            while y >= end_y:
                circle(x, y, dot_r, f=LIGHT)
                y -= dot_spacing
            x += dot_spacing

        # Left accent line
        rect(ML, end_y, 2, start_y - end_y + dot_spacing, f=_blend(T, 0.75))

        page_footer(f"NOTES  {page_num}")
        c.showPage()

    # ── ASSEMBLE PLANNER ────────────────────────────────────────────────────

    page_count = 0
    draw_cover()
    page_count += 1

    if "yearly_overview" in sections or "monthly" in sections:
        draw_yearly_overview()
        page_count += 1

    if "monthly" in sections:
        for mi in range(12):
            draw_monthly_page(mi)
            page_count += 1

    if "weekly" in sections:
        # Walk ISO weeks for the planner year
        first_day = dt_date(planner_year, 1, 1)
        # Start from Monday of week 1
        start = first_day - timedelta(days=first_day.weekday())
        if start.year < planner_year:
            start += timedelta(weeks=1)
        week_num = 1
        while start.year <= planner_year and week_num <= 52:
            draw_weekly_page(week_num, start)
            page_count += 1
            start += timedelta(weeks=1)
            week_num += 1

    if "habit_tracker" in sections:
        draw_habit_tracker()
        page_count += 1

    if "goals" in sections:
        draw_goals_page()
        page_count += 1

    if "notes" in sections:
        for ni in range(4):
            draw_notes_page(ni + 1)
            page_count += 1

    c.save()
    file_size_kb = os.path.getsize(file_path) // 1024

    import hashlib as _hashlib
    with open(file_path, "rb") as _hf:
        product["file_hash"] = _hashlib.sha256(_hf.read()).hexdigest()
    product["is_placeholder"] = False

    product["file_path"] = file_path
    product["file_format"] = "PDF"
    product["file_size_kb"] = file_size_kb
    product["status"] = "qc_pending"
    product["updated_at"] = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success": True,
        "product_id": product_id,
        "file_path": file_path,
        "file_size_kb": file_size_kb,
        "pages": page_count,
        "sections": sections,
        "design": {
            "theme_color": f"#{theme_hex}",
            "accent_color": f"#{accent_hex}",
            "style": "premium minimalist with color-blocked headers and dot-grid notes",
        },
        "status": "qc_pending",
        "next_step": "Send to Quality Check Agent for design review.",
    }, indent=2)


def _list_digital_products(status_filter: str, store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    if status_filter != "all":
        products = [p for p in products if p.get("status") == status_filter]
    summary = [
        {
            "id": p["id"],
            "title": p["title"],
            "type": p["product_type"],
            "status": p["status"],
            "format": p.get("file_format"),
            "price": p["price"],
            "qc_status": p.get("qc_status"),
            "created_at": p["created_at"],
        }
        for p in products
    ]
    return json.dumps({"products": summary, "count": len(summary)}, indent=2)


def _get_digital_product(product_id: str, store: DataStore) -> str:
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})
    return json.dumps(product, indent=2)


def _update_product_status(data: dict, store: DataStore) -> str:
    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Product {data['product_id']} not found"})
    old_status = product["status"]
    product["status"] = data["status"]
    if data.get("notes"):
        product["status_notes"] = data["notes"]
    product["updated_at"] = str(date.today())
    _save_product(product, store)
    return json.dumps({"success": True, "product_id": data["product_id"],
                       "previous_status": old_status, "new_status": data["status"]}, indent=2)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _find_product(product_id: str, store: DataStore) -> dict | None:
    products = store.get("digital_products", default=[])
    return next((p for p in products if p["id"] == product_id), None)


def _save_product(product: dict, store: DataStore) -> None:
    products = store.get("digital_products", default=[])
    for i, p in enumerate(products):
        if p["id"] == product["id"]:
            products[i] = product
            break
    store.set(products, "digital_products")
    store.save()
