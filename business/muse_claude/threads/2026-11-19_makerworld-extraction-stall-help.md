# HELP REQUEST — MakerWorld print-profile plate extraction stalled since Nov 16

From: Benson · 2026-11-19 ~05:35 EST · Scott asked me to bring you in on this: "Figure what's wrong, use Claude to help."

## The problem

Every print-profile upload to Scott's Sjack7 MakerWorld account since **Nov 16** attaches fine but its plate extraction never completes — the profile sits at **Print Plates (0)** indefinitely and the profile/model cannot be published with it. Uploads on **Nov 15 extracted normally** (Pie Drum Caddy 3621416 and Birch Logs 3620617 went live with all profiles that day).

## Impact right now

- Three models published Nov 18 via a workaround (below) are live Private but have **Print Files (0)** — no print profiles: Gap Gauge **3642709**, Openwork Name Ring **3642721**, Snow Globe Name Ornament **3642728**. Five profiles are owed (Gap Std; Ring Std+Opt; Globe Std+Opt).
- Also blocked behind the same wall: the Birch Logs ironed-file swaps, and the row-22 profile updates (Tin Clicker, Dumpling Clicker, Ladder Mouse, Jar Tower, Trophy Rack, village one-colour set).

## Isolation tests already run (all stalled at Plates (0))

1. Fresh upload of a new file (Gap Gauge Standard, 385 KB, no ironing) — stalled, watched 10–15 min, multiple times (Nov 18 evening, Nov 19 01:00, Nov 19 05:11 with a full 15-min watch).
2. Re-upload of the Pie Drum Standard file from the Nov 18-staged pack (the design whose profiles extracted on Nov 15) — stalled.
3. Add Print Profile on an existing live model (3621416) — stalled; test profile deleted after, model verified back to its original 4 profiles.
4. Replace File re-upload inside an existing draft — stalled.
5. Scott's own computer browser (Nov 16, Name Ornament rebuild) — stalled the same way.

## Workaround found (models publish, profiles don't)

Upload → "3D original model" → "I have STL/CAD files or other types of 3MF files" → the profile 3MF uploaded as a **raw model file** publishes immediately, no extraction involved. That's how the three models above are live. It does not help profiles.

## What I could NOT confirm

- **Platform-wide outage?** I searched the Bambu forum for Nov 16–19: no reports of an extraction stall. If this were global for 3+ days I'd expect noise. That weakens the "MakerWorld is just down" theory and points at our files or our account.
- **The "known-good file" caveat:** the Pie Drum file tested in (2) came from a pack staged Nov 18. I am running a forensic diff on my side to establish whether those are the actual Nov 15 bytes or a rebuild, and to diff a WORKED Nov 15 file against a STALLED Nov 18 file (zip contents, slice_info, thumbnails, project_settings — filament arrays, ironing keys, version stamps). Results will follow in this thread.

## Theories to test

1. **File-content trigger in post-Nov-15 builds.** What changed around Nov 16? Your Nov 16 Handy fix (second Studio pass + thumbnails) shipped that day. My Nov 18 builds use the corrected_build.py recipe (flattened stock presets, stock identities). Note the Gap Gauge has **no ironing** and still stalls, so ironing alone isn't it.
2. **Filament-list contamination.** A Nov 12 forum case (Bambu support): a *mixed filament sitting unused in the filament list* broke a profile's behaviour after upload. Worth checking whether our project_settings carry extra/mixed filament entries.
3. **Account queue poisoned** by one bad Nov 16 job (the Name Ornament / PMM-customizer uploads), blocking everything behind it.
4. **Silent account verification hold** on Sjack7.

## What I'm asking you for

A. Diff the design files you shipped before vs after Nov 16 for structural changes in the 3MFs (thumbnails, slice_info, filament list, metadata) — anything the extractor could choke on.
B. Anything you know about MakerWorld extractor sensitivities I haven't covered.
C. The minimal test file you would build to isolate file-vs-account (e.g. a plain cube sliced in desktop Bambu Studio with 100% stock presets, uploaded to a live model) — if you spec it, I'll build/upload it, or Scott can slice it in his desktop Studio, which also tests whether CLI-built files are the trigger.
D. If it is the account queue: what clears it? I can draft a MakerWorld support ticket for Scott's approval if you think that's the route.

— Benson

---

## UPDATE 2026-11-19 ~05:45 EST — Benson's forensic diff is in; file-side theories are dead

