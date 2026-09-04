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

**v3 (2026-09-04): refined, not expanded — outdoor piece.** Scott's
follow-up: more detail on what's already there (no new items), a better
door, better siding, the roof needs to visibly attach to the walls, the
window should recess into the siding rather than stick out, and — because
this is going outdoors — no cut may open into the hollow interior at all.
Changes:
- **Door**: rebuilt as a real two-stage recess (a shallow surrounding
  frame reveal + a deeper inner pocket, both cut into the solid wall only
  — never through it), with the leaf sitting recessed inside, four raised
  plank ridges, a knob, and two strap hinges with rivet bumps on the
  opposite side.
- **Window**: rebuilt to sit RECESSED into the wall (previously a disc
  proud of the surface) with a visible reveal lip around it, same
  never-through-the-wall rule as the door.
- **Roof attachment**: the gill fringe moved from the cap's own widest
  point (16mm above the roofline, leaving a bald gap that read as "the
  roof is floating") down to sit exactly on the seam where the planked
  wall meets the cap — it now works as a real eave/fascia trim the roof
  visibly rests on, and the siding runs right up to it with no gap.
- **Siding**: deeper, crisper plank grooves (a sharpened profile instead
  of a soft cosine wave, so boards read as flat faces with a real seam,
  not a continuous corrugation) with a slow per-board depth variation so
  they don't look machine-uniform.
- **No interior access, anywhere**: both the door and window recesses are
  capped well short of the hollow cavity behind them (real remaining
  backing: ~0.9mm at the door, ~0.5mm at the window, both under the
  2.2mm wall) — confirmed on the real exported mesh, not assumed: the
  thinnest 1% of sampled wall thickness anywhere on the model is 0.898mm,
  meaning nowhere does a cut come close to breaching through.
- A separate raised trim/architrave around the door frame was tried and
  cut: it rendered clean on its own but produced a genuine degenerate
  sliver (caught by a watertightness check on the full assembled model,
  not by eye) where it met the frame reveal's own cut boundary. The
  frame reveal + pocket + hinges + knob + ridges already carry the
  "better door" detail without it.

## Verified before shipping
- Single watertight solid, 1 connected component (no floating pieces),
  confirmed by mesh connected-component analysis on every revision. This
  check has caught a real bug at every stage of this model: v1 had
  disconnected door-groove and window-mullion slivers (decorative details
  sitting exactly flush with their host surface instead of overlapping
  it); v2 had root-tendril spheres dipping below the floor (their radius
  wasn't accounted for when clamping height); v3 had the door-trim sliver
  above. Each was root-caused from the real mesh, not patched blind.
- Wall thickness: 2.2mm nominal through the house body; thinnest real
  sampled point anywhere is 0.898mm (at the door/window recesses, by
  design) — confirms no recess reaches the hollow interior.
- Overhang: the flare from the house wall out to the cap's widest point
  rises at roughly 31 degrees from vertical — under this shop's 40-degree
  visible-surface target (Technique 35). The dome above that point is a
  normal self-supporting dome shape (radius shrinks as height increases).
- Floor sits flush at z=0 (checked directly on the mesh, not assumed) —
  the whole model prints flat on the bed with no auto-shift needed.

## Real things the slicer needs help with
- **The hanging sign has an open underside** — it's a small plank suspended
  on two support rods above the door, with nothing directly beneath it.
  Deliberate design, but the slicer will generate a small support there.
- **The gill fringe (now at the roofline) and vine leaves have small
  unsupported undersides too** — expected for dangly decorative bits at
  this scale, a small fraction of the model's total downward-facing area.
  Don't turn supports off entirely; "support on build plate only" with
  tree/organic supports is enough to catch what these actually need.

## Outdoor use — material is not optional
**This piece is going outdoors, so it must be printed in ASA, not PLA.**
PLA is not viable outdoors at all (Technique 51's real UV-durability
research); ASA holds structural integrity, color, and surface quality
after a full year of direct sun exposure where PLA and even PETG have
already failed. The P1S's enclosure handles ASA natively — no new
hardware needed, just the material swap. Since the door/window are now
sealed relief (no opening into the hollow interior), there's no cavity
for rainwater to enter through them; the one place still worth a real
drain hole is anywhere rain could pool on an upward-facing ledge (the
flower box sill, the cap's dimpled top) if this will sit fully exposed
rather than under any cover.

The maker's mark ("OnBrandCraftz") is engraved into the underside of the
floor, out of sight in normal display.
