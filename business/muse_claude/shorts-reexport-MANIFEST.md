# YouTube Shorts — Etsy Overlay Re-export Manifest

**Date:** 2026-11-12 · **Stage:** inventory + re-export only. **Nothing was uploaded to YouTube, and nothing on the channel was changed or deleted.**
**Approved by Scott:** 2026-11-12 ("Re-export the Shorts without the Etsy overlay").

## What the "Etsy overlay" actually is (key finding)

It is **not** just an ending card. In the village render queue it is a **persistent bottom banner —
"Print files on Etsy - OnBrandCraftz" — burned into every frame** of the video (white bold text on the
navy band at the foot of the frame). It is baked into the queue originals themselves, so every Short built
from that queue carries it, including the post–Nov 9 ones whose *descriptions* were already swapped to
MakerWorld. Other videos carry Etsy text only on an end card, and the two real-timelapse cuts carry it in
two places (timelapse-segment bar + closing card). Each video below was classified by looking at its
actual frames (start / middle / end + segment boundaries), never from filenames.

## Treatment applied

The faithful swap, mirroring the wording the pipeline already uses in descriptions since Nov 9:
the Etsy line is repainted in its own band/card colours and re-rendered in the same position, weight
and style with **"MakerWorld"** in place of **"Etsy"** (queue banner: "Print files on MakerWorld -
OnBrandCraftz"). Nothing else was changed anywhere: same footage, same audio (audio streams copied
bit-identical), same captions/other text, durations identical to the source (0.00 s difference on all 35).
Scott's standing exception holds: **A/B Test 7 and Test 8 Shorts keep their original Etsy endings** —
they are listed as EXEMPT and were not touched.

## Headline counts

