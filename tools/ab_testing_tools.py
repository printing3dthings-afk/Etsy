"""
A/B Testing Tools — systematic experimentation for listings, pricing, and photos.

Etsy doesn't have a built-in A/B testing framework, so this module implements
a lightweight manual testing system: create test variants, track performance metrics
per variant over time, and declare a winner based on statistical significance.

What can be A/B tested on Etsy:
  - Listing titles (primary SEO lever)
  - Main photo / thumbnail (biggest impact on click-through rate)
  - Price points (conversion rate vs margin)
  - Description copy and structure
  - Tag sets (for search ranking)
  - Receipt message copy
"""

import json
import math
from datetime import date, timedelta
from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "create_ab_test",
        "description": "Create an A/B test for a listing element (title, photo, price, description, tags).",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Etsy listing ID being tested"},
                "test_name": {"type": "string", "description": "Descriptive name, e.g. 'Black shelf title test'"},
                "element": {
                    "type": "string",
                    "enum": ["title", "main_photo", "price", "description", "tags", "receipt_message"],
                    "description": "Which listing element is being tested",
                },
                "variant_a": {
                    "type": "object",
                    "description": "Control variant (current version)",
                    "properties": {
                        "label": {"type": "string"},
                        "value": {"type": "string", "description": "The actual content (title text, price, etc.)"},
                    },
                    "required": ["label", "value"],
                },
                "variant_b": {
                    "type": "object",
                    "description": "Test variant (new version to test)",
                    "properties": {
                        "label": {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["label", "value"],
                },
                "duration_days": {
                    "type": "integer",
                    "description": "How many days to run the test (min 14, recommended 28-30)",
                    "default": 28,
                },
                "success_metric": {
                    "type": "string",
                    "enum": ["click_through_rate", "conversion_rate", "revenue", "favorites"],
                    "description": "Primary metric to determine winner",
                    "default": "conversion_rate",
                },
                "hypothesis": {"type": "string", "description": "What you expect and why"},
            },
            "required": ["listing_id", "test_name", "element", "variant_a", "variant_b"],
        },
    },
    {
        "name": "get_active_tests",
        "description": "Get all currently running A/B tests with their status and preliminary results.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "record_variant_metrics",
        "description": "Record performance metrics for a specific variant during the test period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_id": {"type": "string"},
                "variant": {"type": "string", "enum": ["a", "b"], "description": "Which variant to update"},
                "impressions": {"type": "integer", "description": "Number of times listing was shown in search"},
                "clicks": {"type": "integer", "description": "Number of clicks on the listing"},
                "favorites": {"type": "integer", "description": "Number of favorites added"},
                "orders": {"type": "integer", "description": "Number of orders placed"},
                "revenue": {"type": "number", "description": "Total revenue from this variant"},
                "date_recorded": {"type": "string", "description": "YYYY-MM-DD, defaults to today"},
            },
            "required": ["test_id", "variant", "impressions", "clicks"],
        },
    },
    {
        "name": "analyze_test_results",
        "description": "Analyze A/B test results and determine if there is a statistically significant winner.",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_id": {"type": "string"},
            },
            "required": ["test_id"],
        },
    },
    {
        "name": "declare_winner",
        "description": "Declare a winner for a completed A/B test and record the decision.",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_id": {"type": "string"},
                "winner": {"type": "string", "enum": ["a", "b", "no_winner"], "description": "Which variant won"},
                "action_taken": {"type": "string", "description": "What change was made based on the result"},
            },
            "required": ["test_id", "winner"],
        },
    },
    {
        "name": "get_test_history",
        "description": "Get all completed A/B tests with winners and learnings.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "generate_test_ideas",
        "description": "Generate A/B test ideas for a listing based on its current performance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string"},
                "current_ctr": {"type": "number", "description": "Current click-through rate (0-100)"},
                "current_conversion": {"type": "number", "description": "Current conversion rate (0-100)"},
                "current_favorites": {"type": "integer"},
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "get_testing_calendar",
        "description": "Get a recommended A/B testing calendar with what to test and when.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "create_ab_test":
        return _create_ab_test(tool_input, store)
    if tool_name == "get_active_tests":
        return _get_active_tests(store)
    if tool_name == "record_variant_metrics":
        return _record_variant_metrics(tool_input, store)
    if tool_name == "analyze_test_results":
        return _analyze_test_results(tool_input["test_id"], store)
    if tool_name == "declare_winner":
        return _declare_winner(tool_input, store)
    if tool_name == "get_test_history":
        return _get_test_history(store)
    if tool_name == "generate_test_ideas":
        return _generate_test_ideas(tool_input, store)
    if tool_name == "get_testing_calendar":
        return _get_testing_calendar(store)
    return f"Unknown A/B testing tool: {tool_name}"


