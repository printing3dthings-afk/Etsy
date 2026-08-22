# Tool & MCP Fit-Check Log

Append-only log of "is this tool/repo/MCP server something I need?" questions and their
verdicts. Check this before re-researching a tool that sounds familiar — see the Tool &
MCP Fit-Check Protocol (`ceo_operating_playbook.md`, section 14) for the process that
produces these entries. Keep entries short — a few lines each.

---

### 2026-07-03 — Self-hosted Stable Diffusion / FLUX tools
**Tools:** AUTOMATIC1111/stable-diffusion-webui, comfyanonymous/ComfyUI, lllyasviel/Fooocus,
invoke-ai/InvokeAI, black-forest-labs/flux.
**Verdict:** Redundant / not needed.
**Why:** All five are self-hosted Stable Diffusion or FLUX image generators — they'd require
standing up and maintaining a GPU-backed model server. CLAUDE.md's image-generation hard rule
requires an approved AI image engine (gpt-image-1 default, Gemini, or Ideogram — see the
Universal Listing Rules section); a self-hosted generator would need to demonstrably beat all
three to justify the operational burden. `tools/image_gen.py` already has proven multi-engine
dispatch (`openai`/`gemini`/`ideogram`) covering photorealistic edit-from-real-product-photo
(gpt-image-1, Gemini) and in-image text (Ideogram) — the two things these tools are typically
reached for. No gap found.

### 2026-07-03 — Tavily MCP, Firecrawl MCP, Notion MCP
**Tools:** Tavily MCP (real-time web search w/ citations), Firecrawl MCP (URL → clean markdown),
Notion MCP (content calendar / project databases).
**Verdict:** Tavily — redundant. Firecrawl — redundant. Notion — situational, skip by default.
**Why:**
- Tavily's value prop (real-time search + citations) is already covered by Frank's native
  `web_search` tool — an Anthropic-hosted server tool, already billed through the existing
  Anthropic account, no new API key or MCP server to run.
- Firecrawl's value prop (turn a live URL into clean text for an agent to read) is already
  covered by Frank's `browse_web` tool (`tools/browser_agent.get_page_text`, Playwright-backed),
  already working.
- Notion MCP has no existing usage in this codebase. Frank already owns its own calendar/tasks/
  staged-action system — adding a second, parallel calendar in Notion would fragment truth rather
  than add capability. Only reconsider if Scott is already running a personal Notion workspace he
  specifically wants Frank reading from or writing into.

### 2026-08-08 — Dedicated line-art / coloring-page generation tools
**Tools:** lineart.ai (photo → line art converter), Midjourney coloring-book prompt generators,
general "AI coloring book maker" SaaS tools.
**Verdict:** Redundant / wrong problem.
**Why:** Every dedicated tool found solves "turn an existing photo into an outline drawing" —
a different job than what `generate_coloring_pages.py` needs, which is "generate original
themed artwork that IS already clean line art" (a kawaii cat, a stained-glass window motif,
etc. — no source photo exists to trace). Our own pipeline (gpt-image-1 generate →
`_enforce_bw()` hard 185-threshold post-process → vision-QA verify/retry via
`goal_loop.run_until_goal()`) already covers the real requirement end to end, and per
`creative_tooling_assessment.md`'s existing vtracer/potrace verdict, tracing-based tools
actively produce the wrong output shape for anything downstream that needs clean paths. Full
research + the one real prompt-technique gap found (closed-outline instruction, now added to
all 4 `_STYLE*` constants) is in
`data/knowledge_base/coloring_page_design_and_market_research.md`.
