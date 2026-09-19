# Virtual P1S Chamber — print-playback viewer

Replays a real sliced G-code file move by move, in a browser. The page is
static; everything it draws came out of the slicer.

## Files

| File | What it is |
|---|---|
| `virtual_p1s.html` | The page — layout, palette, reference panels. Publish this as the Artifact. |
| `app.js` | Scene, bead geometry, playback, UI. Served next to the page. |
| `jobs/index.js` + `jobs/<id>.js` | Generated payloads, one script per plate. **Committed** (54MB) — the Pages workflow has to find them, and re-slicing 72 plates in CI would need PrusaSlicer and the better part of an hour. Regenerating them adds that much to history again, so do it when there is a reason, not by habit. |
| `build_site.py` | Wraps the page into a standalone document and copies the payloads beside it. |
| `../plate_audit.py` | Checks every plate against the P1S's real printable area. Exits non-zero on one that could not print. |

## Rebuilding the job payloads

```bash
python3 tools/virtual_printer.py openscad_models/sauce_tray.stl -o /tmp/sauce_tray.gcode
python3 tools/gcode_viewer_data.py /tmp/*.gcode -d <viewer>/jobs \
    --label sauce_tray="Sauce Tray (6-well)" \
    --note  sauce_tray="One sentence on what this plate teaches."
```

`gcode_viewer_data.py` writes `jobs/<stem>.js` per file plus `jobs/index.js`,
which the page loads first. A job script is only fetched when its card is
clicked, so adding a heavy plate does not slow the first paint.

## Opening it somewhere other than an Artifact

An Artifact link is private to whoever owns it, so it cannot be handed to
someone else to look at. `build_site.py` turns the same page into plain static
files that work anywhere:

```bash
python3 tools/viewer/build_site.py          # -> tools/viewer/site/
cd tools/viewer/site && python3 -m http.server
```

That folder is the whole thing — one HTML file, two JS bundles (the viewer and
a vendored copy of three.js), one script per plate. No server logic, no build
tooling. Copy it to a USB stick and it still works.

**Offline is a tested claim, not an assumption.** The page's own `<script src>`
points at the three.js CDN, so the build rewrites it to the local copy and
fails loudly if `vendor/three.min.js` is missing rather than shipping a folder
that quietly needs the internet. Verified by loading the built site with every
non-localhost request aborted: three.js r128 loaded, 72 plates listed, a plate
opened and drew 423,863 vertices, zero page errors. The one request that stays
remote is the Google Fonts stylesheet; blocking it only falls the type back to
the system stack.

**The 54MB never lands on a phone at once.** First load is 737KB — the page,
the viewer bundle, three.js, and the plate index. A plate's toolpath is only
fetched when its card is tapped: 0.7MB for a median plate, 3.1MB for the
heaviest, 6KB for a single label. That is the whole reason payloads are one
script per plate instead of one bundle.

**This is a build, not a copy, and the difference matters.**
`virtual_p1s.html` starts at `<title>` with no doctype, charset or viewport,
because the Artifact host supplies all three. Serve that file raw and a phone
lays it out at 980px -- the exact fiction that made every local mobile
measurement wrong earlier in this project. Verified after building: a 390px
phone reports a 390px layout, no horizontal scroll, all 72 plates.

`.github/workflows/pages.yml` publishes it to GitHub Pages on every push that
touches `tools/viewer/`, which gives one public URL that opens on a desktop, a
phone, or anyone else's device. The repo is public, so this costs nothing --
and it means the site is public too, same as the models already in the repo.

**Pages needs one manual switch before that workflow can finish.** Settings ->
Pages -> Build and deployment -> Source: **GitHub Actions**. The workflow asks
for it automatically (`enablement: true`) but the workflow token is not allowed
to grant it — the first run failed with "Resource not accessible by
integration". Everything before that step passed, including the built site and
the plate-count guard, and the workflow now prints that fix in its own log
instead of just failing. The steps *after* it (`upload-pages-artifact`,
`deploy-pages`) have never run, so treat them as untested until a green run
exists.

## Rendering (overhauled 2026-09-17)

Everything used to draw with `MeshLambertMaterial` under the renderer's
default linear output. That is why the machine read as one flat navy shape and
the print floated above a plate it was supposedly standing on.

| | before | after |
|---|---|---|
| Output | linear, no tone curve | sRGB + ACES filmic, exposure 0.95 |
| Materials | Lambert / Basic | `MeshStandardMaterial`, per-surface roughness + metalness |
| Ambient | one flat `AmbientLight` | PMREM environment built from a procedural studio |
| Shadows | none | PCF soft, 1536², manually scheduled |
| The print | raw `ShaderMaterial`, own two-light maths | real PBR material, injected vertex colour |
| Backdrop | flat black void | gradient backdrop, floor, cast shadow |

Four things here were found by measuring, not by eye, and each is a trap worth
knowing about:

1. **three r128 has no automatic colour management.** A hex authored in sRGB
   has to be converted to linear on input or the whole scene washes out. That
   is what `lin()` is for, and why every material colour goes through it.
2. **An environment map lights everything.** A cool fill that looks like a
   tasteful accent in isolation turned the entire printer powder blue. It is
   now restrained, and painted panels reflect far less of the room than
   machined rails do.
3. **The print washing out was never one light being too bright.** Measured
   with each light isolated: every one alone gave the bead saturation
   0.47–0.55, and it was only their sum, at value 0.86, that pushed ACES into
   desaturating orange toward white. The fix was halving the total budget, not
   retuning one lamp.
4. **A flat box face samples the environment in exactly one direction**, so it
   renders as one uniform colour however good the material is. The exterior
   stayed dead flat through the whole PBR pass until the panels got a
   procedural orange-peel normal map to break the reflection up.

**Cost, measured, and not hidden.** On this container's software rasteriser
(SwiftShader — CPU, so it penalises fragment work far harder than any real
GPU) the same frame went 148ms → 517ms at high detail and 402ms at fast.
Shadow-map updates are scheduled manually rather than every frame, which cut
p90 from 1282ms to ~600ms; the rest is fragment shading. The existing
one-way auto-downgrade still measures real frames after a job loads and steps
to fast below 22fps, and it fired on its own during testing. Fast detail is a
different material class (`MeshPhongMaterial`), not the same one turned down,
because three applies `scene.environment` to every standard material and r128
gives no per-material way to opt out of that sample.

