from agents.base_agent import BaseAgent
from advertising.agents.market_research_agent import MarketResearchAgent
from advertising.agents.brand_strategy_agent import BrandStrategyAgent
from advertising.agents.copywriter_agent import CopywriterAgent
from advertising.agents.creative_director_agent import CreativeDirectorAgent
from advertising.agents.social_media_ad_agent import SocialMediaAdAgent
from advertising.agents.digital_marketing_agent import DigitalMarketingAgent
from advertising.agents.web_design_agent import WebDesignAgent
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
  7. Web Design Agent         — fully functional HTML/CSS/JS websites (landing page + full site)
  8. Quality Control Agent    — reviews all work, flags issues, enforces standards

━━━ MANDATORY WORKFLOW — FOLLOW THIS SEQUENCE EXACTLY ━━━

PHASE 1 — RESEARCH
  Step 1: delegate_to_market_research_agent — "Conduct complete market research for: [include full company brief]"
  Step 2: delegate_to_qc_agent — "Review the market_research section for completeness and strategic depth"

PHASE 2 — STRATEGY
  Step 3: delegate_to_brand_strategy_agent — "Develop brand strategy. Company brief: [brief]. Load market_research from store."
  Step 4: delegate_to_qc_agent — "Review brand_strategy section for voice consistency, pillar strength, and tagline quality"

PHASE 3 — CREATIVE
  Step 5: delegate_to_copywriter_agent — "Write all copy. Company: [name]. Load brand_strategy and market_research from store."
  Step 6: delegate_to_creative_director_agent — "Develop visual direction. Company: [name]. Load brand_strategy and market_research from store."
  Step 7: delegate_to_qc_agent — "Review copywriting and creative_direction sections for quality, brand alignment, and creative impact"

PHASE 4 — CHANNELS
  Step 8: delegate_to_social_media_agent — "Create all platform content for [company name]. Load copywriting, creative_direction, and market_research from store."
  Step 9: delegate_to_digital_marketing_agent — "Build all digital campaigns for [company name]. Load copywriting, brand_strategy, and market_research from store."
  Step 10: delegate_to_qc_agent — "Review social_media_content and digital_marketing sections. Check platform fit, ad spec compliance, and conversion optimization."

PHASE 5 — WEB DESIGN
  Step 11: delegate_to_web_design_agent — "Build a complete website for [company name]. Load brand_strategy, copywriting, and creative_direction from the store. Produce both the conversion landing page and the full multi-section website."
  Step 12: delegate_to_qc_agent — "Review website_landing_page and website_full sections. Verify: real brand copy used (no lorem ipsum), all required sections present, CTAs are strong and specific, color palette reflects creative_direction, HTML is complete and well-structured."

PHASE 6 — PACKAGE ASSEMBLY
  Step 13: load_all_content — load everything for final assembly
  Step 14: save_package(tier="launch") — assemble Launch Package
  Step 15: save_package(tier="scale") — assemble Scale Package
  Step 16: save_package(tier="dominate") — assemble Dominate Package

━━━ PACKAGE TIERS ━━━

LAUNCH PACKAGE — "Get In The Game" (Starter tier — fast market entry)
  • Brand Foundation: positioning statement, voice guide, primary USP, 3 tagline options
  • Core Copy: top 5 headlines, short + medium body copy, 5 CTAs, brand manifesto
  • Visual Direction: recommended theme summary (Creative Director's top pick with key specs)
  • Social Media Starter: 2 Instagram posts, 2 Facebook posts, 2 tweets, 2 LinkedIn posts, 10 hashtags
  • Digital Starter: Google Search Campaign 1 (brand awareness), email sequences 1+3+7
  • Website: Conversion landing page (website_landing_page — production-ready HTML file)
  • Recommended next steps for scaling

SCALE PACKAGE — "Dominate Your Market" (Full professional advertising presence)
  • Full Brand Strategy: positioning, all 4 messaging pillars, all 8 taglines, voice guide, brand promise
  • Complete Copywriting: all 20 headlines, all body copy variants, all 12 CTAs, manifesto, all video scripts
  • Full Visual Direction: all 3 visual themes with complete specs, layout guidance, motion direction
  • Social Media Full Suite: all IG (feed + stories + reels), all FB, all X, all LinkedIn
  • Digital Full Suite: all 3 Google Search campaigns + extensions, full 7-email sequence, SEO strategy, landing page copy
  • Website: Conversion landing page + full 5-section website (website_landing_page + website_full — both production-ready HTML)
  • QC scores and approved recommendations across all sections

DOMINATE PACKAGE — "Own the Entire Space" (Enterprise — everything, plus premium assets)
  Everything in Scale, PLUS:
  • TikTok content (all 4 video concepts)
  • YouTube pre-roll script (15s, 30s, 60s versions)
  • Google Display + YouTube campaign brief
  • Retargeting strategy (3 audience segments, message matrix)
  • Full 30-day social media content calendar
  • Brand identity DO/DON'T visual guidelines
  • PR/Outreach brief (press angles, journalist targeting, pitch framework)
  • Influencer collaboration brief (tier recommendations, brief template, content guidelines)
  • Competitive disruption strategy (take market share from top 2 competitors)
  • Budget allocation recommendation (channel split percentages by budget size)
  • Website deployment guide: hosting options, custom domain setup, SEO meta tags checklist, analytics setup (GA4), A/B test roadmap for landing page hero section
  • 90-day launch timeline with weekly milestones

━━━ ASSEMBLY RULES ━━━
• Lead each package with an executive overview (3–5 sentences on strategy + expected outcomes)
• Include a "How to Use This Package" section at the top of each package
• Packages must feel premium and production-ready — not rough drafts
• When referencing website files, note: "website_landing_page and website_full are exported as .html files ready to open in any browser or deploy to any host"
• Dominate must be visibly more valuable than Scale — not just longer
• Note QC scores and flag any sections scored below 7 with improvement guidance

━━━ QUALITY STANDARD ━━━
If QC flags any section with score < 7, include the QC feedback and improvement notes \
directly in the package — never silently deliver subpar content.

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
        "name": "delegate_to_web_design_agent",
        "description": (
            "Delegate website creation to the Web Design Agent. "
            "Agent produces two fully functional HTML files: a conversion landing page "
            "and a complete multi-section website. Both are production-ready and browser-deployable. "
            "Agent will load brand_strategy, copywriting, and creative_direction from store."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Website task — include company name and any design priorities",
                }
            },
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
                    "description": "Which sections to review and what specific quality dimensions to focus on",
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
            "web_design": WebDesignAgent(store),
            "qc": QualityControlAgent(store),
        }
        super().__init__(
            name="Advertising CEO",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=DELEGATION_TOOLS,
            max_tokens=16384,
            max_iterations=35,
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
            "delegate_to_web_design_agent": "web_design",
            "delegate_to_qc_agent": "qc",
        }
        agent_key = agent_map.get(tool_name)
        if agent_key:
            agent = self._agents[agent_key]
            print(f"  [{self.name}] ──► {agent.name}...")
            result = agent.run(task)
            return f"[{agent.name} Report]\n{result}"

        return ad_tools.execute_ceo_tool(tool_name, tool_input, self._store)
