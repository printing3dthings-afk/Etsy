# AGENTS.md — OnBrandCraftz

Instructions for AI coding agents working in this repository.

**Claude Code does not read this file.** It reads `CLAUDE.md`, which takes
precedence whenever it exists (native `AGENTS.md` support landed in Claude
Code v2.1.277, but only as a fallback for repos that have no `CLAUDE.md`).
This file exists for every *other* agent — Codex, Cursor, Copilot, Jules —
which would otherwise start here knowing nothing.

It is deliberately short. `CLAUDE.md` is ~3,800 lines and changes weekly;
copying any of it here would produce two sources of truth that disagree
within a week. This repo has a specific history of that failure — two review
agents declared but never invoked, a hook never wired, a skill whose CLI was
never installed — so: **hard stops below, pointers for everything else.**

---

## What this is

A one-person Etsy shop (OnBrandCraftz, owner Scott) selling digital planners,
printable wall art, sticker packs, and 3D-printed physical goods made on a
Bambu Lab P1S. The codebase is the shop's automation: a FastAPI dashboard
("Frank") on Railway, Etsy API integration, product generation pipelines, and
an OpenSCAD 3D-print pipeline.

---

## Hard stops

These are not style preferences. Violating one can cost real money, a real
customer, or the shop's Etsy standing.

1. **Never state anything untrue to a customer.** Listing photos must show the
   real product — never an AI-generated stand-in. Page counts, sticker counts,
   file specs, and compatibility claims must be verified against the actual
   delivered file, not assumed. This rule outranks everything else here.

2. **Nothing publishes to Etsy without Scott's approval.** Anything that
   mutates a live listing — price, title, tags, description, state, photos —
   is *staged* via `db.enqueue_action()` into the Action Center for one-tap
   review. Never call the mutating Etsy API method directly from a chat tool,
   a script, or a background loop.

3. **Credentials live in `.env`.** Never hardcode one, never commit one, never
   write a fetched secret to disk or into a log.

4. **Never call `EtsyAPIClient.refresh_access_token()` from outside Frank's
   own running process.** It rotates the refresh token; a copy that only
   exists in a throwaway session breaks the shop's Etsy connection until
   Scott re-runs the OAuth flow by hand.

5. **Archive before deleting.** Use `tools/trash.py` (`archive_snippet`,
   `archive_file`) before removing any code block or file. Everything lands in
   the committed vault at `data/trash/` and is restorable for 30 days.

6. **Runtime state never writes to a git-tracked file.** `product_catalog.json`
   and friends are checked in; a runtime write vanishes on the next Railway
   redeploy. Use the volume-or-local sidecar pattern — see
   `.claude/rules/api-conventions.md`.

7. **A new 3D print design needs Scott's sign-off on the *form* first.**
   Present 4–5 genuinely different formal approaches, one sentence each, no
   code. He picks one, then you write the `.scad`. Iterating on an
   already-approved design needs no new approval.

---

## Testing

No pytest. Every test is a standalone runnable script with its own
`check()`/`run()` harness — copy the shape in `.claude/rules/testing.md`
exactly rather than introducing a second style.

```bash
python3 tests/run_all.py -j 4      # full suite: 190 files, ~4-5 min on 4 cores
python3 tests/test_<name>.py       # one file
```

**Actually run it before shipping.** The suite sat red for three days once
because nothing ran it.

A regression test reproduces the *exact* reported bug — the real filenames,
the real numbers — not generic coverage of the function.

---

## Where the real documentation is

| File | Covers |
|---|---|
| `CLAUDE.md` | Everything: product catalog, Etsy rules, pricing, listing standards, printer specs, autonomy boundaries |
| `.claude/rules/code-style.md` | Comments explain WHY; no dead code; no premature abstraction |
| `.claude/rules/testing.md` | The test harness, mocking, the Playwright service-worker trap |
| `.claude/rules/api-conventions.md` | FastAPI route shape, auth dependencies, caching, durable state |
| `.claude/rules/automation-workflow.md` | When a procedure earns a skill, and when a skill earns a script |
| `.claude/rules/subagents.md` | When a subagent is worth its cold start (usually it is not) |
| `data/knowledge_base/` | Sourced reference: P1S hardware, DfAM, photo research, ops runbook |

Read `CLAUDE.md` before any substantial change. Most of what looks like an
obvious improvement here has already been tried and written up with the
measurement that killed it.

---

## Working style

- **Measure, don't assert.** Claims about behaviour get verified by running
  the thing — a render, a browser, a real file — not by reading the source and
  concluding. Several real defects in this repo were found only by looking at
  actual output, and two confident statistics turned out to be measuring the
  wrong pixels entirely.
- **Prefer editing an existing file** over adding a new one.
- **Dated root-cause comments** at the site of a non-obvious fix: what failed,
  and why the fix is shaped that way. Not a changelog — a landmine warning.
- **Before adding a tool or dependency, check what the environment already
  does.** Installed here already: `blender`, `openscad`, `ffmpeg`, Playwright
  with Chromium, Node 22, Python 3.11.
