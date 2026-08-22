#!/usr/bin/env python3
"""
build_wallart_product.py <PID> — one-tap wall-art product build.

Generalizes the "Build whole product" flow (previously digital-planner-only,
see build_product.py) to Wall Art (2026-07-18, per Scott's scoping decision to
ship categories with an existing, verified generator this round rather than
inventing a new photorealistic-photo pipeline for wall art in the same pass).

Chain:
  0. (2026-07-22, only when --description is given and no source art exists
     yet) Generate a brand-new print-ready master JPG via
     art_creation_tools.generate_wall_art_master() -- see that function's own
     docstring for why it, not this script, owns the actual generation call.
     This is what makes the Create screen's "+ new one" flow for Wall Art
     genuinely work end-to-end instead of dead-ending on "no source art
     found" (Scott reported that dead end live, 2026-07-22 — "every action
     on this page has to work").
  1. Multi-size print ZIP (generate_print_sizes.py) — 4x6/8x12/12x18/16x24,
     8x10/16x20, A4/A3, square @300dpi, sRGB. Pure local resize from the
     source JPG (product_files/<PID>.jpg or upscaled/<PID>.jpg), zero API cost.
  2. Quality Check (qc_sweep) — the same honest gate the planner build uses.

Deliberately does NOT generate the 10 lifestyle listing photos in this
one-tap flow -- that's a separate, already category-agnostic tool (Create
screen's "Listing photos" card / POST /api/studio/generate-lifestyle-photo,
tools/listing_photo_pipeline.py) that needs a scene prompt per shot, not a
one-line file build. Run it per-photo from the Create screen after this
finishes. Said explicitly here (and in the API response) so nothing is
silently missing from what "Build whole product" claims to do for this
category -- CLAUDE.md's top-priority rule applies to internal tooling
messaging too, not just customer-facing copy.

Usage:  python tools/build_wallart_product.py WA1030
        python tools/build_wallart_product.py WA1050 --description "a boho sun in terracotta and cream watercolor" --engine gemini
"""
import argparse
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("pid", nargs="?", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--engine", default=None)
    args, _unknown = parser.parse_known_args()

    if not args.pid.strip():
        print("usage: build_wallart_product.py <PID>  (e.g. WA1030) [--description '...'] [--engine ...]")
        return 2
    pid = args.pid.strip().upper()
    print(f"[build_wallart_product] FULL BUILD {pid}", flush=True)

    zip_ok = False
    try:
        import generate_print_sizes as gps
        up = gps.UPSCALED_DIR / f"{pid}.jpg"
        base = gps.PRODUCT_FILES_DIR / f"{pid}.jpg"
        src = up if up.exists() else base

        if not src.exists() and args.description.strip():
            print(f"\n{'='*60}\n[build_wallart_product] step 0/2: generating new master art for {pid}\n{'='*60}", flush=True)
            import art_creation_tools as act
            act.generate_wall_art_master(pid, args.description.strip(), engine=args.engine)
            # Re-resolve now that generation just wrote product_files/<PID>.jpg.
            src = up if up.exists() else base

        print(f"\n{'='*60}\n[build_wallart_product] step 1/2: print-size ZIP {pid}\n{'='*60}", flush=True)
        if not src.exists():
            print(f"[build_wallart_product] ✗ no source art for {pid} — looked for "
                  f"{pid}.jpg in product_files/ and upscaled/.", flush=True)
        else:
            gps.PRINT_ZIPS_DIR.mkdir(parents=True, exist_ok=True)
            res = gps.process_file(src, pid, force=True)
            zip_ok = res.get("status") != "error"
            print(f"[build_wallart_product] print-zip result: {res}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[build_wallart_product] ⚠ print-zip step failed: {exc}", flush=True)

    print(f"\n{'='*60}\n[build_wallart_product] step 2/2: quality check {pid}\n{'='*60}", flush=True)
    verdict = "unknown"
    try:
        import qc_sweep
        rows = list(qc_sweep.sweep(only=pid))
        fails = [r for r in rows if r["severity"] == "FAIL"]
        warns = [r for r in rows if r["severity"] == "WARN"]
        # (2026-07-25) Zero rows = sweep matched nothing (e.g. the print-zip
        # step failed above and left no ZIP) -- never report PASS for zero
        # checks. Same guard as build_coloring_product.py.
        if not rows:
            verdict = "NOT CHECKED"
        else:
            verdict = "FAIL" if fails else ("WARN" if warns else "PASS")
        for r in fails + warns:
            print(f"  [{r['severity']}] {Path(str(r['file'])).name}: {r['check']} — {r['detail']}", flush=True)
        print(f"[build_wallart_product] QC verdict for {pid}: {verdict} "
              f"({len(fails)} fail, {len(warns)} warn, {len(rows)} checks)", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[build_wallart_product] ⚠ QC step failed: {exc}", flush=True)

    try:
        import backup_digital_products
        backup_digital_products.run()
    except Exception as exc:  # noqa: BLE001
        print(f"[build_wallart_product] ⚠ backup step failed (build itself is still good): {exc}", flush=True)

    print(f"\n[build_wallart_product] DONE {pid}: print_zip={'✓' if zip_ok else '✗'}  qc={verdict}", flush=True)
    print(f"[build_wallart_product] Listing photos are a separate step — use Create → "
          f"Listing photos for {pid} once the ZIP looks right.", flush=True)
    return 0 if zip_ok else 1


if __name__ == "__main__":
    sys.exit(main())
