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

## Update 2 (continue-f22my6 session, 2026-08-27, later still — end of session)

**Fidget-card screenshots arrived this session** (2 images + 1 video: a
real "Twelve-in-One Fidget Toy Collection" by YEZAO, MakerWorld/Bambu
Handy reference). Built **v1** (3 mechanisms: rolling wheel, slider,
button) inspired by it, then Scott gave direct feedback: *"The fidget
card will need more work. It doesn't have nearly enough on it."* Built
**v2**, expanding to **8 mechanisms**: 2× rolling wheel, T-slot slider,
3× click button, rotating dial, joystick (ball-in-socket), maze groove
(fingertip-traced channel), plus grip texture, keychain hole, and the
OnBrandCraftz maker's mark. Both versions fully verified (CGAL
`Simple: yes`, connected-components, multi-direction ray-casting, PNG
render review) and **committed + pushed**:
- `openscad_models/cable_clip.scad` — commit `e835c37`
- `openscad_models/fidget_card.scad` v1 — commit `9f4d66a`
- `openscad_models/fidget_card.scad` v2 (current) — commit `69b3596`
- All pushed to `printing3dthings-afk/Etsy`,
  branch **`claude/etsy-automation-agents-continue-f22my6`** — note this
  is a *different* branch name than `claude/etsy-automation-agents-WFAPU`
  referenced earlier in this same handoff file; the harness assigned this
  continuation session a new branch. **Check both branches** when
  resuming — `git fetch origin claude/etsy-automation-agents-WFAPU
  claude/etsy-automation-agents-continue-f22my6` — before assuming either
  is the current source of truth.

**Skill file extended with 3 more techniques** (all in
`.claude/skills/3d-print-design/SKILL.md`, inserted before the closing
"one rule that matters most" section) — **read these before writing any
more OpenSCAD this queue**:
- **Technique 24** (from the cable clip): per-slot-parity hinge
  clearance (a single uniform clearance channel sized for both mechanisms
  leaves both floating — cut clearance only at the *other* side's slot
  positions); a `translate()` must happen *before* `rotate()`, using the
  object's pre-rotation length axis, to actually move it along its own
  length; and the big one — **exact-vertex-sharing connected-component
  checks (Technique 20) are not sufficient** to prove two parts don't
  interpenetrate, because CGAL's `union()` can generate brand-new
  intersection vertices that exist in neither original part's mesh. A
  ray-casting point-in-mesh sweep is the necessary complement.
- **Technique 25** (fidget card v1): a rotation axis's sign convention
  does NOT transfer from a different axis fixed earlier — each
  `rotate([90,0,0])`/`rotate([-90,0,0])`/etc. needs its own empirical
  check by rendering the isolated module and reading its real STL
  bounding box. Also: a ray-cast overlap result must be checked across
  10-20+ random directions before trusting it — a single direction near a
  boundary can give a coin-flip ~50% vote (tangency, not a bug) that
  looks alarming until compared against a real bug's ~90-100% consistent
  vote. Also: structural/interpenetration checks catch zero layout bugs
  between two *static* cuts (e.g. a keychain hole visually merging with a
  button bore into one "eclipse" shape) — only caught by actually looking
  at a rendered PNG.
- **Technique 26** (fidget card v2): process fix — validate a
  multi-feature layout as plain Python bounding-box pairwise-overlap
  checks *before* writing any `.scad`, not after. Also confirms a
  **recurring bug pattern, now seen 3 times across 2 sessions**: a
  captured/floating part's surface must never sit at an EXACT coincident
  coordinate with its cavity's own boundary (floor or shoulder) — even
  though it looks like it should be "touching, not fused," CGAL's
  `union()` genuinely fuses it. The fix is a real symmetric `flange_gap`
  clearance built into the geometry on *all* sides of the cavity, never
  just the side that seemed to need it.

**Frank's volume upload — BLOCKED, not done, real next action for the
fresh session.** Per the standing rule, both `.scad` files (and their
STLs) should have been uploaded to Frank's persistent volume via
`POST /api/files/upload`, verified by re-downloading and comparing MD5.
This session had **zero working path to Frank/Etsy/Railway credentials**:
1. No `.env`/credentials in this container at all (same gap as Update 1
   above).
