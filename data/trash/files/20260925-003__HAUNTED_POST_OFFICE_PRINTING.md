# Haunted Post Office — printing notes

Building #1 of the Haunted Town series (`HAUNTED_TOWN.md`). It is a hollow
lantern with an open base, lit from inside by a battery LED tealight. It has
an octagonal corner turret under a tall witch-hat spire, which leans out
3.5 mm. 110.7 × 81.5 × 160.1 mm including the chimney, the turret and the
parcels.

**Print this:** `haunted_post_office.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | walls, plinth, turret walls, gables and battens, eave flare, step | slate teal `#50666B` |
| roof | roof slab, shingles, ridge cap, chimney, and the turret's spire with its eave and finial | slate `#2B2F38` |
| trim | window and door frames, muntins, door, corner boards, sign board, the parcels' string | cream `#EFE6D2` |
| accent | the parcels, the POST OFFICE letters, the brass mail slot | kraft `#D4A96A` |

The per-part `.stl` files are what the assembler consumes and what the gates
check. They are not the deliverable.

## No supports, and none of the settings below are optional

- **Supports OFF.** Verified: the gate's slicer reports **0 support moves
  and 0 overhang perimeters**.
- **Print it standing up, the way it is in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament | colour changes |
|---|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **13 h 56 m** | **~128 g** | 0 |
| **four colour, AMS** | not reliable here | ~136 g model **+ purge** | **1,285** |

The purge is the real cost of the colour version, the same as the bakery's:
- **255 g** of purge and wipe tower at PrusaSlicer's 140 mm³ per change;
- about **560 g** at the 350 mm³ Bambu default, in flush alone.

Bambu Studio sets its own flush for each colour pair, so slice it there for
the real number before pricing. The four-extruder time estimate overflowed
here, so no four-colour time is quoted. It is longer than the bakery
(11 h 52 m) mainly because of the spire.

A listing must say which version the buyer gets: printed in colour, or
single colour and hand-painted by Jessee.

## The tealight

Measured on the exported mesh: the largest clear circle about the room's
centre is **50.6 mm across at every height from the table to past 90 mm**.
The series rule is ≥ 46 mm across and ≥ 60 mm of headroom. Any common LED
tealight fits (36–38 mm across, 32–45 mm tall). The base is open, and the
house lifts off to reach the switch.

The turret glows too. A tall pointed arch (7 × 47 mm), cut through the
turret's wall where it faces into the room, lets the light in. It can't be
seen from outside.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 160.0 mm of 160.09 modelled (the finial tip);
  - 13.43 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - watertight, consistent winding;
  - **0 zero-area faces**;
  - every edge shared by exactly two faces.
- The roof is two pieces (the main roof and the spire), the trim is 24 and
  the accent is 12. Each piece was checked for real surface contact with
  the part it sits on, sampled by area. The spire shares 226 mm² with the
  turret wall, and the parcels' string shares 314 mm² with the parcels.
- **The parts are disjoint.** All six pairwise intersections render EMPTY.
- The union mesh (used only for the gate) carries 113 zero-area faces,
  every one at z = 84.2 along the eave weld, the same as the bakery. None
  of the four parts that ship has any.
- The 3MF round-trips through the slicer with all four extruders addressed.
- **OBC maker's mark:** engraved 0.8 mm deep under the step, the same mark
  as the bakery, with strokes ≥ 1.0 mm.
- **POST OFFICE letters:** size 4.8, a flush inlay. Eroding them by one
  bead (0.42 mm each side) loses no letter.

## Changes from the pitch, and why

- **The turret is octagonal, not round.** Every face is flat, so the
  bakery's proven window frames, muntins and clapboard carry over
  unchanged. On a round tower each would have needed new, unproven curved
  geometry.
- **The sign is mounted on the wall, not hung from a bracket.** A hanging
  board's bottom edge is a free overhang that no angle rescues. It still
  hangs crooked. It is two lines because one line at a readable size needs
  43 mm and the wall has 38.
- **The parcels stand on the ground by the wall.** There is no porch; a
  porch roof would need support.
- **The turret has windows on its front and right faces only.** On the
  diagonal faces, every window bar sits at 45° to the gate's measuring
  rays, which read each bar's corner as a sliver. The first build measured
  a 0.52 mm 1st-percentile wall from bars that are really 1.24 × 1.68 mm.
  The diagonal faces keep plain clapboard.
