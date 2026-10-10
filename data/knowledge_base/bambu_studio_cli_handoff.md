# Handoff: switch the print checks to Bambu Studio's slicer (2026-09-27)

Scott asked for "a better slicer program than what you are using". The print
checks (`tools/virtual_printer.py`, `tools/print_fidelity.py`,
`tools/as_printed.py`) slice with PrusaSlicer 2.7.2. Its Arachne walls are
close to Bambu Studio's, but not the same program Scott prints from.

## Status

Scott added `github.com` and `objects.githubusercontent.com` to the
environment's allowed domains on 2026-09-27. The session that asked still got
403 from github.com: network policy is fixed when a container starts, so the
change takes effect in the **next** session.

## What the next session should do

1. Check access: `curl -sS -o /dev/null -w "%{http_code}\n"
   https://api.github.com/repos/bambulab/BambuStudio/releases/latest`
   (200 = go). If still 403, tell Scott and stop.
2. Install the Bambu Studio Linux AppImage (or OrcaSlicer, same engine, if
   Bambu's build will not run headless), extract it
   (`--appimage-extract`), and run its CLI headless under `xvfb-run` the way
   `tools/openscad_render.py` already does for OpenSCAD.
3. Validate on the chapel Scott printed (`openscad_models/haunted_town/`
   chapel parts): slice both ways and compare bead widths and layer outlines
   against the PrusaSlicer slice. The chapel is the calibration print, and
   its fidelity result is 0 flags on PrusaSlicer.
4. Add it to `virtual_printer.slice_model` as the preferred slicer and keep
   PrusaSlicer as the fallback. Keep the junk-coordinate retry and refusal
   (`off_bed_moves`) for both.
5. Re-run `tests/run_all.py`; the calibration tests in
   `tests/test_print_fidelity.py` (0.1 mm rib dropped, 0.15 prints; 0.5 mm
   dot dropped, 1.0 prints) must be re-measured on the new slicer, not
   assumed.
6. Ask Scott to export his Bambu Studio printer, filament and process
   profiles (File > Export > Export Preset Bundle) so the checks slice with
   his exact settings instead of defaults.

## Still open, separate from this

- General store timber props: fragility HIGH (slenderness 31). Proposed a
  mid-height brace to the false front plus 3.2 mm props (~12). Awaiting Scott.
- Christmas village: Scott picks one of five styles
  (`openscad_models/christmas_village/concepts/images/styles_lineup.png`).
- Whether to glaze the manor's windows (16 watch-level bars).
