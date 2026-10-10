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
lost per mm of depth**, measured from two suppliers — 18mm deep, with a flat
floor meeting the wall at 45°. A real cup drops in, sits flat on the floor, and
stands **10.6mm proud** so it can be pinched back out.

> **Correction (2026-09-08).** This section used to say the cup "nests against
> the wall down its whole length." It does not, and never did. The mouth was
> sized so the cup's *rim* (30.15mm radius) clears it (30.55mm) — but the rim
> sits 10.6mm above the mouth, where the cup is only 27.22mm. There is a
> constant **3.33mm radial gap** (6.7mm across) from floor to mouth: the cup is
> held by sitting 18mm down a well, not by touching anything. Making it truly
> nest means a 55.2mm mouth instead of 61.1mm, which visibly shrinks every well
> — a design decision, not a correction, and it has not been made.

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
- **No supports.** Worst free-surface angle is **34.4°** from vertical, inside
  the 40° limit for a surface anyone sees. The only downward area past the
  structural limit is the 0.7mm-deep ceiling of the engraved mark on the
  underside — a bridge that short prints on any FDM machine, confirmed on the
  first real print.
- **Ironing on, top surfaces.** The top face and every cavity floor are now
  genuinely flat, so ironing has a single continuous surface to work on.
- Prints flat on its own foot. Broad bed contact, no brim.

## Real print cost — sliced, not estimated

| | size | time | filament | cost |
|---|---|---|---|---|
| 2oz bowl | 212 × 190 × 22.2mm | **11h 53m** | 137.2 g | $2.74 |
| 1oz bowl | 161 × 144 × 24.4mm | **7h 57m** | 94.5 g | $1.89 |

Re-sliced 2026-09-08 after the top face was flattened. Both got **cheaper**:
the 2oz dropped 2h23m (−17%) and 12.2g, the 1oz 1h21m (−15%) and 6.9g. Removing
2.85mm of height removes layers, and one flat top face needs far less solid
top-layer area than a dished one did. The fix that removed the rings also
removed two and a half hours of print time.

Note the 1oz bowl is *taller* than the 2oz (24.4 vs 22.2mm) even though it is much
smaller in plan: the 1oz cup is 31.75mm tall against the 2oz's 28.6mm, so its
cavity has to be deeper and the body has to carry it. Shrinking the footprint by
42% only buys back 35% of the time.

For comparison, the through-bore tray is 7h 34m. **The bowl costs roughly double
because it is a solid 22mm body where the tray is a 14mm plate with six large
holes punched through it** — those holes were removing most of the layer area
that drives the cost. Filament is nearly free either way; printer time is the
entire cost, and 14 hours means one unit every day and a half.

That is a real business fact about this shape, not a defect to fix. And the 1oz
size is a weaker lever here than it was on the tray: the whole set, sliced, runs

| | time |
|---|---|
| tray, 1oz | 4h 58m |
| tray, 2oz | 7h 34m |
| bowl, 1oz | 9h 18m |
| bowl, 2oz | 14h 16m |

so even the *small* bowl costs more machine time than the *large* tray. A closed
solid body is simply an expensive thing to print at this footprint; the through-
bores were removing most of the layer area that drives the cost. If the bowl form
matters more than throughput, that is the price; if throughput matters more, the
tray is the product.

## Verified before shipping — on the real exported mesh
- Watertight, **1 connected component**, flat at z=0.
- **0.00% of downward area past 40°** (see the sliver note above).
- **4.15mm of floor under every cavity.**
- **Minimum wall between any cavity and the exterior: 4.43mm** (2oz) and
  **4.03mm** (1oz) — swept over every (angle, height) pair, not spot-checked.
  Both improved from 3.08mm when the top was flattened.
- **Top face and cavity floors: zero terracing.** `mesh_gate.py` reports no
  upward surface shallow enough to stair-step. This is the defect the first real
  print exposed — see below.
- **4.9mm web between adjacent cavity mouths**, 5.7mm between cup rims.
- Maker's mark **25.76mm** = 36.3% of the 70.9mm centre pad (2oz) and **19.32mm**
  = 35.3% of the 54.7mm pad (1oz), both inside the 35–45% standing target.
- 1oz variant independently verified: 161.1 × 144.1 × 24.4mm, watertight, one
  component, 0 degenerate faces, no terracing.

## What the first real printed part found (2026-09-08)

Scott printed the 2oz bowl. The maker's mark came out legible — confirming the
stroke-width fix — the underside was flat and clean across 212mm, the cavity
walls were smooth, and it needed no supports. Two real defects showed up that
no check in this repo could have caught:

**1. The whole top face was ringed with concentric terraces.** The face was a
shallow paraboloid rising 5.50mm over 95mm of radius. A surface of gradient `g`
steps sideways by `layer_h / g` every layer; this one's *steepest* slope
anywhere was 6.6°, giving a 1.73mm terrace — 4 extrusions wide — and at the
axis, where a paraboloid's slope is zero, the first terrace was **18.12mm**. The
result was a 36.2mm flat disc in the middle and 26 rings tightening outward.
No slicer setting fixes this: ironing smooths *within* a terrace and cannot fill
a vertical step, and adaptive layers do nothing at a stationary point. **The top
face is now flat** — one clean surface, zero steps.

**2. A hard ring in the bottom of every well.** The floor was a flat disc with a
5mm tangent fillet. A tangent fillet is horizontal where it meets the floor, so
its first layer steps by `sqrt(2·R·layer − layer²)` all at once — **1.40mm**,
3.3 extrusions. **The floor now meets the wall at a constant 45°**, which steps
exactly one layer height (0.20mm, half a bead) the whole way.

Both are now checked: `mesh_gate.py` reports `terracing` — upward-facing area
too shallow to hide a layer step — and it flagged the old geometry at 86 cm²
while scoring the new one at zero. Full write-up in the 3d-print-design skill,
Technique 54.

**What was given up:** the dish used to scallop the rim for free, so the rim is
now level. The flower still reads from the petal outline in plan, which is what
the eye picks up first. `flare_ease` also had to drop 1.50 → 1.20: a shorter
body puts the same 8mm of radius change over less height, and 1.50 pushed the
steepest flare to 40.1° — exactly the ceiling for a buyer-visible surface, with
no margin.

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
-D floor_min=4.41
```

The maker's mark needs no override: `mark_size` is **derived** from each
model's own centre pad (50% of it), so a smaller variant automatically gets a
proportionate mark instead of inheriting an oversized one.

`part=` also accepts `preview` (with cup mock-ups), `cavity` and `mark` for
checking a cutter's own extents in isolation.
