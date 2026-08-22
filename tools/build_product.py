#!/usr/bin/env python3
"""
build_product.py <PID> — one-tap FULL product build. Chains the proven builders
in the one correct order, so a single tap turns a planner code into a
publish-ready product:

  1. Sticker pack   (build_sticker_pack.py)  — FIRST, so the sheets exist…
  2. Planner PDFs   (build_planner.py)       — …for the hyperlinker to embed into
                                                the library pages (the DP1030
                                                empty-library bug was this order)
  3. Listing photos (gen_planner_listing_photos) — real pages from the built PDF
  4. Quality Check  (qc_sweep)               — the honest gate: pages, sticker
                                                count, ZIP integrity
  5. Durability backup (backup_digital_products) — automatic (2026-07-17), so the
                                                DP1030-1034 "source files only ever
                                                existed in one place" failure mode
                                                can't happen again

Nothing is published — that stays Scott-gated. A step that fails is logged and the
chain continues where it safely can (e.g. a sticker failure still builds the
planner), so you get maximum output plus a clear list of what needs a look.

Art engine comes from IMAGE_ENGINE (default gemini) and is inherited by the two
spawned builders. Paths are volume-aware through the underlying tools.

Usage:  python tools/build_product.py DP1030
        IMAGE_ENGINE=gemini python tools/build_product.py DP1032
"""
import os
import subprocess
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _run_script(name: str, pid: str) -> bool:
    print(f"\n{'='*60}\n[build_product] running {name} {pid}\n{'='*60}", flush=True)
    rc = subprocess.run([sys.executable, str(_TOOLS / name), pid], cwd=str(_ROOT)).returncode
    if rc != 0:
        print(f"[build_product] ⚠ {name} exited {rc} for {pid} — continuing where safe.", flush=True)
    return rc == 0


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("usage: build_product.py <PID>  (e.g. DP1030)")
        return 2
    pid = sys.argv[1].strip().upper()
    engine = os.getenv("IMAGE_ENGINE", "gemini")
    print(f"[build_product] FULL BUILD {pid} (art engine: {engine})", flush=True)

    results = {}

    # 1 + 2: stickers before planner (so the library pages embed real sheets).
    results["stickers"] = _run_script("build_sticker_pack.py", pid)
    results["planner"] = _run_script("build_planner.py", pid)

    # 3: listing photos from the freshly built PDF.
    print(f"\n{'='*60}\n[build_product] step 3/4: listing photos {pid}\n{'='*60}", flush=True)
    try:
        import gen_planner_listing_photos as glp
        pdf_ok = pid in glp.PLANNER_PAGES and (Path(glp.ART_DIR) / f"{pid}.pdf").exists()
        if not pdf_ok:
            print(f"[build_product] ⚠ skipping photos — {pid}.pdf not present / not a configured planner.", flush=True)
            results["photos"] = False
        else:
            _out, photos = glp.generate_for_planner(pid, None, upload=False, engine=engine)
            print(f"[build_product] photos: {len(photos)} generated", flush=True)
            results["photos"] = len(photos) >= 9
    except Exception as exc:  # noqa: BLE001
        print(f"[build_product] ⚠ photo step failed: {exc}", flush=True)
        results["photos"] = False

    # 4: QC — the honest gate. Print the verdict + every FAIL/WARN line.
    print(f"\n{'='*60}\n[build_product] step 4/4: quality check {pid}\n{'='*60}", flush=True)
    verdict = "unknown"
    try:
        import qc_sweep
        rows = [r for r in qc_sweep.sweep(only=pid)]
        fails = [r for r in rows if r["severity"] == "FAIL"]
        warns = [r for r in rows if r["severity"] == "WARN"]
        verdict = "FAIL" if fails else ("WARN" if warns else "PASS")
        for r in fails + warns:
            print(f"  [{r['severity']}] {Path(str(r['file'])).name}: {r['check']} — {r['detail']}", flush=True)
        print(f"[build_product] QC verdict for {pid}: {verdict} "
              f"({len(fails)} fail, {len(warns)} warn, {len(rows)} checks)", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[build_product] ⚠ QC step failed: {exc}", flush=True)

    # 5: automatic durability backup (2026-07-17) — closes the exact failure mode
    # that lost DP1030-1034's source files the first time around: this used to be
    # an approval-gated command a human had to remember to run. backup_digital_
    # products.run() already knows whether it's looking at a local sandbox
    # checkout or the durable Railway volume and behaves correctly either way
    # (ZIP always made; sync only attempted from the sandbox side). A backup
    # hiccup must never fail an otherwise-good build.
    print(f"\n{'='*60}\n[build_product] step 5/5: durability backup {pid}\n{'='*60}", flush=True)
    try:
        import backup_digital_products
        backup_digital_products.run()
    except Exception as exc:  # noqa: BLE001
        print(f"[build_product] ⚠ backup step failed (build itself is still good): {exc}", flush=True)

    ok = "  ".join(f"{k}={'✓' if v else '✗'}" for k, v in results.items())
    print(f"\n[build_product] DONE {pid}: {ok}  qc={verdict}", flush=True)
    print(f"[build_product] REMINDER: eyeball the sticker sheets + photos for garbled text "
          f"before publishing. Publishing stays Scott-gated.", flush=True)
    # Exit non-zero only if the core deliverable (the planner PDF) failed — that's
    # the one thing there's no product without.
    return 0 if results.get("planner") else 1


if __name__ == "__main__":
    sys.exit(main())
