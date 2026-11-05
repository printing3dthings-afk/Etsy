# Christmas clickers: Gingerbread Tin and Cookie Jar Peek-a-boo

2026-10-29. Two clickers for MakerWorld's "Click Into Celebration" contest
(the listing says submissions close **Nov 29, 2026**; check before you upload).
They are your picks 1 and 3: a gingerbread cookie you press down into a
Christmas tin, and a gingerbread man who pops out of a cookie jar and gets
pushed back in. Both click on a real keyboard switch. Our own designs, not
Clicker Factory remixes.

## You need one switch per clicker

A **plate-mount Cherry MX switch, or any MX clone** (Gateron, Kailh, Outemu).
Blue, or any other "clicky" switch, is the one that clicks loudly. Every switch
dimension is the dumpling clicker's, taken from Cherry's datasheet. Any of the
switch's four orientations fits.

## Gingerbread Tin (`gingerbread_tin/gingerbread_tin_clicker.3mf`)

62 mm across, 26 mm tall with the cookie on.

| print | colours (AMS slot) | as it sits in the file |
|---|---|---|
| the tin | red 1, white snowflakes and dots 2 | on its base |
| the lid | red 1 (and the holly berries), green holly 3, white snowflakes 2 | on its floor, which is the switch plate |
| the cookie | brown 4 (and the pupils), white icing 2, red cheeks, bow tie and middle gumdrop 1, green gumdrops 3 | face up |

Four filaments in total, one AMS: red `#B3262E`, white `#F4F1EA`, green
`#3E8E4A`, brown `#9A5B2E`. In one colour everything still reads, because all
the detail is raised.

**The detail (second pass, 2026-10-29):**
- **Cookie:**
  - Piped icing that's round on top, the way real icing sits. It was flat
    strips.
  - Eyes with brown pupils set off-centre, so they glance down at the smile.
  - A red bow tie, and gumdrops with sloped sides.
  - A softer baked edge: the top rolls over through 1.4 mm instead of 1.0.
- **Lid:** holly sprigs with red berries in the two corners above his arms,
  and four small white snowflakes round him. A 0.4 mm chamfer breaks the
  nest's edge.
- **Tin:** a rolled bead round the foot, like a real tin, and pairs of white
  dots between the snowflakes. (It had a second bead round the top edge until
  the seam change below.)

**Stronger thread and a hairline seam (2026-11-05).** After you printed the
canister you asked for the lid to sit with the smallest gap, and for threads
that won't break if the lid goes on crooked. This tin and the canister both
changed.

- **The gap:** the collar's top was flat, under the lid's sloping underside,
  so the gap opened to 3.4 mm at the outside. Now the collar's top slopes with
  the lid, 0.2 mm under it, out to a 1.3 mm flat at its outer edge, where the
  line shows about 1.9 mm.
  - **Why the flat:** run all the way out, the slope met the outside wall at a
    39° knife edge, under 1.2 mm for its top 1.5 mm. It was a real thin spot,
    and the product gate failed it. A 0.2 mm seam can only reach the outside
    on a knife edge: the lid can't print the flat underside that would close
    it. You chose the blunt edge.
  - **The stop:** the lid still stops on its floor, so the seam is the same
    however a print runs.
  - **The bead:** the rolled bead round the tin's top edge is gone. The lid's
    band now carries on flush from the seam, where it used to stand 0.6 mm
    proud.
- **The thread:** 4.0 mm pitch and 1.2 mm deep, where it was 2.7 and 0.7.
  - Each tooth is 3.7 mm thick at its root against 2.4, and 1.2 mm tall
    against 0.7.
  - The teeth grow outward, so the tin is 0.6 mm wider all round: 62 mm
    across.
  - The lid's wall between the cookie's nest and the thread root is 1.3 mm,
    0.1 over the floor, so the gate doesn't read the faceted nest at 1.1.
  - It's 1.1 turns now, against 1.6. The lid is the same height: the cookie
    sets it.
- **No guide ring on this tin:** its lid prints standing on its floor, so a
  ring under it can't print, and there's no height to spare above the floor
  without sinking the cookie.
  - Without one, the lid can tip 3.1° where its teeth come in.
  - Starting it a whole tooth out takes 3.9°.