**None of this makes the replay more accurate.** The Limits tab says so
directly: the lighting is an invented studio rig, the real P1S has one LED bar
on the left beam, and a better-looking replay is not a better-informed one.

## Stills in the viewer (2026-09-19)

Part-only framing now shows the path-traced still when one exists for the
plate, and stays live when it does not. Nothing about it is required: a plate
with no still, or a site built without any, simply behaves as before.

**The still is of the FINISHED part, so it is only ever shown at the end of
the print.** Scrub back to layer 50 and the live view returns. Showing a
photograph of a completed object over a half-built one is exactly the class of
thing this shop's first rule forbids, and there is a test that fails if the
condition is dropped.

Supports are excluded from stills and kept in the live view, which sounds
inconsistent and is not: live, you are watching the machine build, and the
scaffolding really is standing on the plate; a finished part has had it
snapped off. Without this the axolotl plate -- more support polyline than part
-- rendered as an unrecognisable spire.

Pipeline, and where each piece lives:

    tools/render_plate_stills.sh    mesh + render every plate (resumable)
    tools/webify_stills.py          PNG -> the committed 900px JPEGs
    tools/viewer/build_site.py      copies those into the site

The full renders are ~2.5MB PNGs and stay out of git; the JPEGs are ~20KB each
because the frame is mostly flat backdrop, so all 72 come to about 1.5MB. That
is what makes this fit at all: the artifact was already 54MB against a 64MB
ceiling, and the 18MB these were estimated at would have busted it.

**Two bugs in `blender_render.py` fell out of driving it at volume.** Its
`--version` probe had a 15s timeout and a cold start here measures 13.3s, so
under any load it tripped -- and killed a 72-plate batch on its first plate.
And camera distance was a flat `size * 2.6` regardless of focal length, which
tangled lens with framing: 85mm cropped a tall part, and the wide lens you
reached for to fit it left the subject a speck. Distance scales with lens now,
so the lens sets perspective and framing stays constant.

## Studio stills (2026-09-18)

The viewer's beads are a three-vertex open tent because it has to hold a frame
rate on a phone. That is the right trade for watching a print happen and the
wrong one for looking at the finished part: one bead per 0.2mm layer is about
a pixel on screen, and the lighting swinging across a sub-pixel face is what
makes the surface read as sandpaper. No shading fix helps, because the detail
is finer than the sample grid. Offline there is no frame budget.

    python3 tools/gcode_to_mesh.py tools/viewer/jobs/vase.js -o /tmp/vase.ply
    python3 tools/blender_render.py /tmp/vase.ply -o still.png --lens 38
    tools/render_plate_stills.sh          # both steps, every plate, resumable

`gcode_to_mesh.py` sweeps a closed rounded-rectangle bead along every
extrusion in a viewer payload and writes binary PLY. Built from the shipped
payload rather than raw G-code for two reasons: those are committed for all 72
plates, and it guarantees the still shows the same toolpath the viewer does.

Measured: 538k vertices, 1.0M triangles, 18.8MB for the 600-layer vase; ~14s
to build, ~155s to path-trace at 64 samples.

Four bugs, each of which produced a file that opened fine and was wrong in a
way only a render or a measurement showed. All four now have tests:

1. Vertices are appended one block per cross-section corner, so `len(verts)`
   counts blocks. Using it as a face base index orphaned 79% of the mesh and
   turned a 120mm vase into a 22mm stub -- with a perfectly correct vertex
   array.
2. Sweep winding follows whichever way the slicer walked each loop, so the
   whole mesh came out inside-out. Watertight, winding-consistent, negative
   volume: nothing flagged it except the sign, and Cycles quietly shaded the
   inside of every bead.
3. A bead exactly one layer tall meets its neighbour on a hairline and renders
   as separate ribbons. `--squish` (default 1.25) overlaps them the way real
   extrusion does; overlapping solids cost a path tracer nothing.
4. The mesh is built in plate coordinates, so a part mid-bed sits ~128mm off
   origin and framed as a close-up of its own base. Centred now -- and
   `blender_render`'s own `--lens` help says the 85mm default "crops anything
   much taller than it is wide", which these plates are. 38mm fits them.

The first version's profile also tapered to half width at the top, putting a
groove half the bead deep between every layer; it is a superellipse now
(`--squareness`, 2 is an ellipse, 4 a rounded rectangle).

## Real print mode (2026-09-18)

A fourth mode beside Feature / Speed / Filament. It answers a different
question from the other three: not *what is the slicer doing* but *what would
this look like sitting in the machine*.

- **One filament colour.** AMS slot colours by default, so a multi-colour plate
  is right without anyone choosing anything; a swatch row overrides it to
  preview a plate in a colour you are about to load.
- **Only what you could see.** Sparse infill and the skirt are hidden.
  Everything else stays, including supports, which are real plastic on the
  plate until you snap them off.
- **Layer lines**, drawn at the plate's own measured layer pitch rather than an
  assumed 0.2mm, and faded out analytically via `fwidth` at zoom levels where
  the band period approaches a pixel. Without that fade, 300 layers across
  400px sits right at Nyquist and aliases into surface noise.
- **Three framings**: in machine (head running), head parked, part only.

Four bugs found here, every one of which rendered a wrong picture with no
error, and all four now have tests:

1. `frameJob()` re-shows the gantry and Y rails as part of rescaling the head,
   so any framing applied before it gets silently undone.
2. `updateCutaway()` runs every frame and re-asserts AMS visibility, so it
   undid the solo hiding one tick after it was applied.
3. Hiding the inner perimeter left a one-bead shell. Beads are drawn as open
   tents, so the gaps between them on a curved surface show the unlit far wall
   as dark speckle. Keeping both walls is both better looking and more honest.
4. The P1S drops the bed, which this viewer models by sinking the print -- so a
   finished part sits a full part-height BELOW z=0. Framing it as 0..height put
   it off the bottom of the screen, and leaving solo without re-framing left
   the camera underneath the bed.

