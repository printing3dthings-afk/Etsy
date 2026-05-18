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

# ── Color scheme presets — 8 complete packages ────────────────────────────────
# Each scheme: theme, accent, bg, dark, mid, light (all normalized 0–1 RGB tuples)
COLOR_SCHEMES: dict[str, dict] = {
    "sage_cream": {
        "label":  "Sage & Cream",
        "theme":  (0.529, 0.659, 0.467),   # #87A878 sage green
        "accent": (0.788, 0.643, 0.298),   # #C9A84C warm gold
        "bg":     (0.980, 0.969, 0.945),   # #FAF7F2 warm cream
        "dark":   (0.14, 0.18, 0.13),
        "mid":    (0.43, 0.50, 0.41),
        "light":  (0.86, 0.90, 0.85),
    },
    "dusty_rose": {
        "label":  "Dusty Rose",
        "theme":  (0.769, 0.545, 0.624),   # #C48B9F
        "accent": (0.549, 0.482, 0.459),   # #8C7B75 warm gray
        "bg":     (0.980, 0.961, 0.941),   # #FAF5F0
        "dark":   (0.22, 0.16, 0.19),
        "mid":    (0.50, 0.42, 0.46),
        "light":  (0.91, 0.87, 0.89),
    },
    "midnight_navy": {
        "label":  "Midnight Navy",
        "theme":  (0.106, 0.165, 0.290),   # #1B2A4A deep navy
        "accent": (0.788, 0.643, 0.298),   # #C9A84C gold
        "bg":     (0.980, 0.982, 0.984),   # near white
        "dark":   (0.10, 0.10, 0.14),
        "mid":    (0.40, 0.42, 0.46),
        "light":  (0.87, 0.88, 0.90),
    },
    "terracotta": {
        "label":  "Terracotta & Forest",
        "theme":  (0.757, 0.482, 0.353),   # #C17B5A
        "accent": (0.290, 0.404, 0.255),   # #4A6741 forest green
        "bg":     (0.961, 0.929, 0.843),   # #F5ECD7 warm beige
        "dark":   (0.22, 0.15, 0.12),
        "mid":    (0.50, 0.40, 0.35),
        "light":  (0.91, 0.87, 0.83),
    },
    "lavender_dreams": {
        "label":  "Lavender Dreams",
        "theme":  (0.525, 0.400, 0.667),   # #8666AA muted purple
        "accent": (0.765, 0.694, 0.882),   # #C3B1E1 soft lavender
        "bg":     (0.977, 0.973, 0.988),   # very light lavender
        "dark":   (0.18, 0.14, 0.22),
        "mid":    (0.45, 0.41, 0.52),
        "light":  (0.89, 0.87, 0.93),
    },
    "dark_academia": {
        "label":  "Dark Academia",
        "theme":  (0.110, 0.110, 0.118),   # #1C1C1E near black
        "accent": (0.722, 0.451, 0.200),   # #B87333 copper
        "bg":     (0.961, 0.941, 0.910),   # #F5F0E8 aged cream
        "dark":   (0.10, 0.10, 0.12),
        "mid":    (0.38, 0.36, 0.33),
        "light":  (0.82, 0.80, 0.77),
    },
    "blush_gold": {
        "label":  "Blush & Gold",
        "theme":  (0.714, 0.384, 0.467),   # #B66277 deep blush
        "accent": (0.831, 0.686, 0.216),   # #D4AF37 gold
        "bg":     (0.996, 0.988, 0.992),   # near white with blush tint
        "dark":   (0.22, 0.16, 0.18),
        "mid":    (0.52, 0.44, 0.46),
        "light":  (0.93, 0.89, 0.91),
    },
    "minimal_mono": {
        "label":  "Minimal Monochrome",
        "theme":  (0.176, 0.176, 0.176),   # #2D2D2D charcoal
        "accent": (0.420, 0.447, 0.502),   # #6B7280 cool gray
        "bg":     (0.996, 0.996, 0.996),   # pure white
        "dark":   (0.12, 0.12, 0.12),
        "mid":    (0.42, 0.42, 0.42),
        "light":  (0.88, 0.88, 0.88),
    },
}


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
            "Generate a premium interactive PDF planner using reportlab. "
            "Creates a ready-to-sell digital planner with: a stunning cover page, "
            "hyperlinked side-tab navigation (GoodNotes/Notability compatible), "
            "fillable text form fields, interactive checkboxes, monthly/weekly/habit/goals/notes sections, "
            "and a 'How to Use' instruction page. Choose one of 8 curated color scheme packages."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"},
                "planner_title": {"type": "string", "description": "Planner title shown on the cover"},
                "color_scheme": {
                    "type": "string",
                    "enum": [
                        "sage_cream", "dusty_rose", "midnight_navy", "terracotta",
                        "lavender_dreams", "dark_academia", "blush_gold", "minimal_mono",
                    ],
                    "description": (
                        "Named color scheme package. sage_cream=Sage & Cream (earthy, popular), "
                        "dusty_rose=Dusty Rose (feminine, bestseller), "
                        "midnight_navy=Midnight Navy + Gold (premium professional), "
                        "terracotta=Terracotta & Forest (warm earthy), "
                        "lavender_dreams=Lavender Dreams (soft, calm), "
                        "dark_academia=Dark Academia (rich, dramatic), "
                        "blush_gold=Blush & Gold (elegant, feminine), "
                        "minimal_mono=Minimal Monochrome (clean, modern). "
                        "Default: sage_cream."
                    ),
                    "default": "sage_cream",
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Add fillable PDF form fields and interactive checkboxes (recommended: true). Works in Adobe Reader, Preview, GoodNotes, Notability, Xodo.",
                    "default": True,
                },
                "planner_format": {
                    "type": "string",
                    "enum": ["letter", "a4"],
                    "description": "Page size. letter=8.5x11in (US standard), a4=210x297mm (international). Default: letter.",
                    "default": "letter",
                },
                "year": {
                    "type": "integer",
                    "description": "Planner year. Use 0 for undated (evergreen, outsells dated 3:1).",
                },
                "include_sections": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["monthly", "weekly", "daily", "habit_tracker", "notes", "goals", "budget", "meal_plan"],
                    },
                    "description": "Sections to include. Always include at minimum: monthly, weekly, habit_tracker, goals, notes.",
                    "default": ["monthly", "weekly", "habit_tracker", "goals", "notes"],
                },
                "subtitle": {
                    "type": "string",
                    "description": "Optional subtitle shown below the title on the cover, e.g. 'Undated Daily Planner' or '2026 Annual Planner'.",
                },
                "cover_image_path": {
                    "type": "string",
                    "description": "Optional path to a hand-painted cover image generated by generate_digital_art. Embeds the art image in the top panel of the cover page for a premium, handcrafted look. Pass the file_path returned by generate_digital_art.",
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
        # Use min(img.size) so the SHORTEST side reaches target_px (QC requirement)
        while min(img.size) < target_px:
            scale = min(2.0, target_px / min(img.size))
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

        # Three-pass sharpening: recover LANCZOS softness → fine detail → final crisp
        img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=2))
        img = img.filter(ImageFilter.UnsharpMask(radius=0.6, percent=90,  threshold=1))
        img = img.filter(ImageFilter.UnsharpMask(radius=0.3, percent=50,  threshold=0))

        # Vibrancy + contrast boost for Etsy thumbnail pop (thumbnails compress heavily)
        img = ImageEnhance.Color(img).enhance(1.12)
        img = ImageEnhance.Contrast(img).enhance(1.08)
        img = ImageEnhance.Sharpness(img).enhance(1.15)

        # Save at 97% JPEG — noticeably better fine detail vs 95%, still well under 20 MB
        jpg_path = os.path.splitext(dst_path)[0] + ".jpg"
        img.save(jpg_path, "JPEG", quality=97, dpi=(300, 300), optimize=True)
        # If caller expected a different extension, also write there (no-op if same)
        if jpg_path != dst_path:
            import shutil as _shutil
            _shutil.move(jpg_path, dst_path)
    except ImportError:
        raise RuntimeError("Pillow is required for print upscaling — run: pip install Pillow")
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
            with urllib.request.urlopen(img_data, timeout=60) as _r:
                with open(raw_path, "wb") as _f:
                    _f.write(_r.read())

        # Upscale + sharpen for print quality; output is JPEG (smaller, still print-quality)
        file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.jpg")
        _upscale_for_print(raw_path, file_path, target_px=3000)

        file_size_kb = os.path.getsize(file_path) // 1024

        import hashlib as _hashlib
        with open(file_path, "rb") as _hf:
            product["file_hash"] = _hashlib.sha256(_hf.read()).hexdigest()
        product["is_placeholder"] = False

        product["file_path"] = file_path
        product["file_format"] = "JPEG"
        product["file_size_kb"] = file_size_kb
        product["status"] = "qc_pending"
        product["updated_at"] = str(date.today())
        _save_product(product, store)

        return json.dumps({
            "success": True,
            "product_id": product_id,
            "file_path": file_path,
            "file_size_kb": file_size_kb,
            "dimensions": "3000px min-side JPEG 95% @ 300 DPI (print-ready)",
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

    # ── resolve color scheme ──────────────────────────────────────────────────
    scheme_key = data.get("color_scheme", "sage_cream")
    if scheme_key not in COLOR_SCHEMES:
        scheme_key = "sage_cream"
    cs = COLOR_SCHEMES[scheme_key]
    T      = cs["theme"]
    A      = cs["accent"]
    BG     = cs["bg"]
    DARK   = cs["dark"]
    MID    = cs["mid"]
    LIGHT  = cs["light"]
    WHITE  = (1.0, 1.0, 1.0)

    def _blend(rgb, factor):
        return tuple(c + (1.0 - c) * factor for c in rgb)

    TL  = _blend(T, 0.82)
    TM  = _blend(T, 0.50)
    AL  = _blend(A, 0.75)
    BGL = _blend(BG, -0.03) if BG[0] > 0.5 else _blend(BG, 0.15)

    # ── page setup ────────────────────────────────────────────────────────────
    try:
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.pagesizes import A4, LETTER
        from reportlab.lib.colors import Color
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
    except ImportError:
        brief_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_planner_spec.txt")
        with open(brief_path, "w") as f:
            f.write(f"PLANNER SPEC: {data['planner_title']}\nInstall: pip install reportlab\n")
        product["file_path"] = brief_path
        product["status"] = "concept"
        product["updated_at"] = str(date.today())
        _save_product(product, store)
        return json.dumps({"warning": "reportlab not installed.", "action_needed": "pip install reportlab"}, indent=2)

    import calendar as cal_mod
    from datetime import date as dt_date, timedelta

    fmt = data.get("planner_format", "letter")
    PW, PH = LETTER if fmt == "letter" else A4

    ML = MR = 36.0
    MT = MB = 32.0
    CW = PW - ML - MR
    CH = PH - MT - MB

    # nav tab dimensions (right-side stacked tabs)
    TAB_W  = 28.0
    TAB_H  = 18.0
    TAB_GAP = 1.5
    TAB_X   = PW - TAB_W - 2.0

    is_interactive = data.get("interactive", True)
    planner_year   = data.get("year", dt_date.today().year)
    undated        = (planner_year == 0)
    if undated:
        planner_year = dt_date.today().year

    sections = data.get("include_sections", ["monthly", "weekly", "habit_tracker", "goals", "notes"])
    title    = data["planner_title"]
    subtitle = data.get("subtitle", "")

    MONTHS     = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
    DAYS_SHORT = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
    DAYS_LONG  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.pdf")
    c = pdf_canvas.Canvas(file_path, pagesize=(PW, PH))
    c.setTitle(title)
    c.setAuthor("OnBrandCraftz")
    c.setSubject(f"Digital Planner — {cs['label']} color scheme")
    c.setCreator("OnBrandCraftz Planner Design Agent")

    # ── Color helper for acroForm (needs reportlab Color objects) ─────────────
    def _col(rgb): return Color(rgb[0], rgb[1], rgb[2])

    # ── Drawing helpers ───────────────────────────────────────────────────────
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

    def hline(x1, x2, y, color=None, width=0.5):
        lw(width); stroke(color or LIGHT)
        c.line(x1, y, x2, y)

    def vline(x, y1, y2, color=None, width=0.5):
        lw(width); stroke(color or LIGHT)
        c.line(x, y1, x, y2)

    def circle(cx, cy, r, f=None, s=None, lwidth=0.5):
        if lwidth: lw(lwidth)
        if f: fill(f)
        if s: stroke(s)
        c.circle(cx, cy, r, fill=1 if f else 0, stroke=1 if s else 0)

    def page_bg():
        rect(0, 0, PW, PH, f=BG)

    def page_footer(label=""):
        hline(ML, PW - MR - TAB_W - 4, MB - 6, LIGHT, 0.4)
        font("Helvetica", 6); fill(MID)
        year_str = "" if undated else str(planner_year)
        c.drawString(ML, MB - 16, f"{title}  •  {year_str}".strip(" •"))
        if label:
            c.drawCentredString((PW - TAB_W) / 2, MB - 16, label)
        c.drawRightString(PW - MR - TAB_W - 6, MB - 16, "OnBrandCraftz")

    # ── Navigation tab bookmark registry ─────────────────────────────────────
    # We build this list in order; each entry is (label, bookmark_key)
    NAV_TABS: list[tuple[str, str]] = []
    if "monthly" in sections:
        for m in MONTHS:
            NAV_TABS.append((m[:3].upper(), f"month_{m[:3].lower()}"))
    if "weekly"       in sections: NAV_TABS.append(("WK",    "weekly_start"))
    if "habit_tracker"in sections: NAV_TABS.append(("HABIT", "habits"))
    if "goals"        in sections: NAV_TABS.append(("GOALS", "goals"))
    if "budget"       in sections: NAV_TABS.append(("BUDG",  "budget"))
    if "meal_plan"    in sections: NAV_TABS.append(("MEAL",  "meal_plan"))
    if "notes"        in sections: NAV_TABS.append(("NOTES", "notes"))

    def draw_nav_tabs(active_bm=None):
        """Draw side navigation tabs on every interior page."""
        start_y = PH - MT - 20
        for i, (label, bm) in enumerate(NAV_TABS):
            ty = start_y - i * (TAB_H + TAB_GAP)
            if ty < MB:
                break
            is_active = (bm == active_bm)
            tab_color = T if is_active else _blend(T, 0.68)
            text_color = WHITE if is_active else _blend(WHITE, 0.25)
            rect(TAB_X, ty, TAB_W, TAB_H, f=tab_color, radius=3)
            c.saveState()
            c.translate(TAB_X + TAB_W / 2, ty + TAB_H / 2)
            c.rotate(90)
            font("Helvetica-Bold", 5.5)
            fill(text_color)
            c.drawCentredString(0, -2, label)
            c.restoreState()
            # Clickable internal link
            c.linkAbsolute(label, bm, (TAB_X, ty, TAB_X + TAB_W, ty + TAB_H))

    # ── Fillable field helpers ────────────────────────────────────────────────
    _field_counter = [0]

    def text_field(x, y, w, h, name_hint="field", multiline=False, font_size=9):
        if not is_interactive:
            rect(x, y, w, h, s=_blend(LIGHT, -0.05), lwidth=0.4, radius=1)
            return
        _field_counter[0] += 1
        fname = f"{product_id}_{name_hint}_{_field_counter[0]}"
        flags = "multiline" if multiline else ""
        c.acroForm.textfield(
            name=fname,
            tooltip=name_hint.replace("_", " ").title(),
            x=x, y=y, width=w, height=h,
            borderStyle="underlined",
            borderColor=_col(_blend(LIGHT, -0.1)),
            fillColor=_col(BG),
            textColor=_col(DARK),
            fontSize=font_size,
            forceBorder=True,
            fieldFlags=flags,
        )

    def checkbox_field(x, y, size=9, name_hint="cb"):
        if not is_interactive:
            rect(x, y, size, size, s=_blend(LIGHT, -0.05), lwidth=0.5, radius=1.5)
            return
        _field_counter[0] += 1
        fname = f"{product_id}_{name_hint}_{_field_counter[0]}"
        c.acroForm.checkbox(
            name=fname,
            tooltip="Check when complete",
            x=x, y=y,
            size=size,
            borderWidth=0.6,
            borderColor=_col(MID),
            fillColor=_col(BG),
            textColor=_col(T),
            buttonStyle="check",
            forceBorder=True,
        )

    # ── COVER PAGE ───────────────────────────────────────────────────────────
    def draw_cover():
        c.bookmarkPage("cover")
        c.addOutlineEntry("Cover", "cover", level=0)
        rect(0, 0, PW, PH, f=BG)

        top_h = PH * 0.58
        cover_img_path = data.get("cover_image_path") or ""
        use_art = cover_img_path and os.path.exists(cover_img_path)

        if use_art:
            try:
                c.drawImage(ImageReader(cover_img_path), 0, PH - top_h, PW, top_h,
                            preserveAspectRatio=False)
                # Alpha wash anchors the title text against any cover artwork
                c.setFillAlpha(0.52)
                c.setFillColorRGB(*T)
                c.rect(0, PH - top_h, PW, top_h * 0.42, fill=1, stroke=0)
                c.setFillAlpha(1.0)
            except Exception:
                use_art = False
        if not use_art:
            rect(0, PH - top_h, PW, top_h, f=T)
            circle(PW - 18, PH - 18, 120, f=_blend(T, 0.22))
            circle(22, PH - top_h + 22, 55,  f=A)
            circle(50, PH - top_h + 85,  22,  f=AL)
            circle(PW - 55, PH - top_h + 55, 16, f=_blend(A, 0.55))

        # Accent stripe at base of art/color block
        rect(0, PH - top_h - 6, PW, 6, f=A)
        rect(0, PH - top_h - 10, PW, 3, f=AL)

        # Title
        cx = PW / 2
        words = title.split()
        font("Helvetica-Bold", 40)
        fill(WHITE)
        if len(title) <= 22:
            c.drawCentredString(cx, PH - top_h / 2 + 18, title)
        else:
            mid = len(words) // 2
            c.drawCentredString(cx, PH - top_h / 2 + 34, " ".join(words[:mid]))
            c.drawCentredString(cx, PH - top_h / 2 - 14, " ".join(words[mid:]))

        # Year / undated badge
        badge_label = "UNDATED" if undated else str(planner_year)
        bw = 82; bh = 26
        rect(cx - bw/2, PH - top_h / 2 - 54, bw, bh, f=A, radius=5)
        font("Helvetica-Bold", 13); fill(DARK)
        c.drawCentredString(cx, PH - top_h / 2 - 54 + 8, badge_label)

        # Subtitle
        if subtitle:
            font("Helvetica", 11); fill(WHITE)
            c.drawCentredString(cx, PH - top_h / 2 - 90, subtitle.upper())

        # Bottom info block
        info_top = PH - top_h - 40
        font("Helvetica", 9); fill(MID)
        c.drawCentredString(cx, info_top, "plan with purpose  \xb7  live with intention")
        hline(cx - 70, cx + 70, info_top - 10, A, 1.0)

        # Included sections list
        info_y = info_top - 28
        font("Helvetica-Bold", 7.5); fill(MID)
        c.drawCentredString(cx, info_y, "INSIDE THIS PLANNER")
        info_y -= 14
        section_labels = {
            "monthly":"Monthly Overview","weekly":"Weekly Planning",
            "habit_tracker":"Habit Tracker","goals":"Goals & Vision",
            "notes":"Notes Pages","daily":"Daily Pages",
            "budget":"Budget Tracker","meal_plan":"Meal Planning",
        }
        included = "  \xb7  ".join(section_labels.get(s, s.title()) for s in sections)
        font("Helvetica", 8.5); fill(MID)
        c.drawCentredString(cx, info_y, included)

        # Color scheme label
        info_y -= 20
        font("Helvetica", 7); fill(_blend(MID, 0.4))
        c.drawCentredString(cx, info_y, f"Color Scheme: {cs['label']}")

        # Footer
        font("Helvetica", 7); fill(_blend(MID, 0.5))
        c.drawCentredString(cx, MB + 8, "OnBrandCraftz  \xb7  Digital Download  \xb7  Personal Use")

        c.showPage()

    # ── HOW TO USE PAGE ──────────────────────────────────────────────────────
    def draw_how_to_use():
        c.bookmarkPage("how_to_use")
        c.addOutlineEntry("How to Use", "how_to_use", level=0)
        page_bg()
        rect(0, 0, PW, PH, f=BG)

        # Header
        rect(0, PH - MT - 50, PW, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawCentredString(PW / 2, PH - MT - 34, "HOW TO USE THIS PLANNER")
        rect(0, PH - MT - 54, PW, 4, f=A)

        y = PH - MT - 80
        cx = PW / 2

        steps = [
            ("📱", "Open in Your Favorite App",
             "Works in GoodNotes 5/6, Notability, Noteshelf, Xodo (free), PDF Expert, and Adobe Reader.\n"
             "iPad users: GoodNotes or Notability give the best annotation experience."),
            ("🔗", "Use the Navigation Tabs",
             "Tap any colored tab on the right side of every page to jump instantly\n"
             "to that section. Month tabs jump to monthly views, HABIT to your tracker, etc."),
            ("✏️", "Fill In Your Information",
             "Tap any outlined text box to type directly into the planner.\n"
             "All fields are fillable — goals, notes, priorities, intentions, and more."),
            ("✅", "Use the Interactive Checkboxes",
             "Habit tracker checkboxes are clickable — tap to mark your habits complete.\n"
             "To-do checkboxes work the same way throughout."),
            ("🖨️", "Print It Out (Optional)",
             "Export to PDF and print at home or at a local print shop.\n"
             "Recommended: 100% scale, color, letter or A4 size."),
        ]

        step_h = (y - MB - 20) / len(steps)
        for i, (icon, heading, detail) in enumerate(steps):
            sy = y - i * step_h
            # Number circle
            circle(ML + 14, sy - 16, 13, f=T)
            font("Helvetica-Bold", 11); fill(WHITE)
            c.drawCentredString(ML + 14, sy - 20, str(i + 1))
            # Icon + heading
            font("Helvetica-Bold", 11); fill(T)
            c.drawString(ML + 34, sy - 13, heading)
            # Detail lines
            font("Helvetica", 8.5); fill(MID)
            for li, line in enumerate(detail.split("\n")):
                c.drawString(ML + 34, sy - 26 - li * 13, line.strip())
            # Separator
            if i < len(steps) - 1:
                hline(ML + 28, PW - MR - 4, sy - step_h + 8, LIGHT, 0.4)

        page_footer("HOW TO USE")
        c.showPage()

    # ── YEARLY OVERVIEW ──────────────────────────────────────────────────────
    def draw_yearly_overview():
        c.bookmarkPage("yearly")
        c.addOutlineEntry("Year at a Glance", "yearly", level=0)
        page_bg()

        year_label = "AT A GLANCE" if undated else f"{planner_year} AT A GLANCE"
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 8, PH - MT - 34, year_label)
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        avail_w = CW - TAB_W - 4
        cell_w = avail_w / 4 - 5
        y = PH - MT - 60
        cell_h = (y - MB - 12) / 3 - 8

        for i, month_name in enumerate(MONTHS):
            col = i % 4
            row = i // 4
            x0 = ML + col * (cell_w + 6)
            y0 = y - row * (cell_h + 10) - cell_h

            rect(x0, y0, cell_w, cell_h, f=WHITE, s=LIGHT, lwidth=0.5, radius=4)
            rect(x0, y0 + cell_h - 18, cell_w, 18, f=T, radius=4)
            font("Helvetica-Bold", 7.5); fill(WHITE)
            c.drawCentredString(x0 + cell_w/2, y0 + cell_h - 13, month_name[:3].upper())

            mini_dw = cell_w / 7
            for d, dn in enumerate(["M","T","W","T","F","S","S"]):
                font("Helvetica", 5); fill(TM if d < 5 else T)
                c.drawCentredString(x0 + d * mini_dw + mini_dw/2, y0 + cell_h - 27, dn)

            if not undated:
                cal = cal_mod.monthcalendar(planner_year, i + 1)
                for ri, week in enumerate(cal):
                    for di, day in enumerate(week):
                        if not day: continue
                        dx = x0 + di * mini_dw + mini_dw/2
                        dy = y0 + cell_h - 38 - ri * max((cell_h - 40) / max(len(cal),1), 8)
                        font("Helvetica", 4.5)
                        fill(T if di >= 5 else DARK)
                        c.drawCentredString(dx, dy, str(day))

        draw_nav_tabs("yearly")
        page_footer("YEAR AT A GLANCE")
        c.showPage()

    # ── MONTHLY PAGE ─────────────────────────────────────────────────────────
    def draw_monthly_page(month_idx):
        month_name = MONTHS[month_idx]
        month_num  = month_idx + 1
        bm = f"month_{month_name[:3].lower()}"
        c.bookmarkPage(bm)
        c.addOutlineEntry(month_name, bm, level=1)
        page_bg()

        content_w = CW - TAB_W - 4

        # Header
        rect(0, PH - MT - 52, PW - TAB_W - 2, 52 + MT, f=T)
        font("Helvetica-Bold", 28); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 36, month_name.upper())
        year_str = "" if undated else str(planner_year)
        font("Helvetica", 13); fill(_blend(WHITE, 0.4))
        c.drawRightString(PW - TAB_W - 10, PH - MT - 36, year_str)
        rect(0, PH - MT - 56, PW - TAB_W - 2, 4, f=A)

        top_y     = PH - MT - 60
        notes_h   = 145
        cal_area  = top_y - MB - notes_h - 12
        day_h_row = 22
        num_rows  = 6
        row_h     = (cal_area - day_h_row) / num_rows
        col_w     = content_w / 7

        # Day headers
        for di, dn in enumerate(DAYS_SHORT):
            x0 = ML + di * col_w
            bg = TM if di < 5 else T
            rect(x0, top_y - day_h_row, col_w, day_h_row, f=bg)
            font("Helvetica-Bold", 7.5); fill(WHITE)
            c.drawCentredString(x0 + col_w/2, top_y - day_h_row + 7, dn)

        # Calendar grid
        if not undated:
            cal = cal_mod.monthcalendar(planner_year, month_num)
        else:
            # Generic 5-week undated calendar skeleton
            cal = [[0]*7 for _ in range(5)]

        for ri in range(num_rows):
            for di in range(7):
                cx0 = ML + di * col_w
                cy0 = top_y - day_h_row - (ri+1) * row_h
                bg = _blend(T, 0.94) if di >= 5 else BG
                rect(cx0, cy0, col_w, row_h, f=bg, s=LIGHT, lwidth=0.35)
                if not undated and ri < len(cal):
                    day_num = cal[ri][di]
                    if day_num:
                        font("Helvetica-Bold", 9); fill(T if di >= 5 else DARK)
                        c.drawString(cx0 + 4, top_y - day_h_row - ri * row_h - 14, str(day_num))
                        # Fillable mini event area inside cell
                        if is_interactive and row_h > 22:
                            text_field(cx0 + 2, cy0 + 2, col_w - 4, row_h - 16,
                                       f"month_{month_num}_cell_{ri}_{di}", font_size=6)

        cal_bottom = top_y - day_h_row - num_rows * row_h

        # Notes below calendar
        notes_y_top = cal_bottom - 8
        col2_w  = (content_w - 8) / 2
        col2_x2 = ML + col2_w + 8

        for col_x, col_label in [(ML, "MONTHLY GOALS"), (col2_x2, "NOTES & HIGHLIGHTS")]:
            font("Helvetica-Bold", 7); fill(T)
            c.drawString(col_x, notes_y_top, col_label)
            field_h = notes_y_top - MB - 12
            if field_h > 10:
                text_field(col_x, MB + 8, col2_w, field_h,
                           f"month_{month_num}_{col_label[:4].lower()}", multiline=True)

        draw_nav_tabs(bm)
        page_footer(f"{month_name.upper()}  {year_str}".strip())
        c.showPage()

    # ── WEEKLY PAGE ──────────────────────────────────────────────────────────
    _weekly_page_count = [0]

    def draw_weekly_page(week_num_or_label, start_date=None):
        is_first = (_weekly_page_count[0] == 0)
        _weekly_page_count[0] += 1
        bm = "weekly_start" if is_first else f"week_{week_num_or_label}"
        if is_first:
            c.bookmarkPage("weekly_start")
            c.addOutlineEntry("Weekly Planning", "weekly_start", level=0)
        page_bg()
        content_w = CW - TAB_W - 4

        if undated or start_date is None:
            week_label = f"WEEK {week_num_or_label:02d}" if isinstance(week_num_or_label, int) else str(week_num_or_label)
            date_label = "Date:  ___ / ___ / ___"
        else:
            end_date   = start_date + timedelta(days=6)
            week_label = f"WEEK {week_num_or_label:02d}"
            date_label = f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"

        # Header
        rect(0, PH - MT - 46, PW - TAB_W - 2, 46 + MT, f=T)
        font("Helvetica-Bold", 20); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 30, week_label)
        font("Helvetica", 10); fill(_blend(WHITE, 0.35))
        c.drawRightString(PW - TAB_W - 10, PH - MT - 30, date_label)
        rect(0, PH - MT - 50, PW - TAB_W - 2, 4, f=A)

        top_y    = PH - MT - 54
        sched_w  = content_w * 0.62
        sidebar_w = content_w - sched_w - 8
        sidebar_x = ML + sched_w + 8
        day_h    = (top_y - MB) / 7
        line_clr = _blend(LIGHT, -0.05)

        for di, day_name in enumerate(DAYS_LONG):
            dy_top = top_y - di * day_h
            dy_bot = dy_top - day_h
            is_weekend = di >= 5
            hdr_h = 17

            bg_hdr = TM if is_weekend else T
            rect(ML, dy_top - hdr_h, sched_w, hdr_h, f=bg_hdr)
            font("Helvetica-Bold", 7.5); fill(WHITE)
            c.drawString(ML + 6, dy_top - 12, day_name.upper())
            if not undated and start_date:
                day_date = start_date + timedelta(days=di)
                font("Helvetica", 7); fill(_blend(WHITE, 0.3))
                c.drawRightString(ML + sched_w - 6, dy_top - 12, day_date.strftime("%b %d"))

            # Fillable day area
            field_h = day_h - hdr_h - 2
            if field_h > 6:
                text_field(ML + 2, dy_bot + 2, sched_w - 4, field_h,
                           f"week_{week_num_or_label}_day{di}", multiline=True, font_size=8)

            if di < 6:
                hline(ML, ML + sched_w, dy_bot, LIGHT, 0.4)
            circle(ML + 3, dy_top - hdr_h - (day_h - hdr_h)/2, 2, f=bg_hdr)

        # Right sidebar
        sb_y = top_y

        def sidebar_section(label, field_h, name_hint):
            nonlocal sb_y
            font("Helvetica-Bold", 7); fill(T)
            c.drawString(sidebar_x, sb_y - 11, label.upper())
            text_field(sidebar_x, sb_y - 11 - field_h, sidebar_w, field_h, name_hint, multiline=True, font_size=8)
            sb_y -= field_h + 18

        sidebar_section("TOP PRIORITIES", 75, f"week_{week_num_or_label}_priorities")
        sidebar_section("NOTES", 90, f"week_{week_num_or_label}_notes")

        # Habit mini-tracker
        habit_y = sb_y - 14
        font("Helvetica-Bold", 7); fill(MID)
        c.drawString(sidebar_x, habit_y + 2, "HABITS")
        for hi in range(5):
            hx = sidebar_x + hi * (sidebar_w / 5)
            checkbox_field(hx + 2, habit_y - 14, 10, f"week_{week_num_or_label}_habit{hi}")
            font("Helvetica", 5.5); fill(MID)
            c.drawCentredString(hx + 7, habit_y - 22, str(hi + 1))

        # Water tracker circles
        water_y = habit_y - 34
        font("Helvetica-Bold", 7); fill(MID)
        c.drawString(sidebar_x, water_y, "WATER")
        for wi in range(8):
            wx = sidebar_x + wi * (sidebar_w / 8)
            circle(wx + 5, water_y - 10, 4, s=_blend(T, 0.45), lwidth=0.7)

        draw_nav_tabs("weekly_start")
        page_footer(f"WEEK  {week_num_or_label}")
        c.showPage()

    # ── HABIT TRACKER ────────────────────────────────────────────────────────
    def draw_habit_tracker():
        c.bookmarkPage("habits")
        c.addOutlineEntry("Habit Tracker", "habits", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 34, "HABIT TRACKER")
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        y         = PH - MT - 60
        n_habits  = 12
        n_days    = 31
        label_w   = 105
        cell_w    = (content_w - label_w) / n_days
        hdr_h     = 22
        cell_h    = (y - MB - 40 - hdr_h) / n_habits

        palette = [T, A, TM, AL, _blend(T, 0.35), _blend(A, 0.45),
                   _blend(T, 0.55), _blend(A, 0.65), T, A, TM, AL]

        # Column headers
        for di in range(n_days):
            dx = ML + label_w + di * cell_w
            if di % 7 >= 5:
                rect(dx, MB + 38, cell_w, y - MB - 38 - hdr_h, f=_blend(T, 0.95))
            font("Helvetica-Bold", 6); fill(T if di % 7 >= 5 else MID)
            c.drawCentredString(dx + cell_w/2, y - hdr_h + 7, str(di + 1))

        hline(ML, ML + content_w, y - hdr_h, T, 1.2)

        # Habit rows
        for hi in range(n_habits):
            row_y    = y - hdr_h - (hi+1) * cell_h
            row_clr  = palette[hi]
            row_bg   = BG if hi % 2 == 0 else _blend(LIGHT, 0.5)
            rect(ML, row_y, content_w, cell_h, f=row_bg)

            # Habit name field (clickable label + fillable field)
            pill_h = min(cell_h - 4, 16)
            rect(ML + 2, row_y + (cell_h - pill_h)/2, label_w - 8, pill_h, f=row_clr, radius=3)
            font("Helvetica-Bold", 7); fill(WHITE)
            c.drawString(ML + 7, row_y + (cell_h - pill_h)/2 + 4, f"Habit {hi + 1}")

            # Interactive checkboxes for each day
            for di in range(n_days):
                dx     = ML + label_w + di * cell_w
                cb_s   = min(cell_w - 2, cell_h - 4)
                cb_x   = dx + (cell_w - cb_s) / 2
                cb_y   = row_y + (cell_h - cb_s) / 2
                checkbox_field(cb_x, cb_y, cb_s, f"habit_{hi+1}_day{di+1}")

            hline(ML, ML + content_w, row_y, LIGHT, 0.3)

        # Column header
        rect(ML, y - hdr_h, label_w, hdr_h, f=T)
        font("Helvetica-Bold", 7.5); fill(WHITE)
        c.drawString(ML + 7, y - hdr_h + 7, "HABIT")
        rect(ML, MB + 38, content_w, y - MB - 38, s=_blend(T, 0.4), lwidth=0.8)

        # Month name fillable field at bottom
        font("Helvetica-Bold", 7); fill(MID)
        c.drawString(ML + label_w + 2, MB + 24, "MONTH:")
        text_field(ML + label_w + 50, MB + 18, 90, 16, "habit_month", font_size=9)

        draw_nav_tabs("habits")
        page_footer("HABIT TRACKER")
        c.showPage()

    # ── GOALS PAGE ───────────────────────────────────────────────────────────
    def draw_goals_page():
        c.bookmarkPage("goals")
        c.addOutlineEntry("Goals & Vision", "goals", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 34, "GOALS & VISION")
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        # Decorative circles
        circle(PW - TAB_W - 22, PH - MT - 18, 55, f=_blend(A, 0.88))
        circle(PW - TAB_W + 8,  PH - MT - 78, 30, f=_blend(T, 0.90))

        y = PH - MT - 70

        # Word of the year
        font("Helvetica-Bold", 8); fill(T)
        c.drawString(ML, y, "MY WORD OF THE YEAR")
        y -= 6
        text_field(ML, y - 28, content_w, 28, "word_of_year", font_size=14)
        y -= 42

        # Top 3 goals
        font("Helvetica-Bold", 9); fill(DARK)
        c.drawString(ML, y, "MY TOP 3 GOALS")
        y -= 12
        for gi in range(3):
            box_h = 64
            circle(ML + 14, y - box_h/2 + 10, 13, f=T)
            font("Helvetica-Bold", 12); fill(WHITE)
            c.drawCentredString(ML + 14, y - box_h/2 + 6, str(gi + 1))
            # Three labeled sub-fields
            sub_labels = [("GOAL", 20), ("WHY IT MATTERS", 18), ("FIRST STEP", 18)]
            sy = y - 4
            for slabel, sh in sub_labels:
                font("Helvetica", 6.5); fill(MID)
                c.drawString(ML + 32, sy - 8, slabel)
                text_field(ML + 32, sy - 8 - sh, content_w - 32, sh, f"goal_{gi+1}_{slabel[:4].lower()}", font_size=8)
                sy -= sh + 6
            y -= box_h + 10

        # Intentions / affirmations
        font("Helvetica-Bold", 8); fill(T)
        c.drawString(ML, y, "AFFIRMATIONS & INTENTIONS")
        y -= 10
        remaining_h = y - MB - 4
        if remaining_h > 20:
            text_field(ML, MB + 4, content_w, remaining_h, "affirmations", multiline=True, font_size=9)

        draw_nav_tabs("goals")
        page_footer("GOALS & VISION")
        c.showPage()

    # ── BUDGET PAGE ──────────────────────────────────────────────────────────
    def draw_budget_page():
        c.bookmarkPage("budget")
        c.addOutlineEntry("Budget Tracker", "budget", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 34, "BUDGET TRACKER")
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        y = PH - MT - 70
        col_half = content_w / 2 - 4
        col2_x   = ML + col_half + 8

        for col_x, section_title in [(ML, "INCOME"), (col2_x, "EXPENSES")]:
            font("Helvetica-Bold", 8.5); fill(T)
            c.drawString(col_x, y, section_title)
            sy = y - 14
            for row in range(8):
                font("Helvetica", 7.5); fill(MID)
                c.drawString(col_x, sy - 10, "Item:")
                text_field(col_x + 28, sy - 14, col_half - 72, 14, f"{section_title.lower()}_name_{row}", font_size=8)
                c.drawString(col_x + col_half - 40, sy - 10, "$")
                text_field(col_x + col_half - 32, sy - 14, 30, 14, f"{section_title.lower()}_amt_{row}", font_size=8)
                hline(col_x, col_x + col_half, sy - 16, LIGHT, 0.4)
                sy -= 22

            # Total row
            rect(col_x, sy - 18, col_half, 18, f=_blend(T, 0.9), radius=3)
            font("Helvetica-Bold", 8); fill(T)
            c.drawString(col_x + 4, sy - 12, "TOTAL  $")
            text_field(col_x + 48, sy - 15, col_half - 54, 14, f"{section_title.lower()}_total", font_size=9)
            sy -= 28

        # Net balance
        net_y = y - 8 * 22 - 44
        rect(ML, net_y - 24, content_w, 24, f=T, radius=4)
        font("Helvetica-Bold", 10); fill(WHITE)
        c.drawString(ML + 8, net_y - 16, "NET BALANCE:  $")
        text_field(ML + 100, net_y - 20, 100, 16, "net_balance", font_size=10)

        draw_nav_tabs("budget")
        page_footer("BUDGET TRACKER")
        c.showPage()

    # ── MEAL PLAN PAGE ───────────────────────────────────────────────────────
    def draw_meal_plan_page():
        c.bookmarkPage("meal_plan")
        c.addOutlineEntry("Meal Planning", "meal_plan", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(0, PH - MT - 50, PW - TAB_W - 2, 50 + MT, f=T)
        font("Helvetica-Bold", 22); fill(WHITE)
        c.drawString(ML + 10, PH - MT - 34, "MEAL PLANNER")
        rect(0, PH - MT - 54, PW - TAB_W - 2, 4, f=A)

        y = PH - MT - 62
        meal_labels = ["BREAKFAST","LUNCH","DINNER","SNACKS"]
        meal_colors = [T, A, TM, AL]
        day_col_w   = content_w / 7
        row_h       = (y - MB - 40) / (len(meal_labels) + 1)

        # Day headers
        for di, day in enumerate(["MON","TUE","WED","THU","FRI","SAT","SUN"]):
            dx = ML + di * day_col_w
            bg = TM if di < 5 else T
            rect(dx, y - 20, day_col_w, 20, f=bg)
            font("Helvetica-Bold", 7.5); fill(WHITE)
            c.drawCentredString(dx + day_col_w/2, y - 14, day)

        # Meal rows
        for mi, (meal_label, meal_color) in enumerate(zip(meal_labels, meal_colors)):
            row_y_top = y - 20 - (mi+1) * row_h
            # Row label
            rect(ML - 2, row_y_top - row_h, 38, row_h, f=meal_color, radius=2)
            c.saveState(); c.translate(ML + 17, row_y_top - row_h / 2); c.rotate(90)
            font("Helvetica-Bold", 6.5); fill(WHITE)
            c.drawCentredString(0, -2, meal_label)
            c.restoreState()
            # Day cells
            for di in range(7):
                dx = ML + di * day_col_w
                text_field(dx + 1, row_y_top - row_h + 1, day_col_w - 2, row_h - 2,
                           f"meal_{mi}_{di}", multiline=True, font_size=7)
                if di < 6:
                    vline(dx + day_col_w, row_y_top - row_h, row_y_top, LIGHT, 0.3)
            hline(ML, ML + content_w, row_y_top - row_h, LIGHT, 0.4)

        # Grocery list
        gl_y = y - 20 - (len(meal_labels)+1) * row_h - 8
        font("Helvetica-Bold", 8); fill(T)
        c.drawString(ML, gl_y, "GROCERY LIST")
        remaining = gl_y - MB - 4
        if remaining > 15:
            text_field(ML, MB + 4, content_w, remaining - 10, "grocery_list", multiline=True, font_size=8)

        draw_nav_tabs("meal_plan")
        page_footer("MEAL PLANNER")
        c.showPage()

    # ── NOTES PAGE ───────────────────────────────────────────────────────────
    def draw_notes_page(page_num=1):
        bm = "notes" if page_num == 1 else f"notes_{page_num}"
        if page_num == 1:
            c.bookmarkPage("notes")
            c.addOutlineEntry("Notes", "notes", level=0)
        page_bg()

        content_w = CW - TAB_W - 4
        rect(ML, PH - MT - 40, content_w, 40, f=_blend(T, 0.90))
        rect(ML, PH - MT - 40, 5, 40, f=T)
        font("Helvetica-Bold", 18); fill(T)
        c.drawString(ML + 16, PH - MT - 26, "NOTES")
        font("Helvetica", 8); fill(MID)
        c.drawRightString(ML + content_w, PH - MT - 26, f"{page_num}")

        # Dot grid (iconic planner aesthetic)
        dot_sp = 14; dot_r = 0.85
        sx = ML + dot_sp; sy = PH - MT - 58; ey = MB + 22
        x = sx
        while x <= ML + content_w - dot_sp:
            y = sy
            while y >= ey:
                circle(x, y, dot_r, f=LIGHT)
                y -= dot_sp
            x += dot_sp

        rect(ML, ey, 2, sy - ey + dot_sp, f=_blend(T, 0.72))

        # Large fillable text area over the dot grid (transparent fill)
        text_field(ML + dot_sp, ey, content_w - dot_sp, sy - ey, f"notes_{page_num}", multiline=True, font_size=10)

        draw_nav_tabs("notes")
        page_footer(f"NOTES  {page_num}")
        c.showPage()

    # ── ASSEMBLE ──────────────────────────────────────────────────────────────
    page_count = 0
    draw_cover();       page_count += 1
    draw_how_to_use();  page_count += 1

    if "monthly" in sections or "weekly" in sections:
        draw_yearly_overview(); page_count += 1

    if "monthly" in sections:
        for mi in range(12):
            draw_monthly_page(mi); page_count += 1

    if "weekly" in sections:
        if undated:
            for wn in range(1, 53):
                draw_weekly_page(wn); page_count += 1
        else:
            from datetime import date as dt_date, timedelta
            first_day = dt_date(planner_year, 1, 1)
            start = first_day - timedelta(days=first_day.weekday())
            if start.year < planner_year:
                start += timedelta(weeks=1)
            wn = 1
            while start.year <= planner_year and wn <= 52:
                draw_weekly_page(wn, start); page_count += 1
                start += timedelta(weeks=1); wn += 1

    if "habit_tracker" in sections:
        draw_habit_tracker(); page_count += 1

    if "goals" in sections:
        draw_goals_page(); page_count += 1

    if "budget" in sections:
        draw_budget_page(); page_count += 1

    if "meal_plan" in sections:
        draw_meal_plan_page(); page_count += 1

    if "notes" in sections:
        for ni in range(4):
            draw_notes_page(ni + 1); page_count += 1

    c.save()
    file_size_kb = os.path.getsize(file_path) // 1024

    import hashlib as _hashlib
    with open(file_path, "rb") as _hf:
        product["file_hash"] = _hashlib.sha256(_hf.read()).hexdigest()
    product["is_placeholder"] = False
    product["file_path"]      = file_path
    product["file_format"]    = "PDF"
    product["file_size_kb"]   = file_size_kb
    product["status"]         = "qc_pending"
    product["color_scheme"]   = scheme_key
    product["interactive"]    = is_interactive
    product["updated_at"]     = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success":       True,
        "product_id":    product_id,
        "file_path":     file_path,
        "file_size_kb":  file_size_kb,
        "pages":         page_count,
        "sections":      sections,
        "interactive":   is_interactive,
        "color_scheme":  cs["label"],
        "format":        fmt,
        "status":        "qc_pending",
        "features": [
            "Hyperlinked side navigation tabs (GoodNotes/Notability compatible)",
            "Fillable PDF form fields for all text areas",
            "Interactive checkboxes in habit tracker",
            "PDF bookmarks and outline for table of contents",
            "How to Use instruction page",
        ] if is_interactive else ["Print-ready layout", "PDF bookmarks/outline"],
        "next_step": "Send to Quality Check Agent for review. Then run generate_listing_content for SEO.",
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
