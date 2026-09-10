# Outlet Shelf — printing notes

Replaces a receptacle's cover plate with a shelf. One parametric file,
`outlet_shelf.scad`, two exported variants.

| | duplex | Decora / GFCI |
|---|---|---|
| fits | classic two-round-socket outlet | rocker / GFCI rectangle |
| fixing | one central 6-32 | two 6-32 at 3-13/16″ centres |
| on the wall | 120 w × 161 h × 65 deep mm | same |
| volume | 70.6 cm³ | 68.5 cm³ |
| time | **3h 26m** | **3h 23m** |
| supports | **none** — 0.00 cm² past 55° | same |

Filament weights the slicer quotes (62.0 g / 60.6 g) are at this profile's
**PLA** density of 1.24. Print this in PC FR and the real weight differs;
the volumes above are the number that does not move.

---

## Read this before printing one

This replaces a **listed electrical component**. Two things follow, and
neither is a matter of taste.

**1. Material.** Real wall plates carry a **UL 94 V-2** flammability rating.
PLA and PETG have no flame rating at all, and PLA softens at 55–60 °C while an
outlet under sustained load runs warm — it will creep. Print this in a
flame-rated filament. **Bambu PC FR is UL 94 V-0** (better than the V-2 the
part is replacing), 260–280 °C nozzle, 90–110 °C bed. The P1S is enclosed and
reaches both, though its 100 °C bed is the *bottom* of that range. PC needs
drying first — 80 °C for 12+ hours, per CLAUDE.md's filament table.

**A printed plate is not UL listed as an assembly, whatever it is made of.**
That is true of every printed outlet shelf on the internet and it stays true
here. Say it in the listing rather than implying otherwise.

**2. The cover screw does not carry the shelf, and that is by design.** That
screw is sized to retain a ~15 g plastic plate. Here the back of the part
bears flat against the wall for 104 mm below the screw, so the shelf's moment
resolves as a couple — compression into the wall low down, tension at the
screw. A 300 g load 40 mm out works out at about **1.1 N** on the screw,
roughly 110 grams of pull.

That is the reason the plate region runs the full standard 114.3 mm height
instead of stopping at the device: **the bearing area is the structure.** Do
not shorten it to save filament.

It does not hang on the outlet's *mounting* screws either, and it must never
be fitted to a loose or damaged receptacle — if the device rocks in the box,
fix that first.

---

## Dimensions

ANSI/NEMA WD-6, taken from published figures rather than recalled, and then
measured back out of the finished mesh:

| | standard | measured in the mesh |
|---|---|---|
| duplex opening | 34.13 × 28.58 mm | 34.54 × 29.00 (0.4 mm clearance, intended) |
| duplex socket centres | ±18.98 mm | ±18.98 |
| duplex fixing | one 6-32, centre | Ø3.8 at y = 0 |
| Decora opening | 33.30 × 66.70 mm | 33.70 × 67.15 |
| Decora fixing | 3-13/16″ centres | Ø3.8 at y = ±48.43 |
| plate coverage | 69.85 × 114.30 mm | 74 × 114.30 |

The plate zone is 74 mm wide against the 69.85 mm standard, so it covers about
2 mm past the old plate's edge on each side — enough to hide a paint outline.

Y = 0 is the **centre of the receptacle** throughout the model, because that
is where every one of these figures is quoted from.

## Print orientation

Back-flat, same as the wall charging shelf: the plate lies on the bed and the
shelf grows upward, so the build direction is the shelf's own depth. Every
visible surface prints as a side wall. Measured **0.00 cm² past 55°**, worst
face 49.1°, and zero gap fill in both slices.

The plate is **3.36 mm** (8 × 0.42), thicker than the wall shelf's 2.52,
because the screw countersink eats 1.84 mm of it and what is left still has to
be a plate. The countersink opens toward the room, which makes it an up-facing
cone in the print — no bridge.

## The plate is deliberately not latticed

The lower half is hex-latticed like the rest of the family; the plate zone is
not. The ring left around the device opening is only ~20 mm wide, and
perforating the part whose job is covering an electrical box to save three
grams is the wrong trade.

## Deck

The deck top sits at **64 mm below the receptacle centre**. A compact charger
in the *lower* socket reaches about 39 mm down, so that leaves 25 mm of clear
air above the deck. Anything shallower and the shelf stops being usable while
the outlet is actually in use, which is the one thing this product exists to
avoid — there is an assert in the .scad that fails the render if the deck is
raised far enough to cover the lower socket.

Otherwise it is the wall shelf's deck: 120 × 65, 8 mm rails and front lip,
24 mm cable slot with a peaked end, two toe stops 22 mm out so a standing
phone is captured rather than balanced, and the OBC mark engraved into the
front face of the lip.

## Two traps this model hit

**`center = true` on the opening cut.** `linear_extrude(height = plate_t + 2,
center = true)` spans −2.68 to +2.68, which leaves the top 0.68 mm of a
3.36 mm plate intact as a membrane right across the device opening. 16–22 cm²
of flat 90° overhang that rendered, gated watertight and sliced happily.

**Panels flush with the body's bottom edge** put the panel's boundary
collinear with the plate's along one line, and the shared edge tessellates into
zero-area slivers. They now stop 2.5 mm short. The wall charging shelf gets
away with a flush panel only because its 6 mm corner rounding pulls the
plate's bottom edge inboard of the panels entirely.