**Diagnostic colours got their saturation back.** The PBR overhaul the day
before left the feature colours visibly paler than their legend swatches,
because tone mapping desaturates saturated colour as it brightens. That is
correct for a photograph of a print and wrong for a key you read a legend
against, so the diagnostic modes restore saturation after the tone curve,
where the loss happens. Real print mode sets that to zero: it wants the
photographic behaviour.

## Colour modes

**Feature** uses the slicer's own `;TYPE:` tag. **Speed** uses the real `F`
word on every move. On the stock P1S profile those speeds are not arbitrary:

| Feature | mm/s |
|---|---|
| Top solid infill | 15 |
| Solid infill | 20-30 |
| External perimeter | 30 |
| Perimeter | 60 |
| Internal infill | 80 |

The outer wall runs at half the inner wall and the top surface at a quarter of
the infill, which is CLAUDE.md's "slow down the outer wall" production rule
already present in the stock profile. Speed mode makes that visible rather
than asserted -- and the per-type table in the panel is computed from the
job's own bytes, not typed in.

The ramp is magma reversed and clamped to [0.28, 0.92], so **bright is slow**
-- the surfaces a buyer sees. The raw dark end made fast infill vanish against
the chamber; the clamped range runs luminance 221 -> 46, monotonic, with the
dark end still clear of the `#0d0e11` background. The same numbers appear in
three places (the GLSL ramp, `speedColor()` for legend swatches, the CSS
gradient) -- change one and change all three.

## Build plates, and how a print gets aligned on one (2026-09-19)

The bed used to be a grey square with a grid on it. It is now the actual
plate, and which plate is a control in the Printer panel.

**The numbers are Bambu's, read out of Bambu's own shipped slicer profiles,
not from memory:**

| | | from |
|---|---|---|
| Printable area | `0x0, 256x0, 256x256, 0x256` | `resources/profiles/BBL/machine/fdm_bbl_3dp_001_common.json` |
| Reserved corner | `0x0, 18x0, 18x28, 0x28` | `resources/profiles/BBL/machine/Bambu Lab P1S 0.4 nozzle.json` |

So: origin at the **front-left corner** of the plate, the full 256 x 256 mm
usable, and an **18 x 28 mm rectangle in that front-left corner reserved** —
where the toolhead parks and wipes. The common profile reserves a bigger
L-shaped region and the P1S overrides it with the smaller rectangle, so the
override is the one that counts. Both are drawn on the plate (the reserved
corner in orange) and both are what `tools/plate_audit.py` checks.

Alignment is two things stacked. In hardware, the plate is not positioned by
eye: the slot in its rear tab drops over the heatbed's locating pins, which is
what makes 0,0 land in the same physical place every time you flex a print off
and put the plate back. In the slicer, the part is then arranged inside that
square — centred on 128, 128 for a single object, clear of the reserved corner,
with the wipe tower (if any) placed beside it and the group centred rather than
the part.

### Auditing it

```
python3 tools/plate_audit.py            # all 72
python3 tools/plate_audit.py sundial    # one
```

**Result: all 72 plates print as arranged.** Every part inside 0..256 both
ways, none in the reserved corner, every single-object plate centred within
1.1 mm. Two warnings worth knowing: `sundial` (247.6 mm wide) and `mushroom`
(244.8 mm) leave too little margin for a skirt, so their skirts run a couple of
millimetres off the plate edge — print those two with the skirt off.

Getting that answer took two corrections, both of which are the reason this is
a tool and not a glance at `jobs/index.js`:

* **The index bbox is the wrong number.** It includes the skirt and the wipe
  tower. Checking it flags 29 of 72 plates, and nearly every one is a false
  alarm — `keychain_mc` looks 43 mm off-centre because it is a multi-colour
  plate and its wipe tower sits out at x 178–242, exactly where a wipe tower
  belongs.
* **Centring has to be measured on the part outline, not on every extrusion.**
  Support material only grows on the overhanging side, so part-plus-supports
  sits 1–3 mm off the outline's middle on two dozen correctly arranged plates.

### The plates themselves

Six entries, each one a plate Bambu actually sells for this machine. The wiki
(`wiki.bambulab.com/en/filament-acc/acc/plates`, read 2026-09-19) supplies what
each is made of and which filaments need glue; **every base colour is the
median sampled out of Bambu's own product photography on that page**, not
picked by eye. Textured PEI really is gold. Smooth PEI really is mid grey, and
the dual plate's smooth face is much darker than the standalone smooth plate,
which is why they differ here rather than sharing a colour.

Each plate's finish is three octaves of speckle — coarse mottle, mid grain,
fine grit — plus a companion height map converted to a real tangent-space
normal map. Three things had to be got right and all three were wrong first:

1. **One octave is not enough**, because a 1024px face texture on a 256 mm
   plate is under one texel per screen pixel at any normal zoom. A single fine
   octave mipmaps away into flat paint everywhere except the rows nearest the
   camera — grain at the front of the plate, bare gold at the back.
2. **Only the middle octave carries height.** Coarse relief gives 30px bumps
   whose normals swing the environment reflection across half a centimetre at a
   time, and every plate came out blotched in light grey. Fine relief is worse
   and is the same geometric aliasing the bead mesh hit: sub-pixel normals
   alias into hard specular, and a matte black plate renders as television
   static.
3. **A height field is not a normal map.** Handing the greyscale height canvas
   straight to `normalMap` decodes flat grey to `(0,0,0)` — a degenerate
   normal — and every lighter blob to a steeply tilted facet. `heightToNormal()`
   central-differences the height and builds the real tangent normal. This was
   the single worst-looking bug the viewer has had, and it reads as a colour
   bug, which is why it took three passes to find.

The printable-area ruling and the orange reserved corner are **annotation, and
they disappear in real-print mode** — no plate has them painted on it, and real
mode is "what this looks like in the machine".

The offline stills (`tools/render_plate_stills.sh`) deliberately keep their
neutral studio floor rather than a plate. A still is captioned *the finished
part*: supports snapped off, print flexed off the plate. Putting it back on a
gold plate would be a nicer picture of a different claim.

## The actual bug: three.min.js was never published (2026-09-19)

After four rounds of cache theories, the page finally said what was wrong —
and it was none of them. **The artifact had no `three.min.js` in it.** The
`<script src="three.min.js">` 404'd, `window.THREE` was undefined, and the
page died.

