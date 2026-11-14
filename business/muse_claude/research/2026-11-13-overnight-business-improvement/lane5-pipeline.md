# Lane 5 — Claude Design Pipeline Analysis
**Date:** 2026-11-13 (overnight) · **Lane:** 5 — Design pipeline / stalls
**Scope:** LOCAL FILE WORK ONLY. Nothing pushed to GitHub, nothing posted/published/uploaded. No personal financial data.
**Primary sources read in full:**
- `~/workspace/your_files/claude-pipeline/PIPELINE.md`
- `~/workspace/your_files/claude-pipeline/design-registry.md` — header states: *"States as of 2026-11-08"*
- `~/workspace/your_files/claude-pipeline/QC-PIPELINE.md`
**Corroborating sources (used only where the registry is stale — flagged per row):**
- `~/workspace/goals/christmas-village-print-file-listings/hidden_files/claude-request-list.md` (the Benson→Claude brief list referenced in PIPELINE.md §1)
- Daily memory notes 2026-11-10 / 2026-11-11 / 2026-11-13 (Label Tile, Monogram, Fold Stand v4, Bayonet Jar v3, Gear Heart landings after the registry date)
- Local build folders: `fold-stand-v4-profile/BUILD-NOTES.md`, `gear-heart-upload/BUILD.md`, `bayonet-jar-v3-profile/BUILD-NOTES.md`

**QC gates (QC-PIPELINE.md, "The gates"):** G0 brief → G1 geometry → G2 slice → G3 render read → G4 profiles → G5 physical print → G6 release. *"Nothing goes public before G5. No exceptions."*

---

## 1. Stall map

Citation format: [file → section/row]. "Registry" = design-registry.md. "Request list" = claude-request-list.md.

### G5 — Physical print (the systemic bottleneck — confirmed)

| # | Design(s) | Gate | Since | What's actually blocking |
|---|---|---|---|---|
| 1 | **Most of the 46 private render-rollout designs (Sjack7)** | G5 ⏳ | Registry date 2026-11-08 | Registry → "Private library (46 render-rollout designs)": *"All 46: G4 ✅ for gallery presentation… Most are **G5 ⏳ — never physically printed.** They stay private until printed."* Blocker is not Claude and not Benson tooling — it is Scott's printer time / print queue. No source fix unblocks these; only a prioritised print order + minimal coupons (see Ranked Ask #6) reduce the cost per clearance. |
| 2 | Fold Stand — registry lists **v2 (3549832)**, superseded by **v4** | G5 ⏳ | v2: registry 2026-11-08; v4 swap 2026-11-10 | Registry → Private table, "Fold Stand v2 (3549832) \| G5 ⏳ \| Unprinted; first-print hinge checks owed". Post-registry update (memory 2026-11-11/12): v4 Standard 4108153 + Optimized 4108180 are live Private on the same model 3549832, v3 deleted. G5 is still open in substance: *"print the hinge-test plate first"* — twist-lock pivot + print-in-place prop (0.40 mm measured clearance in `fold-stand-v4-profile/BUILD-NOTES.md`) are physically unproven. The task brief's "Fold Stand v4 G5 open" is **correct in substance, but the registry still says v2** — registry is stale here. |
| 3 | Bayonet Jar v3 (Sjack7 model 3550364) | G5 ⏳ | Landed 2026-11-10, profiles uploaded 2026-11-11 | **Not in the registry at all** (post-dates it). Memory 2026-11-11: all 32 v3 profiles (16 sizes × Std/Opt) built/uploaded Private, but *"No v3 size has been physically printed yet and the clockwise close is untested — v2's printed jar is the only proven one."* Blocker: one Scott print of the smallest size (D40 H30, 31 min / 25 g class) would prove the clockwise bayonet close for the whole family. |
| 4 | Gear Heart (Sjack7 Private 3604645) | G5 ⏳ — partial | Coupon landed 2026-11-11; full profiles uploaded 2026-11-13 | **Not in the registry.** `gear-heart-upload/BUILD.md` → "Upload notes": *"the whole heart is **not yet test-printed**, only the gear mesh coupon was"* (ENGINEERING.md §7). Memory 2026-11-13 confirms the live page honestly states *"full assembly NOT yet test-printed (gear-mesh coupon only)."* Task brief's "G5 open (coupon only)" is **verified correct**. Blocker: Scott printing the full plate + gears and confirming snap-post assembly / gear mesh in the assembled heart, not just the coupon. |
| 5 | Word Sign "FUCK" (3536516) | G5 ⏳ | Registry 2026-11-08 | Registry → Private table: *"Flat 240 variant built + accepted; print result/photo owed; 'Flat 240' profile verification still to confirm Private."* Blocker: Scott print + photo, plus a Benson per-profile Private check. |
| 6 | Otter joint (post-registry, for completeness) | G5 ⏳ — coupon stage | 2026-11-11 | Memory 2026-11-11: `otter_joint_test.3mf` (~28 min) landed as a test piece only; *"the otter itself waits for his test results."* Same pattern as Gear Heart: Claude correctly gated the full design behind a cheap coupon. Not MakerWorld-queue eligible until the coupon passes. |

