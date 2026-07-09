from agents.base_agent import BaseAgent
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Supervisor Agent for OnBrandCraftz. Your only job is task recovery.

When given a stuck task, output a simplified 1-sentence version that:
- Keeps the core goal
- Removes any part that may have caused the stall (excessive scope, missing context, chained steps)
- Is clear and actionable for the agent

If the task requires data that doesn't exist, or is fundamentally broken, reply with exactly: SKIP

Reply with ONLY the simplified task text or SKIP. No explanation, no preamble."""


class SupervisorAgent(BaseAgent):
    """Lightweight agent that simplifies stuck tasks for retry."""

    def __init__(self):
        super().__init__(
            name="Supervisor Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=[],
            model=FAST_MODEL,
        )

    def simplify_task(self, agent_key: str, task: str, elapsed_s: int) -> str:
        prompt = (
            f"Agent '{agent_key}' stalled after {elapsed_s}s on this task:\n\n"
            f"{task}\n\n"
            "Write a simplified 1-sentence retry version, or reply SKIP."
        )
        return self.run(prompt).strip()
