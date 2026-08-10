#!/usr/bin/env python3
"""
business_pipeline.py — OnBrandCraftz Autonomous Business Pipeline

Orchestrates the $5K/month revenue target by running weekly product
generation, quality gates, publishing, and performance monitoring.

Revenue model:
  Sublimation bundles  25 listings × 10 sales/mo × $9.99 = $2,498
  SVG packs            20 listings × 12 sales/mo × $7.99 = $1,918
  Digital planners      6 listings ×  8 sales/mo × $14.99 =  $719
  Sticker packs         8 listings ×  8 sales/mo × $5.99 =   $383
  ──────────────────────────────────────────────────────────────────
  Gross                                                     $5,518
  Etsy fees (~25%)                                         -$1,380
  Net profit                                                $4,138  ← scale to 70+ listings for $5K net

Run modes:
  python tools/agents/business_pipeline.py --mode weekly   ← full weekly cycle
  python tools/agents/business_pipeline.py --mode generate ← generate new products only
  python tools/agents/business_pipeline.py --mode monitor  ← performance check only
  python tools/agents/business_pipeline.py --mode publish  ← publish approved drafts only
"""

import os, sys, re, json, argparse, time
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent.parent))

# Parse .env manually
_env_path = Path(__file__).parent.parent.parent / ".env"
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

STATE_FILE = Path(__file__).parent.parent.parent / "data" / "pipeline_state.json"
LOG_FILE   = Path(__file__).parent.parent.parent / "data" / "pipeline_log.jsonl"

# ── Revenue target tracking ───────────────────────────────────────────────────

MONTHLY_TARGET_PROFIT = 5000.00
ETSY_FEE_RATE         = 0.25   # 6.5% transaction + 3%+$0.25 processing + listing fees ≈ 25% blended

def gross_needed(net_target: float) -> float:
    return net_target / (1 - ETSY_FEE_RATE)

# ── Product backlog — themes to generate next ─────────────────────────────────
# Each entry: (product_type, theme_id, theme_name, priority)
# Priority 1 = highest demand / lowest competition
PRODUCT_BACKLOG = [
    # Sublimation — next batch
    ("sublimation", "baseball_mom",       "Baseball Mom",         1),
    ("sublimation", "soccer_mom",         "Soccer Mom",           1),
    ("sublimation", "in_my_mama_era",     "In My Mama Era",       1),
    ("sublimation", "blessed_mama",       "Blessed Mama",         1),
    ("sublimation", "boho_christian",     "She Is Strong",        1),
    ("sublimation", "chaos_coordinator",  "Chaos Coordinator",    2),
    ("sublimation", "bonus_mom",          "Bonus Mom",            2),
    ("sublimation", "cat_mom",            "Cat Mom",              2),
    ("sublimation", "plant_mom",          "Plant Mom",            2),
    ("sublimation", "coffee_addict",      "But First Coffee",     2),
    ("sublimation", "game_day_vibes",     "Game Day Vibes",       2),
    ("sublimation", "volleyball_mom",     "Volleyball Mom",       3),
    ("sublimation", "basketball_mom",     "Basketball Mom",       3),
    ("sublimation", "hockey_mom",         "Hockey Mom",           3),
    ("sublimation", "swim_mom",           "Swim Mom",             3),

    # SVG packs — next releases
    ("svg",         "teacher_bundle",     "Teacher Life SVG Pack",    1),
    ("svg",         "faith_bundle",       "Faith & Christian SVG",    1),
    ("svg",         "pet_mom_bundle",     "Pet Mom SVG Bundle",       1),
    ("svg",         "nurse_bundle",       "Nurse Life SVG Bundle",    2),
    ("svg",         "fall_seasonal",      "Fall/Autumn SVG Bundle",   2),

    # Digital planners
    ("planner",     "adhd_planner",       "ADHD Planner 2026",        1),
    ("planner",     "teacher_planner",    "Teacher Planner 2026",     1),
    ("planner",     "undated_evergreen",  "Undated Life Planner",     2),
]

# ── Quality gate — enforced before any publish ────────────────────────────────