It could not say so, for a reason worth keeping:

```js
var _ray = new THREE.Raycaster(), _ndc = new THREE.Vector2();   // top level
...
if (!window.THREE) { loading.innerHTML = 'three.js did not load...' }
```

The friendly message at the bottom of the file was **unreachable**. A
top-level `new THREE.Raycaster()` threw a bare `ReferenceError` long before
the guard ran, and the boot block's own try/catch could not see it either —
it only wraps the boot calls, and this threw while the file was still being
evaluated. So every symptom was a stuck spinner with no text, which is
exactly what four different causes look like.

Three fixes, all tested by mutation:

* `_ray`/`_ndc` are built on first use, so the guard is reachable. A test
  walks app.js character by character and fails on *any* `new THREE.` at
  top level. (Its first version counted brace depth from 0 and so put the
  bug straight back in undetected — the whole file is inside one IIFE. Its
  second version flagged a one-line function body. Mutation caught both.)
* A global `error` handler is registered as the second statement in the
  file and paints any uncaught throw — from anywhere, including top-level
  evaluation — onto the loading overlay with its message and source line.
* The build fails if `three.min.js` is not placed beside the page.

**Publishing lesson:** a multi-file artifact keeps files you leave out of a
`files` map, which makes it easy to assume a file is there. It was not.
Check the published listing against the build output, not against memory.

## A fix that never reached the phone (2026-09-19)

Three attempts, two of them wrong, both wrong on real hardware rather than in
theory. Written out because the failure mode each time was *silent* and the
symptom was identical: a spinner, an empty plate list, and no way to tell from
the outside which build was even running.

| attempt | what happened |
|---|---|
| `<script src="app.js">` | The phone kept the cached file across a force-quit. A shipped fix simply never ran, three times over. |
| `<script src="app.js?v=<hash>">` | Untestable — the **page** was cached too, so we never learned whether the query worked. |
| inlined into the page | The script is served intact (verified by reading the published HTML back) and **does not execute**. The host does not run inline script in a multi-file artifact. |
| `<script src="app.<hash>.js">` | Works. A URL that has never been requested cannot come from a cache, and an external file is what demonstrably executes here. |

Every earlier hashed bundle is deleted from the build output, and has to be
removed from the published artifact too (`"app.<old>.js": null` in the publish
`files` map) — otherwise it is a file the host would still serve and nothing
would ever refresh.

**The build stamp had two defects of its own**, both found the hard way and
both now guarded by tests:

* it hashed `app.js` and the HTML but **not `build_site.py`** — so the inlined
  build and the hashed-filename build that replaced it, which differed only in
  `build_site.py`, both stamped `b9dd3ff2a2`, and a photograph of the header
  could not say which one was on screen;
* `paintJobList()` **overwrote** it with the plate counts the moment the app
  ran, destroying the version exactly when it was still wanted. The counts have
  their own `#platechip` now, and nothing in app.js may touch `#buildchip`.

The chip also now proves the script *ran*: app.js appends ` · running` to it as
its first statement, before anything that could throw. Two states look
identical in a photograph of a screen — "the page updated but the script never
executed" and "the page did not update" — and telling them apart is what cost
three round trips.

**The thing that finally made this diagnosable** was a *static* build stamp.
The header chip used to be filled by `paintJobList()`, which is precisely the
function that does not run when something is wrong — so on the one occasion
the version mattered, the page could not say what it was. It now reads
`build <hash>` from the moment the HTML arrives, hashed over app.js **and**
virtual_p1s.html so a change confined to either one still moves it. One
screenshot of the header settled in seconds what three rounds of guessing had
not.

**The boot also paints in two stages now.** `initScene()` is by far the most
expensive thing on the page and it ran *first*, so a slow scene left the plate
list, the panels and the transport blank behind a spinner — the page looked
dead when it was only busy. The UI paints first and the scene is built on the
next frame. Measured under a 6x CPU throttle: the plate list appeared at
**14,106 ms before this and 540 ms after**. The overlay names its stage
(`Starting` / `Building the machine` / `Loading <plate>` / `Building <plate>`)
so a screenshot of a stall says where it stalled.

## A 7.5-second stall, and why the page said nothing (2026-09-19)

Reported from an iPhone as, with complete justification, "it isn't working":
seven seconds of screen recording showing the loading spinner, an empty plate
list, an empty Printer pane and no explanation anywhere.

**Nothing was broken. It was still working.** `heightToNormal()` draws the
plate's height field on a canvas and reads it straight back with
`getImageData`. Without `willReadFrequently` on that context the canvas is
GPU-backed and that single read forces a full readback — **measured at 7,491 ms
for one plate**. It sits inside `initScene()`, which runs before `initUI()`,
the panels and `paintJobList()`, so nothing at all reaches the screen until it
finishes. With the hint: 15 ms.

Three changes came out of it, and the first matters more than the fix:

* **A boot failure now reaches the screen.** `initScene()` running first means
  anything it throws takes the whole page with it and leaves a spinner. The
  boot sequence is wrapped and prints the real message and stack line.
* **The plate finish and the AMS are decoration and cannot be fatal.** Either
  failing now degrades — flat plate colour, no AMS — instead of taking the
  replay down. A phone webview hands back a null 2d context once its canvas
  budget is spent, and the next line was a `fillStyle` assignment.
* **The plate face texture is 512 px, not 1024.** Two texels per millimetre on
  a 256 mm plate is finer than the grain it carries; 1024 bought nothing
  visible and cost four times the canvas memory and four times the draw calls.
  Canvas backing store measured across the page: 12.3 MB → 2.3 MB. The normal
  map is also built once per *grain* rather than per plate, since it does not
  depend on the colour — six plates share five grains.

Two things to know if you touch this. Grain radii are authored against a 1024
canvas and scale with `PLATE_PX`, because the grain is a size on the plate and
not a count of texels. And `heightToNormal`'s `strength` is a per-texel slope,
so it has to *fall* as resolution falls: a feature spans half as many texels on
a 512 map, so the height difference between neighbours is already twice as
large. Scaling it the other way made the textured plate four times too rough —
gold turned into corrugated orange, measured as rgb(119,108,87) → rgb(99,74,44)
at the plate centre.

