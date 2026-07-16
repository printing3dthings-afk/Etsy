#!/usr/bin/env python3
"""
qc_sweep.py — pre-publish quality sweep of every digital deliverable.

Runs each product file through the same content gate used at upload
(validate_digital_file) plus type-specific deep checks, and reports anything that would
fail or look wrong BEFORE it reaches a buyer. Nothing here touches the Etsy API — it
inspects local files only.

Checks by type:
  Planner PDF  — content gate (parses, >=10pp) + page-count sanity + dated/undated pair
  Sticker ZIP  — content gate + transparent PNG sheets + sticker/sheet counts
  Print ZIP    — content gate + expected size subfolders + README + sRGB embedded
  Other ZIP    — content gate (valid archive, has product files, under 20MB)

Usage:
    python tools/qc_sweep.py                 # sweep everything, print report
    python tools/qc_sweep.py --json out.json # also write a machine-readable report
    python tools/qc_sweep.py --only DP1030   # filter to matching filenames
    python tools/qc_sweep.py --fail-only     # print only WARN/FAIL rows
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from tools.etsy_api import validate_digital_file, FileContentError  # noqa: E402


def resolve_dp_base() -> Path:
    """Where the digital-product files actually live for THIS environment.

    On a hosted deploy (Railway) the repo's data/ dir is ephemeral/gitignored and
    the real files sit on the durable volume — sync_files_to_hub.py uploads them
    under <volume>/files/ with the same layout as data/digital_products/ (so
    product_files/, print_zips/, stickers/ …). Mirror main.py's resolution so
    Frank's one-tap Quality Check finds the same files the Files screen shows.
    Locally (Scott's machine, this sandbox) neither is set → the repo dir, unchanged.
    """
    vol = os.getenv("HUB_FILES_DIR", "").strip()
    if vol and Path(vol).is_dir():
        return Path(vol)
    if Path("/data/files").is_dir():
        return Path("/data/files")
    return BASE_DIR / "data" / "digital_products"


DP_BASE = resolve_dp_base()
PF_DIR = DP_BASE / "product_files"
PRINT_ZIP_DIR = DP_BASE / "print_zips"

# Expected planner page counts (from CLAUDE.md catalog). Tolerance applied below.
# DP1030-1034 corrected 2026-07-09 against actual pypdf page counts — the old
# figures (98/105/108/102) were guesses that drifted 5-36 pages from the real
# files and were silently passing/failing on luck rather than ground truth.
PLANNER_PAGES = {
    "DP1026": 143, "DP1027": 131, "DP1028": 144, "DP1029": 133,
    "DP1030": 130, "DP1031": 141, "DP1032": 140, "DP1033": 107, "DP1034": 142,
}
PAGE_TOLERANCE = 8  # generated count may differ slightly from the catalog figure

PRINT_SUBFOLDERS = {"2x3", "4x5", "a_series", "square"}


def _rows():
    """Yield (severity, file, check, detail). severity in PASS/WARN/FAIL."""
    out = []

    def add(sev, f, check, detail=""):
        out.append({"severity": sev, "file": f, "check": check, "detail": detail})

    return out, add


def dp_code_from_stem(stem: str) -> str:
    """Extract the leading DP#### product code from a filename stem, tolerant of
    the undated 'U' suffix and version suffixes like '_v2'/'_v2_final' (e.g.
    DP1034_v2_final, DP1034U_v2_final -> 'DP1034'). Falls back to the raw stem
    with a trailing 'U' stripped if it doesn't look like a DP code at all."""
    m = re.match(r"^(DP\d+)", stem)
    return m.group(1) if m else stem.rstrip("U")


def gate(path: Path, rows_add, **kw) -> dict | None:
    """Run the upload content gate; record PASS/FAIL. Returns facts or None on fail."""
    try:
        facts = validate_digital_file(str(path), **kw)
        rows_add("PASS", path.name, "content_gate",
                 ", ".join(f"{k}={v}" for k, v in facts.items() if k != "path"))
        return facts
    except FileContentError as e:
        rows_add("FAIL", path.name, "content_gate", str(e))
        return None


def check_planner_pdf(path: Path, rows_add):
    facts = gate(path, rows_add, expected_ext=".pdf")
    if not facts:
        return
    code = dp_code_from_stem(path.stem)
    expected = PLANNER_PAGES.get(code)
    pages = facts.get("pdf_pages", 0)
    if expected:
        if abs(pages - expected) > PAGE_TOLERANCE:
            rows_add("WARN", path.name, "page_count",
                     f"{pages}pp vs catalog {expected}pp (>{PAGE_TOLERANCE} off)")
        else:
            rows_add("PASS", path.name, "page_count", f"{pages}pp (~{expected})")


def check_sticker_zip(path: Path, rows_add):
    facts = gate(path, rows_add, expected_ext=".zip")
    if not facts:
        return
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        sheets = [n for n in names if "png_sheets/" in n and n.endswith(".png")]
        indiv = [n for n in names if "individual_stickers/" in n and n.endswith(".png")]
        # Legacy packs may store sheets flat (no png_sheets/ folder)
        if not sheets:
            sheets = [n for n in names if n.lower().endswith((".png", ".jpg")) and "/" not in n]

        if len(sheets) < 5:
            rows_add("WARN", path.name, "sheet_count",
                     f"{len(sheets)} sheets (standard is 5+)")
        else:
            rows_add("PASS", path.name, "sheet_count", f"{len(sheets)} sheets")

        # Transparency check on the first sheet found inside png_sheets/
        png_sheet = next((n for n in names if n.endswith(".png") and "png_sheets/" in n), None)
        if png_sheet:
            with Image.open(io.BytesIO(zf.read(png_sheet))) as im:
                has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
                if has_alpha:
                    rows_add("PASS", path.name, "transparency", f"{png_sheet.split('/')[-1]} has alpha")
                else:
                    rows_add("FAIL", path.name, "transparency",
                             f"{png_sheet.split('/')[-1]} is opaque ({im.mode}) — imports as a white box")
        else:
            rows_add("WARN", path.name, "transparency",
                     "no png_sheets/*.png to verify (legacy JPG pack — white-box risk)")

        if indiv:
            # Below 50 is not "a smaller pack" — it's the background-removal blob
            # defect (found 2026-07-09 on DP1030-1034: 9 sheets x 1 sticker each,
            # because the sheet background was never stripped so every sheet fused
            # into a single connected component). A real, working pack never comes
            # in this low, so this is a hard FAIL, not a soft undercount warning.
            if len(indiv) < 50:
                label = "FAIL"
                detail = f"{len(indiv)} individual stickers (<50 — looks like the background-removal blob defect, not a real pack)"
            elif len(indiv) < 200:
                label = "WARN"
                detail = f"{len(indiv)} individual stickers (<200 target)"
            else:
                label = "PASS"
                detail = f"{len(indiv)} individual stickers"
            rows_add(label, path.name, "sticker_count", detail)


def check_print_zip(path: Path, rows_add):
    facts = gate(path, rows_add, expected_ext=".zip")
    if not facts:
        return
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        folders = {n.split("/")[0] for n in names if "/" in n}
        missing = PRINT_SUBFOLDERS - folders
        if missing:
            rows_add("WARN", path.name, "size_folders", f"missing {sorted(missing)}")
        else:
            rows_add("PASS", path.name, "size_folders", "2x3/4x5/a_series/square present")

        if not any(n.lower().endswith("readme.txt") for n in names):
            rows_add("WARN", path.name, "readme", "no README.txt")

        # sRGB embedded on a sample JPEG?
        sample = next((n for n in names if n.lower().endswith(".jpg")), None)
        if sample:
            with Image.open(io.BytesIO(zf.read(sample))) as im:
                if "icc_profile" in im.info:
                    rows_add("PASS", path.name, "srgb", "sRGB profile embedded")
                else:
                    rows_add("WARN", path.name, "srgb",
                             "no embedded color profile (re-run generate_print_sizes.py)")


def check_other_zip(path: Path, rows_add):
    gate(path, rows_add, expected_ext=".zip")


def sweep(only: str | None = None) -> list[dict]:
    """Run the full pre-publish QC sweep and return the raw rows
    (list of {severity, file, check, detail}). `only` filters to files whose
    name contains that substring (e.g. a product code like "DP1030").

    Importable so the dashboard (Frank's one-tap Quality Check) and the CLI run
    the exact same checks — no shelling out, no drift between the two.
    """
    global Image
    from PIL import Image  # local import so the module imports without PIL present

    rows, add = _rows()

    def want(p: Path) -> bool:
        return (only.lower() in p.name.lower()) if only else True

    # Planner PDFs (DP1026-1034, dated + undated)
    planner_codes = tuple(PLANNER_PAGES)
    for pdf in sorted(PF_DIR.glob("*.pdf")):
        if not want(pdf):
            continue
        if pdf.stem.rstrip("U") in planner_codes:
            check_planner_pdf(pdf, add)

    # Sticker ZIPs
    for z in sorted(PF_DIR.glob("*_sticker_pack.zip")):
        if want(z):
            check_sticker_zip(z, add)

    # Print ZIPs (wall art)
    for z in sorted(PRINT_ZIP_DIR.glob("*.zip")):
        if want(z):
            check_print_zip(z, add)

    # Other deliverable ZIPs (coloring pages, digital paper)
    for sub in ("coloring_pages/sets", "digital_paper"):
        for z in sorted((DP_BASE / sub).glob("*.zip")):
            if want(z):
                check_other_zip(z, add)

    return rows


def main():
    ap = argparse.ArgumentParser(description="Pre-publish QC sweep of digital deliverables")
    ap.add_argument("--json", help="Write machine-readable report to this path")
    ap.add_argument("--only", help="Only files whose name contains this substring")
    ap.add_argument("--fail-only", action="store_true", help="Print only WARN/FAIL rows")
    args = ap.parse_args()

    rows = sweep(args.only)

    # Report
    by_file: dict[str, list[dict]] = {}
    for r in rows:
        by_file.setdefault(r["file"], []).append(r)

    n_fail = sum(1 for r in rows if r["severity"] == "FAIL")
    n_warn = sum(1 for r in rows if r["severity"] == "WARN")

    print(f"\n{'='*70}\nQC SWEEP — {len(by_file)} files, {len(rows)} checks\n{'='*70}")
    for fname in sorted(by_file):
        frows = by_file[fname]
        worst = "FAIL" if any(r["severity"] == "FAIL" for r in frows) else \
                "WARN" if any(r["severity"] == "WARN" for r in frows) else "PASS"
        if args.fail_only and worst == "PASS":
            continue
        mark = {"PASS": "✓", "WARN": "!", "FAIL": "✗"}[worst]
        print(f"\n{mark} {fname}")
        for r in frows:
            if args.fail_only and r["severity"] == "PASS":
                continue
            print(f"    [{r['severity']}] {r['check']}: {r['detail']}")

    print(f"\n{'='*70}")
    print(f"RESULT: {len(by_file)} files | {n_fail} FAIL · {n_warn} WARN · "
          f"{sum(1 for r in rows if r['severity']=='PASS')} PASS")
    print("="*70)

    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2))
        print(f"Report written → {args.json}")

    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