### G1 — Geometry (source fixes Claude owns)

| # | Design | Gate | Since | What's actually blocking |
|---|---|---|---|---|
| 7 | **Gingerbread Tin Clicker + Canister (3518210; public contest model 3560658)** | G1 ❌ | **2026-11-04 — parked 9 days at analysis date** | Registry → Private table: *"Screw-lid rework fails min-wall percentile; with Claude since Nov 4 — profile swap parked. Clicker itself G5 ✅ (Scott's test print Oct 30: 'It works')."* Request list → 2026-11-04 entry gives the measured evidence: repo checks at HEAD 95ecf7b8 *"PRODUCT GATE FAILED on all five gates, every one on the min_wall line only (floor 1.2mm): tin 1st pct 0.00mm… lid 0.46mm… canister 0.00mm…"* Everything else passes (fit, fragility, fidelity advisory only). The brief already offers Claude two honest routes: (a) thicken thread-root regions, or (b) prove the percentile is a sampler artefact at thread roots and fix the gate's banding with documentation. QC-PIPELINE.md G1 now requires thread roots *"measured as their own bands"* — so route (b) is now spec-supported, which makes this the most unblockable G1 stall. Blocks: rebuild/swap of all 6 profiles on 3518210. Note the irony on record in the same brief: the Oct 30 shipped version failed the same line and *"printed fine."* |
| 8 | **Label Tile (3555518)** | G1 ❌ (defect class: bottom-face text) — **not in registry** | Defect held 2026-11-13 | **Not in the registry** (registry predates the finding). Memory 2026-11-13 (two entries, L457/L520): *"its text sits on the bottom/build-plate face and prints mirrored… 'PARTS' reads reversed as printed"*; Wave 1 gallery swap *"deliberately HELD… pending a Claude source fix (mirror the glyphs or move the text to the top face) before any public use, due to the same inconsistent-model-information takedown risk as the Sundial."* Prepared renders exist and honestly show the flawed file. This is a G1 failure under QC-PIPELINE.md G1 (*"OBC mark orientation verified from a below-view render"* / flat base at z=0) even though the affected text is the part label, not only the mark. Task brief **verified correct**. |
| 9 | **Monogram Keychain (3555680)** | G1 ❌ (same defect family, lower severity) — **not in registry** | Flagged 2026-11-13 | Memory 2026-11-13 L458: *"its underside 'OBC' mark inlay also reads REVERSED in use (bottom-face text)."* Difference from Label Tile: its Wave 1 gallery swap **proceeded** (5 images, verified live Private, memory 2026-11-13 L795) because the renders honestly show what prints — but *"the source bug is Claude's to fix on both designs before any public use."* Task brief **verified correct**, with that severity distinction. |
| 10 | Sweet Shop (public, free set) | G1 ⏳ — treated as not passed | Outstanding at registry date 2026-11-08 | Registry → Public designs: *"Sweet Shop: corrected file still outstanding — its current public file predates the fix; free launch of the corrected version, multicolour profiles and group-photo cover all wait on it. Treat as G1 ⏳ until the corrected file lands and re-passes."* This is the only public design not cleanly at G6 in substance, despite the section heading "G6 complete" (see Contradictions). |

### G0 — Brief / identity

