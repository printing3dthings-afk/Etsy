# Christmas glow lanterns

Started 2026-10-13. Scott asked what else, besides the villages, could be
printed for Christmas; from six ideas he asked to see glowing scene lanterns,
and from five lantern forms (`concepts/lantern_forms.jpg`) picked three:

| folder | lantern | prints as |
|---|---|---|
| `hex_lantern/` | Hex carriage lantern: six glass panels, a snowy pointed roof, a red bow, a hanging ring | one piece, upright |
| `drum_lantern/` | Panorama drum: one unbroken Christmas Eve wrapped all the way round | one piece, upright |
| `gift_box_lantern/` | Gift box: four glass sides, a lid tied with a red ribbon and bow | two pieces, box and lid, side by side |

Each holds a battery LED tealight. The hex and drum are open underneath and
lift off over the light; the gift box has a floor and its lid lifts off.

## How the scenes glow

The glass is 1.3 mm of plastic, thin enough to glow. Every scene stands 1.6
mm out of it, so lit from inside the scene is 2.9 mm thick and shows dark on
the glow: the way a lithophane works, and the way the village's toy windows
work. It works printed all in white; in colour, the scenes print in the
frame's colour on white glass.

## Shared files

- `lantern_scenes.scad`: every scene, drawn at print size for a 0.4 mm
  nozzle. No stroke under 1.3 mm (`SW`), no gap under 0.8 mm; `glow_out`
  steps the drawing out of the glass so its undersides print without
  support, after `glow_clean` takes off whatever is too fine to print.
- `lantern_mesh.py`: proves the colour parts closed and disjoint, welds them
  into one body for the gate (manifold3d), and wraps the drum's flat
  panorama round its glass.
- `check_lantern.py`: the full check set for one lantern (gate, 3MF,
  fidelity, fragility, colour and night renders, as-printed, viewer).
- each lantern's `build.sh` exports its parts; `build.sh union` makes the
  gate's mesh.

The `*_night*.png` images are renders of the model printed in white and lit
by a point light where the tealight's flame goes. They are not photos: how
dark the scenes read on a real print depends on the filament and the light.
