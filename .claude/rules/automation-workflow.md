# Automation workflow — when to codify, when to automate

How work in this repo should evolve from one-off chat fixes to durable
tooling, and how to iterate on Frank's own UI. Distilled from a real
2026-08-20 incident (see `.claude/skills/verify-etsy-mutations/SKILL.md`)
where an undocumented procedure (re-verify a mutation's real effect,
never trust its own status) existed only in one session's judgment and
would have been silently lost otherwise.

## Skill first, automation second

A recurring procedure has three stages here, in order — never skip
straight to the last one:

1. **Ad-hoc, in chat.** Done once, by hand, reasoning through it live.
   This is where you learn what the procedure actually needs to check,
   not what it seems like it should check.
2. **A skill** (`.claude/skills/<name>/SKILL.md`). Once a procedure has
   real, non-obvious steps worth repeating exactly (a specific
   verification method, a specific order of checks, a documented reason
   *why* a step exists), write it down as a skill. Run it manually,
   invoked deliberately, for real cases — not on a timer, not
   unattended — until its output is provably right across a few
   different situations.
3. **A script/tool** (`tools/*.py`, an `_EXEC_COMMANDS` entry, a cron
   loop). Only promote a skill to unattended automation once its manual
   runs have actually been trustworthy. Automating a procedure that
   hasn't been proven yet just means the bug ships unattended instead of
   getting caught.

Skipping stage 2 is the specific failure mode to watch for: turning "I
did this once and it seemed to work" directly into a script or a
recurring loop. Nothing here is stopping fast iteration — chat-driven
fixes stay chat-driven for as long as they're one-offs. The discipline
is specifically about the *second* time a procedure repeats: that's the
signal to write it down as a skill before it repeats a third time
unattended.

**Finding what's worth codifying:** the real signal is usually a session
transcript, not a plan — look at what you actually did to fix or verify
something (the exact sequence of checks, not the conclusion), and ask
whether the next person doing this same thing would rediscover those
same steps or skip one. If a step exists because of a real, specific
failure (like re-verifying a mutation's live effect because a status
field lied about it once), that reasoning is exactly what a skill should
preserve — a script can't carry "why," only a written procedure can.

## Iterating on Frank's own UI (`frank_hud_mockup.py`)

For a UI redesign or a new dashboard panel, prefer mocking the visual
direction before touching the real template's Python/CSS/JS:

1. Draft the visual direction as a small number of genuinely distinct
   variations (not incremental tweaks of one idea) before committing to
   any of them.
2. Pick one, then iterate *on that one* — ask for refinements of the
   chosen direction, don't restart from a blank slate each round.
3. Only once a direction is settled, implement it for real in
   `frank_hud_mockup.py` (or the relevant template), matching this
   project's actual token system — see `frank_hud_mockup.py`'s
   `:root` block and `code-style.md`'s naming conventions — rather than
   any placeholder styling the mockup stage used.

This keeps expensive real-code iteration for after the direction is
already right, instead of re-editing live CSS/JS by trial and error.
