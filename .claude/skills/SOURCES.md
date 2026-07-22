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

Each `SKILL.md` was fetched verbatim from the source repo's `main` branch
(unmodified) and is retained under its original MIT license.

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

## `youtube-transcript` is not a pure instruction file — read before use

Unlike the other 8 skills, `youtube-transcript` bundles real executable
behavior: it shells out to `yt-dlp` (auto-installing it via brew/apt/pip
without asking first) and, only with explicit user confirmation, can fall
back to downloading audio and transcribing via OpenAI Whisper (`pip
install openai-whisper`). Reviewed and found legitimate (no injection/
exfiltration patterns, MIT licensed, 498-star repo) — flagged here so
nobody is surprised the first time it silently installs `yt-dlp`.

## How the rest get used

Claude Code auto-discovers project skills under `.claude/skills/<name>/SKILL.md`
and loads one when its `description` matches the task at hand — no manual
invocation needed. Every skill above except `youtube-transcript` is a pure
instruction set (no bundled scripts) — adding them carries no code-execution
risk; they just shape how a Claude Code session approaches copywriting, ad
creative, email sequences, contract review, incident postmortems, SOP
writing, AI-writing cleanup, and pre-work brainstorming when relevant to
OnBrandCraftz work.
