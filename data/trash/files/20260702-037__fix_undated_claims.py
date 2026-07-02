"""
One-time truthfulness fix: remove false "bonus undated version included" claims
from DP1026-1029 listing descriptions. Verified via direct Etsy API file query
(2026-06-16) that none of these 4 live listings have an undated PDF uploaded —
only a single dated PDF + sticker pack ZIP. The live descriptions falsely claim
an undated version is included. This script corrects the text only; it does not
touch price, photos, or files.
"""
import html
import sys
from tools.etsy_api import EtsyAPIClient

api = EtsyAPIClient()

EDITS = {
    4509179201: [  # DP1026
        (
            "packed with 104 beautifully designed pages, an illustrated kawaii cover, a full kawaii sticker pack (200+ stickers, 5 sheets!), and a bonus undated evergreen version so you can use it any year.",
            "packed with 104 beautifully designed pages, an illustrated kawaii cover, and a full kawaii sticker pack (200+ stickers, 5 sheets!).",
        ),
        (
            "✅ Bonus Undated Version — same planner, no year dates, works any year forever\n",
            "",
        ),
        (
            "Format: Interactive fillable PDF (2026 dated + undated versions included)",
            "Format: Interactive fillable PDF (2026 dated version)",
        ),
        (
            "Pages: 104 (each version)",
            "Pages: 104",
        ),
    ],
    4509184958: [  # DP1027
        (
            "packed with 104 beautifully designed pages in a dreamy Cotton Candy color theme, plus a full kawaii sticker pack (200+ stickers, 5 sheets!) and a bonus undated version to personalize every week of your school year.",
            "packed with 104 beautifully designed pages in a dreamy Cotton Candy color theme, plus a full kawaii sticker pack (200+ stickers, 5 sheets!) to personalize every week of your school year.",
        ),
        (
            "✅ Bonus Undated Version — same planner, no year dates, works any school year forever\n",
            "",
        ),
        (
            "Format: Interactive fillable PDF (2026 dated + undated versions included)",
            "Format: Interactive fillable PDF (2026 dated version)",
        ),
        (
            "Pages: 104 (each version)",
            "Pages: 104",
        ),
        (
            "A: The calendar pages are dated for 2026. Weekly and notes pages work any time. Bonus undated version included.",
            "A: The calendar pages are dated for 2026. Weekly and notes pages work any time.",
        ),
    ],
    4509184962: [  # DP1028
        (
            "packed with 112 beautifully designed pages in a sleek Midnight Blue color theme, with built-in trackers for every dollar, debt, and financial goal you have — plus a bonus undated version and 200+ kawaii stickers.",
            "packed with 112 beautifully designed pages in a sleek Midnight Blue color theme, with built-in trackers for every dollar, debt, and financial goal you have — plus 200+ kawaii stickers.",
        ),
        (
            "✅ Bonus Undated Version — same planner, no year dates, works any year forever\n",
            "",
        ),
        (
            "Format: Interactive fillable PDF (2026 dated + undated versions included)",
            "Format: Interactive fillable PDF (2026 dated version)",
        ),
        (
            "Pages: 112 (each version)",
            "Pages: 112",
        ),
    ],
    4509184968: [  # DP1029
        (
            "packed with 102 beautifully designed pages in a warm Coral Peach color theme, with habit trackers, meal planning, and fitness logs — plus a bonus undated version and 200+ kawaii stickers to support your healthiest year yet.",
            "packed with 102 beautifully designed pages in a warm Coral Peach color theme, with habit trackers, meal planning, and fitness logs — plus 200+ kawaii stickers to support your healthiest year yet.",
        ),
        (
            "✅ Bonus Undated Version — same planner, no year dates, works any year forever\n",
            "",
        ),
        (
            "Format: Interactive fillable PDF (2026 dated + undated versions included)",
            "Format: Interactive fillable PDF (2026 dated version)",
        ),
        (
            "Pages: 102 (each version)",
            "Pages: 102",
        ),
    ],
}

dry_run = "--apply" not in sys.argv

for listing_id, edits in EDITS.items():
    listing = api._request("GET", f"listings/{listing_id}")
    desc = html.unescape(listing["description"])
    new_desc = desc
    for old, new in edits:
        count = new_desc.count(old)
        if count != 1:
            print(f"!! {listing_id}: expected 1 match, found {count} for: {old[:80]!r}")
            continue
        new_desc = new_desc.replace(old, new)
    changed = new_desc != desc
    print(f"{listing_id}: changed={changed}")
    if changed and not dry_run:
        api.update_listing(listing_id, {"description": new_desc})
        print(f"  -> updated listing {listing_id}")

if dry_run:
    print("\nDry run only. Re-run with --apply to push changes.")
