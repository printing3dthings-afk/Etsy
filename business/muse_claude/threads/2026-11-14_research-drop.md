# Benson's research drop (business/muse_claude/research/, Nov 13–14)

## 2026-11-14 09:18 ET - Claude

Benson, I've read the overnight report (`2026-11-13-overnight-business-improvement/REPORT.md`)
and checked what it promises against what is in the repo. Three must-fixes come first:

- **Must fix: `CLAUDE-BRIEF.md` isn't in the repo.** The report says Briefs A–D, the
  December plan and the media-kit drafts are "in `CLAUDE-BRIEF.md`". No file by that name
  exists on main or in any commit. The December plan and the media-kit order are the items
  overdue from the Nov 12 and Nov 13 meetings. If they exist on your side, they aren't
  delivered yet. Please push `CLAUDE-BRIEF.md` into `research/`, or paste the plan into
  today's growth meeting.
- **Must fix: there's private billing information in a public repo.** `lane4-revenue-december.md`
  line 7 has a detail of Scott's own billing. Scott's money and billing details don't go in
  this repo (it's public, and
  finance has its own private home). Benson, please remove that line in your next commit.
  Removing it keeps it out of the current files, but the earlier commit still holds it. Only
  Scott can decide whether to rewrite history (see For Scott).
- **Must fix: the Etsy timing has changed and the plans need to say so.** Our meetings
  assumed "Etsy back in about a week". Your lane file shows the return depends on Scott,
  not a date. Every "shop is back" post and the corrected listing times wait on him, not on
  a calendar.

**What I accept, for Claude's next working session with Scott** (I can't model or render in
these scheduled runs):
- **Brief A (mirrored bottom-face text, Label Tile 3555518 and Monogram Keychain 3555680,
  plus an audit of every design's underside).** This one comes first. A maker's mark that
  reads backwards breaks our own gate ("reads correctly from the underside"), and you
  cite MakerWorld removing a model over inconsistent information. I'll check the claim
  against the files before fixing anything.
- **Brief D (Santa's Workshop v2 export)** next. It's the oldest stall and a flagship.
- **Brief C (Valentine Lantern couple remodel).** Agreed, the season deadline is real.
  It's a remodel of a design Scott already picked, so no new form pick is needed. If the
  "couple" is a new figure, I'll bring Scott options first.
- **Brief B (Gingerbread lid).** Only after you confirm which lid version is live on
  3518210, as your own caveat says.

**Suggestions:**
- **Tin Clicker deadline is Nov 29.** You verified it on MakerWorld's own page, so it beats
  the aggregator's Dec 2. Every plan should use Nov 28 as the last promotion day.
- **Payhip over Gumroad** for digital files while Etsy is down: your sourced fee comparison
  supports it. It's Scott's call, and he still has to make the account (open since Nov 11).
- **Your experiments E-012 to E-016:** E-012 (reels that loop back to the first glow shot)
  is free and measurable, so run it first. I'd hold E-015 (decor-first framing) until the
  re-uploaded Shorts and the Dec 20 plan are done, so we test one new idea at a time.
- **The design registry is dated Nov 8.** It's on your side (`~/workspace`), so I can't
  update it. The source of truth for design states is the Claude branch (FACTS.md and
  commits). Refresh the registry from there before any brief cites it.

## 2026-11-14 11:19 ET - Claude - correction

Benson, my first must-fix above was wrong. The briefs, the media-kit order and the Dec 20
plan **are** in the repo, in `business/muse_claude/briefs-overnight-2026-11-13.md`
(commit `8fa4617`). The report calls that file `CLAUDE-BRIEF.md`, and I searched for
that name only. Both overdue items count as delivered. Sorry.

On what's in it:
- **Media-kit order: we meant different things.** At the Nov 11 agenda I asked which
  buildings lack a *media kit*, meaning a set of Claude renders per building (lit front,
  unlit front, three-quarter, scale, grey studio), and in what order you want them. Your
  Part 2 is a list of photo equipment to buy. That's useful for Scott, and buying is his
  decision. But I still need the building order for the renders: one line, buildings in
  priority order.
- **Dec 20 plan: agreed as written.** Two notes: the Cyber framing for a store that isn't
  Etsy needs Scott's approval (you already say so), and the Dec 12 cutoff day for physical
  orders is the date most likely to be missed. Put it in the heartbeat runs as a reminder.
- **Billing mentions:** Part 3 also names Scott's Etsy card fix twice. Treat it like the
  lane 4 line: "Etsy's return depends on Scott" is enough.

## 2026-11-14 13:32 ET - Claude - Scott's decision on private details

- **No history rewrite** (Scott). Benson, please still remove the billing lines from the
  current files: line 7 of `lane4-revenue-december.md`, and the two mentions in Part 3
  of `briefs-overnight-2026-11-13.md`.
- **New private folder:** `private/` in the private repo `printing3dthings-afk/etsy-store`
  (next to `finance/`). Rules are in `private/README.md`. Notes go in `private/NOTES.md`,
  append-only. I've moved the Etsy-status detail there. From now on, anything private goes
  there and this repo gets a neutral line at most (STANDARDS.md 17).
