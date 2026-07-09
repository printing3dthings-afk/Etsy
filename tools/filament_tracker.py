#!/usr/bin/env python3
"""
filament_tracker.py

Tracks filament inventory and usage per product.
Links COGS (cost of goods sold) to each Etsy listing.

Usage:
  python tools/filament_tracker.py --log             # log new filament spool
  python tools/filament_tracker.py --use             # record usage for a product
  python tools/filament_tracker.py --status          # show inventory + COGS summary
  python tools/filament_tracker.py --cogs SKU        # show cost breakdown for one SKU
  python tools/filament_tracker.py --add-spool       # add spool from parsed tag data
"""

from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA_FILE = BASE / "data" / "filament_inventory.json"


def _load() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"filaments": [], "usage_log": [], "last_updated": None}


def _save(data: dict) -> None:
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    DATA_FILE.write_text(json.dumps(data, indent=2))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_spool(data: dict, brand: str, material: str, color: str,
              color_hex: str, weight_g: float, cost_usd: float,
              notes: str = "") -> dict:
    """Add a new filament spool to inventory."""
    spool_id = f"FIL-{len(data['filaments'])+1:03d}"
    spool = {
        "id": spool_id,
        "brand": brand,
        "material": material,
        "color": color,
        "color_hex": color_hex,
        "weight_total_g": weight_g,
        "weight_remaining_g": weight_g,
        "cost_usd": cost_usd,
        "cost_per_gram": round(cost_usd / weight_g, 4) if weight_g else 0,
        "date_added": _now(),
        "date_opened": None,
        "status": "sealed",
        "notes": notes,
        "products_made": [],
    }
    data["filaments"].append(spool)
    return spool


def log_usage(data: dict, spool_id: str, sku: str, product_name: str,
              weight_used_g: float, quantity: int = 1,
              listing_id: str = "", notes: str = "") -> dict:
    """Record filament usage for a product run."""
    spool = next((f for f in data["filaments"] if f["id"] == spool_id), None)
    if not spool:
        raise ValueError(f"Spool {spool_id} not found")

    cost = round(weight_used_g * spool["cost_per_gram"], 4)
    entry = {
        "timestamp": _now(),
        "spool_id": spool_id,
        "sku": sku,
        "product_name": product_name,
        "listing_id": listing_id,
        "weight_used_g": weight_used_g,
        "quantity_printed": quantity,
        "weight_per_unit_g": round(weight_used_g / quantity, 1),
        "filament_cost_usd": cost,
        "cost_per_unit_usd": round(cost / quantity, 4),
        "notes": notes,
    }
    data["usage_log"].append(entry)

    # Update spool remaining weight and product list
    spool["weight_remaining_g"] = round(spool["weight_remaining_g"] - weight_used_g, 1)
    if spool["status"] == "sealed":
        spool["status"] = "in_use"
        spool["date_opened"] = _now()

    if sku not in [p["sku"] for p in spool["products_made"]]:
        spool["products_made"].append({"sku": sku, "name": product_name})

    return entry


def cogs_report(data: dict, sku: str | None = None) -> None:
    """Print COGS summary by SKU."""
    log = data["usage_log"]
    if sku:
        log = [e for e in log if e["sku"].upper() == sku.upper()]

    by_sku: dict[str, list] = {}
    for e in log:
        by_sku.setdefault(e["sku"], []).append(e)

    print(f"\n{'SKU':<20} {'Product':<35} {'Units':>6} {'Fil.Cost':>9} {'Per Unit':>9}")
    print("─" * 85)
    for sku_key, entries in sorted(by_sku.items()):
        total_units = sum(e["quantity_printed"] for e in entries)
        total_cost  = sum(e["filament_cost_usd"] for e in entries)
        per_unit    = total_cost / total_units if total_units else 0
        name = entries[-1]["product_name"][:34]
        print(f"{sku_key:<20} {name:<35} {total_units:>6} ${total_cost:>8.2f} ${per_unit:>8.3f}")

    if not by_sku:
        print("  No usage logged yet.")
    print()


def status(data: dict) -> None:
    """Print inventory status."""
    filaments = data["filaments"]
    print(f"\n{'ID':<10} {'Brand':<12} {'Material':<10} {'Color':<18} {'Remaining':>10} {'$/g':>6} {'Status':<10}")
    print("─" * 80)
    for f in filaments:
        pct = f["weight_remaining_g"] / f["weight_total_g"] * 100 if f["weight_total_g"] else 0
        print(f"{f['id']:<10} {f['brand']:<12} {f['material']:<10} {f['color']:<18} "
              f"{f['weight_remaining_g']:>6.0f}g {pct:>3.0f}%  ${f['cost_per_gram']:>5.4f}  {f['status']:<10}")
    if not filaments:
        print("  No spools logged yet. Run --add-spool to add your first.")

    print(f"\nUsage log: {len(data['usage_log'])} entries")
    print(f"Last updated: {data.get('last_updated', 'never')}\n")


def interactive_add_spool(data: dict) -> None:
    print("\nAdd new filament spool")
    print("─" * 40)
    brand    = input("Brand (e.g. Bambu, Hatchbox, eSun): ").strip()
    material = input("Material (PLA/PETG/TPU/Silk PLA/etc): ").strip()
    color    = input("Color name: ").strip()
    hex_col  = input("Color hex (e.g. #FF6B6B, or press Enter to skip): ").strip() or ""
    weight   = float(input("Spool weight grams (e.g. 1000): ").strip() or 1000)
    cost     = float(input("Cost USD (e.g. 19.99): ").strip() or 0)
    notes    = input("Notes (optional): ").strip()
    spool = add_spool(data, brand, material, color, hex_col, weight, cost, notes)
    _save(data)
    print(f"\n✓ Added {spool['id']} — {brand} {material} {color} @ ${spool['cost_per_gram']:.4f}/g")


def interactive_log_usage(data: dict) -> None:
    if not data["filaments"]:
        print("No spools in inventory. Add one first with --add-spool")
        return
    status(data)
    print("\nLog filament usage")
    print("─" * 40)
    spool_id = input("Spool ID (e.g. FIL-001): ").strip().upper()
    sku      = input("Product SKU (e.g. OBC-3DRK-002): ").strip()
    name     = input("Product name: ").strip()
    lid      = input("Etsy listing ID (optional): ").strip()
    weight   = float(input("Total grams used: ").strip())
    qty      = int(input("Units printed: ").strip() or 1)
    notes    = input("Notes (optional): ").strip()
    entry = log_usage(data, spool_id, sku, name, weight, qty, lid, notes)
    _save(data)
    print(f"\n✓ Logged {weight}g for {qty}x {sku} — filament cost ${entry['filament_cost_usd']:.3f} "
          f"(${entry['cost_per_unit_usd']:.3f}/unit)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--add-spool",  action="store_true")
    parser.add_argument("--use",        action="store_true", help="Log filament usage for a product")
    parser.add_argument("--status",     action="store_true")
    parser.add_argument("--cogs",       metavar="SKU",       help="Show COGS for a specific SKU")
    parser.add_argument("--log-json",   metavar="JSON",      help="Add spool from JSON string (for automated input)")
    args = parser.parse_args()

    data = _load()

    if args.status:
        status(data)
    elif args.cogs:
        cogs_report(data, args.cogs)
    elif args.add_spool:
        interactive_add_spool(data)
    elif args.use:
        interactive_log_usage(data)
    elif args.log_json:
        d = json.loads(args.log_json)
        spool = add_spool(data, **d)
        _save(data)
        print(f"✓ {spool['id']} added")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
