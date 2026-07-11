#!/usr/bin/env python3
"""
Update all Etsy listing descriptions to reflect the accurate sticker count.
Current reality: 5 sheets, ~79 sticker items per planner.
We claim "75+" (conservative/honest) until more stickers are generated.
"""
import os, sys, json, urllib.request, urllib.error, time, re
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

client = EtsyAPIClient()
client.refresh_access_token()
shop_id = client.shop_id
auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}


def get_listing(lid):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/listings/{lid}",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def patch_listing(lid, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{lid}",
        data=data,
        headers={**auth_headers, "Content-Type": "application/json"},
        method="PATCH"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.status == 401:
                client.refresh_access_token()
                auth_headers["Authorization"] = f"Bearer {client.access_token}"
            elif e.status == 429:
                time.sleep(15)
            else:
                raise
    raise RuntimeError(f"Failed to patch listing {lid}")


def fix_description(desc, pid):
    """Replace all false sticker count claims with accurate ones."""

    # 3 PNG sticker sheets → 5 PNG sticker sheets
    desc = re.sub(r'3 PNG sticker sheets', '5 PNG sticker sheets', desc)

    # (60+ stickers, ...) → (75+ stickers, ...)
    desc = re.sub(r'\(60\+ stickers,', '(75+ stickers,', desc)
    desc = re.sub(r'60\+ stickers', '75+ stickers', desc)

    # "import the 3 PNG files" → "import the 5 PNG files"
    desc = re.sub(r'import the 3 PNG files', 'import the 5 PNG files', desc)
    desc = re.sub(r'import the 3 PNG', 'import the 5 PNG', desc)

    # "200+ illustrated sticker" (in sticker library section of planner)
    desc = re.sub(r'200\+ illustrated sticker', '75+ kawaii sticker', desc)

    # "200+ stickers" anywhere else
    desc = re.sub(r'200\+ stickers', '75+ stickers', desc)

    # "800+ stickers" (bundle)
    desc = re.sub(r'800\+ stickers', '300+ stickers', desc)

    # "4 × Kawaii Sticker Packs — 800+ stickers total (5 sheets × 4 planners)"
    desc = re.sub(
        r'4 × Kawaii Sticker Packs — \d+\+ stickers total \(5 sheets × 4 planners\)',
        '4 × Kawaii Sticker Packs — 300+ stickers total (5 sheets × 4 planners)',
        desc)

    # "20 PNG sheets" (bundle)
    # The bundle says "800+ stickers, 20 PNG sheets" → "300+ stickers, 20 PNG sheets"
    # (20 sheets is accurate: 5 per planner × 4)

    return desc


LISTINGS = [
    ('DP1026', 4509179201),
    ('DP1027', 4509184958),
    ('DP1028', 4509184962),
    ('DP1029', 4509184968),
]

STICKER_PACK_LISTINGS = [
    ('Free Sticker Sheet',    4512255508),
    ('Lavender Pack',         4512255514),
    ('Cotton Candy Pack',     4512254015),
    ('Midnight Blue Pack',    4512255536),
    ('Coral Peach Pack',      4512254027),
    ('All 4 Packs Bundle',    4512254035),
]

BUNDLE_LISTING = 4512188970


def fix_listing(name, lid, pid=None):
    print(f"\nFixing {name} (listing {lid})...")
    l = get_listing(lid)
    old_desc = l['description']
    new_desc = fix_description(old_desc, pid or name)

    if new_desc == old_desc:
        print("  No changes needed.")
        return

    # Show what changed
    old_lines = set(re.findall(r'.{0,30}(?:sticker|stickers).{0,30}', old_desc, re.IGNORECASE))
    new_lines = set(re.findall(r'.{0,30}(?:sticker|stickers).{0,30}', new_desc, re.IGNORECASE))
    for line in sorted(old_lines - new_lines):
        print(f"  - {line.strip()}")
    for line in sorted(new_lines - old_lines):
        print(f"  + {line.strip()}")

    patch_listing(lid, {"description": new_desc})
    print(f"  ✓ Updated")
    time.sleep(1)


if __name__ == '__main__':
    print("Fixing sticker count claims across all listings...\n")

    for name, lid in LISTINGS:
        fix_listing(name, lid)

    for name, lid in STICKER_PACK_LISTINGS:
        fix_listing(name, lid)

    fix_listing("All 4 Planners Bundle", BUNDLE_LISTING)

    print("\n" + "="*50)
    print("DONE — all listings now reflect accurate sticker counts.")
    print("="*50)
    print("\nAccurate counts used:")
    print("  Per planner: 75+ stickers across 5 sheets")
    print("  Bundle total: 300+ stickers (75+ × 4 planners)")
    print("\nNext step: generate unique illustrated sticker sheets")
    print("for each planner until each reaches 200+ real stickers.")
