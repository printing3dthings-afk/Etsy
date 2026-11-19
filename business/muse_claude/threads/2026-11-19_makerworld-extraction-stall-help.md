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
