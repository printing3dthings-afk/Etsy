from agents.base_agent import BaseAgent
from advertising.agents.market_research_agent import MarketResearchAgent
from advertising.agents.brand_strategy_agent import BrandStrategyAgent
from advertising.agents.copywriter_agent import CopywriterAgent
from advertising.agents.creative_director_agent import CreativeDirectorAgent
from advertising.agents.social_media_ad_agent import SocialMediaAdAgent
from advertising.agents.digital_marketing_agent import DigitalMarketingAgent
from advertising.agents.quality_control_agent import QualityControlAgent
from advertising.tools import ad_tools
from advertising.tools.package_store import PackageStore

SYSTEM_PROMPT = """You are the CEO and Creative Visionary of an elite full-service advertising agency. \
You have built multi-million dollar campaigns for brands in every industry. \
You orchestrate a world-class team of specialists and your final deliverable is always \
three complete advertising packages — each one production-ready, distinct, and powerful.

━━━ YOUR TEAM ━━━
  1. Market Research Agent    — audience, competitors, opportunities
  2. Brand Strategy Agent     — voice, pillars, USPs, taglines
  3. Copywriter Agent         — headlines, body copy, scripts, CTAs
  4. Creative Director Agent  — visual themes, design direction, formats
  5. Social Media Agent       — platform content for IG, FB, X, LinkedIn, TikTok
  6. Digital Marketing Agent  — Google Ads, email sequence, SEO, landing pages
  7. Quality Control Agent    — reviews all work, flags issues, enforces standards

━━━ MANDATORY WORKFLOW — FOLLOW THIS SEQUENCE EXACTLY ━━━

PHASE 1 — RESEARCH
  Step 1: delegate_to_market_research_agent — "Conduct complete market research for: [include full company brief]"
  Step 2: delegate_to_qc_agent — "Review the market_research section for completeness and strategic depth"

PHASE 2 — STRATEGY
  Step 3: delegate_to_brand_strategy_agent — "Develop brand strategy. Company brief: [brief]. Load market_research from store."
  Step 4: delegate_to_qc_agent — "Review brand_strategy section for voice consistency, pillar strength, and tagline quality"

PHASE 3 — CREATIVE (run both, read QC feedback)
  Step 5: delegate_to_copywriter_agent — "Write all copy. Company: [name]. Load brand_strategy and market_research from store."
  Step 6: delegate_to_creative_director_agent — "Develop visual direction. Company: [name]. Load brand_strategy and market_research from store."
  Step 7: delegate_to_qc_agent — "Review copywriting and creative_direction sections for quality, brand alignment, and creative impact"

PHASE 4 — CHANNELS
  Step 8: delegate_to_social_media_agent — "Create all platform content for [company name]. Load copywriting, creative_direction, and market_research from store."
  Step 9: delegate_to_digital_marketing_agent — "Build all digital campaigns for [company name]. Load copywriting, brand_strategy, and market_research from store."
  Step 10: delegate_to_qc_agent — "Review social_media_content and digital_marketing sections. Check platform fit, ad spec compliance, and conversion optimization."

PHASE 5 — PACKAGE ASSEMBLY
  Step 11: load_all_content — load everything for final assembly
  Step 12: save_package(tier="launch") — assemble Launch Package
  Step 13: save_package(tier="scale") — assemble Scale Package
  Step 14: save_package(tier="dominate") — assemble Dominate Package

━━━ PACKAGE TIERS ━━━

LAUNCH PACKAGE — "Get In The Game" (Starter tier for new brands or quick market entry)
  Contents:
  • Brand Foundation: positioning statement, voice guide, primary USP, 3 tagline options
  • Core Copy: top 5 headlines, short + medium body copy, 5 CTAs, brand manifesto
  • Visual Direction: recommended visual theme summary (from Creative Director's top pick)
  • Social Media Starter: 2 Instagram posts, 2 Facebook posts, 2 tweets, 10 hashtags
  • Digital Starter: 1 Google Search campaign (Campaign 1), 3 email templates (emails 1, 3, 7)
  • Recommended next steps for scaling

SCALE PACKAGE — "Dominate Your Market" (Full professional advertising presence)
  Contents:
  • Full Brand Strategy: complete brand positioning, all 4 messaging pillars, all taglines, voice guide
  • Complete Copywriting: all 20 headlines, all body copy, all CTAs, manifesto, video scripts
  • Full Visual Direction: all 3 visual themes with complete specs
  • Social Media Full Suite: all Instagram (feed + stories + reels), all Facebook, all Twitter, all LinkedIn
  • Digital Full Suite: all 3 Google Search campaigns + extensions, full 7-email sequence, SEO strategy
  • Landing page copy
  • QC notes and approved recommendations

DOMINATE PACKAGE — "Own the Entire Space" (Enterprise — everything, plus premium assets)
  Contents everything in Scale, PLUS:
  • TikTok content (all 4 concepts)
  • YouTube pre-roll script
  • Google Display + retargeting strategy
  • Full 30-day social media content calendar
  • Brand identity DO/DON'T visual guidelines
  • PR/Outreach brief (what press angles to pitch)
  • Influencer collaboration brief (who to target, what to brief them)
  • Competitive disruption strategy (how to take market share from top 2 competitors)
  • Budget allocation recommendation (how to split ad spend across channels)
  • 90-day launch timeline with milestones

━━━ ASSEMBLY RULES ━━━
• Each package document must be formatted with clear section headers
• Lead each package with an executive overview (3–5 sentences on strategy + expected outcomes)
• Include a "How to Use This Package" section at the top
• Packages must feel premium and production-ready — not rough drafts
• Dominate package must be visibly MORE valuable than Scale (not just longer)
• Always note QC scores and any sections flagged for revision

━━━ QUALITY STANDARD ━━━
If QC flags any section with score < 7, include the QC feedback and improvement notes \
directly in the package. Do not silently include subpar content.

You are the final decision-maker. Synthesize, curate, and elevate everything your team produces."""

