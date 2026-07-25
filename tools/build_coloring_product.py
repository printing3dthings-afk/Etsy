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

(2026-07-22) A brand-new, uncataloged pid can now also be built: pass
--description (subject lines, up to generate_coloring_pages.NEW_THEME_SET_SIZE)
and this generates genuinely new coloring-page art via
generate_dynamic_theme_set() instead of the fixed kawaii/fun_basic packs --
see that function's own docstring. This is what makes the Create screen's
"+ new one" flow for Coloring Pages genuinely work end-to-end instead of
dead-ending on "not in the catalog" (Scott reported that dead end live,
2026-07-22 -- "every action on this page has to work").

(2026-07-24) main.py's coloring_pages branch now expands Scott's ONE typed
theme into exactly NEW_THEME_SET_SIZE (20) distinct, never-before-used
subjects itself (an LLM call, checked against a permanent cross-listing
registry -- see main.py's _resolve_coloring_subjects()) before spawning this
script, so --description always arrives here as 20 literal subject lines
already. This script's own job stays unchanged: one page per line, packaged
into one ZIP via build_sets(..., batch_size=gcp.NEW_THEME_SET_SIZE) below.

Usage:  python tools/build_coloring_product.py COLOR_KAWAII_COLORING_PAGES_SET_05
        python tools/build_coloring_product.py COLOR_NEW_SET --description "A sleepy fox under an oak tree
A hot air balloon over mountains" --engine gemini
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _overlay_lookup(pid: str) -> dict | None:
    """Standalone (no FastAPI import) read of the SAME durable overrides
    sidecar main.py's _product_catalog_overrides() reads -- this script runs
    as its own subprocess, not inside the API server, so it mirrors the
    volume-or-local-data-dir resolution instead of importing main.py.
    Returns a dict with `files`/`coloring_pack` for a registered
    is_new_product coloring_pages entry, or None."""
    vol_override = os.getenv("HUB_FILES_DIR", "").strip()
    if vol_override:
        base = Path(vol_override)
    elif Path("/data").is_dir():
        base = Path("/data") / "files"
    else:
        base = _ROOT / "data"
    try:
        overrides = json.loads((base / "product_catalog_overrides.json").read_text())
    except (OSError, json.JSONDecodeError):
        return None
    ov = overrides.get(pid)
    if ov and ov.get("is_new_product") and ov.get("category") == "coloring_pages":
        return {"files": ov.get("files") or [], "coloring_pack": pid.lower()}
    return None


def _catalog_lookup(pid: str) -> tuple[str, list[str]] | None:
    """Returns (pack, expected_file_stems) for a coloring_pages product_id, or
    None if it's not in the catalog / has no files listed. The pid itself
    (e.g. 'COLOR_KAWAII_COLORING_PAGES_SET_05') is NOT a substring of the real
    filename ('coloring_set_05.zip') -- qc_sweep.sweep(only=...) matches by
    filename substring, so the expected stems (not the pid) are what QC needs
    to be pointed at, or it silently checks nothing and reports a false PASS.

    (2026-07-22) Falls back to the durable overlay sidecar when the base
    catalog has no entry, so a previously-registered dynamic-theme product's
    "Regenerate" still resolves correctly -- and prefers an explicit
    `coloring_pack` field (set for every overlay/dynamic entry) over the
    filename-prefix inference below, which only ever distinguished the 2
    original fixed packs and has no way to recognize a dynamic one."""
    entry = None
    try:
        catalog = json.loads((_ROOT / "data" / "product_catalog.json").read_text())
        entry = next((e for e in catalog if e.get("product_id") == pid), None)
    except OSError:
        pass
    if entry is None:
        entry = _overlay_lookup(pid)
    if entry is None:
        return None
    files = entry.get("files") or []
    if not files:
        return None
    pack = entry.get("coloring_pack") or (
        "fun_basic" if files[0].startswith("coloring_fun_basic_set_") else "kawaii")
    stems = [Path(f).stem for f in files]
    return pack, stems


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("pid", nargs="?", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--engine", default=None)
    args, _unknown = parser.parse_known_args()

    if not args.pid.strip():
        print("usage: build_coloring_product.py <PID>  (e.g. COLOR_KAWAII_COLORING_PAGES_SET_05) [--description '...'] [--engine ...]")
        return 2
    pid = args.pid.strip().upper()

    if args.description.strip():
        print(f"[build_coloring_product] FULL BUILD {pid} (new theme)", flush=True)
        subjects = [s.strip() for s in args.description.splitlines() if s.strip()]
        try:
            import generate_coloring_pages as gcp
        except Exception as exc:  # noqa: BLE001
            print(f"[build_coloring_product] ✗ coloring-pages generator unavailable: {exc}")
            return 2
        subjects = subjects[:gcp.NEW_THEME_SET_SIZE]
        if not subjects:
            print("[build_coloring_product] ✗ no subjects provided in --description")
            return 2

        print(f"\n{'='*60}\n[build_coloring_product] step 1/2: coloring pages (new theme, {len(subjects)} pages) {pid}\n{'='*60}", flush=True)
        pages_ok = False
        expected_stems: list[str] = []
        try:
            generated = gcp.generate_dynamic_theme_set(pid, subjects, engine=args.engine)
            pages_ok = bool(generated)
            if generated:
                zip_paths = gcp.build_sets(generated, pack=pid.lower(),
                                            batch_size=gcp.NEW_THEME_SET_SIZE)
                expected_stems = [z.stem for z in zip_paths]
                print(f"[build_coloring_product] generated {len(generated)}/{len(subjects)} pages, "
                      f"{len(zip_paths)} ZIP(s)", flush=True)
            else:
                print("[build_coloring_product] ✗ no pages were generated", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[build_coloring_product] ⚠ new-theme generation failed: {exc}", flush=True)
    else:
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
        # (2026-07-25) Zero rows means qc_sweep matched NOTHING -- generation
        # failed and left no ZIPs, or expected_stems was empty. The old
        # expression turned that into a "PASS" (the exact "silently checks
        # nothing and reports a false PASS" failure mode the docstring above
        # warns about, just via the empty-rows path instead of the stem
        # mismatch it guarded against). Never report PASS for zero checks.
        if not rows:
            verdict = "NOT CHECKED"
        else:
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
