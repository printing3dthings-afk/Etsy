# Haunted Chapel — printing notes

Building #2 of the Haunted Town series (`HAUNTED_TOWN.md`). A stone chapel
with pointed lancet windows and a steep slate gable roof. Its gable walls rise
through the roof as coped parapets. A square bell tower stands on the
front-left corner; just above the roofline it has **cracked and tipped 7°
away from the nave**, carrying the belfry, spire and cross with it. Two
headstones lean against the plinth by the door.

Like the others, it is a hollow lantern with an open base, lit from inside by
a battery LED tealight. The tower is hollow and open to the nave, so light
also comes out of the belfry. It measures 70.2 × 83.6 × 163.0 mm, cross
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
| trim | gable coping, window frames, tracery and panes, door frame, the tower's two bands, the headstones | cream `#EFE6D2` |

**Every framed window is glazed** (added 2026-09-27). A 1.48 mm pane fills the
back of each opening, set into the wall all round, and the window's bars stand
on it. The tealight glows through the panes, like frosted glass. The tower's
small slit windows, the belfry and the door stay open.
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
| **single colour** (e.g. for Jessee to paint) | **9 h 46 m** | **~88 g** | 0 |
| **four colour, AMS** | not reliable here | ~90 g model **+ purge** | **1,016** |

The four-colour slice changes colour 1,016 times, fewer than the bakery
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
  - 1st-percentile wall 1.48 mm, median 2.92 mm, against the 1.2 mm floor
    (1.20 before the panes, which took the thinnest spots off the floor);
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (163.0 mm);
  - 10.42 cm² of bed contact (17.8% of the footprint);
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - watertight;
  - **0 zero-area faces**;
  - every edge shared by exactly two faces.
- **The parts are disjoint.** All six pairwise intersections render EMPTY.
- Every trim and accent piece touches the part it sits on, sampled by area:
  - each nave window's frame and pane, 256–271 mm²;
  - the big front window, 367 mm²;
  - the tower bands, 626 and 646 mm²;
  - the headstones, 57 and 50 mm²;
  - the door, 89 mm²;
  - **the cross, 39.8 mm²**. Its 2.4 mm post is set 3.5 mm into a socket in
    the spire's solid tip; standing on the spire's cut top alone, it had 3 mm².
- The 3MF slices with all four parts and all four extruders addressed.
- **OBC maker's mark:** engraved 0.8 mm deep under the step, the same
  Montserrat Black mark as the other buildings: size 4.6, letter spacing
  1.16, 16.2 mm wide. It reads OBC when you turn the chapel over with the
  front toward you; checked on the sliced first layer.

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
- **The cross still has braced arms.** It is thicker now and prints
  cleanly, but to print without supports its arms keep 66° undersides, so
  from close up it reads as a cross on brackets rather than a crisp one.
- **The panes block the view inside.** Every framed window now glows
  rather than showing the room; the tower's slit windows and belfry are the
  only open ones.

## What the first print showed (2026-09-27)

Scott printed the chapel in white and photographed it. Each fix below is in
this file's current version.

- **The tallest windows lost their tracery.** The front window's centre bar
  and Y, and the back gable's centre bar, were gone: each printed as a lone
  post about 1.7 × 1.2 mm standing free for 10–20 mm, and snapped. The side
  windows' shorter bars survived. **Every framed window now has a pane.**
- **The cross printed as a lump.** It is now a 2.4 mm post with arms 2.0 mm
  thick at the tips, and 1 mm taller.
- **The OBC mark read backwards** ("ƆBO") and its letters ran together: the
  plastic between them was 0.39–0.46 mm, under one extrusion. It is now the
  right way round, with 1.1–1.3 mm between letters. The same fix went into
  every Haunted Town building.
- **Not the model:** stringing across the openings (dry the PLA: 45 °C for
  6–8 h), a line across the roof slope near the front gable's top, and a
  small split in the bottom rim where the tower meets the nave. A mark on the
  right headstone is a scratch or a stuck string: the headstones are plain.

