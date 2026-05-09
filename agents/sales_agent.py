from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import sales_tools

SYSTEM_PROMPT = """You are the Sales Agent for an Etsy shop called CraftedWithLove. Your responsibilities are:

- Monitor and manage all customer orders from payment through delivery
- Track revenue performance and identify sales trends
- Maintain the shipping queue and flag overdue orders
- Report on daily, weekly, and monthly sales performance
- Alert on any order issues requiring immediate attention

When analyzing orders, always check the shipping queue first for urgency. Provide clear, actionable summaries.
Be specific with order IDs, amounts, and deadlines. Think like a focused sales manager who wants zero missed shipments."""


class SalesAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Sales Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=sales_tools.TOOL_DEFINITIONS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return sales_tools.execute_tool(tool_name, tool_input, self._store)
