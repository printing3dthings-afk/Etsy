#!/usr/bin/env python3
"""
One-off corrective tool: fix mismatched "kawaii" tags on listings whose actual
product has nothing to do with kawaii.

Background (2026-06-17): an audit found 44 active listings carrying kawaii tags
('kawaii wall art', 'kawaii paper', 'kawaii character', etc.) while their titles /
products were ordinary wall art prints and scrapbook digital paper packs. Kawaii
tags on a non-kawaii product are a truthfulness violation (CLAUDE.md TOP PRIORITY
RULE) and pollute Etsy's query-matching relevance signal.

IMPORTANT — 3 of the 44 are EXCLUDED on purpose: the Fitness/Budget/Life digital
planners ARE genuinely kawaii products (their catalog tag lists legitimately
include 'kawaii planner'/'kawaii sticker pack'). Removing kawaii from those would
be deleting *accurate* tags. So this tool only touches the 41 genuine mismatches:
  - 12 digital paper packs  -> swap 'kawaii paper' + the misleading 'digital
    planner' tag for two accurate theme tags (also de-duplicates the identical
    tag block they all share, which is itself a spam-detection risk)
  - 29 wall art prints       -> replace kawaii tags with accurate subject tags

Usage:
    python tools/fix_kawaii_tag_mismatch.py            # dry run (default)
    python tools/fix_kawaii_tag_mismatch.py --apply    # push to Etsy
"""

import sys
import time
import re

sys.path.insert(0, "tools")
from etsy_api import EtsyAPIClient, EtsyAPIError

# ── New tag sets, keyed by listing_id ─────────────────────────────────────────
# Every set: exactly 13 tags, each <= 20 chars, lowercase, no 'kawaii', and no
# tag is a contiguous substring of that listing's title (validated below).

# Digital paper packs: replace 'kawaii paper' and 'digital planner' with two
# accurate per-theme tags. Base block is identical to current minus those two.
_PAPER_BASE = [
    "scrapbook paper", "printable paper", "goodnotes background",
    "digital background", "pattern paper", "scrapbook digital",
    "background paper", "paper printable", "digital download",
    "digital paper kit", "scrapbooking kit",
]  # 11 tags; 2 theme tags appended per pack -> 13


def _paper(theme1: str, theme2: str) -> list[str]:
    return [theme1, theme2] + list(_PAPER_BASE)