Colour and height are still drawn from the same sequence so a bright fleck is a
raised fleck, but via a seeded PRNG rather than `Math.random()` in one shared
pass — that is what lets the two be built separately and cached differently.

## The bead has a flat top (2026-09-19)

Reported as "the real print images are showing some missed areas after
printing", and narrowed to the top and bottom faces. It is not a hole and it
is not a missing layer — it is the bead's cross-section.

The bead was a **tent**: two shoulders at the layer floor, an apex at the
layer top. That makes the top of every extrusion a zero-width *ridge*, and the
shoulder normals exactly horizontal. Seen from above, half of every bead's
visible area shades from lit at the ridge to black at the shoulder, so a solid
top face renders as corduroy with what look like gaps in it.

A real extrusion is squashed between the nozzle and the layer below: a
rectangle with semicircular ends, flat across most of its width and rounded
only at the edges. The section is now four points across — shoulder, top
corner, top corner, shoulder — three bands instead of two.

**The flat's width is derived, not tuned.** A single free extrusion has its
flat at `hw - h/2`. Neighbours in a solid layer are not free: they are laid
down molten against each other and *fuse*, so the groove between two of them
is much shallower than the intersection of two separate stadium profiles. The
divisor 2.6 is that fusion, and the picture chose it — measured on the label
tile's top face, the share of pixels dark enough to read as a gap rather than
a tool mark:

| profile | gap pixels | min luminance |
|---|---|---|
| ridge (old) | 15.0% | 62 |
| stadium (`/2`) | 5.6% | 81 |
| **fused (`/2.6`)** | **2.2%** | 82 |
| smoother (`/3.2`) | 0.9% | 84 |

`/3.2` scores better and looks worse — the top stops reading as printed at
all, which is the opposite failure. This is a case where the metric had to be
overruled by looking.

**It costs geometry, and that is the trade taken deliberately.** Scott's call
was iPad first, quality wins ties. Measured on the vase, identical scene:

| | triangles | median frame | p90 |
|---|---|---|---|
| ridge | 517,716 | 1417 ms | 2129 ms |
| flat top | 774,936 | 2033 ms | 4150 ms |

+50% triangles for +43% frame time — on a **software rasteriser**, where
triangle count is the whole cost. A real GPU does not care about 775k
triangles; its cost is fill rate and shader work, neither of which changed.
Treat those numbers as the shape of the trade, not as what an iPad does.

Two things any future change here has to keep, both guarded by tests:
`setDrawRange` steps by the same 18 indices per segment the index writer
emits (they disagree silently and only part way through a replay), and the
shoulders stay at the full half-width or the part gets thin.

## Full screen (2026-09-19)

`#app` goes fullscreen, not the canvas. The transport and the plate list are
what make this a tool rather than a picture, so they come along. The button
hides itself where `requestFullscreen` does not exist rather than sitting
there doing nothing, uses the `webkit` prefix as well (Safari is the browser
this is for), and its label follows the `fullscreenchange` **event** rather
than the call — a refused request must not leave the button lying.

## The AMS (2026-09-19)

Rebuilt from Bambu's own product photography of the 4-slot unit. The shape
that makes it recognisable is the **dome**: a half-cylinder of smoked plastic
whose axis runs along the spool row, so its arch follows the spool circles and
the top half of every reel shows through it. It was a flat-lidded box before,
which from above read as an empty tray with one spool in it.

Proportions are arithmetic off the published 368 x 283 x 224 mm rather than a
guess: the dome radius is half the depth (141.5), so the body below it is the
remaining 82.5 — which is exactly the split the photographs show. Spools are
the AMS's own published compatibility range, 197–202 mm across and 50–68 wide,
which is why four of them very nearly fill the box. Each slot also gets its
drive roller and gear block, visible through the smoked front the way they are
on the real unit.

Deliberately unbranded, same as the machine — the real front band carries a
Bambu Lab wordmark and that is not mine to reproduce.

Three things had to hold while rebuilding it:

* **The coil has to stay a Y-axis cylinder under an X-turned parent**, because
  `updateAMS()` scales its x/z for the falling radius and spins its y. Rebuild
  it any other way and the spool silently gets narrower as it empties instead
  of thinner, and tumbles end over end instead of turning.
* **The flanges are the reel, not the filament**, so they do not shrink with
  the coil — and they have to hide with their slot, or hiding an unused slot
  leaves three pairs of empty discs hanging in the dome.
* **`rotation.y` alone does not orient a half-disc end cap.** `CircleGeometry`
  bulges toward its own +Y, which after that one turn points at world +Y — so
  the caps stood up as flat sheets off the back of the dome instead of closing
  its ends. The z turn (composed first, three.js does XYZ as Rx·Ry·Rz) swings
  the bulge to +Z so it follows the arch.

## The machine itself

Built to the real outside dimensions, **389 x 389 x 458 mm** around the 256mm
build cube (bambulab.com and the US store listing, checked 2026-09-16). Solid
exterior panels, smoked glass front door, inset top cover, screen and knob on
the bottom-right bezel, feet, rear spool holder. The machine-view framing is
computed from the real outer extent rather than a tuned constant, because an
AMS on the lid makes the stack half again as tall and a fixed radius left it
hanging off the top of the frame.

**Deliberately unbranded.** The proportions are the machine's; the logo is not
mine to reproduce, so there isn't one.

**The door is a real hinge**, not a fade: a Group pivoted on one vertical edge
and rotated ~110 degrees. Which edge is a **profile setting** (`hingeLeft`),
not a baked assumption -- no primary source I could reach stated the P1S hinge
side, so it is exposed rather than guessed. Flip it in `PRINTERS` if it is
backwards.

**You open it by touching it.** The glass, the frame and the handle are all
hit targets (`userData.door`); a pointerup that travelled under 7px raycasts
against them and toggles. The threshold is in pixels rather than time because
a phone "tap" always carries a few pixels of finger travel, and a drag that
starts on the door has to orbit, not open it. On a mouse the cursor turns to a
pointer over the door -- a phone has no hover, so that raycast is skipped
there rather than run on every touchmove. The toolbar button still works.

