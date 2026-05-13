from agents.base_agent import BaseAgent
from agents.sales_agent import SalesAgent
from agents.product_agent import ProductAgent
from agents.marketing_agent import MarketingAgent
from agents.analytics_agent import AnalyticsAgent
from agents.customer_service_agent import CustomerServiceAgent
from agents.social_media_agent import SocialMediaAgent
from agents.art_creation_agent import ArtCreationAgent
from agents.quality_check_agent import QualityCheckAgent
from agents.etsy_listing_agent import EtsyListingAgent
from agents.store_manager_agent import StoreManagerAgent
from agents.sales_processor_agent import SalesProcessorAgent
from agents.brand_design_agent import BrandDesignAgent
from agents.financial_agent import FinancialAgent
from agents.print_production_agent import PrintProductionAgent
from agents.etsy_ads_agent import EtsyAdsAgent
from agents.competitor_intel_agent import CompetitorIntelAgent
from agents.promotions_agent import PromotionsAgent
from agents.tax_compliance_agent import TaxComplianceAgent
from agents.returns_agent import ReturnsAgent
from agents.supply_chain_agent import SupplyChainAgent
from agents.email_marketing_agent import EmailMarketingAgent
from agents.ab_testing_agent import ABTestingAgent

SYSTEM_PROMPT = """You are the CEO of OnBrandCraftz (etsy.com/shop/onbrandcraftz) — an Etsy shop selling 3D printed home decor, hand painted wood items, AND digital products (planners, wall art, printables). Your single overriding objective is maximum net profit. Every delegation, every decision, every priority must be measured against: does this make the shop more money?

## PRIMARY MISSION: PROFIT MAXIMIZATION
- Revenue without profit is vanity. Always think: net margin after Etsy fees, COGS, and time.
- Digital products are your highest-margin category (near-zero COGS, unlimited sales). Prioritize their pipeline.
- A well-optimized listing earns more than a new listing. Daily listing review is non-negotiable.
- Data drives decisions. If you don't know the conversion rate of a listing, find out before acting.

## FULFILLMENT MODELS
- Physical (3D printed, hand painted): made-to-order, low stock (1-2) is normal
- Digital: instant download, 999 units, delivered via email — highest margin, no shipping, no materials

## YOUR 22-AGENT TEAM

**Digital Product Pipeline (highest profit priority):**
- Brand Design Agent: brand identity, logo, banner, mockups, thumbnail optimization for CTR
- Art Creation Agent: world-class digital art (DALL-E 3 HD) and premium PDF planners
- Quality Check Agent: ruthless gatekeeper — only top-1% Etsy quality passes
- Etsy Listing Agent: SEO-optimized listings + daily audit of ALL existing listings
- Store Manager Agent: shop health, renewals, daily performance audit
- Sales Processor Agent: instant digital file delivery after purchase

**Shop Operations:**
- Sales Agent: order tracking, revenue reporting, shipping queue
- Product Agent: physical listing management, inventory, pricing optimization
- Marketing Agent: Etsy SEO research, keyword intelligence, competitor analysis
- Analytics Agent: profitability dashboard, per-listing metrics, trend identification
- Customer Service Agent: reviews, messages, Star Seller maintenance
- Social Media Agent: Pinterest traffic, content calendar, organic reach

**Business Infrastructure:**
- Financial Agent: net profit per listing, fee breakdowns, margin alerts, P&L
- Print Production Agent: print queue, machine uptime, filament cost tracking
- Etsy Ads Agent: ROAS optimization, promoted listing ROI, ad budget allocation
- Competitor Intel Agent: market gaps, competitor pricing, trend forecasting
- Promotions Agent: strategic discounts, sales events, bundle pricing
- Tax Compliance Agent: quarterly estimates, deductions, expense tracking
- Returns & Disputes Agent: refund management, Star Seller protection
- Supply Chain Agent: materials inventory, filament stock, supplier costs
- Email Marketing Agent: buyer follow-up, receipt copy, repeat purchase campaigns
- A/B Testing Agent: systematic CTR and conversion experiments

## MANDATORY PRE-LISTING REVIEW PIPELINE
No product goes live until ALL of these steps are complete — in order:
1. **Art Creation Agent** — generates premium asset (DALL-E 3 HD or multi-page planner PDF)
2. **Quality Check Agent** — visual review + technical specs; must APPROVE (not just pass)
3. **Brand Design Agent** — confirms product fits brand identity + provides mockup image
4. **Marketing Agent** — keyword research: identifies top 3 search terms for this product type
5. **Financial Agent** — calculates net margin: price must yield ≥ 35% net after all fees
6. **Etsy Listing Agent** — writes optimized title (140 chars, keyword-first), 13 tags, full description
7. **CEO (you)** — final sign-off: does this listing meet premium standards AND margin target?

Reject and recycle any step that doesn't pass. A mediocre listing hurts search ranking for every other listing in the shop.

## DAILY LISTING REVIEW WORKFLOW (run every day)
This is your most important recurring task. Execute in this order:
1. **Analytics Agent** — pull per-listing views, favorites, conversion rate, revenue (last 7 days)
2. **Marketing Agent** — run SEO audit on all active listings; flag titles/tags below best-practice score
3. **Etsy Listing Agent** — generate optimized replacements for any listing scoring < 80/100 on SEO audit
4. **Store Manager Agent** — check renewal alerts, sold-out flags, listing health score
5. **Financial Agent** — flag any listing with net margin < 25% for repricing or removal
6. **CEO (you)** — approve updates, push changes, report summary of improvements made

Target: zero listings with suboptimal titles, missing tags, or below-margin pricing.

## DELEGATION RULES
- Multi-step tasks → delegate each step sequentially, wait for each result before proceeding
- Parallel-safe tasks (Analytics + Marketing research) → delegate simultaneously
- Never approve a product for listing without the full 7-step pipeline above
- Never skip Financial Agent review — every listing must have a confirmed margin
- When a listing underperforms → Marketing + A/B Testing before giving up on it

## DELEGATION MAP
- Brand/identity/mockups → Brand Design Agent
- New digital product creation → Art Creation Agent
- QC and file approval → Quality Check Agent
- Listing creation + SEO audit + listing updates → Etsy Listing Agent
- Shop health, renewals, announcements → Store Manager Agent
- Digital file delivery → Sales Processor Agent
- Physical orders, shipping → Sales Agent
- Physical inventory, pricing → Product Agent
- SEO research, keyword intel, traffic → Marketing Agent
- Performance reports, dashboards, trends → Analytics Agent
- Customer messages, review responses → Customer Service Agent
- Pinterest, social content → Social Media Agent
- Net profit, margins, fees, P&L → Financial Agent
- 3D print queue, machines, filament → Print Production Agent
- Ad budget, ROAS, promoted listings → Etsy Ads Agent
- Competitor research, market gaps → Competitor Intel Agent
- Discounts, sales events, coupons → Promotions Agent
- Taxes, deductions, compliance → Tax Compliance Agent
- Returns, refunds, disputes → Returns & Disputes Agent
- Materials, suppliers, purchase orders → Supply Chain Agent
- Receipt messages, buyer emails, newsletters → Email Marketing Agent
- CTR/conversion experiments → A/B Testing Agent

## DAILY BRIEFING (run every morning)
1. Revenue last 24h + week-over-week trend (Analytics)
2. New orders needing action (Sales + Print Production)
3. Digital product pipeline status — what's in queue, what's blocked (Art + QC + Listing)
4. Listings flagged from last night's SEO audit (Marketing + Listing Agent)
5. Profit alert — any listing now below margin floor (Financial)
6. Unread messages/reviews needing response (Customer Service)
7. Open disputes (Returns Agent)
8. Top growth opportunity today (Competitor Intel)

## EFFICIENCY RULES
- Delegate, don't repeat. If Analytics already pulled data, pass it to Marketing — don't pull again.
- Cache results. If you've run a competitor report today, use those results all day.
- Time-box each agent run. If a task takes > 3 tool calls and produces no output, escalate.
- Quality over quantity. One excellent $8 planner that converts at 4% beats five mediocre $3 downloads at 0.5%.

You see the whole picture. Every decision is measured in dollars of net profit."""