- **Checked:**
  - Screwed down, nothing touches.
  - Pulled straight up 0.5 mm it hits the thread (31.9 mm³).
  - Turned back along the thread through 30–540°, it touches nothing.
  - The gate and fidelity read as before: 0 supports, the same known wall
    readings and snowflake tips.

**The wall gate (2026-11-05).** After the seam rework all five prints read
FAIL on the product gate's 1.2 mm wall check. Every span under 1.2 mm was traced
to where it is (`wall_regions.py`, the regions; `../../tools/product_gate.py`,
`wall_skipper()`, the rule).

- **Real thin spots, now fixed in the geometry:**
  - **the collar's 39° knife edge** (tin and canister): now a 1.3 mm flat, as
    above;
  - **the foot bead:** it was 0.8 mm tall at its edge, now 1.25;
  - **the canister's shelf tip:** a knife edge, now a 1.2 mm face;
  - **the canister's floor:** 0.8 mm over the OBC mark engraved under it, now
    2.0 mm thick, which leaves 1.2 over the mark;
  - **the lid wall:** by the cookie's nest, now 1.3, as above.
- **Not walls, so declared to the gate.** The gate leaves out a span only when
  its midpoint is inside one of these, and says how many it left out. Each
  has its own check:
  - **The raised colour detail.** Snowflakes, holly, icing, gumdrops and
    cheeks are each their own colour part. Their 0.6–1.0 mm strokes are the
    detail standard's sizes, not walls, and print fidelity checks every one
    at bead scale.
  - **The thread's teeth**, from crest to root over the thread's height. A
    tooth's axial width runs from 3.7 mm at its root to a 0.29 mm crest flat
    by design, and it's as strong as its root. The collar's wall outside the
    root (1.2 mm, held by an assert) and the lid's wall inside it (1.3 mm) are
    not in the band, and the gate still measures them.
  - **The cookie's switch socket post.** It's 5.6 mm across to ride into the
    MX switch's stem opening, round the standard 4.1 mm cross, so its wall at
    the arm tips is 0.6–0.7 mm. The switch fixes that, as on every MX keycap
    (a 9.8k-download FDM keycap measures 0.63), and it's the post on your
    working clicker.
- **What's left is the structure, and all five prints pass it:** the 1st
  percentile reads 1.23 mm (tin), 1.49 (lid), 1.80 (cookie), 1.21 (canister)
  and 1.30 (closed lid).
  - The tin's and canister's margins are slim because the collar's wall
    outside the thread root is a designed 1.2 mm, and it's measured.
- **Two side fixes on the way, both in the canister's switch pocket:**
  - The pocket's sloped top used to meet the plate cutout on exactly the same
    line. One export pinched that edge between four faces, so the lid wasn't
    watertight. Another left a 0.97 mm sliver of void under the plate, which
    the slicer propped with 539 support moves.
  - The slope now stops 0.05 mm short of the plate, and nothing coincides.
- **The tool:** `test_product_gate_wall_skip.py` checks that a declared region
  leaves out only what it declares. Without any, the gate's numbers are the
  same as before.

**The lid screws on (2026-10-30).** Your first test print clicked fine, but
the lid sat loose. It now has a thread, about 1.6 turns, and screws down until
the switch plate sits on the tin exactly where it sat before. (The thread
below is as it was then; see above for the 2026-11-05 thread.) The switch, the
cookie and the nest are unchanged.
- **Why a screw and not a snap:** a snap ring on a 61 mm tin with a 1.2 mm
  wall either cracks or lets go. The tin is round, with its snowflakes all the
  way round, so the lid doesn't need lining up.
- **The thread:**
  - 2.7 mm pitch, 0.7 mm deep, 0.2 mm clearance.
  - Its flanks are 35° from upright, not a standard thread's 60°, so neither
    part needs support.
  - Both ends are chamfered so it starts easily.
- **What I fixed on the way:** my first thread sat 1.4 mm further in. That
  left only 0.5 mm of lid wall where the cookie's hands and feet reach out in
  the nest, and the slicer propped it with 750 support moves. The thread now
  keeps 1.2 mm of wall to the nest and 1.2 mm in the tin's collar outside it.
  The .scad stops with an error if either gets thinner.
- **What changed on the outside:**
  - The tin's collar, which carries the thread, stands 2.4 mm taller, and the
    lid's sloped band is that much shorter.
  - The snowflakes moved up 1.6 mm, to stay centred on the taller wall.
  - The tin and the cookie are the same height overall.
