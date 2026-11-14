# LANE 3 — Social Growth: NEXT Experiments for OnBrandCraftz

**Prepared:** Fri 2026-11-13 (EST) · **Type:** Research / preparation ONLY — nothing posted, published, or changed on any platform.
**Sources read first:** Nov 12 category benchmark (`~/workspace/research_notes/3d-print-social-category-benchmark-20261113-0221/report.md`), Ours Audit (`~/workspace/your_files/social-dashboard/category-benchmark-2026-11-12/ours-audit.md`), Experiment Log E-001 → E-011 (`~/workspace/your_files/social-dashboard/experiments.md`).
**Excluded by instruction:** TikTok-specific work (crosspost-only, decided Nov 13); the two already-queued research-to-choice items — (1) keyword-comment mechanic, (2) Trial Reel formats (POV / Expectation vs Reality / "This is your sign") — are NOT re-proposed here. Also not re-proposed: anything already running/queued as E-002–E-011 (binary-choice captions, slide-2 hook styles, posting time, YT title pattern, mixed-media carousel, function-first Trial cut, single-CTA bar, clean-look, numbered ASMR compilation E-011).

## Baselines used for every read below (from our own stored data, named in the Ours Audit / Experiment Log)

| Metric | Baseline | Source |
|---|---|---|
| IG regular reels — views | median ≈98 (mean 98.2, n=28, Oct 28–Nov 11) | Format-split connector pull, Nov 11 |
| IG regular reels — avg watch time | ≈6.5s | IG connector read, Nov 8 |
| IG reels — shares / follows per 1,000 views | 0 / 0 on all 8 sampled reels | IG connector read, Nov 8 |
| IG comments per post | ≈0 across platforms in stored record | Ours Audit §1/§5 |
| YouTube — views/post | avg 375.5 (Nov 7); tracker median 257 | Low-view tracker |
| YouTube long-form / compilations (ours) | 13–48 views, flatlined ("From Idea to Shelf" 17; All-15-Village compilation 48) | Ours Audit §4 |
| Print Cam | YT Ep 001 = 243 views (series ceiling so far) | Ours Audit §2 |
| Maker Spotlight | Pilot (Rocco) built, not yet posted — no baseline exists yet | MEMORY / readiness board |
| Stories | **No stored data at all** — not in `published.json`, never measured | Ours Audit §1/§5 |

**Why these five:** the benchmark's proven drivers are already partly covered (compilations = E-011, glow-first = locked, keyword mechanic = queued separately). The gaps in *our* data are: (a) watch time / rewatch is our weakest IG signal (6.5s avg, 0 sends/follows), (b) Stories are a daily output with zero measurement, (c) YouTube is our strongest platform but its required 2×/month long-form slot has **zero** November episodes in production, (d) our audience framing is 100% maker-facing while the benchmark's #3 view-driver is non-maker lifestyle, and (e) Maker Spotlight is generous-first but has no distribution multiplier built in.

---

## E-012 — Seamless-loop endings on product / Print Cam reels — **DO-NOW** · Rank 1

