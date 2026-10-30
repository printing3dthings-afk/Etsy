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

## Giant Love Letter (`love_letter/love_letter_mailbox.3mf`)

A big standing envelope: 180 mm across, 62 mm deep, 124 mm tall with the lid.
It holds 1.2 L.

| print | colours (AMS slot) | as it sits in the file | sliced, one colour |
|---|---|---|---|
| the envelope | pink 1, red seal, hearts and postmark 2, white stamp 3, dark "To:" and name 4 | standing on its base | SLICE_BODY |
| the lid | pink 1 | upside down, on its top | SLICE_LID |

Pink `#F6A6C1`, red `#D7263D`, white `#F4F1EA`, dark plum `#3B2A3A`. Both
prints are on one plate in the 3MF.

**What's on it:**
- **The address side:** a white stamp with a perforated edge and a red heart,
  a red wavy postmark, "To:", the child's name and an underline.
- **The back:** the envelope's bottom flap and its top flap overlapping, and a
  red heart wax seal where they meet.
- **The lid:** the top edge of the envelope, with a 118 × 11 mm slot. Its
  spigot drops 10 mm into the envelope, so it sits put and lifts straight off
  to empty it.

## Hungry Love Monster (three 3MFs in `love_monster/`)

A chubby lilac monster whose grin is the card slot, hugging a heart with the
child's name on it. 160 mm across, 120 mm deep, about 150 mm tall with the
fur on.

| print | file | colours (AMS slot) | as it sits in the file | sliced, one colour |
|---|---|---|---|---|
| the body | `love_monster_body.3mf` | lilac 1 | lying on its back | SLICE_MBODY |
| the face | `love_monster_face.3mf` | lilac 1 (and the arms and feet), white eyes, eye shines and teeth 2, red heart 3, dark pupils and name 4 | flat, face up | SLICE_FACE |
| the fur cap | `love_monster_fur.3mf` | pink 1 | upside down, on its top | SLICE_FUR |

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
  - **Monster:**
    - The face slides down its groove and back out touching nothing.
    - Pushed 0.6 mm forward, the ledge stops it. Pushed 0.6 mm back, the rib
      stops it.
    - The fur cap rests on the rim and lifts off cleanly, like the letter's lid.
    - The envelope goes in through the mouth, lying flat, all the way inside.
      The straight gap through the grin is 12 mm.
- **Supports: none on any of the five prints.** These fixes got them there:
  1. **The face as its own flat print** (above).
  2. **The monster body's inner front corners:** they were rounded, which
     made the ledge over the face's groove start as a flat 0.4 mm shelf. The
     slicer propped it with 7,333 moves. Squared, none.
  3. **Every slope at 40°** from upright, not 45°. At exactly 45° the slicer
     still props a surface.
- **Product gate: all five pass.**
  - The monster body first failed the wall check: 0.92 mm against the 1.2 mm
    floor. The ledge and the rib that hold the face each tapered to a knife
    edge.
  - Each now keeps its full depth for 1.4 mm before it tapers. The thinnest
    wall is now 1.78 mm.
  - The ledge laps the face by 2.5 mm, down from 3.5, to keep its slope at
    40°.
- **Print fidelity:**
  - The letter: no flags on the envelope (all four colours) or on the lid.
  - The monster face: no flags.
  - The monster body: no flags.
  - The fur cap has one flag, 0.7 mm³. It's on the inside of the fringe at a
    front corner, where a scallop's edge thins to 0.28 mm and the printer
    rounds it off. It isn't visible.
- **Fragility:** nothing high and nothing on watch, on all five prints.
- **Not tested on the printer yet.** Two things I'd watch:
  - **How the face slides.** It has 0.3 mm clearance each side.
    - If it's tight, sand the face's edges.
    - If it's loose, tell me and I'll tighten it.
  - **The dark name on the letter.** Its letters are spaced wider than the
    font's own spacing. At normal spacing, the raised letters' sloped sides
    ran together, and "OLIVIA" read as "OLMIA" in the render.

## Renders

- `love_letter/images/letter_{front,three_quarter,top,back}.png`
- `love_monster/images/monster_{front,three_quarter,top,apart}.png`

They're made from the real exported parts, assembled. They're design-review
renders, not photos.
