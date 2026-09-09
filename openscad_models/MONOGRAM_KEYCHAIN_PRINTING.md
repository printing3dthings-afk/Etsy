# Monogram Fidget Keychain — printing notes

Print-in-place spinner, three colours, one letter per unit. `letter="J"` today;
the file takes any of A–Z from the same parameter.

| file | what it is |
|---|---|
| `monogram_keychain_J_ring.3mf` | knurled frame + keyring lug — **colour A** |
| `monogram_keychain_J_rotor.3mf` | the spinning disc — **colour B** |
| `monogram_keychain_J_letter.3mf` | the raised monogram — **colour C** |
| `monogram_keychain_J_all.3mf` | everything, for checking the assembly |

Load the three colour bodies as parts of ONE object in Bambu Studio and assign
a filament to each. They already share an origin, so "load as single object"
lands them correctly with no positioning.

## Why this font, and why that is not a matter of taste

`tools/glyph_probe.py` swept all 26 letters in six candidate faces. The
decisive numbers, at size 18:

| font | J's typical stroke | verdict |
|---|---|---|
| **Fredoka** | **9.05 extrusions** | **shipped** |
| Poppins SemiBold | 7.43 | fine, less character |
| Bebas Neue | 6.00 | fine, condensed |
| Caveat Bold | 4.48 | fine |
| Montserrat | 3.81 | fine |
| Cinzel Decorative | **0.57** | **would print as nothing** |

Cinzel's J is a 0.24mm hairline against a 0.42mm bead. It renders beautifully
and prints blank. Fredoka's weakest glyph across the whole alphabet loses
**0.01%** of its area to a one-bead opening.

The probe is validated against real ground truth, not theory: it **rejects**
"OnBrandCraftz" at the exact size that printed blank on three of four sauce
models, and **accepts** the "OBC" that replaced it and verifiably printed.

## The print-in-place trap

The rotor is captive inside the frame on a shallow V — the rotor's rim bulges
1.5mm at mid-height, the frame's bore mirrors it 0.40mm larger. **0.40mm is the
proven rotating clearance**, the number Technique 22's hinge actually spins on;
0.2–0.3mm is a static peg fit and would seize. Both faces of the V sit at 22°
from vertical, far inside the 55° limit, so the trap prints with no support in
either direction.

The bore is defined **once**, by the rotor's own envelope, and cut from the
frame. Defining it in both places left 40 zero-volume slivers where two
near-coincident surfaces fought.

## Detail, on purpose

Corpus finding 1 — *"a smooth panel reads as unfinished, not as minimal"* — so
the frame carries 44 knurl scallops and the rotor face a bezel groove ringing
the letter. The letter's top sits **flush with the frame**, which is both the
cleaner look and the reason the proudest feature never rubs in a pocket.

The rotor face is **flat, deliberately**. A shallow dome there would stair-step
exactly like the sauce bowl's top did (Technique 54).

## Real print cost — sliced, not estimated

| | size | time | filament | cost |
|---|---|---|---|---|
| one keychain | 57.1 × 43.7 × 9.0 mm | **50m 12s** | 8.8 g | $0.17 |

Small enough to plate 6–8 at once, which is corpus finding 10 — *"a 180mm
one-per-plate model is a long print and a weak set."* Against the sauce bowl's
11h53m for a single unit, this is the shape of product that actually pays.

## Verified before shipping — on the real exported mesh
- Watertight, **3 bodies** (frame / rotor / letter), 0 degenerate faces.
- **Zero terracing** — no upward surface shallow enough to stair-step.
- Overhang past 55°: **1.24 cm²**, all of it accounted for — 0.35 cm² is the
  0.7mm-deep OBC mark ceiling on the rotor underside (a bridge that short prints
  fine, confirmed on the real sauce bowl), and 0.89 cm² is the letter's flat
  base, which physically rests on the rotor. The gate counts each colour body
  alone and cannot see that one sits on another; this is why its overhang line
  reports and never fails.

## Not yet true
**Nothing here has been printed.** Every number above is geometry measured
against the mesh or read from a real slice. The 0.40mm clearance is proven on a
hinge, not on this spinner — a spinner is a tighter ask. **Print one before
committing to a 26-letter set.**
