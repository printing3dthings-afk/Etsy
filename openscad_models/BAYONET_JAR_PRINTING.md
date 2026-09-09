# Bayonet twist-lock jar — how to print it

Two parts, one plate. 50mm across, 45mm tall closed. `bayonet_jar.3mf` has
both already laid out and coloured.

| Object | Filament | Orientation |
|---|---|---|
| `base` | steel blue `#2E5C8A` | as loaded — open end up, flat bottom on the plate |
| `lid` | safety orange `#FF6B35` | as loaded — **already flipped, cap face on the plate** |

Both parts are single-colour objects; the colours above are just so the two
read apart on the plate. Change either freely — nothing about the mechanism
depends on them.

## v2 — what changed, and why

Three real defects on the first printed one, all fixed:

**The neck was flimsy.** The lock channel was cut through a 2.4mm wall to a
depth of 2.5mm — it went straight through. The neck was severed over three
33° arcs and the rim was held on by the webs between them. There is now an
internal collar through the lock zone: the channel bottoms out in solid
material with **1.75mm behind it**, and the collar itself is an uncut 360°
hoop, which makes the neck stiffer than the original wall ever was. The
collar's underside is a 45° cone so it prints without support.

**The lid rattled.** It was not a tolerance problem — the lid cap sat **7mm
clear of the jar rim** and the whole thing hung on three balls in oversized
channels. The cap now lands flat on the rim, and the lock channel descends
0.35mm across the twist so closing it draws the lid down onto that seat. At
the locked position the ball is against the channel ceiling and the cap is on
the rim, so there is **no free lift at all** — measured, not estimated.

**Tolerances.** Split into two numbers, because the two interfaces want
opposite things:

- **lock channel 0.25mm** — this is what you feel. Tight.
- **vertical entry 0.45mm** — nothing locks here, it only has to accept the
  ball. Left loose deliberately so a slightly tight print can never stop the
  lid going on.
- **skirt over the jar 0.25mm** — static sliding fit.

If the lid is stiff to turn on your first print, open `lock_clear` to 0.30 and
re-slice. If it still has any play, close it to 0.20. That is the one number
worth touching.

**The mark is now `OBC`.** The old `OnBrandCraftz` in Dancing Script at 1.8mm
was measured at **0.0mm of stroke width — 100% of it vanished under a single
0.42mm bead.** It could not print at any depth; it was never going to appear
on a finished part. `OBC` in Montserrat Black at 6mm measures 1.66mm of
stroke, just under four extrusions wide, and it is engraved 0.6mm into the
underside so it comes out of the first layer.

## Assembly

Push the lid straight down until the cap meets the rim, then twist about 25°
until it stops. It stops on its own — the channel ends just past the locked
position, so there is a defined stop rather than the lid continuing to spin.

## Supports

None, on either part. After flipping the lid there is 0.09 cm² past 55° on it
(three small ball undersides) and 1.26 cm² on the base, of which 0.74 is the
roof of the engraved mark and the rest is the lock channel ceilings — all
short internal bridges. Nothing needs help.

Do not print the lid the way it looks in the assembled preview. It is modelled
skirt-down because that is the only pose the fit can be checked in; printed
that way it would start a 20 cm² disc in mid-air. The `lid` object in the 3MF
is already flipped.