2. Direct `curl` to both `backboard.railway.app` (Railway's GraphQL API)
   and `etsy-production-b2f1.up.railway.app` (Frank's own backend) —
   using a raw Railway API token Scott pasted directly in chat — returned
   **403 on the proxy's CONNECT tunnel**. Confirmed via
   `$HTTPS_PROXY/__agentproxy/status` as an environment-level network
   egress policy denial (this session's environment blocks those
   specific hosts, alongside other already-blocked hosts like
   `mcp.context7.com`), **not** a bad token or auth problem. Per this
   environment's own rules, a 403/407 from the proxy is reported, never
   retried or routed around.
3. Scott then added a Railway MCP connector at the account level. It
   connected once — `mcp__Railway__whoami` succeeded — then the server
   disconnected on its own (confirmed via a system notification listing
   all `mcp__Railway__*` tools as no longer available).
4. Scott toggled "enabled for this chat" specifically afterward, but the
   tools still did not reappear in this running session (`ListConnectors`
   kept reporting `enabledInChat: false`; `ToolSearch` found zero Railway
   tools). Best available explanation (not confirmed): a connector's
   chat-level enablement may only take effect for a session started
   *after* the toggle, not one already running.

**Because of this, Scott chose to start a fresh session** with Railway
enabled account+chat-side before that session begins, specifically so
this handoff could be written first. **The concrete next action for that
fresh session:**
1. Confirm Railway MCP tools are actually live — `ToolSearch` for
   `mcp__Railway__*` or a direct `whoami`-style call — before assuming
   anything.
2. Use them (`list-variables`/`get-service-config` or equivalent) to
   fetch `APP_SECRET_TOKEN` and Frank's real deploy URL
   (`etsy-production-b2f1.up.railway.app`, per CLAUDE.md, but confirm).
3. Regenerate STLs if wanted:
   `python3 tools/openscad_render.py openscad_models/cable_clip.scad -o cable_clip.stl`
   and same for `fidget_card.scad`.
4. Upload `openscad_models/cable_clip.scad`, `openscad_models/fidget_card.scad`
   (and STLs if generated) via `POST /api/files/upload?path=<rel>`, then
   **verify by re-downloading and comparing MD5** — this is the one step
   this whole thread has been blocked on, do not skip the verification
   half even once the upload succeeds.
5. Only after that: pick up sundial (still waiting on the WIP file/phone
   session per Update 1) or whatever Scott asks for next. The fidget card
   v2 has not yet received a second round of feedback from Scott — it may
   need another iteration.

**Not an action item, FYI only:** Scott also sent a TikTok video about a
3D-print AI assistant concept called "Winston" and explicitly said
*"Just FYI / inspiration"* — no build, no comparison, no action requested
on it.

## Pointers

- Branch (original thread): `claude/etsy-automation-agents-WFAPU`, last
  commit confirmed landed: `92b0902` ("Add OnBrandCraftz negative-mark
  standing rule, fix sundial azimuth 180-degree bug, record two reference
  design ideas")
- Branch (this continuation session):
  `claude/etsy-automation-agents-continue-f22my6` — commits `e835c37`
  (cable clip), `9f4d66a` (fidget card v1), `69b3596` (fidget card v2,
  current), plus SKILL.md updates for Techniques 24/25/26. All pushed to
  `printing3dthings-afk/Etsy`.
- Design skill (read before writing any `.scad`):
  `.claude/skills/3d-print-design/SKILL.md` — Technique 22 (print-in-place
  barrel hinge), Technique 23 (sundial geometry), **Technique 24/25/26
  (new this session — hinge clearance parity, ray-cast multi-direction
  verification, layout-vs-structural bug distinction, recurring
  captured-part flange-gap bug)** are most relevant to any further work in
  this queue.
- Cable clip: `openscad_models/cable_clip.scad` (committed, NOT yet on
  Frank's volume — see above)
- Fidget card: `openscad_models/fidget_card.scad` (committed, v2/current,
  NOT yet on Frank's volume — see above)
- Sundial WIP: `openscad_models/sundial_WIP.scad` on Frank's volume
  (`GET /api/files/download?root=volume&path=openscad_models/sundial_WIP.scad`)
- OpenWhen live listing: `https://www.etsy.com/listing/4560574821`
- Product catalog overrides (source of truth for anything not in the
  git-tracked `data/product_catalog.json`):
  `product_catalog_overrides.json` on Frank's volume
