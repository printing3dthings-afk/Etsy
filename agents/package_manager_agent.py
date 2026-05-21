from agents.base_agent import BaseAgent
from tools.client_tools import MANAGER_DIRECT_TOOLS, execute_shared_tool

SYSTEM_PROMPT = """You are the Package Manager for a small business marketing agency.
You are the orchestrator — you know every client's package tier and what they are owed
each month, and you coordinate the full delivery workflow by delegating to specialized agents.

PACKAGE ENTITLEMENTS

starter ($299/mo):
  - 12 social media posts (copywriter)
  - 1 email newsletter (copywriter)
  - 1 initial audit report (audit agent) — first month only, then quarterly
  - Monthly performance report (report agent)

growth ($599/mo):
  - 20 social media posts (copywriter)
  - 2 email newsletters (copywriter)
  - 1 audit report (audit agent) — first month only, then quarterly
  - Keyword research + SEO report (SEO agent)
  - Monthly performance report (report agent)

pro ($1,199/mo):
  - 30 social media posts (copywriter)
  - 4 email newsletters (copywriter)
  - Ad copy — Facebook + Google (copywriter)
  - 1 audit report (audit agent) — first month only, then quarterly
  - Full SEO report with 90-day plan (SEO agent)
  - Weekly performance reports (report agent)

YOUR RESPONSIBILITIES

1. When asked to run a monthly workflow for a client:
   a. Load their profile to confirm package tier
   b. Explain exactly what will be produced
   c. Delegate to each agent in order: audit (if due) → SEO → copywriter → report
   d. Report completion status after each delegation

2. When asked which clients need attention:
   a. List all clients and their package tiers
   b. Flag which deliverables are due this month

3. When asked about a specific client:
   a. Load their profile
   b. Summarize their package, what's been delivered, and what's outstanding

4. When asked to onboard a new client:
   a. Delegate to the intake agent

DELEGATION RULES
- Always load the client profile before delegating — you need the package tier
- Delegate one agent at a time and wait for results before proceeding
- If a client needs something outside their package, flag it and ask the user
- Keep the client's goals front of mind in every delegation task

Be direct, organized, and efficient. You keep the business running on time."""

DELEGATION_TOOLS = [
    {
        "name": "load_client_profile",
        "description": "Load a client profile to check their package tier and details.",
        "input_schema": {
            "type": "object",
            "properties": {"client_id": {"type": "string", "description": "The client's slug ID"}},
            "required": ["client_id"],
        },
    },
    {
        "name": "list_clients",
        "description": "List all clients and their package tiers.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "delegate_to_intake_agent",
        "description": "Delegate a client onboarding or profile update task to the Client Intake Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Task for the Intake Agent"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_audit_agent",
        "description": "Delegate a digital presence audit task to the Audit Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Task for the Audit Agent"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_seo_agent",
        "description": "Delegate keyword research or SEO strategy work to the SEO Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Task for the SEO Agent"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_copywriter_agent",
        "description": "Delegate content creation (social posts, newsletters, ad copy) to the Copywriter Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Task for the Copywriter Agent"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_report_agent",
        "description": "Delegate monthly or weekly report generation to the Report Agent.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Task for the Report Agent"}},
            "required": ["task"],
        },
    },
]

_AGENT_MAP = {
    "delegate_to_intake_agent": "intake",
    "delegate_to_audit_agent": "audit",
    "delegate_to_seo_agent": "seo",
    "delegate_to_copywriter_agent": "copy",
    "delegate_to_report_agent": "report",
}


class PackageManagerAgent(BaseAgent):
    def __init__(self):
        # Import here to avoid circular imports at module load time
        from agents.client_intake_agent import ClientIntakeAgent
        from agents.audit_agent import AuditAgent
        from agents.seo_agent import SEOAgent
        from agents.copywriter_agent import CopywriterAgent
        from agents.report_agent import ReportAgent

        self._agents = {
            "intake": ClientIntakeAgent(),
            "audit": AuditAgent(),
            "seo": SEOAgent(),
            "copy": CopywriterAgent(),
            "report": ReportAgent(),
        }
        super().__init__(
            name="Package Manager",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=DELEGATION_TOOLS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name in ("load_client_profile", "list_clients"):
            return execute_shared_tool(tool_name, tool_input)

        agent_key = _AGENT_MAP.get(tool_name)
        if not agent_key:
            return f"Unknown tool: {tool_name}"

        agent = self._agents[agent_key]
        task = tool_input.get("task", "")
        print(f"  [Package Manager] -> Delegating to {agent.name}...")
        result = agent.run(task)
        return f"[{agent.name}]\n{result}"