def _create_ab_test(data: dict, store: DataStore) -> str:
    tests = store.get("ab_tests", default=[])
    test_id = f"ABT{len(tests) + 1:04d}"
    duration = data.get("duration_days", 28)
    end_date = str(date.today() + timedelta(days=duration))

    if duration < 14:
        return json.dumps({"error": "Minimum test duration is 14 days. Etsy traffic needs time to produce reliable data."})

    test = {
        "id": test_id,
        "listing_id": data["listing_id"],
        "test_name": data["test_name"],
        "element": data["element"],
        "hypothesis": data.get("hypothesis", ""),
        "success_metric": data.get("success_metric", "conversion_rate"),
        "duration_days": duration,
        "start_date": str(date.today()),
        "end_date": end_date,
        "status": "active",
        "variant_a": {
            "label": data["variant_a"]["label"],
            "value": data["variant_a"]["value"],
            "impressions": 0,
            "clicks": 0,
            "favorites": 0,
            "orders": 0,
            "revenue": 0.0,
            "daily_log": [],
        },
        "variant_b": {
            "label": data["variant_b"]["label"],
            "value": data["variant_b"]["value"],
            "impressions": 0,
            "clicks": 0,
            "favorites": 0,
            "orders": 0,
            "revenue": 0.0,
            "daily_log": [],
        },
        "winner": None,
        "created_at": str(date.today()),
    }
    tests.append(test)
    store.set(tests, "ab_tests")
    store.save()

    return json.dumps({
        "success": True,
        "test_id": test_id,
        "test_name": data["test_name"],
        "element": data["element"],
        "variant_a": data["variant_a"]["label"],
        "variant_b": data["variant_b"]["label"],
        "end_date": end_date,
        "success_metric": data.get("success_metric", "conversion_rate"),
        "instructions": (
            f"Run this test until {end_date}. "
            "Check Etsy Shop Stats weekly and log metrics with record_variant_metrics. "
            "Switch to variant B on your listing manually to split-test (alternate weekly). "
            "Do not change any other listing element during the test."
        ),
    }, indent=2)


def _get_active_tests(store: DataStore) -> str:
    tests = store.get("ab_tests", default=[])
    active = [t for t in tests if t.get("status") == "active"]
    today = date.today()

    for t in active:
        try:
            end = date.fromisoformat(t["end_date"])
        except (ValueError, KeyError):
            end = today
        days_remaining = (end - today).days
        t["days_remaining"] = days_remaining
        if days_remaining < 0:
            t["status_note"] = "OVERDUE — ready to analyze and declare winner"
        elif days_remaining <= 7:
            t["status_note"] = f"Ending soon ({days_remaining} days)"
        else:
            t["status_note"] = f"Running ({days_remaining} days left)"

    return json.dumps({
        "active_tests": active,
        "count": len(active),
        "tip": "Use record_variant_metrics to log weekly stats from Etsy Shop Stats.",
    }, indent=2)


