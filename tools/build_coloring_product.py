#!/usr/bin/env python3
"""
build_coloring_product.py <PID> — one-tap coloring-pages product build.

Generalizes the "Build whole product" flow (previously digital-planner-only,
see build_product.py) to Coloring Pages (2026-07-18, per Scott's scoping
decision to ship categories with an existing, verified generator this round).

Determines which theme pack ('kawaii' vs 'fun_basic') to build from the
product's own catalog filename convention (e.g. 'coloring_set_05.zip' ->
kawaii, 'coloring_fun_basic_set_02.zip' -> fun_basic).

Chain:
  1. Coloring pages + ZIP sets (generate_coloring_pages.py --pack <pack>) —
     caches each theme's PNG on disk and skips it if already generated, so
     re-running only pays for genuinely new/uncached pages.
  2. Quality Check (qc_sweep) — the same honest gate the planner build uses.

Deliberately does NOT generate lifestyle listing photos in this one-tap flow
-- see build_wallart_product.py's docstring for the same reasoning (a
separate, already category-agnostic tool exists for that).

Usage:  python tools/build_coloring_product.py COLOR_KAWAII_COLORING_PAGES_SET_05
"""
import json
import subprocess
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _catalog_lookup(pid: str) -> tuple[str, list[str]] | None:
    """Returns (pack, expected_file_stems) for a coloring_pages product_id, or
    None if it's not in the catalog / has no files listed. The pid itself
    (e.g. 'COLOR_KAWAII_COLORING_PAGES_SET_05') is NOT a substring of the real
    filename ('coloring_set_05.zip') -- qc_sweep.sweep(only=...) matches by
    filename substring, so the expected stems (not the pid) are what QC needs
    to be pointed at, or it silently checks nothing and reports a false PASS."""
    try:
        catalog = json.loads((_ROOT / "data" / "product_catalog.json").read_text())
    except OSError:
        return None
    entry = next((e for e in catalog if e.get("product_id") == pid), None)
    if entry is None:
        return None
    files = entry.get("files") or []
    if not files:
        return None
    pack = "fun_basic" if files[0].startswith("coloring_fun_basic_set_") else "kawaii"
    stems = [Path(f).stem for f in files]
    return pack, stems


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("usage: build_coloring_product.py <PID>  (e.g. COLOR_KAWAII_COLORING_PAGES_SET_05)")
        return 2
    pid = sys.argv[1].strip().upper()
    lookup = _catalog_lookup(pid)
    if lookup is None:
        print(f"[build_coloring_product] ✗ {pid} not found in the catalog, or has no files "
              f"listed to infer a theme pack from.")
        return 2
    pack, expected_stems = lookup
    print(f"[build_coloring_product] FULL BUILD {pid} (pack: {pack})", flush=True)

    print(f"\n{'='*60}\n[build_coloring_product] step 1/2: coloring pages ({pack}) {pid}\n{'='*60}", flush=True)
    rc = subprocess.run(
        [sys.executable, str(_TOOLS / "generate_coloring_pages.py"), "--pack", pack],
        cwd=str(_ROOT),
    ).returncode
    pages_ok = rc == 0
    if not pages_ok:
        print(f"[build_coloring_product] ⚠ generate_coloring_pages.py exited {rc} — continuing to QC.", flush=True)

    print(f"\n{'='*60}\n[build_coloring_product] step 2/2: quality check {pid}\n{'='*60}", flush=True)
    verdict = "unknown"
    try:
        import qc_sweep
        rows = []
        for stem in expected_stems:
            rows.extend(qc_sweep.sweep(only=stem))
        fails = [r for r in rows if r["severity"] == "FAIL"]
        warns = [r for r in rows if r["severity"] == "WARN"]
        verdict = "FAIL" if fails else ("WARN" if warns else "PASS")
        for r in fails + warns:
            print(f"  [{r['severity']}] {Path(str(r['file'])).name}: {r['check']} — {r['detail']}", flush=True)
        print(f"[build_coloring_product] QC verdict for {pid}: {verdict} "
              f"({len(fails)} fail, {len(warns)} warn, {len(rows)} checks)", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[build_coloring_product] ⚠ QC step failed: {exc}", flush=True)

    try:
        import backup_digital_products
        backup_digital_products.run()
    except Exception as exc:  # noqa: BLE001
        print(f"[build_coloring_product] ⚠ backup step failed (build itself is still good): {exc}", flush=True)

    print(f"\n[build_coloring_product] DONE {pid}: pages={'✓' if pages_ok else '✗'}  qc={verdict}", flush=True)
    print(f"[build_coloring_product] Listing photos are a separate step — use Create → "
          f"Listing photos for {pid} once the ZIPs look right.", flush=True)
    return 0 if pages_ok else 1


if __name__ == "__main__":
    sys.exit(main())
