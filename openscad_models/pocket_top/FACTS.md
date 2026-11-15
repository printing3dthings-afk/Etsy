# Pocket Top: the UFO, FACTS (2026-11-15)

Scott picked form 1 of five (2026-11-15): a UFO saucer with a little dome and a kawaii face.
It's built on the snap he tested and liked best: pair 2, reach 0.45. The coupon's FACTS
follow below, unchanged.

Status: **designed and checked, not printed.** Nothing about it has been measured on a print:
not the fit, not the spin. Not for children under 3: small parts.

## What it is
- **Two parts.** The brief allows three; the dome and the stem print as one, so there's one
  joint, the tested one.
  - **Saucer** (`parts/ufo_saucer.stl`): printed flat, top face up. 34 mm across, 3.4 thick
    (the tested hub's thickness), with nine raised lights round the rim and a 45° chamfer on
    its top edge. The tested hub sits in the middle unchanged: hex hole, three spring beams,
    nubs.
  - **Stem** (`parts/ufo_stem.stl`): printed upside down, the dome's flat top on the bed.
    The dome is 12.9 across and 7.0 tall; its flat top (6.4 across) is the knob you twirl.
    Then the tested hex and groove, and a cone to a 1 mm round tip.
- **The face:** two droplet eyes and a small v mouth, engraved 0.5 deep on the dome's front.
  Each shape ends in a point at the bottom (in use), because that edge prints as a ceiling;
  rounder shapes made the slicer add support under them.
- **Snap together:** push the stem's hex into the face of the saucer that was up on the
  printer, the same way round as the coupon.

## The brief's budget (Bambu Studio's own slice, PLA Matte, 0.20 Standard, Bambu's settings)
| print | time | filament |
|---|---|---|
| **one plate, one colour (the product)** | **9 min 29 s** | **3.25 g** |
| saucer alone | 6 min 1 s | 2.60 g |
| stem alone | 5 min 8 s | 0.74 g |

- Two colours means two plates: about 11 min 9 s. That is over the brief's 10 minutes, so
  one colour is the default and two-tone is an option for Scott to call.
- **Where the budget bit (FACTS for Benson):**
  - A 37 mm saucer with a raised ring of portholes sliced at 13 min and 5.1 g.
  - The ring and its holes cost 1 min 50 s. Nine studs cost 14 s.
  - Each 0.5 mm of saucer radius costs about 7 s.
  - Sunken panels and open windows between the beams made it *slower*, not faster: every
    new edge is more wall to print.
- The slice files: `ufo_top.gcode.3mf` (the plate), `checks/ufo_saucer.gcode.3mf`,
  `checks/ufo_stem.gcode.3mf`; numbers in `checks/slice_*.json`.

## Checks (all on the exported parts)
- **Fit** (`check_ufo.py` -> `checks/fit_ufo.txt`): PASS.
  - Seated, the saucer's body clears the stem, and the nubs press the groove's floor by the
    preload only.
  - Pushed further, only the boss under the dome meets the saucer, out to r 4.40. The beams
    start at 4.75, so nothing presses on them as they snap.
  - It turns about 6° free, then the hex drives. Pulled 1 mm, it meets the nubs.
  - On the way in, the tip and hex bend each nub out by 0.45, its reach.
- **Balance:** the centre of mass is 0.004 mm off the spin axis, 8.7 mm above the tip.
  - It leans 20.7° before the saucer's rim touches the table.
- **Product gate** (`checks/gate_ufo_*.txt`): both PASS, 0 support moves.
  - The stem's engraved face is declared detail, a band over the dome's middle. On the
    dome's slope its recess edges are corner clips, not walls.
  - The same stem without its face has no span under 1.2 mm anywhere (measured 2026-11-15),
    so the band hides nothing else.
- **print_fidelity** (`checks/fidelity_ufo.txt`): 0 flags on both parts. The face and the
  lights print as drawn.
- **Fragility** (`checks/fragility_ufo.txt`): 0 high.
  - The saucer's 3 "watch" are the spring beams, which bend by design, as on the coupon.
- **Small parts** (`checks/small_parts_ufo.txt`, 16 CFR 1501.4 cylinder):
  - the saucer never fits (by 1.2 mm at best: borderline by the tool's own caution);
  - **the stem is a small part.**
  - "Not for children under 3: small parts" goes on the page and in the guide.

## Spin: an estimate, not a measurement (`checks/spin_estimate.txt`)
- **The model:**
  - air drag on a 34 mm disc;
  - friction at the 1 mm tip;
  - the spin below which a top can't stay up: about 9 turns a second for this one.
- **Result:** from a firm finger twist (assumed 15 to 30 turns a second, not measured), about
  **14 to 59 s**.
- **The spread:** it comes mostly from the launch speed and from how much extra drag the dome,
  lights and slots add.
- **What limits it:** air drag for most of the spin; tip friction near the end. The mass is
  set by the budget, and only 0.74 g of it is in the stem.
- **The brief's 30 s:** reachable from a firm twist in this model.
  - It is a target, not a claim. "Ours spun N seconds" waits for Scott's timed spin of a print.

## Images (`images/`, design-review renders, not photos)
- `ufo_front.png`, `ufo_three_quarter.png`, `ufo_top.png`: assembled, one colour.
- `ufo_exploded.png`: the stem lifted off the saucer.
- `ufo_plate.png`: the two parts as they lie on the plate.
- `ufo_two_colour.png`: the two-plate option.
- `ufo_as_printed.png`: rendered from the toolpath of the checks' slice of the plate.

## Rebuild
`make_ufo.sh` (exports, slices, gates), then `check_ufo.py`, `make_ufo_images.py` and
`make_ufo_guide.py`.

---

# Pocket Top: snap test print, FACTS (2026-11-14)

Status: **G1 candidate (coupon only).** The top's form is not chosen yet: Scott picks it from
the approaches after this coupon passes. Nothing here is a product claim.

## What's on the plate (`pocket_top_snap_test.3mf`)
- 3 hubs, printed flat, 31 mm across, 3.4 mm thick. The stem goes into the face that was up
  on the printer (into the other, the groove misses the nubs). Each has a hex hole and three spring
  beams round it, with a nub on each beam.
- 3 stems, printed upright on a 10 mm grip, 5 mm across the hex's flats, 10.4 mm tall.
- The pairs differ only in how far the nubs reach into the stem's groove:

| mark | hub | stem | reach | strain per snap | push on | pull off | engagement |
|---|---|---|---|---|---|---|---|
| 1 | 1 notch | 1 flat | 0.35 mm | 0.47 % | 7.8 N | 4.1 N | 2.5 x RSS (under the 3x rule: the low end of the test) |
| 2 | 2 notches | 2 flats | 0.45 mm (design) | 0.61 % | 10.0 N | 5.3 N | 3.2 x RSS |
| 3 | 3 notches | 3 flats | 0.55 mm | 0.74 % | 12.2 N | 6.4 N | 3.9 x RSS |

All calculated (`snap_budget.py`, `checks/snap_budget.txt`), not measured. The strain limit
used is printed PLA's repeated-flexing value, 0.8 % (handbook section 3, Bayer/Covestro):
the brief asks for 20 snaps.

## Print
- Bambu Studio, P1S 0.4, PLA Matte, 0.20 mm Standard: **31 min 17 s, 7.70 g, no supports**
  (`checks/snap_coupon.gcode.3mf`). Over the handbook's 30 min for a coupon by 77 s: the
  three hubs are most of it, and their thickness sets the beams' stiffness.
- Every part flat on the bed. Nothing that flexes is printed upright: the beams bend in the
  print plane, along the layers (the Gear Heart's clip snapped bending across them).

## Clearances and their sources
- Hex hole 0.15 a side over the stem: handbook section 1, "a hole drawn in XY prints small",
  0.15 (`mechanism_budget.PROCESS["hole_vertical"]`).
- Gaps round each beam 0.8: over the handbook's 0.30 smallest reliable open gap, and wide
  enough for a 0.4 root fillet.
- Nub preload into the groove 0.05: held strain 0.07 %, under the handbook's 0.5 % for
  anything held bent (PLA creeps).
- **The Fit Test Plate results are not in yet,** so none of these are Scott's measured
  values. They are the handbook's conservative ones.

## Checks run (all on the exported parts)
- Fit (`check_snap.py` -> `checks/fit_snap.txt`): PASS for all three. Seated, only the nubs
  touch, by their preload. The hex drives after about 6.6 deg of free turn. A 1 mm pull
  hits the nubs, and the grip's shoulder stops the push. On the way in, the hex bends each
  nub out by exactly its reach.
- Product gate: hubs PASS (min wall 1.30); each stem PASS (min wall 2.40).
  - The stems are gated one at a time. On one mesh the gate's PrusaSlicer propped stem 1's
    side; alone, each draws 0 support moves.
  - Bambu Studio's slice of the whole plate draws 0 support lines.
- Print fidelity (`checks/fidelity.txt`): 0 flags on all four files.
  - Stem 2 reads 5.5 mm³ "dropped" on its front face and 4.7 mm³ "filled" on its back, the
    full height, 0.2 deep: the slice offset by about 0.2 in y, not missing geometry.
- Fragility (`checks/fragility.txt`): 0 high. The 9 "watch" are the spring beams,
  slenderness 4.1, which are meant to flex.

## Small parts: "Not for children under 3: small parts"
- The gauge: the small-parts cylinder of **16 CFR 1501.4, Figure 1**: 1.25 in (31.7 mm)
  inside diameter, its floor slanting from 1.00 in (25.4 mm) to 2.25 in (57.1 mm) deep.
  - Read from the figure itself (the Cornell LII reproduction of the CFR,
    law.cornell.edu/cfr/text/16/1501.4).
  - The test, 1501.4(b)(1): "Place the article, without compressing it, into the cylinder.
    If the article fits entirely within the cylinder, in any orientation, it fails."
    Detached components are tested the same way.
  - The rule covers articles for children under 3 (1501.2(a)).
- Checked with `tools/small_parts.py`, a geometric search, not a certification
  (`checks/small_parts.txt`):
  - **every stem is a small part** (fits with its top 40 mm below the rim);
  - **the coupon hubs are small parts too** (31 mm across).
- **For the top itself:** a snap-together top comes apart, so its stem will always be a
  small part. The page and FACTS need "Not for children under 3: small parts" whatever the
  form. The body should be over 32 mm across so that at least it doesn't fit.
- A part too big for the cylinder must also survive the use-and-abuse tests of 16 CFR
  1500.51-52 before it counts (1501.4(b)(2)). Nothing here has been through them.

## Material: matte PLA (the brief's trap)
- The numbers above are for PLA in general. Matte PLA is more brittle, and no figure for it
  is in the handbook.
- That is what the coupon is for: 20 snaps each, in matte PLA.
- If no pair survives 20 snaps, that is a named exception for Scott's call (PETG or PLA+ for
  the hub only). The material is not switched quietly.

## Not tested
- Everything above is calculated or geometric. Nothing has been printed or snapped yet.
- Spin time: there is no top yet, so there is no spin estimate.
