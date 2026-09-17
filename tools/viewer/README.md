# Virtual P1S Chamber — print-playback viewer

Replays a real sliced G-code file move by move, in a browser. The page is
static; everything it draws came out of the slicer.

## Files

| File | What it is |
|---|---|
| `virtual_p1s.html` | The page — layout, palette, reference panels. Publish this as the Artifact. |
| `app.js` | Scene, bead geometry, playback, UI. Served next to the page. |
| `jobs/index.js` + `jobs/<id>.js` | Generated payloads, one script per plate. Not committed — 10MB of derived data. |

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
