"""
Financial & Accounting Tools — tracks real profit, Etsy fees, COGS, and P&L.

Etsy fee structure (2026 rates):
  Listing fee:          $0.20 per listing per sale (auto-renewal)
  Transaction fee:      6.5% of (item price + shipping charged)
  Payment processing:   3% + $0.25 per transaction
  Offsite Ads:          15% (optional, shops < $10k/yr TTM revenue)
                        12% (mandatory, shops >= $10k/yr TTM revenue)

Margin benchmarks by product type (from industry research):
  Digital planners/stickers/wall art:  target 70-90%, alert < 65%
  3D printed items:                    target 45-60%, alert < 35%
  Hand-painted wood:                   target 40-55%, alert < 30%
  Blended shop target:                 55-70%+
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

from tools.data_store import DataStore

# ── Etsy fee constants ─────────────────────────────────────────────────────────
ETSY_LISTING_FEE = 0.20
ETSY_TRANSACTION_FEE_PCT = 0.065
ETSY_PAYMENT_PROCESSING_PCT = 0.030
ETSY_PAYMENT_PROCESSING_FLAT = 0.25
ETSY_OFFSITE_ADS_PCT_LOW = 0.15    # < $10k/yr — optional
ETSY_OFFSITE_ADS_PCT_HIGH = 0.12   # >= $10k/yr — mandatory
ETSY_OFFSITE_ADS_THRESHOLD = 10_000
ETSY_OFFSITE_ADS_WARNING = 8_000   # warn 2 months before threshold

# ── Tax constants (2026) ───────────────────────────────────────────────────────
SE_TAX_RATE = 0.153          # self-employment tax on net SE income
TAX_SETASIDE_PCT = 0.28      # recommended combined SE + income tax set-aside
IRS_MILEAGE_2026 = 0.725     # $/mile

# Quarterly estimated tax deadlines (2026 tax year)
QUARTERLY_DEADLINES = [
    ("Q1 (Jan–Mar)", date(2026, 4, 15)),
    ("Q2 (Apr–May)", date(2026, 6, 16)),
    ("Q3 (Jun–Aug)", date(2026, 9, 15)),
    ("Q4 (Sep–Dec)", date(2027, 1, 15)),
]

# ── Margin alert thresholds by product type ────────────────────────────────────
MARGIN_TARGETS = {
    "digital":  {"target": 75, "warn": 65, "critical": 50},
    "physical": {"target": 50, "warn": 35, "critical": 25},
    "3d_print": {"target": 50, "warn": 35, "critical": 25},
    "wood":     {"target": 47, "warn": 30, "critical": 20},
}

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_profit_report",
        "description": "Calculate net profit for a period after all Etsy fees and COGS. Includes AOV and per-category breakdown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "this_week", "this_month", "this_year", "all_time"],
                }
            },
            "required": ["period"],
        },
    },
    {
        "name": "calculate_etsy_fees",
        "description": "Calculate the exact Etsy fee stack for a given sale. Applies correct 12%/15% offsite ads rate based on shop annual revenue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_price": {"type": "number"},
                "shipping_charged": {"type": "number", "default": 0},
                "offsite_ads_sale": {"type": "boolean", "description": "Was this sale from an Offsite Ad?", "default": False},
            },
            "required": ["item_price"],
        },
    },
    {
        "name": "calculate_price_from_target_net",
        "description": "Work backwards from a desired net profit to find the required listing price, accounting for all Etsy fees. Use this to price new products correctly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_net": {"type": "number", "description": "The net amount you want after all Etsy fees (before COGS)"},
                "shipping_charged": {"type": "number", "default": 0},
                "assume_offsite_ads": {"type": "boolean", "description": "Include worst-case 15% offsite ads in the calculation", "default": True},
            },
            "required": ["target_net"],
        },
    },
    {
        "name": "calculate_cogs",
        "description": "Calculate cost of goods sold for a physical product (filament weight, electricity, labour, paint).",
        "input_schema": {
            "type": "object",
            "properties": {
                "filament_grams": {"type": "number", "description": "Grams of filament used"},
                "print_hours": {"type": "number", "description": "Print time in hours"},
                "labour_minutes": {"type": "number", "description": "Manual labour time (post-processing, painting, packing)"},
                "packaging_cost": {"type": "number", "description": "Cost of packaging materials", "default": 0.50},
                "paint_cost": {"type": "number", "description": "Paint and finishing materials cost", "default": 0},
            },
            "required": [],
        },
    },
    {
        "name": "set_product_cogs_recipe",
        "description": "Define or update the COGS recipe for a specific listing. Physical: set filament/labour/packaging. Digital: set creation_cost and expected_units_sold for amortization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string"},
                "product_type": {"type": "string", "enum": ["digital", "3d_print", "wood"], "description": "Determines which COGS model to apply"},
                "filament_grams": {"type": "number", "description": "Physical only: grams of filament per unit"},
                "print_hours": {"type": "number", "description": "Physical only: print/production hours per unit"},
                "labour_minutes": {"type": "number", "description": "Physical only: post-processing minutes per unit"},
                "paint_cost": {"type": "number", "description": "Physical only: paint and materials cost per unit"},
                "packaging_cost": {"type": "number", "description": "Packaging cost per unit"},
                "creation_cost": {"type": "number", "description": "Digital only: total creation cost (tools, AI API, labour)"},
                "expected_units_sold": {"type": "number", "description": "Digital only: lifetime units to amortize creation cost over"},
            },
            "required": ["listing_id", "product_type"],
        },
    },
    {
        "name": "calculate_break_even",
        "description": "Calculate how many units a digital listing must sell to break even on its creation cost.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Look up from recipe, or provide values directly"},
                "sale_price": {"type": "number"},
                "creation_cost": {"type": "number", "description": "Total investment to create the product (tools, AI, labour hours × rate)"},
            },
            "required": ["sale_price", "creation_cost"],
        },
    },
    {
        "name": "get_profit_per_product",
        "description": "Show profit margin for every listing with margin benchmarks, alerts for below-threshold products, and separate digital/physical COGS models.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "enum": ["profit_dollars", "profit_pct", "revenue"],
                    "default": "profit_pct",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_financial_alerts",
        "description": "Run all 6 financial health checks and return any active alerts: margin violations, offsite ads threshold, tax reserve, negative-margin listings, TACOS, refund rate.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_tax_summary",
        "description": "Show quarterly tax set-aside status, next deadline, recommended reserve amount, and deductible expense total.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Tax year, defaults to current"},
            },
            "required": [],
        },
    },
    {
        "name": "log_expense",
        "description": "Record a business expense tagged to an IRS Schedule C category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "category": {
                    "type": "string",
                    "enum": [
                        "materials", "packaging", "equipment", "software",
                        "platform_fees", "advertising", "shipping_postage",
                        "photography", "home_office", "mileage", "education",
                        "professional_services", "banking", "other",
                    ],
                    "description": "IRS Schedule C-aligned category",
                },
                "description": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD, defaults to today"},
                "tax_deductible": {"type": "boolean", "default": True},
                "miles": {"type": "number", "description": "For mileage category: miles driven (auto-calculates at $0.725/mile)"},
            },
            "required": ["amount", "category", "description"],
        },
    },
    {
        "name": "log_ad_spend",
        "description": "Record Etsy Ads or Offsite Ads spend to enable TACOS (Total Advertising Cost of Sale) tracking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Ad spend in USD"},
                "ad_type": {"type": "string", "enum": ["etsy_ads", "offsite_ads"], "default": "etsy_ads"},
                "date": {"type": "string", "description": "YYYY-MM-DD, defaults to today"},
                "attributed_revenue": {"type": "number", "description": "Revenue attributed to this ad spend", "default": 0},
                "notes": {"type": "string"},
            },
            "required": ["amount"],
        },
    },
    {
        "name": "get_expense_summary",
        "description": "Get a summary of all business expenses by IRS category with tax-deductible total.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Filter by year, defaults to current year"},
            },
            "required": [],
        },
    },
    {
        "name": "get_monthly_pl",
        "description": "Generate a full month-by-month P&L with separate digital/physical revenue lines, all fee components, COGS, expenses, and net profit with margin %.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Year to report, defaults to current year"},
            },
            "required": [],
        },
    },
    {
        "name": "update_cogs_rates",
        "description": "Update the default per-unit cost rates used for COGS calculations when no per-product recipe is set.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filament_cost_per_gram": {"type": "number"},
                "electricity_cost_per_hour": {"type": "number"},
                "labour_cost_per_hour": {"type": "number"},
                "paint_cost_per_item": {"type": "number"},
                "packaging_cost": {"type": "number"},
            },
            "required": [],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    dispatch = {
        "get_profit_report":           lambda: _get_profit_report(tool_input["period"], store),
        "calculate_etsy_fees":         lambda: _calculate_etsy_fees(tool_input, store),
        "calculate_price_from_target_net": lambda: _calculate_price_from_target_net(tool_input, store),
        "calculate_cogs":              lambda: _calculate_cogs(tool_input, store),
        "set_product_cogs_recipe":     lambda: _set_product_cogs_recipe(tool_input, store),
        "calculate_break_even":        lambda: _calculate_break_even(tool_input, store),
        "get_profit_per_product":      lambda: _get_profit_per_product(tool_input.get("sort_by", "profit_pct"), store),
        "get_financial_alerts":        lambda: _get_financial_alerts(store),
        "get_tax_summary":             lambda: _get_tax_summary(tool_input.get("year"), store),
        "log_expense":                 lambda: _log_expense(tool_input, store),
        "log_ad_spend":                lambda: _log_ad_spend(tool_input, store),
        "get_expense_summary":         lambda: _get_expense_summary(tool_input.get("year"), store),
        "get_monthly_pl":              lambda: _get_monthly_pl(tool_input.get("year"), store),
        "update_cogs_rates":           lambda: _update_cogs_rates(tool_input, store),
    }
    fn = dispatch.get(tool_name)
    return fn() if fn else f"Unknown financial tool: {tool_name}"


# ── Period helpers ─────────────────────────────────────────────────────────────

def _period_cutoff(period: str) -> str | None:
    today = date.today()
    if period == "today":        return today.isoformat()
    if period == "this_week":    return (today - timedelta(days=today.weekday())).isoformat()
    if period == "this_month":   return today.replace(day=1).isoformat()
    if period == "this_year":    return today.replace(month=1, day=1).isoformat()
    return None


def _orders_in_period(orders: list, period: str) -> list:
    cutoff = _period_cutoff(period)
    result = [o for o in orders if o.get("status") == "complete"]
    if cutoff:
        result = [o for o in result if o.get("completed_at", o.get("created_at", ""))[:10] >= cutoff]
    return result


def _expenses_in_period(expenses: list, period: str) -> list:
    cutoff = _period_cutoff(period)
    if not cutoff:
        return expenses
    return [e for e in expenses if e.get("date", "")[:10] >= cutoff]


def _orders_in_month(orders: list, year: int, month: int) -> list:
    prefix = f"{year}-{month:02d}"
    return [
        o for o in orders
        if o.get("status") == "complete"
        and o.get("completed_at", o.get("created_at", ""))[:7] == prefix
    ]


# ── Offsite ads rate ───────────────────────────────────────────────────────────

def _offsite_rate(store: DataStore) -> tuple[float, str]:
    """Return (rate, label) based on shop's trailing annual revenue."""
    annual = store.analytics.get("revenue", {}).get("this_year", 0)
    if annual >= ETSY_OFFSITE_ADS_THRESHOLD:
        return ETSY_OFFSITE_ADS_PCT_HIGH, f"12% (mandatory — shop >= ${ETSY_OFFSITE_ADS_THRESHOLD:,}/yr)"
    return ETSY_OFFSITE_ADS_PCT_LOW, f"15% (optional — shop < ${ETSY_OFFSITE_ADS_THRESHOLD:,}/yr)"