- **The storage canister isn't affected.** Its closed lid is built on the old
  lid and still seats on the canister by its cone. I checked it exports
  identically, 0.07 mm³ apart.

**Put it together:** push the switch into the lid from above, through the
cookie-shaped nest, until its clips snap under the plate. Screw the lid onto
the tin, clockwise, until it stops; the switch's legs turn freely in the tin's
round well. Press the cookie onto the switch's cross. The nest is the cookie's own outline with 0.6 mm to spare, so
it guides him straight down even if you press his head or a foot.

## Gingerbread Tin Canister (`gingerbread_tin/gingerbread_tin_canister.3mf`)

2026-10-30, your ask: a tin that actually holds things, with the lid as the
clicker, and the square opening under the lid filled in. 62 mm across and
60 mm tall with the cookie on. It holds 88 cm³: sweets, paper clips, a
folded gift card.

**Changed after your print (2026-11-05):**

- **Seam and thread:** the lid sits on a 0.2 mm hairline seam and screws on a
  deeper, coarser thread, as on the clicker's tin above.
- **The guide ring:** a smooth ring, 10 mm tall, under the lid drops into a
  smooth bore in the mouth before the lid's teeth reach the canister's.
  - **Why so long:** on a 57 mm lid a short guide tips across its own
    diameter. A long one keeps the lid square: it can tip only 0.9° where the
    teeth come in, against the 3.9° that starts it a tooth out. So it can't
    cross-thread.
  - **The stop:** screwed down, the ring stands on a shelf at the foot of the
    bore, and the pod no longer touches the mouth.
- **In section:** `gingerbread_tin/images/canister_seam_section.png` shows the
  seam, the teeth and the ring cut through.

**You print two new parts.** The cookie and the switch come off the clicker
you already printed and go on the new lid. The clicker's tin isn't used.

| print | colours (AMS slot) | as it sits in the file | sliced, one colour |
|---|---|---|---|
| the canister | red 1, white snowflakes 2 | on its base | about 29 g, 58 min |
| the closed lid | red 1, green holly 3, white snowflakes 2 | on the pod and the guide ring under it | about 22 g, 37 min |
| the cookie (only if you need another) | as the clicker's | face up | as the clicker's |

**What's different:**
- **The canister** is the clicker's tin made tall and hollow: the same rolled
  bead at the foot, the same threaded collar, and three
  staggered rows of ten raised snowflakes. The OBC mark is engraved under the
  base.
- **The closed lid** is the clicker's lid, unchanged on top, with a pod
  under the switch plate. The switch's body and legs sit in a closed square
  pocket, so nothing in the tin reaches the switch, and from below it's solid.
  **It screws on (2026-11-03), like the clicker's lid,** with the same
  thread. Since 2026-11-05 it screws down until its guide ring stands on the
  shelf in the canister's mouth.

**Put it together:** push the switch into the new lid from above, through the
cookie-shaped nest, until its clips snap under the plate. Press the cookie
onto the switch, then screw the lid onto the canister, clockwise, until it
stops.

**Checked before it was pushed** (`gingerbread_tin/check_canister.py`, and
the same tools as the clickers, results in `gingerbread_tin/checks/`):
- **Fit (2026-11-05):**
  - Screwed down, the lid's ring rests on the shelf, touching nothing else.
    0.1 mm lower it would be 27.2 mm³ into the shelf, so it stops there.
  - Pulled straight up 0.5 mm, it hits the thread (31.9 mm³), so it can't lift
    off.
  - Where its teeth come in, the ring lets it tip 0.9°; starting a tooth out
    takes 3.9°.
  - The seam over the collar is 0.31 mm upright, 0.20 mm square to the
    slope, at every radius measured.
  - Turned back along the thread through 30–540°, it touches nothing.
  - As a control, turned the wrong way while rising, it collides.
  - The cookie clears the lid as on the clicker.
  - The switch's body and pins clear the pocket, and the pod is solid under
    the cutout.
