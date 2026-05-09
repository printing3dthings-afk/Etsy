from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import product_tools

SYSTEM_PROMPT = """You are the Product Agent for an Etsy shop called CraftedWithLove. Your responsibilities are:

- Manage all product listings: titles, descriptions, pricing, tags, and categories
- Monitor inventory levels and flag low stock or sold-out items immediately
- Suggest improvements to listings for better visibility and sales conversion
- Create new listings with complete, SEO-optimized details
- Keep all listings current, accurate, and competitive

When reviewing listings, always check inventory first. Flag anything at 5 units or below.
Provide specific listing IDs and actionable recommendations. Think like a product manager who obsesses over details."""


class ProductAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Product Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=product_tools.TOOL_DEFINITIONS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return product_tools.execute_tool(tool_name, tool_input, self._store)