**The AMS on the lid is Scott's, at its real size**: the standard 4-slot unit,
**368 x 283 x 224 mm, 2.5 kg**, from Bambu Lab's own "AMS Tech Specs" table
(us.store.bambulab.com, checked 2026-09-16). Getting this right took a
deliberate second look -- searching "AMS dimensions" surfaces the **AMS HT**
(114 x 280 x 245) first, and the **AMS 2 Pro** (372 x 280 x 226) is a third
box again. All three get called "the AMS" and only one is the one on screen.
`tests/test_viewer_machine_profile.py` fails if those numbers are ever swapped
for a neighbour's. It is a profile field, so the A-series entry declares none
(AMS Lite is a different unit, not P-series compatible) and nothing is drawn
for it. The spools are drawn at the AMS's own published compatibility range,
197-202mm across and 50-68mm wide, which is why they nearly fill the box --
their colours are illustrative and the panel says so, because nothing here is
reading a real machine. The AMS steps aside in chamber view: it is furniture
on the lid, and in cutaway it would sit on top of the hole the cutaway opened.

### One machine is drawn as itself; the rest get an honest envelope

Selecting the A2L used to draw a fully enclosed case with a smoked glass door
-- while the panel two inches to its right read **"Enclosed: No · Chamber:
None (open frame)"**. The picture contradicted its own caption, on the same
screen, in a page whose whole job is teaching how a machine works. That is the
worst kind of defect this thing can have.

The rule now: **only the P1S is drawn as itself**, because it is the only one
whose service documentation has actually been read. Every other profile gets
an envelope -- published footprint as an edge outline, the base, the bed, the
build volume where the machine can really reach, the gantry, a generic head.
No case, no door, no chamber light, no screen, no invented internals. The
"Open door" button hides itself on a machine that has no door.

The A2L's own facts, verified 2026-09-17: open frame, bed-slinger, no
enclosure, bed capped at 80 degC, footprint **544 x 529 x 505 mm**. Those are
the only things drawn for it.

**And it moves like itself.** A bed-slinger travels the BED in Y and climbs
the gantry in Z; the P1S holds the gantry and drops the bed. Measured on the
same plate: P1S bed z goes -6 to -9 while the gantry holds 19; A2L bed y goes
46 to 13 with bed z pinned at 0 while the gantry climbs 25 to 27 and the
nozzle's Y stays at the bed centre. Two genuinely different machines, not a
reskin. The vertical layout flips with them -- a descending bed needs the case
to reach `-Z` below the plate, a slinger stands up from just under it.

Detailing a second machine properly is a research job per machine, not a
setting. That is the honest cost of the "more printers" goal, and the envelope
is what keeps the page truthful until that work is done.

Two view modes, because the two jobs conflict:

* **View: machine** keeps the exterior solid, so the printer looks like a
  printer. You see in through the glass, or through the opening once the door
  swings.
* **View: chamber** hides whichever panels sit between the camera and the
  build volume (dot product of panel normal against the camera vector). It is
  the only way to watch a print from an arbitrary angle without the case in
  the way.

Exterior and toolhead use `MeshLambertMaterial` with a real key/rim/ambient
rig. The bead shader is unlit and independent -- lights do not touch it. Flat
unlit panels read as cardboard, which is what the first pass looked like.

## What the scene gets right about the machine

**The gantry is fixed and the BED descends.** On a P1S the toolhead moves only
in XY; the heatbed travels down its lead screws as the print grows. The first
build animated the part rising, which is the wrong machine. `bedGroup` holds
plate, grid, contact shadow and the printed part so one transform moves them
exactly as the real bed does. The "Bed drops / Part grows" button switches it.

Two geometry traps this exposed, both found by rendering and looking:

* The enclosure has to span the **full bed travel**. Built to the obvious
  height, the plate sank through the chamber floor and vanished 88mm into the
  vase. The interior now runs from below the lowest bed position to above the
  gantry -- so at layer 1 the bed sits near the top, which is where it really is.
* The shell is **one inverted box** (`side: THREE.BackSide`), not six panels.
  Six opaque panels put the near wall between the camera and the print; that
  render came out solid black. BackSide culls the near wall and shows the
  interior of the far ones, which is how you look into a real enclosure. The
  nearest corner post is culled per frame for the same reason.

### Inside, from Bambu's own service documentation

The first pass drew the interior as a plausible guess and labelled it a guess.
Going and reading the manufacturer's service pages turned most of it into
fact, and corrected two things that were simply wrong:

| drawn | source |
|---|---|
| **Three** lead screws, not two, turned together by one stepper through a belt under the base, with a tensioner also underneath | "The Z-axis is comprised of three lead screws that are connected to a single stepper motor using a belt" (Introduction to P1 series); Z motor / Z timing belt / Z tensioner service pages |
| Three Z sliders carrying the bed | "lock in 3 auxiliary screws to fix the 3 Z-axis sliders" (Z motor) |
| CoreXY with an independent belt per stepper | "Every stepper motor has an independent belt connected to the print head" |
| Chamber LED on the **left** beam, beside the chamber camera | P1 Camera and LED guide: both reached through the left panel, both on the AP board, and the LED "will get caught by the camera" if slid the wrong way |
| Chamber camera at the front-left column | same guide: housing seats in a notch on the frame, flex cable tucked behind the front cover |
| Toolhead as front / middle / rear housings, part-cooling fan in the front one, filament cutter lever, PTFE pneumatic joint on top, all-in-one hotend | Toolhead housing + hotend service pages; "the nozzle is integrated into the heat block and connected to the heatsink via a thin metal tube" |
| A 2.7-inch 192x64 screen -- a 3:1 letterbox, not the near-square first pass | P1 sensors/electronics spec list |
| No LiDAR | that is the X1 Carbon |

Two things are still **drawn rather than documented**, and the printer panel
says so on screen: where the three lead screws sit around the base, and the
toolhead's exact proportions. Bambu publishes neither.

