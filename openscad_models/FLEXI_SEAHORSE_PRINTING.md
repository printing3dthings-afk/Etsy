# Flexi seahorse — how to print it

> **⚠️ DO NOT PRINT THIS FILE YET — the joints will come out fused (2026-09-02).**
>
> Sliced in PrusaSlicer at 0.2mm layers with a 0.4mm nozzle and the whole tail
> comes out as **one connected island of material** through every layer from
> z=2.6 to z=5.8 — the band containing every ball. It would print as a solid
> stick, not an articulated animal.
>
> This was invisible to every check that had been run on it: the mesh is
> genuinely 10 separate solids, the gap really is 0.25mm, and the renders look
> right. The failure only appears in the toolpaths.
>
> **Cause is the socket SHAPE, not the clearance.** A sphere inside a spherical
> cup leaves a crescent-shaped void that is thinner than one extrusion
> everywhere except the single tangent point, so the slicer bridges it. Turning
> off gap-fill and thin-wall detection changes nothing — it is geometry, not a
> setting. Real flexi models use a rounded-rectangle *slot* socket (wide in the
> swing direction, tight only top and bottom); sliced the same way, a slot
> socket with an even smaller 0.175mm clearance comes out cleanly separated.
>
> Fix is to replace the spherical cup with the measured slot socket
> (`.claude/skills/3d-print-design/SKILL.md`, Techniques 42–44) and re-verify by
> slicing, not just by counting mesh components.


One file, one part, no supports, no assembly. It comes off the plate already
articulated: **flex each joint once to break the tiny adhesion at the contact
points** and the tail poses freely. That first flex is normal for every
print-in-place model, not a sign anything is wrong.

Prints flat on its belly exactly as modelled. ~180mm tall straight, ~120mm once
the tail is curled.

| Setting | Value | Why |
|---|---|---|
| Layer height | 0.15–0.20mm | 0.2 is fine; 0.15 gives cleaner joint gaps |
| Walls | 3–4 | 2 is where flexi tails snap on the first flex |
| Infill | 10–15% | More does not help; wall count and joint diameter do |
| Supports | **none** | The belly is flat and nothing needs propping |
| Plate | smooth or textured PEI | Flat belly, adhesion is easy |
| Material | PLA or PLA+ | PETG works but tends to weld joints — raise `clear` first |

**Do not scale this model down.** Joint clearance is 0.25mm per side. That was
described here as "near the reliable floor for a 0.4mm nozzle" — which was the
wrong diagnosis: the number was compensating for a socket shape that does not
slice at any clearance. See the warning at the top. At 80% it becomes 0.20mm and
the tail starts fusing; at 60% it prints as one solid piece. Scaling UP is fine.
If you want a smaller seahorse, raise `clear` and reprint — that parameter
exists for exactly this.

## The joint

The joints are **carved, not built**. The whole seahorse is sculpted as one
continuous solid and each joint is a ring-shaped cutter subtracted from it —
which is how the good flexi models are made, and why the skin stays unbroken
and the joint reads as a line rather than a step between beads.

```
ball dia 5.8    clearance 0.25/side    cone angles 37 / 55 deg
pitch 10.0      9 joints               narrowest neck dia 3.7
```

* **Retention 0.33mm** — how far the collar must spread for a ball to escape.
  It holds under normal handling; a determined pull pops a joint, and it clicks
  back on.
* **Swing 18° per joint, 9 joints = 162° of curl**, measured on the real joint.

The two cone angles are the design: their 18° difference IS the swing, and the
outer one sets retention. Give both cones the same angle and the joint binds at
about 4° no matter how much clearance you give it.

Tail stiff or fused → raise `clear` to 0.30. Tail floppy → drop to 0.20. Print
a one-joint coupon first (`-D part=joint_test`) rather than committing to the
whole animal.

## The OBC medallion

A raised oval plate on the left flank with OBC standing 1.0mm proud of it. It
prints face-up with no support, and it is the only feature that adds to the
model's thickness.

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
