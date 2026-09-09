# Monogram Fidget Keychain — printing notes

Print-in-place spinner, three colours, one letter per unit. `letter="J"` today;
the file takes any of A–Z from the same parameter.

**Print this:** `monogram_keychain_J.3mf` — one file, one object, three parts,
already aligned. Open it and assign a filament to each part.

| part | what it is |
|---|---|
| ring | knurled frame + keyring lug |
| rotor | the spinning disc |
| halo | the offset surround behind the letter |
| letter | the raised monogram |

Each part is independently selectable — right-click one in Bambu Studio and set
its filament. The parts are named `ring` / `rotor` / `halo` / `letter`, not by
filename, so the list is readable.

The per-part `.stl` files are the source the assembler consumes and what
`mesh_gate.py` checks — they are not the deliverable.

> **Do not export the 3MF from OpenSCAD.** Its 3MF writer merges every body
> into a single object with no materials (verified: 1 object, 1 item, 0
> basematerials, 20,065 fused triangles). That file slices fine and no filament
> can be assigned to any part of it. Build the deliverable with
> `tools/assemble_3mf.py` and confirm the parts survived.

## Why this font, and why that is not a matter of taste

A monogram product ships 26 letters and is only as good as its **widest** glyph
and its **thinnest**. `tools/glyph_probe.py` measured every letter in every
candidate face, then scaled each to fit inside the bezel (r=11.1mm after the
halo offset) and re-checked the stroke that survives:

| font | size that fits all 26 | worst stroke | |
|---|---|---|---|
| **Caveat Bold** | **14.7** | **3.87 extrusions** | **shipped** |
| Bebas Neue | 18.2 | 5.46 | modern, not elegant |
| Fredoka | 13.9 | 6.63 | prints beautifully, reads basic |
| Dancing Script Bold | 12.9 | 2.09 | passes, no margin |
| Cinzel Decorative Bold | 8.7 | **1.21** | **fails** |
| Great Vibes | 8.2 | **0.76** | **fails** |

Cinzel Decorative is the trap worth remembering. Judged on stroke width alone at
a fixed size it passes comfortably — but its **Q is 47mm wide at size 22**,
decorative swashes, so fitting the worst glyph on the face shrinks every stroke
to 1.21 extrusions. **A font can fail on proportion rather than on weight**, and
only measuring both catches it.

Caveat Bold is also the face the OBC maker's mark already uses, so the monogram
and the brand mark are the same hand.

The probe is validated against real ground truth: it **rejects** "OnBrandCraftz"
at the size that actually printed blank on three of four sauce models, and
**accepts** the "OBC" that replaced it and verifiably printed.

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
| one keychain | 57.1 × 43.7 × 9.0 mm | **50m 00s** | 8.7 g | $0.17 |

Small enough to plate 6–8 at once, which is corpus finding 10 — *"a 180mm
one-per-plate model is a long print and a weak set."* Against the sauce bowl's
11h53m for a single unit, this is the shape of product that actually pays.

## Verified before shipping — on the real exported mesh
- Watertight, 0 degenerate faces. The merged mesh reports **3** bodies, not 4:
  the halo is a flange that touches the letter, so they fuse there. That shared
  boundary is exactly right for multi-material — no gap, no overlap — and the
  shipped `.3mf` carries all **4** as independent, individually colourable parts.
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
