# For Claude — Overnight Improvement Brief (Fri Nov 13, 2026)

*Ready to paste into `business/muse_claude/`. Prepared by Benson from the overnight five-lane improvement pass (full report: Benson-side `overnight-business-improvement-2026-11-13/REPORT.md`). Business/public information only. Nothing here has been pushed or sent — Scott sees the choices first, per the standing rules.*

**Two corrections that change clocks you may be working to:**
1. **Click Into Celebration closes Nov 29, 2026** (MakerWorld's own contest post; winners Dec 4) — not Dec 2. Tin Clicker promotion finishes by Nov 28.
2. **Printmas 2026's official mechanics are unverified** — no official contest page found. The "comment-a-keyword" mechanic in the wild is entrants' own Instagram funnels. Don't build to Printmas rules we haven't seen; the scene asset in Ask 5 is useful either way.

---

## Part 1 — Design-lane briefs (ready to file, priority order)

Format per PIPELINE.md §1: outcome, context, exact deliverable, acceptance check Benson can verify. Gate references are to QC-PIPELINE.md (G0 brief → G1 geometry → G2 slice → G3 render read → G4 profiles → G5 physical print → G6 release).

### BRIEF A — Bottom-face mirrored text: fix Label Tile + Monogram Keychain, audit the repo (TOP of design lane — takedown-risk class)

**Outcome:** No shipped OnBrandCraftz file prints any text or mark mirrored. Label Tile and Monogram Keychain corrected at source, re-exported, re-rendered; every other repo design audited for the same defect with a written verdict per design.

**Context:** Label Tile (Sjack7 Private 3555518): the shipped file's text sits on the bottom/build-plate face (z 0–0.6) and prints mirrored — its gallery swap is HELD. Monogram Keychain (Sjack7 Private 3555680): underside "OBC" mark (z 0.00–0.60) reads reversed; swap proceeded (renders honestly show what prints) but the source fix is owed. Precedent: MakerWorld removed the Private Sundial model on 2026-11-12 for "inconsistent model information." QC-PIPELINE G1 already requires the OBC mark to read correctly from the underside, verified from a below-view render of the actual mesh — label text never got the same check.

**Deliverable:**
1. Per design, at source (SCAD): either (a) mirror the glyph geometry for text staying on the build-plate face so it reads correctly printed, or (b) move the text to the top face. State route + why per design. Re-export shipping .3mf(s), version bump, PRINTING.md updated.
2. A repo audit table (e.g. `design-audit/bottom-face-text-2026-11.md`): every design whose source places text/mark geometry on the z=0 face — name, text affected, verdict (correct-as-printed / mirrored / no bottom text). Include the OBC mark on every building in scope.
3. New renders per fixed design: the standard set INCLUDING an underside view of the actual shipping mesh showing text reading correctly.

**Acceptance (Benson verifies):** below-view renders of both fixed shipping files show all text reading correctly; Benson re-runs G1 (watertight, min-wall bands unchanged or re-measured, flat base z=0); audit covers 3 random spot-checks; on landing Benson rebuilds profiles (G4) and lifts the Label Tile hold. Designs stay Private.

### BRIEF B — Gingerbread Tin + Canister screw lid: close the G1 stall parked since Nov 4

**Outcome:** The screw-lid rework (Sjack7 3518210) passes G1 honestly so Benson can rebuild and swap all 6 profiles. Geometry fix OR corrected measurement with documentation — either accepted; a waiver is not.

**Context:** Nov 4 measured evidence (HEAD 95ecf7b8): product gate failed on the min-wall line only (floor 1.2 mm) — tin 1st pct 0.00 mm (3.06% below one bead, median 10.49 mm) · lid 0.46 mm (0.89%) · lid_closed 1.03 mm (0.28%) · canister 0.00 mm (1.71%) · cookie 0.58 mm (0.22%). Fit OK (thread holds, unscrew path clears), fragility clean, fidelity advisory only (~0.012% volume at thread roots). QC-PIPELINE G1 now explicitly sanctions measuring thread roots as their own band. The Oct 30 shipped version failed the same line and printed fine; the clicker itself is G5 ✅. **Benson-side note before filing: Benson verifies which lid version is live on 3518210** (Nov 2 record shows a swap underway; Nov 4 record parks a rework — the baseline must be confirmed so the fix targets the right version).

**Deliverable (either route, stated per part):**
- (a) Geometry: thicken thread-root regions so each part's structural min-wall 1st percentile ≥1.2 mm, thread fit unchanged. Re-export `gingerbread_tin_clicker.3mf` + `gingerbread_tin_canister.3mf`, version bump, PRINTING.md updated.
- (b) Measurement: re-issue gate readings with thread-root samples as their own band (root-band minimum stated separately from the structural percentile) + a short written justification in the design notes. Any proposed root-band floor is stated as a number — no silent threshold change.

**Acceptance:** Benson re-runs G1 and reproduces the claimed readings; fit/fragility/fidelity re-issued alongside (no hidden regression); on pass Benson rebuilds all 6 profiles and swaps onto 3518210; design re-enters at G1 → G2 → G4 → G5 (Scott prints lid fit).

### BRIEF C — Valentine Lantern 1: remodel the couple figures to pass G3

**Outcome:** The couple reads as two real people at thumbnail size — modelled detail, not flat round-head cutouts — passing G3 on re-render in time for a mid-December G5 print. **Hard clock: test prints mid-Dec, listings Jan 3. A December landing has no G5 window and the design misses Valentine 2027.**

**Context:** Scott's direct feedback 2026-10-30: figures to be remodelled with real detail. Valentine picks are closed (Lantern 1 + Lantern 5 + Chocolate Shop). Lantern 1 is the personalised-base hero; its scene IS the product. Standing gates in full: walls ≥1.2 mm structural, panes 0.8–1.0 mm, no supports, flat base, watertight, tea-light cavity unchanged unless stated.

**Deliverable:** (1) Remodelled figures in source — distinguishable heads/faces or hair mass, shoulders/torso shaping, a readable pose/gesture between the two figures; silhouette detail, not surface texture alone (G3 is judged on the matte-white render). (2) Re-exported shipping file(s), version bump, PRINTING.md updated (print time/weight changes stated). (3) Grey-studio renders (three-quarter / front / top, true colours, 1400 px) + one zoomed crop of the couple at real scale.

**Acceptance:** Benson's personal G3 read against the Oct 30 feedback line by line; G1 re-run clean (thin limbs/necks are the expected fragility failure — design against it); Scott sees the re-render before anything proceeds (his verdict originated the stall and closes it). Then G2 → G4 → mid-Dec G5.

### BRIEF D — Santa's Workshop v2: print-ready export + lighting rework in ONE landing

**Outcome:** A print-ready v2 Benson can slice (G2) and Scott can test-print (G5) — parts, .3mf, PRINTING.md figures, lighting rework embodied — in a single landing. Oldest open brief (Oct 24/28); everything downstream is queued behind this one export.

**Context:** Oct 24: v2 still design-stage, no .3mf; four virtual fix passes were needed for fine detail (dentil cornice 36°/35° overhangs, slate joints, brick coursing) to survive virtual slicing. Oct 28 lighting rework from Scott's real v1 print: ONE interior chamber, 3 tea lights. Light standard: panes 0.8–1.0 mm at flame height (window band ~30–40 mm above interior floor), structural walls ≥1.2 mm, frames full thickness, cavity ≥46 mm floor per tea light. QC-PIPELINE G2 names this design's dentil cornice as the detail-survival test case.

**Deliverable:** (1) Part files + print-ready combined .3mf for `victorian_santas_workshop_v2`, version recorded, print time + filament weight in PRINTING.md measured from the export (not estimated). (2) Lighting rework in the same export: one open chamber (no accidental dividers), 3-tea-light cavity meeting the floor standard, pane band specification met. (3) White (as-printed) studio renders from the exported file — closes the Oct 24 renders request in the same landing.

**Acceptance:** G1 on the shipping file (watertight, per-band min-wall, bbox within P1S plate with margin, flat base z=0, chamber count = 1, cavity matches the 3-light claim, OBC mark correct from below-view render); G2 with the corrected Bambu recipe (zero slice errors, no supports, dentil cornice / slate joints / brick coursing visibly surviving). Then G4 to Sjack7 Private and Scott's G5 print as the detail verdict. No listing change asked or implied.

### Ranked asks 5–9 (one line each; full reasoning in Benson's Lane 5 file)

5. **Chubby Axolotl (G3 fail):** redesign-or-closure decision package — one reworked form proposal vs an explicit park, so the stall stops ageing silently.
6. **Minimal G5 coupon pack:** small cheap test coupons that unblock named G5 stalls without full prints — a Bayonet Jar close-fit coupon and a Gear Heart full-assembly mesh coupon (Gear Heart's whole-heart mesh is currently coupon-only evidence).
7. **Per-design FACTS.md + 5 standard renders for every completed design** (incl. an underside render — would have caught Brief A's defect class at source). Standing Benson ask, restated.
8. **Sweet Shop corrected file:** the registry's public section claims 16 designs at G6 while its own Sweet Shop row says G1 ⏳ — the corrected file closes the only caveated "public" row.
9. **QC checker tool** (already briefed): automated per-band min-wall + bottom-face-text-orientation checks at export time, so Briefs A and B's defect classes fail in the pipeline, not on MakerWorld.

### MakerWorld-side Claude asks (from the funnel lane)

10. **Printmas / village "scene" asset:** a composed group arrangement + cover treatment of the free village (real-print based, professional-cover standard) usable as (a) a possible bundle-listing cover, (b) the collection cover, (c) a contest-entry hero image — plus per-building keyword cards for the Instagram funnel.
11. **Standardised @P3DT description template:** benefit opener → Boost line → Included Versions/Profiles → Print Guide (filament, layer heights, no supports, Bambu Handy path, full-range compatibility — never P1S-only) → sibling cross-links + collection link → licence/Patreon line → contest line when applicable. Benson verifies against the live Tin Clicker listing before rollout.
12. **January bench prep:** next 4–6 Sjack7 models prepped for public release (ASCII filenames, Standard + Optimized + Multicolour profiles, real-photo checklist per model) so the Tue/Fri cadence survives the Christmas window — Valentine/lantern pieces first per the standing timeline.

**Scott-side items Claude asked about that Benson cannot do (noted, not briefed):** print the full Snowflake Screen this weekend; review the Flexi Otter draft; book a Claude session for corrected Etsy listing times. Benson is surfacing these to Scott separately.

---

## Part 2 — Media-kit order draft (owed to the Nov 13 growth meeting)

*DRAFT ONLY — nothing has been added to Scott's Order List and nothing bought. Prices appear ONLY where verified on a live page opened Nov 13, 2026 (B&H); re-verify at order time. Priority if budget is tight: items 1 + 2 + 3 first, then 9, then 4.*

| # | Item | Why / gap it fixes | Price |
|---|---|---|---|
| 1 | Neewer 660 Pro RGB LED panel (CRI 97, 3200–5600K + RGB, barndoors) | Controlled warm key light so real-print covers and glow shots stop fighting room light; the core gap behind flat covers | **$89.99 verified** — https://www.bhphotovideo.com/c/product/1732697-REG/neewer_66600136_660_pro_rgb_led.html/overview (stand + NP-F batteries NOT included) |
| 2 | Savage #56 Fashion Gray seamless paper, 53" × 36' | Implements the standing plain light-grey backdrop rule for group/Patreon shots; kills household clutter in gallery photos | **$44.99 verified** — http://www.bhphotovideo.com/c/product/486218-REG/Savage_56_1253_Widetone_Seamless_Background_Paper.html (shipping extra) |
| 3 | Manfrotto PIXI Smart mini tripod + phone clamp | Stable, repeatable framing for covers and macro work; reproducible cover angles across designs. Caveat: doesn't tilt a full 90° — overhead is item 5's job | **$36.13 verified** — https://www.bhphotovideo.com/c/product/1860050-REG/manfrotto_mkpixiclmii_bk_pixi_smart_mini_tripod.html |
| 4 | RØDE Wireless Micro, 2-person (USB-C) | Clean spoken audio for maker-talk/behind-the-scenes reels (printer ASMR stays on the phone mic by design). **Confirm Scott's iPhone connector before ordering — the Lightning version's price is unverified** | **$86.00 verified (USB-C version)** — http://www.bhphotovideo.com/c/product/1849609-REG/rode_wimicroc_wireless_micro_2_person_ultracompact.html |
| 5 | Overhead/vertical rig (articulating arm or boom) | Top-down angle is missing entirely: painting/marker tests, assembly, flat-lay village layouts | price unverified |
| 6 | Softbox/diffusion for the panel | Kills harsh shadows on small buildings; "magazine" vs "workbench" covers | price unverified |
| 7 | Second stand + small fill/accent light | A dim warm side fill is what separates a lit building from its backdrop in glow shots | price unverified |
| 8 | Pocket grey/white-balance card + colour checker | Stops matte-white prints drifting yellow/blue between cover sessions; grid consistency | price unverified |
| 9 | Motorised display turntable (~20–30 cm) | Slow rotation of the finished lit building = the proven glow/reveal video format with zero camera movement | price unverified |
| 10 | Microfibre cloths + blower + matte-black foam board | Dust/fingerprints read huge in macro covers; foam board = instant flags and black glow backdrops | price unverified |
| 11 | Spare NP-F batteries + charger | Item 1 ships without batteries; battery power = shooting village set-ups away from the bench | price unverified |
| 12 | Fast high-capacity USB-C offload drive | Prevents "storage full" mid-shoot; keeps 4K originals for re-cuts at the 5:1 video ratio | price unverified |

## Part 3 — December 20 plan draft (owed to the Nov 13 growth meeting)

**Goal:** by Dec 20, OnBrandCraftz has (1) a working non-Etsy checkout for files + physical prints, (2) captured the Cyber + early-December Christmas window without missing the shipping cutoff, and (3) closed the Tin Clicker contest cleanly — with Etsy restored as primary if/when Scott's card fix lands.

**Key dates:** Nov 23–Dec 1 Etsy "Cyber Specials" 25% off — CONDITIONAL on Etsy reopening; if still suspended, the same framing runs on the new store ("Etsy is temporarily down — same sale, here"; copy is a new pattern, needs Scott's approval) · **Nov 29 Click Into Celebration closes (corrected date)** — final Tin Clicker push lands BEFORE, results/thank-you post after · ~Dec 12 Christmas physical-order cutoff · Dec 20 assessment.

- **Week 1 (Nov 16–22) — Build the bridge.** Scott makes ONE call: the file-store platform (benchmark verdict: Payhip Free — 5%/sale, $0/mo, no $100 payout minimum — vs Gumroad's 10% + $0.50 + processing and a $100 minimum/7-day hold). Benson builds the store draft (pages from existing listing copy/photos, standing licence lines, Etsy-matched prices) for Scott's content approval; nothing publishes without it. Meta Shop checkout URL pointed at the store (Meta retired in-app checkout in Sept 2025 — Shops are website-checkout only and invisible without a URL; digital-product catalogue eligibility unverified, so treat Meta Shop as January infrastructure with December upside if it clears). Daily spotlight continues; CTAs dual-tracked (free → MakerWorld, paid → new store, Etsy line only if reopened). First Tin Clicker build-up post.
- **Week 2 (Nov 23–Dec 1) — Cyber window.** 25% off everything on Etsy IF reopened, otherwise on the store with identical framing. One hero offer per day, buildings rotating; glow-first video leads; one send-cue per caption; keyword-first captions. Physical prints featured early (shipping runway); "order by Dec 12" appears from Nov 29. All standing series slots run, each ending on the CTA correct for its building (free vs paid — never "FREE" on a paid building).
- **Week 3 (Nov 29–Dec 8) — Contest close + physical peak.** Nov 29 morning: final Tin Clicker push; after close, results/thank-you post, no entry changes. Physical-print urgency week: real photos, gift framing, DM-to-order via the public PayPal.me link for one-offs (tracked shipping; PayPal.me suits physical, not files — no cart, no auto-delivery; its fee rate is unverified, check in-account before pricing on it), store checkout for standard items. A Village bundle offer may be drafted — new offer, Scott approves first. Patreon licence line rides physical-print content aimed at makers.
- **Week 4 (Dec 9–15) — Cutoff discipline.** Dec 12: physical CTAs come down the same day (queued/owned content swapped to digital-only versions by Benson; live-post edits flagged to Scott same day). Pivot copy: "Missed the post? The file prints tonight." Digital is 100% of the push Dec 13–15. Colour-Your-Own stays OUT unless its existing gates (marker test + photos) have cleared.
- **Week 5 (Dec 16–20) — Close-out + January setup.** Last digital push Dec 16–18, sales copy winds down Dec 19–20. Dec 20 assessment from platform-owned numbers only: sales by channel, best buildings, what the bridge earned vs what Etsy-down cost — no estimates. January prep drafted: Valentine timeline (listings Jan 3), Meta Shop as infrastructure, keep-or-retire the bridge store decided on the Dec 20 numbers.

**Split — Benson alone:** research, store/catalogue drafts, copy drafts in proven patterns, proven-format posting + live verification, CTA/cutoff swaps, social log, Dec 20 numbers pack. **Scott only:** platform choice, payment connections/credentials, Etsy billing fix (already his), Frank one-taps, new-offer/copy approvals, print-capacity and cutoff calls, and anything publishing his name/address (Printables Store — recommendation: don't).

*— End of brief. Full lane research sits with Benson; ask for any lane file by number.*

---

## Brief E — Gear Heart: axle clips need to be much stronger (Scott, 2026-11-14 ~01:16 EST)

**Evidence:** Scott printed the FULL Gear Heart assembly (gold gears, dark plate/clips) on 2026-11-13 evening. The gears mesh and turn — the mesh verdict you were waiting on is PASS (video of the gears turning hands-free is on file with Benson). **But Scott's verdict on the axle clips the gears ride on: "The clips the gears go on need to be much stronger."** Treat the clip/pin as a G5 fail: the design does not clear release until the clips are reworked.

**Ask:** redesign the gear axle clips for substantially higher strength/retention — your call on the mechanism (thicker post, stronger clip geometry, more material at the base, a different retention scheme) as long as: gears still spin freely with the proven +0.20 mesh clearance unchanged, no supports, parts still print flat on the plate, and the assembled look stays the same from the front. If the failure mode matters for the fix, Benson is confirming it with Scott (snapped vs popped-off vs flex/wobble) and will append it here.

**Gate note:** Gear Heart is already up Private on Sjack7 (model 3604645, 4 profiles) with the page stating the full assembly was not yet test-printed — that statement is now stale in our favour on mesh, but the model stays Private and does not advance toward any public release until the clip fix prints and passes.

**Failure mode CONFIRMED by Scott 2026-11-14 08:43 EST: one of the clips SNAPPED / CRACKED.** This is a structural failure, not retention or flex — design the fix for fracture strength first (material at the clip base and finger roots, stress concentrations, and print-orientation layer lines across the clip are the suspects to address). A coupon re-test of the reworked clip should precede a full heart reprint.
