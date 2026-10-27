# Multipart line — how each keeper would be designed

2026-10-27. A plan, not a model: nothing is written in OpenSCAD until Scott
has seen the forms for that product (CLAUDE.md, new 3D print designs).

## What every product shares

- **One part, one colour.** The colour comes from printing each part in its
  own filament, not from paint or the AMS, so any single-colour P1S can make
  the full-colour product.
- **No supports, ever.** Each part is drawn in the pose it prints in, flat
  face down. Where the shape won't allow it, the part is split, never
  propped.
- **Fits from a test plate first.** One small plate of coupons, printed on
  Scott's P1S before any product, sets the real numbers: a thread pair, a
  ball-and-socket pair, a gear pair, a detent wheel and a snap tab, each at
  three clearances. The products are then drawn at the clearances that worked,
  not at a guess. Starting values: 0.2–0.3 mm for slides, threads and joints,
  about 0.5 mm for snaps (`data/knowledge_base/3d_printing_expertise.md`).
- **Every gate on every part**: product gate, print fidelity, fragility, the
  slicer finding no supports. Plus a fit check of the parts as assembled: no
  two overlapping, the moving ones turning through their whole travel.
- **Proven mechanisms, not invented ones.** Gears, threads and hinges come
  from BOSL2 (vendored), which already gets their geometry right.

## 19 · Nesting Characters

- **Form:** 5 figures, about 90, 72, 56, 42 and 30 mm tall, each a rounded
  kawaii body with ears or a hat; the smallest is solid.
- **Mechanism:** a printed trapezoid thread at each waist (BOSL2), pitch
  about 2.5 mm, one and a half turns, so it closes with a twist and the faces
  line up when tight.
- **Printing:** the bottom half stands on its flat base, opening up. The top
  half prints upside down on its rim, and its hollow is a pointed dome
  inside, steep enough to need no support. Rounded heads stay rounded, since
  the flat print face is the rim, not the head.
- **Detail:** faces and clothing in relief, readable in one colour.
- **The hard part:** five threads that all close with the faces aligned.
  Solved by starting each thread at the same angle relative to the face.
- **Sells as:** a set of 5 in five colours; themes later (cats, frogs,
  seasons).

## 9 · Candy Dispenser

- **Form:** a round base with a coin-op look, a dome on top, a knob on the
  front and a little flap door below it.
- **Parts:** base, dispensing wheel, knob and shaft, flap door, dome, fill
  cap. Six parts, 3–4 colours.
- **Mechanism:** a wheel with one pocket sized to the candy turns under the
  dome. At the bottom of each turn the pocket lines up with a chute, and one
  candy drops to the door. The knob has a printed detent, so each click is
  one turn.
- **Candy size is a choice that changes the wheel:** 25 mm gumballs, or
  smaller candy like Skittles or M&Ms. The plan is one base with swappable
  wheels.
- **Dome:** printed in translucent or clear PETG, so the candy shows, held on
  with a twist-lock bayonet.
- **Honest limit:** printed plastic isn't certified food-safe, so the listing
  says to use wrapped candy, or the dome is printed in food-safe PETG and
  says so. Nothing claimed that isn't true.

## 2 · Perpetual Desk Calendar

- **Form:** a low stand with three windows, DAY / DATE / MONTH, character ears
  on top, a name on the base.
- **Mechanism:** four drums on one printed axle: day of week (7), date tens
  (0–3), date ones (0–9) and month (12). Each drum clicks into place on a
  printed flex spring, so it stays put and lines up in its window.
- **Printing:** drums stand on end, their numbers raised on the curved face.
  Raised text on a vertical face prints clean and reads in one colour; the
  window frame contrasts as a second colour.
- **The hard part:** a detent strong enough to hold but not wear out. The
  spring's thickness comes from the test plate.

## 8 · Articulated Creature Kit

- **Form:** the first species is a kawaii dragon, about 200 mm long: head,
  neck, 8–10 body segments, legs and a tail tip.
- **Mechanism:** ball-and-socket snap joints, every segment ball on one end
  and socket on the other. The socket is split by slits so it flexes over the
  ball and grips it, posable but not floppy.
- **Printing:** each segment stands with its ball up and its socket open
  side down on the plate, so the socket's inside needs no support; the
  socket's mouth is chamfered so it prints and snaps cleanly.
- **Colour:** alternating segments in two or three colours, belly a third.
- **Later species reuse the same joint:** axolotl, cat, snake.
- **The hard part:** the grip. Too loose flops, too tight cracks. Set from
  the test plate.

## 5 · Hand-Crank Kinetic Toy

- **Form:** a round stage with a crank at the side. Under it, a gear train;
  on it, a cat and a fish circling, the cat slowly catching the fish and
  falling back again.
- **Mechanism:** two arms on concentric shafts driven by gears with nearly
  the same ratio (say 36:12 and 35:12 via an idler), so one arm gains on the
  other a little each turn. That's the chase. The crank turns a bevel or
  crown gear into the train.
- **Printing:** all gears print flat (BOSL2 spur gears, module about 1.5 mm,
  a little backlash). Shafts are printed pins with snap retainers.
- **The hard part:** smooth turning with no binding. Gear backlash and
  shaft clearance are set from the test plate.

## Order

1. **The test plate:** threads, ball joint, gear pair, detent and snap at
   three clearances. Scott prints it once; every product after uses what
   worked.
2. **Nesting Characters:** simplest mechanism, fastest win.
3. **Candy Dispenser.**
4. **Perpetual Calendar.**
5. **Creature Kit.**
6. **Kinetic Toy:** the most moving parts, last.

For each product: 4–5 forms shown as renders, Scott picks, then the model,
the gates, the fit check, colour and as-printed renders, and the 3MF with
its parts on plates.