# ── COGS helpers ───────────────────────────────────────────────────────────────

def _default_rates() -> dict:
    return {
        "filament_cost_per_gram": 0.02,
        "electricity_cost_per_hour": 0.12,
        "labour_cost_per_hour": 20.00,   # updated to $20/hr (research: $20-30/hr skilled production)
        "paint_cost_per_item": 5.00,
        "packaging_cost": 0.75,           # updated to $0.75 (research: mailer box + tissue + card)
    }


def _cogs_for_listing(listing: dict, store: DataStore) -> tuple[float, str]:
    """Return (cogs_per_unit, cogs_type) for a listing using recipe if available."""
    lid = listing.get("id", "")
    recipes = store.get("financial_data", "cogs_recipes", default={})
    rates = store.get("financial_data", "cogs_rates", default=_default_rates())
    ltype = listing.get("type", "physical")

    if lid in recipes:
        recipe = recipes[lid]
        rtype = recipe.get("product_type", ltype)
        if rtype == "digital":
            cc = recipe.get("creation_cost", 0)
            units = max(recipe.get("expected_units_sold", 1), 1)
            return round(cc / units, 4), "digital_amortized"
        # Physical recipe
        fg = recipe.get("filament_grams", 0)
        ph = recipe.get("print_hours", 0)
        lm = recipe.get("labour_minutes", 0)
        paint = recipe.get("paint_cost", 0)
        pkg = recipe.get("packaging_cost", rates.get("packaging_cost", 0.75))
        cogs = (
            fg * rates.get("filament_cost_per_gram", 0.02) +
            ph * rates.get("electricity_cost_per_hour", 0.12) +
            (lm / 60) * rates.get("labour_cost_per_hour", 20.00) +
            paint + pkg
        )
        return round(cogs, 2), "recipe"

    # No recipe — use type-based defaults
    if ltype == "digital" or listing.get("is_digital"):
        return 0.0, "digital_zero_marginal"

    # Physical default estimate
    default_cogs = (
        rates.get("filament_cost_per_gram", 0.02) * 75 +   # 75g default (more realistic than 50g)
        rates.get("electricity_cost_per_hour", 0.12) * 3 +
        rates.get("packaging_cost", 0.75)
    )
    return round(default_cogs, 2), "default_estimate"


