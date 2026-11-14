# New design briefs: Press-to-Light Chapel, Pocket Top, Gear Heart clips (Brief E)

## 2026-11-14 11:19 ET - Claude

Benson, all three are received. My must-fixes and the plan for each:

**Before any modelling, for both new products: Scott picks the form first.** CLAUDE.md,
"Starting a NEW 3D print design": every new product starts with 4–5 genuinely different
formal approaches, then Scott picks one. "Approved by Scott" covers the concept and the
mechanism, not the form. The mechanism coupons can come first, because they test a joint,
not a product's look. So the order is: coupon, approaches for Scott, his pick, full design.

**Press-to-Light Chapel**
- **Must fix: "return by geometry, gravity or a cam" doesn't lift a pressed steeple.**
  Gravity pulls the steeple *down*. Once pressed, something has to push it back *up*, and
  a helix or a cam only converts motion; it doesn't store any. Without a spring, the steeple
  stays down until a finger pulls it up. Three honest options for Scott: (a) a separate
  spring part in PETG or TPU, which the brief already allows as a named exception;
  (b) a lift-then-drop design, where the steeple is lifted and its own weight drives the
  spin on the way down, so gravity does the work; (c) a twist instead of a press. I'll
  test (b) on the coupon, because it keeps matte PLA and no spring, and bring (a) as the
  fallback.
- **Must fix: LED tea lights only.** A spinning PLA drum close to a flame is a fire risk.
  FACTS.md and the page will say "battery LED tea light only".
- **Suggestion:** the drum sits inside the light chamber, so the ≥46 mm floor must be
  measured *inside* the drum, not inside the walls. The chapel will be wider than a static
  one. I'll give the true footprint at G1.

**Pocket Top**
- **Must fix: small parts.** A 3-part top under 5 g has parts that come apart and are
  small. For under-3s that's a choking hazard. The brief only checks "once assembled", and
  snap-together means it won't always be assembled. FACTS.md and the page need "Not for
  children under 3: small parts". The coupon should also check whether each part clears the
  small-parts test size (I'll name the gauge and its source in FACTS.md, not from memory).
- **Suggestion:** 30 s from 5 g is a target to test, not a promise. I'll model the spin from
  rim mass and tip radius and state the expected range. "Ours spun 41 seconds" goes on a
  post only after Scott times a real print.

**Brief E — Gear Heart clips (snapped)**
- Agreed: a fracture, so the fix is strength first. That means more material at the base
  and finger roots, no sharp internal corners, and layer lines not across the flex. Then a
  clip coupon before a full heart reprint. The +0.20 mesh stays as is. The Sjack7 page's
  "not yet test-printed" line is now stale. When the fix lands, the page should say
  "mesh tested, clips v2".

**Order** for Claude's next working session with Scott: Brief A (mirrored text, takedown
risk), then Brief E (Gear Heart clips, already in the shop privately), the Pocket Top snap
coupon, the chapel lift-and-drop coupon, then Briefs D, C and B. The two coupons are small,
so I can deliver both quickly; the full designs wait for Scott's form picks.

**Housekeeping:** please file new briefs as threads (`threads/<date>_<name>.md`). The
loose `brief-*.md` files at the top of the folder aren't on the list the scheduled runs
check, so I only found these by chance.

## 2026-11-14 11:39 ET - Claude - Scott's answers

Scott decided just now:
1. **Chapel return: lift-and-drop first.** The steeple is lifted and its own weight drives
   the spin on the way down: matte PLA, no spring. A separate PETG spring part is the
   fallback, only if the lift-and-drop coupon fails.
2. **Photo gear: items 1–3 only** from Part 2 of `briefs-overnight-2026-11-13.md` (the
   light panel, the grey seamless backdrop, the mini tripod). Scott buys them himself.
   Items 4–12 are parked. Benson: please still send the building order for Claude's
   render sets, which are a separate thing.

The design work (Briefs A and E, the two coupons) happens in Scott's design session with
Claude ("Get going"), not in these scheduled runs.
