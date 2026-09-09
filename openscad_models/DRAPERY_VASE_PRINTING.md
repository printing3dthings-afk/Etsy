# Drapery Vase — printing notes

180mm morphing-flute decorative vessel. `drapery_vase.3mf` is the file to print.

## ⚠️ SLICE IT IN VASE MODE. This is not a preference.

The model is **solid** — 841 cm³ of it. That is deliberate and it is the whole
design (see below), but it means the slicer, not the geometry, decides whether
you get a vase or a brick:

| how you slice it | time | filament | result |
|---|---|---|---|
| **Vase mode** (spiral outer contour) | **3h 08m** | **41 g** | ← print this |
| 3 walls · 0% infill · 0 top layers | 7h 41m | 111 g | sturdier, 2.4× the cost |
| anything with real infill | — | ~1 kg | a paperweight |

**Bambu Studio:** Others → *Spiral vase* ✔. It forces 1 wall, 0 top layers and
0% infill by itself. Bottom layers stay solid, which is what carries the
maker's mark.

Wall comes out one extrusion (~0.42mm). For a sturdier piece, raise the
vase-mode extrusion width to 0.6–0.8mm rather than adding walls — adding walls
means leaving vase mode.

## Why it is modelled solid

`tools/detail_probe.py` scores contour rugosity — a cross-section's perimeter
over its own convex hull. Across 343 real reference meshes the median is 1.061
and p90 is 1.477. **This shop's previous best, across fifteen measurable
models, was 1.086, and seven scored exactly 1.000 — no vertical relief at all.**
Our own spiral fluted vase cut flutes **1.6% of its radius** deep where real
fluted vases cut 8–20%.

That was structural, not careless. We modelled the wall, so a groove deeper
than the wall is a breach. Sectioning the corpus's top-scoring vessels returns
**no interior ring at any height** — they are solid, the slicer makes the wall,
and groove depth is therefore unconstrained.

This one is built the same way:

| | this vase | our previous best | corpus |
|---|---|---|---|
| rugosity | **2.027** | 1.086 | median 1.061 · p75 1.235 · p90 1.477 |
| flute depth | **21.3% of radius** | 1.6% | median 7.9% · p75 13.7% · p90 29.0% |
| depth : pitch | 0.83 | — | real vessels run 0.69–1.20 |

## Verified before shipping — on the real exported mesh

- Gate PASSED: watertight, one body, 111.1 × 111.0 × 180.0mm, zero degenerate
  faces, no terracing.
- **Overhang past 55°: 2.43 cm², all of it at exactly z=0.70** — that is the
  maker's mark's own 0.7mm ceiling, a bridge that short prints fine. The flutes
  and the 70° twist contribute **none**, despite running 21% deep.
- 261,248 triangles (0.5° angular sampling = 15 samples across the finest rim
  lobe).
- Sliced for real, not estimated. Layer 1 rasterises as **4 islands** — the
  foot plus the O's counter and the B's two bowls — which is the signature of
  the mark genuinely being cut rather than merged away by the slicer.

## The shape

A real ogee, proportioned off a measured reference rather than eyeballed: foot
r=43.7, **belly r=56.1 at 25% of the height** (low, not at the middle), neck
r=19.4, small lip flare to r=23.9.

The flutes **morph** rather than repeat — three harmonics (12, 24, 48)
crossfaded by height, so each broad lobe at the foot splits once through the
belly and again toward the rim. Octaves are deliberate: a non-harmonic morph
beats against itself and reads as a mistake, where a doubling reads as fabric
gathering. Amplitude breathes — quiet at the foot, deepest through the belly,
easing back at the lip so the detail resolves at both ends instead of being
chopped off at a boundary.

## Two things a first print will settle

**The flutes are deliberately bold.** 21.3% sits between the corpus p75 (13.7%)
and p90 (29.0%). If that reads as too aggressive in the hand, `depth_frac` is
the single number to pull back — 0.26 gives ~15% and rugosity 1.65, still well
above anything this shop has shipped.

**The maker's mark handedness is genuinely unsettled, and no render can
settle it.** It uses `mirror([0,1,0])`, the axis confirmed on a real vase in a
real viewer. That is correct if you **tip the vase forward** to read its base;
**turn it about its vertical axis instead and it reads reversed.** The two
flips need opposite mirrors and no single choice covers both. It matters less
here than usual — O, B and C are all near-symmetric top-to-bottom in Montserrat
Black — but if it looks wrong on the real print it is a one-character fix.

## Not yet true

**Nothing here has been printed.** Every number above is measured off the real
mesh or read from a real slice, not estimated — but a physical print outranks
all of it (Technique 35 was learned exactly that way: a wall verified at 53°
passed every check and still printed rough).