def _margin_status(profit_pct: float, product_type: str) -> str:
    thresholds = MARGIN_TARGETS.get(product_type, MARGIN_TARGETS["physical"])
    if profit_pct >= thresholds["target"]:  return "healthy"
    if profit_pct >= thresholds["warn"]:    return "below_target"
    if profit_pct >= thresholds["critical"]:return "warning"
    return "critical"


# ── Tool implementations ───────────────────────────────────────────────────────

def _get_profit_report(period: str, store: DataStore) -> str:
    revenue_data = store.analytics.get("revenue", {})
    gross = revenue_data.get(period, 0)
    completed = _orders_in_period(store.orders, period)
    total_items = sum(len(o.get("items", [1])) for o in completed)

    transaction_fees = gross * ETSY_TRANSACTION_FEE_PCT
    payment_fees = gross * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT * len(completed)
    listing_fees = total_items * ETSY_LISTING_FEE
    total_fees = transaction_fees + payment_fees + listing_fees

    all_expenses = store.get("financial_data", "expenses", default=[])
    expense_total = sum(e["amount"] for e in _expenses_in_period(all_expenses, period))

    rates = store.get("financial_data", "cogs_rates", default=_default_rates())
    avg_physical_cogs = (
        rates.get("filament_cost_per_gram", 0.02) * 75 +
        rates.get("electricity_cost_per_hour", 0.12) * 3 +
        rates.get("packaging_cost", 0.75)
    )
    estimated_cogs = avg_physical_cogs * len(completed)

    aov = round(gross / len(completed), 2) if completed else 0
    net_profit = gross - total_fees - expense_total - estimated_cogs
    margin_pct = round(net_profit / gross * 100, 1) if gross > 0 else 0

    ad_log = store.get("financial_data", "ad_spend_log", default=[])
    period_ads = sum(e["amount"] for e in _expenses_in_period(ad_log, period))
    tacos = round(period_ads / gross * 100, 1) if gross > 0 and period_ads > 0 else None

    return json.dumps({
        "period": period,
        "gross_revenue": round(gross, 2),
        "order_count": len(completed),
        "average_order_value": aov,
        "etsy_fees": {
            "transaction_6.5pct": round(transaction_fees, 2),
            "payment_processing": round(payment_fees, 2),
            "listing_renewal": round(listing_fees, 2),
            "total_fees": round(total_fees, 2),
            "fees_pct_of_revenue": f"{round(total_fees / gross * 100, 1)}%" if gross else "N/A",
        },
        "estimated_cogs": round(estimated_cogs, 2),
        "operating_expenses": round(expense_total, 2),
        "net_profit": round(net_profit, 2),
        "profit_margin_pct": margin_pct,
        "tacos_pct": tacos,
        "note": "COGS uses default estimates for physical. Set per-listing recipes for accuracy.",
    }, indent=2)


