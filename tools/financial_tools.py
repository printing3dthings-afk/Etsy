"""
Financial & Accounting Tools — tracks real profit, Etsy fees, COGS, and P&L.

Etsy fee structure (as of 2025):
  Listing fee:          $0.20 per listing (every 4 months)
  Transaction fee:      6.5% of item price + shipping charged
  Payment processing:   3% + $0.25 per transaction (Etsy Payments)
  Offsite Ads:          12% (shops > $10k/yr revenue) or 15% (under $10k)
  Regulatory fee:       varies by country (US: not applicable in most states)
"""

import json
from datetime import date, datetime
from typing import Any

from tools.data_store import DataStore

ETSY_LISTING_FEE = 0.20
ETSY_TRANSACTION_FEE_PCT = 0.065
ETSY_PAYMENT_PROCESSING_PCT = 0.030
ETSY_PAYMENT_PROCESSING_FLAT = 0.25
ETSY_OFFSITE_ADS_PCT_LOW = 0.15   # < $10k/yr revenue
ETSY_OFFSITE_ADS_PCT_HIGH = 0.12  # >= $10k/yr revenue

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_profit_report",
        "description": "Calculate net profit for a period after all Etsy fees and COGS.",
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
        "description": "Calculate exact Etsy fees for a given sale amount and shipping charge.",
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
        "name": "calculate_cogs",
        "description": "Calculate cost of goods sold for a physical product (filament weight, electricity, labour).",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Listing ID to look up (optional, or provide values directly)"},
                "filament_grams": {"type": "number", "description": "Grams of filament used"},
                "print_hours": {"type": "number", "description": "Print time in hours"},
                "labour_minutes": {"type": "number", "description": "Manual labour time (post-processing, painting, packing)"},
                "packaging_cost": {"type": "number", "description": "Cost of packaging materials", "default": 0.50},
            },
            "required": [],
        },
    },
    {
        "name": "get_profit_per_product",
        "description": "Show profit margin for every listing after fees and COGS.",
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
        "name": "log_expense",
        "description": "Record a business expense (filament, tools, software, shipping supplies, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "category": {
                    "type": "string",
                    "enum": ["materials", "equipment", "software", "shipping_supplies", "advertising", "fees", "other"],
                },
                "description": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD, defaults to today"},
                "tax_deductible": {"type": "boolean", "default": True},
            },
            "required": ["amount", "category", "description"],
        },
    },
    {
        "name": "get_expense_summary",
        "description": "Get a summary of all business expenses by category.",
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
        "description": "Generate a month-by-month P&L statement showing revenue, fees, COGS, expenses, and net profit.",
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
        "description": "Update the per-unit cost rates used for COGS calculations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filament_cost_per_gram": {"type": "number", "description": "Cost per gram of filament in USD"},
                "electricity_cost_per_hour": {"type": "number", "description": "Electricity cost per print hour in USD"},
                "labour_cost_per_hour": {"type": "number", "description": "Your time value per hour in USD"},
                "paint_cost_per_item": {"type": "number", "description": "Average paint/supplies cost for hand-painted items"},
            },
            "required": [],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_profit_report":
        return _get_profit_report(tool_input["period"], store)
    if tool_name == "calculate_etsy_fees":
        return _calculate_etsy_fees(tool_input)
    if tool_name == "calculate_cogs":
        return _calculate_cogs(tool_input, store)
    if tool_name == "get_profit_per_product":
        return _get_profit_per_product(tool_input.get("sort_by", "profit_pct"), store)
    if tool_name == "log_expense":
        return _log_expense(tool_input, store)
    if tool_name == "get_expense_summary":
        return _get_expense_summary(tool_input.get("year"), store)
    if tool_name == "get_monthly_pl":
        return _get_monthly_pl(tool_input.get("year"), store)
    if tool_name == "update_cogs_rates":
        return _update_cogs_rates(tool_input, store)
    return f"Unknown financial tool: {tool_name}"


