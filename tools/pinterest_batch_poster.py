"""
Pinterest Batch Poster — OnBrandCraftz

Posts all 23 wall art listings (DP1007–DP1037) to Pinterest, one pin per board
per listing, using the listing's main Etsy image as the pin image.

Prerequisites:
  1. Pinterest app approved (App ID + Secret in .env)
  2. OAuth run: python tools/pinterest_oauth.py
  3. .env has PINTEREST_ACCESS_TOKEN and PINTEREST_REFRESH_TOKEN

Usage:
  python tools/pinterest_batch_poster.py            # dry run — shows what would be posted
  python tools/pinterest_batch_poster.py --post     # actually post pins
  python tools/pinterest_batch_poster.py --post --listing DP1007   # single listing
  python tools/pinterest_batch_poster.py --boards   # create all boards first
  python tools/pinterest_batch_poster.py --status   # show what's already been posted
"""
from __future__ import annotations

import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.error

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

from tools.pinterest_api import PinterestClient, PinterestAPIError
from tools.social_media_tools import BOARDS, LISTING_BOARD_MAP, PIN_DESCRIPTIONS

# ── State file (tracks which pins have been posted) ──────────────────────────
STATE_FILE = os.path.join(ROOT, "data", "pinterest_post_state.json")

# ── Listing ID map (product_id → Etsy listing ID) ────────────────────────────
LISTING_IDS: dict[str, str] = {
    "DP1007": "4509218152",
    "DP1012": "4509258172",
    "DP1013": "4509258700",
    "DP1014": "4509213345",
    "DP1015": "4509213533",
    "DP1016": "4509213667",
    "DP1017": "4509259354",
    "DP1018": "4509218860",
    "DP1019": "4509214051",
    "DP1020": "4509214237",
    "DP1021": "4509214477",
    "DP1022": "4509219594",
    "DP1023": "4509214803",
    "DP1024": "4509219904",
    "DP1025": "4509215145",
    "DP1030": "4509598660",
    "DP1031": "4509598784",
    "DP1032": "4509593487",
    "DP1033": "4509593623",
    "DP1034": "4509593697",
    "DP1035": "4509600086",
    "DP1036": "4509596017",
    "DP1037": "4509597559",
    # Digital Planners
    "DP1026": "4509179201",
    "DP1027": "4509184958",
    "DP1028": "4509184962",
    "DP1029": "4509184968",
}

ETSY_API_KEY = os.getenv("ETSY_API_KEY", "")
ETSY_CLIENT_ID = os.getenv("ETSY_CLIENT_ID", "") or ETSY_API_KEY
ETSY_CLIENT_SECRET = os.getenv("ETSY_CLIENT_SECRET", "")
ETSY_ACCESS_TOKEN = os.getenv("ETSY_ACCESS_TOKEN", "")
SHOP_URL = "https://www.etsy.com/shop/onbrandcraftz"

# Delay between pin creation requests (seconds) — Pinterest rate limit is lenient
# but 3s between pins keeps us safe
PIN_DELAY = 3.0


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"posted": {}}  # posted[product_id][board_name] = pin_id


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_etsy_image_url(listing_id: str) -> str | None:
    """Fetch the rank-1 image URL for an Etsy listing using the OAuth API."""
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    headers = {
        "x-api-key": f"{ETSY_CLIENT_ID}:{ETSY_CLIENT_SECRET}" if ETSY_CLIENT_SECRET else ETSY_API_KEY,
        "Authorization": f"Bearer {ETSY_ACCESS_TOKEN}",
    }

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                results = data.get("results", [])
                if not results:
                    return None
                # Sort by rank, return the rank-1 image URL (largest available)
                results.sort(key=lambda x: x.get("rank", 99))
                img = results[0]
                return (
                    img.get("url_fullxfull")
                    or img.get("url_570xN")
                    or img.get("url_75x75")
                )
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt * 2)
            else:
                print(f"    Warning: could not fetch image for listing {listing_id}: {e}")
                return None
    return None


def get_or_create_board(client: PinterestClient, board_name: str, board_cache: dict) -> str | None:
    """Return board ID, creating the board if it doesn't exist. Cache results."""
    if board_name in board_cache:
        return board_cache[board_name]

    # Look up in board meta for description
    board_meta = {b["name"]: b for b in BOARDS}
    focus = board_meta.get(board_name, {}).get("focus", "OnBrandCraftz Etsy shop products")

    try:
        board_id = client.get_board_id(board_name)
        if board_id:
            board_cache[board_name] = board_id
            print(f"  Board found: {board_name!r} → {board_id}")
            return board_id

        # Create the board
        board = client.create_board(board_name, description=f"OnBrandCraftz — {focus}")
        board_id = board["id"]
        board_cache[board_name] = board_id
        print(f"  Board created: {board_name!r} → {board_id}")
        time.sleep(1)
        return board_id

    except PinterestAPIError as e:
        print(f"  ERROR creating/finding board {board_name!r}: {e}")
        return None


def cmd_status(args) -> None:
    state = load_state()
    posted = state.get("posted", {})
    all_pids = [p for p in LISTING_IDS if p in LISTING_BOARD_MAP]

    total_expected = sum(len(LISTING_BOARD_MAP[p]) for p in all_pids if p in LISTING_BOARD_MAP)
    total_posted = sum(len(boards) for boards in posted.values())

    print(f"\nPinterest Post Status")
    print(f"{'='*50}")
    print(f"Total expected pins: {total_expected}")
    print(f"Total posted pins:   {total_posted}")
    print()

    for pid in sorted(all_pids):
        boards = LISTING_BOARD_MAP.get(pid, [])
        pid_posted = posted.get(pid, {})
        done = [b for b in boards if b in pid_posted]
        todo = [b for b in boards if b not in pid_posted]
        status = "✓ complete" if not todo else f"{len(done)}/{len(boards)} boards"
        print(f"  {pid}: {status}")
        for b in todo:
            print(f"      → pending: {b}")


