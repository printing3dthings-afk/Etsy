# Valentine mailboxes: Hungry Love Monster and Giant Love Letter

2026-10-30. Your picks 2 and 4 of the five classroom Valentine mailboxes: a box
a child brings to school for the other kids to post their valentines into.

**School-friendly by design:**
- No small or loose parts.
- No magnets, no glue, no screws.
- Rounded wherever hands go.
- Every opening takes a standard kids' valentine in its envelope (2.75 × 4 in,
  70 × 102 mm), 3 mm thick for a card with a sticker or a flat lollipop.

Each one has the child's name on the front. It's one line at the top of the
.scad (`NAME = "OLIVIA";`, `NAME = "LIAM";`) and scales to fit.

Times and weights are from PrusaSlicer with the P1S 0.2 mm Standard
settings, one colour, no colour changes. Bambu Studio's times will differ,
and colour changes add purge and time.

## Giant Love Letter (`love_letter/love_letter_mailbox.3mf`)

A big standing envelope: 180 mm across, 62 mm deep, 124 mm tall with the lid.
It holds 1.2 L.

| print | file | colours (AMS slot) | as it sits in the file | sliced, one colour |
|---|---|---|---|---|
| the envelope | `love_letter_mailbox.3mf` | pink 1, red seal, hearts and postmark 2, white stamp 3, dark "To:" and name 4 | standing on its base | 3 h 53 min, about 161 g |
| the lid | `love_letter_mailbox.3mf` | pink 1 | upside down, on its top | 51 min, about 35 g |
| Cupid | `love_letter_cupid.3mf` | white 1 | flat, face up | 10 min, about 4 g |

The whole letter is about 4 h 54 min and 200 g of PLA.

Pink `#F6A6C1`, red `#D7263D`, white `#F4F1EA`, dark plum `#3B2A3A`. The
envelope and lid share one plate. Cupid has his own 3MF: he's one white
filament, so he can go on any plate that prints white.

**What's on it:**
- **The address side:** a white stamp with a perforated edge and a red heart,
  a red wavy postmark, "To:", the child's name and an underline.
- **Cupid,** in a pocket at the lower left, aiming his arrow at the name.
  He's a flat white charm, 60 × 56 mm and 3 mm thick, and presses onto two
  pegs in a 1 mm deep pocket shaped like him. Each peg has a crush rib down
  both sides, so he snaps in snug and pulls back out. He doesn't come off
  in a child's hands by accident, and he isn't glued, so he can be put back.
- **Sticker hearts,** raised in the envelope's own colours: red on a white
  sticker, or pink on a red one. Three on the front, four on the back. They're
  part of the envelope, not loose pieces.
- **The back:** the envelope's bottom flap and its top flap overlapping, and a
  red heart wax seal where they meet.
- **The lid:** the top edge of the envelope, with a 118 × 11 mm slot. Its
  spigot drops 10 mm into the envelope, so it sits put and lifts straight off
  to empty it.

**Put it together:** press Cupid into his pocket, pegs first, until he sits
flat. To take him out, get a fingernail under his edge and lift.

## Hungry Love Monster (three 3MFs in `love_monster/`)

A chubby lilac monster whose grin is the card slot, hugging a heart with the
child's name on it. 160 mm across, 120 mm deep, about 150 mm tall with the
fur on.

| print | file | colours (AMS slot) | as it sits in the file | sliced, one colour |
|---|---|---|---|---|
| the body | `love_monster_body.3mf` | lilac 1 | lying on its back | 4 h 1 min, about 186 g |
| the face | `love_monster_face.3mf` | lilac 1 (and the arms and feet), white eyes, eye shines and teeth 2, red heart 3, dark pupils and name 4 | flat, face up | 1 h 24 min, about 56 g |
| the fur cap | `love_monster_fur.3mf` | pink 1 | upside down, on its top | 2 h 11 min, about 90 g |

The whole monster is about 7 h 37 min and 332 g of PLA.

Lilac `#B79CE0`, white `#F4F1EA`, red `#D7263D`, dark `#2B2433`, pink fur
`#F58CB4`.

