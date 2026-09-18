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