def _calculate_etsy_fees(data: dict, store: DataStore) -> str:
    price = data["item_price"]
    shipping = data.get("shipping_charged", 0)
    offsite = data.get("offsite_ads_sale", False)
    rate, rate_label = _offsite_rate(store)

    subtotal = price + shipping
    transaction_fee = subtotal * ETSY_TRANSACTION_FEE_PCT
    payment_fee = subtotal * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT
    offsite_fee = price * rate if offsite else 0
    listing_fee = ETSY_LISTING_FEE
    total_fees = transaction_fee + payment_fee + offsite_fee + listing_fee
    net = price - total_fees

    return json.dumps({
        "item_price": price,
        "shipping_charged": shipping,
        "fees": {
            "listing_renewal": round(listing_fee, 2),
            "transaction_6.5pct": round(transaction_fee, 2),
            "payment_processing_3pct_plus_25c": round(payment_fee, 2),
            "offsite_ads": round(offsite_fee, 2) if offsite else "N/A",
            "offsite_ads_rate": rate_label if offsite else "N/A",
            "total_fees": round(total_fees, 2),
            "fees_pct_of_price": f"{round(total_fees / price * 100, 1)}%",
        },
        "net_after_fees": round(net, 2),
        "tip": "Subtract your COGS from net_after_fees for true profit. Use calculate_price_from_target_net to work backwards from a desired net.",
    }, indent=2)


def _calculate_price_from_target_net(data: dict, store: DataStore) -> str:
    """Solve for the listing price that yields the target net after all Etsy fees."""
    target_net = data["target_net"]
    shipping = data.get("shipping_charged", 0)
    include_offsite = data.get("assume_offsite_ads", True)
    offsite_rate, offsite_label = _offsite_rate(store)
    ads_rate = offsite_rate if include_offsite else 0

    # Fee stack applied to price P:
    #   total_fees = P * 0.065 + (P + shipping) * 0.03 + 0.25 + P * ads_rate + 0.20
    # net = P - total_fees
    # Solve for P: net = P * (1 - 0.065 - 0.03 - ads_rate) - shipping * 0.03 - 0.45
    variable_rate = ETSY_TRANSACTION_FEE_PCT + ETSY_PAYMENT_PROCESSING_PCT + ads_rate
    fixed_fees = shipping * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT + ETSY_LISTING_FEE
    required_price = (target_net + fixed_fees) / (1 - variable_rate)

    # Verify by calculating actual fees at this price
    actual_fees = (
        required_price * ETSY_TRANSACTION_FEE_PCT +
        (required_price + shipping) * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT +
        required_price * ads_rate + ETSY_LISTING_FEE
    )
    actual_net = required_price - actual_fees

    return json.dumps({
        "target_net": target_net,
        "required_listing_price": round(required_price, 2),
        "suggested_price": round(round(required_price / 0.5) * 0.5, 2),  # round to nearest $0.50
        "verification": {
            "price": round(required_price, 2),
            "total_fees": round(actual_fees, 2),
            "net_after_fees": round(actual_net, 2),
        },
        "offsite_ads_included": include_offsite,
        "offsite_ads_rate": offsite_label if include_offsite else "excluded",
        "tip": "suggested_price rounds to nearest $0.50 for clean pricing. Subtract COGS for final profit check.",
    }, indent=2)


def _calculate_cogs(data: dict, store: DataStore) -> str:
    rates = store.get("financial_data", "cogs_rates", default=_default_rates())
    fg = data.get("filament_grams", 0)
    ph = data.get("print_hours", 0)
    lm = data.get("labour_minutes", 0)
    paint = data.get("paint_cost", 0)
    pkg = data.get("packaging_cost", rates.get("packaging_cost", 0.75))

    filament_cost = fg * rates.get("filament_cost_per_gram", 0.02)
    electricity_cost = ph * rates.get("electricity_cost_per_hour", 0.12)
    labour_cost = (lm / 60) * rates.get("labour_cost_per_hour", 20.00)
    total_cogs = filament_cost + electricity_cost + labour_cost + paint + pkg

    return json.dumps({
        "inputs": {"filament_grams": fg, "print_hours": ph, "labour_minutes": lm, "paint_cost": paint},
        "cogs_breakdown": {
            "filament": round(filament_cost, 2),
            "electricity": round(electricity_cost, 2),
            "labour": round(labour_cost, 2),
            "paint_materials": round(paint, 2),
            "packaging": round(pkg, 2),
        },
        "total_cogs": round(total_cogs, 2),
        "rates_used": rates,
    }, indent=2)


