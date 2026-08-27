# Handoff — 3D-print design queue (OpenSCAD)

## Status

OnBrandCraftz's Etsy shop is in good shape overall (OpenWhen is live,
148 active listings). The one open thread is a run of new OpenSCAD
physical-product designs. Of "the current four," two are done, one is
being actively finished on a phone-based session concurrently with this
handoff being written, and one (the sundial) has an unfinished, unsaved
v1 that a fresh session should either continue or discard depending on
what the phone session lands.

**Concurrency warning, read this first:** this Etsy automation project is
being run from multiple simultaneous Claude Code sessions against the
*same* git branch and Frank storage volume (at minimum: a CLI/container
session and a phone-app session, both showing as session
`session_016e5iMGm6mJ4K9b59aPaAvV` on `claude/etsy-automation-agents-WFAPU`).
**Before starting any 3D-print work, run `git fetch origin
claude/etsy-automation-agents-WFAPU && git log origin/claude/etsy-automation-agents-WFAPU
--oneline -20` and check whether the thing you're about to build has
already landed or is already in flight elsewhere.** A collision already
happened once this session (this session and the phone session both
independently started building the sundial at the same time) — caught
only because a screenshot showed the phone session's live progress.

## Key decisions and why

- **Never work from a stale local git checkout.** Earlier this session
  the local checkout was ~30 commits behind `origin/claude/etsy-automation-agents-WFAPU`
  (a different container instance of this same session had pushed real
  work — ghost rebuild, axolotl, honeycomb pen holder — that this
  checkout never pulled). This caused real confusion: work looked "lost"
  when it was actually just unpulled. Always `git fetch` + compare
  `HEAD` vs `origin/<branch>` before assuming anything is missing.
- **OpenWhen was never actually lost** — it looked lost because the
  wrong field name was checked in `/api/products` (`id` vs `product_id`)
  and the real record lives in `product_catalog_overrides.json` on
  Frank's volume (`GET /api/files/download?root=volume&path=product_catalog_overrides.json`),
  not in the git-tracked `data/product_catalog.json`. It's live on Etsy:
  listing `4560574821`, state `active`, $4.99, 10 photos, real digital
  file attached — verified directly against the live Etsy listing, not
  just Frank's cache.
- **Every physical design gets committed + pushed + uploaded to Frank's
  volume immediately after it's verified working** — not batched at the
  end of a session. Scott has explicitly asked for this because
  uncommitted work in a container's `/tmp` is genuinely unrecoverable if
  that container cycles (this is exactly how the "cable clip" and
  "fidget-card design" work from an earlier phone-session thread was
  lost — never committed or saved before that container ended).
- **Sundial solar-position math (this session's own derivation, verified
  numerically against known sun positions):**
  ```
  function solar_altitude(lat, hour) = asin(cos(lat) * cos(15 * (hour - 12)));
  function solar_azimuth(lat, hour) =
      let(H = 15 * (hour - 12), sin_az = -sin(H), cos_az = -sin(lat) * cos(H))
      atan2(sin_az, cos_az);
  ```
  Verified in Python against latitude 35: noon → alt 55°/az 180° (south),
  6am → alt 0°/az 90° (east), 6pm → alt 0°/az 270° (west) — all correct.
  This is almost certainly the same fix the earlier "sundial azimuth
  180-degree bug" commit (`92b0902`) already made, but that commit only
  touched the skill doc's prose, not a saved `.scad` file, so there was
  nothing to diff against to confirm it's identical. If the phone
  session's sundial math disagrees with this, treat this derivation as
  the one to trust — it's numerically verified against known sun
  positions, not just eyeballed.

## Update (continue-f22my6 session, 2026-08-27, later same day)

**No Frank/Etsy/Railway credentials were available in this session's
container** (no `.env`, nothing in `env`, no Railway token) — the
"Direct Infrastructure Access" section of root `CLAUDE.md` assumes those
are reachable; they weren't here. Couldn't check the phone session's live
state or pull `sundial_WIP.scad` off the volume as a result. Asked Scott
directly (AskUserQuestion) rather than guess:
- **Cable clip → "Rebuild it myself."** Done, see below.
- **Sundial → "Wait for the WIP file."** Not touched this session — the
  next session should get Frank credentials (or the actual WIP file
  content) before picking this up, per Scott's own answer.
- **Fidget-card → "I'll send screenshots."** Not sent yet as of this
  session ending. Next session: check for a screenshot/description in
  the conversation before doing anything else on this thread.

**Cable clip: built, verified, DONE.** `openscad_models/cable_clip.scad`
(committed to git this session). A functional print-in-place design:
flat base with a semicircular cable channel + 2 screw-mount ears with
countersunk M3 holes, a hinged lid (Technique 22 barrel hinge, 5
knuckles) that swings open to load/unload the cable, and a friction
peg/socket latch to hold it shut. OnBrandCraftz maker's mark engraved on
the underside per the standing rule.

Getting the hinge geometrically correct (base and lid genuinely
disconnected — no interpenetration — while still print-in-place
interlocked) took real, multi-round debugging, now written up as
**Technique 24** in `.claude/skills/3d-print-design/SKILL.md`: a shared
one-size clearance channel left both the collar and sleeve floating
(needed per-slot-parity clearance instead); a `translate()` on the wrong
side of a `rotate()` shifted a bore 0.5mm off-axis instead of realigning
it along its own length; and — the most important methodological
finding — an exact-vertex-sharing connected-component check (this skill's
established Technique 20 method) is NOT sufficient to prove two parts
don't interpenetrate: base and lid each rendered as one clean component
and shared zero vertices with each other, yet still fused into one solid
on `union()`, because CGAL generates new intersection vertices that exist
in neither part's standalone mesh. Only a real ray-casting point-in-mesh
test caught it. Final verification: `openscad --render` reports
`Simple: yes`; the combined model splits into exactly 2 connected
components (base X[0,46] Z[0,8.75], lid X[10.3,35.7] Z[2.75,11.5],
matching the two physical parts); a full point-in-mesh sweep found zero
vertices of either part inside the other; 4 rendered PNG views (front,
back showing the 5-knuckle hinge, top-down) all look correct.