def _record_variant_metrics(data: dict, store: DataStore) -> str:
    tests = store.get("ab_tests", default=[])
    test = next((t for t in tests if t["id"] == data["test_id"]), None)
    if not test:
        return json.dumps({"error": f"Test {data['test_id']} not found."})

    variant_key = f"variant_{data['variant']}"
    variant = test.get(variant_key)
    if not variant:
        return json.dumps({"error": f"Variant '{data['variant']}' not found in test."})

    variant["impressions"] += data.get("impressions", 0)
    variant["clicks"] += data.get("clicks", 0)
    variant["favorites"] += data.get("favorites", 0)
    variant["orders"] += data.get("orders", 0)
    variant["revenue"] += data.get("revenue", 0.0)

    log_entry = {
        "date": data.get("date_recorded", str(date.today())),
        "impressions": data.get("impressions", 0),
        "clicks": data.get("clicks", 0),
        "favorites": data.get("favorites", 0),
        "orders": data.get("orders", 0),
        "revenue": data.get("revenue", 0.0),
    }
    variant.setdefault("daily_log", []).append(log_entry)

    store.set(tests, "ab_tests")
    store.save()

    ctr = round(variant["clicks"] / variant["impressions"] * 100, 2) if variant["impressions"] else 0
    conv = round(variant["orders"] / variant["clicks"] * 100, 2) if variant["clicks"] else 0

    return json.dumps({
        "success": True,
        "test_id": data["test_id"],
        "variant": data["variant"],
        "cumulative": {
            "impressions": variant["impressions"],
            "clicks": variant["clicks"],
            "click_through_rate_pct": ctr,
            "orders": variant["orders"],
            "conversion_rate_pct": conv,
            "revenue": round(variant["revenue"], 2),
        },
    }, indent=2)


def _analyze_test_results(test_id: str, store: DataStore) -> str:
    tests = store.get("ab_tests", default=[])
    test = next((t for t in tests if t["id"] == test_id), None)
    if not test:
        return json.dumps({"error": f"Test {test_id} not found."})

    va = test["variant_a"]
    vb = test["variant_b"]

    def safe_rate(num, den):
        return num / den if den > 0 else 0.0

    # Compute per-variant rates
    ctr_a = safe_rate(va["clicks"], va["impressions"])
    ctr_b = safe_rate(vb["clicks"], vb["impressions"])
    conv_a = safe_rate(va["orders"], va["clicks"])
    conv_b = safe_rate(vb["orders"], vb["clicks"])
    rev_per_imp_a = safe_rate(va["revenue"], va["impressions"])
    rev_per_imp_b = safe_rate(vb["revenue"], vb["impressions"])
    fav_rate_a = safe_rate(va["favorites"], va["impressions"])
    fav_rate_b = safe_rate(vb["favorites"], vb["impressions"])

    metric = test.get("success_metric", "conversion_rate")
    metric_map = {
        "click_through_rate": (ctr_a, ctr_b),
        "conversion_rate": (conv_a, conv_b),
        "revenue": (rev_per_imp_a, rev_per_imp_b),
        "favorites": (fav_rate_a, fav_rate_b),
    }
    score_a, score_b = metric_map.get(metric, (conv_a, conv_b))

    lift = round((score_b - score_a) / score_a * 100, 1) if score_a > 0 else None

    # Simple z-test approximation for proportions (CTR/conversion)
    confidence = None
    if metric in ("click_through_rate", "conversion_rate", "favorites"):
        n_a = va["impressions"] if metric in ("click_through_rate", "favorites") else va["clicks"]
        n_b = vb["impressions"] if metric in ("click_through_rate", "favorites") else vb["clicks"]
        _key = "clicks" if metric == "click_through_rate" else ("favorites" if metric == "favorites" else "orders")
        p_pool = safe_rate(va.get(_key, 0) + vb.get(_key, 0), n_a + n_b) if (n_a + n_b) > 0 else 0
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b)) if (n_a > 0 and n_b > 0 and p_pool > 0) else 0
        z = abs(score_b - score_a) / se if se > 0 else 0
        # Approximate confidence from z
        if z >= 2.576:
            confidence = 99
        elif z >= 1.960:
            confidence = 95
        elif z >= 1.645:
            confidence = 90
        elif z >= 1.282:
            confidence = 80
        else:
            confidence = round(z / 1.282 * 80, 0)

    try:
        days_run = (date.today() - date.fromisoformat(test["start_date"])).days
        days_remaining = (date.fromisoformat(test["end_date"]) - date.today()).days
    except (ValueError, KeyError):
        days_run = 0
        days_remaining = 0

    recommendation = "Continue testing — not enough data yet."
    if confidence and confidence >= 95 and score_b > score_a:
        recommendation = f"Variant B is the winner with {confidence}% confidence. Implement B."
    elif confidence and confidence >= 95 and score_a > score_b:
        recommendation = f"Variant A (control) is better with {confidence}% confidence. Keep A."
    elif days_remaining < 0 and confidence and confidence < 80:
        recommendation = "Test has ended without a clear winner. Consider extending or running a new test."
    elif days_remaining < 0:
        recommendation = "Test ended. Declare a winner based on the primary metric direction."

    return json.dumps({
        "test_id": test_id,
        "test_name": test["test_name"],
        "element": test["element"],
        "days_run": days_run,
        "days_remaining": max(0, days_remaining),
        "success_metric": metric,
        "variant_a": {
            "label": va["label"],
            "impressions": va["impressions"],
            "clicks": va["clicks"],
            "ctr_pct": round(ctr_a * 100, 2),
            "orders": va["orders"],
            "conversion_pct": round(conv_a * 100, 2),
            "favorites": va["favorites"],
            "revenue": round(va["revenue"], 2),
        },
        "variant_b": {
            "label": vb["label"],
            "impressions": vb["impressions"],
            "clicks": vb["clicks"],
            "ctr_pct": round(ctr_b * 100, 2),
            "orders": vb["orders"],
            "conversion_pct": round(conv_b * 100, 2),
            "favorites": vb["favorites"],
            "revenue": round(vb["revenue"], 2),
        },
        "lift_pct": lift,
        "confidence_pct": confidence,
        "recommendation": recommendation,
        "minimum_confidence_to_act": 95,
    }, indent=2)