def _set_product_cogs_recipe(data: dict, store: DataStore) -> str:
    lid = data["listing_id"]
    fin = store.get("financial_data", default={"cogs_recipes": {}})
    recipes = fin.get("cogs_recipes", {})
    recipe = {"product_type": data["product_type"]}

    if data["product_type"] == "digital":
        recipe["creation_cost"] = data.get("creation_cost", 0)
        recipe["expected_units_sold"] = data.get("expected_units_sold", 100)
        cc = recipe["creation_cost"]
        units = max(recipe["expected_units_sold"], 1)
        recipe["_amortized_cogs_per_unit"] = round(cc / units, 4)
    else:
        for field in ("filament_grams", "print_hours", "labour_minutes", "paint_cost", "packaging_cost"):
            if field in data:
                recipe[field] = data[field]

    recipes[lid] = recipe
    fin["cogs_recipes"] = recipes
    store.set(fin, "financial_data")
    store.save()
    return json.dumps({"success": True, "listing_id": lid, "recipe": recipe}, indent=2)


def _calculate_break_even(data: dict, store: DataStore) -> str:
    price = data["sale_price"]
    creation_cost = data["creation_cost"]
    lid = data.get("listing_id", "")

    # Fees per sale (no offsite ads for break-even — use base fees)
    fees_per_sale = (
        price * ETSY_TRANSACTION_FEE_PCT +
        price * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT +
        ETSY_LISTING_FEE
    )
    net_per_sale = price - fees_per_sale
    break_even_units = creation_cost / net_per_sale if net_per_sale > 0 else float("inf")

    revenue_at_break_even = price * break_even_units
    days_to_break_even_1_per_day = break_even_units
    days_to_break_even_3_per_day = break_even_units / 3

    return json.dumps({
        "listing_id": lid,
        "sale_price": price,
        "creation_cost": creation_cost,
        "fees_per_sale": round(fees_per_sale, 2),
        "net_per_sale_after_fees": round(net_per_sale, 2),
        "break_even_units": round(break_even_units, 1) if break_even_units != float("inf") else "n/a (negative margin)",
        "gross_revenue_at_break_even": round(revenue_at_break_even, 2) if break_even_units != float("inf") else "n/a",
        "days_to_break_even": {
            "at_1_sale_per_day": round(days_to_break_even_1_per_day, 0) if break_even_units != float("inf") else "n/a",
            "at_3_sales_per_day": round(days_to_break_even_3_per_day, 1) if break_even_units != float("inf") else "n/a",
        },
        "tip": "Once past break-even, every sale is pure profit (digital). Consider lowering price to accelerate volume if margin allows.",
    }, indent=2)


def _get_profit_per_product(sort_by: str, store: DataStore) -> str:
    listings = store.listings
    offsite_rate, offsite_label = _offsite_rate(store)

    rows = []
    for l in listings:
        price = l.get("price", 0)
        if price == 0:
            continue
        ltype = "digital" if l.get("is_digital") or l.get("type") == "digital" else l.get("type", "physical")
        norm_type = "digital" if ltype == "digital" else ("wood" if "wood" in ltype.lower() else "3d_print")

        base_fees = (
            price * ETSY_TRANSACTION_FEE_PCT +
            price * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT +
            ETSY_LISTING_FEE
        )
        fees_with_offsite = base_fees + price * offsite_rate
        cogs, cogs_type = _cogs_for_listing(l, store)

        profit = price - base_fees - cogs
        profit_with_offsite = price - fees_with_offsite - cogs
        profit_pct = round(profit / price * 100, 1) if price else 0
        status = _margin_status(profit_pct, norm_type)

        thresholds = MARGIN_TARGETS.get(norm_type, MARGIN_TARGETS["physical"])
        rows.append({
            "id": l["id"],
            "title": l["title"][:50],
            "type": norm_type,
            "price": price,
            "etsy_fees": round(base_fees, 2),
            "cogs": round(cogs, 2),
            "cogs_source": cogs_type,
            "profit_dollars": round(profit, 2),
            "profit_pct": profit_pct,
            "profit_pct_worst_case_offsite": round(profit_with_offsite / price * 100, 1) if price else 0,
            "margin_status": status,
            "target_margin": f"{thresholds['target']}%",
        })

    sort_map = {
        "profit_dollars": lambda r: r["profit_dollars"],
        "profit_pct":     lambda r: r["profit_pct"],
        "revenue":        lambda r: r["price"],
    }
    rows.sort(key=sort_map.get(sort_by, sort_map["profit_pct"]), reverse=True)

    critical = [r for r in rows if r["margin_status"] == "critical"]
    warning  = [r for r in rows if r["margin_status"] == "warning"]

    return json.dumps({
        "products": rows,
        "offsite_ads_rate": offsite_label,
        "critical_listings": [{"id": r["id"], "title": r["title"], "profit_pct": r["profit_pct"]} for r in critical],
        "warning_listings":  [{"id": r["id"], "title": r["title"], "profit_pct": r["profit_pct"]} for r in warning],
        "healthy_count": len([r for r in rows if r["margin_status"] == "healthy"]),
        "note": "Listings with cogs_source='default_estimate' — use set_product_cogs_recipe for accurate margins.",
    }, indent=2)