**Deviation from the usual "commit code, upload .scad/.stl to Frank's
volume" rule, because of the credentials gap above:** the `.scad` is
committed to git at `openscad_models/cable_clip.scad` as the durable
fallback. It was NOT uploaded to Frank's volume (`POST /api/files/upload`)
because this session had no `APP_SECRET_TOKEN`/`FRANK_API_BASE` to call
that endpoint with. **A future session with real Frank credentials should
upload `openscad_models/cable_clip.scad` (and can regenerate the STL from
it, `python3 tools/openscad_render.py openscad_models/cable_clip.scad -o
cable_clip.stl`) to the volume to bring this back in line with the
standing convention** — nothing about the design itself needs revisiting,
just the storage step this session couldn't complete.

## Open threads (original, from earlier in the day — see update above for current status)

- **Cable clip** — being actively finished on the phone session as of
  2026-08-27 ~18:28 local (base/hinge/lid/latch assembled, a comprehensive
  verification agent was mid-run). Check `git log` for whether it's
  landed; if not, it may still be in progress or may have been lost the
  same way the first attempt was — ask Scott before rebuilding blind.
  **[RESOLVED — see update above: rebuilt independently, done.]**
- **Sundial** — this session built and partially verified a v1
  (7-hour dot-matrix digital sundial, digit-matrix logic visually
  confirmed correct for "12", a full numeric verification agent was
  launched but abandoned mid-run once the phone-session collision was
  discovered). WIP source saved to Frank's volume at
  `openscad_models/sundial_WIP.scad` — NOT committed to git, NOT
  necessarily the final version. Check whether the phone session already
  finished its own sundial before touching this.
- **Fidget-card design** — mentioned by Scott in a conversation this
  session has no transcript of (only referenced secondhand via a
  screenshot: "the fidget-card design is a strong pick and I'll queue it
  once the current four wrap up"). No written spec exists anywhere found
  so far (not in git, not on Frank's volume, not in the skill doc's
  "Reference ideas from Scott" section, which only records two ideas: a
  folding fan with a print-in-place hinge, and a ribbed desk organizer
  caddy). **Ask Scott directly what the fidget-card design actually is**
  before attempting to build it — there is nothing to reconstruct it from.

## Gotchas discovered this session

- `/api/products` uses field names `id`/`listing_id`, not
  `product_id`/`etsy_listing_id` — a script filtering on the wrong name
  will silently return zero matches for a product that actually exists
  and is live. Cross-check against `product_catalog_overrides.json`
  directly (via `/api/files/download?root=volume&path=product_catalog_overrides.json`)
  if `/api/products` seems to be missing something.
- The Etsy API's rate limit (daily quota + circuit breaker) can make
  `/api/actions` and `/api/metrics` report transient errors that look
  like real problems but clear on their own within the day — check
  `/api/ping` and retry rather than concluding something is broken.
- A container's `/tmp` is genuinely ephemeral — anything valuable built
  there needs `git commit` + `git push` (for code/skill docs) and an
  upload to Frank's volume (for `.scad`/`.stl` files, via
  `POST /api/files/upload?path=<rel>`, verified by re-downloading and
  comparing MD5) before considering it safe. Do this after every
  individually-verified unit of work, not at the end of a session.
- This session's local git checkout can silently fall behind `origin`
  because other concurrent sessions (phone, other containers) push
  independently. `git fetch` + compare HEAD vs origin should be a
  standard first step of any 3D-print (or any git-touching) task in this
  project, not just something to do when something seems missing.

## Next action

Run `git fetch origin claude/etsy-automation-agents-WFAPU && git log
origin/claude/etsy-automation-agents-WFAPU --oneline -20` to see what's
landed since this handoff was written. If the sundial and cable clip both
show real commits, both are done — move on to the fidget-card design
(after asking Scott what it actually is) or whatever Scott asks for next.
If either is still missing, pick it up from the state described above
(sundial: `openscad_models/sundial_WIP.scad` on Frank's volume, solar-math
verified; cable clip: ask Scott, since this session has no artifact for
it at all).

## Pointers

- Branch: `claude/etsy-automation-agents-WFAPU`, last commit this session
  confirmed as landed: `92b0902` ("Add OnBrandCraftz negative-mark
  standing rule, fix sundial azimuth 180-degree bug, record two reference
  design ideas")
- Design skill (read before writing any `.scad`):
  `.claude/skills/3d-print-design/SKILL.md` — Technique 22 (print-in-place
  barrel hinge), Technique 23 (physically-computed sundial geometry,
  per-hour isolated verification) are most relevant to the open threads
  above
- Sundial WIP: `openscad_models/sundial_WIP.scad` on Frank's volume
  (`GET /api/files/download?root=volume&path=openscad_models/sundial_WIP.scad`)
- OpenWhen live listing: `https://www.etsy.com/listing/4560574821`
- Product catalog overrides (source of truth for anything not in the
  git-tracked `data/product_catalog.json`):
  `product_catalog_overrides.json` on Frank's volume