def cmd_boards(args) -> None:
    """Create all Pinterest boards from BOARDS list."""
    client = PinterestClient()
    if not client.access_token:
        print("ERROR: No Pinterest access token. Run: python tools/pinterest_oauth.py")
        sys.exit(1)

    print(f"Creating {len(BOARDS)} boards on Pinterest...\n")
    board_cache: dict[str, str] = {}
    for board in BOARDS:
        name = board["name"]
        get_or_create_board(client, name, board_cache)

    print(f"\nDone — {len(board_cache)} boards ready.")


def cmd_post(args) -> None:
    client = PinterestClient()
    if not client.access_token and not args.dry_run:
        print("ERROR: No Pinterest access token. Run: python tools/pinterest_oauth.py")
        sys.exit(1)

    state = load_state()
    posted = state.setdefault("posted", {})

    # Determine which listings to process
    target_pids = [args.listing] if args.listing else sorted(
        p for p in LISTING_IDS if p in LISTING_BOARD_MAP
    )

    board_cache: dict[str, str] = {}
    pin_count = 0
    skip_count = 0
    error_count = 0

    for pid in target_pids:
        listing_id = LISTING_IDS.get(pid)
        boards = LISTING_BOARD_MAP.get(pid, [])
        pin_data = PIN_DESCRIPTIONS.get(pid, {})

        if not listing_id or not boards:
            print(f"\n{pid}: skipped (no listing ID or board mapping)")
            continue

        print(f"\n{'='*55}")
        print(f"{pid} — listing {listing_id} — {len(boards)} board(s)")

        # Fetch image URL
        image_url = get_etsy_image_url(listing_id)
        if not image_url:
            print(f"  ✗ No image URL — skipping")
            continue
        print(f"  Image: {image_url[:80]}...")

        etsy_url = f"https://www.etsy.com/listing/{listing_id}"
        title = pin_data.get("title", f"{pid} Art Print | Digital Download | OnBrandCraftz")
        description = pin_data.get("description", f"Shop link in bio! {etsy_url}")

        pid_posted = posted.setdefault(pid, {})

        for board_name in boards:
            if board_name in pid_posted:
                print(f"  ↳ {board_name!r}: already posted (pin {pid_posted[board_name]})")
                skip_count += 1
                continue

            if args.dry_run:
                print(f"  [DRY RUN] Would pin to {board_name!r}")
                continue

            board_id = get_or_create_board(client, board_name, board_cache)
            if not board_id:
                error_count += 1
                continue

            for attempt in range(3):
                try:
                    pin = client.create_pin(
                        board_id=board_id,
                        title=title,
                        description=description,
                        image_url=image_url,
                        link=etsy_url,
                    )
                    pin_id = pin.get("id", "?")
                    pid_posted[board_name] = pin_id
                    save_state(state)
                    print(f"  ✓ Pinned to {board_name!r} → pin {pin_id}")
                    pin_count += 1
                    time.sleep(PIN_DELAY)
                    break
                except PinterestAPIError as e:
                    if attempt < 2:
                        wait = (attempt + 1) * 5
                        print(f"  Attempt {attempt+1} failed ({e}), retry in {wait}s")
                        time.sleep(wait)
                    else:
                        print(f"  ✗ Failed to pin to {board_name!r}: {e}")
                        error_count += 1
                except Exception as e:
                    print(f"  ✗ Unexpected error pinning to {board_name!r}: {e}")
                    error_count += 1
                    break

    print(f"\n{'='*55}")
    if args.dry_run:
        print("DRY RUN complete — no pins were actually posted.")
    else:
        print(f"Done: {pin_count} pins posted, {skip_count} skipped (already done), {error_count} errors.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pinterest batch poster for OnBrandCraftz")
    sub = parser.add_subparsers()

    # status command
    p_status = sub.add_parser("--status", help="Show posting status")
    p_status.set_defaults(func=cmd_status)

    # boards command
    p_boards = sub.add_parser("--boards", help="Create all Pinterest boards")
    p_boards.set_defaults(func=cmd_boards)

    # post command
    p_post = sub.add_parser("--post", help="Post pins to Pinterest")
    p_post.add_argument("--listing", help="Only process this product ID (e.g. DP1007)")
    p_post.add_argument("--dry-run", action="store_true", help="Show what would be posted without posting")
    p_post.set_defaults(func=cmd_post)

    # If called with no subcommand, default to dry-run mode
    args = parser.parse_args()
    if not hasattr(args, "func"):
        # Default: dry run showing all pending pins
        args.dry_run = True
        args.listing = None
        cmd_post(args)
        return

    args.func(args)


# Allow running as: python tools/pinterest_batch_poster.py [--post] [--status] [--boards]
# by mapping top-level flags to subcommands
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pinterest batch poster for OnBrandCraftz")
    parser.add_argument("--post", action="store_true", help="Actually post pins (default: dry run)")
    parser.add_argument("--boards", action="store_true", help="Create all Pinterest boards and exit")
    parser.add_argument("--status", action="store_true", help="Show posting status and exit")
    parser.add_argument("--listing", help="Only process this product ID (e.g. DP1007)")
    args = parser.parse_args()

    if args.status:
        cmd_status(args)
    elif args.boards:
        cmd_boards(args)
    else:
        args.dry_run = not args.post
        cmd_post(args)
