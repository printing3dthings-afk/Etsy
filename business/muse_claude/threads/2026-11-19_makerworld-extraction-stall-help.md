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
