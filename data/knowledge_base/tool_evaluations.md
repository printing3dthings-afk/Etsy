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

### 2026-09-06 — Agent-memory / context-compression repo roundup (12 tools from a social screenshot)
**Tools:** MemOS (MemTensor), engram (Gentleman-Programming), obsidian-second-brain
(eugeniughelbur), letta-code (letta-ai), openwolf (cytostack), claude-mem, headroom
(headroomlabs-ai), OmniRoute (diegosouzapw), crewAI, anthropics/claude-plugins-official,
one-skill-to-rule-them-all (rebelytics), plus livekit/agents and langgenius/dify.
**Verdict:** Six memory tools — **redundant**. headroom — **situational, precondition not met**.
OmniRoute — **redundant for images, wrong shape for LLM**. crewAI, livekit, dify — **no**.
claude-plugins-official — **use it, and it is already installed**. one-skill — **redundant**.
**Why:**
- **Source quality first: the numbers in that screenshot are not evidence.** Same repo
  (headroom), same day, three sources: 24.9k / 49k / 68.9k stars. These are engagement
  accounts (@marm.ai, @ai.blueprint, "Save this build list"). Repos were verified to exist;
  the stats were not usable.
- **Memory (6 of 12) is already solved here, and better.** CLAUDE.md + `.claude/skills/*/SKILL.md`
  + `ops_runbook.md` + `ceo_learnings.md` + this file are plain markdown, agent-agnostic, in
  git, versioned, and deployed. That is obsidian-second-brain's literal pitch, except ours
  travels with the deploy instead of sitting in one machine's vault. It demonstrably works:
  Technique 36, written in an earlier session, correctly predicted that the sauce tray's
  fluted skirt would wash out under real light. Adding a second store fragments truth — same
  reasoning that rejected Notion MCP on 2026-07-03.
- **The real gap the roundup exposes is RETRIEVAL, not memory.** `SKILL.md` is 300KB and cannot
  be read in full; `ops_runbook.md` is 1.8MB and gets hard-truncated into Frank's prompt. Both
  hit in one session. The fix is better search over what exists (`_kb_search`, the `query` arg
  on `read_knowledge_base_doc`) — not a new store to keep in sync.
- **headroom** is real (library/proxy/MCP; 20% on coding agents, 60-95% on JSON) and compresses
  large *tool output* before it reaches the model. Frank's token cost is not tool output — it is
  large static docs assembled into the system prompt, which compression does not fix and
  retrieval does. Revisit only if Frank's Anthropic spend becomes the binding constraint AND
  tool output is shown to be the driver.
- **OmniRoute**: `tools/image_gen.py` already dispatches across OpenAI/Gemini/Ideogram/Grok, and
  CLAUDE.md records Grok working as a real fallback when OpenAI and Gemini were both out of
  credit. Frank's LLM path is Anthropic-only by design; routing it to a non-Claude model
  conflicts with every prompt in the system.
- **claude-plugins-official is the one clear yes, and costs nothing** — it is the marketplace
  that already ships with Claude Code, so there is nothing to install. `claude-md-management`
  and `claude-code-setup` are directly relevant to a CLAUDE.md that has grown past 1,000 lines.
- **one-skill-to-rule-them-all** duplicates `.claude/rules/automation-workflow.md`, which
  already mandates skill-before-automation in three stages. An automated skill-writer watching
  sessions would tend to codify procedures that have run once — precisely what that rule exists
  to prevent.
- **Not assessed: licences.** Nothing here was checked for licence compatibility. Per the
  2026-09-01 finding (a reviewed repo under PolyForm Noncommercial, unusable for a commercial
  shop), check the licence before vendoring any of these, not after.

### 2026-09-06 — 3D-printing Claude skills roundup (3 repos from a social screenshot)
**Tools:** flowful-ai/cad-skill, EdwinjJ1/3d-print-skill, jirihelmich/3print-starter.
Plus three closer alternatives found while checking: swh/openscad-skill,
andreahaku/openscad_claude_skill, iancanderson/openscad-agent.
**Verdict:** cad-skill — **hard no, PolyForm Noncommercial**. 3print-starter — **does not
exist**. The other four — real and legal-or-not, but **no capability gap**; nothing vendored.
One genuine gap found and closed with our own code: `tools/mesh_gate.py`.
**Why:**
- **flowful-ai/cad-skill is PolyForm Noncommercial 1.0.0.** Unusable in a commercial shop,
  full stop — the second time in five days a screenshot-sourced repo has been PolyForm-NC
  (see 2026-09-01). It is also CadQuery, not OpenSCAD, so adopting it would mean a second
  modelling stack next to the one 53 techniques are written against.
- **jirihelmich/3print-starter does not resolve** on GitHub and does not appear in search.
  The screenshot's list is itself LLM-written; treat every repo name in one as unverified
  until `git ls-remote` says otherwise. Two of its three entries were wrong or unusable.
- **Licence reading needs the README, not just the file list.** `EdwinjJ1/3d-print-skill`
  and `iancanderson/openscad-agent` both have NO LICENSE file, which looked like all-rights-
  reserved, but each declares MIT in its README (the former in a Chinese-language section).
  Check both before writing off a repo — or before trusting one.
- **No capability gap.** These are starter kits: spec search, mesh validation, STL→3MF,
  a Gridfinity generator. `tools/openscad_render.py` already exports 3MF natively, BOSL2 is
  vendored, PNG preview works headless, and `tools/mesh_anatomy.py` + `tools/inlay_probe.py`
  go considerably further than anything in them. Our own skill is 5,282 lines of measured,
  P1S-specific findings against their few hundred of generic advice.
- **The one real gap: no committed pre-slice gate.** Watertight / winding / component /
  bbox checks had been retyped by hand for every model (five in one session). Closed with
  `tools/mesh_gate.py` — our own code, our conventions, no vendoring needed for ~100 lines
  of trimesh calls.
- **The multi-agent carousel in the same screenshot is marketing, not a tool.**
  "PLAN → CODE → FIX → TEST → REVIEW" is the built-in Plan/Explore agents plus the three
  reviewers already in `.claude/agents/`. Nothing to install.

**Correction to the 2026-09-06 agent-memory entry above:** it said claude-plugins-official
"is already installed... there is nothing to install." That was wrong — this repo had no
`.claude/settings.json` at all, so no marketplace was registered and no plugin was enabled.
Fixed the same day; `claude-md-management` and `claude-code-setup` are now enabled there.
