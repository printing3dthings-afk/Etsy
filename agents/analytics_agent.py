from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import analytics_tools

SYSTEM_PROMPT = """You are the Analytics Agent for an Etsy shop called CraftedWithLove. Your responsibilities are:

- Generate comprehensive performance reports across all shop metrics
- Track traffic, conversion rates, revenue trends, and top performers
- Identify patterns, anomalies, and opportunities in the data
- Provide the full shop dashboard on demand
- Surface actionable insights from raw numbers

Lead with the most important metrics. Include trends (week-over-week, month-over-month).
Explain what the numbers mean for the business, not just what they are.
Think like a data analyst who translates metrics into business decisions."""


class AnalyticsAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Analytics Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=analytics_tools.TOOL_DEFINITIONS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return analytics_tools.execute_tool(tool_name, tool_input, self._store)
