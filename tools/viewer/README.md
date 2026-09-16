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
the bottom-right bezel, feet, rear spool holder.

**Deliberately unbranded.** The proportions are the machine's; the logo is not
mine to reproduce, so there isn't one.

**The door is a real hinge**, not a fade: a Group pivoted on one vertical edge
and rotated ~110 degrees. Which edge is a **profile setting** (`hingeLeft`),
not a baked assumption -- no primary source I could reach stated the P1S hinge
side, so it is exposed rather than guessed. Flip it in `PRINTERS` if it is
backwards.

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

Everything is generated -- PEI speckle, shell gradient, contact shadow, nozzle
glow are all canvas textures, because the artifact CSP blocks image hosts.
The enclosure is deliberately unbranded.

## Performance

3.07M triangles for the heaviest plate in **30 draw calls** -- one mesh, one
`setDrawRange`, no per-frame rebuild.

`--simplify` (default 0.02mm) drops points whose removal shifts the path less
than a twentieth of a bead: 8-30% of points on real plates, with time, mass and
speed data bit-identical afterwards. It will not merge across a speed change.

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
