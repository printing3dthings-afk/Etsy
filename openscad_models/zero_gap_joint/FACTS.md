# Zero-gap joint test, FACTS (2026-11-14)

**The question:** can a moving part print with no gap at all, if the gap is filled with a
material made not to bond to PLA? Every print-in-place joint we make needs 0.3–0.45 mm of
air today, and that air is the wobble. Background:
`data/knowledge_base/fdm_only_techniques.md`, section 3.

## The print (`zero_gap_coupon.gcode.3mf`, sliced; `zero_gap_coupon.3mf`, the project)
- **Materials:** AMS slot 1 PLA, slot 2 **Bambu Support For PLA** (Scott has it).
- **Bambu Studio 2.8.2:** 1 h 1 min 26 s; 15.9 g PLA, 4.3 g support (mostly purge);
  20 layers, 22 material changes; no supports. Ironing off, so the top isn't smoothed
  across the joints.
- Over the 30-minute aim for a coupon: every layer has both materials, so the changes are
  most of the time.

## The three turntables (rotor in a ring, held by a V ridge with 50° flanks)
| dots | gap |
|---|---|
| 1 | 0.30 mm of air (control, what we do today) |
| 2 | 0.45 mm sleeve of support material, no air: **zero gap** |
| 3 | 0.45 mm sleeve + 0.10 mm of air |

## Checks (on the exported parts)
- **Fit** (`check_fit.py` -> `checks/fit.txt`): PASS.
  - Each rotor clears its ring.
  - The sleeves touch, without overlapping.
  - A 0.5 lift hits the ridge, so it's held.
  - Turned, it's free.
- **Product gate (PLA parts):** PASS.
  - Min wall 1.24.
  - At 45° the ridge flanks drew 54 support moves in the gate's slicer, so they are 50°.
- **Print fidelity, both materials:** 0 flags. The one-bead sleeve prints whole; only
  0.1 mm specks at the dots are missed.
- **Fragility:** 0.
- **Caught by the cut-away render, not by any gate:** a sealed diamond void at every
  rotor's centre.
  - Cause: the turned profile started at radius ridge(z), not 0, so the cavity touched
    the axis only along a line and the mesh still read as one watertight shell.
  - Fixed: the centre is now filled.
  - The gate has no sealed-void check (see the knowledge file).

## Not known until Scott prints it
- Whether Support For PLA stays unbonded **side by side** in the same layer. It is made
  not to bond **layer on layer**.
- How hard the first turn is.
- Whether the sleeve survives as a bearing.

Guide: `Zero_Gap_Joint_Test_Guide.pdf`.