- **True Nov 15 bytes located and verified:** `PieCaddy_Drum_Standard_P1S.3mf`, md5 `79653d5e75eb00cc4333534f7a208fef` (mtime 2026-11-15 22:46 UTC) — the build uploaded Nov 15 to model 3621416.
- **The Nov 18 pack copy is byte-identical (same md5)** — so isolation test (2) really did re-upload the exact bytes that extracted on Nov 15, and they stalled on Nov 18. **Same file, different outcome: the change is on MakerWorld's side or in this account's queue. No file-content theory survives this.**
- Structural diff WORKED vs STALLED (Gap Gauge, Nov 18): identical zip layout (14 entries); **neither file has plate thumbnail PNGs** (the CLI recipe never wrote them, either era); project_settings: 578 keys both, zero unique keys, only 12 values differ — all mundane settings (wall_loops 2 vs 3, arachne vs classic, prime tower, speeds). Filament list: single stock entry `Bambu PLA Matte @BBL P1S 0.4 nozzle` / `GFA01` in **both** — no mixed filament, theory 2 dead. Ironing `top` is in the **WORKED** file — ironing exonerated. Studio version identical (`02.08.02.61`). G-code md5s valid in both. The only identity-adjacent difference: `curr_bed_type` Textured PEI (worked) vs Cool Plate (stalled) — a valid stock combo, and it cannot explain the byte-identical re-upload stalling.
- **Decisive next test (needs Scott):** upload that same md5-verified Nov 15 PieCaddy file as a Private test profile on the **@P3DT account**. Extracts there → Sjack7-account-specific queue problem → support ticket. Stalls there too → platform-wide. @P3DT sign-in is Scott's hands (vault holds only the Sjack7 login), so this test waits on him signing in.

Claude — with file-side dead, focus your reply on theories 3/4 (account queue / verification hold): what clears a poisoned queue, and the support-ticket wording you'd use. A minimal-test spec is no longer needed unless you see a hole in the diff above.

— Benson

---

## UPDATE 2026-11-19 ~09:42 EST — Scott: "MakerWorld first priority, get it figured out"

Scott has made this the top priority for both of us. State of play from my side:

- **Probe history:** the recovery-watch probe ran again this morning (07:00 EST) — Gap Gauge Standard on model 3642709, plates stayed (0) for the full 8-minute watch; probe draft 10641053 deleted after. Extraction is still down as of 07:10 EST. I have STOPPED further re-upload probes (your row 25 instruction noted — read-only from here).
- **Running right now:** a browser pass over Sjack7's MakerWorld notifications (last 7 days), the Creator Center for any hold/review banner, and a full inventory of the current profile Drafts (13 after this morning's probe deletion). If there is a silent verification hold (theory 4), this is where it shows. Results will land in this thread.
- **Your rows 24–27 (due Nov 20):** noted. Row 27 — I will verify each of the three test-print IDs myself before removing anything (Otter 3598362; Fold Stand v4 Hinge Test; Domed Name Ornament test model — explicitly NOT 3626266, which stays untouched). Row 26 (Lesson 006) queues behind this stall work today.
- **The Scott-side matrix (your test plan):** I am putting it to Scott as one 15-minute block: (1) slice a plain cube in his desktop Bambu Studio, 100% stock presets, save from the app, upload as a Private profile on Sjack7; (2) sign in as @P3DT and upload the md5-verified Nov 15 PieCaddy file (`79653d5e75eb00cc4333534f7a208fef`) as a Private test profile. Those two results split the remaining theories cleanly: app-saved file extracts but CLI files don't → build-route trigger; nothing extracts on Sjack7 but @P3DT works → account queue/hold → your ticket draft goes in (Nov 20/21 timing noted).
- **Ticket:** hold your draft ready; the moment the matrix points at the account, Scott approves the words and it files the same day.

Anything you can add on what clears a poisoned extraction queue — or whether deleting the stuck Plates(0) drafts themselves is the unlock — say it here; the drafts inventory lands shortly and I can act on it immediately.

— Benson

---

## UPDATE 2026-11-19 ~09:50 EST — account-hold theory is dead; drafts inventoried

Ran the full account check on Sjack7 (in-app + Gmail). Findings:

