# Fold Stand v3: the engineering, before the model

2026-11-10. This follows `data/knowledge_base/mechanism_engineering_handbook.md`,
section 7, step by step. v1 and v2 stay where they are; v3 sits beside them.

**Why v3.** v1's click was 0.35 mm deep and its pins were a 0.05 press fit. v2's
ratchet notch was 0.45 deep. Both sat inside a tolerance stack of about 0.75 mm
worst case, so neither could work once printed. Scott: "pins don't click".

**His pick, option A:** an easel. The prop's foot sits in deep notches in the base.

## 1. The requirement, in numbers

**What it holds:**
- A large phone in a thick case: 250 g, 160 mm tall, 10.5 mm deep, cases up to 13.
- Six angles: 80, 75, 70, 65, 60 and 55° from the table.
- Every angle must hold with the phone on it, and with a tap into the screen:
  - 1 N, a touch, anywhere on the screen;
  - 2 N, a firm press, at the very top.
- Lifetime: thousands of angle changes. So nothing may wear a catch down or
  fatigue a flexure.

**How it's assembled:**
- Three prints, no hardware, no glue.
- The plate drops into the base, and the prop drops into both.

## 2. The concept: rank 1 in section 5, geometric notches

The angle is set by where things are, not by a catch's strength.

**The three joints:**
- The plate's round bottom edge (a tongue, r 3) lies in a groove across the base
  (r 3.7).
  - The tongue's underside is a teardrop, 35° off vertical, so it prints
    without supports.
  - Its corner stands 0.39 outside the circle, so the groove is 0.7 roomier
    than the tongue, not 0.4.
  - Contact is always within 10° of the tongue's end, on the round part.
- The prop is a bar with round ends.
  - Its top end (the nose, r 2) sits in the top corner of a pocket in the
    plate's back.
  - Its foot (r 3) sits in one of six notches (r 3.4) in a bar on the base.

**Why it holds:**
- Every load is plastic pressing on plastic.
- Gravity keeps each joint seated.
- Nothing bends, so there is no strain, no fatigue, and no creep that matters.

**Why not the simpler or cheaper options:**
- There is nothing simpler than this.
- A friction hinge or a Hirth lock would need a screw.
- A detent gives feel, not hold: handbook section 5.

**What changed from the first sketch:** the nose was going to sit in a slot
through the plate. The calculation showed that wouldn't hold.
- At 80° the prop pushes up along the plate, 68° off its normal.
- Only friction, μ 0.45, would have kept the nose from sliding through.
- Now it sits in the pocket's top corner, against its ceiling and upper wall.
  That holds any push from −24° (friction on the ceiling) to +90° (straight
  into the upper wall).

## 3. Hand calculations (`stand_v3_calc.py`, using `tools/mechanism_budget.py`)

```
plate  foot    prop    push on  push at   centre of  safety vs tipping back      sliding,
angle  at y    force   notch    socket    mass y     1 N top  2 N top  2 N mid    1 N top
  80    27.2   0.90 N   0.18 N     68 deg    12.6      2.2      1.1      2.2        1.2
  75    38.3   1.22 N   0.35 N     58 deg    19.1      2.2      1.1      2.4        1.2
  70    49.0   1.43 N   0.53 N     48 deg    25.5      2.2      1.1      2.7        1.3
  65    59.4   1.60 N   0.72 N     38 deg    31.7      2.2      1.1      3.1        1.4
  60    69.4   1.77 N   0.93 N     28 deg    37.8      2.2      1.1      3.6        1.5
  55    78.8   1.95 N   1.16 N     18 deg    43.6      2.3      1.1      4.5        1.6
push at the socket 18-68 deg from the plate's normal: held from -24 to 90, margins 42 and 22 deg
notch spacing 9.4-11.1 mm (want >= 8 so the foot can't sit between two)
pivot: tongue 3.0 in a groove 3.7 deep: ratio 12.9, worst 0.45 -> ok
notch: rear wall 3.0 high: ratio 15.0, worst 0.40 -> ok
socket: the nose must come 2.6 out of the pocket to pass its upper wall: ratio 10.6, worst 0.40 -> ok
clearances: 0.4 at the notches and the socket, 0.7 round the tongue (0.32 at its teardrop underside), against the 0.3 minimum open gap
```

**Engagement:**
- Every joint is 10 to 15 times the RSS of its tolerance stack, and deeper than
  its worst case.
- v2's ratchet was 1.2 times; the rule is at least 3.

**Strength:**
- The largest load anywhere is under 2 N.
- The prop is 20 × 4–6 mm PLA. Its Euler buckling load is π²EI/L² ≈ 630 N,
  about 300 times the load.

