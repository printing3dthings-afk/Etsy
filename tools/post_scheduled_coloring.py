#!/usr/bin/env python3
"""
tools/post_scheduled_coloring.py

Scheduled coloring book poster — generates a new coloring page pack
(alternating between Adult, Kids, and Kawaii), packages ZIP files and metadata,
creates an Etsy draft listing, and STAGES it in Frank's Action Center for
one-tap approval.

Never publishes to Etsy automatically — enforces Frank's Hard Stop / Autonomy Boundaries.

State file: data/coloring_schedule.json

Usage:
    python tools/post_scheduled_coloring.py            # run if due today
    python tools/post_scheduled_coloring.py --force    # generate + stage now regardless of schedule
    python tools/post_scheduled_coloring.py --preview  # test generation without staging on Etsy
    python tools/post_scheduled_coloring.py --status   # show current rotation status
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_env_path = _ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for line in _f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

STATE_FILE = _ROOT / "data" / "coloring_schedule.json"
PACK_ROTATION = ["adult", "kids", "kawaii"]
DAYS_BETWEEN_POSTS = 4


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "queue_position": 0,
        "next_post_date": date.today().isoformat(),
        "history": [],
    }


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def run_scheduled_coloring(force: bool = False, preview: bool = False) -> dict:
    state = load_state()
    today_str = date.today().isoformat()

    if not force and state.get("next_post_date") and today_str < state["next_post_date"]:
        print(f"[SCHEDULED COLORING] Not due yet. Next run scheduled for {state['next_post_date']}.")
        return {"status": "not_due", "next_post_date": state["next_post_date"]}

    pos = state.get("queue_position", 0) % len(PACK_ROTATION)
    pack = PACK_ROTATION[pos]

    print(f"\n============================================================")
    print(f" [SCHEDULED COLORING] Generating Pack: '{pack}' (Position {pos + 1}/{len(PACK_ROTATION)})")
    print(f"============================================================\n", flush=True)

    import generate_coloring_pages as gcp

    if preview:
        print("[SCHEDULED COLORING] Preview mode — testing generation metadata...")
        meta = gcp._LISTING_META.get(pack, {})
        print(f"  Pack Title: {meta.get('title')}")
        print(f"  Price: ${meta.get('price')}")
        print(f"  Tags ({len(meta.get('tags', []))}): {', '.join(meta.get('tags', []))}")
        return {"status": "preview_complete", "pack": pack}

    # Generate full page set. PACKS[pack] is the theme list directly (no
    # "themes"/"style" sub-dict), and generate_coloring_pages.py has no
    # generate_pack() batch function -- this now matches the same per-theme
    # loop that module's own main() uses (2026-08-06 fix: the previous code
    # here never worked, TypeError'd on every scheduled run since this script
    # was written -- see ops_runbook.md).
    themes = gcp.PACKS[pack]
    generated_files = []
    for theme in themes:
        p = gcp.generate_coloring_page(theme, gcp.COLORING_DIR)
        if p:
            generated_files.append(p)

    if not generated_files:
        print("[SCHEDULED COLORING] ✗ Image generation failed or returned 0 files.")
        return {"status": "failed", "error": "No pages generated"}

    # Build ZIP package
    zip_paths = gcp.build_sets(generated_files, pack=pack, batch_size=gcp.PAGES_PER_SET)
    listing_json_path = gcp.generate_listing_json(zip_paths, pack=pack)

    # Update schedule state
    next_date = (date.today() + timedelta(days=DAYS_BETWEEN_POSTS)).isoformat()
    state["queue_position"] = (pos + 1) % len(PACK_ROTATION)
    state["next_post_date"] = next_date
    state["history"].append({
        "date": today_str,
        "pack": pack,
        "pages_count": len(generated_files),
        "zip_count": len(zip_paths),
        "listing_json": str(listing_json_path),
    })
    save_state(state)

    print(f"\n[SCHEDULED COLORING] ✓ Successfully generated '{pack}' pack with {len(generated_files)} pages!")
    print(f"[SCHEDULED COLORING] Next run scheduled for: {next_date}")

    return {
        "status": "success",
        "pack": pack,
        "pages": len(generated_files),
        "zips": len(zip_paths),
        "next_post_date": next_date,
    }


def main():
    parser = argparse.ArgumentParser(description="Scheduled Coloring Book Generator & Stager")
    parser.add_argument("--force", action="store_true", help="Force run now regardless of schedule")
    parser.add_argument("--preview", action="store_true", help="Test pack metadata without generating images")
    parser.add_argument("--status", action="store_true", help="Display current schedule status")
    args = parser.parse_args()

    if args.status:
        state = load_state()
        pos = state.get("queue_position", 0) % len(PACK_ROTATION)
        print(f"Coloring Schedule Status:")
        print(f"  Next Pack: {PACK_ROTATION[pos]}")
        print(f"  Next Date: {state.get('next_post_date', 'Not scheduled')}")
        print(f"  Total Posts Completed: {len(state.get('history', []))}")
        return

    result = run_scheduled_coloring(force=args.force, preview=args.preview)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
