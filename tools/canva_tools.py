"""
Canva Tools — agent-facing wrapper around tools/canva_api.py.

Automates the "added in Canva post" step CLAUDE.md calls for on listing
photo slots 2, 6, 7, 9, 10 across every product line: text-overlay graphics
like what's-included callouts, numbered how-to steps, and app-compatibility
labels, built on top of a gpt-image-1-generated background.

Workflow for the agent:
  1. list_brand_templates              — see what templates Scott has built in Canva's UI
  2. get_brand_template_dataset        — discover a template's fillable field names/types
  3. upload_canva_asset                — push a local background PNG (e.g. gpt-image-1 output)
  4. generate_listing_graphic          — autofill the template + export a flattened PNG in one call

Requires CANVA_ACCESS_TOKEN in .env (run tools/canva_oauth.py) AND at least
one Brand Template created manually in the Canva UI — there is no API to
create a Brand Template from scratch.
"""
from __future__ import annotations

import json
import os

from tools.canva_api import CanvaAPIClient, CanvaAPIError, is_configured

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "check_canva_status",
        "description": "Check whether Canva is connected (access token present) and list any Brand Templates available.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_brand_templates",
        "description": (
            "List Brand Templates Scott has created in the Canva UI. "
            "Brand Templates are the only way to programmatically inject text/images into a "
            "design via Canva's API — they cannot be created via API, only discovered."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_brand_template_dataset",
        "description": (
            "Get the fillable placeholder fields (name + type: text/image/chart) for a Brand Template. "
            "Call this before generate_listing_graphic so you know what keys to pass in field_values."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_template_id": {"type": "string", "description": "ID from list_brand_templates"},
            },
            "required": ["brand_template_id"],
        },
    },
    {
        "name": "upload_canva_asset",
        "description": (
            "Upload a local image file (e.g. a gpt-image-1-generated background) to Canva as an asset. "
            "Returns an asset_id to use as an image field value in generate_listing_graphic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the local image file"},
                "asset_name": {"type": "string", "description": "Optional name for the asset (max 50 chars)"},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "generate_listing_graphic",
        "description": (
            "Full pipeline: autofill a Brand Template's placeholders with text/asset values, "
            "then export the resulting design as a flattened PNG and download it to output_path. "
            "Use this for listing photo slots that need text overlays (what's-included callouts, "
            "how-to steps, app compatibility labels, etc.) per CLAUDE.md's photo requirements. "
            "Call get_brand_template_dataset first to know the correct field_values keys/types."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_template_id": {"type": "string", "description": "ID from list_brand_templates"},
                "field_values": {
                    "type": "object",
                    "description": (
                        "Map of placeholder field name -> value. For a text field pass the string. "
                        "For an image field pass the asset_id returned by upload_canva_asset. "
                        "Example: {\"headline\": \"200+ Stickers\", \"photo\": \"<asset_id>\"}"
                    ),
                },
                "output_path": {"type": "string", "description": "Absolute local path to save the exported PNG"},
                "width": {"type": "integer", "default": 2400},
                "height": {"type": "integer", "default": 2400},
                "title": {"type": "string", "description": "Optional title for the generated Canva design"},
            },
            "required": ["brand_template_id", "field_values", "output_path"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "check_canva_status":
        return _check_status()
    if tool_name == "list_brand_templates":
        return _list_brand_templates()
    if tool_name == "get_brand_template_dataset":
        return _get_dataset(tool_input["brand_template_id"])
    if tool_name == "upload_canva_asset":
        return _upload_asset(tool_input["file_path"], tool_input.get("asset_name", ""))
    if tool_name == "generate_listing_graphic":
        return _generate_listing_graphic(tool_input)
    return f"Unknown canva tool: {tool_name}"


def _check_status() -> str:
    configured = is_configured()
    if not configured:
        return json.dumps({
            "configured": False,
            "action_needed": "Run 'python tools/canva_oauth.py' to connect Canva (requires CANVA_CLIENT_ID/CANVA_CLIENT_SECRET in .env first).",
        }, indent=2)
    try:
        client = CanvaAPIClient()
        templates = client.list_brand_templates()
        return json.dumps({
            "configured": True,
            "brand_template_count": len(templates),
            "brand_templates": [{"id": t.get("id"), "title": t.get("title")} for t in templates],
            "note": "" if templates else "No Brand Templates found. Scott must create at least one in the Canva UI before generate_listing_graphic can be used.",
        }, indent=2)
    except CanvaAPIError as e:
        return json.dumps({"configured": True, "error": str(e)}, indent=2)


def _list_brand_templates() -> str:
    if not is_configured():
        return json.dumps({"error": "Canva not connected. Run tools/canva_oauth.py first."})
    try:
        client = CanvaAPIClient()
        templates = client.list_brand_templates()
        return json.dumps({"count": len(templates), "templates": templates}, indent=2)
    except CanvaAPIError as e:
        return json.dumps({"error": str(e)})


def _get_dataset(brand_template_id: str) -> str:
    if not is_configured():
        return json.dumps({"error": "Canva not connected. Run tools/canva_oauth.py first."})
    try:
        client = CanvaAPIClient()
        dataset = client.get_brand_template_dataset(brand_template_id)
        return json.dumps({"brand_template_id": brand_template_id, "dataset": dataset}, indent=2)
    except CanvaAPIError as e:
        return json.dumps({"error": str(e)})


def _upload_asset(file_path: str, asset_name: str) -> str:
    if not is_configured():
        return json.dumps({"error": "Canva not connected. Run tools/canva_oauth.py first."})
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    try:
        client = CanvaAPIClient()
        result = client.upload_asset(file_path, asset_name)
        job = result.get("job", result)
        asset = job.get("asset", {})
        return json.dumps({
            "status": job.get("status"),
            "asset_id": asset.get("id"),
            "asset_name": asset.get("name"),
            "error": job.get("error"),
        }, indent=2)
    except CanvaAPIError as e:
        return json.dumps({"error": str(e)})


def _generate_listing_graphic(data: dict) -> str:
    if not is_configured():
        return json.dumps({"error": "Canva not connected. Run tools/canva_oauth.py first."})

    brand_template_id = data["brand_template_id"]
    field_values = data["field_values"]
    output_path = data["output_path"]
    width = data.get("width", 2400)
    height = data.get("height", 2400)
    title = data.get("title", "")

    try:
        client = CanvaAPIClient()

        # Build the autofill data map by checking each field's declared type
        dataset = client.get_brand_template_dataset(brand_template_id)
        autofill_data = {}
        for key, value in field_values.items():
            field_type = dataset.get(key, {}).get("type", "text")
            if field_type == "image":
                autofill_data[key] = {"type": "image", "asset_id": value}
            elif field_type == "chart":
                autofill_data[key] = {"type": "chart", "chart_data": value}
            else:
                autofill_data[key] = {"type": "text", "text": str(value)}

        unknown_keys = [k for k in field_values if k not in dataset]
        if unknown_keys:
            return json.dumps({
                "error": f"Unknown field key(s) for this template: {unknown_keys}",
                "available_fields": dataset,
            })

        autofill_result = client.create_autofill_job(brand_template_id, autofill_data, title=title)
        job = autofill_result.get("job", autofill_result)
        if job.get("status") != "success":
            return json.dumps({"error": f"Autofill failed: {job.get('error')}", "status": job.get("status")})

        design = job.get("result", {}).get("design", {})
        design_id = design.get("id")
        if not design_id:
            return json.dumps({"error": "Autofill succeeded but no design ID returned", "raw": job})

        export_result = client.create_export_job(design_id, fmt="png", width=width, height=height)
        export_job = export_result.get("job", export_result)
        if export_job.get("status") != "success":
            return json.dumps({"error": f"Export failed: {export_job.get('error')}", "status": export_job.get("status")})

        client.download_export(export_result, output_path)
        return json.dumps({
            "success": True,
            "design_id": design_id,
            "design_url": design.get("url"),
            "output_path": output_path,
        }, indent=2)

    except CanvaAPIError as e:
        return json.dumps({"error": str(e)})
    except KeyError as e:
        return json.dumps({"error": f"Missing required field: {e}"})