| # | Design | Gate | Since | What's actually blocking |
|---|---|---|---|---|
| 11 | Santa's Workshop v2 | G0/G1 ⏳ | Briefs open **2026-10-24 / 2026-10-28 — oldest open design stall (20 days)** | Registry → Private table: *"Parts/.3mf export + lighting rework briefs open since Oct 24/28 (one chamber, 3 tea lights)."* Request list → 2026-10-24 entry (marked "GATING"): *"export the v2 part files and a print-ready .3mf… v2 is still design-stage (no .3mf as of Oct 24)"* after four virtual fix passes on dentil cornice / slate joints / brick coursing; plus 2026-10-28 lighting rework (one chamber, 3 tea lights, thin panes at flame height per the 2026-10-24 light-transmission standard in the same list). QC-PIPELINE.md G2 cites *"the Santa's Workshop v2 dentil-cornice lesson"* — detail survival must be proven in slice, then the physical print is the verdict. Blocker is entirely on the Claude export side; Benson/Scott cannot print what has not been exported. |
| 12 | "Candy Tower" identity | G0 ❌ | Unconfirmed since **2026-11-04** | Registry → Private table: *"'Candy Tower' = Candy Lighthouse vs Wrap-Around Tower still unconfirmed since Nov 4; blocks its Multicolor profile."* Memory 2026-11-04/05 corroborates: Scott repeated "Candy tower" after being asked; no design literally named Candy Tower exists. **This is a Scott decision, not a Claude task** — no brief to Claude can resolve it. See Contradictions for the post-registry complication (Candy Lighthouse itself launched public 2026-11-13). |

### G3 — Render read (remodels Claude owns)

