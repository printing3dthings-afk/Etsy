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
| `fastapi-patterns` | [affaan-m/ECC](https://github.com/affaan-m/ECC) (`skills/fastapi-patterns`) | MIT | 2026-07-29 |
| `cost-tracking` | [affaan-m/ECC](https://github.com/affaan-m/ECC) (`skills/cost-tracking`) | MIT | 2026-07-29 |
| `cast`, `paint` | [ATheVon/genjutsu](https://github.com/ATheVon/genjutsu) (`skills/cast`, `skills/paint`) | MIT | 2026-08-04 |
| `_jutsu/*` (9 sub-skills, see note below) | [ATheVon/genjutsu](https://github.com/ATheVon/genjutsu) (`skills/_jutsu/*`) | MIT | 2026-08-04 |

Each `SKILL.md` was fetched verbatim from the source repo's `main` branch
(unmodified) and is retained under its original MIT license. `graphify` is
the one exception — its `main` branch didn't have a stable `skill.md` path
at fetch time, so it was pulled from the `v8` tag instead (same file,
pinned version).

## Project subagents (`.claude/agents/`)

Two custom subagent definitions added 2026-07-29, same vetting process as
skills, sourced from [affaan-m/ECC](https://github.com/affaan-m/ECC) (MIT):

| Agent | Source path | Why |
|---|---|---|
| `fastapi-reviewer` | `agents/fastapi-reviewer.md` | Our server is FastAPI (`Depends`, `HTTPException`, async routes throughout `main.py`) — a specialized reviewer beats a generic one for this specific framework. |
| `silent-failure-hunter` | `agents/silent-failure-hunter.md` | Directly matches an explicit hard rule already in `.claude/rules/code-style.md` ("Errors: never a bare 500, never a silent swallow") — a dedicated hunter for exactly that bug class. |
| `security-reviewer` | `agents/security-reviewer.md` | OWASP Top 10 + secrets-detection specialist, added 2026-07-29 to back `/security-scan`. **Caveat**: its example "Analysis Commands" (`npm audit`, `eslint --plugin security`) are Node-biased — the review framework itself is language-agnostic but those two specific commands won't run here. Complements `fastapi-reviewer`, doesn't replace it. |

Both are clean, self-contained Claude Code subagent definitions (standard
`name`/`description`/`tools`/`model` frontmatter, `tools: Read, Grep, Glob,
Bash` — read-focused, no write/network tools) with a sensible "Prompt
Defense Baseline" section guarding against injected instructions in
whatever code they review. No external dependencies, no npx calls, no
credentials.

## `/security-scan` — installed, but runs unaudited third-party code on demand

Added 2026-07-29 (`commands/security-scan.md`, `agents/security-reviewer.md`,
both from affaan-m/ECC, MIT). One adaptation was needed to actually work
standalone: the command's frontmatter declared `agent: ecc:security-reviewer`
(ECC's own plugin namespace, which we don't have installed) — changed to
`agent: security-reviewer` to point at the plain agent installed alongside it.
Nothing else in the file was touched.

**Read this before running `/security-scan`**: it shells out to `npx
ecc-agentshield scan` — downloading and executing a **separate npm package**
at invocation time, not just following markdown instructions. Researched
`affaan-m/agentshield` itself (not just its own README): MIT, read-only by
default (file changes only with an explicit `--fix` flag), no API key needed
for the basic scan (only its optional `--opus` deep-analysis mode calls
Claude), scans local `~/.claude/` config files only, no other network calls.
But it's young — built at a February 2026 hackathon, ~1k stars — and I have
not personally read its scanning source, only its own description of itself.
**Deliberately did not trigger the first real execution of `npx
ecc-agentshield` from this sandbox** — that should happen once, on Scott's
own machine, so he can see exactly what it does before it becomes a standing
tool, rather than this session running unaudited third-party code on his
behalf sight-unseen.

## `cost-tracker.js` hook — hand-written, not vendored

Added 2026-07-29 at `.claude/hooks/cost-tracker.js` — the first Node.js file
in this repo (everything else is Python). This is **not a copy** of ECC's
`scripts/hooks/cost-tracker.js`; that file pulls in a ~950-line cross-platform
dependency chain (`utils.js` → `agent-data-home.js` → `path-safety.js`) built
for ECC's own Cursor+Claude multi-harness distribution — none of which this
single-project use case needs. Read the real file plus its full dependency
chain before deciding this, then hand-wrote a ~150-line version that keeps
the two things worth keeping (the per-`message.id` token dedup — the
original's own comments cite a real bug where summing every transcript line
inflated cost 2.5-3x — and the per-model rate table) and drops everything
else (no Cursor support, no project-config-file overrides, no
`child_process` calls anywhere in the file). Smaller, fully-audited surface
for the one thing we actually need.

**Deliberately not registered in this repo's own `.claude/settings.json`.**
The hook writes to `~/.claude/metrics/costs.jsonl` — the user's home
directory, a personal cross-project preference, not something that should
silently fire for anyone who clones this repo. Registering it is a one-time
step in Scott's own **user-level** `~/.claude/settings.json` (never
committed) — see the delivery message in chat for the exact JSON snippet.

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

## `cast`/`paint` (genjutsu) — motion/design pipeline, scoped to this repo's web-only stack

Added 2026-08-04 at Scott's request after reviewing a "top GitHub repos" post
(the same "Genjutsu... 172 stars" slide flagged `Web (React, Vue, Svelte,
vanilla CSS, Three.js, Canvas)` specifically -- direct overlap with real work
already in this repo: the vendored Three.js wordmark orb and every hand-rolled
CSS/JS animation across the Frank UI audit). Cloned the actual repo (`git
clone`, not marketing copy) and read `skills/cast/SKILL.md` in full plus
grepped every `skills/**/*.md` for exfiltration/install/credential-harvesting
patterns (`curl`, `wget`, `npx`, `pip install`, `api_key`, `secret`, `token`,
`~/.ssh`, etc.) before adding anything -- every hit was benign (either a
literal design-token reference, i.e. color/spacing/motion tokens, not auth
tokens, or a legitimate local dev-tool invocation like `npx pa11y`/`npx
source-map-explorer` gated behind `design-audit`'s own audit mode, same bar
already applied to `youtube-transcript`/`clipify`/`graphify`). MIT, real
author (Adrien Thevon), no API keys, no network calls beyond what Claude's
own execution context already does, no phone-home.

**Structure differs from every other skill in this file** -- it's not one
`SKILL.md`, it's two orchestrators (`cast` = motion/micro-interactions,
`paint` = full design-system pipeline) that internally load "sub-skills"
from `_jutsu/<name>/SKILL.md` at runtime based on detected stack. Installed
matching the upstream repo's own directory shape flattened one level (drop
the outer `skills/` folder since `.claude/skills/` already serves that
role): `.claude/skills/cast/`, `.claude/skills/paint/`,
`.claude/skills/_jutsu/<name>/` -- so the orchestrators' internal relative
paths to `_jutsu/...` keep resolving.

**Only 9 of the upstream repo's 14 `_jutsu/` sub-skills were copied** --
`css-native`, `gsap`, `threejs-r3f`, `canvas-generative`,
`motion-principles`, `design-audit`, `desktop-principles`,
`mobile-principles`, `ui-ux-pro-max`. Excluded: `compose-graphics`,
`compose-motion`, `compose-multiplatform`, `swiftui-graphics`,
`swiftui-motion` (Android/Apple-native -- this repo is 100% web, no native
targets exist or are planned), and `framer-motion` (React-specific --
Frank's frontend is vanilla JS/CSS with zero React, per this whole file's
established stack). If `cast`/`paint` ever try to route to an excluded
sub-skill on some future non-web work, they'll simply not find it -- no
functional loss for the actual stack this repo has today, and cheaper than
carrying ~40% more sub-skill weight (mostly Kotlin/Swift-specific token
codegen guidance) that can never fire here.

`_jutsu/ui-ux-pro-max` is itself a second-order vendor -- see its own
`UPSTREAM.md` (copied along with it) for the chain: it mirrors
[nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
(MIT), synced to upstream v2.11.0, ~1.8MB of design-token reference data +
Python scripts (also grepped clean -- no `subprocess`/`os.system`/`eval`/
`exec`/network calls). This is the *same* `ui-ux-pro-max` repo evaluated
and explicitly passed on as a standalone install earlier in this same
review pass (redundant with this shop's own custom 12-theme color system +
WCAG checker + font-pairing picker) -- here it's an internal lookup module
genjutsu's own pipeline consults, not something invoked directly, so the
earlier "redundant" call doesn't apply to this nested copy.

**Scope note, matching this file's `taste-skill`/`hallmark` caveats**:
`cast`'s own frontmatter says it "adapts to Web, Android (Compose), Apple
(SwiftUI)" -- unlike `taste-skill`/`hallmark`, which explicitly exclude
dashboards, `cast`/`paint` don't carry that same landing-page-only
restriction, so (unlike those two) they're expected to actually apply to
Frank's own dashboard/admin-UI work, not just one-off marketing pages.

## `gsap` — vendored animation library, not a skill

Added 2026-08-04, same request as `cast`/`paint` above. **Not a Claude
Skill** -- GSAP (GreenSock Animation Platform) is a client-side JS animation
library, vendored the same way Three.js already is in this repo (see
`tools/api_server/static/vendor/three/` and main.py's `_CachedStaticFiles`
-- anything under `.../vendor/` is auto-served with a 7-day cache header,
no route changes needed). Fetched the real upstream file directly (`curl` to
jsdelivr's npm mirror, not a WebFetch summary -- WebFetch runs fetched
content through a model and can silently paraphrase/truncate, which is fine
for reading a license page but not safe for a file real browsers will
execute) into `tools/api_server/static/vendor/gsap/gsap.min.js` (GSAP
3.12.7, upstream's own minified build, unmodified, original license banner
intact at the top of the file).

**Not MIT** -- GSAP ships under GreenSock's own "Standard No Charge"
license (confirmed by reading `https://gsap.com/standard-license/`
directly, not marketing copy): free for this exact use case (embedding in
an internal/commercial dashboard, no payment, no attribution requirement
beyond not stripping the license banner), restricted only on building a
*competing* no-code visual-animation-builder product or reverse-engineering
GSAP to build one -- neither applies to using it as a library inside
Frank's UI.

**Vendored only, not yet wired into any feature** -- no `<script>` tag
was added to `frank_hud_mockup.py`. Matches how Three.js itself was first
vendored as pure infrastructure in one task, then actually wired into the
wordmark orb in a later, separate task -- adding an unconditional
`<script src="/static/vendor/gsap/gsap.min.js">` to every page load today
would cost real parse/execute time for zero current benefit, since nothing
uses it yet. When a future task actually builds a GSAP-based animation,
load it there (a plain global `<script src="...">` tag, since GSAP ships
UMD/global-style, not ESM -- unlike `three`, it doesn't need an importmap
entry).

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