**Put it together:**
1. Slide the face down into the grooves at the front of the body. The ledges
   at the front hold it in.
2. Set the fur cap over the top. It holds the face down.
3. To empty it, lift off the fur cap. The cards come out the top.

**Why the face is a separate print:** a card-wide mouth through an upright
wall can't print without support. The first one-piece version needed 7,962
support moves, all under the eight tooth tips, which start in mid-air. Printed
flat, the mouth is just a hole in a plate. The face's colours and detail also
land on a top surface, where small detail prints best.

## Checked before it was pushed

The checks are `check_mailboxes.py` and `ship.sh`. Their results are in each
design's `checks/` folder.

- **Fit:**
  - **Letter:** the lid rests on the rim. 0.1 mm lower it would be 111 mm³
    into the body, so it can't drop in. Lifted 0.2 mm and slid 0.15 mm, it
    touches nothing, so it lifts off cleanly. The envelope passes through the
    slot all the way to the floor without touching plastic.
  - **Cupid:** in his pocket, the only contact is the pegs' crush ribs in his
    holes (0.11 mm³: a press fit, not a jam). His back sits on the pocket
    floor, since 0.1 mm deeper would be 110 mm³ into the wall. Slid 0.6 mm
    in any direction, he hits the pegs or the pocket's edge (1.9 mm³), so he
    can't wander.
  - **Monster:**
    - The face slides down its groove and back out touching nothing.
    - Pushed 0.6 mm forward, the ledge stops it. Pushed 0.6 mm back, the rib
      stops it.
    - The fur cap rests on the rim and lifts off cleanly, like the letter's lid.
    - The envelope goes in through the mouth, lying flat, all the way inside.
      The straight gap through the grin is 12 mm.
- **Supports: none on any of the six prints.** These fixes got them there:
  1. **The face as its own flat print** (above).
  2. **The monster body's inner front corners:** they were rounded, which
     made the ledge over the face's groove start as a flat 0.4 mm shelf. The
     slicer propped it with 7,333 moves. Squared, none.
  3. **Every slope at 40°** from upright, not 45°. At exactly 45° the slicer
     still props a surface.
- **Product gate: all six pass.**
  - The monster body first failed the wall check: 0.92 mm against the 1.2 mm
    floor. The ledge and the rib that hold the face each tapered to a knife
    edge.
  - Each now keeps its full depth for 1.4 mm before it tapers. The thinnest
    wall is now 1.78 mm.
  - The ledge laps the face by 2.5 mm, down from 3.5, to keep its slope at
    40°.
- **Print fidelity:**
  - The letter: no flags on the envelope (all four colours), the lid or Cupid.
  - The monster face: no flags.
  - The monster body: no flags.
  - The fur cap has one flag, 0.7 mm³. It's on the inside of the fringe at a
    front corner, where a scallop's edge thins to 0.28 mm and the printer
    rounds it off. It isn't visible.
- **Fragility:** nothing high on any of the six prints. Cupid has three on
  watch: his bow and his arrow, about 11 mm long and 4–5 mm² across. They're
  a third of the way to where the chapel's window bar snapped, and he's
  pressed in from the front, never pulled by them.
- **Not tested on the printer yet.** Two things I'd watch:
  - How firmly Cupid presses in. Each rib reaches 0.2 mm into his hole. If
    he's too stiff to press in, tell me and I'll take that down. If he falls
    out, I'll take it up.
  - How the monster's face slides. It has 0.3 mm clearance each side.
  - If it's tight, sand the face's edges.
  - If it's loose, tell me and I'll tighten it.
- **The names are laid out one letter at a time** (`name_text.scad`). Fredoka
  draws "IV" as one joined glyph, so typed as one line, "OLIVIA" printed as
  "OLMIA". Any name works now, in OpenSCAD 2021 as well. Letters outside A–Z,
  a–z, 0–9 and ` -'.!&` get an average width.

## Renders

- `love_letter/images/letter_{front,three_quarter,top,back,apart}.png` and `cupid.png`
- `love_monster/images/monster_{front,three_quarter,top,apart}.png`

They're made from the real exported parts, assembled. They're design-review
renders, not photos.
