#!/usr/bin/env python3
"""
build_planner.py <PID> — one-shot planner build for Frank's one-tap "Build planner"
capability. Chains the two proven CLIs Claude runs by hand:

  1. generate_planner_v2.py <PID>   → base dated + undated PDFs + AI cover art
  2. planner_hyperlinker.py <PID>   → final PDFs with hyperlinked nav, TOC,
                                      fillable fields, and embedded sticker sheets

then copies the `_v2_final` outputs to the plain delivery names (<PID>.pdf,
<PID>U.pdf). Running the CLIs (rather than reimplementing) keeps this in lockstep
with the manual build.

The only AI/API touch is the cover image (a few cents); everything else is local
reportlab/PyMuPDF. Paths are volume-aware through the underlying scripts'
resolve_dp_base(), so on the Railway server this reads/writes the durable volume.

Usage:  python tools/build_planner.py DP1030
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent


def _dp_base() -> Path:
    vol = os.getenv("HUB_FILES_DIR", "").strip()
    if vol and Path(vol).is_dir():
        return Path(vol)
    if Path("/data/files").is_dir():
        return Path("/data/files")
    return _ROOT / "data" / "digital_products"


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("usage: build_planner.py <PID>  (e.g. DP1030)")
        return 2
    pid = sys.argv[1].strip().upper()
    py = sys.executable

    print(f"[build_planner] {pid}: building base PDFs + cover art…", flush=True)
    if subprocess.run([py, str(_TOOLS / "generate_planner_v2.py"), pid], cwd=str(_ROOT)).returncode != 0:
        print(f"[build_planner] FAILED: base build did not complete for {pid}")
        return 1

    print(f"[build_planner] {pid}: finalizing (nav, TOC, fillable fields, sticker sheets)…", flush=True)
    if subprocess.run([py, str(_TOOLS / "planner_hyperlinker.py"), pid], cwd=str(_ROOT)).returncode != 0:
        print(f"[build_planner] FAILED: finalize did not complete for {pid}")
        return 1

    pf = _dp_base() / "product_files"
    copied = []
    for final_name, deliver_name in (
        (f"{pid}_v2_final.pdf", f"{pid}.pdf"),
        (f"{pid}U_v2_final.pdf", f"{pid}U.pdf"),
    ):
        src = pf / final_name
        if src.exists():
            shutil.copy2(src, pf / deliver_name)
            copied.append(deliver_name)

    if not copied:
        print(f"[build_planner] FAILED: no finalized PDFs were produced for {pid}")
        return 1

    # Automatic durability backup (2026-07-17) — closes the exact failure mode that
    # lost DP1030-1034's source files the first time (approval-gated, so nobody
    # remembered to run it). A backup hiccup must never fail an otherwise-good build.
    try:
        import backup_digital_products
        backup_digital_products.run()
    except Exception as exc:  # noqa: BLE001
        print(f"[build_planner] ⚠ backup step failed (build itself is still good): {exc}", flush=True)

    print(f"[build_planner] DONE {pid}: {', '.join(copied)} (in {pf})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
