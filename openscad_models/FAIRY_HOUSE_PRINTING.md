# Fairy House — printing notes

A toadstool-shaped fairy house, ~70mm x 69mm x 99mm tall, with an arched
door, a doorknob, a round window with a small flower box, a chimney with a
curling smoke wisp, a warty/spotted cap trimmed with a scalloped gill
fringe around the eave, a climbing vine with leaves winding up one side,
curling root tendrils at the foot, a small companion baby mushroom growing
against the base, and a hanging wood sign over the door reading "Jessee's
House". One piece, one file (`fairy_house.stl` / `.3mf`), fully hollow
through the house body with a solid floor and a solid cap — no assembly
required.

**v2 (2026-09-04): much more exterior detail, more fairy-themed** — added
the gill fringe, climbing vine + leaves, root tendrils, baby mushroom, and
chimney smoke on top of the v1 house (door/window/sign/chimney/dimples),
per Scott's request for more detail and more fairy theming. The vine
deliberately covers only the back ~225 degrees of the house, leaving the
door/window/sign side clear (Technique 31's negative-space principle — a
house wrapped in vine on every side reads busy, not charming).

## Verified before shipping
- Single watertight solid, 1 connected component (no floating pieces),
  confirmed by mesh connected-component analysis. This check has caught
  real bugs at every stage of this model: v1 had a set of disconnected
  door-groove slivers and a disconnected window-mullion sliver (both from
  decorative details sitting exactly flush with their host surface
  instead of overlapping it); v2's first pass had the root tendrils'
  spheres dipping to z=-0.37 (the sphere *center* was clamped to z>=0.4,
  but its own radius wasn't accounted for, so part of the sphere still
  sat below the floor) — caught by a bed-contact area check collapsing
  from ~2300mm2 to 47mm2, fixed by tying each tendril bead's height
  directly to its own radius instead of an independent curve.
- Wall thickness: 2.2mm through the house body (median wall overall 3.0mm
  including the solid cap/floor), well within this shop's printable range.
- Overhang: the flare from the house wall out to the cap's widest point
  rises at roughly 31 degrees from vertical — under this shop's 40-degree
  visible-surface target (Technique 35). The dome above that point is a
  normal self-supporting dome shape (radius shrinks as height increases),
  the same as every other dome/mushroom cap this shop has built.
- Floor sits flush at z=0 (checked directly on the mesh, not assumed) —
  the whole model prints flat on the bed with no auto-shift needed.

## Real things the slicer needs help with
- **The hanging sign has an open underside** — it's a small plank suspended
  on two support rods above the door, with nothing directly beneath it.
  Deliberate design, but the slicer will generate a small support there.
- **The gill fringe (roof eave) and vine leaves have small unsupported
  undersides too** — expected for dangly decorative bits at this scale
  (238mm2 total across the whole model, a small fraction of its total
  downward-facing area). Don't turn supports off entirely for this model;
  "support on build plate only" with tree/organic supports is enough to
  catch what these features actually need.

## Suggested settings
- 0.2mm layer height, 3-4 walls, 15-20% infill (gyroid, per this shop's
  own current default for a part with no single dominant load direction).
- PLA is fine if this stays indoor decor. If it's ever meant to actually
  live in a garden, print in ASA instead and add a drain hole in the roof
  overhang / any upward-facing ledges — see Technique 51's real UV-
  durability numbers (PLA is not viable outdoors at all).
- The maker's mark ("OnBrandCraftz") is engraved into the underside of
  the floor, out of sight in normal display.