| Count | Number |
|---|---|
| Published Shorts checked (48 in `social/published.json` + Shorts #25/#26 from the draft log) | **50** |
| …with a burned-in Etsy CTA | **34** |
| …exempt (A/B Tests 7 & 8 sources — Scott's decision) | **2** |
| …checked, no Etsy overlay | **14** |
| …with Etsy overlay but no usable local source | **0** |
| Unique files re-exported for posted Shorts | **31** (they cover all 34 uploads — see notes) |
| Unposted drafts also pre-fixed (same defect, scheduled to post) | **4** |
| **Total re-exported files in this folder** | **35** |

Claude's growth-meeting estimate of "~30" was close: the true figure is **34 of 50 published Shorts**.

Notes on coverage: one re-exported file can serve two channel uploads — the Gingerbread Cottage colour
file covers both the Oct 17 upload and Scott's Oct 18 "dark" repost (same for Candy Cane Chapel white),
and the Sweet Shop cut file covers both its original Short and the A/B Test 3 re-run.

## Table A — Re-exported: posted Shorts (34 uploads / 31 files)

"Overlay confirmed" = the actual file's frames were viewed (bottom-strip contact sheets for the queue
files; end-card + segment frames for the rest). QC for every output: full decode clean, duration
identical to source, new ending frames viewed (evidence in `.qc/`).

| # | Short (subject) | YouTube | Posted | Overlay confirmed | Source file | Output (in this folder) | QC |
|---|---|---|---|---|---|---|---|
| 1 | Church — white (queue #1) | [gw0BjZq1ws0](https://www.youtube.com/shorts/gw0BjZq1ws0) | 2026-10-17 | Frame-viewed, persistent banner | `videos/tiktok/tiktok_empty_church.mp4` | `short-01-church-white/` | PASS |
| 2 | Gingerbread Cottage — colour (#2) | [heVd8jTiOXg](https://www.youtube.com/shorts/heVd8jTiOXg) | 2026-10-17 | Frame-viewed, persistent banner | `videos/tiktok/tiktok_color_cottage_gingerbread.mp4` | `short-02-gingerbread-cottage-colour/` | PASS |
| 3 | Gingerbread Cottage — colour, Oct 18 repost of #2 | [YoFjGmzl-ZI](https://www.youtube.com/shorts/YoFjGmzl-ZI) | 2026-10-18 | Same source file as #2 | same as #2 | `short-02-gingerbread-cottage-colour/` (same file) | PASS |
| 4 | Candy Cane Chapel — white (#3) | [wuK1OXnQrO8](https://www.youtube.com/shorts/wuK1OXnQrO8) | 2026-10-17 | Frame-viewed, persistent banner | `videos/tiktok/tiktok_empty_candy_cane_chapel.mp4` | `short-03-candy-cane-chapel-white/` | PASS |
| 5 | Candy Cane Chapel — white, Oct 18 repost of #3 | [sLPt3Dx1-T0](https://www.youtube.com/shorts/sLPt3Dx1-T0) | 2026-10-18 | Same source file as #4 | same as #4 | `short-03-candy-cane-chapel-white/` (same file) | PASS |
| 6 | Church — colour (#4) | [EHsvn2dWh8Y](https://www.youtube.com/shorts/EHsvn2dWh8Y) | 2026-10-18 | Frame-viewed, persistent banner | `shorts-drafts/youtube_short_draft_2026-10-18_church_color.mp4` | `short-04-church-colour/` | PASS |
| 7 | Coaching Inn — white (#5) | [qF3Wsinu7nA](https://www.youtube.com/shorts/qF3Wsinu7nA) | 2026-10-20 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-19_coaching_inn.mp4` | `short-05-coaching-inn-white/` | PASS |
| 8 | Santa's Workshop — gingerbread colour (#6) | [PwpbNNaPsXc](https://www.youtube.com/shorts/PwpbNNaPsXc) | 2026-10-20 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-20_santas_workshop.mp4` | `short-06-santas-workshop-colour/` | PASS |
| 9 | Cocoa Cafe — white (#7) | [3RJJfQjkf8E](https://www.youtube.com/shorts/3RJJfQjkf8E) | 2026-10-21 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-21_cocoa_cafe.mp4` | `short-07-cocoa-cafe-white/` | PASS |
| 10 | Coaching Inn — colour (#8) | [RxfOd_fyWtI](https://www.youtube.com/shorts/RxfOd_fyWtI) | 2026-10-22 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-22_coaching_inn_color.mp4` | `short-08-coaching-inn-colour/` | PASS |
| 11 | Cocoa Cafe — colour (#10) | [uDIlKlvt0pY](https://www.youtube.com/shorts/uDIlKlvt0pY) | 2026-10-27 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-24_cocoa_cafe_color.mp4` | `short-10-cocoa-cafe-colour/` | PASS |
| 12 | Gingerbread Cottage — white (#11) | [qeCsbubg8Qw](https://www.youtube.com/shorts/qeCsbubg8Qw) | 2026-10-28 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-25_cottage_gingerbread_white.mp4` | `short-11-gingerbread-cottage-white/` | PASS |
| 13 | Cookie Clock Tower — colour (#12) | [yE0Tzcg9aQM](https://www.youtube.com/shorts/yE0Tzcg9aQM) | 2026-10-28 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-26_cookie_clock_tower_color.mp4` | `short-12-cookie-clock-tower-colour/` | PASS |
| 14 | Clock Tower — white (#13) | [qFRbEKs2zk4](https://www.youtube.com/shorts/qFRbEKs2zk4) | 2026-10-27 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-27_clock_tower_white.mp4` | `short-13-clock-tower-white/` | PASS |
| 15 | Candy Cane Chapel — colour (#14) | [RthKJSFZU6Y](https://www.youtube.com/shorts/RthKJSFZU6Y) | 2026-10-29 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-28_candy_cane_chapel_color.mp4` | `short-14-candy-cane-chapel-colour/` | PASS |
| 16 | Victorian Cottage — white (#15) | [uZB_H7UUVGk](https://www.youtube.com/shorts/uZB_H7UUVGk) | 2026-11-03 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-29_cottage_victorian_white.mp4` | `short-15-victorian-cottage-white/` | PASS |
| 17 | Clock Tower — colour (#16) | [l3vAWqh7liw](https://www.youtube.com/shorts/l3vAWqh7liw) | 2026-11-03 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-30_clock_tower_color.mp4` | `short-16-clock-tower-colour/` | PASS |
| 18 | Santa's Workshop — gingerbread white (#17) | [hY4Uyun-7FE](https://www.youtube.com/shorts/hY4Uyun-7FE) | 2026-11-04 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-10-31_santas_workshop_gingerbread_white.mp4` | `short-17-santas-workshop-gingerbread-white/` | PASS |
| 19 | Victorian Cottage — colour (#18) | [STTivUKNg3g](https://www.youtube.com/shorts/STTivUKNg3g) | 2026-11-04 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-11-01_cottage_victorian_color.mp4` | `short-18-victorian-cottage-colour/` | PASS |
| 20 | Shop House — white (#21) | [jaFfgPV41ao](https://www.youtube.com/shorts/jaFfgPV41ao) | 2026-11-10 | Frame-viewed (original strip re-checked 2026-11-12), persistent banner | `shorts-drafts/…_2026-11-04_shop_house_white.mp4` | `short-21-shop-house-white/` | PASS |
| 21 | Shop House — colour (#22) | [yd80LWcOH64](https://www.youtube.com/shorts/yd80LWcOH64) | 2026-11-10 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-11-05_shop_house_color.mp4` | `short-22-shop-house-colour/` | PASS |
| 22 | Sweet Shop — white (#23) | [ptu6a07lT9o](https://www.youtube.com/shorts/ptu6a07lT9o) | 2026-11-11 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-11-06_sweet_shop_white.mp4` | `short-23-sweet-shop-white/` | PASS |
| 23 | Sweet Shop — colour (#24) | [yNerqBMUWLw](https://www.youtube.com/shorts/yNerqBMUWLw) | 2026-11-11 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-11-07_sweet_shop_color.mp4` | `short-24-sweet-shop-colour/` | PASS |
| 24 | Townhouse — white (#25) | [oUKzp8xg8Sw](https://www.youtube.com/shorts/oUKzp8xg8Sw) | 2026-11-12 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-11-08_townhouse_white.mp4` | `short-25-townhouse-white/` | PASS |
| 25 | Townhouse — colour (#26) | [98S25Cf4dSE](https://www.youtube.com/shorts/98S25Cf4dSE) | 2026-11-12 | Frame-viewed, persistent banner | `shorts-drafts/…_2026-11-09_townhouse_color.mp4` | `short-26-townhouse-colour/` | PASS |
| 26 | Christmas Village — long v3 (whole-village VO video) | [qtFNjrJFxis](https://www.youtube.com/shorts/qtFNjrJFxis) | 2026-10-18 | Body frames (t=3/40/80) + end card viewed — persistent footer AND Etsy end-card line | `your_files/christmas-village-video/christmas_village_long_v3.mp4` | `christmas-village-long-v3/` | PASS |
| 27 | Christmas Village Montage — "8 print files" | [grkXzlWWPIU](https://www.youtube.com/shorts/grkXzlWWPIU) | 2026-10-23 | End card viewed; body segments checked (title/counter template, no Etsy) | `social-dashboard/montage-videos/christmas-village-montage-v1.mp4` | `christmas-village-montage-v1/` | PASS |
| 28 | 15-Building Compilation | [LVXvwbKmDME](https://www.youtube.com/shorts/LVXvwbKmDME) | 2026-10-29 | End card viewed; body segments checked (no Etsy) | `social-dashboard/montage-videos/15-building-compilation-v1.mp4` | `compilation-15-buildings/` | PASS |
| 29 | Lantern Trio Montage | [kb-mo4HHW0s](https://www.youtube.com/shorts/kb-mo4HHW0s) | 2026-10-26 | End card viewed; body segments checked (no Etsy) | `social-dashboard/montage-videos/lantern-trio-montage-v1.mp4` | `lantern-trio-montage/` | PASS |
| 30 | Sweet Shop — real timelapse cut | [CyolRsPAcZQ](https://www.youtube.com/shorts/CyolRsPAcZQ) | 2026-10-26 | Segment frames viewed — banner in timelapse bar (2–11s) + closing card (14.2s→) | `social-dashboard/timelapse-cuts/sweet-shop-timelapse-cut-v1.mp4` | `sweet-shop-timelapse-cut/` | PASS |
| 31 | A/B Test 3 — "It prints in one piece — then the whole tower GLOWS 🍬" | [PVWY3ykp2Yc](https://www.youtube.com/shorts/PVWY3ykp2Yc) | 2026-10-26 | Same video file as #30 (title-only variant, per A/B log) | same as #30 | `sweet-shop-timelapse-cut/` (same file) | PASS |
| 32 | Gingerbread Cottage — real timelapse cut | [So0C15HqDZE](https://www.youtube.com/shorts/So0C15HqDZE) | 2026-10-26 | Segment frames viewed — same two Etsy elements as #30 | `social-dashboard/timelapse-cuts/gingerbread-cottage-timelapse-cut-v1.mp4` | `gingerbread-cottage-timelapse-cut/` | PASS |
| 33 | Santa's Workshop v4 (upgrade sample) | [e46BMv4ZBy8](https://www.youtube.com/shorts/e46BMv4ZBy8) | 2026-10-28 | End card viewed; pre-card frames checked (no Etsy) | `social-dashboard/upgrade-sample-santas-workshop-v3/sample-video-v4.mp4` | `santas-workshop-v4/` | PASS |
| 34 | Sketch to Reality — "Santa's Workshop — Sketch to Reality 🎄 Watch It Glow" | [rgIQ5saVCL0](https://www.youtube.com/shorts/rgIQ5saVCL0) | 2026-10-31 | Final card viewed — mixed card: "FREE NOW ON MAKERWORLD" (kept) + gold "PRINT FILE ON ETSY · ONBRANDCRAFTZ" (swapped) | `social-dashboard/sketch-to-reality-sample/sketch-to-reality-workshop-v2-freenow.mp4` | `sketch-to-reality-santas-workshop-v2/` | PASS |

Source paths abbreviated: `videos/tiktok/` = `~/workspace/goals/christmas-village-print-file-listings/files/christmas-village-3mf-listings/videos/tiktok/`;
`shorts-drafts/` = `~/workspace/goals/grow-onbrandcraftz-social-following/hidden_files/shorts-drafts/`;
`social-dashboard/` = `~/workspace/your_files/social-dashboard/`. Posted dates are the `published.json` record dates.

## Table B — Unposted drafts pre-fixed (4 files, not yet on the channel)

These drafts carry the same burned-in banner and were scheduled to post with it. Fixed versions are
supplied so the uploads use the MakerWorld banner. Frame-viewed on the originals 2026-11-12 (all four
confirmed carrying "Print files on Etsy - OnBrandCraftz").

| Draft | Planned slot (per draft log) | Source file | Output | QC |
|---|---|---|---|---|
| Cookie Clock Tower — white (queue #9; upload was blocked Oct 26, never posted) | — | `shorts-drafts/…_2026-10-23_cookie_clock_tower.mp4` | `short-09-cookie-clock-tower-white-unposted/` | PASS |
| Toy Shop — white (#27) | Tue Nov 17, 2:30 PM EST | `shorts-drafts/…_2026-11-10_toy_shop_white.mp4` | `short-27-toy-shop-white-unposted/` | PASS |
| Toy Shop — colour (#28) | Tue Nov 17, 8:30 PM EST | `shorts-drafts/…_2026-11-11_toy_shop_color.mp4` | `short-28-toy-shop-colour-unposted/` | PASS |
| Turret House — white (#29) | Wed Nov 18, 2:30 PM EST | `shorts-drafts/…_2026-11-12_turret_house_white.mp4` | `short-29-turret-house-white-unposted/` | PASS |

## Table C — EXEMPT (2) — not touched, per Scott's explicit decision

| Short | YouTube | Posted | Why exempt |
|---|---|---|---|
| Santa's Workshop — Victorian white (queue #19) | [Bc68l19QgtA](https://www.youtube.com/shorts/Bc68l19QgtA) | 2026-11-05 | Source of A/B Test 8 (music-only re-run, Tue Nov 17) — Tests 7/8 keep their original Etsy endings |
| Santa's Workshop — Victorian colour (queue #20) | [2QV4FzlatvA](https://www.youtube.com/shorts/2QV4FzlatvA) | 2026-11-05 | Source of A/B Test 7 (post-time re-run, Thu Nov 19) — same exception |

## Table D — Checked, NO Etsy overlay (14) — no action needed

| Short | YouTube | Posted | How settled |
|---|---|---|---|
| Gingerbread Tin Clicker | [OQDDNViY_gE](https://www.youtube.com/shorts/OQDDNViY_gE) | 2026-11-09 | Frames viewed (13.5s/14.8s): real-photo footage, no burned-in CTA at all |
| Haunted General Store — timelapse | [czMLZuUQ6j8](https://www.youtube.com/shorts/czMLZuUQ6j8) | 2026-10-26 | Source is the raw 5s P1S timelapse (`social/inbox/timelapses/`); end frames viewed — no overlay exists in the source. Caveat: settled from the source file, the only local candidate for the upload |
| Haunted Bakery — timelapse | [f2WdaBacKNI](https://www.youtube.com/shorts/f2WdaBacKNI) | 2026-10-26 | Same as above |
| Haunted Cemetery — timelapse | [EXecomlnojc](https://www.youtube.com/shorts/EXecomlnojc) | 2026-10-26 | Same as above |
| How-To Ep 1 — TPU on the P1S (Explained Lesson 002) | [sUkSbeAuP6E](https://www.youtube.com/shorts/sUkSbeAuP6E) | 2026-10-28 | End frame + mid-frame band viewed: series title card only, no Etsy |
| Explained Lesson 003 — one tea light lights a house | [Qu6CgW93_1o](https://www.youtube.com/shorts/Qu6CgW93_1o) | 2026-10-31 | End frames of BOTH candidate files (sample v2 + final v2) + mid-frame viewed: series card only, no Etsy |
| Print Cam Ep 001 — Santa's Workshop | [knDZr6IrwvI](https://www.youtube.com/shorts/knDZr6IrwvI) | 2026-10-30 | End card viewed: already reads "FREE ON MAKERWORLD" |
| Hot Plate Ep 001 — glue stick | [mFhzBMHT5KA](https://www.youtube.com/shorts/mFhzBMHT5KA) | 2026-10-31 | End card viewed: "THE COMMENTS DECIDE" scoreboard, no Etsy |
| A/B Test 5 — "Do you use glue stick on your build plate? 🔴 or 🔵" | [Gl_dH6TLKsw](https://www.youtube.com/shorts/Gl_dH6TLKsw) | 2026-11-02 | Title-only re-run of Hot Plate Ep 001 — same file as above |
| Versus — filament dryer duel | [sdoSupXm84w](https://www.youtube.com/shorts/sdoSupXm84w) | 2026-10-19 | End frame + mid-frame footer viewed: verdict card / "Prices checked" footer, no Etsy |
| Versus — hotend duel | [zYBFMitNKcg](https://www.youtube.com/shorts/zYBFMitNKcg) | 2026-10-19 | Same template check as above |
| Versus — "Which 3D printer should you buy in 2026?" | [i2IRHZaGR-I](https://www.youtube.com/shorts/i2IRHZaGR-I) | 2026-10-19 | Same template check as above |
| Versus — multicolour duel (AMS vs CFS vs CANVAS) | [hi5-ZGV4G6Y](https://www.youtube.com/shorts/hi5-ZGV4G6Y) | 2026-10-19 | Same template check as above |
| Versus — P1S vs K2 Plus duel | [jLU0Ywbe2OA](https://www.youtube.com/shorts/jLU0Ywbe2OA) | 2026-10-19 | Same template check as above |

## Caveats / unsettled points

1. **Haunted trio (Table D):** no finished "cut" file exists locally; the uploads were almost certainly
   the raw inbox timelapses (possibly with music muxed, which doesn't change the video stream). The
   no-overlay verdict rests on those source files. If a differently-built upload file exists outside the
   workspace records, it isn't in any log I can find.
2. **Oct 18 reposts (Table A #3/#5):** Scott uploaded those from his side; the fixed files derive from
   the folder originals of the same renders. If his uploads came from a phone-side variant file, the
   content is the same render with the same banner, and these fixed files supersede either way.
3. **Banner typeface:** the replacement line is set in Liberation Sans Bold (the original's exact font
   couldn't be identified — the local Montserrat file is a variable font that renders light); weight,
   size class, position and band colour match the original, verified side-by-side.
4. **One near-miss caught in QC:** the long-v3 video's Etsy footer runs through the whole body, not
   just its end card — the first re-export only fixed the card; it was re-done with both fixes before
   delivery (see its NOTE.md). The montages were re-checked segment-by-segment for the same issue and
   are clean.
5. **Incident:** a runtime restart corrupted the first Gingerbread Cottage cut encode (missing moov
   atom); it was re-rendered and the delivered file passes full decode.
6. Dates in Table A are the `published.json` record dates; a few scheduled Shorts went public a day or
   two later than the record date per the draft log. YouTube IDs/URLs are exact.

## QC summary

- All **35/35** outputs: full-decode clean; duration **identical** to source (0.00 s); audio stream-copied.
- Visual verification viewed for every output: queue banner strips (`.qc/qsheet1–3.jpg`), end cards
  (`.qc/cardsheet.jpg`), cut segments (`.qc/cutsheet.jpg`), gate boundaries (`.qc/gatesheet.jpg`),
  long-v3 before/after (`.qc/lv_new_sheet.jpg`), plus originals re-check (`.qc/osheet.jpg`).
- Machine-readable QC results: `.qc/qc_results.json`.
