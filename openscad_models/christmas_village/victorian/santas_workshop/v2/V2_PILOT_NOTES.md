# Santa's Workshop v2: the detail-print pilot (2026-10-24)

Scott, 2026-10-23: pilot a new fine-detail method on this one building, deliver
before/after renders and the 0.4 mm slice check, then **stop and wait for his
decision**. The listed file, `../victorian_santas_workshop.scad`, and its
meshes and 3MF are untouched. If Scott approves, this becomes a v2 he can
choose to swap in. Nothing here is listed.

The method is `../../../../detail_calibration/DETAIL_STANDARD.md`.

**Decision, 2026-10-30: Scott chose v2.** `victorian_santas_workshop_v2.3mf`
is now the version to print. The v1 files one folder up stay where they are,
unchanged. The method is the standard for new designs from here on.

## What v2 adds

| detail | where | colour | sized by |
|---|---|---|---|
| joints between slates, 0.5 wide, staggered | all four turret cones | slate | upright grooves hold to 0.01 mm in the slice |
| joints between slates, 3.4 apart, staggered | the three roof slopes, none within 3 mm of a turret or stack | slate | same |
| a corbel table: 20 brackets 1.8 wide, 0.8 proud, climbing at 35° | under each turret cone | brick | 4 beads wide; nothing past 37° |
| a cornice on dentils | under the gatehouse battlements, front and sides | white | heights on the 0.2 grid; 36° and 35° undersides |
| planked leaves, grooves with 60° pointed tops | the gatehouse doors | slate (straps white) | upright grooves; pointed tops have no ceiling |
| voussoir joints, every 15° | the big toy windows' arches | white | radial, so mostly upright |

## Checks: slices of the model, not a print

- **Supports:** the union, sliced on the gate's slicer with supports allowed.
  Every support v2's details caused was found and removed (list below). The
  final slice still shows **1,436 support moves and 1 overhang perimeter**,
  all at one spot inside the hall by the front-left turret (model −46.8,
  −34.1, z 83.6). That is not v2's: the **listed file, put through the same
  fast engine, gives the identical 1,436 and 1 at the identical spot**, and
  its CGAL mesh slices to 0 and 0. At that spot both fast-engine meshes carry
  8 zero-area triangles and no real downward face, and the CGAL mesh has
  neither. The one v2 slice taken before the slate-joint clearance was
  added came out at 0 and 0. The CGAL export confirms this either way. Until
  then, this is the claim, not a measurement of the shipping mesh.
- **Print fidelity at 0.2 mm layers on the 0.4 mm nozzle**, four colours:
  **8 flags, every one of which the listed file also has.** That is two rose-window
  glass slivers, one sign letter's top layer, four single brick layers at
  the valleys and one wreath leaf tip. The listed file has 11. None of v2's
  additions is flagged: dropped 55.2 mm³ of 428,773 mm³ modelled.
- **Five things the checks caught and that were fixed before this was
  shown**, each recorded where it was fixed:
  - Cornice and dentils at exactly 45° put 29,332 support moves under them.
  - Plank grooves clipped to the arch had a 22° top: 1,290 support moves.
  - Planks stopped under the hinge straps made each strap a bridge: 8 overhang perimeters.
  - A plank groove left a 0.55 strip of strap that the slice dropped: 4 flags.
  - A slate joint beside a turret cut off a 0.49 shard: 1 flag.

## What is NOT done yet, deliberately

- **Shipping meshes.** These parts come from OpenSCAD 2026's fast manifold
  engine, which renders a part in under a minute but writes zero-area slivers
  into its STL that `mesh_gate` reads as open. The meshes and 3MF that would
  ship come from `./build.sh cgal` (hours per part), then `product_gate`,
  `fragility` and the 3MF. All of that waits for Scott's decision.
- **The as-printed renders and the viewer entry.** Same.
- **A real print of the detail coupon**
  (`../../../../detail_calibration/detail_coupon.stl`). Every number here is
  toolpath, not plastic.

## Files

- `victorian_santas_workshop_v2.scad`: the model. Every addition is marked `v2:`.
- `build.sh`: fast build by default; `./build.sh cgal` for shipping.
- `run_checks.sh`: rebuild, then the fidelity slice, then `render_compare.sh`.
- `images/before_after_v1_v2.jpg`: the comparison sheet.
- `images/v1_colour_*`, `images/v2_colour_*`: the full views behind it.
- `logs/fidelity.txt`, `logs/fidelity.json`, `logs/supports.json`: the check results.
