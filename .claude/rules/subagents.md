# Subagents — when a second agent earns its cold start

There was no guidance on this until 2026-09-06, so the decision got remade
ad hoc every time. Written after reviewing a widely-shared carousel
promoting "let Claude decide how many agents to use" — the pattern is real,
but its value in this repo is close to the opposite of what that pitch
claims, for a reason specific to how work here goes wrong.

## The cost is context, and here that cost is unusually high

A spawned agent starts cold. It does not carry CLAUDE.md (3,800 lines),
`3d-print-design/SKILL.md` (5,300 lines), or these rules — roughly 9,500
lines of hard-won, mostly non-obvious constraints. Almost every real defect
caught in this shop was caught *because of* that context, not in spite of
it:

- The maker's mark had never been printable. Found by measuring stroke
  widths against one extrusion — you only think to measure that if you know
  the standing mark rule exists.
- `mesh_gate.py`'s overhang scan was inverted. Found because Technique 38
  documents that exact sign trap, by name.
- A sauce bowl cavity sat 0.09mm from breaching its own exterior. Found by
  sweeping the real (angle, height) profile, not by reading the source.

A cold agent re-deriving the situation would have missed all three. Parallel
throughput is not this shop's constraint; being right is.

## So the default is: do it yourself

Do not spawn an agent because a task is large, has several parts, or sounds
thorough. Handle it inline. This matches the harness default — the Agent
tool is for when the user, a CLAUDE.md, or a skill actually asks for it.

## Three cases where a subagent genuinely wins

1. **Broad fan-out search where you need only the conclusion.** Sweeping
   many files or naming conventions to answer "where does X live" — the
   context an agent lacks does not matter, because the answer is a path, not
   a judgment. Use `Explore`.
2. **Independent review of a diff you just wrote.** Here the cold start is
   the *feature*: a reader who did not write the code has no stake in it
   being correct. `security-reviewer`, `fastapi-reviewer` and
   `silent-failure-hunter` exist for this.
3. **Genuinely mechanical work across many files** where the change is
   already decided and the risk is tedium, not judgment.

Everything else — design calls, verification, anything touching a live
listing or a customer-facing claim — stays inline.

## Gap closed 2026-09-11 — `/review`

This section used to read: only `security-reviewer` is wired to anything
(`/security-scan`); `fastapi-reviewer` and `silent-failure-hunter` are declared
but nothing ever invokes them, so in practice they never run.

`.claude/commands/review.md` closes it. `/review [target]` reviews a diff and
**routes by what changed**, which is where the real judgment lives:

| changed | runs |
|---|---|
| `tools/api_server/*.py` | `fastapi-reviewer` + `silent-failure-hunter` |
| any other `.py` | `silent-failure-hunter` |
| auth/secrets/webhooks/subprocess/file I/O | adds `security-reviewer` |
| `.scad`, `openscad_models/`, `.claude/skills/`, `CLAUDE.md`, docs | **nothing** |

That last row is this file's own argument applied honestly. A cold agent
reviewing a `.scad` does not know the maker's-mark rule, the P1S overhang
limit, the sealed-void class, or that a clean `mesh_gate` is not proof of
correctness — it will produce confident, wrong review. Those passes stay
inline. The command spawns exactly where case 2 above says a cold start is the
feature and nowhere else.

Findings come back as claims and are verified against the real lines before
anything is reported, per the caution at the top of this file. Nothing is
auto-applied.

**Why this instead of a plugin.** Anthropic's `/feature-dev` plugin was
evaluated the same day (Scott, from a TikTok). It is legitimate — Anthropic
Verified, 256k installs — and still the wrong fit: its `code-explorer` is the
built-in `Explore` agent this file already endorses, its `code-reviewer`
duplicates three reviewers already declared here, and its `code-architect`
("proposes multiple implementation approaches with clear trade-offs") is the
opposite of CLAUDE.md's delivery rule, which asks for a recommendation rather
than a survey. The shortage was never review agents. It was wiring.

## What not to take from the carousel

"Stop telling Claude how many agents to use" optimises for throughput. The
one number worth optimising here is how many wrong things reach a customer,
and no amount of parallelism improves it. Its "3 months of work in days"
claim carries no source and is not evidence of anything.
