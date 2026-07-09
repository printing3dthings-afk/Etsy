#!/usr/bin/env python3
"""
Audit all active wall-art listings — classify art source as LOCAL (verified ours)
vs CDN (sourced from listing's own Etsy photo), and flag any potential issues.
Read-only — makes no changes.
"""

import sys, re, json, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient

REPO = Path(__file__).parent.parent
ART  = REPO / "data/digital_products/product_files"
UPSC = ART / "upscaled"

SKIP_TITLE_KEYWORDS = [
    "3d printed", "koozie", "can holder", "can koozie", "lamp",
    "planter", "candle holder", "tea light", "vase", "pen holder",
    "centerpiece", "arch", "sticker pack", "sticker bundle", "sticker sheet",
    "svg bundle", "commercial license", "sublimation", "tumbler wrap",
    "digital planner", "planner bundle", "kawaii planner bundle",
    "kawaii sticker",
]

# Parse fill_all second-run log to know what CDN rank was used as art source
FILL_LOG = Path("/tmp/claude-0/-home-user-Etsy/9894bfe8-9da5-47a5-ad10-4fce7367a283/tasks/b45goju69.output")

def parse_fill_log():
    """Returns {listing_id: art_source_string} from fill_all second run."""
    if not FILL_LOG.exists():
        return {}
    result = {}
    current_lid = None
    for line in FILL_LOG.read_text().splitlines():
        m = re.match(r'\s{2}(\d+)\s+\[\d+/10\]', line)
        if m:
            current_lid = int(m.group(1))
            continue
        m = re.match(r'\s+art:\s+(\S+)', line)
        if m and current_lid:
            result[current_lid] = m.group(1)
    return result

def resolve_local_art(lid, title, lmap):
    """Returns (art_path, source_label) if local art exists, else (None, None)."""
    lid_to_pid = {v["listing_id"]: k for k, v in lmap.items()}
    pid = lid_to_pid.get(lid)
    if pid:
        for fname in lmap[pid].get("files", []):
            for cand in [ART / fname, UPSC / fname]:
                if cand.exists() and cand.suffix in (".jpg", ".png", ".jpeg"):
                    return str(cand), f"dp_listing_map → {pid}/{fname}"
    m = re.search(r"[Nn]o\.(\d+)", title)
    if m:
        n = int(m.group(1))
        for cand in [UPSC / f"DP{n}.jpg", ART / f"DP{n}.jpg"]:
            if cand.exists():
                return str(cand), f"No.{n} title pattern → {cand.name}"
    return None, None

