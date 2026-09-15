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
