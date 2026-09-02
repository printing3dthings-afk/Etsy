# Flexi seahorse — how to print it

One file, one part, no supports, no assembly. It comes off the plate already
articulated: **flex each joint once to break the tiny adhesion at the contact
points** and the tail poses freely. That first flex is normal for every
print-in-place model, not a sign anything is wrong.

Prints flat on its belly exactly as modelled. ~174mm tall straight, ~120mm once
the tail is curled.

| Setting | Value | Why |
|---|---|---|
| Layer height | 0.15–0.20mm | 0.2 is fine; 0.15 gives cleaner joint gaps |
| Walls | 3–4 | 2 is where flexi tails snap on the first flex |
| Infill | 10–15% | More does not help; wall count and joint diameter do |
| Supports | **none** | The belly is flat and nothing needs propping |
| Plate | smooth or textured PEI | Flat belly, adhesion is easy |
| Material | PLA or PLA+ | PETG works but tends to weld joints — raise `clear` first |

**Do not scale this model down.** Joint clearance is 0.25mm per side and that is
already near the reliable floor for a 0.4mm nozzle. At 80% it becomes 0.20mm and
the tail starts fusing; at 60% it prints as one solid piece. Scaling UP is fine.
If you want a smaller seahorse, raise `clear` and reprint — that parameter
exists for exactly this.

## The joint

Ball-and-collar, designed and verified on its own before the animal was drawn
around it:

```
ball dia 5.8    clearance 0.25/side    neck dia 2.9    mouth relief 22°
pitch 8.7       collar wall 1.6        bead dia 9.5
```

* **Retention 0.42mm** — how far the collar must spread for a ball to escape.
  The tail holds together under normal handling; a determined pull will pop a
  bead off, and it clicks back on.
* **Swing 14° per joint, 11 joints = 154° of curl.** Measured on the finished
  decorated segment, not the bare joint — the bony ring and dorsal crest cost 2°.

Tail stiff or fused → raise `clear` to 0.30. Tail floppy → drop to 0.20. Either
way print a two-segment coupon first (`-D part=joint_test`) rather than
committing to the whole animal.

## Why it prints flat, and why that matters

Every neck's bending stress runs along the layer plane, which is the strong
direction in FDM. Standing the model up would put that same load across the
layer bonds — 4–5× weaker — and the tail would snap at the first bend. So the
tail curls in the print plane, which happens to be the plane a real seahorse
curls in. Nothing was given up for it.

## Posing

Print it straight; curl it afterwards. `-D pose=curled` is a preview pose for
renders only — never slice that version, the joints are rotated into each other's
clearance and it is not what should go on a plate.