NEW_TAGS = {
    # ── 12 digital paper packs ────────────────────────────────────────────────
    4519456348: _paper("sunflower paper", "yellow paper"),       # Sunflower Studio
    4519457131: _paper("sage green paper", "botanical paper"),   # Sage Garden
    4519457007: _paper("teal digital paper", "coastal paper"),   # Ocean Breeze
    4519455964: _paper("brown digital paper", "coffee paper"),   # Mocha Latte
    4519455834: _paper("navy digital paper", "blue paper pack"), # Midnight Blue
    4519455652: _paper("mermaid paper", "ocean paper"),          # Mermaidcore
    4519456441: _paper("green digital paper", "matcha paper"),   # Matcha Serenity
    4519455342: _paper("lavender paper", "purple paper"),        # Lavender Dreams
    4519456175: _paper("pink digital paper", "pastel paper"),    # Cotton Candy
    4519456025: _paper("peach paper", "coral paper"),    # Coral Peach
    4519455899: _paper("sakura paper", "pink paper pack"),       # Cherry Blossom
    4519454834: _paper("celestial paper", "star paper"),         # Celestial Night

    # ── Wall art: full regeneration from subject ──────────────────────────────
    4515678344: [  # Abstract Brushstroke / Modern
        "abstract art print", "modern wall art", "minimalist art", "neutral wall art",
        "living room art", "bedroom wall art", "office wall decor", "gallery wall art",
        "housewarming gift", "gift for her", "digital print", "contemporary art", "boho wall art"],
    4515678198: [  # Vintage Botanical / Herb
        "garden wall art", "vintage wall art", "herb wall art", "kitchen wall decor",
        "botanical art", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "cottagecore art", "plant wall art"],
    4515672496: [  # Paris Skyline / Minimalist
        "paris wall art", "cityscape art", "travel wall art", "minimalist art",
        "black and white art", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "gift for her", "digital print", "city print", "france wall art"],
    4515675887: [  # Grand Canyon / Vintage
        "grand canyon art", "national park art", "travel wall art", "vintage wall art",
        "landscape print", "living room art", "office wall decor", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "desert wall art", "adventure art"],
    4515675813: [  # Tropical Leaves / Monstera Palm
        "tropical wall art", "monstera print", "palm leaf art", "botanical print",
        "green wall art", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "plant wall art", "jungle wall art"],
    4515672204: [  # Abstract Woman Portrait / Feminist Line Art
        "line art print", "woman portrait art", "feminist wall art", "abstract print",
        "minimalist art", "bedroom wall art", "living room art", "gallery wall art",
        "housewarming gift", "gift for her", "digital print", "face line art", "modern wall art"],
    4515675583: [  # Italian Kitchen / Food
        "kitchen wall art", "italian wall art", "food wall art", "restaurant decor",
        "dining room art", "living room art", "gallery wall art", "housewarming gift",
        "gift for her", "digital print", "foodie gift", "retro wall art", "cafe wall art"],
    4515675481: [  # Autumn Fox / Woodland
        "fox wall art", "woodland nursery", "autumn wall art", "animal wall art",
        "nursery wall art", "kids room decor", "bedroom wall art", "gallery wall art",
        "nature lover gift", "digital print", "forest wall art", "fall wall art", "cute animal art"],
    4515675373: [  # Hummingbird Watercolor / Botanical Bird / Floral
        "hummingbird art", "bird wall art", "watercolor art", "botanical print",
        "floral wall art", "bedroom wall art", "living room art", "gallery wall art",
        "nature lover gift", "gift for her", "digital print", "garden wall art", "spring wall art"],
    4515671764: [  # Baby Bear Nursery / Woodland Nursery
        "nursery wall art", "baby bear print", "forest nursery", "animal nursery art",
        "kids room decor", "baby shower gift", "nursery decor", "gallery wall art",
        "gift for baby", "digital print", "bear wall art", "cute nursery art", "playroom art"],
    4515675145: [  # Mountain Lake / Landscape
        "mountain wall art", "landscape print", "lake wall art", "nature wall art",
        "living room art", "office wall decor", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "cabin wall art", "adventure art"],
    4515671558: [  # Wildflower Meadow / Botanical
        "wildflower art", "meadow wall art", "botanical print", "floral wall art",
        "nature wall art", "bedroom wall art", "living room art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "cottagecore art", "flower print"],
    4515671458: [  # Cat Reading / Bookish
        "cat wall art", "bookish wall art", "book lover gift", "reading nook art",
        "cat lover gift", "living room art", "bedroom wall art", "gallery wall art",
        "cute animal art", "digital print", "library wall art", "book wall art", "cozy wall art"],
    4515671336: [  # Ocean Wave / Coastal
        "ocean wall art", "coastal wall art", "beach wall art", "wave wall art",
        "nature wall art", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nautical decor", "digital print", "blue wall art", "surf wall art"],
    4515671216: [  # Lavender Fields / Provence
        "lavender wall art", "french country art", "floral wall art", "botanical print",
        "french wall art", "bedroom wall art", "living room art", "gallery wall art",
        "housewarming gift", "gift for her", "digital print", "purple wall art", "cottagecore art"],
    4515670946: [  # Snowy Owl / Wildlife
        "owl wall art", "wildlife wall art", "bird wall art", "animal wall art",
        "winter wall art", "nursery wall art", "bedroom wall art", "gallery wall art",
        "nature lover gift", "digital print", "forest wall art", "cute animal art", "woodland art"],
    4515669596: [  # Farmhouse Rooster / Kitchen / Country
        "rooster wall art", "farmhouse decor", "kitchen wall art", "country wall art",
        "dining room art", "animal wall art", "gallery wall art", "housewarming gift",
        "rustic wall art", "digital print", "farm wall art", "chicken wall art", "cottage decor"],
    # Four Seasons Wall Art Set (4 duplicate listings, same product)
    4515672895: [
        "four seasons art", "watercolor art", "set of 4 prints", "nature wall art",
        "botanical print", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "seasonal wall art", "tree wall art"],
    4515669370: [
        "four seasons art", "watercolor art", "set of 4 prints", "nature wall art",
        "botanical print", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "seasonal wall art", "tree wall art"],
    4515669246: [
        "four seasons art", "watercolor art", "set of 4 prints", "nature wall art",
        "botanical print", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "seasonal wall art", "tree wall art"],
    4515669140: [
        "four seasons art", "watercolor art", "set of 4 prints", "nature wall art",
        "botanical print", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "seasonal wall art", "tree wall art"],
    4515668698: [  # Coastal Art Set of 4
        "coastal wall art", "beach wall art", "set of 4 prints", "ocean wall art",
        "nautical decor", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "blue wall art", "seaside wall art"],
    4515672065: [  # Fox Watercolor / Woodland
        "fox wall art", "watercolor art", "woodland art", "animal wall art",
        "nursery wall art", "bedroom wall art", "living room art", "gallery wall art",
        "nature lover gift", "digital print", "forest wall art", "cute animal art", "kids room decor"],
    4515671951: [  # Paris Cafe / French
        "paris wall art", "french wall art", "cafe wall art", "travel wall art",
        "kitchen wall art", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "gift for her", "digital print", "city print", "europe wall art"],

    # ── Wall art: good tags already, only the stray kawaii tag swapped ─────────
    4515674250: [  # Boho Botanical Floral
        "boho wall art", "botanical print", "flower wall art", "bedroom wall art",
        "living room art", "boho home decor", "gallery wall art", "housewarming gift",
        "gift for her", "nature lover gift", "art print poster", "cottagecore art", "floral art print"],
    4515674144: [  # Boho Botanical Floral
        "boho wall art", "botanical print", "flower wall art", "bedroom wall art",
        "living room art", "boho home decor", "gallery wall art", "housewarming gift",
        "gift for her", "nature lover gift", "art print poster", "cottagecore art", "floral art print"],
    4515676915: [  # Watercolor Floral / Boho
        "watercolor art", "floral wall art", "flower print", "bedroom wall art",
        "living room art", "boho wall art", "gallery wall art", "housewarming gift",
        "gift for her", "floral poster", "art print poster", "botanical print", "cottagecore art"],
    4515676301: [  # Floral Wreath
        "floral wreath print", "botanical print", "floral wall art", "bedroom wall art",
        "living room art", "cottage home decor", "gallery wall art", "housewarming gift",
        "gift for her", "wreath wall art", "art print poster", "cottagecore art", "floral art print"],
    4515672588: [  # Pastel Celestial Moon Stars
        "pastel wall art", "celestial wall art", "moon wall art", "bedroom wall art",
        "living room art", "astrology art", "gallery wall art", "housewarming gift",
        "gift for her", "pastel art print", "art print poster", "nursery wall art", "stars wall decor"],
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


def validate(listing_id: int, title: str, tags: list[str]) -> list[str]:
    """Return a list of problems with the proposed tag set (empty == clean)."""
    problems = []
    if len(tags) != 13:
        problems.append(f"expected 13 tags, got {len(tags)}")
    if len(set(tags)) != len(tags):
        problems.append("duplicate tags within the set")
    ntitle = _norm(title)
    for t in tags:
        if len(t) > 20:
            problems.append(f"tag >20 chars: '{t}' ({len(t)})")
        if t != t.lower():
            problems.append(f"tag not lowercase: '{t}'")
        if "kawaii" in t.lower():
            problems.append(f"kawaii still present: '{t}'")
        if _norm(t) and _norm(t) in ntitle:
            problems.append(f"tag duplicates title phrase: '{t}'")
    return problems


def main() -> int:
    apply = "--apply" in sys.argv
    client = EtsyAPIClient()

    # Pull current titles + tags for every target so we can show before/after and
    # validate against the real title.
    print("Fetching current listings…")
    all_listings = client.get_shop_listings_all(state="active")
    by_id = {l["listing_id"]: l for l in all_listings}

    any_invalid = False
    plans = []
    for lid, new_tags in NEW_TAGS.items():
        l = by_id.get(lid)
        if not l:
            print(f"  ⚠ {lid} not found among active listings — skipping")
            continue
        title = l.get("title", "")
        problems = validate(lid, title, new_tags)
        if problems:
            any_invalid = True
            print(f"  ✗ {lid} {title[:50]}")
            for p in problems:
                print(f"       - {p}")
        plans.append((lid, title, l.get("tags", []), new_tags))

    if any_invalid:
        print("\nABORT: one or more proposed tag sets failed validation. Fix before applying.")
        return 1

    print(f"\n{len(plans)} listings validated clean.\n")
    for lid, title, old, new in plans:
        removed = [t for t in old if t not in new]
        added = [t for t in new if t not in old]
        print(f"• {lid}  {title[:55]}")
        print(f"    - remove: {removed}")
        print(f"    + add:    {added}")

    if not apply:
        print(f"\nDRY RUN — no changes pushed. Re-run with --apply to update {len(plans)} listings.")
        return 0

    print(f"\nAPPLYING to {len(plans)} listings…")
    ok, fail = 0, 0
    for lid, title, _old, new in plans:
        # Handle the documented non-deterministic 403 'not editable' PATCH race.
        for attempt in range(3):
            try:
                client.update_listing(lid, {"tags": new})
                ok += 1
                print(f"  ✓ {lid}")
                break
            except EtsyAPIError as e:
                if e.code == 403 and attempt < 2:
                    time.sleep(2)
                    continue
                fail += 1
                print(f"  ✗ {lid} FAILED: {e}")
                break
            except Exception as e:  # noqa: BLE001
                fail += 1
                print(f"  ✗ {lid} FAILED: {e}")
                break
        time.sleep(0.4)  # gentle on the per-second rate limit

    print(f"\nDone. {ok} updated, {fail} failed.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
