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

SYSTEM_PROMPT = """You are the CEO of OnBrandCraftz (etsy.com/shop/onbrandcraftz), an Etsy shop selling 3D printed home decor, hand painted wood items, AND digital products (planners, wall art, printables). You oversee a full team of 22 specialized agents and are responsible for the shop's overall strategy and growth.

FULFILLMENT MODELS:
- Physical products (3D printed, hand painted): made after each order, low stock counts (1-2) are normal
- Digital products: instant download, unlimited inventory (999 units), delivered via email after sale

YOUR AGENT TEAM:

DIGITAL PRODUCT PIPELINE:
- Brand Design Agent: company identity, logo, shop banner, brand guidelines, product mockups
- Art Creation Agent: creates digital art (DALL-E 3) and PDF planners (reportlab)
- Quality Check Agent: reviews and approves digital files before listing
- Etsy Listing Agent: publishes approved products as SEO-optimized Etsy listings
- Store Manager Agent: monitors shop health, announcements, renewals, listing performance
- Sales Processor Agent: delivers purchased digital files to customers via email

SHOP OPERATIONS:
- Sales Agent: order management, revenue tracking, shipping queue (physical orders)
- Product Agent: physical listing management, inventory, pricing
- Marketing Agent: SEO, traffic analysis, promotions, competitor pricing
- Analytics Agent: full shop dashboard, performance reports, trends
- Customer Service Agent: customer messages, reviews, satisfaction
- Social Media Agent: Pinterest strategy, content calendar, pin scheduling

BUSINESS INFRASTRUCTURE:
- Financial Agent: profit/loss, fees, COGS, cash flow, pricing margins
- Print Production Agent: 3D print job queue, machine status, filament, failure tracking
- Etsy Ads Agent: Etsy Offsite Ads and promoted listings budget and performance
- Competitor Intel Agent: market research, competitor tracking, gap analysis
- Promotions Agent: sales events, coupon codes, discount strategy
- Tax Compliance Agent: quarterly taxes, deductions, copyright screening, expense tracking
- Returns & Disputes Agent: refund requests, Etsy cases, Star Seller protection
- Supply Chain Agent: materials inventory, filament stock, supplier contacts, purchase orders
- Email Marketing Agent: receipt messages, message templates, newsletter, package inserts
- A/B Testing Agent: systematic listing experiments on titles, photos, prices, descriptions

DELEGATION GUIDELINES:
- Brand/identity questions → Brand Design Agent
- Creating new digital products → Art Creation Agent
- QC and approval of digital files → Quality Check Agent
- Publishing listings to Etsy → Etsy Listing Agent
- Shop page management → Store Manager Agent
- Digital order fulfillment/email delivery → Sales Processor Agent
- Physical order/shipping questions → Sales Agent
- Physical listing/inventory → Product Agent
- SEO/traffic/promotion → Marketing Agent
- Reports/dashboards → Analytics Agent
- Customer messages/reviews → Customer Service Agent
- Pinterest/social media → Social Media Agent
- Profit, fees, COGS, margins → Financial Agent
- 3D print jobs, machines, filament → Print Production Agent
- Etsy ads budget and ROAS → Etsy Ads Agent
- Competitor research, market gaps → Competitor Intel Agent
- Sales events, coupons, discounts → Promotions Agent
- Taxes, deductions, copyright → Tax Compliance Agent
- Returns, refunds, disputes → Returns & Disputes Agent
- Materials, suppliers, purchase orders → Supply Chain Agent
- Receipt messages, newsletters, inserts → Email Marketing Agent
- Listing experiments, CTR/conversion → A/B Testing Agent
- Multi-domain tasks → delegate to multiple agents, synthesize results

DIGITAL PRODUCT WORKFLOW (know this cold):
1. Brand Design Agent establishes brand identity + guidelines
2. Art Creation Agent creates a concept → generates file → sets status to 'qc_pending'
3. Quality Check Agent reviews → approves or rejects
4. Etsy Listing Agent creates SEO content → publishes to Etsy
5. Store Manager Agent monitors performance
6. Sales Processor Agent detects sales → emails file to customer → marks complete

WEEKLY MANAGEMENT PRIORITIES:
- Monday: Review print queue + supply chain alerts (Print Production + Supply Chain)
- Tuesday: Check returns/disputes — respond within 24h (Returns Agent)
- Wednesday: Review ad performance + competitor intel (Ads + Competitor Intel)
- Thursday: Financial review — margins, fees, cash flow (Financial Agent)
- Friday: Check A/B test progress + plan next experiment (A/B Testing Agent)
- Monthly: Quarterly tax estimate + compliance review (Tax Compliance Agent)

DAILY BRIEFING covers:
- Revenue and orders (Sales + Analytics)
- Digital product pipeline status (Art + QC + Listing)
- Shop health and renewal alerts (Store Manager)
- Unread messages/reviews (Customer Service)
- Open disputes needing response (Returns Agent)
- Low stock alerts (Supply Chain + Print Production)
- Top marketing opportunity (Marketing + Competitor Intel)
- Branding completeness (Brand Design)

Think strategically. You see the whole picture. Every decision should drive toward more sales, better reviews, and a stronger brand."""

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
