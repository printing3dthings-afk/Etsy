"""
Build script: rebuild DP1026 + create DP1027/DP1028/DP1029.
Run from the /home/user/Etsy directory.
"""
import os, sys, json
from datetime import date

# Load .env
with open(os.path.join(os.path.dirname(__file__), ".env")) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(__file__))
from tools.data_store import DataStore
from tools.art_creation_tools import _create_digital_planner, PRODUCT_FILES_DIR

store = DataStore()

KAWAII_COVER = os.path.join(PRODUCT_FILES_DIR, "DP1026_kawaii_cover.jpg")

def get_or_create_product(pid, title, product_type="digital_planner"):
    products = store.get("digital_products", default=[])
    for p in products:
        if p.get("id") == pid:
            return p
    product = {
        "id": pid,
        "title": title,
        "product_type": product_type,
        "art_style": "kawaii digital planner",
        "concept": title,
        "target_audience": "planner enthusiasts",
        "dimensions": "letter PDF",
        "price": 12.99,
        "status": "concept",
        "file_path": None,
        "file_format": None,
        "file_size_kb": None,
        "qc_status": None,
        "qc_notes": None,
        "etsy_listing_id": None,
        "created_at": str(date.today()),
        "updated_at": str(date.today()),
    }
    products.append(product)
    store.set(products, "digital_products")
    store.save()
    print(f"  Created product record: {pid}")
    return product


def build(data):
    pid = data["product_id"]
    print(f"\n{'='*60}")
    print(f"Building {pid}: {data['planner_title']}")
    print(f"{'='*60}")
    result_json = _create_digital_planner(data, store)
    result = json.loads(result_json)
    if result.get("success"):
        print(f"  ✓ {result['pages']} pages | {result['file_size_kb']}KB | {result['color_scheme']}")
        print(f"  → {result['file_path']}")
    else:
        print(f"  ✗ ERROR: {result}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# DP1026 — Ultimate Digital Life Planner (rebuild with kawaii cover + 3 sticker sheets)
# ─────────────────────────────────────────────────────────────────────────────
get_or_create_product("DP1026", "Ultimate Digital Life Planner Bundle — Lavender Dreams")
build({
    "product_id":       "DP1026",
    "planner_title":    "Ultimate Digital Life Planner",
    "subtitle":         "Fillable PDF · GoodNotes · Notability · Xodo",
    "color_scheme":     "lavender_dreams",
    "planner_tier":     3,
    "interactive":      True,
    "include_sections": ["monthly", "monthly_review", "month_at_a_glance",
                         "weekly", "habit_tracker", "goals", "budget", "meal_plan", "notes"],
    "cover_image_path": KAWAII_COVER if os.path.exists(KAWAII_COVER) else "",
    "full_page_cover":  True,
    "year":             2026,
})

# ─────────────────────────────────────────────────────────────────────────────
# DP1027 — Student / School Planner
# ─────────────────────────────────────────────────────────────────────────────
get_or_create_product("DP1027", "Student & School Planner 2026 — Kawaii Academic Organizer")
build({
    "product_id":       "DP1027",
    "planner_title":    "Student Planner 2026",
    "subtitle":         "Academic · Study · School · GoodNotes · Notability",
    "color_scheme":     "cotton_candy",
    "planner_tier":     3,
    "interactive":      True,
    "include_sections": ["monthly", "monthly_review", "weekly",
                         "habit_tracker", "goals", "notes"],
    "year":             2026,
})

# ─────────────────────────────────────────────────────────────────────────────
# DP1028 — Budget / Finance Planner
# ─────────────────────────────────────────────────────────────────────────────
get_or_create_product("DP1028", "Budget & Finance Planner 2026 — Money Management Organizer")
build({
    "product_id":       "DP1028",
    "planner_title":    "Budget & Finance Planner 2026",
    "subtitle":         "Monthly Budget · Bill Tracker · Savings Goals · Net Worth",
    "color_scheme":     "midnight_blue",
    "planner_tier":     3,
    "interactive":      True,
    "include_sections": ["monthly", "monthly_review", "month_at_a_glance",
                         "weekly", "budget", "goals", "notes"],
    "year":             2026,
})

# ─────────────────────────────────────────────────────────────────────────────
# DP1029 — Fitness / Wellness Planner
# ─────────────────────────────────────────────────────────────────────────────
get_or_create_product("DP1029", "Fitness & Wellness Planner 2026 — Health & Habit Tracker")
build({
    "product_id":       "DP1029",
    "planner_title":    "Fitness & Wellness Planner 2026",
    "subtitle":         "Workout Log · Meal Plan · Habit Tracker · Mindfulness",
    "color_scheme":     "coral_peach",
    "planner_tier":     3,
    "interactive":      True,
    "include_sections": ["monthly", "monthly_review", "weekly",
                         "habit_tracker", "meal_plan", "goals", "notes"],
    "year":             2026,
})

print("\n\nAll planners built successfully!")

# ─────────────────────────────────────────────────────────────────────────────
# UNDATED (EVERGREEN) VERSIONS — year=0 produces perpetual planners
# ─────────────────────────────────────────────────────────────────────────────
print("\n\n--- Building undated evergreen versions ---\n")

get_or_create_product("DP1026U", "Ultimate Digital Life Planner — Undated (Lavender Dreams)")
build({
    "product_id":       "DP1026U",
    "planner_title":    "Ultimate Digital Life Planner",
    "subtitle":         "Undated · Fillable PDF · GoodNotes · Notability · Xodo",
    "color_scheme":     "lavender_dreams",
    "planner_tier":     3,
    "interactive":      True,
    "include_sections": ["monthly", "monthly_review", "month_at_a_glance",
                         "weekly", "habit_tracker", "goals", "budget", "meal_plan", "notes"],
    "year":             0,
})

get_or_create_product("DP1027U", "Student Planner Undated — Kawaii Academic Organizer")
build({
    "product_id":       "DP1027U",
    "planner_title":    "Student Planner",
    "subtitle":         "Undated · Academic · Study · School · GoodNotes · Notability",
    "color_scheme":     "cotton_candy",
    "planner_tier":     3,
    "interactive":      True,
    "include_sections": ["monthly", "monthly_review", "weekly",
                         "habit_tracker", "goals", "notes"],
    "year":             0,
})

get_or_create_product("DP1028U", "Budget & Finance Planner Undated — Money Management Organizer")
build({
    "product_id":       "DP1028U",
    "planner_title":    "Budget & Finance Planner",
    "subtitle":         "Undated · Monthly Budget · Bill Tracker · Savings Goals",
    "color_scheme":     "midnight_blue",
    "planner_tier":     3,
    "interactive":      True,
    "include_sections": ["monthly", "monthly_review", "month_at_a_glance",
                         "weekly", "budget", "goals", "notes"],
    "year":             0,
})

get_or_create_product("DP1029U", "Fitness & Wellness Planner Undated — Health & Habit Tracker")
build({
    "product_id":       "DP1029U",
    "planner_title":    "Fitness & Wellness Planner",
    "subtitle":         "Undated · Workout Log · Meal Plan · Habit Tracker · Mindfulness",
    "color_scheme":     "coral_peach",
    "planner_tier":     3,
    "interactive":      True,
    "include_sections": ["monthly", "monthly_review", "weekly",
                         "habit_tracker", "meal_plan", "goals", "notes"],
    "year":             0,
})

print("\n\nAll undated versions built successfully!")
