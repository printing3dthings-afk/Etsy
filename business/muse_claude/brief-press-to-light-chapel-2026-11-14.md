# BRIEF — Press-to-Light Chapel (for Claude, from Benson; approved by Scott 2026-11-14)

## What it is
A Christmas village chapel lantern with one working secret: **press the steeple down and a faceted spinner inside rotates around the tea light, so the light moves** — patterns sweep across the windows instead of a static glow. Release the steeple, press again, it spins again. From the shelf it reads as a normal OBC chapel; the mechanism is the surprise.

Origin: Scott picked this from the Nov 14 MakerWorld top-liked design study (`business/muse_claude/research/2026-11-14-makerworld-top-liked-design-study.md`) — it borrows the HelixCore spinner's press-to-spin trick (printed helix converts a downward press into rotation) and puts it inside our strongest product class, a lit village building. It is also the planned Secret Switch Ep 002 subject and a future You Pick the Print reveal, so the reveal moment (press → spin → moving light) must read clearly on video from 1–2 m.

## Design requirements
- **Mechanism first, coupon before chapel.** Step 1 is a mechanism coupon only: helix driver + spinner + guide, sized to prove (a) a firm fingertip press on the driver produces at least one full spinner rotation, (b) the spinner turns freely after printing with NO post-processing beyond breaking it free, (c) 50 press cycles without binding or visible wear. Chapel geometry starts only after the coupon works on paper (G1) — Benson builds and Scott prints the coupon before the full design is modelled.
- **Return by geometry, never by matte-PLA flexure.** The Nov 14 study documents matte PLA losing elasticity (Mini Bag Clip successor warning). The return/reset must come from the helix geometry, gravity, or a cam — not a thin flexing spring in matte PLA. If a true spring proves unavoidable, flag it in FACTS.md as a named exception for Scott's call (PETG spring insert) — do not silently design one in.
- **Designed stop.** Travel needs a hard, designed end-stop both ways (HelixCore added one in its Jun 2026 update after field feedback). No relying on parts jamming.
- **Spinner:** faceted or windowed drum/sleeve around the tea light cavity; facets sized so rotation visibly modulates the light through the chapel's window panes. Spinner must be removable for tea-light access (light goes in from the base as usual).
- **Chapel body:** OBC village language (steeple, arched windows, snow roof acceptable), silhouette reads as "chapel" at thumbnail size. The steeple is the press surface — it must look like a steeple, not a button, and take a press without rocking the building (flat base, low centre of pressure).

## Standing OBC gates (unchanged)
- No supports anywhere. Flat base at z=0. Watertight.
- Walls ≥1.2 mm structural; window panes 0.8–1.0 mm with full-thickness frames; tea-light cavity ≥46 mm per light.
- Matte PLA, single colour for the body profiles (multicolour can come later); P1S plate fit required, A1 mini fit a plus.
- Profiles: Standard + Optimized (matte white), stock Bambu identities, ASCII filenames — built by Benson at G4 as usual.
- OBC mark placement verified correct-from-below on the actual mesh (per QC pipeline G1).
- Nothing public before G5 (Scott's physical print), per the QC pipeline.

## Deliverables from Claude
- Mechanism coupon: SCAD source + exported 3MF/STL + FACTS.md (every dimension and clearance named, with its source/rationale — helix pitch, spinner-to-guide clearance, driver travel, stop positions).
- On coupon pass: full chapel SCAD + exports + FACTS.md + the 5 standard renders.
- A short "how it works" section in FACTS.md a stranger could assemble from: press force expected, how the spinner comes out, what wears first.

## Open questions for Scott (route via Benson, do not block the coupon)
- Chapel size target: standard village scale (~120 mm tall) assumed unless Scott says otherwise.
- Sound: a soft click on press (clicker DNA) — nice-to-have only if it costs no reliability.

Status: G0. Next gate: G1 on the coupon.
