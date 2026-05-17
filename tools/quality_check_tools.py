"""
Quality Check Tools — validates digital product files before listing on Etsy.

Uses Pillow to inspect image specs (dimensions, DPI, format, file size).
Uses Claude vision (via the QualityCheckAgent's run method) for AI visual review.

Etsy digital product requirements:
  - Max file size: 20 MB per file
  - Formats: PDF, PNG, JPEG, ZIP, etc.
  - Recommended print DPI: 300+
  - Recommended min resolution for prints: 3000px on shortest side
"""

import json
import os
from datetime import date

from tools.data_store import DataStore

ETSY_MAX_FILE_SIZE_KB = 20 * 1024  # 20 MB
RECOMMENDED_DPI = 300
RECOMMENDED_MIN_PX = 3000

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "list_products_for_review",
        "description": "List all digital products awaiting QC (status = qc_pending or concept with a file).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "check_file_specs",
        "description": (
            "Run automated spec checks on a product's file: dimensions, DPI, "
            "format, file size, color mode. Returns pass/fail for each check."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "DP-prefixed product ID"}
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "approve_product",
        "description": "Approve a digital product after QC passes. Updates status to 'approved'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "qc_notes": {"type": "string", "description": "Optional notes about quality"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "reject_product",
        "description": "Reject a digital product. Updates status to 'rejected' with reasons.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "rejection_reasons": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific reasons for rejection",
                },
                "suggested_fixes": {
                    "type": "string",
                    "description": "What needs to be fixed before re-submission",
                },
            },
            "required": ["product_id", "rejection_reasons"],
        },
    },
    {
        "name": "get_qc_summary",
        "description": "Get a summary of QC statistics: how many approved, rejected, pending.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "flag_for_revision",
        "description": "Flag a product as needing revision without fully rejecting it. Adds detailed notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "issues": {"type": "string", "description": "Specific issues found that need addressing"},
            },
            "required": ["product_id", "issues"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "list_products_for_review":
        return _list_products_for_review(store)
    if tool_name == "check_file_specs":
        return _check_file_specs(tool_input["product_id"], store)
    if tool_name == "approve_product":
        return _approve_product(tool_input, store)
    if tool_name == "reject_product":
        return _reject_product(tool_input, store)
    if tool_name == "get_qc_summary":
        return _get_qc_summary(store)
    if tool_name == "flag_for_revision":
        return _flag_for_revision(tool_input, store)
    return f"Unknown quality check tool: {tool_name}"


# ── IMPLEMENTATIONS ───────────────────────────────────────────────────────────

def _list_products_for_review(store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    reviewable = [
        p for p in products
        if p.get("status") in ("qc_pending", "concept") and p.get("file_path")
    ]
    # Newest first so the agent reviews the most recently created product first
    reviewable.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    summary = [
        {
            "id": p["id"],
            "title": p["title"],
            "type": p["product_type"],
            "status": p["status"],
            "file_path": p.get("file_path"),
            "file_format": p.get("file_format"),
            "file_size_kb": p.get("file_size_kb"),
            "created_at": p["created_at"],
        }
        for p in reviewable
    ]
    return json.dumps({
        "products_pending_review": summary,
        "count": len(summary),
        "note": "Use check_file_specs for automated checks, then approve_product or reject_product.",
    }, indent=2)


def _check_file_specs(product_id: str, store: DataStore) -> str:
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})

    file_path = product.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"No file found for {product_id}. Generate the file first."})

    # Hard stop: zero-byte file
    if os.path.getsize(file_path) == 0:
        return json.dumps({
            "product_id": product_id,
            "overall_result": "FAIL",
            "error": "File is empty (0 bytes). Regenerate the product.",
            "checks": [{"check": "File Integrity", "value": "0 bytes", "requirement": "> 0 bytes", "pass": False}],
        })

    # Hard stop: concept placeholder — never approve these
    if product.get("is_placeholder"):
        return json.dumps({
            "product_id": product_id,
            "overall_result": "FAIL",
            "error": "This is a concept placeholder card, not real art. Generate actual art with gpt-image-1 before QC.",
            "checks": [{"check": "Concept Card", "value": "Placeholder detected", "requirement": "Real generated art required", "pass": False}],
        })

    checks: list[dict] = []
    file_size_kb = os.path.getsize(file_path) // 1024

    # File size check
    size_pass = file_size_kb <= ETSY_MAX_FILE_SIZE_KB
    checks.append({
        "check": "File Size",
        "value": f"{file_size_kb} KB",
        "requirement": f"≤ {ETSY_MAX_FILE_SIZE_KB} KB (20 MB)",
        "pass": size_pass,
    })

    file_ext = os.path.splitext(file_path)[1].upper().lstrip(".")
    # Format check
    allowed_formats = {"PNG", "JPG", "JPEG", "PDF", "ZIP", "TXT"}
    format_pass = file_ext in allowed_formats
    checks.append({
        "check": "File Format",
        "value": file_ext,
        "requirement": f"One of: {', '.join(sorted(allowed_formats))}",
        "pass": format_pass,
    })

    # Image-specific checks via Pillow
    image_checks: list[dict] = []
    if file_ext in ("PNG", "JPG", "JPEG"):
        try:
            from PIL import Image as PILImage
            with PILImage.open(file_path) as img:
                img.load()  # Force full read — catches truncated/corrupt files
                width, height = img.size
                color_mode = img.mode
                dpi_info = img.info.get("dpi", (72, 72))
                # round() not int() — PIL stores 300dpi as 11811 px/m which reads back as 299.9994
                dpi = round(dpi_info[0]) if isinstance(dpi_info, tuple) else round(dpi_info)

            min_dimension = min(width, height)
            res_pass = min_dimension >= RECOMMENDED_MIN_PX
            image_checks.append({
                "check": "Resolution",
                "value": f"{width}x{height}px",
                "requirement": f"Min {RECOMMENDED_MIN_PX}px on shortest side",
                "pass": res_pass,
            })

            dpi_pass = dpi >= RECOMMENDED_DPI
            image_checks.append({
                "check": "DPI",
                "value": f"{dpi} DPI",
                "requirement": f"≥ {RECOMMENDED_DPI} DPI for print quality",
                "pass": dpi_pass,
            })

            image_checks.append({
                "check": "Color Mode",
                "value": color_mode,
                "requirement": "RGB or RGBA (PNG/JPEG), CMYK acceptable for print",
                "pass": color_mode in ("RGB", "RGBA", "CMYK"),
            })

        except ImportError:
            image_checks.append({
                "check": "Image Analysis",
                "value": "skipped",
                "requirement": "Install Pillow: pip install Pillow",
                "pass": None,
            })
        except Exception as exc:
            image_checks.append({
                "check": "Image Analysis",
                "value": f"Error: {exc}",
                "pass": False,
            })

    elif file_ext == "PDF":
        try:
            with open(file_path, "rb") as pdf_f:
                raw = pdf_f.read()
            # Header check
            has_header = raw[:5] == b"%PDF-"
            # EOF marker check
            has_eof = b"%%EOF" in raw[-200:]
            # Minimum size — a valid sellable PDF should be >50 KB
            min_size_pass = file_size_kb >= 50
            # Page count estimate (count /Type /Page objects)
            page_count = raw.count(b"/Type /Page") + raw.count(b"/Type/Page")
            product_type = product.get("product_type", "")
            min_pages = 20 if "planner" in product_type else 1
            pages_pass = page_count >= min_pages

            image_checks.append({
                "check": "PDF Header",
                "value": "Valid %PDF- header" if has_header else "Missing PDF header",
                "requirement": "File must start with %PDF-",
                "pass": has_header,
            })
            image_checks.append({
                "check": "PDF Structure",
                "value": "Valid EOF marker" if has_eof else "Missing %%EOF",
                "requirement": "PDF must have proper end-of-file marker",
                "pass": has_eof,
            })
            image_checks.append({
                "check": "PDF Size",
                "value": f"{file_size_kb} KB",
                "requirement": "≥ 50 KB (empty/stub PDFs rejected)",
                "pass": min_size_pass,
            })
            image_checks.append({
                "check": "Page Count",
                "value": f"~{page_count} pages",
                "requirement": f"≥ {min_pages} page(s) for {product_type or 'this product type'}",
                "pass": pages_pass,
            })
        except Exception as exc:
            image_checks.append({
                "check": "PDF Validation",
                "value": f"Error reading PDF: {exc}",
                "requirement": "PDF must be readable",
                "pass": False,
            })

    all_checks = checks + image_checks
    passed = sum(1 for c in all_checks if c.get("pass") is True)
    failed = sum(1 for c in all_checks if c.get("pass") is False)
    overall = "PASS" if failed == 0 else "FAIL"

    # Update product with latest spec info
    product["file_size_kb"] = file_size_kb
    product["spec_check_result"] = overall
    product["spec_check_date"] = str(date.today())
    _save_product(product, store)

    # Compute and store file hash for delivery integrity verification
    import hashlib
    with open(file_path, "rb") as hf:
        file_hash = hashlib.sha256(hf.read()).hexdigest()
    product["file_hash"] = file_hash
    _save_product(product, store)

    return json.dumps({
        "product_id": product_id,
        "file_path": file_path,
        "overall_result": overall,
        "checks_passed": passed,
        "checks_failed": failed,
        "checks": all_checks,
        "recommendation": (
            "Approve this product — all specs pass." if overall == "PASS"
            else "Fix the failed checks before approving."
        ),
    }, indent=2)