def main():
    lmap = json.loads((REPO / "data/dp_listing_map.json").read_text())
    fill_sources = parse_fill_log()

    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Etsy token refreshed OK\n")

    all_listings = client.get_shop_listings_all(state="active", limit=100)
    print(f"Total active listings: {len(all_listings)}")

    wall_art = []
    skipped_non_art = []
    for l in all_listings:
        tlow = l["title"].lower()
        if any(kw in tlow for kw in SKIP_TITLE_KEYWORDS):
            skipped_non_art.append(l["title"][:60])
        else:
            wall_art.append(l)

    print(f"Wall-art listings: {len(wall_art)}")
    print(f"Skipped (non-wall-art): {len(skipped_non_art)}")
    print()

    local_art_listings  = []
    cdn_art_listings    = []
    cdn_r3_listings     = []   # used broken empty-room as art (now fixed)
    cdn_r1_listings     = []   # used hero as art (cleanest)
    cdn_r2_listings     = []   # used rank 2 as art
    cdn_other_listings  = []   # used rank 6+ (processed photo as art source)

    for l in sorted(wall_art, key=lambda x: x["listing_id"]):
        lid   = l["listing_id"]
        title = l["title"]
        n_photos = l.get("num_favorers", 0)  # placeholder — get real count below

        art_path, art_label = resolve_local_art(lid, title, lmap)
        fill_src = fill_sources.get(lid, "not in fill_all log")

        if art_path:
            local_art_listings.append({
                "lid": lid, "title": title[:60],
                "art": art_label, "fill_src": fill_src
            })
        else:
            entry = {"lid": lid, "title": title[:60],
                     "fill_src": fill_src}
            cdn_art_listings.append(entry)

            # Categorize by which CDN rank was used
            m = re.search(r'_r(\d+)\.jpg$', fill_src)
            if m:
                rank = int(m.group(1))
                if rank == 3:
                    cdn_r3_listings.append(entry)
                elif rank == 1:
                    cdn_r1_listings.append(entry)
                elif rank == 2:
                    cdn_r2_listings.append(entry)
                else:
                    cdn_other_listings.append(entry)
            else:
                cdn_other_listings.append(entry)

    # ── Report ────────────────────────────────────────────────────────────────
    print("=" * 70)
    print("LOCAL ART — verified our files (dp_listing_map or No.XXXX)")
    print("=" * 70)
    for e in local_art_listings:
        print(f"  ✓  {e['lid']}  {e['title']}")
        print(f"       art: {e['art']}")

    print()
    print("=" * 70)
    print("CDN ART — art sourced from listing's own Etsy rank-1/2 photo")
    print("=" * 70)

    print(f"\n  [OK] Used rank 1 (hero) as art source ({len(cdn_r1_listings)} listings):")
    for e in cdn_r1_listings:
        print(f"    {e['lid']}  {e['title']}")

    print(f"\n  [OK] Used rank 2 as art source ({len(cdn_r2_listings)} listings):")
    for e in cdn_r2_listings:
        print(f"    {e['lid']}  {e['title']}")

    print(f"\n  [NOTE] Used rank 6+ (processed photo) as art source ({len(cdn_other_listings)} listings):")
    for e in cdn_other_listings:
        print(f"    {e['lid']}  {e['title']}")
        print(f"      fill_src: {e['fill_src']}")

    print(f"\n  [FIXED] Previously used rank 3 (empty room — now cleaned up) ({len(cdn_r3_listings)} listings):")
    for e in cdn_r3_listings:
        print(f"    {e['lid']}  {e['title']}")

    print()
    print("=" * 70)
    print("LISTINGS NOT IN FILL_ALL LOG (had ≥10 photos already, untouched)")
    print("=" * 70)
    not_in_log = [l for l in wall_art
                  if l["listing_id"] not in fill_sources
                  and not resolve_local_art(l["listing_id"], l["title"], lmap)[0]]
    for l in not_in_log:
        print(f"  {l['listing_id']}  {l['title'][:60]}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Wall-art listings total:     {len(wall_art)}")
    print(f"  Verified local art (ours):   {len(local_art_listings)}")
    print(f"  CDN art (own listing photo): {len(cdn_art_listings)}")
    print(f"    - rank 1 hero:             {len(cdn_r1_listings)}")
    print(f"    - rank 2:                  {len(cdn_r2_listings)}")
    print(f"    - rank 6+ (processed):     {len(cdn_other_listings)}")
    print(f"    - rank 3 (fixed):          {len(cdn_r3_listings)}")
    print(f"  Not in fill_all log:         {len(not_in_log)}")
    print()
    print("ACTION NEEDED:")
    if cdn_other_listings:
        print(f"  ⚠  {len(cdn_other_listings)} CDN listings used a processed photo (rank 6+) as art source.")
        print("     These may show a zoomed/processed version of the art rather than the original.")
        print("     Review titles above — if any art belongs to someone else, remove listing.")
    if not_in_log:
        print(f"  ⚠  {len(not_in_log)} CDN listings were untouched (already had 10 photos).")
        print("     Manual review recommended to confirm photos show correct product.")
    if not cdn_other_listings and not not_in_log:
        print("  ✓  All listings use verified local art or their own rank-1/2 hero photo.")

if __name__ == "__main__":
    main()