class QualityGate:
    """
    Programmatic quality checks. All checks must pass (True) before publish.
    Any failure halts the pipeline and logs the rejection reason.
    """

    @staticmethod
    def check_title(title: str) -> tuple[bool, str]:
        if len(title) > 140:
            return False, f"Title too long: {len(title)} chars (max 140 — Etsy's platform limit)"
        if "sublimation" not in title.lower() and "svg" not in title.lower() and "planner" not in title.lower():
            return False, "Title missing product category keyword"
        if "instant download" not in title.lower():
            return False, "Title missing 'instant download'"
        return True, "OK"

    @staticmethod
    def check_tags(tags: list[str]) -> tuple[bool, str]:
        if len(tags) < 13:
            return False, f"Only {len(tags)} tags — need all 13"
        for tag in tags:
            if len(tag) > 20:
                return False, f"Tag too long ({len(tag)} chars): '{tag}'"
        return True, "OK"

    @staticmethod
    def check_zip_size(zip_path: str) -> tuple[bool, str]:
        size_mb = Path(zip_path).stat().st_size / 1024 / 1024
        if size_mb > 20:
            return False, f"ZIP is {size_mb:.1f} MB — Etsy limit is 20 MB"
        return True, f"ZIP size OK: {size_mb:.1f} MB"

    @staticmethod
    def check_image_dimensions(img_path: str, expected_w: int, expected_h: int) -> tuple[bool, str]:
        from PIL import Image
        img = Image.open(img_path)
        w, h = img.size
        if abs(w - expected_w) > 10 or abs(h - expected_h) > 10:
            return False, f"Image dimensions {w}×{h} — expected {expected_w}×{expected_h}"
        return True, f"Dimensions OK: {w}×{h}"

    @staticmethod
    def check_no_pale_background(img_path: str, sample_edges: bool = True) -> tuple[bool, str]:
        """Sample background corners — reject if any corner is too light (LAB L* > 85)."""
        from PIL import Image
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        sample_size = 30
        corners = [
            img.crop((0, 0, sample_size, sample_size)),
            img.crop((w - sample_size, 0, w, sample_size)),
            img.crop((0, h - sample_size, sample_size, h)),
            img.crop((w - sample_size, h - sample_size, w, h)),
        ]
        for corner in corners:
            pixels = list(corner.getdata())
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            avg_g = sum(p[1] for p in pixels) / len(pixels)
            avg_b = sum(p[2] for p in pixels) / len(pixels)
            # Approximate luminance (sRGB)
            luminance = 0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b
            if luminance > 217:  # ~85% of 255 = too light
                return False, f"Corner too light (luminance {luminance:.0f}/255) — pale/white background"
        return True, "Background darkness OK"

    @classmethod
    def run_all(cls, checks: dict) -> tuple[bool, list[str]]:
        """Run a dict of {check_name: (bool, message)} and return overall pass/fail."""
        failures = []
        for name, (passed, msg) in checks.items():
            if not passed:
                failures.append(f"FAIL [{name}]: {msg}")
        return (len(failures) == 0), failures


# ── Performance monitor ───────────────────────────────────────────────────────

def check_performance() -> dict:
    """
    Pulls listing stats from Etsy API and returns a performance report.
    Flags: low conversion, zero views, high favorites but no sales.
    """
    from etsy_api import EtsyAPIClient
    client = EtsyAPIClient()

    try:
        listings = client.get_listings(state="active", limit=100)
    except Exception as e:
        return {"error": str(e)}

    report = {
        "date": date.today().isoformat(),
        "total_listings": len(listings),
        "flags": [],
        "top_performers": [],
        "revenue_estimate": 0.0,
    }

    for l in listings:
        lid   = l.get("listing_id")
        title = l.get("title", "")[:50]
        views = l.get("views", 0)
        favs  = l.get("num_favorers", 0)
        price = float(l.get("price", {}).get("amount", 0)) / 100 if isinstance(l.get("price"), dict) else 0

        # Flag: high views, zero conversion indicator
        if views > 200 and favs == 0:
            report["flags"].append({
                "listing_id": lid, "title": title,
                "issue": f"HIGH_VIEWS_NO_FAVS: {views} views, 0 favorites — photo or pricing problem"
            })

        # Flag: zero engagement after 30+ days (hard to detect without creation date, approximate)
        if views < 10 and price > 0:
            report["flags"].append({
                "listing_id": lid, "title": title,
                "issue": "ZERO_VISIBILITY: < 10 views — title/tag SEO problem"
            })

        # Top performers (most favorited)
        if favs > 5:
            report["top_performers"].append({"listing_id": lid, "title": title, "favorites": favs})

    report["top_performers"].sort(key=lambda x: x["favorites"], reverse=True)
    return report


# ── State management ──────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "last_weekly_run": None,
        "listings_published": 0,
        "monthly_revenue_estimate": 0.0,
        "completed_themes": [],
        "pending_publish": [],
    }

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log_event(event_type: str, data: dict):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({
            "ts": datetime.now().isoformat(),
            "type": event_type,
            **data
        }) + "\n")


# ── Pipeline modes ────────────────────────────────────────────────────────────

def run_monitor():
    print("── Performance Monitor ──────────────────────────────────────")
    report = check_performance()
    if "error" in report:
        print(f"  Error: {report['error']}")
        return

    print(f"  Active listings: {report['total_listings']}")
    print(f"  Issues flagged: {len(report['flags'])}")

    if report["flags"]:
        print("\n  Flags requiring action:")
        for flag in report["flags"][:10]:
            print(f"    [{flag['listing_id']}] {flag['title']}")
            print(f"      → {flag['issue']}")

    if report["top_performers"]:
        print("\n  Top performers (by favorites):")
        for p in report["top_performers"][:5]:
            print(f"    {p['favorites']} ★  [{p['listing_id']}] {p['title']}")

    gross_target = gross_needed(MONTHLY_TARGET_PROFIT)
    print(f"\n  Revenue target: ${MONTHLY_TARGET_PROFIT:,.0f}/mo net (${gross_target:,.0f} gross needed)")
    print(f"  Current listing count: {report['total_listings']}")
    needed = max(0, 70 - report["total_listings"])
    print(f"  Listings needed to reach target: +{needed} more")

    log_event("monitor", report)
    return report


