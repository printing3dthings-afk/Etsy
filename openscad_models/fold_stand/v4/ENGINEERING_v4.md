# Fold Stand v4: the engineering

2026-11-10. This follows `data/knowledge_base/mechanism_engineering_handbook.md`,
section 7. v1–v3 are untouched; v4 sits beside them.

**Why v4.** Scott printed v3's test piece: "It's good, but it needs to be 3 pieces
that connect and stay together. I want people to be able to fold it down and
store it when not in use. The way it works is good." He chose the prop folding
flush into the plate.

## 1. The requirement, in numbers

- **v3's holding is kept:** the same notched easel, six angles from 80° to 55°, with
  a 250 g phone in a thick case.
- **Three pieces that can't come apart,** in use or folded and carried.
- **It folds flat:** the prop folds into the plate, and the plate folds down onto
  the base.
- **No hardware.** Every print has no supports.

## 2. The concept

### The prop's hinge: print-in-place cones
- **What it is:** the prop lies in a slot cut right through the plate, and prints
  in it, already assembled.
  - Two cones, 2.0 mm radius, stand inward from the slot's walls.
  - They sit in cone sockets in the prop's sides, 0.45 mm clear.
  - The cones' undersides are 40° off vertical as they print, so nothing prints
    over air.
- **Why not a twist-lock here too:** a twist-lock has to line up at an angle the
  joint never visits. Between folded and working, the prop swings through about
  160° of the 180° a two-flat pin repeats over. That leaves no safe angle.
- **It can't come off:** to clear one cone, the prop would have to move 1.28 mm
  sideways. The other cone stops it after 0.4.
- **Its stop:** the slot runs 26 mm below the hinge, so the prop can swing out
  past the steepest notch's angle. The slot's end stops it 4° beyond that.

### The pivot: a twist-lock
- **What it is:** pins on the plate's two side edges sit in bores in two lugs on
  the base.
  - Each pin is 6 mm round, with two flats 3.0 mm apart.
  - Each bore's slot rises straight up and is 3.6 mm wide.
- **When it lets go:** a pin fits the slot only when its flats stand upright. The
  flats are tilted 35° on the plate, so that happens only with the plate tipped
  forward to 145°.
  - From folded (0°) to the steepest notch (80°) the flats are 35–65° off.
  - At 35° off, the pin is 2 × 2.72 mm across the slot, against 3.6.
- **How it prints:**
  - **The pins** print on the plate's side edges, on the bed. A 35° flank replaces
    the part of the underside that would have overhung.
  - **The bores** have 35° teardrop flanks up to the slot's walls, so every surface
    prints.
- **What I tried first:** a slot leaning 35° left the bore's roof printing over air,
  and the slicer wanted 1,907 support moves. A teardrop roof on that leaning slot
  opened a second way out at 75–85°.

### Folding
- **The pivot height:** the pivot sits 10 mm up, so the folded plate's back face
  clears the notch bar.
- **The rest pad:** a pad at the far end of the base carries the folded plate.
- **Folded size:** 34 mm tall, on a 148 × 87 mm footprint.

## 3. Hand calculations (`stand_v4_calc.py`)

```
plate  foot    prop    push on  centre of  safety vs tipping back      sliding,
angle  at y    force   notch    mass y     1 N top  2 N top  2 N mid    1 N top
  80    19.5   1.04 N   0.16 N    13.4      2.7      1.4      2.8        1.2
  75    30.1   1.47 N   0.35 N    20.0      2.8      1.4      3.2        1.3
  70    40.5   1.71 N   0.54 N    26.6      2.9      1.4      3.7        1.4
  65    50.6   1.89 N   0.75 N    33.0      3.0      1.5      4.5        1.5
  60    60.3   2.06 N   0.97 N    39.2      3.1      1.5      5.9        1.6
  55    69.5   2.23 N   1.21 N    45.1      3.2      1.6      8.8        1.7
notch spacing 9.3-10.6 mm
pivot twist-lock: at its worst angle (folded) each side 0.92 wider than the slot: ratio 4.6, worst 0.40 -> ok; passes only at 145 deg, 65 past the steepest notch
prop hinge: cones 1.28 into the prop's sides: ratio 5.2, worst 0.40 -> ok; it cannot come off at all (the far cone stops it)
notch: rear wall 3.0 high: ratio 15.0, worst 0.40 -> ok
```

- **Tipping:** better than v3, at 1.4–1.6 for a firm 2 N press at the very top
  (v3 was 1.1).
  - The plate is heavier, at 8 mm.
  - The base runs 140 mm behind the pivot, so the folded plate can lie on it.
- **The prop and plate geometry was re-solved** for a hinge 1 mm in front of the
  pivot line:
  - the plate is 135 long;
  - the hinge is 61 up it;
  - the prop is 65 long;
  - the notches are 9.3 mm apart (v3's were 9.4).

## 4. Failure modes

| part | how it could fail | likely? | what prevents it |
|---|---|---|---|
| prop hinge | fuses in the print | medium | 0.45 normal gap at the cones, 0.4 at the sides; **the hinge test print checks it** |
| prop hinge | comes apart | none | the far cone stops any sideways shift after 0.4; 1.28 needed |
| prop | doesn't fold flush | low | it prints flush; the check folds it |
| prop | swings too far at 80° | low | the slot's end stops it 4° past the steepest notch's angle |
| pivot | pops out in use | very low | the pins clear the slots only at 145°; folded to 85° they're 0.92+ too wide each side |
| pivot | won't go on | low | at 145° the pins lift 15 mm out of the slots untouched (checked) |
| pivot | binds | low | 0.35 radial gap round the pins, which stand out to 3.38 at a corner, in 3.73 bores |
| plate | rubs the base | low | 0.4 clear at every angle; a 2 mm chamfer on its bottom front edge clears the floor at 145° |
| foot | sits between notches | low | 9.3 spacing, 3.7 troughs, 1.9 ridges |
| stand | tips forward | low | the base ends 8.5 in front of the pivot; the weight is always behind it |

## 5. The hinge test print (`fold_stand_v4_hinge_test.3mf`)

- **What it is:** both new joints at their real size.
  - A short, narrow plate, 34 wide, with the twist-lock pins and a short prop
    printed in place on its cones.
  - A small base with the two lugs.
- **No notches:** v3's test piece already proved them.

**What to check:**
1. The prop swings out of the plate freely. It mustn't be fused at the cones, and
   it mustn't come out.
2. Tip the plate well forward, past upright (about 145°), and lower its pins
   straight down into the lugs' slots.
3. Tilt it back: it should turn freely, and not lift out at any angle from flat to
   upright.

## 6. Checked on the exported parts

- **`check_stand_v4.py`:**
  - the prop in the plate's print: 0.40 least gap;
  - the prop swings out untouched from folded to 4° past the steepest notch;
  - at all six angles, nothing overlaps, the gaps are 0.40, and the foot's centre
    is on its notch;
  - folded, nothing overlaps;
  - the plate turns 0–90° in the lugs;
  - the twist-lock holds from 0 to 85° and lets go only at 145°;
  - the cones stop a 1 mm sideways shift.
- **`check_hinge_test.py`:** the same checks on the test print's own parts.

**Not tested on the printer:** both new joints. Print the hinge test first.