def _declare_winner(data: dict, store: DataStore) -> str:
    tests = store.get("ab_tests", default=[])
    test = next((t for t in tests if t["id"] == data["test_id"]), None)
    if not test:
        return json.dumps({"error": f"Test {data['test_id']} not found."})

    test["status"] = "completed"
    test["winner"] = data["winner"]
    test["action_taken"] = data.get("action_taken", "")
    test["completed_at"] = str(date.today())

    winner_label = "No clear winner"
    if data["winner"] == "a":
        winner_label = test["variant_a"]["label"]
    elif data["winner"] == "b":
        winner_label = test["variant_b"]["label"]

    store.set(tests, "ab_tests")
    store.save()

    return json.dumps({
        "success": True,
        "test_id": data["test_id"],
        "test_name": test["test_name"],
        "winner": data["winner"],
        "winner_label": winner_label,
        "action_taken": data.get("action_taken", ""),
        "learning": f"Test on {test['element']} for listing {test['listing_id']} completed. Winner: {winner_label}.",
    }, indent=2)


def _get_test_history(store: DataStore) -> str:
    tests = store.get("ab_tests", default=[])
    completed = [t for t in tests if t.get("status") == "completed"]
    winners: dict[str, int] = {"a": 0, "b": 0, "no_winner": 0}
    by_element: dict[str, int] = {}
    for t in completed:
        w = t.get("winner", "no_winner")
        winners[w] = winners.get(w, 0) + 1
        el = t.get("element", "unknown")
        by_element[el] = by_element.get(el, 0) + 1

    return json.dumps({
        "completed_tests": completed,
        "count": len(completed),
        "summary": {
            "variant_a_wins": winners.get("a", 0),
            "variant_b_wins": winners.get("b", 0),
            "no_winner": winners.get("no_winner", 0),
            "tests_by_element": by_element,
        },
        "tip": "Review completed tests quarterly to build a knowledge base of what works for your shop.",
    }, indent=2)


