# Request: MakerWorld spec cards (gallery images, not covers)

**Started by:** Claude, 2026-11-20 (content-ramp thread).

**Where it goes:** one gallery image per MakerWorld model page, 1600 × 1200 (4:3). **Never the
cover:** since Nov 19, MakerWorld wants the cover to match the real print and at least three
real-print photos per page. A card adds to the photos; it doesn't replace any.

**What it must show:** print time, filament, size, colours by AMS slot with grams each, and the
slicer settings. Every figure is read from the model's own `.gcode.3mf`, so the card matches
the file it's published with. The render on the card is labelled "Design-review render, not a
photo". The card says nothing about free or paid: that's Scott's call per model.

**First three:** `openwork_name_ring_claude.png`, `snow_globe_name_ornament_claude.png`,
`gap_gauge_claude.png`. Benson, these match **my** slices. If a page carries your profile, the
card must be rebuilt from your file (`spec_card.py` takes any `.gcode.3mf`), or left off.

**Made with:** `business/social/makerworld_cards/spec_card.py` (Claude branch `316e3f1`).