**The chamber lamp has to actually light something.** It is a real
`PointLight` at the LED's real position -- but the first version of it was
decorative and I nearly shipped it claiming otherwise. Rendering one frame
with the lamp on and one with it off and differencing them gave **0.79 of a
level out of 255**: a light that was not a light. Cause: the interior liner is
the largest surface in the chamber and it was `MeshBasicMaterial`, which
ignores lights entirely. As Lambert, with the lamp at its real intensity, the
lit left side of the chamber measures **31.1 mean against 23.9 unlit**, while
the right side is unchanged at 25.4 -- a directional pool from the correct
side, which is the whole point of putting it where the real one is.
`tests/test_viewer_machine_profile.py` fails if the liner ever goes unlit again.

The lamp is deliberately invisible to the print: the bead shader is unlit, so
the light changes the machine around the part and never the part itself.

Everything is generated -- PEI speckle, shell gradient, contact shadow, nozzle
glow are all canvas textures, because the artifact CSP blocks image hosts.
The enclosure is deliberately unbranded.

## Performance

3.07M triangles for the heaviest plate. The toolpath itself is **one draw
call** -- one mesh, one `setDrawRange`, no per-frame rebuild. The machine
around it costs the rest: 30 calls bare, 88 with the full interior, the
toolhead and the AMS, all of them static boxes and cylinders.

`--simplify` (default 0.02mm) drops points whose removal shifts the path less
than a twentieth of a bead: 8-30% of points on real plates, with time, mass and
speed data bit-identical afterwards. It will not merge across a speed change.

### Every model in the repo is a plate

Scott: "there are a whole lot more prints than just the eleven -- I need all of
the stuff that is on GitHub, including what I've had OpenAI design." Right: the
eleven were a hand-picked teaching set, while `openscad_models/` holds 147
printable files. **72 plates now**, every one sliced through the real slicer.

Choosing what counts as a plate took some care. 93 file stems reduce to 72 by
dropping pieces that an assembly 3MF already contains -- read from each file's
own `Slic3r_PE_model.config` volume names rather than guessed from filename
prefixes, which is what a first pass did and it quietly dropped the Glow Stand
**v2** as if it were a part of v1, plus both 1 oz sauce variants.

**Three files turned out not to be plates at all**, and the slicer said so
where a mesh check could not: `Crescent_Assembly.3mf` lays its parts out to
X=502mm and `Soft_Frame_Assembly.3mf` to X=819mm, on a 256mm bed. They are
viewing layouts, like Gobble's own `_VIEW_ONLY` file. Their individual parts
are all here and all fit. The sundial looked like a fourth until the per-type
extents showed only its *skirt* crossing the edge -- the part itself spans
4.2-251.8mm and prints fine.

That off-bed case used to surface as a bare `struct.error` from the int16
packing with no filename attached. It now fails with the span and the likely
cause, because "off the bed" is a real answer and a packing error is not.

**Fitting 72 plates in one page.** The artifact ceiling is 64MB per version and
the set came to 66.2MB at full fidelity. Rather than coarsen everything
quietly, `--max-mb` re-simplifies only the plates that exceed a budget and
records the tolerance it settled on; the viewer prints "path simplified to
X mm to fit the page" under any plate that got it. Total: **53.6MB**. Seven of
the heaviest cannot be thinned much further -- the rule that a point is never
dropped across a speed change puts a floor under it.

Each plate names the repo file it came from, so a plate on screen is something
you can go and print rather than only watch. A filter box narrows 72 down by
name or path.

**One thing this broke and had to fix:** three curated notes quoted raw move
counts, and simplification changes those. The notes now cite filament and
time, which it cannot change -- and the mushroom lamp's real number is worse
than the old one said: **79 g of its 227 g is support**, 35% of the filament,
not "20% of its moves".

### Eleven plates, and you can find all eleven

Scott opened it and could not see the rest of the prints. He was right, and
the numbers are ugly: the plate list was a **236px box holding 702px of
cards**, its bottom faded out by a CSS mask, sitting inside a rail that also
scrolled. **Three of eleven** plates were reachable without discovering a
nested scrollbar that this browser draws as a 0px-wide overlay -- invisible
until you already know to scroll. The mask actively said the list had ended.

Fixed by measuring rather than guessing at it: the cap now follows the
viewport (`min(54vh,560px)`), the mask is gone, the heading carries a live
**N / 11**, the selected plate scrolls itself into view, and a button under
the list states in words how many are out of view and pages to them. Desktop
went from 3 visible to 7-8; phone already showed all eleven, because the
narrow layout drops the cap -- the breakage was desktop-only, which is worth
saying since the phone is where most of this got tested.

The scrollbar could not be trusted to carry the message: `offsetWidth -
clientWidth` measured **0**, so styling it was not enough and the hint had to
be text.

### The AMS actually feeds the nozzle

Scott: "make that function the way it should no matter single colour or multi
colour." So none of it is conditional on the plate: the AMS feeds every job,
and a single-filament print is one slot doing all the work.

Per slot, live as the replay runs: how much that filament has used, whether it
is the one currently feeding, and the spool turning as it is pulled off. The
feed line takes the live slot's colour. A third colour mode, **Filament**,
paints every bead in the colour of the slot it came from.

**A real multi-colour plate, not a mock-up.** `tools/assemble_3mf.py` already
writes a per-part extruder into `Metadata/Slic3r_PE_model.config`, which is
exactly what PrusaSlicer reads, so the monogram keychain slices as a genuine
five-filament job: 52 tool changes and a real wipe tower. Two non-obvious
things that took getting there (both now in `virtual_printer.MMU`):

* the wipe tower **requires relative E** -- without it the slice refuses;
* priming must be **off**, or the priming block emits 304 lines of
  `G1 X-40263464.000`, a garbage coordinate rather than a move.

The same plate, one filament against five, is the whole lesson:

| | 1 filament | 5 filaments |
|---|---|---|
| filament | 8.6 g | **33.4 g** |
| of which purge | — | **25.1 g (75%)** |
| time | 57 min | 109 min |
| tool changes | 0 | 52 |

Three quarters of the multi-colour plate is wiped into the purge tower and
thrown away. In Filament mode you can see it: the tower is striped with every
colour it cleaned out.

It also needs **five** slots and one AMS holds four, which the panel says
plainly rather than quietly drawing four and hoping.

