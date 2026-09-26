# Haunted Cemetery — printing notes

Scenery for the Haunted Town series (`HAUNTED_TOWN.md`). It is a graveyard
hill: a lumpy mound on an oval base, 104 × 76 mm and 66.6 mm tall to the tip
of the tree.

Built 2026-09-26. Scott chose the hill form, all four Halloween touches (the
jack-o'-lanterns, skeleton hand, dead tree and open grave) and short joke
epitaphs. The same day he asked for better detail and picked all four
options: carved headstones, textured ground, sculpted props and a broken
iron fence. This file describes the detailed version.

**On the hill:**
- **Seven headstones in six different shapes**, leaning every which way,
  each on a two-step base with a bevelled edge:
  - round-top **RIP**, with a carved skull;
  - pointed gothic **BOO**, with a carved bat and a crack, over a kerbed
    grave;
  - snapped-off **BRB**, with a crack, and a skeleton hand reaching out of
    the grave in front of it;
  - pedimented **NEXT**, with a carved hourglass, at the head of an open
    grave;
  - round-top **OOPS**, with a crack;
  - a plain cross;
  - a plain obelisk.
- **A broken wrought-iron fence** across the front:
  - pickets with arrowhead finials;
  - one panel fallen out and its post snapped off;
  - two panels leaning;
  - the gate swung open and sagging.
- **A bare dead tree** on the crest. Its bark twists round the trunk, with a
  root flare and roots. A crow stands on a sawn-off branch.
- **Three jack-o'-lanterns** with dark carved faces and curling stems.
- **An open grave**, with a dirt pile beside it and a shovel stuck in it.
- **Scattered on the ground:**
  - two bones and a skull;
  - four stepping stones leading in from the gate;
  - five pebbles;
  - eleven tufts of grass.

**It is not a lantern.** The hill is solid ground with no tealight inside.
The town's rule is a 46 mm circle under 50 mm of headroom, and that would
make a hill about 90 mm tall.

**Print this:** `haunted_cemetery.3mf`. It is one object with four parts,
already aligned.

| part | what it is | colour in the file |
|---|---|---|
| body | the hill, the grave mounds, the dirt pile, the grass, the pumpkins' stems | moss `#4A5140` |
| roof | the tree and crow, the fence and gate, the stepping stones and pebbles, the epitaphs, motifs and cracks, the pumpkins' faces, the skull's eyes | slate `#2B2F38` |
| trim | the seven headstones and their bases, BOO's kerb, the skeleton hand, the bones, the skull | cream `#EFE6D2` |
| accent | the three pumpkins, the shovel | kraft `#D4A96A` |

The epitaphs, motifs, cracks and the pumpkins' faces are **flush inlays**:
dark slate set level into the cream stone and the kraft pumpkins, not raised
and not cut in. So on a single-colour print they do not show at all; Jessee
would paint them.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- Print it flat on its base, as it sits in the file.
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament | colour changes |
|---|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **4 h 48 m** | **~39 g** | 0 |
| **four colour, AMS** | not reliable here | ~39 g model **+ purge** | **475** |

The detail pass added about 46 minutes over the first version (4 h 02 m).
The slicer's single-colour total is 31.5 cm³, about 39 g of PLA. With
PrusaSlicer's 140 mm³ flush, the four-colour print uses about 143 g in all,
so the wipe tower is **~104 g**, more than twice the cemetery itself. Slice it in
Bambu Studio for the real flush figure before pricing. A listing must say
which version the buyer gets.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union:
  - watertight, one body;
  - 1st-percentile wall 1.20 mm, median 5.45 mm, against the 1.2 mm
    floor. That is exactly at the floor: 47 of 6,567 wall samples
    are under 1.2 mm, where the rule allows 1%;
  - 0 supports, 0 overhang perimeters;
  - printed height matches the model (66.6 mm);
  - 61.5 cm² of bed contact (78% of the footprint);
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - watertight;
  - **0 zero-area faces**;
  - every edge shared by exactly two faces.
- **The parts are disjoint.** All six pairwise intersections render EMPTY.
- **Every piece touches the model**, sampled by area. The smallest shares
  are the skeleton hand (13% of its surface, about 28 mm²) and the shovel
  (15%, 32 mm²).
- **The inlays are printable**, measured on a 0.02 mm raster of each stone's
  whole inlay:
  - every slate stroke keeps ≥ 98% of its area under a one-bead (0.42 mm)
    opening;
  - no two pieces merge under a one-bead closing. The closest pair is 0.64 mm
    apart.
  - NEXT has its own letter spacing (1.3) and a wider tablet: at the common
    1.12, its X and T stood 0.26 mm apart and would have fused.
- **OBC maker's mark:** engraved 0.8 mm deep in the underside, the same
  size-5 Montserrat Black mark as the buildings.

## What the detail pass took

Each fix below was measured on the gate's slicer or wall check;
`.claude/skills/3d-print-design/SKILL.md` Technique 75 has the detail.

- **The fence prints like a row of little pointed windows.** Its rails have
  no flat undersides: each rail's underside is a row of 58° gables between
  the pickets. The sagging gate's gables are 64°, so they stay steep enough
  after the sag.
- **The tree's limbs are square in section** and start on the trunk's axis.
  Round limbs failed the wall check; limbs started off-axis poked flat
  discs out between the bark's lobes and drew supports.
- **The branch the crow stands on has a 3.8 mm square top.** At 3.0 mm, the
  crow's belly overhung its corners and drew 360 support lines.
- **The finials are blunt arrowheads.** Sharp spear points were sub-bead
  walls in their last millimetre.

## Honest weak points

- **The tree is blocky.** Square limbs with flat-cut ends read as a
  stylised, low-poly tree, not a gnarled one. That is what it took to pass
  the wall check at this size.
- **The crow is small and reads as a dark lump** from most angles. It is
  about 7 mm long. A larger, rounder crow drew supports in every version
  tried.
- **The shovel can read as a paddle.** Its blade is mostly in the dirt pile,
  and the grip's undersides are 58° wedges, so the top looks flared.
- **The walls sit exactly at the 1.2 mm floor** at the 1st percentile. That
  passes, with little margin.
- **Some pebbles are half-buried** where the hill is steep. Only their
  downhill side shows.
