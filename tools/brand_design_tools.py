"""
Brand Design Tools — manages the company's visual identity, logo, and Etsy shop branding.

Handles: brand guidelines, logo generation (DALL-E 3), shop banner creation,
color palette management, font selection, and brand asset storage.

Requires for full functionality:
  OPENAI_API_KEY  — DALL-E 3 logo/banner generation
  Pillow          — image processing and mockup creation
"""

import json
import os
import urllib.request
import urllib.error
from datetime import date
from typing import Any

from tools.data_store import DataStore

BRAND_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "brand")
BRAND_ASSETS_DIR = os.path.join(BRAND_DIR, "assets")
BRAND_GUIDELINES_FILE = os.path.join(BRAND_DIR, "brand_guidelines.json")

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_brand_guidelines",
        "description": "Get the current brand guidelines: colors, fonts, logo, voice, and positioning.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_brand_guidelines",
        "description": (
            "Create or update the brand guidelines for OnBrandCraftz. "
            "Covers colors, typography, brand voice, tagline, and target audience."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "shop_name": {"type": "string", "description": "Official shop name"},
                "tagline": {"type": "string", "description": "Short brand tagline (e.g. 'Modern Prints for Modern Homes')"},
                "brand_story": {"type": "string", "description": "1-2 sentence brand story for the About section"},
                "target_audience": {"type": "string", "description": "Primary buyer persona"},
                "brand_voice": {
                    "type": "string",
                    "description": "Tone: e.g. 'warm, approachable, creative, modern'",
                },
                "primary_color": {"type": "string", "description": "Primary brand hex color, e.g. '#6B7280'"},
                "secondary_color": {"type": "string", "description": "Secondary hex color"},
                "accent_color": {"type": "string", "description": "Accent hex color for highlights"},
                "primary_font": {"type": "string", "description": "Primary font name, e.g. 'Playfair Display'"},
                "secondary_font": {"type": "string", "description": "Body/secondary font, e.g. 'Lato'"},
                "style_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-5 style words: e.g. ['minimalist', 'boho', 'modern', 'clean']",
                },
                "niche": {"type": "string", "description": "Market niche, e.g. 'digital planners and printable home decor'"},
            },
            "required": ["shop_name", "tagline", "primary_color"],
        },
    },
    {
        "name": "generate_logo",
        "description": (
            "Generate a logo for the shop using DALL-E 3. "
            "Saves the logo as a PNG in the brand assets directory. "
            "Requires OPENAI_API_KEY."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "logo_concept": {
                    "type": "string",
                    "description": "Detailed description of the logo: style, icon, colors, feel",
                },
                "logo_type": {
                    "type": "string",
                    "enum": ["wordmark", "icon_only", "icon_with_text", "monogram"],
                    "description": "Type of logo",
                    "default": "icon_with_text",
                },
                "asset_name": {
                    "type": "string",
                    "description": "File name for the asset, e.g. 'logo_primary'",
                    "default": "logo_primary",
                },
            },
            "required": ["logo_concept"],
        },
    },
    {
        "name": "generate_shop_banner",
        "description": (
            "Generate a shop banner image for the Etsy shop page using DALL-E 3. "
            "Etsy banner optimal size: 3360x840px. Saves as PNG."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "banner_concept": {
                    "type": "string",
                    "description": "What the banner should show: products, mood, style, text if any",
                },
                "asset_name": {
                    "type": "string",
                    "description": "File name, e.g. 'shop_banner_main'",
                    "default": "shop_banner_main",
                },
            },
            "required": ["banner_concept"],
        },
    },
    {
        "name": "list_brand_assets",
        "description": "List all brand assets (logos, banners, profile images, mockups) stored locally.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_etsy_branding_checklist",
        "description": "Get a checklist of all Etsy shop branding elements and their completion status.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "generate_product_mockup_prompt",
        "description": (
            "Generate a DALL-E 3 prompt for creating a product mockup image "
            "(e.g., a framed print on a wall, a planner on a desk). "
            "Returns the prompt for use with generate_logo or the Art Creation Agent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "enum": ["wall_art", "planner", "clipart", "sticker", "printable"],
                },
                "setting": {
                    "type": "string",
                    "description": "Scene for the mockup, e.g. 'modern living room', 'cozy desk setup'",
                },
                "style": {
                    "type": "string",
                    "description": "Visual style, e.g. 'minimalist', 'boho', 'bright and airy'",
                },
            },
            "required": ["product_type", "setting"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_brand_guidelines":
        return _get_brand_guidelines()
    if tool_name == "set_brand_guidelines":
        return _set_brand_guidelines(tool_input, store)
    if tool_name == "generate_logo":
        return _generate_brand_asset(tool_input, asset_type="logo")
    if tool_name == "generate_shop_banner":
        return _generate_brand_asset(tool_input, asset_type="banner")
    if tool_name == "list_brand_assets":
        return _list_brand_assets()
    if tool_name == "get_etsy_branding_checklist":
        return _get_etsy_branding_checklist(store)
    if tool_name == "generate_product_mockup_prompt":
        return _generate_mockup_prompt(tool_input)
    return f"Unknown brand design tool: {tool_name}"


# ── IMPLEMENTATIONS ───────────────────────────────────────────────────────────

def _ensure_brand_dirs() -> None:
    os.makedirs(BRAND_ASSETS_DIR, exist_ok=True)


def _get_brand_guidelines() -> str:
    _ensure_brand_dirs()
    if not os.path.exists(BRAND_GUIDELINES_FILE):
        return json.dumps({
            "status": "No brand guidelines set yet.",
            "action": "Use set_brand_guidelines to establish your brand identity.",
        }, indent=2)
    with open(BRAND_GUIDELINES_FILE) as f:
        return f.read()


def _set_brand_guidelines(data: dict, store: DataStore) -> str:
    _ensure_brand_dirs()
    guidelines: dict[str, Any] = {
        "shop_name": data.get("shop_name", store.shop.get("name", "OnBrandCraftz")),
        "tagline": data.get("tagline", ""),
        "brand_story": data.get("brand_story", ""),
        "target_audience": data.get("target_audience", ""),
        "brand_voice": data.get("brand_voice", "warm, creative, modern"),
        "colors": {
            "primary": data.get("primary_color", "#6B7280"),
            "secondary": data.get("secondary_color", "#9CA3AF"),
            "accent": data.get("accent_color", "#F59E0B"),
        },
        "typography": {
            "primary_font": data.get("primary_font", "Playfair Display"),
            "secondary_font": data.get("secondary_font", "Lato"),
        },
        "style_keywords": data.get("style_keywords", ["modern", "minimalist", "clean"]),
        "niche": data.get("niche", "digital planners and printable home decor"),
        "updated_at": str(date.today()),
    }

    with open(BRAND_GUIDELINES_FILE, "w") as f:
        json.dump(guidelines, f, indent=2)

    # Update shop name in data store if provided
    if data.get("shop_name"):
        store.shop["name"] = data["shop_name"]
        store.save()

    return json.dumps({
        "success": True,
        "guidelines_saved": BRAND_GUIDELINES_FILE,
        "brand": guidelines,
        "next_steps": [
            "Use generate_logo to create your logo",
            "Use generate_shop_banner to create your Etsy banner",
            "Share guidelines with Art Creation Agent for consistent product style",
        ],
    }, indent=2)


def _generate_brand_asset(data: dict, asset_type: str) -> str:
    _ensure_brand_dirs()
    api_key = os.getenv("OPENAI_API_KEY", "")

    asset_name = data.get("asset_name", f"{asset_type}_primary")
    concept_key = "logo_concept" if asset_type == "logo" else "banner_concept"
    concept = data.get(concept_key, "")

    if asset_type == "logo":
        logo_type = data.get("logo_type", "icon_with_text")
        dalle_prompt = (
            f"Professional logo design for an Etsy shop: {concept}. "
            f"Style: {logo_type}, clean vector-style art, suitable for small business branding. "
            "White background, high contrast, scalable design. No photographic elements. "
            "Modern, professional, memorable. Square format."
        )
        image_size = "1024x1024"
    else:
        dalle_prompt = (
            f"Wide format shop banner image: {concept}. "
            "Landscape orientation (approximately 4:1 ratio), clean and professional, "
            "suitable for an Etsy shop header. No text overlays. "
            "High quality, modern aesthetic."
        )
        image_size = "1792x1024"

    if not api_key:
        brief_path = os.path.join(BRAND_ASSETS_DIR, f"{asset_name}_brief.txt")
        with open(brief_path, "w") as f:
            f.write(f"DALL-E 3 Prompt for {asset_type.upper()} '{asset_name}':\n\n{dalle_prompt}\n")
        return json.dumps({
            "warning": "OPENAI_API_KEY not set. Design brief saved instead.",
            "brief_path": brief_path,
            "dalle_prompt": dalle_prompt,
            "action_needed": "Add OPENAI_API_KEY to .env to generate the image.",
        }, indent=2)

    try:
        import base64
        # gpt-image-1 only supports 1024x1024, 1536x1024, 1024x1536
        safe_size = "1536x1024" if image_size == "1792x1024" else "1024x1024"
        request_body = json.dumps({
            "model": "gpt-image-1",
            "prompt": dalle_prompt,
            "size": safe_size,
            "quality": "high",
            "n": 1,
            "output_format": "png",
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
        file_path = os.path.join(BRAND_ASSETS_DIR, f"{asset_name}.png")
        if result["data"][0].get("b64_json"):
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(img_data))
        else:
            import urllib.request as _ur
            _ur.urlretrieve(img_data, file_path)
        file_size_kb = os.path.getsize(file_path) // 1024

        # Save asset record
        _record_asset(asset_name, asset_type, file_path, file_size_kb)

        etsy_specs = {
            "logo": "Etsy profile icon: upload as square PNG, min 500x500px",
            "banner": "Etsy shop banner: optimal 3360x840px — resize before uploading",
        }

        return json.dumps({
            "success": True,
            "asset_type": asset_type,
            "asset_name": asset_name,
            "file_path": file_path,
            "file_size_kb": file_size_kb,
            "etsy_upload_note": etsy_specs.get(asset_type, ""),
            "revised_prompt": result["data"][0].get("revised_prompt", dalle_prompt),
        }, indent=2)

    except urllib.error.HTTPError as e:
        return json.dumps({"error": f"DALL-E 3 error {e.code}: {e.read().decode()}"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _list_brand_assets() -> str:
    _ensure_brand_dirs()
    assets_record = _load_assets_record()
    files = []
    if os.path.exists(BRAND_ASSETS_DIR):
        for fname in os.listdir(BRAND_ASSETS_DIR):
            fpath = os.path.join(BRAND_ASSETS_DIR, fname)
            if os.path.isfile(fpath):
                size_kb = os.path.getsize(fpath) // 1024
                files.append({
                    "filename": fname,
                    "path": fpath,
                    "size_kb": size_kb,
                    "type": assets_record.get(fname, {}).get("type", "unknown"),
                    "created": assets_record.get(fname, {}).get("created", "unknown"),
                })
    has_logo = any(f["type"] == "logo" for f in files)
    has_banner = any(f["type"] == "banner" for f in files)
    return json.dumps({
        "brand_assets": files,
        "count": len(files),
        "has_logo": has_logo,
        "has_banner": has_banner,
        "guidelines_exist": os.path.exists(BRAND_GUIDELINES_FILE),
    }, indent=2)


def _get_etsy_branding_checklist(store: DataStore) -> str:
    assets_record = _load_assets_record()
    has_logo = any(v.get("type") == "logo" for v in assets_record.values())
    has_banner = any(v.get("type") == "banner" for v in assets_record.values())
    has_guidelines = os.path.exists(BRAND_GUIDELINES_FILE)
    announcement = store.shop.get("announcement", "")
    shop = store.shop
    sections = store.get("shop_sections", default=[])

    checklist = [
        {"item": "Brand Guidelines", "complete": has_guidelines,
         "action": "Run set_brand_guidelines" if not has_guidelines else ""},
        {"item": "Shop Logo / Profile Icon", "complete": has_logo,
         "action": "Run generate_logo" if not has_logo else "Upload to Etsy → Shop Manager → Info & Appearance"},
        {"item": "Shop Banner", "complete": has_banner,
         "action": "Run generate_shop_banner" if not has_banner else "Upload to Etsy → Shop Manager → Info & Appearance"},
        {"item": "Shop Announcement", "complete": bool(announcement),
         "action": "Run set_shop_announcement (Store Manager Agent)" if not announcement else ""},
        {"item": "Shop Sections", "complete": len(sections) >= 2,
         "action": "Add sections via Store Manager Agent" if len(sections) < 2 else ""},
        {"item": "About Section / Bio", "complete": bool(shop.get("brand_story")),
         "action": "Write a brand story with set_brand_guidelines"},
        {"item": "Shop Policies", "complete": bool(shop.get("policies_set")),
         "action": "Set policies in Etsy Shop Manager → Policies"},
    ]

    complete_count = sum(1 for c in checklist if c["complete"])
    return json.dumps({
        "branding_checklist": checklist,
        "completed": complete_count,
        "total": len(checklist),
        "completion_pct": round(complete_count / len(checklist) * 100),
        "tip": "A fully branded shop increases buyer trust and conversion rates by 20-30%.",
    }, indent=2)


def _generate_mockup_prompt(data: dict) -> str:
    product_type = data["product_type"]
    setting = data["setting"]
    style = data.get("style", "modern minimalist")

    prompts = {
        "wall_art": (
            f"Product photography mockup: a beautifully framed art print displayed in a {setting}. "
            f"Style: {style}. The frame is clean and modern. "
            "The print shows abstract/decorative art. Soft, natural lighting. "
            "No text overlays. Professional lifestyle photography aesthetic. "
            "The product is the clear focal point. Shallow depth of field."
        ),
        "planner": (
            f"Product photography mockup: an open planner/notebook on a {setting}. "
            f"Style: {style}. Styled with minimal props: a pen, a small plant, a cup of coffee. "
            "The planner pages show weekly planning layout. Overhead or 45-degree angle shot. "
            "Soft, bright, airy lighting. Clean and organized."
        ),
        "clipart": (
            f"Product mockup: multiple clipart illustrations arranged in a flat-lay style on {setting}. "
            f"Style: {style}. Clean white or neutral background. "
            "Colorful, charming illustrations displayed clearly. Digital product feel."
        ),
        "sticker": (
            f"Sticker sheet mockup: a printed sheet of stickers displayed in a {setting}. "
            f"Style: {style}. The stickers are colorful and well-organized on the sheet. "
            "Clean, bright photography. Some stickers peeled off showing the design."
        ),
        "printable": (
            f"Product mockup: printed pages or cards displayed in a {setting}. "
            f"Style: {style}. Clean, professional printing. "
            "Items arranged neatly. Lifestyle photography feel."
        ),
    }

    prompt = prompts.get(product_type, prompts["wall_art"])
    return json.dumps({
        "product_type": product_type,
        "setting": setting,
        "dalle_prompt": prompt,
        "usage": "Use this prompt with generate_logo (asset_type='logo') or directly with DALL-E 3 for mockup images.",
        "tip": "Good mockup images are the #1 factor in Etsy conversion rates.",
    }, indent=2)


# ── ASSET RECORD HELPERS ──────────────────────────────────────────────────────

def _load_assets_record() -> dict:
    record_file = os.path.join(BRAND_DIR, "assets_record.json")
    if not os.path.exists(record_file):
        return {}
    with open(record_file) as f:
        return json.load(f)


def _record_asset(name: str, asset_type: str, file_path: str, size_kb: int) -> None:
    _ensure_brand_dirs()
    record_file = os.path.join(BRAND_DIR, "assets_record.json")
    record = _load_assets_record()
    filename = os.path.basename(file_path)
    record[filename] = {
        "name": name,
        "type": asset_type,
        "path": file_path,
        "size_kb": size_kb,
        "created": str(date.today()),
    }
    with open(record_file, "w") as f:
        json.dump(record, f, indent=2)