**Two measurement traps, both caught by checking rather than assuming.**
PrusaSlicer's own per-extruder footer (`; filament used [mm]`) came to 6,314 mm
against 11,200 mm actually extruded -- it leaves the purge out, and reported
`filament used for wipe tower [g] = 0.00` as well. Every slot would have read
44% light. The exporter measures per filament from the moves instead, which
sums to the job total by construction. Then the viewer made the same class of
mistake one level up: interpolating a slot's usage from the layer total by
segment index charged slot 1 with 24.4 g against its real 17.0 g, because the
purge is a lot of filament laid over very few moves. It reads measured
per-layer rows now, so every layer boundary is exact.

The spool shrinks on the right axis and turns the right way, which sounds
trivial and was not: a cylinder's own axis is local Y, so scaling Y made the
spool narrower instead of emptier and spinning X tumbled it end over end. What
it shows is honest in a way a nicer animation would not be -- 17 g off a 1 kg
spool visibly turns the reel and barely changes its diameter, because 1 kg of
PLA is about 320 m.

### Smoothness while rotating

Three changes, and the first one is the one that matters most:

* **The camera is damped, and the damping is time-based.** `cam` is the target
  every caller writes to; `view` eases toward it and is what gets rendered. The
  easing rate and the fling decay are expressed per sixtieth of a second and
  converted against the real frame time -- never applied once per frame. That
  distinction is the whole feature on a slow device: a flat 0.19-per-frame ease
  on a phone rendering at 9fps takes a second and a half to catch up with a
  finger that has already stopped, which is worse than no damping at all. This
  container's software renderer measures **8-9fps**, so that case was real and
  would otherwise have shipped broken.
* **A flick keeps turning.** Released mid-drag, the view coasts and decays;
  stop first and it holds. The fling is measured as a *velocity* -- angle over
  the real gap between pointer events -- because the browser coalesces
  pointermove while a frame is busy. Measured here: **377ms between the last
  pointermove and pointerup** on a 2fps page, so the original fixed 90ms arming
  window never opened at all. The window and the velocity both scale with the
  observed event gap now.
* **Fewer pixels while the view is moving.** Pixel ratio drops to 1 during a
  drag, pinch, wheel or fling and snaps back the moment it settles. A phone
  caps at 2, which is four times the fragments -- and a moving frame is the one
  frame nobody is studying.

**Detail: high / fast** switches the specular and Fresnel terms with a shader
`#define`, and steps down once automatically if the first measured frame rate
is under 22fps. Do not trust this container's own fps numbers: it renders
through SwiftShader on the CPU, which charges perhaps ten times what a GPU
does for per-fragment math, and repeated measurements in one page drift far
enough that "fast" can measure slower than "high". Draw calls and triangle
counts are deterministic and are what this repo benchmarks.

## This is not a simulator, and the difference matters

Scott asked directly: "if it prints perfect in this it should print perfect in
the real world?" No.

The viewer draws the instruction file exactly. It models **no physics**: no
gravity, no melt rheology, no thermal contraction, no bed adhesion, no layer
bonding, no moisture. The Material tab is reference text; the same G-code
prints in PLA or PETG. The failure modes that actually ruin prints -- warping,
a curled corner the nozzle then strikes, delamination, stringing -- are all
invisible to it. Predicting warping for real is thermo-mechanical FEA, a
different class of tool.

What IS honest is measuring signals from the real file that correlate with
known failures. `tools/print_risk.py` reports five, and reports numbers rather
than verdicts:

| signal | why it correlates |
|---|---|
| `unsupported_span_mm` | longest CONTIGUOUS run of a bridge with nothing beneath |
| `short_layers` | layers under the profile's own `slowdown_below_layer_time` |
| `first_layer_area_mm2` | grip on the plate |
| `aspect_ratio` | tall and narrow gets knocked over |
| `overhang_mm` | length the slicer itself tagged as overhang perimeter |

**Its thresholds are guesses.** They stay guesses until real prints are logged
against them (`--record ok|failed|partial`, `--calibration`), and the report
refuses to claim a signal separates good from bad below 3 examples on each
side. `product_gate.py` prints these as advisories that **never fail the
gate** -- failing a real product on an uncalibrated number is precisely the
threshold-fitting that gate exists to avoid.

The measurement care this needs is real. The longest bridge MOVE on the sauce
tray is 107.9mm, which sounds unprintable; the longest genuinely unsupported
run inside it is 5.6mm, at z=0.8mm -- the ceiling of the engraved maker's mark,
independently where an earlier overhang investigation landed. Reporting 107.9
would have condemned a clean, selling part.

## Two slicer facts this surfaced, both verified against real output

**A layer count is layer changes, not height / layer height.** With supports
on, the slicer gives support material its own layer heights and injects extra
layer changes. Measured on `halloween_pumpkin.stl`: 469 uniform 0.2mm layers
with supports off, 604 with them on, same 93.8mm part. A plain 20mm cube
slices to exactly 100 uniform layers, which is how the config was cleared of
suspicion. The layer-height comparison jobs are sliced WITHOUT supports so
the three differ only in layer height.

**`;HEIGHT:` is per extrusion, not per layer.** A bridge inside a 0.2mm layer
reports 0.4. The cube emits 100 `;LAYER_CHANGE` and 101 `;HEIGHT:` lines.
Take the first after each layer change; taking the last rendered those beads
at twice their real thickness.

**A job's layer height is the modal one, not `layers[0]`.** `first-layer-height`
is pinned to 0.2, so reading index 0 reported a 0.28mm job as "0.20 mm".

## Why the payload looks the way it does

Consecutive extrusions are chained into polylines and XY is quantized to
int16 hundredths of a millimetre. That is what makes an 830,000-move plate
fit in a web page; 0.01mm is a fortieth of a 0.42mm bead, well under
anything the view can resolve. Travel moves are dropped — half the move
count, and nothing is drawn for them.

Each bead renders as a three-vertex "tent" (edge, ridge, edge) rather than a
flat ribbon, so layer lines are visible from a side view. Surface normals
come from screen-space derivatives in the fragment shader, which costs no
vertex attribute and gives the facet shading the tent actually has.

## Honest limits, stated on the page itself

PrusaSlicer is not Bambu Studio — geometric decisions track closely, speeds
and time estimates do not. Nothing thermal is modelled. See the **Limits**
tab; keep it accurate if the pipeline changes.