def _get_financial_alerts(store: DataStore) -> str:
    alerts = []
    today = date.today()

    # Alert 1: Margin violations per listing
    listings = store.listings
    offsite_rate, _ = _offsite_rate(store)
    for l in listings:
        price = l.get("price", 0)
        if not price:
            continue
        ltype = "digital" if l.get("is_digital") or l.get("type") == "digital" else "3d_print"
        fees = (price * ETSY_TRANSACTION_FEE_PCT + price * ETSY_PAYMENT_PROCESSING_PCT +
                ETSY_PAYMENT_PROCESSING_FLAT + ETSY_LISTING_FEE)
        cogs, _ = _cogs_for_listing(l, store)
        profit_pct = round((price - fees - cogs) / price * 100, 1) if price else 0
        status = _margin_status(profit_pct, ltype)
        if status in ("warning", "critical"):
            thresholds = MARGIN_TARGETS.get(ltype, MARGIN_TARGETS["physical"])
            alerts.append({
                "type": "margin_violation",
                "severity": status,
                "listing_id": l["id"],
                "listing_title": l["title"][:50],
                "current_margin": f"{profit_pct}%",
                "target_margin": f"{thresholds['target']}%",
                "action": f"Raise price or review COGS. Use calculate_price_from_target_net for target {thresholds['target']}% margin.",
            })

    # Alert 2: Offsite Ads threshold warning
    annual_revenue = store.analytics.get("revenue", {}).get("this_year", 0)
    if ETSY_OFFSITE_ADS_WARNING <= annual_revenue < ETSY_OFFSITE_ADS_THRESHOLD:
        remaining = ETSY_OFFSITE_ADS_THRESHOLD - annual_revenue
        alerts.append({
            "type": "offsite_ads_threshold",
            "severity": "warning",
            "current_annual_revenue": round(annual_revenue, 2),
            "threshold": ETSY_OFFSITE_ADS_THRESHOLD,
            "remaining_before_mandatory": round(remaining, 2),
            "action": f"At ${remaining:.0f} more revenue, Offsite Ads become mandatory at 12%. Review pricing to maintain margins.",
        })

    # Alert 3: Negative-margin listings
    for l in listings:
        price = l.get("price", 0)
        if not price:
            continue
        fees = (price * ETSY_TRANSACTION_FEE_PCT + price * ETSY_PAYMENT_PROCESSING_PCT +
                ETSY_PAYMENT_PROCESSING_FLAT + ETSY_LISTING_FEE)
        cogs, _ = _cogs_for_listing(l, store)
        if (price - fees - cogs) < 0:
            alerts.append({
                "type": "negative_margin",
                "severity": "critical",
                "listing_id": l["id"],
                "listing_title": l["title"][:50],
                "loss_per_sale": round(price - fees - cogs, 2),
                "action": "This listing loses money on every sale. Raise price immediately or remove the listing.",
            })

    # Alert 4: Tax reserve underfunded
    fin = store.get("financial_data", default={})
    tax_reserve = fin.get("tax_reserve", 0)
    net_profit_ytd = store.analytics.get("revenue", {}).get("this_year", 0) * 0.65  # rough estimate
    recommended_reserve = net_profit_ytd * TAX_SETASIDE_PCT
    if tax_reserve < recommended_reserve and recommended_reserve > 0:
        shortfall = recommended_reserve - tax_reserve
        alerts.append({
            "type": "tax_reserve_underfunded",
            "severity": "warning",
            "current_reserve": round(tax_reserve, 2),
            "recommended_reserve": round(recommended_reserve, 2),
            "shortfall": round(shortfall, 2),
            "action": f"Transfer ${shortfall:.2f} to your tax reserve account. Target: {int(TAX_SETASIDE_PCT*100)}% of net profit.",
        })

    # Alert 5: TACOS spike (total ad spend vs. total revenue this month)
    ad_log = fin.get("ad_spend_log", [])
    month_prefix = today.strftime("%Y-%m")
    month_ads = sum(e["amount"] for e in ad_log if e.get("date", "").startswith(month_prefix))
    month_revenue = store.analytics.get("revenue", {}).get("this_month", 0)
    if month_revenue > 0 and month_ads > 0:
        tacos = round(month_ads / month_revenue * 100, 1)
        if tacos > 10:
            alerts.append({
                "type": "tacos_spike",
                "severity": "warning" if tacos <= 15 else "critical",
                "tacos_pct": tacos,
                "ad_spend_this_month": round(month_ads, 2),
                "revenue_this_month": round(month_revenue, 2),
                "action": f"TACOS at {tacos}% (healthy target: under 10%). Review which listings are consuming ad budget without converting.",
            })

    # Alert 6: Upcoming quarterly tax deadline
    for quarter, deadline in QUARTERLY_DEADLINES:
        days_until = (deadline - today).days
        if 0 <= days_until <= 21:
            alerts.append({
                "type": "quarterly_tax_deadline",
                "severity": "warning" if days_until > 7 else "critical",
                "quarter": quarter,
                "deadline": deadline.isoformat(),
                "days_until": days_until,
                "action": f"Quarterly estimated tax payment ({quarter}) due {deadline.strftime('%B %d')}. Pay at IRS.gov/payments.",
            })

    return json.dumps({
        "alert_count": len(alerts),
        "alerts": alerts,
        "checked_at": today.isoformat(),
        "status": "all_clear" if not alerts else ("critical" if any(a["severity"] == "critical" for a in alerts) else "warning"),
    }, indent=2)


