# Press-to-Light Chapel: the lift-and-drop drive (mechanism handbook section 7), 2026-11-17

Benson's brief (2026-11-14, approved by Scott): press the steeple and a spinner inside
turns round the tea light, so the light moves across the windows. Scott chose
**lift-and-drop** over a spring: lift the steeple and let go, and its own weight drives
the spin on the way down. No spring, matte PLA. This file covers the test print only;
the chapel is designed round it after Scott has printed and tried it.

## 1. Requirement
- **Let go of the lifted steeple, and the spinner turns at least one full turn,** with
  no push, from the steeple's weight alone.
- **The spinner turns freely as printed,** with nothing to clean up but snapping the
  parts off the plate.
- **50 lift-and-drop cycles** without binding or visible wear.
- **Hard stops both ways,** by design, not by parts jamming.
- **The steeple doesn't turn** as it rises and falls; only the spinner does.
- **Battery LED tea lights only:** a spinning PLA drum near a flame is a fire risk.

## 2. Concept: a twisted star through a short star nut, then a coast
- **The drive:**
  - The steeple's shaft carries a twisted star bar: four teeth, a turn every 24 mm,
    20 mm long.
  - It passes down through a 4 mm star-shaped nut at the top of the spinner's hub.
  - The shaft can't turn (a square key slides in the guide's tunnel), so the falling shaft
    turns the nut, and the spinner with it.
  - This is the push-to-spin helix of the HelixCore spinner in Benson's design study, run by
    gravity instead of a thumb.
- **The coast:** just before the steeple lands, the star leaves the bottom of the nut. From
  there the spinner is free on a point pivot, and runs on.
- **The lift:** the star goes back up through the nut. The spinner turns back, and the
  star's pointed tip finds the nut from below.
- **The stops:**
  - **Up:** a collar under the key seats in the guide's tunnel mouth on a 38 deg cone. It
    never passes through the nut: at rest it sits 1 mm above the hub.
  - **Down:** the steeple lands on the guide's top.
- **Why not simpler:** a thread you press down is self-locking at a normal pitch, and a
  spring in matte PLA is out (Benson's brief: it loses its springiness). The helix has to be
  steep enough for the weight to back-drive it, and shallow enough to print without support.

## 3. Numbers (`chapel_budget.py` -> `checks/budget.txt`)
- **Helix:** 56 deg from level at the teeth's middle. PLA on PLA slides at about 24 deg
  (mu 0.45), 29 deg at worst (0.55), so the weight drives it with margin.
- **Printing:** every twisted face leans 45 deg or less from upright: the shaft's tips 39.5,
  the nut's slots 43.7, the bore under the nut 44.5.
- **Drive against friction:** with the masses measured on the exported parts (9.4 g
  falling, the steeple printed solid), the weight's torque on the hub is 4 times the
  pivot's drag at worst-case friction (needs 2). The guide's key friction is counted.
- **Turns:** one full turn driven, then a coast. The pivot alone would let it coast 6 to 10
  turns; rubbing elsewhere will cut that, and the test print is what measures it.
- **Engagement:** the star's tips overlap the nut's teeth by 0.65 to 0.85 mm across the
  three clearances, more than 3 times the tolerance stack (needs 0.54).

## 4. What the checks changed, in order (each was found by a check, not by eye)
1. **The nut's underside was a round 45 deg cone.** It filled the star's slots, and the
   fit check's sweep found the shaft running into it, 2-3 mm3 part-way down, on every
   hub. Now a 3 mm cone for the nut teeth's undersides, with the star's slots running
   straight down through it.
2. **At 20 mm a turn the nut's slots leaned 48 deg** (they sit further out than the
   shaft's tips), and the gate's slicer propped them. At 24 mm a turn, all are under 45.
   That also steepened the helix: more drive. The star grew from 16 to 20 mm to keep a full
   driven turn.
3. **The star's end, printed upside down, hung 1.5 mm off the rod.** A round cone there
   can't pass through the nut. The star now tapers into the rod over 5 mm, twisted the same
   way, so every section of it fits through the nut.
4. **The lift stop:** first planned on the taper, the check found it 1.2 mm off, at a wedge
   angle (about 18 deg) that could hold the steeple up. Moved to a collar that never
   reaches the nut, with a 38 deg seat.
5. **Smaller ones:**
   - the base's square bosses stood out past its rounded corners;
   - the arch's square tunnel had a flat 5.2 mm roof (now a peaked diamond, the key turned
     45 deg);
   - the pivot's needle tip was finer than a bead (now a 0.4 radius flat, the budget's
     friction radius);
   - the collar's rim was 0.6 thick, under the wall floor (now 1.2);
   - the shaft's round tip met the star's root circle on the same radius and left slivers
     (now the star tapering to a point, twisted the same way).

## 5. Checks on the exported parts (`run_gates.sh` -> `checks/`)
- **Fit, the whole drop** (`fit_coupon.txt`), with the hub turned by the helix at every
  step:
  - no contact with any of the three hubs or the frame;
  - at rest the hub turns a full turn untouched;
  - both stops catch.
  - A hub turned the wrong way does collide, so the sweep can see a bad helix.
- **Product gate:** base, arch, steeple and all three hubs pass.
  - The shaft declares two thin-on-purpose bands to the wall check: the taper, where the
    teeth shrink into the rod, and the pointed tip.
- **Fragility:** 0 high, 0 watch.
- **Slice** (Bambu Studio, PLA Matte, its own speeds; 0 supports):
  - main plate: everything with the 0.4 hub, 57 min 53 s, 24.4 g;
  - second plate: the 0.3 and 0.5 hubs, 23 min 49 s, 9.9 g.
  - **The main plate is over the handbook's 30 minutes.** The drop can't be tested without
    the frame, the shaft and a steeple of real weight, and the solid steeple alone is about
    a quarter of it. The second plate is printed only if the 0.4 hub binds or rattles.

## 6. Failure modes
| mode | how likely | what prevents it, or what the test print tells us |
|---|---|---|
| the weight won't drive it (self-locking) | low | helix 56 deg vs friction 24-29 deg; 4x margin at worst |
| binds in the nut part-way | medium | three clearances (0.3 / 0.4 / 0.5); the sweep checks the whole drop |
| the star doesn't find the nut on the lift | medium | pointed tip; the hub is free to turn into line; four starts |
| the lift stop wedges and holds the steeple up | low | 38 deg seat, wider than friction's 29 at worst |
| coast is short (rubbing) | medium | point pivot on a 0.4 flat; the rod 0.7 clear of the nut; the test print shows it |
| the shaft snaps (3.2 mm rod) | low | it only carries the steeple's weight; guided top and bottom; fragility 0 |
| the twist prints rough | medium | every twisted face 45 deg or less; the slice shows it |
| the arch's pegs are loose or tight in the base | low | 0.15 all round, a push fit |

## 7. What only Scott's test print can answer
- Whether the steeple, let go, spins the hub, and how many turns in all.
- Whether the lift always finds the nut, and the stop always lets go.
- With 50 drops, any binding or wear; with the second plate if needed, which clearance runs
  best.
