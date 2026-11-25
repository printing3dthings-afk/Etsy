# TEST — Snap-Fit Coupon — pack

Status: BUILT Nov 22, 2026 (Batch 3 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
Snap-fit arms sized by the strain formula ε = 1.5·h·y/L² instead of guesswork.
Five arms bracket the PLA limits (1.2% repeated use, 2.0% single snap) so one
print finds the shop's design ceiling.

## Geometry (src/snap_fit.py, src/SnapFitCoupon.stl)
- Base plate 168 x 62 x 4 mm + back rail; five arms stand 6 mm tall on the
  plate, printed flat, flexing in the layer plane (bending across layers
  would halve the allowable strain).
- Each arm: root thickness h, tapered to 55% at the tip, root fillets
  r = 0.6h (≥ the 0.5t rule). Tip hook printed ENGAGED in a notch in a catch
  block: hook penetration 1.3 mm = the release deflection y; printed gaps
  0.3 mm (arm↔block, hook in notch) so nothing is fused.
- Arms (L, h, design strain at y = 1.3): 22/2.0 → 0.8%, 18/2.0 → 1.2%,
  15/1.8 → 1.6%, 14/2.0 → 2.0%, 13/2.2 → 2.5%. Strains are the prismatic-
  beam formula values; the taper lowers the true peak strain slightly —
  the labels are the conservative design numbers.
- Labels engraved on the plate in front of each arm ("L22 0.8%" …).
- Mesh-verified (verify_batch3.py): arm widths at root+2 mm within 0.03 of
  design, hook penetration 1.300 mm on all five, notch back gap 0.31 mm.

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- SnapFitCoupon_Standard_P1S.3mf — 0.20 mm Standard @BBL X1C, 3 walls, 15% grid,
  supports off, ironing ON (top). Verified slice: 1 hr 35 min - 40.42 g.
- SnapFitCoupon_Optimized_P1S.3mf — 0.16 mm Optimal @BBL X1C, 3 walls, 12% gyroid,
  supports off, ironing ON (top). Verified slice: 1 hr 58 min - 44.05 g.
- Both: matte white PLA (Bambu PLA Matte @BBL P1S 0.4 nozzle), printer Bambu Lab
  P1S 0.4 nozzle, round-trip re-slice with checks ON passed. Clearances are
  IDENTICAL in both profiles — layer height is the only variable.

## Profile choices / compromises
- Ironing ON for this coupon only in Batch 3: the measured features (hook,
  pocket, arm flex) are all in-plane; ironing touches only the top faces and
  the plate/rail tops are the customer-facing-style flats. It costs real time
  (the Standard's 1h35 is mostly plate) — noted, accepted.
- Arms are 6 mm tall for grip; their in-plane thickness (1.8–2.2 mm) is the
  bending dimension h in the formula.

## Gallery
images/ are the Studio plate render of the Standard profile + centre/corner
crops — renders, labelled as such in the listing copy until Scott prints it.