def _get_tax_summary(year: int | None, store: DataStore) -> str:
    year = year or date.today().year
    today = date.today()
    fin = store.get("financial_data", default={})

    # Revenue and profit estimates
    gross_ytd = store.analytics.get("revenue", {}).get("this_year", 0)
    expenses = [e for e in fin.get("expenses", []) if e.get("date", "").startswith(str(year))]
    expense_total = sum(e["amount"] for e in expenses)
    deductible_total = sum(e["amount"] for e in expenses if e.get("tax_deductible", True))
    estimated_net = gross_ytd * 0.65 - expense_total   # rough net after fees + COGS

    # Tax set-aside calculations
    se_tax_est = max(estimated_net, 0) * SE_TAX_RATE
    income_tax_est = max(estimated_net, 0) * 0.12   # conservative estimate for 12% bracket
    total_tax_est = se_tax_est + income_tax_est
    recommended_reserve = max(estimated_net, 0) * TAX_SETASIDE_PCT
    current_reserve = fin.get("tax_reserve", 0)

    # Next deadline
    next_deadline = next(
        ((q, d) for q, d in QUARTERLY_DEADLINES if d >= today),
        QUARTERLY_DEADLINES[-1]
    )

    return json.dumps({
        "tax_year": year,
        "estimated_gross_revenue_ytd": round(gross_ytd, 2),
        "deductible_expenses_ytd": round(deductible_total, 2),
        "estimated_net_profit_ytd": round(estimated_net, 2),
        "tax_estimates": {
            "self_employment_tax_15.3pct": round(se_tax_est, 2),
            "estimated_income_tax": round(income_tax_est, 2),
            "total_estimated_tax": round(total_tax_est, 2),
        },
        "tax_reserve": {
            "current_reserve_on_file": round(current_reserve, 2),
            "recommended_28pct_of_net": round(recommended_reserve, 2),
            "shortfall": round(max(recommended_reserve - current_reserve, 0), 2),
        },
        "next_quarterly_deadline": {
            "quarter": next_deadline[0],
            "date": next_deadline[1].isoformat(),
            "days_until": (next_deadline[1] - today).days,
        },
        "all_deadlines_2026": [
            {"quarter": q, "date": d.isoformat()} for q, d in QUARTERLY_DEADLINES
        ],
        "mileage_rate_2026": f"${IRS_MILEAGE_2026}/mile",
        "tip": "Pay quarterly estimates at IRS.gov/payments. Set aside 28% of every Etsy payout to stay current.",
    }, indent=2)


def _log_expense(data: dict, store: DataStore) -> str:
    fin = store.get("financial_data", default={"expenses": [], "cogs_rates": _default_rates()})
    expenses = fin.get("expenses", [])
    amount = data["amount"]

    # Auto-calculate mileage expense
    if data["category"] == "mileage" and "miles" in data:
        amount = round(data["miles"] * IRS_MILEAGE_2026, 2)

    exp_id = f"EXP{len(expenses) + 1:04d}"
    record = {
        "id": exp_id,
        "amount": amount,
        "category": data["category"],
        "description": data["description"],
        "date": data.get("date", str(date.today())),
        "tax_deductible": data.get("tax_deductible", True),
    }
    if "miles" in data:
        record["miles"] = data["miles"]
    expenses.append(record)
    fin["expenses"] = expenses
    store.set(fin, "financial_data")
    store.save()
    return json.dumps({"success": True, "expense_id": exp_id, "amount": amount,
                       "category": record["category"], "tax_deductible": record["tax_deductible"]}, indent=2)


def _log_ad_spend(data: dict, store: DataStore) -> str:
    fin = store.get("financial_data", default={})
    ad_log = fin.get("ad_spend_log", [])
    entry = {
        "amount": data["amount"],
        "ad_type": data.get("ad_type", "etsy_ads"),
        "date": data.get("date", str(date.today())),
        "attributed_revenue": data.get("attributed_revenue", 0),
        "notes": data.get("notes", ""),
    }
    if entry["attributed_revenue"] > 0:
        entry["roas"] = round(entry["attributed_revenue"] / entry["amount"], 2)
    ad_log.append(entry)
    fin["ad_spend_log"] = ad_log
    store.set(fin, "financial_data")
    store.save()
    return json.dumps({"success": True, "logged": entry}, indent=2)


