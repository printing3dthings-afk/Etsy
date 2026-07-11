#!/usr/bin/env python3
"""
stage_p3d_photo_approvals.py
One-off script (NOT part of the live server) to push the 9 P3D listings' already-
generated, already-verified replacement photos into the Action Center approval
queue, so Scott can review/approve/reject them from /frank instead of a chat file
dump. No Etsy listing is touched by this script — it only stages pending
`listing_photo` actions via POST /api/queue/stage-photo; uploading to the live
listing happens only when Scott taps Approve.

Source photos: /tmp/p3d_photos/generated/<SKU>/photo_<rank>.jpg (rank is the
2-digit slot number embedded in the filename, e.g. photo_06.jpg -> rank 6).

For each SKU this script:
  1. Looks up etsy_listing_id from data/product_catalog.json
  2. Downloads the listing's current rank-1 photo (the real product photo already
     live on Etsy) to use as the `design_paths` reference for any future reject-fix
     regeneration via generate_verified_photo()
  3. POSTs the generated photo + listing_id/rank/sku/physics/scene_prompt/design_paths
     to /api/queue/stage-photo on the target hub server

Usage:
    python tools/stage_p3d_photo_approvals.py                  # stage all 9 SKUs
    python tools/stage_p3d_photo_approvals.py --sku P3D_CRYSTAL_GLOW_LAMP
    HUB_BASE_URL=https://your-app.up.railway.app python tools/stage_p3d_photo_approvals.py
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = Path("/tmp/p3d_photos/generated")
SOURCE_DIR = ROOT / "data" / "p3d_photo_sources"

HUB_BASE_URL = os.getenv("HUB_BASE_URL", "http://localhost:8000").rstrip("/")
APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "").strip()

# Maps each SKU to its PHYSICS template key in tools/listing_photo_pipeline.py.
SKU_PHYSICS = {
    "P3D_COFFEE_BAR_SIGN": "sign_flat",
    "P3D_CRYSTAL_GLOW_LAMP": "3d_print_lamp",
    "P3D_GEOMETRIC_GLOW_LAMP": "3d_print_lamp",
    "P3D_MINIMALIST_PEN_HOLDER": "3d_print_holder",
    "P3D_RIBBED_PLANTER_POT": "3d_print_planter",
    "P3D_RIBBED_TEA_LIGHT_HOLDER": "3d_print_holder",
    "P3D_RIBBED_VASE_FOR_DRIED_FLOWERS": "3d_print_vase",
    "P3D_SCULPTURAL_MESH_LAMP": "3d_print_lamp",
    "P3D_TEXTURED_TEA_LIGHT_HOLDERS": "3d_print_holder",
}


def _load_catalog() -> dict[str, dict]:
    catalog = json.loads((ROOT / "data" / "product_catalog.json").read_text())
    return {item["product_id"]: item for item in catalog}


def _scene_prompt_for(sku: str, name: str) -> str:
    return (
        f"Photorealistic Etsy product photography of the real {name} (actual 3D printed "
        "product, not a stand-in). Render the exact physical object shown in the source "
        "photo — same shape, same colors, same surface finish — staged in a complementary "
        "lifestyle scene. The product itself must not be altered or redesigned."
    )


def _download_rank1_image(client, listing_id: str, dest: Path) -> Path | None:
    """Download the listing's current rank-1 image — the real product photo already
    live on Etsy — as the design reference for any future reject-fix regeneration."""
    try:
        images = client.get_listing_images(listing_id)
    except Exception as exc:
        print(f"  ! could not fetch listing images for {listing_id}: {exc}")
        return None
    rank1 = next((img for img in images if img.get("rank") == 1), None)
    if not rank1:
        rank1 = images[0] if images else None
    if not rank1:
        print(f"  ! listing {listing_id} has no images to use as a design reference")
        return None
    url = rank1.get("url_fullxfull") or rank1.get("url_570xN")
    if not url:
        return None
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)
    return dest


def stage_sku(sku: str, catalog: dict[str, dict], client) -> None:
    entry = catalog.get(sku)
    if not entry:
        print(f"! {sku}: not found in product_catalog.json — skipping")
        return
    listing_id = entry.get("etsy_listing_id")
    if not listing_id:
        print(f"! {sku}: no etsy_listing_id in catalog — skipping")
        return
    photo_dir = GENERATED_DIR / sku
    if not photo_dir.is_dir():
        print(f"! {sku}: no generated photos at {photo_dir} — skipping")
        return
    physics = SKU_PHYSICS.get(sku, "sign_flat")
    scene_prompt = _scene_prompt_for(sku, entry.get("name", sku))

    source_path = _download_rank1_image(client, listing_id, SOURCE_DIR / sku / "source_rank1.jpg")
    design_paths = [str(source_path)] if source_path else []

    photo_files = sorted(photo_dir.glob("photo_*.jpg"))
    if not photo_files:
        print(f"! {sku}: no photo_*.jpg files in {photo_dir} — skipping")
        return

    for photo_path in photo_files:
        m = re.search(r"photo_(\d+)", photo_path.stem)
        rank = int(m.group(1)) if m else 1
        summary = f"New photo for {sku} (listing {listing_id}, rank {rank})"
        print(f"  staging {photo_path.name} -> listing {listing_id} rank {rank} ...", end=" ")
        try:
            r = requests.post(
                f"{HUB_BASE_URL}/api/queue/stage-photo",
                params={
                    "listing_id": listing_id,
                    "rank": rank,
                    "sku": sku,
                    "summary": summary,
                    "physics": physics,
                    "scene_prompt": scene_prompt,
                    "design_paths": json.dumps(design_paths),
                },
                data=photo_path.read_bytes(),
                headers={
                    "Authorization": f"Bearer {APP_TOKEN}",
                    "Content-Type": "application/octet-stream",
                },
                timeout=60,
            )
            r.raise_for_status()
            d = r.json()
            print(f"action_id={d.get('action_id')}")
        except requests.HTTPError as exc:
            detail = ""
            try:
                detail = exc.response.json().get("detail", "")
            except Exception:
                pass
            print(f"FAILED: {exc} {detail}")
        except Exception as exc:
            print(f"FAILED: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sku", help="Stage only this SKU (default: all 9 P3D SKUs found)")
    args = parser.parse_args()

    if not APP_TOKEN:
        print("APP_SECRET_TOKEN is not set in the environment — cannot authenticate to the hub.")
        return 1

    sys.path.insert(0, str(ROOT))
    from tools.etsy_api import EtsyAPIClient

    client = EtsyAPIClient()
    catalog = _load_catalog()

    skus = [args.sku] if args.sku else sorted(SKU_PHYSICS.keys())
    print(f"Hub: {HUB_BASE_URL}")
    for sku in skus:
        print(f"== {sku} ==")
        stage_sku(sku, catalog, client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
