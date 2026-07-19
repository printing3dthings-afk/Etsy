#!/usr/bin/env python3
"""
etsy_file_inventory.py

Full inventory of what Etsy actually has on file for every active listing
(2026-07-19). Scott asked the Files tab to show every file from the Etsy
listings themselves, not just Frank's own local/generated storage -- this is
the sweep that makes that possible.

Etsy's Open API v3 does NOT expose a way to download a listing's digital
file content -- GET .../listings/{id}/files returns metadata only (filename,
size, rank, upload date), confirmed against this codebase's own prior
incidents (data/knowledge_base/ops_runbook.md, 2026-06-19 and 2026-06-20:
lost local backups could not be restored via the API for exactly this
reason). So this script records names/sizes, not bytes -- the Files-tab UI
cross-references each filename against the local file index
(_catalog_filename_index() in main.py) to offer a real download where a
local copy happens to exist, and an honest "open on Etsy" link otherwise.
Never claims a local copy IS what's live on Etsy -- it's labeled as a local
copy, full stop.

Sweeps every `status: "active"` catalog product with a real etsy_listing_id
(unlike tools/audit_product_files.py, this is NOT limited to products
already flagged as missing files -- it's a full inventory, not a gap audit).
Read-only against Etsy -- calls only get_listing_files(), never uploads or
modifies anything.

Writes its findings to a durable report file (the persistent Railway volume
when configured, else data/etsy_file_inventory_report.json for local runs)
that GET /api/etsy-files reads on each request -- see
_etsy_file_inventory_report() in main.py. Runs automatically once a day via
_calendar_tasks_loop() so the Files tab stays fresh without Scott needing to
remember to run this by hand.

Usage:
    python tools/etsy_file_inventory.py                    # sweep + write report
    python tools/etsy_file_inventory.py --dry-run           # print only, no write
    python tools/etsy_file_inventory.py --product DP1026    # sweep a single product
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tools" / "api_server"))

# main.py needs these set before import -- same convention tests/*.py and
# audit_product_files.py already use when importing it standalone.
os.environ.setdefault("APP_SECRET_TOKEN", "etsy-inventory-not-a-real-secret")
os.environ.setdefault("DB_PATH", str(BASE / "data" / "hub.db"))

import main as _main  # noqa: E402 -- needs sys.path/env set up first
from tools.etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402

REPORT_FILENAME = "etsy_file_inventory_report.json"


def _report_path() -> Path:
    vol = _main._FILE_ROOTS.get("volume")
    if vol:
        return vol / REPORT_FILENAME
    return BASE / "data" / REPORT_FILENAME


def _catalog() -> list[dict]:
    return json.loads((BASE / "data" / "product_catalog.json").read_text())


def sweep(only_product: str | None = None, client: EtsyAPIClient | None = None) -> dict:
    """Core sweep logic, importable/testable independent of the CLI. `client`
    is injectable so tests can pass a mock instead of hitting real Etsy."""
    catalog = _catalog()
    overrides = _main._product_catalog_overrides()
    statuses = _main._build_products_status(catalog, _main._catalog_file_exists, overrides)
    by_id = {s["id"]: s for s in statuses}

    client = client or EtsyAPIClient()
    listings: list[dict] = []
    skipped: list[dict] = []

    for entry in catalog:
        pid = entry.get("product_id")
        if only_product and pid != only_product:
            continue
        row = by_id.get(pid)
        if row is None or row.get("status") != "active":
            continue
        listing_id = row.get("listing_id")
        if not listing_id:
            skipped.append({"product_id": pid, "reason": "no etsy_listing_id on an active product"})
            continue
        try:
            etsy_files = client.get_listing_files(listing_id)
        except EtsyAPIError as e:
            skipped.append({"product_id": pid, "reason": str(e)})
            continue
        except Exception as e:  # noqa: BLE001 -- any transport failure must not look like "zero files"
            skipped.append({"product_id": pid, "reason": f"request failed: {e}"})
            continue
        listings.append({
            "product_id": pid,
            "title": row.get("title"),
            "category": row.get("category"),
            "listing_id": listing_id,
            "files": [
                {
                    "filename": f.get("filename"),
                    "listing_file_id": f.get("listing_file_id"),
                    "size_bytes": f.get("size_bytes"),
                    "rank": f.get("rank"),
                    "create_timestamp": f.get("create_timestamp"),
                }
                for f in etsy_files
            ],
        })

    return {"listings": listings, "skipped": skipped}


def main_cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Print results, don't write the report file")
    parser.add_argument("--product", help="Sweep a single product_id instead of the whole active catalog")
    args = parser.parse_args()

    result = sweep(only_product=args.product)
    result["swept_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    total_files = sum(len(l["files"]) for l in result["listings"])
    print(f"Inventoried {len(result['listings'])} active listing(s), {total_files} file(s) total.")
    for l in result["listings"]:
        names = ", ".join(f["filename"] for f in l["files"]) or "(no files attached)"
        print(f"  {l['product_id']} (Etsy #{l['listing_id']}) — {names}")

    print(f"\nSkipped (no listing id / API error, re-run to retry): {len(result['skipped'])}")
    for r in result["skipped"]:
        print(f"  ? {r['product_id']}: {r['reason']}")

    if not args.dry_run:
        path = _report_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, indent=2))
        tmp.replace(path)
        print(f"\nReport written to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main_cli())
