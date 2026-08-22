---
name: write-a-skill
description: "Turn a procedure that just happened (or that the user describes) into a proper .claude/skills/<name>/SKILL.md file. Use when the user says 'write this up as a skill', 'save this procedure', 'make a skill out of this', 'turn this into a reusable skill', or when a procedure has now repeated a second time in this session and per .claude/rules/automation-workflow.md's discipline should be written down before it repeats a third time unattended."
---

# Write a Skill

Operationalizes `.claude/rules/automation-workflow.md`'s stage 2: "ad-hoc →
**skill** → automation." This skill exists specifically because that rule
was written down but nothing made it easy to actually follow — turning a
proven procedure into a skill still meant hand-authoring a SKILL.md from
scratch each time. This closes that gap.

## Step 1 — Ground it in what actually happened, not an idealized version

Before writing anything, answer: what did I (or the user) actually do, in
what order, and *why* did each non-obvious step exist? Pull this from the
real conversation/transcript, not a generic best-practices version of the
task. If the user just says "write a skill for X" with no prior context in
this session, ask them for the concrete example or incident that motivated
it — a skill grounded in a real case is worth far more than one grounded in
a guess. The best skills already in this repo (`verify-etsy-mutations`)
open with a "Why this exists" section naming the exact incident, files,
and function names involved — that's the bar to match, not generic advice
a search engine could produce.

If a step in the procedure exists because of a specific failure mode
(a bug that was hit, a wrong assumption that cost time, a real edge case),
that reasoning is exactly what the skill must preserve — see
`code-style.md`'s "dated root-cause comments" convention and apply the
same discipline to skill-writing: never write WHAT a step does (that's
obvious from reading it), always capture WHY it exists when it's not
obvious.

**Sanity check before committing to this:** has the procedure actually
proven itself, or is this canonizing a first-time guess? `automation-
workflow.md` frames the real signal as "the second time a procedure
repeats." If this is a one-off that hasn't been tested more than once,
say so to the user rather than silently treating it as settled — their
call whether to write it up anyway.

## Step 2 — Check for overlap before adding a new file

```bash
ls .claude/skills/
```

Read the `description` field of anything that sounds adjacent. A
near-duplicate skill is worse than no skill — it splits future trigger
matching and rots independently. (Concrete example from this session: a
proposed "Anti-AI" skill turned out to duplicate the already-installed
`avoid-ai-writing` skill almost exactly — caught by this exact check
before any file was written.) If real overlap exists, extend the existing
skill instead of adding a new one.

## Step 3 — Name the capability, not the incident

Kebab-case, describes what the skill *does* going forward
(`verify-etsy-mutations`, not `fix-price-bug-aug-20`). The incident that
motivated it belongs in the skill's body as grounding, not in its name.

## Step 4 — Write the SKILL.md

Match this repo's existing first-party format exactly (see
`.claude/skills/verify-etsy-mutations/SKILL.md` as the reference):

```markdown
---
name: <kebab-case-name>
description: "<one sentence, written as a trigger condition: 'Use this
skill when...' or 'After X happens, do Y before Z.' This is what gets
matched against a task to decide whether to load the skill, so it must
name the concrete situation, not just the topic.>"
---

# <Title>

## Why this exists (<date> incident, if grounded in one)
<The real, specific situation that made this worth writing down. Name
real files, functions, error messages, action ids -- whatever makes this
unmistakably about a real case, not a hypothetical.>

## <The actual procedure, as concrete numbered/titled steps>
<Each step should be followable by a fresh Claude session with zero
memory of this conversation. Include the "why" inline wherever a step
would look arbitrary or skippable without it.>
```

Keep it as short as it can be while staying concrete — a skill that's a
wall of generic advice gets skimmed and ignored; one grounded in a real
case with real file paths gets followed.

## Step 5 — Never add a first-party skill to SOURCES.md

`.claude/skills/SOURCES.md` is explicitly scoped to third-party,
fetched-from-elsewhere skills only (its own header says so). A skill
written by this process is first-party — do not add an entry there. This
is a documented trap: it's easy to assume every skill needs a SOURCES.md
row and pollute a file that's specifically a provenance/license ledger for
external code.

## Step 6 — This is stage 2, not stage 3

Per `automation-workflow.md`, writing the skill is not the same as
automating it. Don't wire the new skill into a cron loop, a background
agent, or an `_EXEC_COMMANDS` entry as part of this same step — a skill
gets invoked deliberately and manually until its output has proven
trustworthy across a few different real situations. Promoting it to
unattended automation is a separate, later decision, made only after that
track record exists.

## Step 7 — Show the draft before treating it as final

Naming and scope are judgment calls the user may want to adjust. Write
the file, then say what you named it and why, and give the user a chance
to redirect before moving on — don't silently commit a new skill and
consider the job done without that checkpoint.
