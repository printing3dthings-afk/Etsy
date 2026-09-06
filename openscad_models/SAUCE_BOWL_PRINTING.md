# Six-well sauce bowl — printing notes

One enclosed piece: a flared six-petal bowl with six **cup-shaped cavities**
sunk into the top. Nothing passes through it. The closed sibling of
`sauce_tray.scad`, which holds the same cups in through-bores.

| File | What it is |
|---|---|
| `sauce_bowl` | 2oz cavities — the standard dipping cup |
| `sauce_bowl_1oz` | 1oz cavities — smaller, and the only real lever on print time |

Both ship as `.3mf` (use these — real mm units) and `.stl`.

## The cavity is cut to the real cup, on purpose

Each cavity follows the actual 2oz portion cup's taper — **0.2762mm of radius
lost per mm of depth**, measured from two suppliers — plus 0.8mm of fit, 18mm
deep with a 5mm filleted floor. A real cup drops in, nests against the wall down
its whole length, and stands **10.6mm proud** so it can be pinched back out.

That is a deliberate constraint, not a coincidence of scaling. FDM layer lines
are porous and trap residue that washing does not clear, and this shop's P1S runs
a **stock brass nozzle**, which sheds trace lead. A dish sold to be poured into
directly is a food-contact claim we cannot defend. Cutting the cavity to the real
cup keeps the piece honestly sellable as a holder while looking and behaving
exactly like a bowl — the customer decides.

**Do not re-cut these cavities to an arbitrary size without re-opening that
question.** The parameter carries the same warning in the source.

## Print settings
- **PLA or PETG**, 0.2mm layers, 3 walls, 15% gyroid.
- **No supports.** Worst free-surface angle is 37.5° from vertical, inside the
  40° limit for a surface anyone sees. Two faces measure 46.3° but carry
  **0.000 mm²** between them — degenerate slivers where a cavity mouth meets the
  dished top, not a real unsupported region.
- Prints flat on its own foot. Broad bed contact, no brim.

## Real print cost — sliced, not estimated

| | size | time | filament | cost |
|---|---|---|---|---|
| 2oz bowl | 212 × 190 × 25mm | **14h 16m** | 149.4 g | $2.99 |
| 1oz bowl | _measuring — figures added when sliced_ | | | |

For comparison, the through-bore tray is 7h 34m. **The bowl costs roughly double
because it is a solid 25mm body where the tray is a 14mm plate with six large
holes punched through it** — those holes were removing most of the layer area
that drives the cost. Filament is nearly free either way; printer time is the
entire cost, and 14 hours means one unit every day and a half.

That is a real business fact about this shape, not a defect to fix. The levers
are the 1oz size or a shallower cavity, both parametric.

## Verified before shipping — on the real exported mesh
- Watertight, **1 connected component**, flat at z=0.
- **0.00% of downward area past 40°** (see the sliver note above).
- **4.15mm of floor under every cavity.**
- **Minimum wall between any cavity and the exterior: 3.08mm** — swept over
  every (angle, height) pair, not spot-checked.
- **4.9mm web between adjacent cavity mouths**, 5.7mm between cup rims.
- Maker's mark **25.76mm** = 36.3% of the 70.9mm centre pad, inside the 35–45%
  standing target.

## Real bugs caught during the build
- **The cavity nearly breached the outer wall, and no render showed it.** The
  mouth is 61.1mm here against the tray's 53mm bore, so it does *not* fit inside
  the tray's petal outline. A numeric sweep over every (angle, height) pair found
  the cavity within **0.09mm** of the exterior near the petal shoulders. `rim_r`
  and `petal_amp` were then *solved* against that sweep rather than chosen by
  eye. Inheriting a proven outline is not the same as verifying it against new
  geometry.
- **The web between adjacent cavity mouths was 1.9mm** at the tray's spacing —
  printable, but a sliver that reads as a mistake. `ring_r` 63 → 66.
- **The bowl flares the "wrong" way on purpose.** A real bowl flares hardest at
  the *bottom*, which is exactly the unprintable direction — a small foot
  opening out fast is a steep overhang. This one stays near-vertical low down and
  opens toward the rim (`flare_ease = 1.5`), which reads as a flared vessel and
  prints support-free. The petals are 60% developed at the foot and 100% at the
  rim, so the flower opens as it rises and the foot stays broad enough to keep
  the flare inside the angle limit.

## Regenerating a variant
Every dimension is a named parameter and `z_samples` derives from `bowl_h`, so a
new cup size is a set of `-D` overrides. The 1oz variant is exactly:

```
-D cup_rim_d=44.5 -D cup_base_d=31.75 -D cup_h=31.75 -D cav_depth=20 \
-D ring_r=50 -D rim_r=72 -D foot_r=66 -D petal_amp=9.1 \
-D bowl_h=27 -D dish_lo=22 -D mark_size=2.7
```

`part=` also accepts `preview` (with cup mock-ups), `cavity` and `mark` for
checking a cutter's own extents in isolation.
