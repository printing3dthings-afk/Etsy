---
name: handoff
description: "Write a short, human-readable markdown handoff document capturing where this work stands, so it can continue in a new chat/session (local or remote) without losing context. Use when the user asks for a handoff, says 'save our progress', 'write up where we are', 'I want to continue this on my laptop', or before a session is likely to end with real follow-up work still open."
---

# Handoff

This environment already auto-summarizes long conversations when context
fills up — that mechanism is opaque and internal, not something a human
reads or something that survives moving to a genuinely different session
(a fresh local Claude Code window, a different machine, a different
person picking up the work). This skill produces the thing that
mechanism doesn't: a short markdown file a person can actually read in
under two minutes, and a fresh Claude session can use to skip straight to
productive work instead of re-deriving context from scratch.

## What makes a handoff useful (and what doesn't)

The failure mode to avoid is a padded, generic status report that reads
fine but doesn't actually save the next session any work. Ground every
section in what specifically happened in *this* conversation — real file
paths, real commit SHAs, real error messages — never a vague paraphrase.
If a piece of information isn't concretely known, say "unknown" rather
than writing something plausible-sounding to fill the section.

The single highest-value thing a handoff can carry is **why**, not
**what** — a decision that would look wrong or arbitrary without context
is exactly what a generic summary loses first, and exactly what causes a
fresh session to either redo already-settled work or quietly undo a
deliberate choice. (Real example: a fix that looked "obviously correct"
and passed its own tests still turned out wrong on the first live call,
because the test fixtures didn't match the real API's actual response
shape — a handoff that only recorded "fixed the bug" instead of "fixed
it, but only verified against mocks, not a real call yet" would have let
a fresh session confidently report something not actually confirmed.)

## Sections to write, in this order

1. **Status** — one short paragraph, plain language. What's actually
   done, what's in-flight, what's blocked and specifically why it's
   blocked (a missing credential, a pending human approval, an external
   rate limit — name the real blocker, not "waiting on external factors").

2. **Key decisions and why** — bullet list. Each bullet: what was decided,
   and the reasoning that isn't obvious from the decision alone
   (especially "did X instead of the more obvious Y, because Z").

3. **Open threads** — anything waiting on a human: an unanswered question,
   an approval sitting in a queue, a credential someone else needs to
   provide. Be explicit about who/what it's waiting on.

4. **Gotchas discovered this session** — real bugs, traps, or wrong
   assumptions found and fixed (or found and *not yet* fixed) during this
   work. This is the section most worth being concrete in: its entire
   purpose is stopping a fresh session from rediscovering the same thing
   the hard way.

5. **Next action** — the single next concrete step. Not a to-do list of
   everything eventually left to do — just what happens next, specific
   enough that a fresh session can start immediately.

6. **Pointers** — real paths, commit SHAs, action/ticket ids, URLs. A
   fresh session should be able to `git show <sha>` or open a real file
   directly rather than trusting a prose description of what changed.

## Where to write it

`.claude/handoffs/<slug>-<YYYY-MM-DD>.md` (get the real date via `date
+%F` — never guess it). Create the directory if it doesn't exist. Slug
from the work itself (e.g. `etsy-price-fix-verification`), not from a
generic "handoff" name, since multiple handoff files will accumulate over
time and need to stay distinguishable at a glance.

## After writing

Tell the user the file path and give a one-line summary of what's in it.
Don't auto-commit it — whether a handoff doc belongs in git history
(useful project record) or is a throwaway personal note is the user's
call, matching this environment's general rule of only committing when
asked.

## Not a replacement for permanent documentation

If something produced during this work belongs in the project's actual
durable record (this repo's own pattern: `data/knowledge_base/
ops_runbook.md` for infrastructure incidents, `CLAUDE.md` for standing
conventions), the handoff doc should point to that entry, not duplicate
its content. The handoff is for resuming a specific thread of work; the
permanent docs are the record that outlives any one thread.
