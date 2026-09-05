# Dumpling Clicker Keychain — printing notes

A kawaii bao bun keycap that presses a **real Cherry MX switch**, seated in a
bamboo steamer basket with a keyring tab. Two printed parts plus one
off-the-shelf switch — the switch is the click; nothing printed has to flex.

| File | What it is | Filament |
|---|---|---|
| `dumpling_clicker_basket` | steamer basket, switch plate, keyring tab | bamboo / tan |
| `dumpling_clicker_bao` | the bun — **standard socket fit** | bun colour |
| `dumpling_clicker_bao_loose` | the bun — **loose socket**, if the first is tight | bun colour |
| `dumpling_clicker_bao_eyes` | eyes + smile, one flush inlay | **black** |
| `dumpling_clicker_bao_blush` | the two cheeks | **pink** |
| `dumpling_clicker_bao_shine` | the two catchlights | **white** |

Each ships as both `.3mf` (use these — real mm units, ~1/13th the size) and `.stl`.

## The face is real colour, not a painted dimple

The eyes, smile, blush and catchlights are **separate solids that exactly
fill their own recesses in the bun**, so the printed surface stays smooth and
the face is purely a filament change (Technique 39's flush-inlay method).

- **Multi-colour (AMS):** load all four bun parts as one object in Bambu
  Studio and assign bun / black / pink / white. Four slots — exactly one AMS
  unit. On a cream or white bun the catchlight can share the bun's filament,
  dropping it to three.
- **Single colour:** print `dumpling_clicker_bao` alone and skip the three
  inlays. The face then reads as recessed dimples — still a face, carved
  rather than coloured.

Verified with the two tests that actually matter for a colour split, both
returning empty geometry:
- `intersection(eyes, blush)` — **empty**. No two colour parts share volume.
  They did at first: at 33 degrees against the eyes' 17 the blush genuinely
  overlapped, which no render would have shown and which would have had two
  printed parts claiming the same space. Rather than hunt for an angle that
  happens to clear, the eye is now subtracted from the blush, so they are
  disjoint by construction at any placement.
- `bao_gross − body − eyes − blush − shine` — **empty**. The four parts
  reconstitute the bun exactly, leaving no gap between them.

## The basket is built from the reference photo, not from memory

A real bamboo steamer is a **shallow dish**, not a drum, and its collar is the
dominant feature — roughly a third of the total height — with a shorter band
of fine lines below it and a plain foot. Two rounds of getting this wrong:

1. **4 deep cosine swells** read as a screw thread. A cosine has no flat
   between its dips, so the body never reads as a barrel with lines scribed
   on it. Replaced with explicit V-notches.
2. **8 notches spread over the full height** inverted the proportions — the
   grooves dominated and the collar became a thin lip. Counted off the photo
   properly: **6 notches, 0.42mm deep and 0.85mm wide**, occupying the middle
   band only, with the collar owning the top 4.8mm and rolling over in a
   bullnose at its lip.

**And it was too tall.** The basket measured 0.54 height-over-width against
the photo's ~0.41, because the switch's 3.3mm pins were being cleared by
sinking the *entire* well 3.3mm deeper. Cherry's own footprint drawing shows
those pins inside a ~13×9mm patch near the centre, so they now get a small
relief slot through the floor instead and the whole basket drops by that
3.3mm. It measures **0.409** — the reference is ~0.41.

The bun's belly bulge went at the same time. Its rim is now the widest point
at 15.2mm in a 15.6mm bore, so the visible gap around it is 0.4mm instead of
the 0.9mm ring you could previously see down into, and its side drops
straight into the steamer the way the reference does.

Print the standard bun first. If it will not press onto the switch stem,
print the loose one — that is the whole reason both exist (Technique 47: the
best-selling real fidget clicker on Printables ships exactly this two-file
tolerance ladder rather than betting on one number, because printers vary).

## You need to buy one thing
A **Cherry MX (or MX-compatible) plate-mount switch**. Any colour works;
**MX Blue is the one that actually clicks**, which is the point of the toy.
The design is built to Cherry's own published dimensions, so Gateron/Kailh
MX-clones fit too.

## Assembly
1. Push the switch down into the basket from **above**. Its two clips snap
   under the 1.5mm plate and it seats flat on the plate face.
2. Push the bun down onto the switch's cross stem until it stops.
3. Split ring through the tab.

## Print settings
- **PLA or PETG**, 0.2mm layers, 3 walls, 15% gyroid.
- **No supports on either part.** Both print flat on their own base with
  nothing overhanging past 55°. The one horizontal face — the underside of
  the switch plate — is an annular *bridge* anchored to the wall the whole
  way round, which is a routine hole ceiling, not a support case.
- The bun prints rim-down. Its whole underside cavity, the socket post and
  the engraved mark are all self-supporting in that orientation by design.

## Real print cost — sliced, not estimated

| | time | filament | cost @ $20/kg |
|---|---|---|---|
| bun | 36m 58s | 5.26 g | $0.11 |
| basket | 44m 31s | 7.34 g | $0.15 |
| **one complete unit** | **~1h 22m** | **12.6 g** | **~$0.26** + one switch |

Multi-colour adds purge on top of that — budget roughly double for a
four-filament bun, since the face spans ~37 layers and every one swaps.

Well inside the ~4h-per-sellable-unit ceiling Technique 44 sets, and the
basket batches ~40 to a 256x256 plate, so a full plate is a day's run and
tens of units. Technique 49's sourced market data puts keychains at $3-12
retail on 80-90% margins; the binding cost here is the switch, not the print.

## Verified before shipping — on the real exported meshes, not by eye
- **Every Cherry MX dimension came from Cherry's own datasheet drawing**
  (MX1A series) or Cherry's published keycap slot spec: 15.6mm housing,
  14mm plate cutout, 1.5mm plate, 5.0mm body below the plate, 3.3mm pins,
  6.6mm housing above the plate, 3.6mm stem, 4.0mm travel, and a
  4.1mm × 1.17mm keycap cross. The entire Z stack is *derived* from those —
  there is not one eyeballed height in the model.
- **Socket bore measured on a real cross-section: 4.220mm** (standard) and
  **4.320mm** (loose) — matching the modelled 4.10 + fit exactly.
- **Socket confirmed open** by point-containment at z = 0.5 / 2.0 / 3.0 and
  solid at 3.8, i.e. a real 3.4mm-deep blind bore, not a rendered-looking
  one. A cutter that misses removes nothing and renders perfectly clean.
- **Travel actually works**: the cap's rim ends 2.8mm clear of the plate at
  full press, and the cap never fouls the basket bore — max radius 15.14mm
  against a 15.5mm bore over the whole 2.8mm it descends into it.
- **Housing clearance**: the cavity was sized against the housing's 22.06mm
  *corner diagonal*, not its 15.6mm face — the corners are what collide.
- 1 connected component per part, watertight, flat on the bed at z=0.
- Wall p05 1.00mm, median 4.00mm. The 1.2% of ray samples under 0.8mm are
  scattered across the entire part with no cluster on any feature — edge
  sampling artifact, not a thin region.
- **Maker's mark**: "OBC" engraved into the basket's underside, 15.46mm wide
  = 44% of the 35.2mm base, inside the 35–45% standing target, and its
  recess floor was confirmed to physically exist (2954 vertices on the plane).

## Real bugs caught during the build, for whoever touches this next
- **The eye dimples punched straight through into the hollow cavity.** The
  cavity had been held at 12mm radius "to be safe" far higher than the
  switch ever reaches; the eyes broke into it and the render showed real
  holes. The cavity only needs to be wide where the housing actually is
  (bao-local 3.8mm) — every millimetre above that is wall thrown away.
- **The face cut depths were inverted**: blush cutting 1.55mm against the
  eyes' 1.3mm, so the shallowest feature was the deepest one and the face
  read as five unrelated blobs. Eyes deepest, smile mid, blush barely a dish.
- **The smile was a hard boomerang chevron** — `abs(i)` for the curve puts a
  corner at the centre. A parabolic `i*i` rise fixed it.
- **The floor weave was invisible**, sitting flush *in* the plate rather than
  standing on it. It also has to start outside the housing's corner radius,
  or a rib under the switch stops it seating flat on the one surface the
  whole mechanism references from.
- **`pin_relief()` was defined but never called.** A patch matched the wrong
  indentation, so the module existed, the render looked perfect, and the
  basket was watertight and single-component — but the switch's pins would
  have bottomed out on the floor and held it 2.7mm proud of the plate. Caught
  only by point-containment testing three coordinates inside the intended
  slot; nothing visual would have shown it.
- **The keyring lug stood 1.5mm above the rim**, which made the basket both
  measure and read taller than the dish in the photo. Its Z is now derived
  from its own outer radius rather than set by hand.
- **The overhang scan was written backwards.** `asin(|nz|)` *is* the angle
  from vertical, so filtering `< 35` selected the safe faces and reported
  47% of the bun as needing support. Same class as Technique 38's sign trap.