def _generate_test_ideas(data: dict, store: DataStore) -> str:
    listing_id = data["listing_id"]
    ctr = data.get("current_ctr", 0)
    conv = data.get("current_conversion", 0)

    ideas = []

    # Low CTR → photo or title issues
    if ctr < 2.0:
        ideas.append({
            "priority": "HIGH",
            "element": "main_photo",
            "idea": "Test a lifestyle photo vs plain product photo as the thumbnail",
            "why": f"CTR of {ctr}% is below the Etsy average of 2-3%. The thumbnail is the #1 driver of clicks.",
            "hypothesis": "A lifestyle photo in context (e.g. shelf styled with books) will outperform a plain white background photo.",
        })
        ideas.append({
            "priority": "HIGH",
            "element": "title",
            "idea": "Test a keyword-led title vs a benefit-led title",
            "why": "CTR improvements often come from matching search intent in the first 3 words of the title.",
            "hypothesis": "Starting with the most searched keyword phrase (e.g. '3D Printed Floating Shelf') vs a branded opener will increase visibility and clicks.",
        })

    # Low conversion → price or description issues
    if conv < 1.5:
        ideas.append({
            "priority": "HIGH",
            "element": "price",
            "idea": "Test current price vs 10% lower price",
            "why": f"Conversion of {conv}% is low. Price sensitivity testing helps find the optimal price point.",
            "hypothesis": "A lower price may increase conversion enough to generate more total revenue despite lower margin per sale.",
        })
        ideas.append({
            "priority": "MEDIUM",
            "element": "description",
            "idea": "Test a short punchy description vs a detailed spec-focused description",
            "why": "Buyers scan, not read. A clear value proposition in the first 3 lines may improve conversion.",
            "hypothesis": "Leading with the top 3 benefits (not features) will convert better than a spec list.",
        })

    # Photo test always worth doing
    if len(ideas) < 3:
        ideas.append({
            "priority": "MEDIUM",
            "element": "main_photo",
            "idea": "Test vertical (portrait) vs square crop for mobile optimisation",
            "why": "Over 70% of Etsy traffic is mobile. Vertical photos take up more screen real estate.",
            "hypothesis": "A taller crop ratio will increase click-through on mobile devices.",
        })

    # Tags always worth testing
    ideas.append({
        "priority": "MEDIUM",
        "element": "tags",
        "idea": "Test long-tail specific tags vs broad category tags",
        "why": "Long-tail tags (e.g. 'floating shelf for succulents') attract buyers with high purchase intent.",
        "hypothesis": "Replacing 3 broad tags with 3 specific long-tail alternatives will improve conversion rate from search.",
    })

    return json.dumps({
        "listing_id": listing_id,
        "current_metrics": {
            "ctr_pct": ctr,
            "conversion_pct": conv,
            "favorites": data.get("current_favorites", 0),
        },
        "test_ideas": ideas,
        "recommended_order": "Start with the HIGH priority test. Run one test at a time per listing.",
        "note": "Never change more than one element at a time — you won't know which change caused the result.",
    }, indent=2)


def _get_testing_calendar(store: DataStore) -> str:
    today = date.today()
    month = today.strftime("%B %Y")

    calendar = [
        {
            "week": 1,
            "focus": "Title testing",
            "description": "Test keyword-led vs benefit-led titles on your top 3 listings",
            "duration": "28 days",
            "metric": "click_through_rate",
        },
        {
            "week": 5,
            "focus": "Photo testing",
            "description": "Test lifestyle photos vs product-on-white for your top sellers",
            "duration": "28 days",
            "metric": "click_through_rate",
        },
        {
            "week": 9,
            "focus": "Price testing",
            "description": "Test current price vs ±10% on mid-tier listings",
            "duration": "28 days",
            "metric": "revenue",
        },
        {
            "week": 13,
            "focus": "Description testing",
            "description": "Test short punchy vs detailed spec descriptions",
            "duration": "28 days",
            "metric": "conversion_rate",
        },
        {
            "week": 17,
            "focus": "Tag testing",
            "description": "Test long-tail vs broad tags across all active listings",
            "duration": "28 days",
            "metric": "click_through_rate",
        },
        {
            "week": 21,
            "focus": "Receipt message testing",
            "description": "Test different coupon amounts or CTAs in receipt message",
            "duration": "28 days",
            "metric": "conversion_rate",
        },
    ]

    active_tests = [t for t in store.get("ab_tests", default=[]) if t.get("status") == "active"]

    return json.dumps({
        "current_month": month,
        "active_tests_count": len(active_tests),
        "recommended_calendar": calendar,
        "rules": [
            "Run only ONE test per listing at a time",
            "Minimum 14 days per test (28 days preferred for statistical significance)",
            "Need 95% confidence before acting on results",
            "Log weekly metrics every Monday from Etsy Shop Stats",
            "Avoid testing during major holidays when traffic patterns are abnormal",
        ],
        "etsy_stats_path": "Shop Manager → Stats → Listings → select listing → view impressions, clicks, conversions",
    }, indent=2)
