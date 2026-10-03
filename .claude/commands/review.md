---
description: Run the project's specialist review agents against the current diff, routed by what actually changed.
---

# Review Command

Independent review of a diff by the specialist agents this project already
declares. Exists because `.claude/rules/subagents.md` named a real gap:
`fastapi-reviewer` and `silent-failure-hunter` were declared and **nothing ever
invoked them**, so in practice they never ran. A review agent that never fires
is a review that never happens.

## Usage

`/review [target]`

- no argument: uncommitted changes (`git diff HEAD`), falling back to the last
  commit (`git diff HEAD~1 HEAD`) when the tree is clean
- a commit-ish, branch, or `A..B` range: reviewed as given
- a path: limits the diff to that path

## Routing — spawn only where a cold start is affordable

`.claude/rules/subagents.md` is the authority here and it cuts **both** ways.
Its case 2 says independent review of a diff you just wrote is exactly where a
subagent wins, *because* the reviewer has no stake in the code being correct.
Its main argument says a cold agent carries none of this repo's ~12,100 lines
of CLAUDE.md, rules and 3D-print skill — and that three of the real defects
found here were caught **because** of that context.

So route by whether the missing context matters:

| changed files | run |
|---|---|
| `tools/api_server/*.py` | `fastapi-reviewer` **and** `silent-failure-hunter` |
| any other `.py` | `silent-failure-hunter` |
| auth, tokens, secrets, webhooks, request handling, file upload/download, subprocess, or anything touching `.env`/credentials | add `security-reviewer` |
| **`.scad`, `openscad_models/`, `.claude/skills/`, `CLAUDE.md`, `data/knowledge_base/`, docs only** | **run nothing — say so and stop** |

That last row is not a shortcut, it is the point. A cold agent reviewing a
`.scad` file does not know the maker's-mark rule, the P1S overhang limits, the
sealed-void class, or that `mesh_gate` passing is not proof of correctness. It
will produce confident, wrong review. Do that pass inline instead.

Launch the selected agents **in parallel in one block** — they are independent.

## What to tell each agent

Pass it enough to review without exploring the whole tree:

1. The diff itself (`git diff <target> -- <paths>`).
2. The full path of each changed file, so it can read surrounding context.
3. This instruction: *report only defects you can point at a specific line for;
   for each one give file:line, what breaks, and a concrete failing case. Do
   not report style preferences. Do not suggest rewrites of code that works.*
4. The two project rules most often violated here, quoted, since the agent
   cannot see them:
   - *Errors: never a bare 500, never a silent swallow.* Every external call
     (Etsy, Anthropic, filesystem) gets wrapped into a clear `HTTPException`
     with an actionable `detail`, or an honest `{"error": ...}` the caller can
     branch on. Never catch-and-ignore an error that changes what gets reported
     as true.
   - *Route handlers stay thin; blocking work goes off the event loop* via
     `await asyncio.to_thread(...)`. A real `rglob()`/subprocess call inside an
     `async def` route body blocks the whole single-process server.

## Verifying before reporting

Agent findings are **claims, not facts** — `.claude/rules/subagents.md` warns
that other agents report incorrect or misleading results. Before surfacing any
finding:

1. Read the actual line. Confirm the code says what the finding says it says.
2. Discard anything already handled by a caller, a wrapper, or an existing
   guard the agent could not see.
3. Discard duplicates where two agents found the same thing; report once.

Report what survives, most severe first, each with file:line and a concrete
failing case. If nothing survives, say that plainly — an empty review is a
real result and padding it is worse than useless.

**Never auto-apply fixes from this command.** Report; let Scott decide. Fixes
to anything that touches a live Etsy listing still stage through the Action
Center like everything else.

## Arguments

$ARGUMENTS: optional target (commit-ish, range, or path)
