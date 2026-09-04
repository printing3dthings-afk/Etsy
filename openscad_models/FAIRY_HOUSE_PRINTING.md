# Fairy House — printing notes

A toadstool-shaped fairy house, ~65mm diameter x 90mm tall, with an arched
door, a doorknob, a round window with a small flower box, a chimney, a
warty/spotted cap, and a hanging wood sign over the door reading
"Jessee's House". One piece, one file (`fairy_house.stl` / `.3mf`), fully
hollow with a solid floor and a solid cap — no assembly required.

## Verified before shipping
- Single watertight solid, 1 connected component (no floating pieces),
  confirmed by mesh connected-component analysis after two real bugs were
  found and fixed that way (a set of disconnected door-groove slivers, and
  one disconnected window-mullion sliver — both from decorative details
  sitting exactly flush with their host surface instead of overlapping it).
- Wall thickness: 2.2mm through the house body (median wall overall 3.0mm
  including the solid cap/floor), well within this shop's printable range.
- Overhang: the flare from the house wall out to the cap's widest point
  rises at roughly 31 degrees from vertical — under this shop's 40-degree
  visible-surface target (Technique 35). The dome above that point is a
  normal self-supporting dome shape (radius shrinks as height increases),
  the same as every other dome/mushroom cap this shop has built.

## One real thing the slicer needs help with
**The hanging sign has an open underside** — it's a small plank suspended
on two support rods above the door, with nothing directly beneath it. This
is a real, deliberate design (Technique 51-adjacent whimsical detail), but
it means the slicer will generate a small support structure under the sign
during slicing. That's expected and normal — just don't turn supports off
entirely for this model, or set "support on build plate only" if using
tree/organic supports so it only builds what the sign actually needs.

## Suggested settings
- 0.2mm layer height, 3-4 walls, 15-20% infill (gyroid, per this shop's
  own current default for a part with no single dominant load direction).
- PLA is fine if this stays indoor decor. If it's ever meant to actually
  live in a garden, print in ASA instead and add a drain hole in the roof
  overhang / any upward-facing ledges — see Technique 51's real UV-
  durability numbers (PLA is not viable outdoors at all).
- The maker's mark ("OnBrandCraftz") is engraved into the underside of
  the floor, out of sight in normal display.