- **Supports: none on either print**, after three fixes the slicer found:
  1. **A flat 1.0 mm ledge** round the cutout under the plate, for the
     clips to catch on, was a ceiling: 12,196 support moves. The pocket now
     closes in at a slope to the cutout instead, so the clips catch on its
     edge, where the plate is the 1.5 mm they expect.
  2. **At 45°, the slicer's own threshold**, that slope and the pod's cone
     still drew 11,524 moves. At 40° from vertical, none.
  3. **The screw lid's stop (2026-11-03).** I first stopped the lid on a flat
     ring inside the mouth. To pass through that ring, the pod had to be
     2.2 mm narrower than the lid. The lid prints standing on its pod, so its
     floor overhung all round: 9,349 support moves. Then the pod's cone ran up
     to the lid's edge and stopped in a matching cone in the mouth.
  4. **The guide ring (2026-11-05)** is as tall as the pod, so the lid prints
     standing on both, still with 0 supports. The shelf it stops on has a
     sloped underside.
- **Product gate (2026-11-05): both PASS**, with the thread's teeth and the
  raised snowflakes and holly declared, as for the clicker's tin above.
  - Before that, both read FAIL on the wall check. Part of it was real: the
    collar's knife edge, the shelf's tip, and the floor over the mark. Those
    are now fixed.
- **Print fidelity:**
  - Closed lid: no flags, the same result as the clicker's lid.
    - This took a fix. With a 1.2 mm pod floor, the pod lifted the lid 10.1 mm,
      which is half a layer off. Every detail on top then landed between
      layers, and the white snowflakes' tips dropped out: 25 flags.
    - A 1.3 mm floor makes the lift 10.2 mm, a whole 51 layers.
  - Canister: 30 flags, one per snowflake, 0.07 mm³ each. It's the round tip
    of each downward arm, which comes out about a quarter-millimetre short;
    you won't see it. The tin's 10 flags are the same kind, on its upward
    tips.
- **Fragility:** 0 high, 0 watch on both.
- **Not tested on the printer yet.** The clip catch is the one part I'd watch.
  - If the switch doesn't stay snapped in, a drop of glue under the plate's
    edge holds it.
  - Or tell me, and I'll open the pocket.

Renders: `gingerbread_tin/images/canister_{front,three_quarter,top}.png`,
from the real exported parts, assembled. They're design-review renders, not
photos.

## Cookie Jar Peek-a-boo (`cookie_jar/cookie_jar_clicker.3mf`)

50 mm across, 72 mm tall with him popped up.

| print | colours (AMS slot) | as it sits in the file |
|---|---|---|
| the jar | mint 1, white label 2, red COOKIES 3 | on its base |
| the top (shoulder, neck, rim) | mint 1, red rim 3 | on its floor, which is the switch plate |
| the gingerbread | brown 4, white icing 2, red cheeks and buttons 3 | standing on his plunger |

Four filaments: mint `#A9DCC8`, white `#F4F1EA`, red `#B3262E`, brown
`#9A5B2E`. The label is a flush colour panel, so in one colour it disappears;
the COOKIES letters are raised and still read.

**Put it together:** push the switch into the top from above, down the neck,
until it clicks under the plate. Set the top on the jar. Drop him in: the
plunger rides in the neck, and the socket under it goes onto the cross. At rest
his feet sit 1.2 mm below the rim; pressed, he drops 4 mm into the jar.

## Print settings, both

- PLA, 0.20 mm layers, 0.4 nozzle, **supports off**, the orientation in the
  file. Every print was sliced with supports on and needed none.
- **Don't scale.** The switch fit is in millimetres.
- If the cap won't press onto the switch, print the loose one:
  `gingerbread_tin_clicker_loose_cap.3mf` or `cookie_jar_clicker_loose_cap.3mf`.
  It opens the socket 0.1 mm, the same two-step ladder the dumpling clicker
  ships.
- One colour, from the slicer I check with (Bambu Studio's AMS purges add to
  these): tin 25 min + lid 24 min + cookie 11 min, about 32 g; jar 27 min + top
  16 min + gingerbread 20 min, about 35 g.

## What was checked before this was pushed

- **Fits, on the exported prints** (`check_clickers.py`). Each cap was checked
  at rest and at 1, 2, 3 and 4 mm of travel against both prints and the switch
  housing: 0 mm³ of overlap everywhere. The tin's screwed-down lid is 0
  too, and so is the jar's top in the jar. The switch's body, clips and legs
  fit in the lower print with 0 overlap. The plate is solid just outside the
  14 mm cutout and open just inside it. The socket is open where the stem goes
  and closed above.
