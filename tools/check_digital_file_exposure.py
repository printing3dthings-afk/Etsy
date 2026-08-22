#!/usr/bin/env python3
"""
OnBrandCraftz — Digital File Exposure Check
=============================================
Mission: "Providing the best and most accurate transaction for our customers
so we can grow responsibly."

Read-only audit for the failure class found 2026-07-15: a product's real
source files (PDF, sticker ZIP, cover art, print-size ZIP, etc.) existing
nowhere durable — not on disk, not on Etsy. Three checks:

  1. Every catalog entry with status=active and a real etsy_listing_id:
     confirm its live listing still has at least one file attached via
     GET .../listings/{id}/files. A listing that drops to 0 files is the
     exact failure mode this check exists to catch early.
  2. Every catalog entry that is NOT yet published (draft/ready_for_review/
     qc_pending, empty etsy_listing_id): confirm every path in its "files"
     list actually exists on disk. A missing path here means the product's
     underlying work has no known copy anywhere -- this is what surfaced
     DP1030-1034 as a total loss during the 2026-07-15 audit.
  3. data/hub_db_backups/hub_db_state.json (Frank's own todos/actions/
     activity-log snapshot, see backup_hub_db.py) hasn't gone stale. It went
     a full week stale once already (caught and refreshed 2026-07-15) with
     nothing to flag it -- there's no automated way to keep it fresh (a
     human still has to run backup_hub_db.py and commit the output), so this
     is the early-warning half of that gap, not a fix for the gap itself.

Never mutates anything -- pure read (Etsy GET + local os.path.exists).

Usage:
  python tools/check_digital_file_exposure.py
"""

import os, sys, json, pathlib, time
from datetime import datetime, timezone

# Repo-relative, not hardcoded -- this script runs both on Scott's machine and
# (via main.py's _EXEC_COMMANDS registry) inside Frank's Railway container,
# which has no /home/user/Etsy and no .env file (env vars are injected by the
# platform directly). See ops_runbook.md 2026-06-17 for the bug class this
# pattern avoids.
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_env_path = ROOT / '.env'
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient

CATALOG_PATH = ROOT / 'data' / 'product_catalog.json'
UNPUBLISHED_STATUSES = {'draft', 'ready_for_review', 'qc_pending'}
HUB_DB_BACKUP_PATH = ROOT / 'data' / 'hub_db_backups' / 'hub_db_state.json'
HUB_DB_BACKUP_MAX_AGE_DAYS = 10


def _load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text())


def check_live_listings(catalog: list[dict], client: EtsyAPIClient) -> list[dict]:
    """Flag any active, published listing whose Etsy files list is empty."""
    problems = []
    active = [p for p in catalog if p.get('status') == 'active' and p.get('etsy_listing_id')]
    for p in active:
        lid = p['etsy_listing_id']
        try:
            files = client.get_listing_files(lid)
        except Exception as exc:
            problems.append({
                'product_id': p.get('product_id', '?'), 'listing_id': lid,
                'issue': f'could not fetch file list: {exc}',
            })
            continue
        if not files:
            problems.append({
                'product_id': p.get('product_id', '?'), 'listing_id': lid,
                'issue': 'live listing has ZERO digital files attached',
            })
        time.sleep(0.15)  # gentle on Etsy's per-second rate limit across a full catalog sweep
    return problems


def check_unpublished_local_files(catalog: list[dict]) -> list[dict]:
    """Flag any not-yet-published product whose listed file paths don't exist on disk."""
    problems = []
    for p in catalog:
        if p.get('status') not in UNPUBLISHED_STATUSES:
            continue
        if p.get('etsy_listing_id'):
            continue  # has a listing_id despite a draft-ish status -- Etsy check above covers it
        missing = [f for f in p.get('files', []) if not (ROOT / f).is_file()]
        if missing:
            problems.append({
                'product_id': p.get('product_id', '?'), 'status': p.get('status'),
                'missing_count': len(missing), 'total_count': len(p.get('files', [])),
                'missing_files': missing,
            })
    return problems


def check_hub_db_backup_staleness() -> dict | None:
    """Flag data/hub_db_backups/hub_db_state.json if it's missing, unreadable,
    or older than HUB_DB_BACKUP_MAX_AGE_DAYS. Returns a problem dict, or None
    if the backup is present and fresh."""
    if not HUB_DB_BACKUP_PATH.is_file():
        return {'issue': f'{HUB_DB_BACKUP_PATH.relative_to(ROOT)} does not exist'}
    try:
        exported_at = json.loads(HUB_DB_BACKUP_PATH.read_text()).get('exported_at')
    except Exception as exc:
        return {'issue': f'could not read/parse hub_db_state.json: {exc}'}
    if not exported_at:
        return {'issue': 'hub_db_state.json has no exported_at timestamp'}
    try:
        exported = datetime.fromisoformat(exported_at)
    except ValueError:
        return {'issue': f'hub_db_state.json has an unparseable exported_at: {exported_at}'}
    if exported.tzinfo is None:
        exported = exported.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - exported).days
    if age_days > HUB_DB_BACKUP_MAX_AGE_DAYS:
        return {'issue': f'hub_db_state.json is {age_days} days stale (last exported {exported_at})'}
    return None


def main():
    catalog = _load_catalog()
    client = EtsyAPIClient()

    live_problems = check_live_listings(catalog, client)
    local_problems = check_unpublished_local_files(catalog)
    hub_db_problem = check_hub_db_backup_staleness()

    print(f"\n{'='*70}\nDIGITAL FILE EXPOSURE CHECK — {len(catalog)} catalog entries\n{'='*70}")

    print(f"\n[LIVE LISTINGS] {len(live_problems)} problem(s):")
    for pr in live_problems:
        print(f"  ✗ {pr['product_id']} (listing {pr['listing_id']}): {pr['issue']}")
    if not live_problems:
        print("  ✓ every active listing has at least one file attached")

    print(f"\n[UNPUBLISHED PRODUCTS] {len(local_problems)} product(s) with missing local files:")
    for pr in local_problems:
        print(f"  ✗ {pr['product_id']} ({pr['status']}): "
              f"{pr['missing_count']}/{pr['total_count']} listed files missing on disk")
        for f in pr['missing_files']:
            print(f"      missing: {f}")
    if not local_problems:
        print("  ✓ every unpublished product's listed files exist on disk")

    print(f"\n[HUB DB BACKUP] ", end="")
    if hub_db_problem:
        print(f"✗ {hub_db_problem['issue']}")
    else:
        print("✓ hub_db_state.json is present and fresh")

    n_problems = len(live_problems) + len(local_problems) + (1 if hub_db_problem else 0)
    print(f"\n{'='*70}")
    print(f"RESULT: {n_problems} problem(s) found across {len(catalog)} catalog entries")
    print("="*70)

    sys.exit(1 if n_problems else 0)


if __name__ == "__main__":
    main()
