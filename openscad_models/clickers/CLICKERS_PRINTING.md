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

61 mm across, 26 mm tall with the cookie on.

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
- **Tin:** a rolled bead round the foot and another round the top edge, like a
  real tin, and pairs of white dots between the snowflakes.

**The lid screws on (2026-10-30).** Your first test print clicked fine, but
the lid sat loose. It now has a thread, about 1.6 turns, and screws down until
the switch plate sits on the tin exactly where it sat before. The switch, the
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
clicker, and the square opening under the lid filled in. 61 mm across and
60 mm tall with the cookie on. It holds 89 cm³: sweets, paper clips, a
folded gift card.

**You print two new parts.** The cookie and the switch come off the clicker
you already printed and go on the new lid. The clicker's tin isn't used.

| print | colours (AMS slot) | as it sits in the file | sliced, one colour |
|---|---|---|---|
| the canister | red 1, white snowflakes 2 | on its base | 51 min, 8.7 m, about 26 g |
| the closed lid | red 1, green holly 3, white snowflakes 2 | on the pod under it | 33 min, 6.4 m, about 19 g |
| the cookie (only if you need another) | as the clicker's | face up | as the clicker's |

**What's different:**
- **The canister** is the clicker's tin made tall and hollow: the same rolled
  beads at the foot and the top, the same lip, and three staggered rows of
  ten raised snowflakes. The OBC mark is engraved under the base.
- **The closed lid** is the clicker's lid, unchanged on top, with a pod
  under the switch plate. The switch's body and legs sit in a closed square
  pocket, so nothing in the tin reaches the switch, and from below it's solid.
  The pod's cone drops into the canister's mouth and seats on a matching ring
  inside it. That ring holds the lid; the lid lifts straight off.

**Put it together:** push the switch into the new lid from above, through the
cookie-shaped nest, until its clips snap under the plate. Press the cookie
onto the switch, then set the lid on the canister.

**Checked before it was pushed** (`gingerbread_tin/check_canister.py`, and
the same tools as the clickers, results in `gingerbread_tin/checks/`):
- **Fit:**
  - The lid rests on its seat. 0.1 mm lower it would be 17.7 mm³ into the
    canister, so it can't drop in.
  - Lifted 0.3 mm and slid sideways, it touches nothing, so it lifts off
    without binding.
  - The cookie clears the lid as on the clicker.
  - The switch's body and pins clear the pocket, and the pod is solid under
    the cutout.
- **Supports: none on either print**, after two fixes the slicer found:
  1. **A flat 1.0 mm ledge** round the cutout under the plate, for the
     clips to catch on, was a ceiling: 12,196 support moves. The pocket now
     closes in at a slope to the cutout instead, so the clips catch on its
     edge, where the plate is the 1.5 mm they expect.
  2. **At 45°, the slicer's own threshold**, that slope and the pod's cone
     still drew 11,524 moves. At 40° from vertical, none.
- **Product gate:**
  - The closed lid PASSES.
  - The canister reads FAIL on the wall check only: the raised snowflakes,
    0.9 mm strokes, as on the tin.
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
  these): tin 24 min + lid 22 min + cookie 11 min, about 31 g; jar 27 min + top
  16 min + gingerbread 20 min, about 35 g.

## What was checked before this was pushed

- **Fits, on the exported prints** (`check_clickers.py`). Each cap was checked
  at rest and at 1, 2, 3 and 4 mm of travel against both prints and the switch
  housing: 0 mm³ of overlap everywhere. The lid's spigot in the tin's lip is
  0 too, and so is the top's in the jar's. The switch's body, clips and legs
  fit in the lower print with 0 overlap. The plate is solid just outside the
  14 mm cutout and open just inside it. The socket is open where the stem goes
  and closed above.
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
- **Product gate:** the jar and the top PASS. The tin, the lid, the cookie and
  the gingerbread read FAIL on the wall check only. Every span under 1.2 mm
  was traced:
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
