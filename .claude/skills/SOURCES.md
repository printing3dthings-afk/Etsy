# Skill provenance

Project-level Claude Skills added to this repo, and where each came from.
All are third-party, community-authored skills (not written by Anthropic or
OnBrandCraftz) — vetted before adding: content reviewed for suspicious
instructions (prompt injection, data exfiltration, safety overrides — none
found), license confirmed, author/repo checked for legitimacy.

| Skill | Source repo | License | Fetched |
|---|---|---|---|
| `copywriting` | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | MIT | 2026-07-22 |
| `ad-creative` | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | MIT | 2026-07-22 |
| `email-sequences` | [rampstackco/claude-skills](https://github.com/rampstackco/claude-skills) | MIT | 2026-07-22 |
| `contract-review` | [evolsb/claude-legal-skill](https://github.com/evolsb/claude-legal-skill) | MIT | 2026-07-22 |
| `incident-postmortem` | [w95/awesome-claude-corporate-skills](https://github.com/w95/awesome-claude-corporate-skills) | MIT | 2026-07-22 |
| `sop-builder` | [w95/awesome-claude-corporate-skills](https://github.com/w95/awesome-claude-corporate-skills) | MIT | 2026-07-22 |
| `avoid-ai-writing` | [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) | MIT | 2026-07-22 |
| `brainstorming` | [obra/superpowers](https://github.com/obra/superpowers) (skills/brainstorming) | MIT | 2026-07-22 |
| `youtube-transcript` | [michalparkola/tapestry-skills](https://github.com/michalparkola/tapestry-skills) | MIT | 2026-07-22 |
| `taste-skill` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | MIT | 2026-07-25 |
| `graphify` | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) (`v8` tag) | Apache-2.0 / MIT (dual) | 2026-07-29 |
| `obsidian-markdown` | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | MIT | 2026-07-29 |
| `obsidian-bases` | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | MIT | 2026-07-29 |
| `json-canvas` | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | MIT | 2026-07-29 |
| `obsidian-cli` | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | MIT | 2026-07-29 |
| `defuddle` | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | MIT | 2026-07-29 |
| `hallmark` | [Nutlope/hallmark](https://github.com/Nutlope/hallmark) | MIT | 2026-07-29 |
| `clipify` | [louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify) | MIT | 2026-07-29 |

Each `SKILL.md` was fetched verbatim from the source repo's `main` branch
(unmodified) and is retained under its original MIT license. `graphify` is
the one exception — its `main` branch didn't have a stable `skill.md` path
at fetch time, so it was pulled from the `v8` tag instead (same file,
pinned version).

## Not added

- **legal-risk** — no dedicated, well-sourced skill found distinct from
  `contract-review`; the latter already covers trademark/liability-style
  risk flagging for this shop's needs.
- **AI Writing Auditor Agent** (VoltAgent/awesome-claude-code-subagents) —
  same job as `avoid-ai-writing` above, implemented as a subagent instead
  of a skill. Redundant with a skill we already have; not worth adding a
  second implementation of the same capability.
- **Buffer Publish** (buffer.com) — not a Claude skill/MCP server at all,
  a third-party paid social-scheduling SaaS product. Would also duplicate
  the Pinterest/social posting already built into Frank (`tools/
  pinterest_api.py`, `social_media_tools.py` — see CLAUDE.md's automation
  stack). A business/tooling decision for Scott, not something to vet and
  commit as a file.
- **Claude Code Sub-Agents** (docs.anthropic.com) — this is Anthropic's
  own official feature documentation, not a third-party thing to install.
  Real capability already usable today (see the built-in Explore/Plan/
  general-purpose agent types); a genuinely *custom* project subagent
  (e.g. an Etsy-listing-specific reviewer) is a real, larger design task
  if wanted later, not a drop-in file.
- **last30days-skill** (mvanhorn/last30days-skill, 2026-07-29) — a real,
  legitimate MIT tool (52+ contributors) for 30-day trending-topic research,
  but its actual `SKILL.md` (~1,400 lines) doesn't pass the same bar every
  other skill here did. It auto-reads browser cookies (Chrome/Firefox/
  Safari, for X/Twitter session auth) and its setup flow collects and
  persists several third-party API keys (ScrapeCreators, Perplexity, Brave,
  OpenRouter, Exa, a Bluesky app password, a GitHub OAuth device flow) to a
  local `.env` config file via an escalating, consent-narrowing multi-step
  flow. That credential-harvesting design pattern is a real mismatch for a
  repo that already holds live Etsy/OpenAI/SMTP secrets in its own `.env`.
  Raised directly to Scott rather than deciding unilaterally either way —
  he chose to skip it. Don't re-propose without re-surfacing this tradeoff.
- **cc-switch** — not a Claude skill at all (a standalone desktop app for
  switching between Claude Code provider/model config profiles). Nothing to
  vet or install here; excluded per Scott's own instruction.
- **OpenMontage** (calesthio/OpenMontage, 2026-07-29) — not a lightweight
  skill file: a complete agentic video-production system requiring a full
  repo clone (Python 3.10+, Node.js 18+, FFmpeg, `npm install` for its
  Remotion composition engine, `make setup`), and **AGPLv3 licensed**
  (copyleft — a materially different obligation profile than every
  MIT-licensed skill in this repo). Forcing a heavy AGPL Node+Python clone
  into this repo to get one capability is the wrong shape of integration.
  If Scott wants full agentic video production later, the right move is
  running it as a completely separate standalone tool on his own machine,
  not merging it here.
- **pycaps** (francozanardi/pycaps, 2026-07-29) — also not a skill file: a
  Python CLI/library (`pip install git+...`) needing ffmpeg + optional
  Playwright + an auto-downloaded Whisper model, for burning animated
  CSS-styled captions onto video. A real feature candidate (captioned
  product/promo videos) but it's actual new pipeline work — a new tool
  module, a `requirements.txt` entry, wiring into existing video output —
  not a file to fetch and drop in. Scoped as a documented future option,
  not built.

## `taste-skill` scope — read before expecting it to fire on dashboard work

Picked over the alternative candidate, `alchaincyf/huashu-design` (2026-07-25,
Scott: "You pick what you think is most beneficial"): `taste-skill` is ~10x
more adopted (66k★ vs 6.6k★), corporately sponsored (Vercel, IMG.LY,
Novamira), and targets exactly the kind of work this repo actually does —
better-designed frontend *code* (the CSS/JS/HTML embedded directly in
`frank_hud_mockup.py`) — where `huashu-design` targets slide decks/
prototypes/MP4 exports OnBrandCraftz doesn't produce.

**Important caveat, confirmed by reading the fetched file itself (not
assumed from marketing copy):** the skill's own frontmatter scopes it to
"landing pages, portfolios, and redesigns... **Not dashboards, not data
tables, not multi-step product UI.**" Frank's own Command Center screens
(`frank_hud_mockup.py`'s core dashboard/tab-bar/action-queue UI) are
explicitly outside this skill's stated scope — it will not (and per its own
rules, should not) fire on that work. Where it *does* apply: one-off
landing-page-shaped HTML (the Home-screen mockup Artifacts built earlier
this session, any future marketing/report pages) — genuinely useful there,
just not a blanket upgrade to every UI edit in this repo.

## `hallmark` overlaps `taste-skill` — same scope gap, use whichever fires

Added 2026-07-29 at Scott's request after reviewing a "top GitHub repos"
post. Reviewed the actual `skills/hallmark/SKILL.md` (~15,000 words, MIT,
19.5k★, real developer — Hassan El Mghari/Nutlope): clean, no exfiltration/
credential/auto-install red flags, all file writes confined to the local
project directory and transparently disclosed. It's more built-out than
`taste-skill` (57 "slop-test" quality gates, 20 themes, 4 modes: build/
audit/redesign/study) but **has the identical scope gap** — its own
document explicitly limits itself to landing pages, marketing sites, and
simple components, and does not address dashboards, data tables, multi-step
forms, or admin panels. Frank's own Command Center screens are out of scope
for this skill too, for the same reason `taste-skill` doesn't fire on them
(see that section below). Both installed as companions, not a replacement
for one another — Claude Code will pick whichever's description matches
better for a given one-off landing/marketing page task.

## `youtube-transcript` is not a pure instruction file — read before use

Unlike the other 9 skills, `youtube-transcript` bundles real executable
behavior: it shells out to `yt-dlp` (auto-installing it via brew/apt/pip
without asking first) and, only with explicit user confirmation, can fall
back to downloading audio and transcribing via OpenAI Whisper (`pip
install openai-whisper`). Reviewed and found legitimate (no injection/
exfiltration patterns, MIT licensed, 498-star repo) — flagged here so
nobody is surprised the first time it silently installs `yt-dlp`.

## `clipify` requires a separate local install — read before expecting it to just work

Added 2026-07-29. Same category as `youtube-transcript`/`graphify` below —
not a pure instruction file. Its `SKILL.md` drives real local processing
(ffmpeg, local Whisper transcription, numpy) to find funny moments in a
video, cut/reframe them to 9:16, and burn word-by-word captions. Reviewed
clean (MIT, no API keys, fully local — no cloud calls of any kind). Needs
`ffmpeg` + `whisper` installed locally to actually do anything; without
them the skill will correctly report they're missing rather than silently
failing.

## `graphify` requires a separate local install — read before expecting it to just work

Like `youtube-transcript`, `graphify` isn't a pure instruction file — its
`SKILL.md` teaches how to drive the real `graphify` CLI (local, deterministic
tree-sitter AST parsing of a codebase into a queryable knowledge graph;
optional git hooks to auto-rebuild on commit/checkout). The CLI itself isn't
bundled here and needs Scott to `pip install`/`uv tool install graphify`
separately for this skill to do anything — until then, the skill will just
correctly report the tool isn't installed. Reviewed the actual `skill.md`
content directly (not marketing copy): it explicitly refuses to ask for or
require any API key ("graphify needs no API key. Never ask the user for
one, and never block on one"), and every optional external integration
(Gemini for extraction, Neo4j/FalkorDB for graph storage) is opt-in via
explicit flags/env vars — no injection or exfiltration patterns found.

## How the rest get used

Claude Code auto-discovers project skills under `.claude/skills/<name>/SKILL.md`
and loads one when its `description` matches the task at hand — no manual
invocation needed. Every skill above except `youtube-transcript` and
`graphify` is a pure instruction set (no bundled scripts) — adding them
carries no code-execution risk; they just shape how a Claude Code session
approaches copywriting, ad creative, email sequences, contract review,
incident postmortems, SOP writing, AI-writing cleanup, pre-work
brainstorming, frontend design taste (landing/portfolio-shaped only, see the
caveat above), and Obsidian-flavored markdown/Bases/Canvas/CLI conventions,
when relevant to OnBrandCraftz work.
