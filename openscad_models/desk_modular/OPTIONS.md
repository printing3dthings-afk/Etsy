# Modular Desktop Organizer: five ways to connect (2026-11-24)

Benson's brief (`business/muse_claude/threads/2026-11-24_modular-organizer-brief.md` on main),
from Scott: "We need something like this. A modular design that we can build attachments for.
Need to use a different connection method. Not so much infill. Maybe stronger walls."

Sketches only (`concepts/concepts.scad`, renders in `concepts/images/`): walls and fits are
indicative. Nothing is designed for real until Scott picks. All five share:
- **A 40 mm grid.** Every module is a whole number of units across (1×1, 2×1, 2×2), so every
  attachment fits every other.
- **Strength from walls.** 2.0 mm walls (five beads), thicker only where the joint is, at ~10%
  infill.

| | how it joins | for | against |
|---|---|---|---|
| **1 Drop-in dovetail** | Tails on one side, sockets on the other; the next module drops down onto them and stops on a 4 mm ledge. | No extra parts. Very rigid side to side. The tails are vertical, so they print with no overhang. | Modules are handed (tails one side, sockets the other), which limits layouts. Each fit needs a coupon. |
| **2 Butterfly keys** | The same half-pocket every 40 mm on every side; a small bow-tie key drops into two pockets to join them. | Any module joins any side, any way round. Keys print flat in minutes, carry load along their layers (the strong way), and can be a contrast colour: two-tone without an AMS. Replaceable. | A small part to lose. Each pocket needs a thickened boss in the wall. |
| **3 Base grid** | A plate of shallow sockets; modules stand in it on locating feet. | Easiest to rearrange. Modules never have to touch each other. | The plate is a big extra print and fixes the footprint. Grid-plate systems are everywhere, so ours would read as one more. |
| **4 Back rail** | A dovetail rail lies along the back; modules slide on from the end. | A neat straight line. Rails can be sold in lengths. | One line only, no 2-D layouts. To take out a middle module you slide others off. The slot's roof is a 14 mm bridge. |
| **5 Magnets** | 6×3 mm magnets pressed behind a thin skin, on every side. | The nicest feel; fastest to rearrange. | Hardware: 8 magnets a bin, a pause in every print to drop them in, polarity right in every pocket. Loose magnets are a swallowing hazard round children. |

## Recommendation: 2, butterfly keys
- **It's a different method from the puzzle interlock,** and one interface on every side of every
  module. That is what an attachment system needs: a new attachment only has to carry pockets at
  the grid spacing.
- **The load goes through walls and the key.** Each pocket is a thickened boss, and the key is
  printed flat, so a sideways pull runs along its layers, not across them.
- **The keys are a product of their own:** colour packs, and spares.

First step after a pick is a coupon, under 30 minutes: two wall sections with pockets, and keys
at 0.15, 0.2 and 0.25 clearance. That sets the fit before any bin is built.

## Starter set (on whichever interface Scott picks)
Base tray, phone stand, pen/tool holder, small bin, from the brief.
