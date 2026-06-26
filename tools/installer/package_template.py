"""Distribution-time packaging script — turns this repo into a fresh,
business-IP-free template a new owner can deploy as their own instance.

Never touches the working tree. Builds the package in a temp directory from
a clean git snapshot (tracked files + untracked-but-not-gitignored files,
i.e. exactly what `git add -A` would pick up), strips Scott's proprietary
OnBrandCraftz business data via an explicit exclude list, resets the CEO
agent's accumulated knowledge-base logs to empty seeds (or to a generalized
override, if one has been written — see template_overrides/), runs a secrets
safety grep, then zips the result.

Usage:
    python tools/installer/package_template.py --dry-run
    python tools/installer/package_template.py --output dist/etsy-hub-template.zip
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OVERRIDES_DIR = Path(__file__).resolve().parent / "template_overrides"

# ---------------------------------------------------------------------------
# Business-IP exclusion list
# ---------------------------------------------------------------------------
# Maintained as an allowlist-of-exclusions rather than the inverse: Scott's
# business data is concentrated and enumerable, while the reusable framework
# (agents/, tools/, town_app/, web/, mobile_app/) is not — a denylist here is
# far less likely to silently exclude framework code than an allowlist would
# be to silently leak business data.
EXCLUDE_DIRS = [
    "data/3d_print_signs", "data/backups", "data/brand", "data/commercial_license_photos",
    "data/design_references", "data/digital_products", "data/faith_pack", "data/financial",
    "data/grad_pack", "data/groovy_pack", "data/kdp", "data/mom_life_pack", "data/performance",
    "data/printify", "data/reports", "data/retro_moms_pack", "data/shop_assets", "data/social",
    "data/sublimation_mockups", "data/sublimation_pack", "data/sublimation_samples",
    "data/svg_bundles", "data/svg_pack", "data/trash",
    "review_batches", "pinterest_app_demo",
]
EXCLUDE_FILES = [
    # data/ root-level business state (catalogs, schedules, logs, manifests)
    "data/ads_log.json", "data/art_pipeline.json", "data/art_schedule.json",
    "data/bundle_listing.json", "data/dashboard.html", "data/decision_log.json",
    "data/dp1030_listing.json", "data/dp1033_listing.json", "data/dp_listing_map.json",
    "data/filament_inventory.json", "data/fix_queue.json", "data/health_log.json",
    "data/listing_approvals.json", "data/listing_audit_report.json",
    "data/listing_cleanup_2026-06-18.json", "data/listing_image_manifest.json",
    "data/listing_manifest.json", "data/listing_rules.json", "data/makerworld_specs.json",
    "data/marketing_copy.md", "data/new_3d_product_ideas.json",
    "data/pending_listing_updates.json", "data/photo_hash_cache.json",
    "data/planner_gap_analysis.json", "data/planner_reupload_2026-06-18.json",
    "data/printify_shipping_state.json", "data/product_art_registry.json",
    "data/product_catalog.json", "data/registered_commands.json", "data/schedule.json",
    "data/sj_layered_design_FINAL.svg", "data/shop_data.json", "data/tiktok_app_icon.png",
    "data/tiktok_content_calendar.json", "data/todo.md",
    # Root-level business-branded files
    "OnBrandCraftz_SKU_Catalog_2026-05-21.xlsx", "OnBrandCraftz Dashboard.bat",
    "OnBrandCraftz Dashboard.command", "art_review.html", "market_references.html",
    "products_index.html", "privacy.html", "PRIVACY_POLICY.md",
    # Windows-only Scott-specific launchers — superseded by setup_wizard.py (cross-platform)
    "SETUP.bat", "Setup.bat", "START_HUB.bat", "Update.bat", "setup_desktop_shortcut.bat",
    "Setup Etsy OAuth.bat", "Setup Pinterest OAuth.bat", "Start Command Center.bat",
    "Start Frank Local.bat", "Start Town.bat",
]

# knowledge_base/ files that hold Scott's accumulated operational history or
# research rather than reusable doctrine. Reset to an empty seed of the same
# JSON/Markdown shape unless template_overrides/knowledge_base/<name> exists
# (populated by the separate CLAUDE.md/knowledge-base editorial split).
KNOWLEDGE_BASE_SEED_FILES = [
    "action_plan_2026.md", "business_standards.md", "ceo_learnings.md",
    "ceo_operating_playbook.md", "competitor_research_2026.md",
    "design_quality_research_2026-06.md", "designs.json", "insights.json",
    "lifestyle_photo_mastery.md", "ops_runbook.md", "performance.json",
    "price_tests.md", "room_library.json", "strategies.json",
    "sublimation_standards.md",
]
KNOWLEDGE_BASE_SEED_DIRS = ["market_research"]

MD_SEED_HEADER = "# {title}\n\n_New instance — no entries yet._\n"

# Patterns checked against every text file in the finished package. Anything
# matching aborts the build — directly motivated by the SETUP.bat leaked-key
# incident this plan flagged. `.env.example`'s placeholder strings (e.g.
# "your_anthropic_api_key_here") never match these, since they require
# real-looking key bodies.
SECRET_PATTERNS = [
    re.compile(r"sk-ant-api\d{2}-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{32,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"AIza[A-Za-z0-9_\-]{30,}"),
    re.compile(r"\bETSY_API_KEY=[a-z0-9]{20,}"),
    re.compile(r"\bETSY_CLIENT_SECRET=[a-z0-9]{8,}"),
]
TEXT_SUFFIXES = {
    ".py", ".js", ".ts", ".json", ".md", ".txt", ".html", ".css", ".sh", ".bat",
    ".toml", ".cfg", ".ini", ".yml", ".yaml", ".env", "",
}


def _git_tracked_and_untracked_files():
    """Returns repo-relative paths git would include in a fresh `git add -A` —
    i.e. tracked files plus untracked files not covered by any .gitignore."""
    tracked = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return tracked + untracked


def _is_excluded(rel_path: str) -> bool:
    for d in EXCLUDE_DIRS:
        if rel_path == d or rel_path.startswith(d + "/"):
            return True
    return rel_path in EXCLUDE_FILES


def _seed_content_for(original_path: Path) -> str:
    name = original_path.name
    if name == "ceo_learnings.md":
        return MD_SEED_HEADER.format(title="CEO Agent Learnings")
    if name == "ops_runbook.md":
        return MD_SEED_HEADER.format(title="Ops Runbook — Infrastructure Incidents & Fixes")
    if original_path.suffix == ".md":
        return MD_SEED_HEADER.format(title=name.replace(".md", "").replace("_", " ").title())
    if original_path.suffix == ".json":
        try:
            original = original_path.read_text(encoding="utf-8").lstrip()
        except OSError:
            original = "[]"
        return "{}\n" if original.startswith("{") else "[]\n"
    return ""


def build_file_plan():
    """Returns (copy_list, seed_list, skipped_list) without touching disk."""
    all_paths = _git_tracked_and_untracked_files()
    copy_list, seed_list, skipped_list = [], [], []

    for rel in all_paths:
        if _is_excluded(rel):
            skipped_list.append(rel)
            continue

        if rel.startswith("data/knowledge_base/"):
            sub = rel[len("data/knowledge_base/"):]
            top = sub.split("/", 1)[0]
            override = OVERRIDES_DIR / "knowledge_base" / sub
            if override.exists():
                copy_list.append((rel, override))
                continue
            if top in KNOWLEDGE_BASE_SEED_DIRS:
                skipped_list.append(rel)
                continue
            if sub in KNOWLEDGE_BASE_SEED_FILES:
                seed_list.append(rel)
                continue

        if rel == "CLAUDE.md":
            override = OVERRIDES_DIR / "CLAUDE.md"
            if override.exists():
                copy_list.append((rel, override))
            else:
                seed_list.append(rel)
            continue

        if rel == ".dockerignore":
            override = OVERRIDES_DIR / ".dockerignore"
            copy_list.append((rel, override if override.exists() else REPO_ROOT / rel))
            continue

        copy_list.append((rel, REPO_ROOT / rel))

    # No root README.md exists today, so the git-file walk above never picks
    # one up — add the template's README unconditionally.
    readme_override = OVERRIDES_DIR / "README.md"
    if readme_override.exists():
        copy_list.append(("README.md", readme_override))

    return copy_list, seed_list, skipped_list


def write_package(output_dir: Path, copy_list, seed_list):
    for rel, src in copy_list:
        dest = output_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)

    for rel in seed_list:
        dest = output_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel == "CLAUDE.md":
            dest.write_text(
                "# Etsy Automation Hub\n\n"
                "_This is a generic template instance. Replace this file with your own "
                "business doctrine — see CLAUDE.md in the source repo for the structure "
                "to follow (mission statement, quality gates, product catalog, etc.)._\n",
                encoding="utf-8",
            )
        else:
            dest.write_text(_seed_content_for(REPO_ROOT / rel), encoding="utf-8")


def scan_for_secrets(output_dir: Path):
    hits = []
    for path in output_dir.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append((str(path.relative_to(output_dir)), pattern.pattern))
    return hits


def make_zip(output_dir: Path, zip_path: Path):
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(output_dir))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "dist" / "etsy-hub-template.zip",
                         help="Path to the output zip (default: dist/etsy-hub-template.zip)")
    parser.add_argument("--dry-run", action="store_true",
                         help="Report what would be included/seeded/skipped without writing anything")
    parser.add_argument("--keep-temp", action="store_true",
                         help="Don't delete the staging directory after building (for inspection)")
    args = parser.parse_args()

    copy_list, seed_list, skipped_list = build_file_plan()

    print(f"Files to copy as-is:     {len(copy_list)}")
    print(f"Files reset to seed:     {len(seed_list)}")
    print(f"Business-IP files/dirs skipped: {len(skipped_list)}")

    if args.dry_run:
        print("\n--- seeded (would reset to empty template) ---")
        for rel in seed_list:
            print(f"  {rel}")
        print("\n--- skipped (business IP, excluded entirely) ---")
        for rel in sorted(skipped_list)[:40]:
            print(f"  {rel}")
        if len(skipped_list) > 40:
            print(f"  ... and {len(skipped_list) - 40} more")
        return 0

    staging = Path(tempfile.mkdtemp(prefix="etsy_hub_template_"))
    try:
        write_package(staging, copy_list, seed_list)

        secret_hits = scan_for_secrets(staging)
        if secret_hits:
            print("\nABORTED — possible secrets found in packaged output:", file=sys.stderr)
            for rel, pattern in secret_hits:
                print(f"  {rel}  (matched: {pattern})", file=sys.stderr)
            return 1

        make_zip(staging, args.output)
        print(f"\nTemplate package written to: {args.output}")
        return 0
    finally:
        if args.keep_temp:
            print(f"Staging directory kept at: {staging}")
        else:
            shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
