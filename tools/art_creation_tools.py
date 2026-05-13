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
from typing import Any

from tools.data_store import DataStore

DIGITAL_PRODUCTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "digital_products")
PRODUCT_FILES_DIR = os.path.join(DIGITAL_PRODUCTS_DIR, "product_files")


def _ensure_dirs() -> None:
    os.makedirs(PRODUCT_FILES_DIR, exist_ok=True)


def _next_product_id(store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    nums = [int(p["id"][2:]) for p in products if p["id"].startswith("DP") and p["id"][2:].isdigit()]
    return f"DP{max(nums, default=0) + 1:03d}"


# ── TOOL DEFINITIONS ──────────────────────────────────────────────────────────

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
                    "enum": ["1024x1024", "1792x1024", "1024x1792"],
                    "description": "Image size (1024x1024 is square, others are landscape/portrait)",
                    "default": "1024x1024",
                },
                "quality": {
                    "type": "string",
                    "enum": ["standard", "hd"],
                    "description": "hd produces more detailed images (costs more)",
                    "default": "hd",
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
        request_body = json.dumps({
            "model": "dall-e-3",
            "prompt": data["dalle_prompt"],
            "size": data.get("image_size", "1024x1024"),
            "quality": data.get("quality", "hd"),
            "n": 1,
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=request_body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())

        image_url = result["data"][0]["url"]
        revised_prompt = result["data"][0].get("revised_prompt", data["dalle_prompt"])

        # Download the image
        file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.png")
        urllib.request.urlretrieve(image_url, file_path)
        file_size_kb = os.path.getsize(file_path) // 1024

        product["file_path"] = file_path
        product["file_format"] = "PNG"
        product["file_size_kb"] = file_size_kb
        product["status"] = "qc_pending"
        product["dalle_revised_prompt"] = revised_prompt
        product["updated_at"] = str(date.today())
        _save_product(product, store)

        return json.dumps({
            "success": True,
            "product_id": product_id,
            "file_path": file_path,
            "file_size_kb": file_size_kb,
            "revised_prompt": revised_prompt,
            "status": "qc_pending",
            "next_step": "Send to Quality Check Agent for review.",
        }, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return json.dumps({"error": f"DALL-E 3 API error {e.code}: {error_body}"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _create_digital_planner(data: dict, store: DataStore) -> str:
    _ensure_dirs()
    product_id = data["product_id"]
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})

    try:
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        )
        _has_reportlab = True
    except ImportError:
        _has_reportlab = False

    if not _has_reportlab:
        brief_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}_planner_spec.txt")
        sections = data.get("include_sections", ["monthly", "weekly", "habit_tracker", "notes"])
        with open(brief_path, "w") as f:
            f.write(f"PLANNER SPECIFICATION: {data['planner_title']}\n")
            f.write(f"Theme Color: {data.get('theme_color', '#6B7280')}\n")
            f.write(f"Accent Color: {data.get('accent_color', '#9CA3AF')}\n")
            f.write(f"Year: {data.get('year', date.today().year)}\n")
            f.write(f"Sections: {', '.join(sections)}\n\n")
            f.write("Install reportlab to auto-generate: pip install reportlab\n")
        product["file_path"] = brief_path
        product["status"] = "concept"
        product["updated_at"] = str(date.today())
        _save_product(product, store)
        return json.dumps({
            "warning": "reportlab not installed. Planner spec saved instead.",
            "spec_path": brief_path,
            "action_needed": "Run: pip install reportlab  — then call this tool again.",
        }, indent=2)

    planner_year = data.get("year", date.today().year)
    sections = data.get("include_sections", ["monthly", "weekly", "habit_tracker", "notes"])
    theme_hex = data.get("theme_color", "#6B7280").lstrip("#")
    accent_hex = data.get("accent_color", "#9CA3AF").lstrip("#")

    def hex_to_color(h: str):
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return rl_colors.Color(r / 255, g / 255, b / 255)

    theme_color = hex_to_color(theme_hex)
    accent_color = hex_to_color(accent_hex)

    file_path = os.path.join(PRODUCT_FILES_DIR, f"{product_id}.pdf")
    doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=28, textColor=theme_color, spaceAfter=12, alignment=1, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle("Sub", fontSize=14, textColor=accent_color, spaceAfter=8, alignment=1)
    heading_style = ParagraphStyle("Head", fontSize=16, textColor=theme_color, spaceAfter=6, fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Normal", fontSize=10, spaceAfter=4)

    story = []

    # Cover page
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(data["planner_title"], title_style))
    story.append(Paragraph(str(planner_year), subtitle_style))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Plan • Dream • Achieve", subtitle_style))
    story.append(PageBreak())

    MONTHS = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
    DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    if "monthly" in sections:
        for month in MONTHS:
            story.append(Paragraph(f"{month} {planner_year}", heading_style))
            story.append(Spacer(1, 0.3 * cm))
            header_row = DAYS[:]
            grid = [header_row]
            for _ in range(5):
                grid.append(["" for _ in range(7)])
            t = Table(grid, colWidths=[2.5 * cm] * 7, rowHeights=[0.7 * cm] + [1.8 * cm] * 5)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), theme_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.grey),
                ("VALIGN", (0, 1), (-1, -1), "TOP"),
            ]))
            story.append(t)
            story.append(PageBreak())

    if "weekly" in sections:
        for w in range(1, 53):
            story.append(Paragraph(f"Week {w}  •  {planner_year}", heading_style))
            story.append(Spacer(1, 0.2 * cm))
            week_data = [["Day", "Morning", "Afternoon", "Evening", "Notes"]]
            for d in DAYS:
                week_data.append([d, "", "", "", ""])
            t = Table(week_data, colWidths=[1.5 * cm, 4 * cm, 4 * cm, 4 * cm, 4 * cm],
                      rowHeights=[0.7 * cm] + [1.4 * cm] * 7)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), accent_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(t)
            story.append(PageBreak())

    if "habit_tracker" in sections:
        story.append(Paragraph("Habit Tracker", heading_style))
        story.append(Spacer(1, 0.3 * cm))
        habit_header = ["Habit"] + [str(d) for d in range(1, 32)]
        habit_rows = [habit_header] + [["" for _ in range(32)] for _ in range(10)]
        t = Table(habit_rows, colWidths=[3.5 * cm] + [0.55 * cm] * 31,
                  rowHeights=[0.7 * cm] + [0.8 * cm] * 10)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), theme_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(PageBreak())

    if "goals" in sections:
        story.append(Paragraph("Goals & Vision", heading_style))
        for label in ["My #1 Goal This Year", "Why It Matters", "Action Steps", "Milestones", "Reward When Done"]:
            story.append(Paragraph(label, normal_style))
            story.append(Spacer(1, 1.5 * cm))
        story.append(PageBreak())

    if "notes" in sections:
        for _ in range(4):
            story.append(Paragraph("Notes", heading_style))
            lines = [[""] for _ in range(20)]
            t = Table(lines, colWidths=[17 * cm], rowHeights=[0.9 * cm] * 20)
            t.setStyle(TableStyle([
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, rl_colors.lightgrey),
            ]))
            story.append(t)
            story.append(PageBreak())

    doc.build(story)
    file_size_kb = os.path.getsize(file_path) // 1024

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
        "sections": sections,
        "pages_estimate": (
            (12 if "monthly" in sections else 0) +
            (52 if "weekly" in sections else 0) +
            (1 if "habit_tracker" in sections else 0) +
            (4 if "notes" in sections else 0) +
            (1 if "goals" in sections else 0) + 1
        ),
        "status": "qc_pending",
        "next_step": "Send to Quality Check Agent for review.",
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
