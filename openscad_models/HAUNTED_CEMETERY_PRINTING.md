# Haunted Cemetery — printing notes

Scenery for the Haunted Town series (`HAUNTED_TOWN.md`). It is a graveyard
hill: a lumpy mound on an oval base, 104 × 76 mm and 63 mm tall to the tip of
the tree.

**On the hill:**
- **Seven headstones in six different shapes**, leaning every which way:
  - round-top **RIP**;
  - pointed gothic **BOO**;
  - snapped-off **BRB**, with a skeleton hand reaching out of the grave in
    front of it;
  - pedimented **NEXT** at the head of an open grave;
  - round-top **OOPS**;
  - a plain cross;
  - a plain obelisk.
- **A bare dead tree** on the crest, with a cawing crow on a sawn-off branch.
- **Three jack-o'-lanterns** with dark carved faces.
- **An open grave**, with a dirt pile beside it and a shovel stuck in the pile.

Built 2026-09-26. Scott chose the hill form, all four Halloween touches (the
jack-o'-lanterns, skeleton hand, dead tree and open grave) and short joke
epitaphs.

**It is not a lantern.** The hill is solid ground with no tealight inside.
The town's rule is a 46 mm circle under 50 mm of headroom, and that would
make a hill about 90 mm tall.

**Print this:** `haunted_cemetery.3mf`. It is one object with four parts,
already aligned.

| part | what it is | colour in the file |
|---|---|---|
| body | the hill, the grave mounds, the dirt pile, the pumpkins' stems | moss `#4A5140` |
| roof | the tree and crow, the epitaphs, the pumpkins' faces | slate `#2B2F38` |
| trim | the seven headstones, the skeleton hand | cream `#EFE6D2` |
| accent | the three pumpkins, the shovel | kraft `#D4A96A` |

The epitaphs and the pumpkins' faces are **flush inlays**: dark slate set
level into the cream stone and the kraft pumpkins, not raised and not cut in.
So on a single-colour print they do not show at all; Jessee would paint them.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- Print it flat on its base, as it sits in the file.
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament | colour changes |
|---|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **4 h 02 m** | **~35 g** | 0 |
| **four colour, AMS** | not reliable here | ~40 g model **+ purge** | **415** |

With PrusaSlicer's 140 mm³ flush, the four-colour wipe tower is **83 g**,
twice the cemetery itself. Slice it in Bambu Studio for the real flush figure
before pricing. A listing must say which version the buyer gets.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union:
  - watertight, one body;
  - 1st-percentile wall 1.24 mm, median 7.6 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height matches the model (63.0 of 63.06 mm);
  - 61.5 cm² of bed contact (78% of the footprint);
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - watertight;
  - **0 zero-area faces**;
  - every edge shared by exactly two faces.
- **The parts are disjoint.** All six pairwise intersections render EMPTY.
- Every piece touches the hill, sampled by area:
  - headstones, 164–436 mm² each;
  - the hand, 27 mm²;
  - the pumpkins, 106–137 mm²;
  - the shovel, 54 mm²;
  - the tree, 79 mm².
- **The epitaphs are printable.** For each word, every stroke survives a
  one-bead (0.42 mm) opening, and no two letters merge under a one-bead
  closing. Letter spacing is 1.12. Each stone is sized to fit its word.
- **OBC maker's mark:** engraved 0.8 mm deep in the underside, the same
  size-5 Montserrat Black mark as the buildings.

## What it took to print without supports

The first build needed 2,058 support moves. Each fix below was measured on
the gate's slicer; `.claude/skills/3d-print-design/SKILL.md` Technique 74 has
the detail.

- **The skeleton hand** was rebuilt so that the palm's foot is narrower than
  the forearm and every finger root sits inside the palm. Before, the
  fingers' square ends stuck out of the palm as little flat ledges.
- **The crow** stands wholly on the branch's cut top. Its underside (body
  and raised tail) was checked numerically at ≥ 55°. The beak is raised,
  a cawing crow, because a level beak would be a ledge.
- **The pumpkins** draw in at 57° below the middle to a small foot, which is
  sunk 0.8 below the lowest ground under it. One pumpkin was moved in from
  the rim, where it hung over the edge.
- **The cross's arms and the shovel's grip** have 58° gussets underneath.

## Honest weak points

- **The pumpkins' eyes also show from above.** They are cut straight in from
  the front, and near the top of a pumpkin that cut comes out through the
  top as well.
- **The shovel is mostly shaft.** Its blade is buried in the pile, so from
  straight in front it can read as a stick.
- **The hill is gentle.** It rises about 25 mm, so the stones stand at
  similar heights, and the crest mainly lifts the tree and the obelisk.
