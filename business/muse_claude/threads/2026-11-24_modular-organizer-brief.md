Filed by Benson 2026-11-24 at Scott's direction. Claude expected active ~12:07 PM ET today.
Full brief follows, unabridged.

# Brief — Modular Desktop Organizer System (for Claude)
Filed by Benson, 2026-11-24, at Scott's direction. Claude expected active ~12:07 PM ET today.

## Reference (inspiration only — do NOT copy)
MakerWorld model 3204584, "Kribu-Krabu" modular desktop organizer:
https://makerworld.com/models/3204584
What it is: puzzle-interlocking modules (catch-all trays, phone stands, storage bins) that lock together without hardware; the interlocking joints double as exterior slots that hold pens/pencils/tools. Support-free, flat printing.

Scott's words: "We need something like this. A modular design that we can build attachments for. Need to use a different connection method. Not so much infill. Maybe stronger walls."

## The ask
Design OUR OWN modular desktop organizer system — a base platform with a defined connection interface, so we can keep releasing new attachments/modules for it over time. Original design throughout: no Kribu-Krabu geometry, name, or branding.

## Scott's requirements
1. **Different connection method** — NOT the puzzle interlock. Propose options (e.g. dovetail slide rail, snap-clip, magnetic, rail/track) with honest trade-offs.
2. **Strength from walls, not infill** — design the parts so they print strong at low infill (target ~8–12%): 3+ walls, ribbed/thickened load paths where needed, no reliance on dense infill.
3. **Per Scott's standing design rule: propose 4–5 genuinely different forms/connection directions FIRST — he picks one.** Do not build out a single direction before his pick.
4. House printability gates: no supports, flat base, watertight, walls ≥1.2mm, matte PLA, P1S bed (256mm), silhouette must read at thumbnail size.
5. Starter module set to scope with the system: base tray, phone stand, pen/tool holder, small bin — all on the one interface, so future attachments plug into the same standard.

## Deliverable at this stage
The 4–5 options (form + connection method + why), each with a quick render or sketch-level visual Scott can judge, plus your recommendation. Scott picks; full design + profiles follow his pick.

## Claude, 2026-11-24 3:28 PM: five options, with Scott to pick

Sketch renders of all five, with the joint in red:
`openscad_models/desk_modular/concepts/images/concept_sheet.jpg` on branch
`claude/new-session-o245bl`. The write-up is `openscad_models/desk_modular/OPTIONS.md`.
All five share a 40 mm grid and 2.0 mm walls at ~10% infill.

1. **Drop-in dovetail:** tails on one side, sockets on the other, drop the next one down. Rigid,
   no extra parts, but modules are handed.
2. **Butterfly keys:** the same half-pocket every 40 mm on every side; a bow-tie key joins two.
   Any module joins any side. Keys are printed flat, can be a contrast colour, and are their own
   SKU.
3. **Base grid:** a socket plate the modules stand in. The plate is a big print, and grid
   systems are everywhere.
4. **Back rail:** modules slide along one rail. A line only.
5. **Magnets:** the best feel, but hardware, a pause in every print, and a swallowing hazard.

**Recommended: 2.** It's one interface on every side, which is what an attachment system needs,
and its load runs through walls and the key's layers. After Scott picks: a joint coupon under
30 minutes (keys at 0.15 / 0.2 / 0.25), then the starter set from the brief. None of the
Kribu-Krabu geometry or its pen-slot joints is used.

## 2026-11-24 - Benson: Scott's pick — #2 Butterfly keys

Scott picked **#2 — Butterfly keys** (Claude's recommendation, from the five concepts in openscad_models/desk_modular/OPTIONS.md on the design branch).

Next, per Claude's OPTIONS.md plan:
- Design the real system on the butterfly-key interface: 40mm grid, the same half-pocket every 40mm on every side of every module, thickened boss at each pocket, 2.0mm walls, ~10% infill.
- FIRST deliverable is the fit coupon (under 30 min print): two wall sections with pockets + keys at 0.15 / 0.2 / 0.25 clearance, so Scott's print sets the fit before any module is built.
- Starter set after the coupon reads: base tray, phone stand, pen/tool holder, small bin.

House gates as briefed: no supports, flat base, watertight, matte PLA, P1S 256mm, thumbnail-readable silhouette. Original design only.

— Benson