def _get_expense_summary(year: int | None, store: DataStore) -> str:
    year = year or date.today().year
    fin = store.get("financial_data", default={"expenses": []})
    expenses = [e for e in fin.get("expenses", []) if e.get("date", "").startswith(str(year))]
    by_cat: dict[str, float] = {}
    deductible_total = 0.0
    for e in expenses:
        cat = e.get("category", "other")
        by_cat[cat] = round(by_cat.get(cat, 0) + e["amount"], 2)
        if e.get("tax_deductible", True):
            deductible_total += e["amount"]
    return json.dumps({
        "year": year,
        "total_expenses": round(sum(by_cat.values()), 2),
        "by_category": by_cat,
        "tax_deductible_total": round(deductible_total, 2),
        "expense_count": len(expenses),
        "schedule_c_note": "Categories align to IRS Schedule C. Share with your accountant at tax time.",
    }, indent=2)


def _get_monthly_pl(year: int | None, store: DataStore) -> str:
    year = year or date.today().year
    fin = store.get("financial_data", default={"expenses": []})
    expenses = fin.get("expenses", [])
    all_orders = store.orders
    listings_map = {l["id"]: l for l in store.listings}
    rates = store.get("financial_data", "cogs_rates", default=_default_rates())
    offsite_rate, offsite_label = _offsite_rate(store)

    # Per-order digital/physical split
    def classify_order(order):
        items = order.get("items", [])
        for item in items:
            lid = item.get("listing_id", "")
            l = listings_map.get(lid, {})
            if l.get("is_digital") or l.get("type") == "digital":
                return "digital"
        return "physical"

    monthly = []
    for month in range(1, 13):
        month_str = f"{year}-{month:02d}"
        month_orders = _orders_in_month(all_orders, year, month)
        month_expenses = sum(e["amount"] for e in expenses if e.get("date", "").startswith(month_str))

        digital_orders = [o for o in month_orders if classify_order(o) == "digital"]
        physical_orders = [o for o in month_orders if classify_order(o) == "physical"]

        digital_rev = sum(o.get("total_price", 0) for o in digital_orders)
        physical_rev = sum(o.get("total_price", 0) for o in physical_orders)
        gross = digital_rev + physical_rev

        # Fees
        transaction_fees = gross * ETSY_TRANSACTION_FEE_PCT
        payment_fees = gross * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT * len(month_orders)
        listing_fees = len(month_orders) * ETSY_LISTING_FEE
        total_fees = transaction_fees + payment_fees + listing_fees

        # COGS — digital is near-zero, physical uses rates
        avg_physical_cogs = (
            rates.get("filament_cost_per_gram", 0.02) * 75 +
            rates.get("electricity_cost_per_hour", 0.12) * 3 +
            rates.get("packaging_cost", 0.75)
        )
        digital_cogs = 0  # marginal COGS for digital is zero
        physical_cogs = avg_physical_cogs * len(physical_orders)

        net = gross - total_fees - digital_cogs - physical_cogs - month_expenses
        margin = round(net / gross * 100, 1) if gross > 0 else 0

        monthly.append({
            "month": month_str,
            "revenue": {
                "digital": round(digital_rev, 2),
                "physical": round(physical_rev, 2),
                "total": round(gross, 2),
            },
            "order_count": {"digital": len(digital_orders), "physical": len(physical_orders)},
            "etsy_fees": round(total_fees, 2),
            "cogs_est": round(digital_cogs + physical_cogs, 2),
            "operating_expenses": round(month_expenses, 2),
            "net_profit": round(net, 2),
            "net_margin_pct": margin,
        })

    totals = {
        "gross_revenue": round(sum(m["revenue"]["total"] for m in monthly), 2),
        "digital_revenue": round(sum(m["revenue"]["digital"] for m in monthly), 2),
        "physical_revenue": round(sum(m["revenue"]["physical"] for m in monthly), 2),
        "total_fees": round(sum(m["etsy_fees"] for m in monthly), 2),
        "total_cogs": round(sum(m["cogs_est"] for m in monthly), 2),
        "total_expenses": round(sum(m["operating_expenses"] for m in monthly), 2),
        "net_profit": round(sum(m["net_profit"] for m in monthly), 2),
    }
    gross_total = totals["gross_revenue"]
    totals["blended_margin_pct"] = round(totals["net_profit"] / gross_total * 100, 1) if gross_total else 0

    return json.dumps({
        "year": year,
        "offsite_ads_rate": offsite_label,
        "monthly_pl": monthly,
        "annual_totals": totals,
        "benchmark": "Healthy blended margin for a digital-heavy Etsy shop: 55-70%+",
        "note": "Physical COGS uses default estimates. Use set_product_cogs_recipe per listing for accuracy.",
    }, indent=2)


def _update_cogs_rates(data: dict, store: DataStore) -> str:
    fin = store.get("financial_data", default={"expenses": [], "cogs_rates": _default_rates()})
    rates = fin.get("cogs_rates", _default_rates())
    changed = {}
    for key in ("filament_cost_per_gram", "electricity_cost_per_hour", "labour_cost_per_hour",
                "paint_cost_per_item", "packaging_cost"):
        if key in data:
            changed[key] = {"from": rates.get(key), "to": data[key]}
            rates[key] = data[key]
    fin["cogs_rates"] = rates
    store.set(fin, "financial_data")
    store.save()
    return json.dumps({"success": True, "updated_rates": rates, "changes": changed}, indent=2)