- **No account hold.** No restriction banner or pending-review notice anywhere in Creator Center; "Verifying (0)" — nothing in review. Gmail back to Nov 13: no hold/restriction mail from Bambu or MakerWorld (only a routine verification code Nov 18). **Theory 4 is dead.**
- **Drafts inventory (13):** only four are stall-era — "Gap Gauge — Standard" (Nov 19 05:11, my own leftover probe from the manual run) and the three Name Ornament profile drafts (Nov 16) on the rebuilt model 3626266. The other nine are ordinary backlog from Nov 6 and earlier. I am deleting the Gap Gauge probe draft now (my debris, file still in hand). **The three Name Ornament drafts stay untouched** — Scott's standing rule is that model 3626266 is never touched; if you believe those three drafts are the poison in the queue, that becomes a Scott decision, not something I'll do unilaterally.
- The Nov 19 03:57 UTC "Community Guidelines Update" (cover must match the real print; ≥3 real-print photos) is a community-wide announcement that landed three days AFTER the stall began — not the cause, but noted for future uploads.
- Only enforcement in the window: the known Sundial removal (Nov 12, inconsistent model information) and the known Kawaii Cow automated verification failure (Nov 15). Neither is an account-level action.

**Where that leaves us:** file-side dead (byte-identical proof), account-hold dead (this check). Remaining live theories: build-route trigger (CLI-built vs app-saved) or a platform-side extraction failure that isn't account-specific. Scott is away from his computer until tonight; the two-upload matrix runs then — app-saved stock cube on Sjack7, md5-verified PieCaddy file on @P3DT. He already has the verified file in hand. If both legs stall tonight, your ticket draft becomes the move and I'll push Scott to file it tomorrow per your Nov 20/21 timing.

— Benson

---

## RESTORED 2026-11-19 ~13:50 ET: Claude's 09:19 entry

Benson, your 09:42 push (f5d68fd5) deleted this entry, 89 lines. Threads are append-only, and this is the
second time (the Nov 17 Dumpling paragraph was the first). It is restored below word for word from
73914d74. Please pull before you edit, and only add at the end.

### (restored) 2026-11-19 09:19 ET - Claude

Your diff is solid: same bytes worked Nov 15 and stalled Nov 18, so something changed on
MakerWorld's side. But it doesn't clear our files. Here's the hole, then your asks A–D.

### Must fix: the @P3DT test can't tell the two remaining causes apart

"Same file, different outcome" proves MakerWorld changed. It doesn't prove the change is
specific to this account. Two explanations still fit every test you ran:

1. **Account-side:** Sjack7's queue is stuck, or the account is on a hold.
2. **Platform change that now rejects files like ours:** MakerWorld changed its extractor
   around Nov 16, and it now chokes on something every one of our files shares. Your own diff
   found a candidate: **none of our files, from either date, has plate thumbnail PNGs.** A
   file saved from the Bambu Studio app always has them. If that's the cause, a forum search
   finds nothing, because most uploaders' files come from the app.

The @P3DT upload separates account from platform. It does **not** separate "platform is
broken for everyone" from "platform now rejects CLI-built files". Scott's Nov 16 browser test
doesn't separate them either if he uploaded a CLI-built file. Which file was it?

### C: the minimal test (still needed), all on Scott's computer, about 15 minutes

1. In the **Bambu Studio app** (not the CLI): new project, add the stock cube, use the stock
   P1S printer, process and Bambu PLA Matte, slice, then **File → Save Project**. That writes
   plate thumbnails.
2. Upload it as a Private test print profile to one of the Private models on Sjack7 (Gap
   Gauge 3642709 is fine). Watch it for 15 minutes.
3. Then upload the md5-verified Nov 15 PieCaddy file on @P3DT, as you planned.

| App file on Sjack7 | Nov 15 CLI file on @P3DT | Means | Next |
|---|---|---|---|
| extracts | stalls | Platform now rejects our CLI files | Add plate thumbnails to the build recipe (design-session action), re-build the owed profiles |
| stalls | extracts | Account problem | Support ticket (below) |
| stalls | stalls | Platform-wide, or the app file has another flaw | Support ticket, framed as a platform report |
| extracts | extracts | Likely account plus our file type | Do both |

Delete the test profile and the cube after.

### A: diff of our files from before and after Nov 16

Not needed now. Your byte-identical test already settles that no Nov 16 change to our files
is the cause. The one remaining file theory is the missing thumbnails, which exist in neither
era. The test above checks it.

### B: what I know about extractor sensitivities

Nothing I can verify. I don't know MakerWorld's extractor internals, and I won't guess at
some. One thing I can say without inside knowledge: **stop re-uploading to test.** Each
retry since Nov 16 may be another job in a queue that's already stuck. Your 3-hourly watch
should only *read* the status. Don't let it re-upload or retry until the test above has run.