def _approve_product(data: dict, store: DataStore) -> str:
    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Product {data['product_id']} not found"})

    # Block approval if automated spec check has failed
    if product.get("spec_check_result") == "FAIL":
        return json.dumps({
            "error": "Cannot approve: automated spec check FAILED. Run check_file_specs to see what needs fixing.",
            "product_id": data["product_id"],
            "spec_result": product.get("spec_check_result"),
        })

    # Block approval of concept cards
    if product.get("is_placeholder"):
        return json.dumps({
            "error": "Cannot approve: this is a concept placeholder, not real art.",
            "product_id": data["product_id"],
        })

    product["status"] = "approved"
    product["qc_status"] = "approved"
    product["qc_notes"] = data.get("qc_notes", "Passed QC review.")
    product["qc_date"] = str(date.today())
    product["updated_at"] = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success": True,
        "product_id": data["product_id"],
        "title": product["title"],
        "status": "approved",
        "next_step": "Send to Etsy Listing Agent to create the listing.",
    }, indent=2)


def _reject_product(data: dict, store: DataStore) -> str:
    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Product {data['product_id']} not found"})

    product["status"] = "rejected"
    product["qc_status"] = "rejected"
    product["qc_rejection_reasons"] = data["rejection_reasons"]
    product["qc_suggested_fixes"] = data.get("suggested_fixes", "")
    product["qc_date"] = str(date.today())
    product["updated_at"] = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success": True,
        "product_id": data["product_id"],
        "title": product["title"],
        "status": "rejected",
        "rejection_reasons": data["rejection_reasons"],
        "suggested_fixes": data.get("suggested_fixes", ""),
        "next_step": "Fix the issues, then regenerate the file and resubmit for QC.",
    }, indent=2)


def _flag_for_revision(data: dict, store: DataStore) -> str:
    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Product {data['product_id']} not found"})

    product["qc_status"] = "revision_needed"
    product["qc_revision_notes"] = data["issues"]
    product["qc_date"] = str(date.today())
    product["updated_at"] = str(date.today())
    _save_product(product, store)

    return json.dumps({
        "success": True,
        "product_id": data["product_id"],
        "qc_status": "revision_needed",
        "issues": data["issues"],
    }, indent=2)


def _get_qc_summary(store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    by_status: dict[str, int] = {}
    for p in products:
        s = p.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    return json.dumps({
        "total_digital_products": len(products),
        "by_status": by_status,
        "pending_review": by_status.get("qc_pending", 0),
        "approved": by_status.get("approved", 0),
        "rejected": by_status.get("rejected", 0),
        "listed_on_etsy": by_status.get("listed", 0),
    }, indent=2)


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