- **Hypothesis:** A reel whose final frame *is* its first frame (the lit house in the dark, identical framing) earns replays, lifting average view duration and views above the regular-reel baseline — because the benchmark's winners all "end on product, loop back to the dark glow" with no outro/logo card (Benchmark §3), and 2026 Shorts/Reels guidance consistently identifies seamless looping / rewatch as a heavily weighted retention signal (Kompozy 2026 Shorts optimisation guide: "Design the last frame to flow into the first… a Short that loops invisibly can double its effective watch time"; Teleprompter.com 2026 Shorts guide: loop rate and average view duration drive distribution).
- **Exact format / ONE variable:** Ending treatment only. Test arm: last ~1s cross-fades/match-cuts back to the exact frame-1 glow shot, **no end card, no logo, no "thanks" beat**. Control arm: our current ending (end card / natural stop). Everything else held constant — glow-first opening (locked), 10–20s length, keyword-first caption, one send cue, Ronan/ASMR audio rules, same building class, same slot. Runs inside product spotlights and Print Cam episodes that were already going out; **no extra posts**.
- **Scott's time: ZERO.** Pure edit decision in the existing build. No filming, no printing, no in-app step.
- **Benson/Claude effort:** Low — Benson adds a loop-match step to the reel build checklist (~15 min per edit until templated); Claude can pre-flag which existing clips already start/end on compatible framing.
- **Metric & read horizon:** IG connector insights at **72h** per reel (decision read, per the loop's standard): average view duration / % of runtime viewed, views, and sends+follows per 1,000. Judged across **≥4 reels (≥2 per arm)** vs baseline avg watch ≈6.5s and median ≈98 views. YouTube Shorts legs read at 7 days vs 375.5 avg baseline as supporting evidence.
- **Kill / graduate:** GRADUATE (lock loop endings into the reel build standard) if the loop arm's median avg-watch-% beats the control arm by **≥30%** across the set AND views are not lower. KILL if avg-watch-% is within ±10% across ≥4 reels — rewatch engineering isn't our constraint; log it and stop spending edit time on it. Split result (watch up, views flat) → ITERATE once on the 60s compilation format only.

## E-013 — Story Poll Decides: followers vote the next Print Cam / Versus hero building — **DO-NOW** · Rank 2

- **Hypothesis:** A one-tap Story poll that *actually decides* a real production choice (which building is next week's Print Cam hero / next Versus hero — enforcing the existing Rotate-the-Building rule) converts our currently unmeasured Stories into measurable engagement, and the voted-for episode out-performs its series baseline because voters return to see "their" pick. Benchmark support: ForgeCore's "comment what I should make next" threads become his idea pipeline (430 comments on the chess-set countdown, Benchmark §2 #5); 2026 Stories guidance is consistent that poll/quiz stickers are the lowest-friction, highest-tap interactive format (one tap vs typing a comment) — VerTech 2026 Stories roundup and Sked Social's 2026 Stories tactics, via search.
- **Exact format / ONE variable:** Pre-episode Story sequence only. Test weeks: 24h before a Print Cam episode, post ONE Story — two real lit-building photos side by side, native Poll sticker, exact question "Which one prints next?" — then a results Story when the episode posts, with the link sticker (locked standard) to the episode. Control weeks: episode posts with the normal promo Story (link sticker, no poll). The episode itself, caption, and slot are unchanged. Distinct from E-003 (binary-choice *caption* prompt): this is the Stories surface, the vote binds a real production decision, and the follow-through/results Story is part of the mechanic.
- **Scott's time: ZERO.** Benson runs Stories through the existing pipeline route; the poll uses buildings already printed and photographed. ⚠️ One operational check for Benson at run time (not Scott): confirm the instagram-cli Story editor supports the native Poll sticker the way it already supports link stickers; if it doesn't, this drops to CHOICE (app-only step) rather than asking Scott ad hoc.
- **Benson/Claude effort:** Low-medium — Benson adds poll + results Stories to the Print Cam run sheet and **starts logging Stories in the social log** (closing the Ours Audit's "Stories: no stored record" gap is a deliverable of this experiment, win or lose). Claude: no build needed; optionally pre-ranks building pairs with available lit photos.
- **Metric & read horizon:** Primary: poll votes + Story views/replies per sequence (creating the first-ever Stories baseline). Secondary: the voted episode's views at **72h (IG) / 7 days (YT)** vs Print Cam baseline (YT Ep 001 = 243; IG regular-reel median ≈98).
- **Kill / graduate:** GRADUATE if, across **≥3 poll cycles**, voted episodes beat the Print Cam baseline by **≥25%** on views OR poll participation averages ≥10 votes/sequence with replies > 0 (engagement exists where comments are ≈0). KILL if votes average <5/sequence across 3 cycles AND voted episodes show no lift — the follower base is too small for voting mechanics yet; revisit at 500 followers and log that threshold.

## E-014 — The Stitched Village: monthly YouTube long-form built ONLY from proven Shorts — **DO-NOW** · Rank 3

- **Hypothesis:** A themed 8–12 minute YouTube long-form stitched from our *already-proven* glow timelapses/Shorts (e.g. "Every Christmas Village House, Printed — Ambient ASMR Edition") out-performs our original long-form baseline (13–48 views) by an order of magnitude, because the benchmark shows exactly this repurposing working: Stan 3D's 10:50 stitched compilation "57 Oddly Satisfying 3D PRINTED Fidgets | ASMR" held **123K views** while his channel's original long-form peers do not drive his growth (Benchmark §3). Our own caveat is priced in: our *untested* All-15-Village compilation flopped at 48 views — so this version differs in two disciplined ways: (1) it stitches **only clips that individually cleared 250+ views** (our top-10 are all 366–1,062), and (2) it is titled/packaged as ambient ASMR viewing, not as a "compilation of our posts."
- **Exact format / ONE variable:** Source-selection + packaging only, against the failed All-15 baseline. Top-clips-only (≥250 stored views each), printer-ASMR bed throughout, chapter markers per building, end-screen to the newest Short (per the locked "every Short links to long-form" relationship, run in reverse). ONE episode, placed in the currently **empty** November long-form slot (2/month rule, Nov 9 — zero in production at Nov 12 per the Ours Audit). No new footage.
- **Scott's time: ZERO.** Every clip already exists in the workspace; no filming or printing. (If a gap clip is missing, the episode ships without that building — Scott is not asked to fill gaps.)
- **Benson/Claude effort:** Medium, one-off — Benson selects/orders clips from stored view data and builds the stitch + chapters (~1 session); Claude can draft chapter titles/descriptions (keyword-first, itemised list with a MakerWorld link per building — the Printsculptors caption-as-shopping-list pattern, Benchmark §3).
- **Metric & read horizon:** YouTube views + average view duration + watch hours at **7 days and 28 days** (long-form compounds slowly; the 28d read is the decision read) vs the long-form baseline of 17–48 views.
- **Kill / graduate:** GRADUATE (make it the standing monthly long-form recipe, alternating village/haunted themes) if it clears **≥250 views at 28 days** (≈5–15× baseline, i.e. at least Print Cam's single-episode level sustained over 10 minutes). KILL the stitched-compilation route if it lands <100 views at 28 days — that would confirm distribution, not content selection, is our long-form constraint, and the second monthly slot should be reassigned (e.g. to a Maker's Blueprint long cut) instead of repeating this.

## E-015 — Mantel-First: the same village, framed for decor lovers instead of makers — **CHOICE** · Rank 4

- **Why CHOICE, not DO-NOW:** this is a first-time audience/category framing (non-maker buyers), which under Scott's approval model needs his exact yes on the framing before it runs — even though execution needs none of his time for the pilot.
- **Hypothesis:** A 15–20s "mantel transformation" reel — frame 1 an ordinary mantel/shelf, then building-by-building the lit village appears, closing on the exact glow shot we already use — out-reaches our maker-framed product reels with *non-followers*, because the benchmark's #3 view-driver is product-in-use lifestyle for non-makers: Kristina's printed-play-food Reel passed **6M views** (Bambu Lab, 19 Oct 2026) opening on finished products *in use* with the text "I stopped buying play kitchen toys… and started printing them instead" (Benchmark §1 #3). Our transfer line: "I stopped buying Christmas village houses…" — aimed at the collector audience we already joined on Facebook (Christmas Village Collectors, 24.9K; The World of Christmas Villages, 108.9K).
- **Exact format / ONE variable:** Audience framing only. Same buildings, same glow footage/photos, same length and caption rules — the ONE change is narrative point of view: room-first transformation + replacement-claim on-screen text in second 1, **zero printer, zero print-process beats**. Pilot built entirely from existing staged/lit photos (photo push-in transformation sequence) — honestly labelled a pilot limitation, the same one logged on E-002/E-008.
- **Scott's time: ZERO for the pilot** (existing photos only). ⚠️ **FLAGGED:** if this graduates, the strong version needs ONE thing only Scott can supply — a 15–20s phone clip of the real mantel/shelf being dressed with the lit village. That ask should be made once, at graduation, with the pilot's numbers — not before.
- **Benson/Claude effort:** Medium — Claude builds the transformation sequence from the professional-cover/lit photo set; Benson QCs it against the animation/photo-led quality bar and writes the non-maker caption variant (keyword phrases decor buyers search: "Christmas village display", "mantel decor").
- **Metric & read horizon:** IG **72h**: non-follower % of views, views vs ≈98 median, sends per 1,000 (decor content is the natural send-to-a-collector-friend case; baseline sends = 0, so any sustained sends > 0 is signal). Facebook leg read at 7 days vs FB baseline median 7 views — the collector groups' Page audience is the warmest FB surface we have.
- **Kill / graduate:** GRADUATE if the pilot beats the IG regular-reel median on views AND non-follower share is the majority of reach (proof it escaped the maker bubble). KILL if it performs at/below a normal product reel — decor framing without real room footage doesn't travel, and we don't ask Scott for the mantel clip.

## E-016 — Maker Spotlight as an Instagram Collab post (co-authored with the featured creator) — **CHOICE** · Rank 5

- **Why CHOICE, not DO-NOW:** Spotlight's locked positioning is "generous-first, no ask." A Collab invite *is* a small ask (the creator must tap Accept), so Scott decides whether that exception is worth it — starting with the already-approved Rocco pilot or holding it for STAN 3D (208K, second in the running order).
- **Hypothesis:** Publishing the Spotlight carousel as a native Instagram Collab (co-authored) puts it on both grids and into both audiences with pooled engagement, materially beating a tag-only Spotlight post. External evidence: Emplifi's analysis of 520,000+ Instagram brand posts (H1 2026, via Socinova/Lilach Bullock roundups) found accepted Collab posts generated **roughly 5× the interactions of regular posts for profiles under 10,000 followers**, with the caveat that this is association, not proven causation; Meta's own description confirms the post appears on each collaborator's grid and reaches each audience after acceptance.
- **Exact format / ONE variable:** Distribution authorship only. Identical Spotlight carousel (same slides, same caption, same credit, slide-2 second cover, music-owed flag per the carousel-music standard) — the ONE change is inviting the featured creator as collaborator at publish instead of tag-only. Everything about the feature itself stays generous-first: their best work, no pitch, no follow-back request; the invite is the only new element, and a declined/ignored invite simply publishes as the normal tag-only post (no follow-up nudge — one invite, no chasing).
- **Scott's time: ZERO.** Benson sends the invite through the normal posting flow. No DM from Scott, no filming.
- **Benson/Claude effort:** Low — Benson adds the invite step + an accept/decline log line; Claude: nothing new (pilot carousel already built).
- **Metric & read horizon:** **7 days** (carousel read standard): views, likes+comments, profile follows attributed in IG insights, and non-follower reach — vs (a) our IG carousel baseline (median 20.5 views, format-split Nov 11) and (b) the tag-only Spotlight pilot if it posts first; if Collab is used *on* the pilot, the carousel baseline is the comparator and the bar is set higher to compensate.
- **Kill / graduate:** GRADUATE (Collab becomes the default Spotlight ask, one invite per feature) if the Collab episode beats the carousel baseline by **≥3× on views and ≥3× on interactions** (deliberately set below the claimed ~5× — we graduate on our numbers, not Emplifi's). KILL if the invite is declined/ignored twice in a row OR an accepted Collab shows no lift — Spotlight reverts to pure tag-only generous-first permanently, and the relationship value is kept unspent.

---

## Considered and parked (not proposed, so they aren't re-litigated later)

- **Fail-and-fix episode (benchmark §1 #4 — fail timelapses are comment-heavy):** genuinely promising, but there is no verified fail clip in the workspace yet. It only works at zero Scott-time if Benson first finds a usable detach/spaghetti moment in the existing P1S chamber replays Scott already cleared for posts. Parked pending that asset audit — Scott must never be asked to *produce* a failure.
- **Advent "Day N of 24" daily series (benchmark §5, play 3):** strong seasonal mechanic, but it adds up to 24 extra posts in December and collides with the locked daily pipeline + series-readiness rule. If Scott wants a December ritual, E-013's weekly vote is the sized-down version already proposed above.
- **Facebook Groups-native posting test:** our FB Page baseline is dire (median 7 views, 0 likes on 46/46 stored posts) and the collector groups are large — but group posting carries admin-approval and Page-identity risks that deserve their own scoped proposal with the group rules re-read first, not a line item here.

## Ranking summary

| Rank | Experiment | Tag | Scott time | Primary metric / horizon |
|---|---|---|---|---|
| 1 | E-012 Seamless-loop endings | DO-NOW | Zero | IG avg watch % + views, 72h, ≥4 reels |
| 2 | E-013 Story Poll Decides next Print Cam | DO-NOW | Zero* | Poll votes (new baseline) + episode views, 72h/7d |
| 3 | E-014 Stitched Village YouTube long-form | DO-NOW | Zero | YT views/watch time, 7d + 28d decision |
| 4 | E-015 Mantel-First non-maker framing | CHOICE | Zero for pilot; one mantel clip ONLY if it graduates | IG non-follower reach + sends, 72h |
| 5 | E-016 Spotlight as IG Collab post | CHOICE | Zero | Carousel views/interactions, 7d |

\* E-013 conditional on Benson confirming Poll-sticker support in the existing Story route at run time; otherwise it converts to CHOICE rather than creating Scott-side work.

## Sources relied on

- Internal (primary): Nov 12 category benchmark report, Ours Audit, and Experiment Log E-001–E-011 — paths at the top of this file. All baselines and category numbers (Printsculptors/Stan/ForgeCore/Kristina/lethimprint) are quoted from the benchmark, which cites its own live/index sources per claim.
- External (fresh, this lane, via web search 2026-11-13):
  - Kompozy, "YouTube Shorts optimization tips (2026)" — seamless-loop / rewatch guidance: https://kompozy.io/how-to/youtube-shorts-optimization-tips
  - Teleprompter.com, "How to Go Viral on YouTube Shorts (2026)" — loop rate + average view duration as ranking signals: https://www.teleprompter.com/blog/how-to-go-viral-on-youtube-shorts
  - Emplifi H1-2026 Collab analysis (~5× interactions for <10K-follower profiles; association, not causation) as summarised at: http://socinova.com/coffee-shop-collab-posts/ and https://www.lilachbullock.com/how-to-use-instagram-collab-feature/
  - VerTech, "Instagram Stories Ideas" (2026) — poll/quiz sticker series as the lowest-friction Story engagement format: https://vertechlimited.com/instagram-stories-ideas/
