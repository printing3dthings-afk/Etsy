# Pocket Top: engineering (mechanism handbook section 7), 2026-11-14

## 1. Requirement
- Three parts, snapped together by hand: no glue, no tools.
- The snap survives **20 snap-and-unsnaps** in matte PLA (the brief).
- It holds the body on in spinning and in a drop, and the stem drives the body when twisted.
- Concentric enough to spin.
- Budget for the whole top: ≤ 5 g and ≤ 10 min. The coupon isn't held to that, but the joint
  has to fit in a top that is.

## 2. Concept: in-plane spring beams in a flat hub, a hex stem
- **Simpler classes fall short:**
  - A press fit or friction can't come apart 20 times.
  - A split stem (like the Gear Heart pin) prints lying down, so its round, its tip and its
    concentricity come out stepped.
- **The chosen layout:**
  - The hub prints flat. Its three beams lie in that plane and bend along the layers.
  - The stem prints upright, so its hex, groove and future tip are drawn in XY, true and
    round.
  - The hex drives the spin. Friction alone would pass on about 0.5 N mm against the
    1.8 N mm a twist needs (`snap_budget.py`).
  - The three nubs, held 0.05 into the groove, hold the stem and centre it.

## 3. Numbers
`snap_budget.py` -> `checks/snap_budget.txt`; table in FACTS.md. The beams are 1.3 x 3.4 x 12
(constant section), and every variant stays under the 0.8 % repeated-strain limit.

## 4. Failure modes
| mode | how likely | what prevents it, or what the coupon tells us |
|---|---|---|
| beam cracks at its root | the main risk (matte PLA) | strain 0.47-0.74 % vs 0.8 %; bends along the layers; round slot ends (r 0.4) at the root; **20 snaps is the test** |
| won't snap in | low | 45 deg lead-in on the stem end; push-on 8-12 N |
| too loose, the body falls off | medium for pair 1 | pair 1's 0.35 reach is under 3x RSS on purpose; pull-off 4-6 N |
| comes apart in a drop | medium | pull-off is lower than push-on: the catch flank is 30 deg from the axis so the upright stem prints without supports; tell Scott to drop-test |
| stem spins inside the body | low | hex drive, 6.6 deg free play then it bears |
| wobble (off-centre) | low | three preloaded nubs centre it; the hex has 0.15 a side |
| beams creep, the hold weakens | low | held strain 0.07 % |
| small part swallowed | certain for the stem | label "Not for children under 3: small parts"; body over 32 mm |

## 5. What the coupon must answer (Scott)
- Which pair survives 20 snaps without whitening at a beam root? Does any crack?
- Which feels best: firm going on, and not falling off when shaken or dropped onto a table?
- Does any stem wobble or spin loose in its hub?

## 6. Scott's result (2026-11-15)

Scott: "The snap top test, they all passed." All three pairs (reach 0.35, 0.45, 0.55) snapped in and stayed in.
He asked how tight it should be. The answer, from the design:
- **In and out:** no play at all. The nubs sit 0.05 into the groove, so the stem shouldn't slide or
  rattle along its axis.
- **Side to side:** no wobble. The three preloaded nubs centre the stem, and any wobble shortens
  a top's spin.
- **Twist:** a few degrees of free turn (6.6° by design: the hex has 0.15 a side) before the hex
  catches. That's normal, and harmless for a top.

**Scott's pick: pair 2, reach 0.45** (2026-11-15: "Number 2 felt the best"). That's the
design value, so nothing changes:
- the top uses 0.45;
- the Wishing Well windlass's crank wheel already does.

## 7. The UFO (Scott's form pick, 2026-11-15)
- **The joint is pair 2 exactly.** `ufo_top.scad` takes every joint number from
  `snap_coupon.scad` (`snap_dims()`, `beam_cut()`, `nub(1)`), so the saucer's hub is the coupon's
  hub and the stem's hex and groove are the coupon's.
- **What changed round the joint, and why it's safe:**
  - The shoulder is a boss of r 4.4 under the dome. The coupon's grip was r 5. Both stop short
    of the beams (r 4.75), so the beams flex freely; the fit check confirms it.
  - The full hex runs 1.7 past the saucer, then becomes the tip cone. The coupon's hex ran on to
    a chamfer. The catch flank still ends in full hex at the flats and the corners.
  - The tip cone is the lead-in: on the way in it bends each nub out by the full 0.45, as the
    coupon's 45° chamfer did.
- **Failure modes added by the form:**

| mode | how likely | what prevents it |
|---|---|---|
| dome snaps off the stem at the boss | low | solid dome, boss 8.8 across; a twist is about 1.8 N mm (`snap_budget.py`) |
| tip wears or chips in a drop | medium | 1 mm round end (the penny spinner's), cone at 25° from the axis |
| face prints with sagging edges | low | each shape ends in a point at its ceiling; print_fidelity 0 flags |
| rim touches the table early | low | 20.7° of lean before the rim touches |
| small parts swallowed | certain for the stem | "Not for children under 3: small parts" |

- **What only a print can answer:** whether 20 snaps in matte PLA still hold for the saucer's
  hub (the coupon says yes); how long it really spins; whether the face reads at arm's length.
