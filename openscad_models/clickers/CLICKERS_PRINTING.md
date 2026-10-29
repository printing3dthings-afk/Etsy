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
| the tin | red 1, white snowflakes 2 | on its base |
| the lid | red 1 | on its floor, which is the switch plate |
| the cookie | brown 3, white icing 2, red cheeks and gumdrops 1, green gumdrop 4 | face up |

Four filaments in total, one AMS: red `#B3262E`, white `#F4F1EA`, brown
`#9A5B2E`, green `#3E8E4A`. In one colour everything still reads, because the
icing, gumdrops and snowflakes are all raised.

**Put it together:** push the switch into the lid from above, through the
cookie-shaped nest, until its clips snap under the plate. Set the lid on the
tin; the switch's legs drop into the tin's well. Press the cookie onto the
switch's cross. The nest is the cookie's own outline with 0.6 mm to spare, so
it guides him straight down even if you press his head or a foot.

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
- **Product gate:** the lid, the jar and the top PASS. The tin, the cookie and
  the gingerbread read FAIL on the wall check only. Every span under 1.2 mm
  was traced:
  - **0.9 mm:** the piped icing lines and the snowflake strokes, two beads
    wide by design. They are raised detail, not walls.
  - **0.6–0.7 mm:** the socket post, measured at the cross's arm tips. It's the
    standard MX keycap wall; a 9.8k-download FDM keycap measures 0.63.
  - **0.6–1.0 mm:** the islands inside the engraved B of the OBC mark, 0.8 mm
    tall on the floor.
- **Print fidelity** (`tools/print_fidelity.py`, every colour part). There are
  no flags on five prints. On the tin there are 20, each 0.04–0.07 mm³: the one
  layer at the very tip of a snowflake arm, where the round end of a stroke
  is thinner than a bead. Each arm comes out about 0.2 mm shorter, which you
  won't see. 1.8 mm³ dropped in all, on a 27 cm³ print.
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

`./build.sh [tin|jar]` exports every part (OpenSCAD's CGAL, one at a time).
`./ship.sh tin|jar` runs the fit check, gate, fidelity and fragility, and
writes the 3MFs. `python3 render_clickers.py tin|jar --views` renders. The
STLs aren't committed; the 3MFs hold every part.