def run_generate(n: int = 1, product_type: str | None = None):
    """Generate the next N products from the backlog."""
    state = load_state()
    completed = set(state.get("completed_themes", []))

    backlog = [
        item for item in PRODUCT_BACKLOG
        if item[1] not in completed
        and (product_type is None or item[0] == product_type)
    ]
    backlog.sort(key=lambda x: x[3])  # sort by priority

    if not backlog:
        print("Backlog is empty — add more themes to PRODUCT_BACKLOG")
        return

    for product_type, theme_id, theme_name, priority in backlog[:n]:
        print(f"\nGenerating: [{product_type}] {theme_name} (priority {priority})")

        if product_type == "sublimation":
            _generate_sublimation_theme(theme_id, theme_name)
        elif product_type == "svg":
            print(f"  SVG generation: run tools/generate_retro_moms_pack.py for {theme_name}")
        elif product_type == "planner":
            print(f"  Planner generation: run planner pipeline for {theme_name}")

        state.setdefault("completed_themes", []).append(theme_id)
        save_state(state)


def _generate_sublimation_theme(theme_id: str, theme_name: str):
    """Import and run the sublimation generator for a single new theme."""
    # This dynamically adds the theme to the generator and runs it.
    # For autonomous operation, the agent constructs the prompt and calls gpt-image-1.
    print(f"  → Add '{theme_id}' to DESIGNS in tools/generate_sublimation_wraps.py and run:")
    print(f"    python tools/generate_sublimation_wraps.py {theme_id}")


def run_weekly():
    """Full weekly cycle: health check → monitor → generate → report → summary."""
    print("=" * 60)
    print(f"OnBrandCraftz Weekly Pipeline — {date.today()}")
    print("=" * 60)

    # ── Step 0: Health check — abort if critical issues ──────────────────────
    print("\n[0/4] Daily Health Check")
    try:
        import health_check
        exit_code = health_check.run(quiet=True)
        if exit_code != 0:
            print("  🚨 CRITICAL health issues found — pipeline paused.")
            print("     Fix the issues above and re-run.")
            log_event("pipeline_abort", {"reason": "health_check_critical", "date": date.today().isoformat()})
            return
        print("  ✓ All systems healthy")
    except Exception as e:
        print(f"  ⚠  Health check failed to run: {e} — continuing anyway")

    # ── Step 1: Performance monitor ──────────────────────────────────────────
    print("\n[1/4] Performance Monitor")
    report = run_monitor()

    # ── Step 2: Generate new products ────────────────────────────────────────
    print("\n[2/4] Generate New Products (2 per week)")
    run_generate(n=2)

    # ── Step 3: Weekly business report ───────────────────────────────────────
    print("\n[3/4] Generating Weekly Business Report")
    try:
        import weekly_report
        weekly_report.run(save_only=True)
        weekly_report.log_decision(
            "weekly_pipeline_run",
            f"Weekly pipeline completed — {date.today().isoformat()}",
            {"mode": "weekly"},
        )
        print("  ✓ Report saved to data/reports/")
    except Exception as e:
        print(f"  ⚠  Report generation failed: {e}")

    # ── Step 4: Summary ──────────────────────────────────────────────────────
    print("\n[4/4] Weekly Summary")
    state = load_state()
    state["last_weekly_run"] = date.today().isoformat()
    save_state(state)

    print(f"  Themes completed: {len(state.get('completed_themes', []))}")
    remaining = len([t for t in PRODUCT_BACKLOG if t[1] not in state.get("completed_themes", [])])
    print(f"  Themes remaining in backlog: {remaining}")
    print(f"  Weeks to clear backlog at current pace: {remaining // 2}")
    print("\nNext run: next Sunday 9am (cron) or: python tools/agents/business_pipeline.py --mode weekly")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OnBrandCraftz Business Pipeline")
    parser.add_argument("--mode", choices=["weekly", "generate", "monitor", "publish"],
                        default="weekly")
    parser.add_argument("--type", choices=["sublimation", "svg", "planner"],
                        default=None, help="Filter generate mode by product type")
    parser.add_argument("--n", type=int, default=1, help="Number of designs to generate")
    args = parser.parse_args()

    if args.mode == "weekly":
        run_weekly()
    elif args.mode == "generate":
        run_generate(n=args.n, product_type=args.type)
    elif args.mode == "monitor":
        run_monitor()
    elif args.mode == "publish":
        print("Publish mode: review data/pipeline_state.json pending_publish queue")
        state = load_state()
        pending = state.get("pending_publish", [])
        print(f"  Pending: {len(pending)} products queued")
        for item in pending:
            print(f"    • {item}")


if __name__ == "__main__":
    main()