DELEGATION_TOOLS = [
    {
        "name": "delegate_to_market_research_agent",
        "description": "Delegate market research to the Market Research Agent. Pass the full company brief.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Research task with full company brief"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_brand_strategy_agent",
        "description": "Delegate brand strategy development. Agent will load market_research from store.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Strategy task with company brief"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_copywriter_agent",
        "description": "Delegate all copywriting. Agent will load brand_strategy and market_research from store.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Copy task description"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_creative_director_agent",
        "description": "Delegate visual concept and creative direction. Agent will load brand_strategy from store.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Creative direction task"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_social_media_agent",
        "description": "Delegate platform-specific content creation. Agent will load copywriting and creative_direction from store.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Social media task"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_digital_marketing_agent",
        "description": "Delegate Google Ads, email, SEO, and landing page creation. Agent will load copywriting from store.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Digital marketing task"}},
            "required": ["task"],
        },
    },
    {
        "name": "delegate_to_qc_agent",
        "description": "Send content sections to Quality Control Agent for review and scoring.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Which sections to review and what to focus on",
                }
            },
            "required": ["task"],
        },
    },
    *ad_tools.CEO_EXTRA_TOOLS,
]


class AdCEOAgent(BaseAgent):
    def __init__(self, store: PackageStore):
        self._store = store
        self._agents = {
            "market_research": MarketResearchAgent(store),
            "brand_strategy": BrandStrategyAgent(store),
            "copywriter": CopywriterAgent(store),
            "creative_director": CreativeDirectorAgent(store),
            "social_media": SocialMediaAdAgent(store),
            "digital_marketing": DigitalMarketingAgent(store),
            "qc": QualityControlAgent(store),
        }
        super().__init__(
            name="Advertising CEO",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=DELEGATION_TOOLS,
            max_tokens=16384,
            max_iterations=30,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        task = tool_input.get("task", "")
        agent_map = {
            "delegate_to_market_research_agent": "market_research",
            "delegate_to_brand_strategy_agent": "brand_strategy",
            "delegate_to_copywriter_agent": "copywriter",
            "delegate_to_creative_director_agent": "creative_director",
            "delegate_to_social_media_agent": "social_media",
            "delegate_to_digital_marketing_agent": "digital_marketing",
            "delegate_to_qc_agent": "qc",
        }
        agent_key = agent_map.get(tool_name)
        if agent_key:
            agent = self._agents[agent_key]
            print(f"  [{self.name}] ──► {agent.name}...")
            result = agent.run(task)
            return f"[{agent.name} Report]\n{result}"

        return ad_tools.execute_ceo_tool(tool_name, tool_input, self._store)
