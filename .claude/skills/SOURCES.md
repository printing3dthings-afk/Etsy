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

Each `SKILL.md` was fetched verbatim from the source repo's `main` branch
(unmodified) and is retained under its original MIT license.

## Not added

- **legal-risk** — no dedicated, well-sourced skill found distinct from
  `contract-review`; the latter already covers trademark/liability-style
  risk flagging for this shop's needs.
- **Context7** — not a skill file, an MCP server (official Upstash product,
  `@upstash/context7-mcp`). Requires an API key and a project-level
  `.mcp.json` entry (or `claude mcp add`), not a files-only add — left as a
  follow-up if wanted, since it needs a credential Scott would provide.

## How these get used

Claude Code auto-discovers project skills under `.claude/skills/<name>/SKILL.md`
and loads one when its `description` matches the task at hand — no manual
invocation needed. These are pure instruction sets (no bundled scripts), so
adding them carries no code-execution risk; they just shape how a Claude
Code session approaches copywriting, ad creative, email sequences, contract
review, incident postmortems, and SOP writing when relevant to OnBrandCraftz
work.