| # | Design | Gate | Since | What's actually blocking |
|---|---|---|---|---|
| 13 | Chubby Axolotl (3549332) | G3 ❌ | Registry 2026-11-08 | Registry → Private table: *"Shipping mesh reads as a segmented stack, not an animal; rendered matte white (repo pink is a presentation colourway). Needs redesign or Scott's written overrule."* QC-PIPELINE.md G3 codifies it as "the Chubby Axolotl rule": silhouette must read as the object at a glance. Note: its Wave 1 gallery swap completed 2026-11-13 (6 images, Private) — that was honest presentation of the current mesh, **not** a G3 pass. Task brief **verified correct**. |
| 14 | Valentine Lantern 1 | G3 ❌ | Scott feedback **2026-10-30** | Registry → Private table: *"Couple figures to be remodelled with real detail (Scott, Oct 30); re-render owed before approval."* Request list → 2026-10-30 entry is the originating brief (Scott direct: figures look like "flat round-head cutouts" — wording from Scott's standing feedback, summarised in MEMORY.md as *"make the people look better, better detail"*). Time-critical: Valentine 2027 plan on record is designs in Nov, test prints mid-Dec, listings Jan 3 — a G3 fail here eats the test-print window. Task brief **verified correct**. |

### Customizer / PMM — cross-gate stall (sits between G4 and G6; registry logs it as its own ❌)

| # | Design | Gate | Since | What's actually blocking |
|---|---|---|---|---|
| 15 | Name Ornament (3549622) | Customizer ❌ | Briefs 2026-11-05, 2026-11-09 | Registry → Private table: *"Centering patch proven in the PMM editor; PMM Save fails ('Failed to download SCAD file', 6 attempts). Scott's 2-minute manual edit is the remaining route."* Request list → 2026-11-09 entry: full Tombstone-shaped rebuild still asked of Claude (no offset() chains on text, one top-level object at origin, no color() split, advance-table name measurement, centring acceptance for "Amy"/"Olivia"/"Christopher" within ±1 mm). **Major post-registry development — see Contradictions:** the PMM Save failure was confirmed 2026-11-13 as a *platform-wide* wall, so part of this stall is no longer Claude-fixable at all. |
| 16 | Love Letter Mailbox (3549413) | Customizer ❌ | Diagnosis filed 2026-11-05/06 | Registry → Private table: *"Awaits Claude bisect/rebuild (diagnosis filed Nov 5–6)."* Request list → 2026-11-05 (evening) + addenda: both customizers time out on PMM Generate and fail Handy cloud slicing; diagnosis vs the working Tombstone customizer identifies nested offset() chains on glyphs (Ornament 13 sites, Love Letter 18, Tombstone 1), multi-colour top-level re-evaluation, and Love Letter's 411-point pocket polygon as suspects. Ask on file: bisect first, then rebuild Tombstone-shaped. Its Wave 1 gallery swap completed 2026-11-13 (8 images, Private) — the *model* is presentable; the *customizer* is the stall. |
| 17 | Standing Heart Lantern (3519443) | Customizer ⏳ | Brief open since **2026-10-31** | Registry → Private table: *"Needs a self-contained customizer SCAD (brief open since Oct 31)."* Request list → 2026-10-31 entry: flatten four library includes into one `standing_heart_customizer.scad`, expose NAMES/DATE (defaults "Emma & James" / "02.14.2027"), swap Playfair Display if MakerWorld's renderer lacks it. Same Valentine-season clock as #14. Its gallery swap completed 2026-11-13 (5 images, Private); customizer still owed. |

### G2 / G4 / G6 — no named stalls on record
- **G2 (slice):** No design is listed as stuck at G2 in the registry or request list. G2 failures on record (Santa v2 dentil detail, Gift Box path-conflict class) were lessons absorbed into the gate, not open stalls.
- **G4 (profiles):** Registry states all 46 private designs are G4 ✅ for gallery presentation and *"Upload backlog: EMPTY"* (Standing counts, 2026-11-08). Post-registry builds (Fold Stand v4, Bayonet Jar v3, Gear Heart) also cleared G4. G4 is **not** a bottleneck.
- **G6 (release):** The 16 public designs are recorded G6 complete, with the Sweet Shop caveat (#10) as the single exception in substance.

### Stall count summary
- **Distinct named stalls: 17 rows** (rows 2–17, with row 1 counted once as the bulk G5 class).
- **By gate:** G0: 2 (Santa v2 shared with G1; Candy Tower) · G1: 4 (Gingerbread, Label Tile, Monogram, Sweet Shop; + Santa v2 shared) · G2: 0 · G3: 2 (Axolotl, Valentine Lantern 1) · G4: 0 · **G5: 1 bulk class covering most of 46 private designs + 5 named (Fold Stand v4, Bayonet Jar v3, Gear Heart, Word Sign, Otter)** · Customizer/PMM cross-gate: 3 (Name Ornament, Love Letter, Standing Heart).
- **By owner of the next action:** Claude: 9 (Gingerbread, Label Tile, Monogram, Sweet Shop corrected file, Santa v2, Axolotl, Valentine Lantern 1, Love Letter rebuild, Standing Heart SCAD — Name Ornament partially, see Contradictions) · Scott (print or decision): 7 (bulk G5, Fold Stand, Bayonet, Gear Heart, Word Sign, Otter, Candy Tower identity) · Platform (MakerWorld PMM): 1 shared (Name Ornament / all PMM Saves).
- **Oldest stalls:** Santa's Workshop v2 export (2026-10-24, 20 days), Standing Heart customizer (2026-10-31), Gingerbread lid (2026-11-04).

---

## 2. Ranked Claude asks (highest leverage first)

Ranking logic: (designs unblocked × severity of risk) ÷ Claude effort, with seasonal deadlines weighted.

1. **Bottom-face mirrored-text fix — Label Tile + Monogram Keychain + a repo-wide audit for the same defect class.** One root cause, two named designs, and an unknown tail: every design with text/mark geometry on the build-plate face is a candidate. Label Tile is already *held* from its gallery swap over takedown risk (the Sundial precedent: MakerWorld removed even a Private model for "inconsistent model information" on 2026-11-12). The audit converts a two-design fix into a permanent G1 checklist line, exactly as QC-PIPELINE.md's failure loop requires. → **Brief A.**
2. **Gingerbread Tin + Canister screw-lid: close the G1 min-wall stall (thicken thread roots OR fix the gate banding with documentation).** Parked since Nov 4, blocks 6 profile rebuilds on the model that doubles as the public "Click Into Celebration" contest entry (closes Dec 2). QC-PIPELINE.md G1 now explicitly sanctions per-band measurement for thread roots, so Claude has a spec-backed route that did not exist when the stall started. Either route ends the stall; Benson does not need Claude to pick the harder one. → **Brief B.**
3. **Valentine Lantern 1 couple-figure remodel (G3).** Direct Scott feedback from Oct 30, still owed. Hard external clock: test prints mid-Dec, listings Jan 3. A remodel that lands in December has no G5 window and the design misses Valentine 2027 entirely. Also unblocks the Standing Heart customizer's season indirectly (same product family, same launch). → **Brief C.**
4. **Santa's Workshop v2: parts/.3mf export + lighting rework.** The oldest open brief (Oct 24) and the only flagship Christmas building still at design stage. Everything downstream (G2 detail-survival check, G5 print, any v2 listing swap) is queued behind a single export. The request on file is already precise (one chamber, 3 tea lights, panes 0.8–1.0 mm at flame height); it needs Claude execution, not a new brief design — the draft below re-files it with gate-tied acceptance so it cannot land as renders-only again. → **Brief D.**
5. **Chubby Axolotl redesign (G3) — or formal closure.** Silhouette must read as an axolotl (external gills, wide head, tapered tail) at thumbnail size in matte white, not only in the pink presentation colourway. Ranked below the seasonal items because it has no deadline and Scott holds a written-overrule option; but it should not sit as an indefinite ❌ — the brief should ask Claude for the redesign *and* state that if the form cannot pass G3 within the standing gates, Benson will bring Scott the overrule/delete choice (the Mochi Fox precedent, deleted 2026-11-09 for the same G3 class, shows the alternative is real).
6. **Minimal G5 coupon pack for the three named print-gate stalls.** Claude cannot print, but Claude *can* shrink Scott's cost per G5 verdict: (a) Bayonet Jar — confirm the D40 H30 is the designated proof size and, if the repo lacks one, add a bayonet-close coupon (lug + socket segment only) so the clockwise close can be proven in minutes, not a full jar; (b) Gear Heart — an assembly coupon showing one snap post + two meshing gears at full scale (the existing coupon proved gear mesh alone, not the post/assembly the full print must prove); (c) Fold Stand — hinge-test plate already exists and leads the v4 profiles, no new work, just confirm it is the G5 entry point in PRINTING.md. One small brief, three G5s made cheaper.
7. **Per-design FACTS.md + 5 standard renders for every stalled design (standing ask, re-stated).** For each design in the stall map: a FACTS.md (latest commit, version, gate state claimed, dimensions, light count, palette, profile list) plus the 5 standard renders (three-quarter / front / top / underside / detail). The underside render is the specific artefact that would have caught Label Tile / Monogram at G1 without a print or a gallery prep. This is the cheapest systemic fix in the list and directly feeds Benson's G1/G3 verification.
8. **Sweet Shop corrected file.** Named G1 ⏳ in the registry with no detail on what the correction *is* — before Claude can be briefed usefully, Benson needs to identify the correction from the design's own notes (see Unclear, §4). Ranked last not because it is unimportant (it is a *public* free design carrying a pre-fix file) but because the ask cannot be written precisely yet.
9. **QC checker tool (request list, 2026-11-08 — "top of the design lane").** Already briefed and open: one runner for G1–G2 (watertight, per-band min-wall, bbox/base, OBC-mark orientation, chamber/cavity, slice-data readback) with three known-verdict acceptance files. Not re-drafted below because the brief on file is complete; flagged here because Asks #1 and #2 both become one-command verifications once it lands, and its per-band min-wall check is the permanent form of the Gingerbread fix.

---

## 3. Brief drafts — READY TO SEND (staged locally only, NOT sent)

Format follows PIPELINE.md §1: outcome, context, exact deliverable, acceptance check Benson can verify, priority. File these on the Claude request list only on Scott's / parent direction.

---

### BRIEF A — Bottom-face mirrored text: fix Label Tile + Monogram Keychain, audit the repo for the defect class

**Priority:** Top of the design lane (takedown-risk class).
**Outcome wanted:** No shipped OnBrandCraftz file prints any text or mark mirrored. Label Tile and Monogram Keychain corrected at source, re-exported, and re-rendered; every other repo design audited for the same defect with a written verdict per design.

**Context Claude needs:**
- Label Tile (MakerWorld Sjack7 Private 3555518): Benson's Wave 1 gallery prep on 2026-11-13 proved from the shipped file that its text volume sits on the bottom / build-plate face and prints mirrored — "PARTS" reads reversed as printed. Its gallery swap is HELD and it must not go public in this state. Precedent: on 2026-11-12 MakerWorld removed the (Private) Sundial model for "inconsistent model information"; a backwards-text lead image invites the same action.
- Monogram Keychain (Sjack7 Private 3555680): same family — its underside "OBC" mark inlay reads reversed in use. Its gallery swap proceeded because the renders honestly show what prints, but the source fix is owed before any public use.
- QC-PIPELINE.md G1 already requires: OBC mark *"reads CORRECTLY viewed from the underside"* (standing design gate) and mark orientation *"verified from a below-view render of the actual mesh."* The Oct 24 mirrored-mark incident is the named G1 fail example. This defect survived because label text (not just the mark) was never given the same below-view check.

**Exact deliverable:**
1. For each of Label Tile and Monogram Keychain, at source (SCAD): either (a) mirror the glyph geometry for any text that must remain on the build-plate face, so it reads correctly on the printed part, or (b) move the text to the top face. State which route per design and why. Re-export the shipping .3mf(s), bump the version, update PRINTING.md.
2. A repo audit table (`design-audit/bottom-face-text-2026-11.md` or the repo's equivalent): every design whose source places text/mark geometry on the z=0 face — design name, text affected, verdict (correct-as-printed / mirrored / no bottom text). Include the OBC mark on every building in scope.
3. New renders per fixed design: the standard set **including an underside view of the actual shipping mesh** showing the text reading correctly.

**Acceptance checks (Benson will verify):**
- Below-view renders of both fixed shipping .3mfs show all text reading correctly (not mirrored).
- Benson re-runs G1 on both files: watertight, min-wall bands unchanged or re-measured, flat base at z=0.
- The audit table covers every design Benson spot-checks (Benson will pick 3 at random and verify the verdict from the mesh).
- On landing, Benson rebuilds the profiles (G4), swaps the Label Tile gallery with the re-made renders, and lifts the hold. Designs stay Private.

---

### BRIEF B — Gingerbread Tin + Canister screw lid: close the G1 min-wall stall parked since Nov 4

**Priority:** High — blocks the contest-entry model's profile swap; contest closes Dec 2, 2026.
**Outcome wanted:** The screw-lid rework for the Gingerbread Tin Clicker + Canister (Sjack7 3518210) passes G1 honestly, so Benson can rebuild and swap all 6 profiles. Either the geometry clears the gate, or the gate's measurement is corrected with documentation — Benson accepts either; what is not accepted is a waiver.

**Context Claude needs:**
- The full measured evidence is in the request-list entry dated 2026-11-04 (HEAD 95ecf7b8): product gate FAILED on all five parts on the min_wall line only (floor 1.2 mm): tin 1st pct 0.00 mm (3.06% below one bead, median 10.49 mm) · lid 0.46 mm (0.89%) · lid_closed 1.03 mm (0.28%) · canister 0.00 mm (1.71%) · cookie 0.58 mm (0.22%). Fit check OK (thread holds, unscrew path clears, 88 cm³), fragility clean, fidelity advisory only (~0.012% volume at thread roots).
- Since that brief was filed, QC-PIPELINE.md G1 has been written to require: *"thread roots and designed-thin panes measured as their own bands, not hidden in the whole-part percentile."* Route (b) below is therefore now the specified measurement method, not an exception.
- On record in the same Nov 4 brief: the Oct 30 shipped version failed the same line (tin 0.92 mm, lid 0.90 mm) and printed fine, and the clicker itself is G5 ✅ (Scott, Oct 30: "It works"). The stall is a measurement/geometry question, not a function question.

**Exact deliverable (either route, or one per part — state which per part):**
- **Route (a) — geometry:** thicken thread-root regions so each part's structural min-wall 1st percentile is ≥1.2 mm, thread fit unchanged (fit check still OK, unscrew path still clears). Re-export `gingerbread_tin_clicker.3mf` and `gingerbread_tin_canister.3mf`, version bump, PRINTING.md updated.
- **Route (b) — measurement:** re-issue the gate readings with thread-root samples reported as their own band (root band minimum stated separately from the structural percentile), plus a short written justification in the design's notes for why the root band's floor differs (thread geometry, bead width), so the checks *"read truthfully"* per the Nov 4 brief. No silent threshold change: any proposed root-band floor is stated as a number for Scott's call if Benson cannot trace it to the standing gates.

**Acceptance checks (Benson will verify):**
- Benson re-runs G1 on the re-exported files and reproduces the claimed readings within tolerance.
- Fit/fragility/fidelity readings are re-issued alongside (no regression hidden behind the min-wall fix).
- On pass: Benson rebuilds all 6 profiles and swaps them onto 3518210; the design re-enters at G1 per QC-PIPELINE.md's failure loop, then proceeds G2 → G4 → G5 (Scott prints the lid fit).

---

### BRIEF C — Valentine Lantern 1: remodel the couple figures to pass G3

**Priority:** High — seasonal deadline (test prints mid-Dec, listings Jan 3).
**Outcome wanted:** Lantern 1's couple reads as two real people at thumbnail size — modelled detail, not flat round-head cutouts — and passes G3 on re-render, in time for a mid-December G5 print.

**Context Claude needs:**
- Scott's direct feedback, 2026-10-30 (request-list entry of the same date; registry G3 ❌ row): the couple figures are to be *"remodelled with real detail"*; Scott's standing summary of the flaw is that the figures look like flat round-head cutouts. Re-render is owed before Scott's approval — nothing about the lantern body is in question.
- Valentine 2027 picks are closed decisions (Lantern 1 + Lantern 5 + Chocolate Shop/Shop 2, made 2026-10-30): designs Nov, test prints mid-Dec, listings Jan 3. Lantern 1 is the personalised-base hero of the set, so its scene *is* the product.
- Standing gates still apply in full: walls ≥1.2 mm structural, panes 0.8–1.0 mm, no supports, flat base, watertight, tea-light cavity unchanged unless the remodel forces a stated change. The scene must survive slicing at the design's fine features (G2 compares detail survival — the Santa v2 dentil lesson).

**Exact deliverable:**
1. Remodelled couple figures in source: distinguishable heads/faces or hair mass, shoulders/torso shaping, and a readable pose/gesture between the two figures — silhouette detail, not surface texture alone, because G3 is judged on the matte-white render.
2. Re-exported shipping file(s) for Lantern 1, version bump, PRINTING.md updated (any change to print time/weight stated).
3. Grey-studio renders (three-quarter / front / top, true colours, 1400 px per QC-PIPELINE.md G3) plus one zoomed crop of the couple at the scene's real scale.

**Acceptance checks (Benson will verify):**
- G3 read by Benson personally on the new renders: the couple reads as two people with detail at thumbnail size; Benson compares against the Oct 30 feedback line by line.
- G1 re-run on the new file: all standing gates pass; fragility check clean on the remodelled figures (thin limbs/necks are the expected failure — design against it).
- Scott sees the re-render before anything proceeds (his G3 call was the originating verdict; his approval closes it). Then G2 → G4 → Scott's mid-Dec G5 print.

---

### BRIEF D — Santa's Workshop v2: export the print-ready parts/.3mf + lighting rework (re-file of the Oct 24/28 gating briefs)

**Priority:** High — oldest open design brief (2026-10-24); gates every downstream step for the flagship building.
**Outcome wanted:** A print-ready Santa's Workshop v2 that Benson can slice (G2) and Scott can physically test (G5) — parts, .3mf, and PRINTING.md figures — incorporating the lighting rework, in one landing.

**Context Claude needs:**
- Request list, 2026-10-24 (marked GATING): v2 was still design-stage with no .3mf; four virtual fix passes were needed for the fine detail (dentil cornice at 36°/35° overhangs, slate joints, brick coursing) to survive virtual slicing. Benson's assessment on file: the physical P1S print is the real verdict.
- Request list, 2026-10-28: lighting rework from Scott's real print of v1 — **one interior chamber, 3 tea lights**. Combined with the 2026-10-24 light-transmission standard (same list): panes 0.8–1.0 mm vs structural walls ≥1.2 mm, frames full thickness, window band aligned to the flame zone (~30–40 mm above the interior floor), cavity ≥46 mm of floor per standard tea light (QC-PIPELINE.md G0/G1 standing gates).
- Registry state: G0/G1 ⏳, *"briefs open since Oct 24/28."* QC-PIPELINE.md G2 names this design's dentil cornice as the detail-survival test case.

**Exact deliverable:**
1. Part files + a print-ready combined .3mf for `victorian_santas_workshop_v2`, version recorded, with print time and filament weight in PRINTING.md (measured from the export, not estimated).
2. The lighting rework embodied in the same export: one open chamber (no accidental dividers), 3-tea-light cavity meeting the ≥46 mm-per-light floor standard, pane band at 0.8–1.0 mm with full-thickness frames, flame zone aligned to the window band.
3. White (as-printed) studio renders from the exported file — the 2026-10-24 renders request depends on this export and is closed by the same landing.

**Acceptance checks (Benson will verify):**
- G1 on the shipping file: watertight/manifold, per-band min-wall (structural ≥1.2 mm; panes in their 0.8–1.0 mm band), bbox within the P1S plate with margin, flat base at z=0, chamber count = 1, cavity floor space matches the 3-light claim, OBC mark correct from a below-view render.
- G2 with the corrected Bambu recipe: zero slice errors, no supports, and dentil cornice / slate joints / brick coursing visibly surviving in the slice at the known fine features.
- Only then: profiles (G4) to Sjack7 Private and Scott's physical test print (G5) as the detail verdict. No listing change is asked or implied by this brief.

---

## 4. Anything the files contradicted or left unclear

1. **Registry is dated 2026-11-08 and is stale in at least four places** — it is still the cited "source of truth" (PIPELINE.md, QC-PIPELINE.md) but: (a) it lists **Fold Stand v2** at G5 ⏳ where v4 has since replaced v3 on the model (Nov 10); (b) **Bayonet Jar v3 and Gear Heart do not appear at all**, though both landed Nov 10–13 and both sit at G5; (c) **Label Tile / Monogram Keychain do not appear**, though both carry the mirrored-text defect held/flagged Nov 13; (d) its standing counts (repo HEAD d89cfead Nov 6; Sjack7 103 models / 401 profiles Nov 6) predate at least the Bayonet (+32 profiles), Fold Stand v4, and Gear Heart uploads. **Recommendation (Benson-side, not Claude): refresh the registry before any brief is filed from it, or briefs will be written against superseded versions.** The task brief's stall list was more current than the registry on every one of these points — all seven task-supplied stalls verified as correct in substance.
2. **Name Ornament: the "Claude fix owed" framing is now only half true.** Registry + request list frame the stall as a Claude rebuild + a PMM Save failure. Post-registry memory (2026-11-13) records a **platform-wide PMM Save wall**: Save throws "Failed to download SCAD file" on *every* PMM customizer tested (Name Ornament ×7 through Nov 9; Soft Frame label customizer ×2 on Nov 13, where test generations *passed* in the editor). Conclusion on file: *"the SCAD and generation are fine, the Save path is broken."* So the Tombstone-shaped rebuild (request list, Nov 9) may still be worth doing for Generate/slice health, but **no Claude rebuild can clear the Save wall** — filing it as a pure Claude stall would send Claude at a MakerWorld platform bug. Next route on file is Scott trying the save in his own session, or parking customizers until MakerWorld fixes PMM.
3. **"Candy Tower" G0 ❌ vs Candy Lighthouse's public launch.** The registry blocks "Candy Tower's" Multicolor profile pending identity confirmation (Lighthouse vs Wrap-Around Tower). Separately, standing memory records **Candy Lighthouse LIVE and complete on @P3DT on 2026-11-13 (model 3605973) with all 4 profiles public, including Multicolour Standard and Multicolour Optimized**. The files do not state whether that launch *was* Scott resolving the identity question (making the registry row moot) or a separate track. **Unclear — Benson should confirm with Scott / close the registry row explicitly** rather than let a G0 ❌ sit against a launched design.
4. **Public section heading vs Sweet Shop row.** Registry → Public designs is headed *"Public designs (16) — G6 complete"* and in the same section flags Sweet Shop's corrected file as outstanding with *"Treat as G1 ⏳."* Both cannot be literally true; the row is the honest statement, the heading is the loose one. Any count of "designs at G6" quoted from this file should be 15 clean + 1 caveated.
5. **Gingerbread canister: two different "lid" stories in the record.** The Nov 2 memory records canister screw-lid profiles built/verified and a swap "underway"; the Nov 4 request-list entry and the registry both record the rework as G1-failed with the *"profile swap parked."* These reconcile only if the Nov 2 swap was of the earlier version and the Nov 4 rework is a subsequent version that never swapped — the files do not state this explicitly. **Unclear which lid version is currently live on 3518210's canister profiles**; Benson should verify from the live model before Brief B is filed, so Claude's fix targets the right baseline.
6. **Axolotl / Mochi Fox asymmetry is Scott's call, not an inconsistency.** Both failed G3 on silhouette; Mochi Fox was deleted at Scott's direction (Nov 9) while Axolotl awaits "redesign or Scott's written overrule" (registry). No file explains the different treatment — it reads as Scott's preference, recorded here so no one "corrects" it.
7. **Fold Stand version numbering in the registry vs reality.** Registry says v2; the live model now carries v4 profiles (and briefly carried v3 profiles on Nov 10 before they were deleted the same day). Anyone reading only the registry would brief Claude against a two-versions-old design. Folded into recommendation #1 above.
8. **Santa's Workshop v2 "G0/G1 ⏳" understates the age.** The registry row is accurate but carries no escalation flag despite the underlying briefs being the oldest in the entire request list (Oct 24) and marked "GATING" in their own text. The stall map above dates it explicitly for that reason.

---
*End of Lane 5. Briefs A–D are drafts staged in this file only — not filed on the Claude request list, not pushed to GitHub, not sent anywhere.*