def _get_profit_report(period: str, store: DataStore) -> str:
    revenue_data = store.analytics.get("revenue", {})
    gross = revenue_data.get(period, 0)
    orders = store.orders

    # Filter orders by period (simplified — use all completed orders)
    completed = [o for o in orders if o.get("status") == "complete"]
    total_items = sum(len(o.get("items", [1])) for o in completed)

    # Fee estimates
    transaction_fees = gross * ETSY_TRANSACTION_FEE_PCT
    payment_fees = gross * ETSY_PAYMENT_PROCESSING_PCT + (ETSY_PAYMENT_PROCESSING_FLAT * len(completed))
    listing_fees = total_items * ETSY_LISTING_FEE
    total_fees = transaction_fees + payment_fees + listing_fees

    # Expenses for period
    expenses = store.get("financial_data", "expenses", default=[])
    expense_total = sum(e["amount"] for e in expenses)

    # COGS estimate (from rates)
    rates = store.get("financial_data", "cogs_rates", default=_default_rates())
    avg_cogs_per_order = (
        rates.get("filament_cost_per_gram", 0.02) * 50 +
        rates.get("electricity_cost_per_hour", 0.12) * 3 +
        rates.get("packaging_cost", 0.50)
    )
    estimated_cogs = avg_cogs_per_order * len(completed)

    net_profit = gross - total_fees - expense_total - estimated_cogs
    margin_pct = round((net_profit / gross * 100), 1) if gross > 0 else 0

    return json.dumps({
        "period": period,
        "gross_revenue": round(gross, 2),
        "etsy_fees": {
            "transaction_6.5pct": round(transaction_fees, 2),
            "payment_processing": round(payment_fees, 2),
            "listing_fees": round(listing_fees, 2),
            "total_fees": round(total_fees, 2),
        },
        "estimated_cogs": round(estimated_cogs, 2),
        "other_expenses": round(expense_total, 2),
        "net_profit": round(net_profit, 2),
        "profit_margin_pct": margin_pct,
        "completed_orders": len(completed),
        "note": "COGS is estimated from rates. Use update_cogs_rates to set accurate per-product costs.",
    }, indent=2)


def _calculate_etsy_fees(data: dict) -> str:
    price = data["item_price"]
    shipping = data.get("shipping_charged", 0)
    offsite = data.get("offsite_ads_sale", False)

    subtotal = price + shipping
    transaction_fee = subtotal * ETSY_TRANSACTION_FEE_PCT
    payment_fee = subtotal * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT
    offsite_fee = price * ETSY_OFFSITE_ADS_PCT_LOW if offsite else 0
    listing_fee = ETSY_LISTING_FEE
    total_fees = transaction_fee + payment_fee + offsite_fee + listing_fee
    net = price - total_fees

    return json.dumps({
        "item_price": price,
        "shipping_charged": shipping,
        "fees": {
            "listing_fee": round(listing_fee, 2),
            "transaction_fee_6.5pct": round(transaction_fee, 2),
            "payment_processing": round(payment_fee, 2),
            "offsite_ads_15pct": round(offsite_fee, 2) if offsite else "N/A",
            "total_fees": round(total_fees, 2),
            "fees_as_pct_of_price": f"{round(total_fees / price * 100, 1)}%",
        },
        "net_after_fees": round(net, 2),
        "tip": "This does NOT include your COGS (materials, labour). Subtract those from net_after_fees for true profit.",
    }, indent=2)


def _calculate_cogs(data: dict, store: DataStore) -> str:
    rates = store.get("financial_data", "cogs_rates", default=_default_rates())
    filament_g = data.get("filament_grams", 0)
    print_hrs = data.get("print_hours", 0)
    labour_min = data.get("labour_minutes", 0)
    packaging = data.get("packaging_cost", rates.get("packaging_cost", 0.50))

    filament_cost = filament_g * rates.get("filament_cost_per_gram", 0.02)
    electricity_cost = print_hrs * rates.get("electricity_cost_per_hour", 0.12)
    labour_cost = (labour_min / 60) * rates.get("labour_cost_per_hour", 15.00)
    total_cogs = filament_cost + electricity_cost + labour_cost + packaging

    return json.dumps({
        "inputs": {"filament_grams": filament_g, "print_hours": print_hrs, "labour_minutes": labour_min},
        "cogs_breakdown": {
            "filament": round(filament_cost, 2),
            "electricity": round(electricity_cost, 2),
            "labour": round(labour_cost, 2),
            "packaging": round(packaging, 2),
        },
        "total_cogs": round(total_cogs, 2),
        "rates_used": rates,
    }, indent=2)