DELEGATION_TOOLS = [
    # ── Digital Product Pipeline ─────────────────────────────────────────────
    {
        "name": "delegate_to_brand_design_agent",
        "description": "Delegate brand identity, logo, banner, mockup, or visual identity tasks to the Brand Design Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_art_creation_agent",
        "description": "Delegate digital art creation, concept design, or planner generation to the Art Creation Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_quality_check_agent",
        "description": "Delegate digital file review, QC approval, or rejection to the Quality Check Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_etsy_listing_agent",
        "description": "Delegate Etsy listing creation, SEO content, pricing research, or publishing to the Etsy Listing Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_store_manager_agent",
        "description": "Delegate shop health checks, announcements, renewal alerts, or performance reports to the Store Manager Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_sales_processor_agent",
        "description": "Delegate digital order fulfillment, email delivery, or delivery tracking to the Sales Processor Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    # ── Shop Operations ──────────────────────────────────────────────────────
    {
        "name": "delegate_to_sales_agent",
        "description": "Delegate physical order management, revenue tracking, or shipping queue tasks to the Sales Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_product_agent",
        "description": "Delegate physical product listings, inventory, or pricing tasks to the Product Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_marketing_agent",
        "description": "Delegate SEO, traffic analysis, promotion, or growth tasks to the Marketing Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_analytics_agent",
        "description": "Delegate reporting, dashboard, or data analysis tasks to the Analytics Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_customer_service_agent",
        "description": "Delegate customer messages, review responses, or satisfaction tasks to the Customer Service Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_social_media_agent",
        "description": "Delegate Pinterest strategy, content calendar, or pin scheduling to the Social Media Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    # ── Business Infrastructure ──────────────────────────────────────────────
    {
        "name": "delegate_to_financial_agent",
        "description": "Delegate profit/loss analysis, fee calculations, COGS, cash flow, or pricing margin tasks to the Financial Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_print_production_agent",
        "description": "Delegate 3D print job queue management, machine status, filament tracking, or failure analysis to the Print Production Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_etsy_ads_agent",
        "description": "Delegate Etsy ad budget management, ROAS analysis, promoted listings, or ad strategy to the Etsy Ads Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_competitor_intel_agent",
        "description": "Delegate competitor research, market gap analysis, seasonal trends, or pricing intelligence to the Competitor Intel Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_promotions_agent",
        "description": "Delegate sales events, coupon codes, discount strategy, or seasonal promotion planning to the Promotions Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_tax_compliance_agent",
        "description": "Delegate quarterly tax estimates, deduction tracking, copyright compliance checks, or expense logging to the Tax Compliance Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_returns_agent",
        "description": "Delegate return requests, refund processing, Etsy dispute cases, or Star Seller protection to the Returns & Disputes Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_supply_chain_agent",
        "description": "Delegate materials inventory, filament stock levels, supplier management, or purchase orders to the Supply Chain Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_email_marketing_agent",
        "description": "Delegate receipt message copy, buyer message templates, newsletter drafting/sending, subscriber list, or package insert copy to the Email Marketing Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_ab_testing_agent",
        "description": "Delegate A/B tests on listing titles, photos, prices, descriptions, or tags to improve click-through and conversion rates.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
]


class CEOAgent(BaseAgent):
    def __init__(self):
        self._agents = {
            # Digital Product Pipeline
            "brand_design": BrandDesignAgent(),
            "art_creation": ArtCreationAgent(),
            "quality_check": QualityCheckAgent(),
            "etsy_listing": EtsyListingAgent(),
            "store_manager": StoreManagerAgent(),
            "sales_processor": SalesProcessorAgent(),
            # Shop Operations
            "sales": SalesAgent(),
            "product": ProductAgent(),
            "marketing": MarketingAgent(),
            "analytics": AnalyticsAgent(),
            "customer_service": CustomerServiceAgent(),
            "social_media": SocialMediaAgent(),
            # Business Infrastructure
            "financial": FinancialAgent(),
            "print_production": PrintProductionAgent(),
            "etsy_ads": EtsyAdsAgent(),
            "competitor_intel": CompetitorIntelAgent(),
            "promotions": PromotionsAgent(),
            "tax_compliance": TaxComplianceAgent(),
            "returns": ReturnsAgent(),
            "supply_chain": SupplyChainAgent(),
            "email_marketing": EmailMarketingAgent(),
            "ab_testing": ABTestingAgent(),
        }
        super().__init__(
            name="CEO Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=DELEGATION_TOOLS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        task = tool_input.get("task", "")
        agent_map = {
            "delegate_to_brand_design_agent": "brand_design",
            "delegate_to_art_creation_agent": "art_creation",
            "delegate_to_quality_check_agent": "quality_check",
            "delegate_to_etsy_listing_agent": "etsy_listing",
            "delegate_to_store_manager_agent": "store_manager",
            "delegate_to_sales_processor_agent": "sales_processor",
            "delegate_to_sales_agent": "sales",
            "delegate_to_product_agent": "product",
            "delegate_to_marketing_agent": "marketing",
            "delegate_to_analytics_agent": "analytics",
            "delegate_to_customer_service_agent": "customer_service",
            "delegate_to_social_media_agent": "social_media",
            "delegate_to_financial_agent": "financial",
            "delegate_to_print_production_agent": "print_production",
            "delegate_to_etsy_ads_agent": "etsy_ads",
            "delegate_to_competitor_intel_agent": "competitor_intel",
            "delegate_to_promotions_agent": "promotions",
            "delegate_to_tax_compliance_agent": "tax_compliance",
            "delegate_to_returns_agent": "returns",
            "delegate_to_supply_chain_agent": "supply_chain",
            "delegate_to_email_marketing_agent": "email_marketing",
            "delegate_to_ab_testing_agent": "ab_testing",
        }
        agent_key = agent_map.get(tool_name)
        if not agent_key:
            return f"Unknown delegation tool: {tool_name}"

        agent = self._agents[agent_key]
        print(f"  [CEO] -> Delegating to {agent.name}...")
        result = agent.run(task)
        return f"[{agent.name} Report]\n{result}"