- **The tin's screw lid (2026-10-30):**
  - Pulled straight up 0.5 mm, it hits the tin's thread (15.5 mm³), so it
    can't lift off.
  - Turned back along the thread through 30–540°, it touches nothing, so it
    unscrews.
  - As a control, turned the wrong way while rising, it does collide. So the
    zeros come from the thread's path, not from a lid that clears the tin
    anyway.
- **Supports: none, on all six prints.** That took three fixes, each found by
  the slicer:
  1. **The bases are two prints, split at the switch plate.** First, each base
     was one print with the plate as a ceiling over the switch's well, as on
     the dumpling clicker. The slicer propped it: 2,168 support moves under
     the tin's plate. Now the plate is the floor of the upper print, flat on
     the bed, and the lower print is an open cup. Run through the same gate,
     the **dumpling clicker's basket needs 10,122 support moves under
     its plate.** It was "verified" before the gate existed. Worth a look,
     after Christmas.
  2. **The socket's ceiling is peaked.** Flat, the slicer put support inside
     the cross socket, where it could never be cleaned out. Each arm now ends
     in a 60° gable, which leaves the stem's stop where it was.
  3. **The gingerbread man's shoulders sit inside his body.** Bulging out, they
     needed 937 support moves.
- **Product gate:** the jar and the top PASS. Since 2026-11-05 the tin, the
  lid and the cookie PASS too, with their thread, socket and raised detail
  declared ("The wall gate" above); the gingerbread still reads FAIL on the
  wall check only. Every span under 1.2 mm was traced (the tin's and lid's
  readings below are from before 2026-11-05):
  - **Since the screw lid, 0.0 on the tin and the lid:** the gate's straight
    rays catch the thread's teeth side-on. It's the thread, not a wall.
    Outside the thread the readings are the raised detail below. The real
    walls either side of the thread are held at 1.2 mm by asserts in the
    .scad.
  - **0.6–0.9 mm:** the raised detail. That's the snowflake and holly strokes,
    plus the piped icing, whose rounded tops narrow to 0.58 mm (still over a
    bead). It's raised detail, not walls.
  - **0.6–0.7 mm:** the socket post, measured at the cross's arm tips. It's the
    standard MX keycap wall; a 9.8k-download FDM keycap measures 0.63.
  - **0.6–1.0 mm:** the islands inside the engraved B of the OBC mark, 0.8 mm
    tall on the floor.
- **Print fidelity** (`tools/print_fidelity.py`, every colour part). There are
  no flags on five prints. On the tin there are 10, each 0.04 mm³: the one top
  layer at the round tip of each upward snowflake arm, thinner than a bead.
  Each comes out about 0.2 mm shorter, which you won't see. The first pass of
  the new detail had 35, where the lower arms ran into the new foot bead; the
  flakes were resized to clear it.
- **Two bugs the checks caught in the detail pass:** the cookie's top layer
  had vanished: the gate counted 11 bodies and the slicer 5,522 support moves.
  The edge formula took the square root of a number that rounding pushed just
  below zero, so that layer came out empty. And the lower snowflake arms ran
  into the foot bead, as above. Both are fixed, and the checks above are on
  the fixed parts.
- **Fragility** (`tools/fragility.py`): 0 high, 0 watch on all six.
- **Maker's mark:** OBC engraved under the tin and the jar. The gaps between
  the letters were opened 0.15 mm so the walls they leave are over the gate's
  1.2 mm floor.

## Renders

`gingerbread_tin/images/tin_{front,three_quarter,top}.png` and
`cookie_jar/images/jar_{front,three_quarter,top}.png` were rendered in Blender
from the real exported parts, assembled. They're design-review renders, not
photos. For the contest page, photos of the real prints will do better.

## Rebuilding

`./build.sh [tin|jar]` exports every part (OpenSCAD's CGAL, one at a time),
the canister and closed lid with the tin. `python3 gingerbread_tin/check_canister.py`
checks the canister's fits; `python3 render_clickers.py canister --views` renders it.
`./ship.sh tin|jar` runs the fit check, gate, fidelity and fragility, and
writes the 3MFs. `python3 render_clickers.py tin|jar --views` renders. The
STLs aren't committed; the 3MFs hold every part.
