#!/usr/bin/env python3
"""
Restore correct shop section assignments for all 79 listings.
Maps each listing to the correct section based on title keywords.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from etsy_api import EtsyAPIClient, EtsyAPIError

client = EtsyAPIClient()
client.refresh_access_token()

# === SECTION ID MAP ===
SEC = {
    "svg":          58769490,   # SVG Cut Files
    "planners":     58657105,   # Digital Planners
    "stickers":     58657107,   # Kawaii Sticker Packs
    "botanical":    58666507,   # Botanical and Floral Art
    "abstract":     58666617,   # Abstract and Modern Art
    "landscape":    58666619,   # Landscape and Nature Art
    "celestial":    58649236,   # Celestial and Travel Art
    "novelty":      58649260,   # Novelty and Pop Art (funny/pop, skulls, cars)
    "quote":        58666641,   # Quote & Inspiration Art
    "nursery":      58746201,   # Nursery Art
    "lamps":        58395766,   # Table Lamps
    "candle":       58412815,   # Candle Holders & Vases
    "kitchen":      58395778,   # Kitchen & Fun Signs
    "koozies":      58412823,   # Koozies & Drinkware
    "storage":      58395782,   # Jewelry & Storage
}

# === EXPLICIT MAPPING BY LISTING ID ===
LISTING_SECTION_MAP = {
    # SVG Cut Files
    4514536935: SEC["svg"],    # Good Vibes SVG Bundle
    4514392281: SEC["svg"],    # Mom Life SVG Bundle
    4514136783: SEC["svg"],    # Graduation SVG Bundle
    4514134583: SEC["svg"],    # Christian SVG Bundle
    4514130045: SEC["svg"],    # Floral SVG Bundle Cricut

    # Digital Planners
    4512188970: SEC["planners"],  # Kawaii Digital Planner Bundle 2026
    4509184968: SEC["planners"],  # Digital Fitness Planner
    4509184962: SEC["planners"],  # Digital Budget Planner
    4509184958: SEC["planners"],  # Kawaii Student Planner
    4509179201: SEC["planners"],  # Digital Planner 2026 Undated

    # Kawaii Sticker Packs
    4512255508: SEC["stickers"],  # FREE Kawaii Sticker Sheet
    4512254035: SEC["stickers"],  # Kawaii Sticker Bundle All 4
    4512254027: SEC["stickers"],  # Kawaii Sticker Pack Coral Peach
    4512255536: SEC["stickers"],  # Kawaii Sticker Pack Midnight Blue
    4512254015: SEC["stickers"],  # Kawaii Sticker Pack Cotton Candy
    4512255514: SEC["stickers"],  # Kawaii Sticker Pack Lavender Dreams

    # Botanical & Floral Art
    4512780614: SEC["botanical"],  # Pelican Watercolor
    4512768771: SEC["botanical"],  # Sunflower Watercolor
    4512768858: SEC["botanical"],  # Cherry Blossom Watercolor
    4512750191: SEC["botanical"],  # Hummingbird Watercolor
    4512301880: SEC["botanical"],  # Boho Botanical Set of 4
    4509593487: SEC["botanical"],  # Vintage Botanical Printable
    4509258700: SEC["botanical"],  # Watercolor Botanical Print
    4509198446: SEC["botanical"],  # Eucalyptus Branch
    4509193231: SEC["botanical"],  # Sage Lavender Botanical
    4512760918: SEC["botanical"],  # Lavender Fields
    4509214237: SEC["botanical"],  # Poppy Field
    4509213667: SEC["botanical"],  # White Roses
    4509259354: SEC["botanical"],  # Minimalist Botanical Line Art
    4509193237: SEC["botanical"],  # Pampas Grass

    # Landscape & Nature Art
    4512780869: SEC["landscape"],  # Fox Watercolor Woodland
    4512774863: SEC["landscape"],  # Lighthouse
    4512772539: SEC["landscape"],  # Sea Turtle
    4512772452: SEC["landscape"],  # Winter Birch
    4512770031: SEC["landscape"],  # Autumn Maple
    4512760671: SEC["landscape"],  # Snowy Owl
    4512755568: SEC["landscape"],  # Mountain Lake
    4512747600: SEC["landscape"],  # Autumn Fox
    4509214051: SEC["landscape"],  # Mountain Meadow
    4509198434: SEC["landscape"],  # Boho Wildflower
    4512763302: SEC["landscape"],  # Rooster Kitchen (farmhouse/countryside)
    4512784817: SEC["landscape"],  # Coastal Art Set of 4
    4512784922: SEC["landscape"],  # Four Seasons Set of 4
    4512776173: SEC["landscape"],  # Coral Reef
    4512758123: SEC["landscape"],  # Ocean Wave
    4512756952: SEC["botanical"],  # Wildflower Meadow -> botanical
    4509218860: SEC["landscape"],  # Japandi Tree

    # Abstract & Modern Art
    4509596017: SEC["abstract"],   # Abstract Woman Portrait
    4509600086: SEC["abstract"],   # Tropical Leaves Print (Bold Monstera)
    4509598784: SEC["abstract"],   # Abstract Brushstroke
    4509258172: SEC["abstract"],   # Checkerboard Floral

    # Celestial & Travel Art
    4509593697: SEC["celestial"],  # Grand Canyon (travel/landscape)
    4509593623: SEC["celestial"],  # Paris Skyline
    4509598660: SEC["celestial"],  # Moon Phases Print
    4512783077: SEC["celestial"],  # Paris Café
    4509214803: SEC["celestial"],  # Astronaut Space / Galaxy
    4509219594: SEC["celestial"],  # Full Moon Ocean
    4509218152: SEC["celestial"],  # Mediterranean Window (travel)

    # Quote & Inspiration Art
    4509213533: SEC["quote"],      # She Believed She Could
    4509213345: SEC["quote"],      # Good Things Take Time
    4512758458: SEC["quote"],      # Cat Reading (bookish/quote vibe)

    # Novelty & Pop Art
    4509215145: SEC["novelty"],    # Day of the Dead Skull
    4509219904: SEC["novelty"],    # Muscle Car
    4509214477: SEC["novelty"],    # Funny Dog
    4509597559: SEC["novelty"],    # Italian Kitchen

    # Nursery Art
    4512753302: SEC["nursery"],    # Baby Bear Nursery

    # 3D Products - Koozies
    4506555435: SEC["koozies"],    # Slim Can Koozie
    4506562262: SEC["koozies"],    # Standard Can Koozie
    4497769840: SEC["koozies"],    # Puffer Jacket Can Koozie

    # 3D Products - Lamps
    4488477854: SEC["lamps"],      # Crystal Glow Lamp
    4490472707: SEC["lamps"],      # Sculptural Mesh Lamp
    4497392795: SEC["lamps"],      # Geometric Glow Lamp

    # 3D Products - Candle/Vases
    4506557906: SEC["candle"],     # Ribbed Tea Light Holder
    4506559866: SEC["candle"],     # Ribbed Planter Pot
    4492610660: SEC["candle"],     # Textured Tea Light Holders
    4488532602: SEC["candle"],     # Ribbed Vase for Dried Flowers
    4497385915: SEC["candle"],     # Boho Arch Centerpiece

    # 3D Products - Kitchen/Signs
    4488666558: SEC["kitchen"],    # Coffee Bar Sign

    # 3D Products - Storage
    4507783049: SEC["storage"],    # Minimalist Pen Holder
}

def update_section(listing_id, section_id):
    try:
        client._request(
            "PATCH",
            f"shops/{client.shop_id}/listings/{listing_id}",
            body={"shop_section_id": section_id}
        )
        return True
    except EtsyAPIError as e:
        print(f"    ✗ Error: {e}")
        return False

def main():
    # Get current listing state
    data = client._request('GET', f'shops/{client.shop_id}/listings/active',
                           params={'limit': 100, 'offset': 0})
    listings = {l['listing_id']: l for l in data['results']}
    print(f"Loaded {len(listings)} listings\n")

    moved = 0
    skipped = 0
    errors = 0

    for lid, target_sec in LISTING_SECTION_MAP.items():
        if lid not in listings:
            print(f"  ⚠ Listing {lid} not found (may be inactive)")
            continue

        current_sec = listings[lid].get('shop_section_id')
        title = listings[lid]['title'][:60]

        if current_sec == target_sec:
            skipped += 1
            continue

        print(f"  → {lid} | {title}")
        print(f"    {current_sec} → {target_sec}", end=" ", flush=True)

        if update_section(lid, target_sec):
            print("✓")
            moved += 1
        else:
            errors += 1
        time.sleep(0.3)  # rate limit

    print(f"\n{'='*50}")
    print(f"✅ Moved: {moved} | Already correct: {skipped} | Errors: {errors}")
    print(f"{'='*50}")

    # Show final section distribution
    data2 = client._request('GET', f'shops/{client.shop_id}/listings/active',
                            params={'limit': 100, 'offset': 0})
    secs = {}
    for l in data2['results']:
        s = l.get('shop_section_id')
        secs[s] = secs.get(s, 0) + 1
    print("\nFinal section distribution:")
    for s, cnt in sorted(secs.items(), key=lambda x: -x[1]):
        # Find section name
        name = next((k for k, v in SEC.items() if v == s), str(s))
        print(f"  {s} ({name}): {cnt}")

if __name__ == "__main__":
    main()