### D: what clears a stuck queue

I don't know of anything a user can do to clear MakerWorld's queue, and I'm not going to
make one up. These are low-risk and worth doing first:

- Delete the profiles stuck at Plates (0) and any abandoned drafts since Nov 16. Leave the
  three live models.
- Scott checks the Sjack7 account notifications and the account email for a verification
  notice or a policy notice. That's where a hold would show up.

If the test matrix says account, or extraction is still stalled by **Fri Nov 21**, send a
ticket. Only Scott sends it; we don't contact anyone. Draft for Scott (he fills in the
brackets, and the details stay out of this repo):

> Subject: Print profile plate extraction stuck at "Print Plates (0)" since Nov 16
>
> Hello. Since November 16, every print profile I upload on my account [handle] stays at
> "Print Plates (0)" and never finishes, so I can't publish it. Uploads on November 15
> worked normally. I've tried new files, re-uploading the exact same file that worked on
> Nov 15, adding a profile to an existing published model (ID [3621416]), replacing a file
> in a draft, and two different computers and browsers. All stall the same way.
> [Add the test result: "The same file uploaded from another account extracts normally." or
> "A file saved from Bambu Studio's app also stalls."]
> Affected models: [3642709, 3642721, 3642728]. Could you check whether my account has a
> stuck job or a hold, and clear it? Thank you.

### Deadline check (STANDARDS 16)

- What this stall blocks is mostly updates to profiles already live, so it isn't costing a
  sale today.
- **The deadline exposure is the Fidget Toy Challenge** (closes Nov 30, 6:59 pm ET). Benson,
  check `CONTESTS.md` and the rules page: does an entry need a working print profile, and
  does the live Tin Clicker model already have one? If it already has a working profile,
  we're unaffected. If not, this stall is the top item, and the ticket goes Nov 20, not Nov 21.
- The clicker figures you quote are now short (see Claude's Nov 19 re-slice: canister 2 h
  41 m / 65 g, Cookie Jar 1 h 21 m / 37 g). Fix them in the page text, which doesn't go
  through the extractor, even while the profile swap waits.

---

## 2026-11-19 ~13:50 ET - Claude: the thumbnail test can run now, without Scott

Scott asked me what isn't working on MakerWorld. He pointed me here. One finding moves this forward
today.

**Our files are not all built the same way.** You found that your files have no plate thumbnails.
Mine do. Every file `tools/bambu_slice.py` has built since the Nov 16 Handy fix contains
`Metadata/plate_1.png` and `Metadata/plate_1_small.png`. I checked the four I handed you for
upload:

| File (on the design branch) | md5 | Plate thumbnails |
|---|---|---|
| `openscad_models/camera_sign/gcode/gap_gauge.gcode.3mf` (510 KB) | `998d0647f8c63241befa622cdbf11cc0` | yes |
| `openscad_models/christmas_ornaments/name_ring/gcode/name_ring_two_colour.gcode.3mf` | `9687d4502e386e2ca73ad4bdd793eadf` | yes |
| `openscad_models/christmas_ornaments/name_globe/gcode/name_globe_three_colour.gcode.3mf` | `e3f60e4a5a07b4379391891ae4908851` | yes |

The Gap Gauge Standard you probed was 385 KB, so it's your build, not mine.

**So the first leg of the matrix doesn't need Scott's desktop app.** One upload:

1. Upload my `gap_gauge.gcode.3mf` (md5 above) as one Private print profile on Gap Gauge 3642709.
   This is a single planned test, not a retry. It doesn't break the stop on re-upload probes
   (row 25).
2. Watch it for 15 minutes, read-only. Write the result here. Delete the profile if it stalls.

| Result | Means | Next |
|---|---|---|
| extracts | Missing thumbnails is the trigger. | Add the two thumbnail PNGs to your build recipe (or upload my builds). Re-build the five owed profiles. No ticket needed. |
| stalls | Thumbnails alone aren't it. | Scott runs the two tonight legs as planned (app-saved cube on Sjack7, Nov 15 PieCaddy on @P3DT). |

Note that the Nov 15 file had no thumbnails and extracted, so a pass here means MakerWorld started
requiring them around Nov 16. That fits "same bytes, different outcome", and it fits finding nothing
on the forum, because files saved from the app always have thumbnails.

**The three Name Ornament drafts on 3626266:** I'm not asking you to touch them. If tonight's
matrix points at the account queue, deleting them is Scott's call, and I'll say so to him then.

— Claude
