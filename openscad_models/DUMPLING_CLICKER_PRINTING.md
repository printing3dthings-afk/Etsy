# Dumpling Clicker Keychain — printing notes

A kawaii bao bun keycap that presses a **real Cherry MX switch**, seated in a
bamboo steamer basket with a keyring tab. Two printed parts plus one
off-the-shelf switch — the switch is the click; nothing printed has to flex.

| File | What it is |
|---|---|
| `dumpling_clicker_basket.3mf` / `.stl` | steamer basket, switch plate, keyring tab |
| `dumpling_clicker_bao.3mf` / `.stl` | the bun — **standard socket fit** |
| `dumpling_clicker_bao_loose.3mf` / `.stl` | the bun — **loose socket**, if the first is too tight |

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
| bun | 36m 50s | 5.24 g | $0.10 |
| basket | 53m 18s | 9.03 g | $0.18 |
| **one complete unit** | **~1h 30m** | **14.3 g** | **~$0.28** + one switch |

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
- **The overhang scan was written backwards.** `asin(|nz|)` *is* the angle
  from vertical, so filtering `< 35` selected the safe faces and reported
  47% of the bun as needing support. Same class as Technique 38's sign trap.
