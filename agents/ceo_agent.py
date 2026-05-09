from agents.base_agent import BaseAgent
from agents.sales_agent import SalesAgent
from agents.product_agent import ProductAgent
from agents.marketing_agent import MarketingAgent
from agents.analytics_agent import AnalyticsAgent
from agents.customer_service_agent import CustomerServiceAgent

SYSTEM_PROMPT = """You are the CEO of OnBrandCraftz (etsy.com/shop/onbrandcraftz), an Etsy shop selling 3D printed home decor and hand painted wood items. This is a PRINT-TO-ORDER business — products are made after orders are placed, so low stock counts (1-2 units) are normal and not a concern. Only sold-out listings (0 units) are urgent inventory issues since they vanish from Etsy search. You oversee a team of specialized agents:

- Sales Agent: Order management, revenue tracking, shipping queue
- Product Agent: Listing management, inventory, pricing
- Marketing Agent: SEO, traffic analysis, promotions, competitor pricing
- Analytics Agent: Full shop dashboard, performance reports, trends
- Customer Service Agent: Customer messages, reviews, satisfaction

Your role:
1. Understand incoming requests and determine which agent(s) should handle them
2. Delegate tasks to the appropriate agent(s) using your delegation tools
3. Synthesize results from multiple agents when needed
4. Provide strategic decisions and recommendations based on agent reports
5. Run a daily briefing when asked, pulling insights from all agents

Delegation guidelines:
- Use Analytics Agent for broad performance questions or dashboard requests
- Use Sales Agent for order/revenue/shipping questions
- Use Product Agent for listing/inventory/pricing questions
- Use Marketing Agent for SEO/promotion/growth questions
- Use Customer Service Agent for message/review questions
- Delegate to multiple agents when a task spans multiple domains
- Always synthesize agent outputs into a clear, executive-level response

Think strategically. You see the whole picture. Make data-driven decisions."""

DELEGATION_TOOLS = [
    {
        "name": "delegate_to_sales_agent",
        "description": "Delegate a sales, orders, revenue, or shipping task to the Sales Agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Clear description of the task for the Sales Agent to perform",
                }
            },
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_product_agent",
        "description": "Delegate a product listings, inventory, or pricing task to the Product Agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Clear description of the task for the Product Agent to perform",
                }
            },
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_marketing_agent",
        "description": "Delegate an SEO, traffic, promotion, or growth task to the Marketing Agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Clear description of the task for the Marketing Agent to perform",
                }
            },
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_analytics_agent",
        "description": "Delegate a reporting, dashboard, or data analysis task to the Analytics Agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Clear description of the task for the Analytics Agent to perform",
                }
            },
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_customer_service_agent",
        "description": "Delegate a customer message, review response, or satisfaction task to the Customer Service Agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Clear description of the task for the Customer Service Agent to perform",
                }
            },
            "required": ["task"],
        },
    },
]


class CEOAgent(BaseAgent):
    def __init__(self):
        self._agents = {
            "sales": SalesAgent(),
            "product": ProductAgent(),
            "marketing": MarketingAgent(),
            "analytics": AnalyticsAgent(),
            "customer_service": CustomerServiceAgent(),
        }
        super().__init__(
            name="CEO Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=DELEGATION_TOOLS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        task = tool_input.get("task", "")
        agent_map = {
            "delegate_to_sales_agent": "sales",
            "delegate_to_product_agent": "product",
            "delegate_to_marketing_agent": "marketing",
            "delegate_to_analytics_agent": "analytics",
            "delegate_to_customer_service_agent": "customer_service",
        }
        agent_key = agent_map.get(tool_name)
        if not agent_key:
            return f"Unknown delegation tool: {tool_name}"

        agent = self._agents[agent_key]
        print(f"  [CEO] -> Delegating to {agent.name}...")
        result = agent.run(task)
        return f"[{agent.name} Report]\n{result}"
