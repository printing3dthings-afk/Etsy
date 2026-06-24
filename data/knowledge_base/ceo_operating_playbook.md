# CEO Operating Playbook — Decision Frameworks for Frank

*On-demand reference only. Not baked into every system prompt — call `read_knowledge_base_doc`
when a decision genuinely depends on one of these frameworks. Written as rules and decision
trees, not literature review. Source: condensed CEO/business-operator research, June 2026.*

---

## 1. Weekly Flight-Check Metrics (Leading vs. Lagging)

A one-person shop drowns if it only watches revenue — revenue is a *lagging* indicator that
moves weeks after the decision that caused it. Watch leading indicators weekly so problems are
visible before they show up in the bank account.

| Indicator | Type | Why it leads |
|---|---|---|
| Listing views (7-day) | Leading | Drops here precede a revenue drop by 1–3 weeks |
| Click-through rate (views → clicks) | Leading | Thumbnail/title problem shows here first |
| Conversion rate (clicks → orders) | Leading | Photo/price/description problem shows here first |
| Favorites/saves | Leading | Early signal of demand before purchase intent matures |
| Revenue, order count | Lagging | Confirms what leading indicators already predicted |
| Refund/case rate | Lagging | Confirms a quality-gate failure already happened |

**Rule:** if a leading indicator drops 2 weeks running, treat it as a signal worth investigating
*now* — don't wait for the lagging revenue number to confirm it. By the time revenue confirms it,
the fix is already a week late.

---

## 2. Bezos One-Way vs. Two-Way Door Framework

Before staging or recommending any action, classify it:

- **Two-way door (reversible):** a price test, a new tag set, a title edit, a new listing draft.
  Reversing costs little. **Bias toward speed** — stage it, let Scott approve, move on. Don't
  over-analyze a reversible decision.
- **One-way door (hard to reverse):** deleting a listing, deactivating a long-running listing
  with sales history, large bulk edits (>10 listings), any change to business structure
  (S-corp election, legal entity), publishing a product line that required real production work
  to build. **Bias toward deliberation** — lay out the downside explicitly before recommending it,
  even if Scott didn't ask for the downside.

**Rule:** never apply one-way-door caution to a two-way-door decision (that's how good ideas die
from analysis paralysis) and never apply two-way-door speed to a one-way-door decision (that's
how avoidable damage happens).

---

## 3. Pre-Mortems Before Committing Real Production Time

Before recommending Scott commit real production time (a new product line, a new theme bundle,
a structural pricing change), run a pre-mortem: *"Assume this failed six months from now — what's
the most likely reason?"* Common failure modes already seen in this shop's own history:
- Built a product nobody searched for (no validated keyword/demand check first)
- Photos looked AI-generated/fake (violates the CARDINAL CHECK — instant trust loss)
- Price didn't match perceived value tier
- Cannibalized an existing listing's sales rather than adding net-new revenue

State the most likely failure mode out loud in the recommendation, not just the upside.

---

## 4. Explicit Kill Criteria — Decide the Exit Before You Enter

Every new initiative (a new product, an ad campaign, a sticker pack line) should have its kill
criteria set *before* launch, not improvised after the fact when sunk-cost bias is already active.

- **Ads:** kill at $30 spend with zero orders (already a hard rule in CLAUDE.md's Etsy Ads
  Strategy section). Kill after 30 days if ROAS < 1.5x with no upward trend.
- **New listing:** if it has zero favorites/saves and near-zero views after 2–3 weeks (past the
  new-listing boost window), the keyword/demand thesis was wrong — flag for Scott to reconsider,
  don't keep iterating photos on a listing nobody is searching for.
- **New product line (e.g. a new planner SKU):** if the first listing in the line underperforms
  the shop's median by 50%+ after 60 days, pause expansion of that line rather than building the
  next 3 variants on an unproven base.

**Rule:** when proposing a new initiative, state the kill criterion in the same message as the
proposal. A recommendation with no exit condition is incomplete.

---

## 5. Three-Bucket Etsy Decline Triage

When views/conversion drop, sort the cause into exactly one bucket before recommending a fix —
each bucket has a different (and non-overlapping) remedy:

1. **Shop-wide (quality score / policy):** all or most listings drop together. Check for a
   recent policy violation, a removed listing, or a bulk edit that looked automated. Remedy:
   stop editing, let the score recover over weeks — there is no shortcut (see CLAUDE.md's
   Ranking Recovery Playbook).
2. **Listing-specific (this one listing dropped, others didn't):** check title length (>70
   chars), recent edit (2–3 week dip is normal and expected), photo/thumbnail CTR, or a price
   change made too early (<30 days after going live). Remedy: matches the specific cause — don't
   touch the other 9 listings.
3. **Category-wide / seasonal:** the whole niche's search volume moved (e.g. back-to-school
   keywords drop in October). Remedy: nothing to fix — this is normal seasonality, not decline.
   Misdiagnosing bucket 3 as bucket 1 or 2 wastes effort fixing something that isn't broken.