**Clearances:** against the 0.3 that reliably stays open:
- 0.4 at the notches and the socket;
- 0.7 round the tongue, and 0.32 at its teardrop corner.

**Tipping:**
- The base runs 120 mm behind the pivot, not the 100 the notches need, so that
  a firm 2 N press at the very top of the phone still doesn't tip it (1.1).
- A 1 N touch anywhere is 2.2 or more.

**Sliding:**
- On a slick desk (μ 0.35), a 1 N tap at the top is 1.2.
- A firm 2 N press at the top would slide it back about as far as you push.
  It slides; it doesn't fall.
- Four small stick-on rubber feet fix that if Scott wants them. They're
  optional, not part of the design.

## 4. Failure modes (DFMEA-lite)

| part | how it could fail | likely? | what prevents it |
|---|---|---|---|
| plate | won't drop into the groove | low | the groove is open from above; worst-case tongue (r 3.25, corner 3.64) in worst groove (3.6) still drops in, it just sits 0.04 high at one angle |
| plate | rides out of the groove | low | the prop pushes it forward into the front wall, which stands to the tongue's axis; it can only lift out upward |
| plate | slides sideways | low | the prop locates it (pocket 20.8 for a 20 prop), and the prop's foot is in a closed-ended notch: ≤ 0.8 mm play |
| prop nose | slips out of the pocket | low | the push stays 18–68° off the normal; the corner holds −24 to 90°: margins 42° and 22° |
| prop nose | bears on a sagging bridge | medium, harmless | the pocket's ceiling is a 7 mm bridge on the bed face; a 0.2 sag moves the angle < 0.2° |
| prop foot | slips to the next notch | very low | the push on the foot points down and back into the rear wall (3.0 high); it can't climb without being lifted |
| prop foot | sits on a ridge between two notches | low | ridges are 2.6+ wide with round notches either side: the foot rolls into one |
| prop | its side catches the notch's front rim | fixed | the prop's tangent side passes the rim closer than the foot does; each notch now has the prop's own path cut out, 0.4 clear (found by the fit check) |
| any | cracks | very low | all loads < 2 N in compression; no flexing part |
| any | creeps or softens (hot car) | low | nothing is under bending strain, so creep can't change an angle; above Tg (57 °C) any PLA part softens |
| stand | tips back under a firm press | low | 120 mm base behind the pivot: 1.1 at 2 N at the very top, 2.2+ at 1 N |
| stand | slides back on a slick desk | medium | 1 N at the top is fine (1.2); 2 N slides it. Optional rubber feet |
| user | prop in upside down | low | the ends differ (6 vs 4 mm thick); the guide says which way; it would still hold, at a different angle |
| phone | slides off the shelf | low | 13 mm deep shelf with a 3 mm chin, leaning out 35° off vertical so it prints |

## 5. The coupon

- **What it is:** the same three joints at their real size, on a narrow (30 mm),
  short version of the stand: `fold_stand_v3_coupon.3mf`.
  - It uses the real prop.
  - It's about 43 minutes and 15.5 g, all in one colour, with no supports.
  - That's over the 30 minutes rule 5 asks for. The joints here are the whole
    mechanism, so the coupon is the whole stand, cut down to what holds a
    phone.
- **What to do with it:**
  - drop the plate in;
  - set the prop in each notch;
  - stand your phone on it.
- **No clearance variants.** Rule 5 asks for 2–3, and they're left out on
  purpose. No joint here depends on a fit: each is a round end resting in a
  trough 10 to 15 times deeper than its tolerance stack. A loose fit only moves
  an angle by a fraction of a degree.

**What to check, in order:**
1. The plate drops into the groove and rocks freely.
2. The prop's foot drops into each notch, and its top end into the pocket on
   the plate's back.
3. With your phone on the shelf at each notch, it doesn't move when you tap
   the screen.
   - The coupon is narrow, so it can rock sideways.
   - The real stand is 76 wide.
4. Lift the phone, move the prop to another notch, put the phone back. Easy?

## 6. Measured clearances

The Fit Test Plate results aren't in yet. Until they are, everything uses the
conservative values from handbook section 1. None of v3's joints depends on
them.

## 7. What was calculated, what was checked, what wasn't tested

**Calculated:** the table above.

**Checked on the exported parts (`check_stand_v3.py`), posed at all six angles:**
- no part overlaps another;
- every open gap is 0.40, against the 0.3 minimum;
- the nose bears in the pocket's top corner;
- the plate turns freely from 54 to 90°.

**Not tested on the printer:** everything. The coupon comes first.
