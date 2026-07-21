#!/usr/bin/env python3
"""
deactivate_missing_files.py

Deactivates every ACTIVE digital listing that genuinely has no hard file
behind it — neither on local disk/volume nor attached to the live Etsy
listing itself. Per CLAUDE.md's top-priority "never lie to the customer"
rule, an active listing a buyer could purchase and receive NOTHING for is
the worst compliance failure this shop can have.

CRITICAL: this reuses tools/audit_product_files.py's exact live-Etsy-VERIFIED
classification (`genuinely_missing`) — NOT a local-file-only check. A missing
LOCAL backup copy alone is a data-hygiene gap, not a reason to take a
perfectly good, currently-selling listing offline (Etsy commonly still has
the real file attached even when the local backup is gone — see
audit_product_files.py's docstring and the 2026-07-18/19 "5/176 false
missing" incidents in ops_runbook.md). Only listings where Etsy ITSELF
reports zero files attached (EtsyAPIClient.get_listing_files() returns
empty) are touched here. This means a live ETSY_ACCESS_TOKEN is required —
this script cannot run correctly (and will refuse to --execute) without one.

Physical products (3d_print_physical) and license-grant listings (no design
file of their own) are already excluded upstream by audit()'s own
`files_not_applicable` gate — this script only ever sees genuine digital
downloads that are missing their actual deliverable.

For each genuinely-missing listing, with --execute:
  1. PATCH the Etsy listing to state="inactive" (EtsyAPIClient.update_listing)
  2. Update the local product_catalog.json entry's status to "inactive" so
     the local catalog doesn't drift from what's actually live on Etsy
  3. Record every action (succeeded/failed) in a timestamped report file

Defaults to a DRY RUN — pass --execute to actually make changes. This is a
real, customer-facing, revenue-affecting mutation against the live shop;
review the dry-run list before ever passing --execute.

Usage:
    python tools/deactivate_missing_files.py                    # dry run, print + report only
    python tools/deactivate_missing_files.py --execute           # actually deactivate (asks to confirm)
    python tools/deactivate_missing_files.py --execute --yes     # skip the confirmation prompt
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

# audit_product_files (imported below) needs these set before it imports main.py —
# same convention every standalone script that touches main.py already uses.
os.environ.setdefault("APP_SECRET_TOKEN", "deactivate-script-not-a-real-secret")
os.environ.setdefault("DB_PATH", str(BASE / "data" / "hub.db"))

from tools.audit_product_files import audit  # noqa: E402
from tools.etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402

CATALOG_PATH = BASE / "data" / "product_catalog.json"


def _report_path() -> Path:
    return BASE / "data" / "reports" / f"deactivate_missing_files_{time.strftime('%Y-%m-%d')}.json"


def _load_catalog(catalog_path: Path) -> list[dict]:
    return json.loads(catalog_path.read_text())


def _write_catalog(catalog_path: Path, catalog: list[dict]) -> None:
    tmp = catalog_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(catalog, indent=2))
    tmp.replace(catalog_path)


def run(execute: bool, client: EtsyAPIClient | None = None,
        catalog_path: Path = CATALOG_PATH, audit_result: dict | None = None) -> dict:
    """Core logic, independent of the CLI so it's directly unit-testable.

    `audit_result` can be injected (skips the live audit() call) for tests
    that want to drive `run()` without going through the full audit pipeline
    a second time; production callers always let this run the real audit."""
    client = client or EtsyAPIClient()
    audit_result = audit_result if audit_result is not None else audit(client=client)
    targets = audit_result["genuinely_missing"]

    catalog = _load_catalog(catalog_path)
    by_id = {p["product_id"]: p for p in catalog}

    deactivated: list[dict] = []
    failed: list[dict] = []
    catalog_changed = False

    for t in targets:
        pid = t["product_id"]
        listing_id = t["listing_id"]
        if not execute:
            deactivated.append({**t, "dry_run": True})
            continue
        try:
            client.update_listing(listing_id, {"state": "inactive"})
        except EtsyAPIError as e:
            failed.append({**t, "error": str(e)})
            continue
        except Exception as e:  # noqa: BLE001 -- any transport failure must not look like success
            failed.append({**t, "error": f"request failed: {e}"})
            continue
        entry = by_id.get(pid)
        if entry is not None:
            entry["status"] = "inactive"
            entry["last_updated"] = time.strftime("%Y-%m-%d")
            entry["note"] = (
                f"Auto-deactivated {time.strftime('%Y-%m-%d')} by tools/deactivate_missing_files.py — "
                f"no digital file attached on Etsy and no local backup. Reactivate only after "
                f"re-uploading and verifying a real file."
            )
            catalog_changed = True
        deactivated.append(t)

    if execute and catalog_changed:
        _write_catalog(catalog_path, catalog)

    return {
        "executed": execute,
        "deactivated": deactivated,
        "failed": failed,
        "skipped_audit": audit_result["skipped"],
        "verified_live_untouched": len(audit_result["verified_live"]),
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def main_cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execute", action="store_true",
                         help="Actually deactivate on Etsy + update the local catalog (default: dry run)")
    parser.add_argument("--yes", action="store_true",
                         help="Skip the interactive confirmation prompt when --execute is passed")
    args = parser.parse_args()

    # Run the live-Etsy audit exactly once and reuse it for both the preview
    # and (if --execute) the real pass -- calling audit() twice would double
    # every listing's Etsy round-trip for no benefit and risks the two calls
    # disagreeing if shop state changes in between.
    client = EtsyAPIClient()
    audit_result = audit(client=client)
    preview = run(execute=False, client=client, audit_result=audit_result)
    targets = preview["deactivated"]

    print(f"Listings with NO file attached on Etsy AND no local backup ({len(targets)}):")
    for t in targets:
        print(f"  ⚠️  {t['product_id']} ({t['category']}) — {t['title']} (Etsy #{t['listing_id']})")
    print(f"\nVerified live on Etsy (has real files, left untouched): {preview['verified_live_untouched']}")
    if preview["skipped_audit"]:
        print(f"Skipped during audit (no listing id / API error — re-run to retry): {len(preview['skipped_audit'])}")
        for s in preview["skipped_audit"]:
            print(f"  ? {s['product_id']}: {s['reason']}")

    if not targets:
        print("\nNothing to deactivate.")
        return 0

    if not args.execute:
        print(f"\nDRY RUN — no changes made. Re-run with --execute to deactivate these {len(targets)} listing(s).")
        report = {**preview, "executed": False}
        path = _report_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2))
        print(f"Report written to {path}")
        return 0

    if not args.yes:
        resp = input(
            f"\nThis will set state=inactive on {len(targets)} LIVE Etsy listing(s) above. Type 'yes' to continue: "
        ).strip().lower()
        if resp != "yes":
            print("Aborted — no changes made.")
            return 1

    result = run(execute=True, client=client, audit_result=audit_result)
    print(f"\nDeactivated {len(result['deactivated'])} listing(s), {len(result['failed'])} failure(s).")
    for f in result["failed"]:
        print(f"  ✗ {f['product_id']}: {f['error']}")

    path = _report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2))
    print(f"Report written to {path}")
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    sys.exit(main_cli())