**Rule:** always check bucket 3 (seasonality) first — it's the cheapest to rule out and the most
commonly misdiagnosed as a real problem.

---

## 6. SKU-Renewal ROI Rule

Etsy listing fees renew every 4 months or per sale ($0.20 each). Before recommending Scott keep
renewing a listing that hasn't sold:
- If a listing has had zero sales and near-zero views for 2+ renewal cycles (8+ months), the ROI
  of the $0.20 renewal is negative relative to the opportunity cost of a fresh listing slot.
- Flag it for Scott's review rather than auto-renewing or auto-deactivating — this is a
  one-way-ish door (deactivating loses any accumulated search history) so it goes through
  Action Center, never auto-executed.

---

## 7. Automate-vs-Human Escalation Threshold

Use this threshold, consistent with CLAUDE.md's Autonomy Boundaries section, when judging whether
a new task should become an automated tool or stay manual:
- **Automate** when: the task is repeated weekly+ AND has a deterministic, checkable correctness
  rule (e.g. tag length, file validation, price-tier lookup).
- **Stay manual** when: the task requires emotional judgment (review responses, negative-review
  replies), one-off pricing/feasibility judgment (custom orders), or touches money/legal/identity
  in a way a wrong automated guess can't cheaply undo.
- **When unsure which side a new recurring task falls on:** default to manual once, log how it
  went in `ceo_learnings.md`, and only propose automating it after it's been done the same way
  3+ times with no judgment calls needed.

---

## 8. Andon-Cord Quality Gates (Stop the Line, Don't Ship Around It)

Borrowed from Toyota's andon cord: any worker who spots a defect stops the line rather than
letting it pass downstream where it's more expensive to fix. Applied here:
- If a quality gate fails (digital file validation, photo CARDINAL CHECK, title/tag length), the
  listing stops — full stop — until fixed. Never stage a listing "to get Scott's eyes on it
  anyway" with a known failing gate; that erodes the gate's meaning and trains Scott to
  re-verify everything himself, defeating the point of automation.
- This is the same standard as CLAUDE.md's "If any gate fails → listing is blocked. Fix first.
  Publish never comes before truth." This playbook entry exists to generalize that listing-level
  rule to every gated process Frank runs, not just listings.

---

## 9. Financial Review Cadence

Matches CLAUDE.md's Weekly & Monthly Operational Cadence — restated here as the CEO-level "why":
- **Weekly (leading indicators):** catch problems while they're still cheap to fix.
- **Monthly (full health check):** catch trends a single week of noise would hide.
- **Quarterly (taxes, structure, competitive review):** catch structural decisions (S-corp
  threshold, pricing strategy, new product line) on a cadence slow enough to avoid reacting to
  noise, fast enough to not miss a year of compounding the wrong choice.

---

## 10. S-Corp Election Sliding Scale

Already detailed in CLAUDE.md's Business Structure & Tax section — restated as a decision rule:
- Below ~$50k consistent annual net profit: stay sole prop / single-member LLC. The S-corp
  compliance overhead (payroll, separate filing) costs more than it saves at this scale.
- $50k–$80k+ consistent annual net profit: S-corp election (Form 2553) becomes worth it — net
  savings after compliance costs is roughly $2,500–$4,500/yr at $100k net profit.
- **"Consistent"** means net profit trend over the trailing 12 months, not a single good quarter
  or a single big order. Don't recommend election off one strong month.

---

## 11. Checklist Over Gut Feel

Every pre-publish gate in this codebase (quality gate, photo CARDINAL CHECK, SS-series pre-publish
checklist) exists because "looks good" is not a gate — a checklist with a pass/fail per item is.
When Frank is asked to judge something subjective ("does this listing look ready?"), the correct
answer is to run the relevant checklist from CLAUDE.md and report which items pass/fail, not to
give an overall vibe-based yes/no.

---

## 12. "Decide Once" Standing Rules

Recurring decisions that have already been settled should not be re-litigated from scratch every
time they come up — that wastes Scott's attention on a decision already made. Standing rules
already in force (treat these as decided, not open questions):
- Pricing tiers per product category (CLAUDE.md pricing tables) — don't propose a new price
  point without a specific reason tied to data (a price test result, a competitor shift).
- The Action Center approval gate for every mutating action — never propose bypassing it, even
  for a "obviously safe" case. If a case seems obviously safe, that's a reason to make approval
  fast, not a reason to skip it.
- AI disclosure on every AI-generated listing — not optional, not case-by-case.

When a genuinely new situation doesn't fit an existing standing rule, that's worth bringing to
Scott as a real decision — but don't manufacture a decision point out of something already
settled.

---

## 13. Blameless Postmortem Culture

When something breaks (a failed deploy, a bad batch of photos, an API outage), the `ops_runbook.md`
entry and any escalation report should describe what happened and what will change, never assign
blame — including never blaming "the AI" or "the model" in a way that avoids stating the concrete
mechanism that failed. A postmortem that says "the script had a bug in the retry logic" is useful;
one that says "something went wrong" is not. Specificity is the point, not fault-finding.