def _get_profit_per_product(sort_by: str, store: DataStore) -> str:
    listings = store.listings
    rates = store.get("financial_data", "cogs_rates", default=_default_rates())
    default_cogs = (
        rates.get("filament_cost_per_gram", 0.02) * 50 +
        rates.get("electricity_cost_per_hour", 0.12) * 3 +
        rates.get("packaging_cost", 0.50)
    )

    rows = []
    for l in listings:
        price = l.get("price", 0)
        if price == 0:
            continue
        fees = (
            price * ETSY_TRANSACTION_FEE_PCT +
            price * ETSY_PAYMENT_PROCESSING_PCT + ETSY_PAYMENT_PROCESSING_FLAT +
            ETSY_LISTING_FEE
        )
        cogs = l.get("cogs", default_cogs)
        profit = price - fees - cogs
        rows.append({
            "id": l["id"],
            "title": l["title"][:50],
            "price": price,
            "etsy_fees": round(fees, 2),
            "cogs": round(cogs, 2),
            "profit_dollars": round(profit, 2),
            "profit_pct": round(profit / price * 100, 1) if price else 0,
            "type": l.get("type", "physical"),
        })

    sort_map = {
        "profit_dollars": lambda r: r["profit_dollars"],
        "profit_pct": lambda r: r["profit_pct"],
        "revenue": lambda r: r["price"],
    }
    rows.sort(key=sort_map.get(sort_by, sort_map["profit_pct"]), reverse=True)

    winners = [r for r in rows if r["profit_pct"] > 40]
    losers = [r for r in rows if r["profit_pct"] < 20]

    return json.dumps({
        "products": rows,
        "high_margin_winners": [r["id"] for r in winners],
        "low_margin_concern": [r["id"] for r in losers],
        "note": "COGS uses estimates. Set per-listing 'cogs' field or use update_cogs_rates for accuracy.",
    }, indent=2)


def _log_expense(data: dict, store: DataStore) -> str:
    fin = store.get("financial_data", default={"expenses": [], "cogs_rates": _default_rates()})
    expenses = fin.get("expenses", [])
    exp_id = f"EXP{len(expenses) + 1:04d}"
    record = {
        "id": exp_id,
        "amount": data["amount"],
        "category": data["category"],
        "description": data["description"],
        "date": data.get("date", str(date.today())),
        "tax_deductible": data.get("tax_deductible", True),
    }
    expenses.append(record)
    fin["expenses"] = expenses
    store.set(fin, "financial_data")
    store.save()
    return json.dumps({"success": True, "expense_id": exp_id, "amount": data["amount"],
                       "tax_deductible": record["tax_deductible"]}, indent=2)


def _get_expense_summary(year: int | None, store: DataStore) -> str:
    year = year or date.today().year
    fin = store.get("financial_data", default={"expenses": []})
    expenses = [e for e in fin.get("expenses", []) if e.get("date", "").startswith(str(year))]
    by_cat: dict[str, float] = {}
    deductible_total = 0.0
    for e in expenses:
        cat = e.get("category", "other")
        by_cat[cat] = round(by_cat.get(cat, 0) + e["amount"], 2)
        if e.get("tax_deductible"):
            deductible_total += e["amount"]
    return json.dumps({
        "year": year,
        "total_expenses": round(sum(by_cat.values()), 2),
        "by_category": by_cat,
        "tax_deductible_total": round(deductible_total, 2),
        "expense_count": len(expenses),
    }, indent=2)


def _get_monthly_pl(year: int | None, store: DataStore) -> str:
    year = year or date.today().year
    fin = store.get("financial_data", default={"expenses": []})
    expenses = fin.get("expenses", [])

    monthly: list[dict] = []
    for month in range(1, 13):
        month_str = f"{year}-{month:02d}"
        month_expenses = sum(e["amount"] for e in expenses if e.get("date", "").startswith(month_str))
        monthly.append({
            "month": month_str,
            "gross_revenue": 0,
            "etsy_fees_est": 0,
            "cogs_est": 0,
            "other_expenses": round(month_expenses, 2),
            "net_profit": round(-month_expenses, 2),
            "note": "Connect Etsy API to populate revenue. Expenses tracked locally.",
        })

    return json.dumps({
        "year": year,
        "monthly_pl": monthly,
        "annual_totals": {
            "total_expenses": round(sum(m["other_expenses"] for m in monthly), 2),
        },
        "tip": "Revenue data populates automatically once Etsy OAuth is configured.",
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


def _default_rates() -> dict:
    return {
        "filament_cost_per_gram": 0.02,
        "electricity_cost_per_hour": 0.12,
        "labour_cost_per_hour": 15.00,
        "paint_cost_per_item": 5.00,
        "packaging_cost": 0.50,
    }
