"""
Tax & Compliance Tools — tracks tax obligations, deductions, and Etsy policy compliance.

Important: This provides guidance, not legal/tax advice. Consult a CPA for your specific situation.

Key facts:
  - Etsy collects and remits sales tax in most US states automatically (marketplace facilitator laws)
  - You still owe income tax on your NET profit from the shop
  - Etsy sends a 1099-K if you receive $600+ in gross sales in a calendar year (as of 2024 IRS rules)
  - Business expenses reduce your taxable income
"""
from __future__ import annotations

import json
from datetime import date
from tools.data_store import DataStore

# Self-employment tax rate (15.3% on net self-employment income)
SE_TAX_RATE = 0.153
# Federal income tax estimate (bracket-based, simplified)
FEDERAL_BRACKETS = [(11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24), (243725, 0.32)]

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_tax_overview",
        "description": "Overview of tax obligations: estimated annual tax, quarterly payment schedule, 1099-K status.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "calculate_quarterly_tax",
        "description": "Estimate quarterly estimated tax payment based on current YTD profit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "quarter": {
                    "type": "integer",
                    "description": "Tax quarter (1=Jan-Mar, 2=Apr-Jun, 3=Jul-Sep, 4=Oct-Dec)",
                    "enum": [1, 2, 3, 4],
                }
            },
            "required": ["quarter"],
        },
    },
    {
        "name": "log_deductible_expense",
        "description": "Log a business expense that reduces taxable income.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "category": {
                    "type": "string",
                    "enum": ["home_office", "equipment", "materials", "software_subscriptions",
                             "advertising", "shipping", "professional_services", "education", "other"],
                },
                "description": {"type": "string"},
                "receipt_reference": {"type": "string", "description": "Receipt/invoice number for records"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["amount", "category", "description"],
        },
    },
    {
        "name": "get_deductions_summary",
        "description": "Summary of all logged tax-deductible expenses for the year.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "check_etsy_compliance",
        "description": "Check if shop practices comply with Etsy's seller policies.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "check_copyright_guidance",
        "description": "Guidance on copyright and IP risks for a product concept before creating it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_concept": {"type": "string", "description": "Describe the product to assess for copyright risk"},
            },
            "required": ["product_concept"],
        },
    },
    {
        "name": "get_1099k_status",
        "description": "Check if the shop is on track to receive a 1099-K from Etsy and what that means.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_tax_calendar",
        "description": "Get important tax dates and deadlines for the current year.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# 2026-08-06 (full-system audit follow-up): get_tax_overview/calculate_quarterly_tax/
# get_1099k_status/check_etsy_compliance used to read store.analytics/store.listings --
# fields NOTHING in the live app populates (that's a separate, ad-spend-only local log
# tools/etsy_ads_tools.py uses honestly; see main.py's own comment on why that one's
# legit). Reading it here would have silently reported $0 revenue / zero compliance
# issues as if real. These 4 now take the real numbers as EXPLICIT required params
# (real_data, populated by main.py from a real date-scoped Etsy receipts fetch and a
# real live listings fetch) instead of deriving them from the disconnected store --
# structurally impossible to accidentally call with fabricated data again.
_REAL_DATA_TOOL_NAMES = frozenset({
    "get_tax_overview", "calculate_quarterly_tax", "get_1099k_status", "check_etsy_compliance",
})


def execute_tool(tool_name: str, tool_input: dict, store: DataStore, real_data: dict | None = None) -> str:
    if tool_name in _REAL_DATA_TOOL_NAMES and real_data is None:
        raise ValueError(
            f"{tool_name} requires real_data (gross_ytd/listings from a live Etsy fetch) -- "
            "refusing to silently report zero/fabricated numbers"
        )
    if tool_name == "get_tax_overview":
        return _get_tax_overview(store, real_data["gross_ytd"], real_data["ytd_orders_capped"])
    if tool_name == "calculate_quarterly_tax":
        return _calculate_quarterly_tax(tool_input["quarter"], store, real_data["gross_ytd"], real_data["ytd_orders_capped"])
    if tool_name == "log_deductible_expense":
        return _log_deductible_expense(tool_input, store)
    if tool_name == "get_deductions_summary":
        return _get_deductions_summary(tool_input.get("year"), store)
    if tool_name == "check_etsy_compliance":
        return _check_etsy_compliance(real_data["listings"])
    if tool_name == "check_copyright_guidance":
        return _check_copyright_guidance(tool_input["product_concept"])
    if tool_name == "get_1099k_status":
        return _get_1099k_status(real_data["gross_ytd"], real_data["ytd_orders_capped"])
    if tool_name == "get_tax_calendar":
        return _get_tax_calendar()
    return f"Unknown tax compliance tool: {tool_name}"


_YTD_CAP_NOTE = (
    "gross_revenue_ytd is based on the most recent 100 paid orders since Jan 1 (Etsy's "
    "per-call limit) -- this shop has had 100+ orders this year, so actual YTD revenue "
    "is HIGHER than shown here."
)


def _get_tax_overview(store: DataStore, gross_ytd: float, ytd_orders_capped: bool) -> str:
    fin = store.get("financial_data", default={})
    expenses_ytd = sum(e["amount"] for e in fin.get("expenses", [])
                       if e.get("date", "").startswith(str(date.today().year)))
    tax_deductions = sum(e["amount"] for e in store.get("tax_deductions", default=[])
                         if e.get("date", "").startswith(str(date.today().year)))
    etsy_fees_est = gross_ytd * 0.10  # ~10% total Etsy fees
    net_profit = gross_ytd - etsy_fees_est - expenses_ytd - tax_deductions
    se_tax = max(0, net_profit * 0.9235 * SE_TAX_RATE)  # SE deduction applied
    fed_tax = _estimate_federal_tax(net_profit)
    total_est_tax = se_tax + fed_tax

    result = {
        "year": date.today().year,
        "gross_revenue_ytd": round(gross_ytd, 2),
        "estimated_etsy_fees": round(etsy_fees_est, 2),
        "business_expenses_logged": round(expenses_ytd + tax_deductions, 2),
        "estimated_net_profit": round(net_profit, 2),
        "estimated_tax": {
            "self_employment_tax": round(se_tax, 2),
            "federal_income_tax_estimate": round(fed_tax, 2),
            "total_estimated": round(total_est_tax, 2),
            "effective_rate_pct": round(total_est_tax / net_profit * 100, 1) if net_profit > 0 else 0,
        },
        "quarterly_set_aside_recommended": round(total_est_tax / 4, 2),
        "disclaimer": "Estimates only. Consult a CPA for your specific situation.",
    }
    if ytd_orders_capped:
        result["revenue_caveat"] = _YTD_CAP_NOTE
    return json.dumps(result, indent=2)


def _calculate_quarterly_tax(quarter: int, store: DataStore, gross_ytd: float, ytd_orders_capped: bool) -> str:
    quarterly_revenue = gross_ytd / max(quarter, 1)
    quarterly_fees = quarterly_revenue * 0.10
    fin = store.get("financial_data", default={})
    quarterly_expenses = sum(e["amount"] for e in fin.get("expenses", [])) / max(quarter, 1)
    net_quarter = quarterly_revenue - quarterly_fees - quarterly_expenses
    se_tax = max(0, net_quarter * 0.9235 * SE_TAX_RATE)
    fed_tax = _estimate_federal_tax(net_quarter)
    total = se_tax + fed_tax

    due_dates = {1: "April 15", 2: "June 17", 3: "September 16", 4: "January 15 (next year)"}

    result = {
        "quarter": f"Q{quarter} {date.today().year}",
        "due_date": due_dates.get(quarter, ""),
        "estimated_quarterly_revenue": round(quarterly_revenue, 2),
        "estimated_quarterly_net_profit": round(net_quarter, 2),
        "estimated_quarterly_tax": round(total, 2),
        "payment_method": "IRS Direct Pay at irs.gov/payments or EFTPS",
        "disclaimer": "Estimates only. Consult a tax professional.",
    }
    if ytd_orders_capped:
        result["revenue_caveat"] = (
            "Based on YTD revenue capped at the most recent 100 paid orders (Etsy's "
            "per-call limit) -- actual revenue may be higher, which would raise this estimate."
        )
    return json.dumps(result, indent=2)


def _log_deductible_expense(data: dict, store: DataStore) -> str:
    deductions = store.get("tax_deductions", default=[])
    record = {
        "id": f"DED{len(deductions) + 1:04d}",
        "amount": data["amount"],
        "category": data["category"],
        "description": data["description"],
        "receipt_reference": data.get("receipt_reference", ""),
        "date": data.get("date", str(date.today())),
    }
    deductions.append(record)
    store.set(deductions, "tax_deductions")
    store.save()
    return json.dumps({"success": True, "deduction_id": record["id"],
                       "amount": data["amount"], "category": data["category"],
                       "tax_savings_estimate": round(data["amount"] * 0.25, 2),
                       "note": "Estimated savings at 25% effective tax rate."}, indent=2)


def _get_deductions_summary(year: int | None, store: DataStore) -> str:
    year = year or date.today().year
    deductions = [d for d in store.get("tax_deductions", default=[])
                  if d.get("date", "").startswith(str(year))]
    by_cat: dict[str, float] = {}
    for d in deductions:
        c = d.get("category", "other")
        by_cat[c] = round(by_cat.get(c, 0) + d["amount"], 2)
    total = sum(by_cat.values())
    return json.dumps({
        "year": year,
        "total_deductions": round(total, 2),
        "by_category": by_cat,
        "estimated_tax_savings": round(total * 0.25, 2),
        "count": len(deductions),
        "common_deductions_checklist": [
            "Home office (dedicated workspace %)",
            "Computer / equipment depreciation",
            "Software subscriptions (Canva, Adobe, Claude AI)",
            "Filament, paint, and materials",
            "Shipping supplies (boxes, tape, labels)",
            "Etsy fees (already deducted as business expense)",
            "Ad spend (Etsy Ads)",
            "Business education / courses",
        ],
    }, indent=2)


def _check_etsy_compliance(listings: list[dict]) -> str:
    """listings are raw Etsy listing dicts (from EtsyAPIClient.get_shop_listings_all(),
    includes="images") -- NOT the trimmed shape main.py's own _listings_sync() returns,
    which doesn't carry description/images. See main.py's dispatch comment for why this
    is a separate fetch rather than reusing that cache."""
    issues = []
    warnings = []

    for l in listings:
        lid = l.get("listing_id", "?")
        tags = l.get("tags", []) or []
        if len(tags) < 10:
            warnings.append(f"{lid}: Only {len(tags)} tags — use all 13 for best SEO")
        description = l.get("description") or ""
        if len(description) < 100:
            issues.append(f"{lid}: Description too short — Etsy requires complete descriptions")
        images = l.get("images", []) or []
        if len(images) < 3:
            warnings.append(f"{lid}: Only {len(images)} images — 5-10 recommended")

    return json.dumps({
        "listings_checked": len(listings),
        "compliance_issues": issues,
        "warnings": warnings,
        "etsy_policy_checklist": {
            "handmade_only": "Only sell items you make, design, or resell as vintage (20+ yrs)",
            "accurate_descriptions": "Listings must accurately represent the item",
            "no_prohibited_items": "Review Etsy prohibited items list regularly",
            "digital_files_policy": "Digital downloads must be delivered as described",
            "review_solicitation": "Never pay for, exchange for, or coerce reviews",
            "intellectual_property": "Do not use copyrighted characters, logos, or trademarked terms",
            "shop_policies": "Complete return, shipping, and payment policies required",
        },
        "overall_status": "Issues found — address compliance issues immediately" if issues else "Good — address warnings when possible",
    }, indent=2)


def _check_copyright_guidance(concept: str) -> str:
    concept_lower = concept.lower()
    high_risk_terms = ["disney", "marvel", "pokemon", "harry potter", "nintendo", "nike", "gucci",
                       "starbucks", "batman", "star wars", "hello kitty", "snoopy", "minnie", "mickey"]
    medium_risk_terms = ["inspired by", "style of", "like", "similar to", "fan art"]

    risk_level = "LOW"
    flags = []
    for term in high_risk_terms:
        if term in concept_lower:
            risk_level = "HIGH"
            flags.append(f"'{term}' is a protected trademark/copyright — do NOT use")
    for term in medium_risk_terms:
        if term in concept_lower:
            risk_level = max(risk_level, "MEDIUM") if risk_level != "HIGH" else "HIGH"
            flags.append(f"'{term}' implies copying another work — clarify originality")

    guidance = {
        "LOW": "Concept appears original. Create freely. Always use your own original designs.",
        "MEDIUM": "Some risk. Ensure the work is fully original and not derived from copyrighted material.",
        "HIGH": "HIGH RISK — Do NOT create this product. Using protected IP on Etsy results in listing removal and potential legal action.",
    }

    return json.dumps({
        "product_concept": concept,
        "risk_level": risk_level,
        "flags": flags,
        "guidance": guidance[risk_level],
        "safe_alternatives": [
            "Create original characters and artwork from scratch",
            "Use public domain works (pre-1928 in US)",
            "License images from stock sites with commercial use rights",
            "Create 'inspired by era/style' not 'inspired by specific copyrighted work'",
        ],
        "disclaimer": "This is general guidance, not legal advice. Consult an IP attorney for specific situations.",
    }, indent=2)


def _get_1099k_status(gross_ytd: float, ytd_orders_capped: bool) -> str:
    threshold = 600

    result = {
        "current_year": date.today().year,
        "gross_revenue_ytd": round(gross_ytd, 2),
        "1099k_threshold": threshold,
        "will_receive_1099k": gross_ytd >= threshold,
        "explanation": (
            f"Etsy will send you a 1099-K if you receive ${threshold}+ in gross payments this year. "
            "This reports your GROSS revenue to the IRS — not your profit. "
            "You owe tax only on your NET profit (gross minus all expenses and fees)."
            if gross_ytd >= threshold * 0.5
            else f"Currently at ${gross_ytd:.2f} — below the ${threshold} 1099-K threshold for this year."
        ),
        "action": "Keep all expense receipts. The 1099-K amount will be higher than your actual profit.",
    }
    if ytd_orders_capped:
        result["revenue_caveat"] = (
            "gross_revenue_ytd is capped at the most recent 100 paid orders since Jan 1 "
            "(Etsy's per-call limit) -- if this shop has had more than 100 orders this year, "
            "actual revenue is higher, and will_receive_1099k is very likely true regardless."
        )
    return json.dumps(result, indent=2)


def _get_tax_calendar() -> str:
    year = date.today().year
    return json.dumps({
        "tax_deadlines": [
            {"date": f"Jan 15, {year}", "event": "Q4 estimated tax payment due (from prior year)"},
            {"date": f"Jan 31, {year}", "event": "Etsy sends 1099-K forms (if applicable)"},
            {"date": f"Apr 15, {year}", "event": "Federal tax return due + Q1 estimated tax payment"},
            {"date": f"Jun 17, {year}", "event": "Q2 estimated tax payment due"},
            {"date": f"Sep 16, {year}", "event": "Q3 estimated tax payment due"},
            {"date": f"Jan 15, {year + 1}", "event": "Q4 estimated tax payment due"},
        ],
        "year_end_checklist": [
            "Download Etsy shop payment CSV (Shop Manager → Finances → Payment Account)",
            "Gather all receipts for business expenses",
            "Calculate home office deduction if applicable",
            "Log all equipment purchases for depreciation",
            "Verify 1099-K matches your records",
        ],
        "disclaimer": "Dates may vary. Always verify with irs.gov or your tax professional.",
    }, indent=2)


def _estimate_federal_tax(income: float) -> float:
    if income <= 0:
        return 0
    tax = 0
    prev = 0
    for bracket, rate in FEDERAL_BRACKETS:
        if income > bracket:
            tax += (bracket - prev) * rate
            prev = bracket
        else:
            tax += (income - prev) * rate
            break
    else:
        tax += (income - FEDERAL_BRACKETS[-1][0]) * 0.35
    return max(0, tax)
