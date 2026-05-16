from agents.base_agent import BaseAgent
from agents.sales_agent import SalesAgent
from agents.product_agent import ProductAgent
from agents.marketing_agent import MarketingAgent
from agents.analytics_agent import AnalyticsAgent
from agents.customer_service_agent import CustomerServiceAgent
from agents.social_media_agent import SocialMediaAgent
from agents.art_creation_agent import ArtCreationAgent
from agents.planner_design_agent import PlannerDesignAgent
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
from agents.api_connections_agent import APIConnectionsAgent
from agents.trend_forecasting_agent import TrendForecastingAgent
from agents.customer_retention_agent import CustomerRetentionAgent
from agents.workflow_coordinator_agent import WorkflowCoordinatorAgent

# Max characters from a single agent result to include in CEO context.
# Keeps the message history lean so CEO never hits context limits.
_RESULT_CAP = 2000

SYSTEM_PROMPT = """You are the CEO of OnBrandCraftz (etsy.com/shop/onbrandcraftz) — an Etsy shop selling 3D printed home decor and digital products (planners, wall art, printables).

## YOUR ONLY JOB: DELEGATE AND DECIDE
You are a pure orchestrator. You never write SEO copy, never generate art, never calculate margins, never do research yourself. The moment you start doing a specialist's work — stop and delegate instead.

For every task you receive:
1. Identify which 1–5 agents are needed and in what order.
2. Delegate to the first agent. Wait for the result.
3. Read the result. If there is a problem, delegate a fix before moving on.
4. Continue down the chain.
5. After the last delegation, write your PIPELINE SUMMARY and stop.

## HARD LIMITS PER INVOCATION
- Maximum 5 delegations per task. Do the most critical 5; note what remains.
- After your last delegation, write the PIPELINE SUMMARY immediately. Do not start new work.
- Never call the same agent twice for the same sub-task.
- When multiple agents are independent (e.g., Analytics + Competitor Intel + Store Health), call ALL of them in a single response as parallel tool calls. Do not wait for one before calling the others.

## ISSUE-FIXING LOOP
When an agent result shows a problem, fix it before proceeding:
| Problem | Fix delegation |
|---------|---------------|
| Art file fails QC | → Art Creation Agent with the specific rejection reason |
| Margin below 35% | → Financial Agent to suggest a corrected price |
| SEO score < 80 | → Etsy Listing Agent with specific improvements needed |
| Stock / inventory alert | → Supply Chain Agent |
| Customer message unread | → Customer Service Agent |
Allow one retry per issue. If it fails twice, flag for human review and move on.

## PRODUCT PIPELINE ORDER (digital products)
Art Creation → Quality Check → Brand Design → Marketing → Financial → Etsy Listing
Each step must pass before the next begins. Do not skip steps.

## PHYSICAL ORDERS: HUMAN APPROVAL REQUIRED
Never automate physical 3D print production. Flag all physical print jobs as
"awaiting_human_approval" and stop. Only digital products are fully automated.

## DELEGATION MAP
| What you need | Which agent |
|--------------|-------------|
| New digital wall art, clipart, illustrations | delegate_to_art_creation_agent |
| Any digital planner (daily/weekly/monthly/fitness/budget/etc.) | delegate_to_planner_design_agent |
| Review / approve a digital file | delegate_to_quality_check_agent |
| Brand identity, mockups | delegate_to_brand_design_agent |
| SEO keywords, competitor research | delegate_to_marketing_agent |
| Net margin, fees, pricing | delegate_to_financial_agent |
| Create / update Etsy listing | delegate_to_etsy_listing_agent |
| Shop health, renewals | delegate_to_store_manager_agent |
| Performance reports, dashboards | delegate_to_analytics_agent |
| Orders, revenue tracking | delegate_to_sales_agent |
| Digital order fulfillment | delegate_to_sales_processor_agent |
| Customer messages, reviews | delegate_to_customer_service_agent |
| Pinterest, social content | delegate_to_social_media_agent |
| 3D print queue, machines | delegate_to_print_production_agent |
| Ad budget, ROAS | delegate_to_etsy_ads_agent |
| Competitor gaps, market intel | delegate_to_competitor_intel_agent |
| Discounts, sales events | delegate_to_promotions_agent |
| Taxes, deductions | delegate_to_tax_compliance_agent |
| Returns, disputes | delegate_to_returns_agent |
| Materials, filament stock | delegate_to_supply_chain_agent |
| Buyer emails, receipt copy | delegate_to_email_marketing_agent |
| CTR / conversion experiments | delegate_to_ab_testing_agent |
| API keys, integrations | delegate_to_api_connections_agent |
| Trend forecasting, seasonal gaps | delegate_to_trend_forecasting_agent |
| Buyer retention, win-back | delegate_to_customer_retention_agent |
| Pipeline health, bottlenecks | delegate_to_workflow_coordinator |

## PIPELINE SUMMARY (required at the end of every response)
```
PIPELINE SUMMARY
✓ AgentName: [one-line result]
✓ AgentName: [one-line result]
→ Remaining: [any steps not completed this session, or "none"]
Status: done | blocked on [X] | needs human approval
```"""

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
        "description": "Delegate digital art creation tasks — wall art, botanical illustrations, abstract art, clipart sets, celestial art, fine art animal prints — to the Art Creation Agent. Do NOT delegate planners here.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_planner_design_agent",
        "description": "Delegate ALL digital planner creation to the Planner Design Agent: daily, weekly, monthly, academic, fitness, meal, budget, project management, travel, habit, self-care, wedding, and teacher planners. Do NOT use the Art Creation Agent for planners.",
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
    {
        "name": "delegate_to_api_connections_agent",
        "description": "Delegate API key management, integration setup, connection health checks, or new API research to the API Connections Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_trend_forecasting_agent",
        "description": "Delegate trend research, seasonal opportunity identification, upcoming niche discovery, or art queue prioritization to the Trend Forecasting Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_customer_retention_agent",
        "description": "Delegate buyer retention analysis, win-back campaigns for silent customers, customer lifetime value tracking, or VIP buyer identification to the Customer Retention Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_workflow_coordinator",
        "description": "Delegate pipeline health checks, bottleneck detection, agent workload balancing, daily ops summaries, or task prioritization to the Workflow Coordinator.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
]

