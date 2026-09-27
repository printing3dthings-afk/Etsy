# Handoff: the print checks now slice with Bambu Studio (2026-09-27)

Scott asked for "a better slicer program than what you are using". The print
checks (`tools/virtual_printer.py`, `tools/print_fidelity.py`,
`tools/as_printed.py`) sliced with PrusaSlicer 2.7.2. They now slice with
**Bambu Studio 02.08.02.61**, the program Scott prints from, with Bambu's own
stock P1S presets. PrusaSlicer stays as the fallback.

## Status: done, and one thing to re-do every session

The container is ephemeral, so each new session installs it again (~1.4 GB, a
few minutes):

    tools/install_bambu_studio.sh

Without it the checks quietly fall back to PrusaSlicer, and every report says
which slicer it used (`sliced by bambu` / `sliced by prusa`).
`VIRTUAL_PRINTER_SLICER=prusa|bambu` pins one.

## Why the earlier plan did not work as written

The earlier handoff blamed the domain allowlist. That was not the cause: the
403 from github.com said "GitHub access to this repository is not enabled for
this session". The session proxy serves `git clone` of public repos, not
release downloads, so the Bambu AppImage is still unreachable. Bambu Studio
comes from **Flathub** instead (`com.bambulab.BambuStudio`), run directly
under bubblewrap because `flatpak run` needs a system D-Bus the container
lacks. Details in `tools/bambu_slicer.py`'s docstring.

## What was found on the way (all fixed, all in tests/test_bambu_slicer.py)

Every one of these returned "Success" and looked like a normal slice:

- The CLI does not follow a preset's `inherits`: the stock P1S sliced on a
  200 x 200 bed. Presets are flattened before slicing.
- The P1S's real start/end/toolchange G-code lives in `include`d template
  files; without them it used a generic start.
- A filament preset with no colour left filament 2's parts out of the G-code.
- **Bambu Studio only builds parts from 3MF `<components>`.** Our assembler
  wrote one mesh with triangle ranges (what PrusaSlicer reads), so Bambu
  loaded the chapel as ONE part on one filament. `assemble_3mf` now has
  `--layout bambu`; the fidelity check uses it automatically.
- The P1S profile has `extruder_offset = 0x2`: G-code Y is 2 mm off the plate.
- Arc fitting is on in the stock process; the readers only follow G1, so it
  is turned off for these slices (same path, straight segments).
- Bambu's `T255` / `T1000` control codes and its indented first `T<n>` were
  misread as filament slots.
- `virtual_printer.analyse()` read relative E as absolute (also wrong for
  PrusaSlicer's multi-filament slices).

## Results

- Calibration block (`tests/test_print_fidelity.py`), re-measured and drawn:
  Bambu stock uses **classic** walls, not Arachne, so ribs up to 0.2 mm get
  no bead at all (PrusaSlicer kept 0.15 and 0.2), and a 0.5 mm dot prints
  (PrusaSlicer dropped it). The test now holds each slicer to its own answers.
- Chapel, four colours: **0 flags on Bambu Studio, 0 on PrusaSlicer** -- both
  agree with the print Scott made. Bambu leaves more unflagged sub-bead
  slivers (96 mm3 against 4 mm3: bands ~0.3 mm wide, 3 layers tall, where
  slopes change), consistent with classic walls. PrusaSlicer's first attempt
  at this plate was refused outright (17,643 junk coordinates on three slices
  running); its retry sliced clean.
- Sauce tray (`virtual_printer.py`): clean on both.

## Needs Scott

1. **Does `haunted_chapel.3mf` open in Bambu Studio as four parts, or as one
   object you had to colour yourself?** Bambu's importer (source and CLI)
   says one part. If so, every shipped multi-colour 3MF should be re-written
   with `--layout bambu`. Not done yet: those are product files.
2. Export your Bambu Studio presets (File > Export > Export Preset Bundle) so
   the checks slice with your settings, not Bambu's defaults. In particular:
   is your wall generator Classic (stock) or Arachne? It changes which fine
   details survive.
3. What did Bambu Studio say for the chapel's print time and filament? The
   stock slice here says 31.3 h and 441 g across four filaments; your numbers
   would show how far stock is from your setup.

## Still open, separate from this

- General store timber props: fragility HIGH (slenderness 31). Proposed a
  mid-height brace to the false front plus 3.2 mm props (~12). Awaiting Scott.
- Christmas village: Scott picks one of five styles
  (`openscad_models/christmas_village/concepts/images/styles_lineup.png`).
- Whether to glaze the manor's windows (16 watch-level bars).
