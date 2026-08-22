#!/usr/bin/env python3
"""
audit_product_files.py

Etsy-first verification for the "missing files" flags on the Products screen
(2026-07-18). The file-existence resolution logic in main.py
(_catalog_file_exists()) was fixed the same day this script was added -- most
non-planner categories' catalog paths were never rooted under
data/digital_products/ and were silently mis-resolved -- but a "missing"
flag can still be legitimate: the real product file might genuinely live only
on Scott's own machine, or might genuinely not exist anywhere.

Before assuming any "active" (live, real Etsy listing) product with a
missing-files flag is a genuine "customer might be getting nothing"
compliance problem, this script checks what's ACTUALLY attached to the live
Etsy listing via EtsyAPIClient.get_listing_files() -- read-only, no writes to
Etsy. Per CLAUDE.md's top-priority rule, an active listing with no real
content behind it is a hard-stop compliance issue that must be surfaced, not
silently ignored -- but an active listing that simply has no LOCAL backup
copy is an operational gap, not an emergency, and must NOT trigger
auto-regenerated replacement content (that could show a buyer art/pages that
don't match what they already paid for).

Classifies every "active" catalog product whose files aren't confirmed
present locally into:
  - verified_live: Etsy has real digital files attached today. Not a
    compliance risk -- just a missing local backup, queued for a later
    backfill download rather than urgent action.
  - genuinely_missing: neither the local/volume check nor Etsy itself has
    anything. This is the real "customer might be getting nothing" bucket --
    surfaced to GET /api/alerts (source: "product_file_integrity") so it
    becomes a visible punch list for Scott instead of a buried dashboard
    percentage.
  - skipped: no Etsy listing id to check against, or the Etsy call itself
    failed (auth/rate limit/network) -- reported separately so an API
    problem is never silently counted as "missing".

Writes its findings to a durable report file (the persistent Railway volume
when configured, else data/file_audit_report.json for local runs) that
GET /api/alerts reads on each request -- see _file_audit_report() in main.py.

Usage:
    python tools/audit_product_files.py                    # audit + write report
    python tools/audit_product_files.py --dry-run           # print only, no write
    python tools/audit_product_files.py --product DP1026    # audit a single product
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

# main.py needs these set before import -- same convention tests/*.py already
# use when importing it standalone (see e.g. tests/test_bundle_opportunities.py).
os.environ.setdefault("APP_SECRET_TOKEN", "audit-script-not-a-real-secret")
os.environ.setdefault("DB_PATH", str(BASE / "data" / "hub.db"))

import main as _main  # noqa: E402 -- needs sys.path/env set up first
from tools.etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402

REPORT_FILENAME = "file_audit_report.json"


def _report_path() -> Path:
    vol = _main._FILE_ROOTS.get("volume")
    if vol:
        return vol / REPORT_FILENAME
    return BASE / "data" / REPORT_FILENAME


def _catalog() -> list[dict]:
    return json.loads((BASE / "data" / "product_catalog.json").read_text())


def audit(only_product: str | None = None, client: EtsyAPIClient | None = None) -> dict:
    """Core audit logic, importable/testable independent of the CLI. `client`
    is injectable so tests can pass a mock instead of hitting real Etsy."""
    catalog = _catalog()
    overrides = _main._product_catalog_overrides()
    statuses = _main._build_products_status(catalog, _main._catalog_file_exists, overrides)
    by_id = {s["id"]: s for s in statuses}

    client = client or EtsyAPIClient()
    verified_live: list[dict] = []
    genuinely_missing: list[dict] = []
    skipped: list[dict] = []

    for entry in catalog:
        pid = entry.get("product_id")
        if only_product and pid != only_product:
            continue
        row = by_id.get(pid)
        if row is None or row.get("status") != "active":
            continue
        if row.get("files_not_applicable") or row.get("all_files_present") is True:
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
        except Exception as e:  # noqa: BLE001 -- any transport failure must not look like "missing"
            skipped.append({"product_id": pid, "reason": f"request failed: {e}"})
            continue
        if etsy_files:
            verified_live.append({
                "product_id": pid,
                "listing_id": listing_id,
                "etsy_file_names": [f.get("filename") for f in etsy_files],
                "local_files": [fs["name"] for fs in row.get("files", [])],
            })
        else:
            genuinely_missing.append({
                "product_id": pid,
                "listing_id": listing_id,
                "title": row.get("title"),
                "category": row.get("category"),
                "expected_files": [fs["name"] for fs in row.get("files", [])],
            })

    return {
        "verified_live": verified_live,
        "genuinely_missing": genuinely_missing,
        "skipped": skipped,
    }


def main_cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Print results, don't write the report file")
    parser.add_argument("--product", help="Audit a single product_id instead of the whole active catalog")
    args = parser.parse_args()

    result = audit(only_product=args.product)
    result["audited_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    print(f"Verified live on Etsy (local backup gap only, not urgent): {len(result['verified_live'])}")
    for r in result["verified_live"]:
        print(f"  ✅ {r['product_id']} — Etsy has {len(r['etsy_file_names'])} file(s): {', '.join(r['etsy_file_names'])}")

    print(f"\nGenuinely missing everywhere (compliance risk — flag for Scott): {len(result['genuinely_missing'])}")
    for r in result["genuinely_missing"]:
        print(f"  ⚠️  {r['product_id']} ({r['category']}) — {r['title']} (Etsy #{r['listing_id']})")

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