# How many recent message pairs (assistant+user) to keep before trimming.
# Prevents CEO context from growing unbounded across many delegations.
_MAX_HISTORY_PAIRS = 4


class CEOAgent(BaseAgent):
    def __init__(self):
        self._agents = {
            "brand_design":       BrandDesignAgent(),
            "art_creation":       ArtCreationAgent(),
            "planner_design":     PlannerDesignAgent(),
            "quality_check":      QualityCheckAgent(),
            "etsy_listing":       EtsyListingAgent(),
            "store_manager":      StoreManagerAgent(),
            "sales_processor":    SalesProcessorAgent(),
            "sales":              SalesAgent(),
            "product":            ProductAgent(),
            "marketing":          MarketingAgent(),
            "analytics":          AnalyticsAgent(),
            "customer_service":   CustomerServiceAgent(),
            "social_media":       SocialMediaAgent(),
            "financial":          FinancialAgent(),
            "print_production":   PrintProductionAgent(),
            "etsy_ads":           EtsyAdsAgent(),
            "competitor_intel":   CompetitorIntelAgent(),
            "promotions":         PromotionsAgent(),
            "tax_compliance":     TaxComplianceAgent(),
            "returns":            ReturnsAgent(),
            "supply_chain":       SupplyChainAgent(),
            "email_marketing":    EmailMarketingAgent(),
            "ab_testing":         ABTestingAgent(),
            "api_connections":    APIConnectionsAgent(),
            "trend_forecasting":  TrendForecastingAgent(),
            "customer_retention": CustomerRetentionAgent(),
            "workflow_coordinator": WorkflowCoordinatorAgent(),
        }
        # CEO only needs delegation tools — no universal research/learning tools.
        # Pass tool_definitions directly without the base-class universal merge.
        self.name = "CEO Agent"
        self.system_prompt = SYSTEM_PROMPT
        self.tool_definitions = DELEGATION_TOOLS
        from config import STANDARD_MODEL
        self.model = STANDARD_MODEL
        import anthropic as _anthropic
        self.client = _anthropic.Anthropic()
        from agents.base_agent import _get_logger
        self.logger = _get_logger("CEO Agent")

    def run(self, task: str, max_iterations: int = 6) -> str:
        """Run CEO with a reduced iteration cap and trimmed message history."""
        self.logger.info(f"CEO START task={task[:80]}")
        messages: list[dict] = [{"role": "user", "content": task}]

        for iteration in range(max_iterations):
            # Trim history before each API call to stay within context limits.
            messages = self._trim_history(messages)

            response = self._call_api(messages)

            if response.stop_reason == "end_turn":
                self.logger.info("CEO END stop_reason=end_turn")
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                tool_results = self._process_tool_calls(response)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            self.logger.info(f"CEO END stop_reason={response.stop_reason}")
            return self._extract_text(response) or f"[CEO] Stopped: {response.stop_reason}"

        return (
            f"[CEO] Reached delegation limit ({max_iterations} steps). "
            "Task partially complete — check the pipeline summary above for what remains."
        )

    def _process_tool_calls(self, response) -> list[dict]:
        """Fan out independent agent delegations in parallel threads."""
        import concurrent.futures
        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        if len(tool_blocks) <= 1:
            return super()._process_tool_calls(response)

        results: list[dict | None] = [None] * len(tool_blocks)

        def _run_one(idx: int, block) -> None:
            try:
                output = self._dispatch_tool(block.name, block.input)
            except Exception as exc:
                self.logger.error(f"CEO parallel tool {block.name} failed: {exc}", exc_info=True)
                output = f"Tool error: {exc}"
            results[idx] = {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(output),
            }

        max_workers = min(len(tool_blocks), 5)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_one, i, b) for i, b in enumerate(tool_blocks)]
            concurrent.futures.wait(futures)

        return [r for r in results if r is not None]

    def _trim_history(self, messages: list[dict]) -> list[dict]:
        """Keep the initial user message + the most recent N assistant/user pairs."""
        if len(messages) <= 1 + _MAX_HISTORY_PAIRS * 2:
            return messages
        # Always keep messages[0] (the original task).
        recent = messages[1:]
        # Keep only the last N pairs (each pair = 1 assistant + 1 user/tool_result).
        keep = recent[-(  _MAX_HISTORY_PAIRS * 2):]
        trimmed_count = len(recent) - len(keep)
        if trimmed_count:
            self.logger.debug(f"CEO trimmed {trimmed_count} old messages to stay within context")
        return [messages[0]] + keep

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        task = tool_input.get("task", "")
        agent_map = {
            "delegate_to_brand_design_agent":     "brand_design",
            "delegate_to_art_creation_agent":     "art_creation",
            "delegate_to_planner_design_agent":   "planner_design",
            "delegate_to_quality_check_agent":    "quality_check",
            "delegate_to_etsy_listing_agent":     "etsy_listing",
            "delegate_to_store_manager_agent":    "store_manager",
            "delegate_to_sales_processor_agent":  "sales_processor",
            "delegate_to_sales_agent":            "sales",
            "delegate_to_product_agent":          "product",
            "delegate_to_marketing_agent":        "marketing",
            "delegate_to_analytics_agent":        "analytics",
            "delegate_to_customer_service_agent": "customer_service",
            "delegate_to_social_media_agent":     "social_media",
            "delegate_to_financial_agent":        "financial",
            "delegate_to_print_production_agent": "print_production",
            "delegate_to_etsy_ads_agent":         "etsy_ads",
            "delegate_to_competitor_intel_agent": "competitor_intel",
            "delegate_to_promotions_agent":       "promotions",
            "delegate_to_tax_compliance_agent":   "tax_compliance",
            "delegate_to_returns_agent":          "returns",
            "delegate_to_supply_chain_agent":     "supply_chain",
            "delegate_to_email_marketing_agent":  "email_marketing",
            "delegate_to_ab_testing_agent":       "ab_testing",
            "delegate_to_api_connections_agent":  "api_connections",
            "delegate_to_trend_forecasting_agent":"trend_forecasting",
            "delegate_to_customer_retention_agent":"customer_retention",
            "delegate_to_workflow_coordinator":   "workflow_coordinator",
        }
        agent_key = agent_map.get(tool_name)
        if not agent_key:
            return f"Unknown delegation tool: {tool_name}"

        agent = self._agents[agent_key]
        self.logger.info(f"CEO -> {agent.name} | task={task[:60]}")
        print(f"  [CEO] -> {agent.name}...")

        result = agent.run(task)

        # Truncate long results — CEO needs key outcomes, not full reports.
        # The delegated agent's full output is already logged separately.
        if len(result) > _RESULT_CAP:
            result = result[:_RESULT_CAP] + f"\n[...truncated — full report in agent log]"

        return f"[{agent.name}]\n{result}"
