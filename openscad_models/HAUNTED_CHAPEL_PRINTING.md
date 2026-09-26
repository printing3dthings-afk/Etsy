# Haunted Chapel — printing notes

Building #2 of the Haunted Town series (`HAUNTED_TOWN.md`). A stone chapel
with pointed lancet windows and a steep slate gable roof. Its gable walls rise
through the roof as coped parapets. A square bell tower stands on the
front-left corner; just above the roofline it has **cracked and tipped 7°
away from the nave**, carrying the belfry, spire and cross with it. Two
headstones lean against the plinth by the door.

Like the others, it is a hollow lantern with an open base, lit from inside by
a battery LED tealight. The tower is hollow and open to the nave, so light
also comes out of the belfry. It measures 70.2 × 83.6 × 162.0 mm, cross
included.

Built 2026-09-25/26 to Scott's variety plan: stone walls, pointed lancets and
a steep gable with a tipped tower. It shares none of these with the bakery,
the post office or the general store. Scott chose the corner-tower form from
four options.

**Print this:** `haunted_chapel.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | stone walls, tower, plinth, step, the ledge under the eaves | stone grey `#77716B` |
| roof | roof slab, slate courses, ridge cap, spire | slate `#2B2F38` |
| trim | gable coping, window frames and tracery, door frame, the tower's two bands, the headstones | cream `#EFE6D2` |
| accent | the door, the cross | kraft `#D4A96A` |

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.** The tipped tower and
  every underside are designed for this orientation only.
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament | colour changes |
|---|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **9 h 59 m** | **~86 g** | 0 |
| **four colour, AMS** | not reliable here | ~88 g model **+ purge** | **1,017** |

The four-colour slice changes colour 1,017 times, fewer than the bakery
(1,293) or the general store (1,317). The walls and the cream frames share
fewer layers here. With PrusaSlicer's 140 mm³ flush the wipe tower is
**212 g**, more than twice the chapel itself. Slice it in Bambu Studio for
the real flush figure before pricing, as with the others. A listing must say
which version the buyer gets.

## The tealight

Measured on the exported mesh:
- **46.8 mm clear across from the table up to 50 mm**;
- a 46 mm circle still fits up to **52.6 mm**. Above that, the 62° ceiling
  closes in.

The series rule is ≥ 46 mm across and ≥ 50 mm of headroom. The base is open,
so the chapel lifts off to switch the light.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union:
  - watertight, one body;
  - 1st-percentile wall 1.20 mm, median 2.92 mm, against the 1.2 mm floor.
    That is exactly at the floor, with no margin;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (162.0 mm);
  - 10.34 cm² of bed contact (17.6% of the footprint);
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - watertight;
  - **0 zero-area faces**;
  - every edge shared by exactly two faces.
- **The parts are disjoint.** All six pairwise intersections render EMPTY.
- Every trim and accent piece touches the part it sits on, sampled by area:
  - each nave window frame, about 195 mm²;
  - the big front window, 284 mm²;
  - the tower bands, 626 and 646 mm²;
  - the headstones, 57 and 50 mm²;
  - the door, 89 mm²;
  - **the cross, 28.6 mm²**. Its post is set 3.5 mm into a socket in the
    spire's solid tip; standing on the spire's cut top alone, it had 3 mm².
- The 3MF slices with all four parts and all four extruders addressed.
- **OBC maker's mark:** engraved 0.8 mm deep under the step, the same size-5
  Montserrat Black mark as the other buildings.

## Design notes: what it took to print without supports

The first build needed 44,654 support moves. Each fix below was measured on
the gate's slicer; `.claude/skills/3d-print-design/SKILL.md` Technique 73 has
the detail.

- **The eaves stand on a ledge.** A steep roof's eave hangs lower at its edge
  than where it meets the wall, so its first layers printed in mid-air. A
  52° ledge under each eave now carries it. That ledge also keeps the eaves
  short (2 mm), which is why the side windows sit low.
- **The coping's overhang is undercut.** Where the cream coping stands proud
  of the stone, its underside rises at 58° like every other raised detail
  here, and it stops before the rounded corners.
- **The tower's inner walls reach the ground.** Where the tower overlaps the
  nave, its wall used to start on the sloping ceiling and hang over the
  tower's hollow. Its two inner walls now run to the base, each with a tall
  pointed arch so light reaches the belfry. The corner between them is left
  open, to keep a 46 mm circle clear.
- **The crack only runs downward.** A zig-zag crack leaves a point of stone
  hanging above every trough. The crack runs down from the tip in steep
  jagged steps.
- **The tower's bands meet in mitres at the corners.** Run past each other,
  they hung in the air.

## Honest weak points

- **The tip is subtle.** It is 7°, about 8 mm of lean at the spire. The
  tower's stone courses, openings and bands were set for 7° so they print;
  much more would need them reworked.
- **The stone reads partly as stacked courses.** It has irregular block
  lengths and quoins at the corners. The printable V-shaped courses still
  give it a banded look from a distance.
- **The walls sit exactly at the 1.2 mm wall floor** at the 1st percentile.
  That passes, with no margin.
