# Wrap-Around Tower

2026-11-04. Your pick, form 2 of five: four-in-a-row played round a tower,
where lines can wrap all the way round.

## The game

- **Board:** eight tubes stand round a tower, six pieces high. That's 48
  cells, 24 pieces each.
- **Your turn:** drop a piece into any tube. A window down the front of each
  tube shows its stack.
- **To win:** make four in a row, across, up or diagonally. **Rows wrap
  round:** a line can run from tube 8 into tube 1, so there's no edge to
  hide against.
- **When the game's over:** lift the tower off its tray and the pieces drop
  out.
- **To put it away:** all 48 pieces go back in the tubes.

The rules of four-in-a-row are free to use. The classic upright blue grid
with red and yellow discs is a brand's look, so this keeps away from it: a
round cream tower on a lilac tray, with pink and lilac pieces. Don't use the
brand's name in the listing.

**Telling the players apart:** pink pieces carry a pressed heart on top,
lilac pieces a star. The two players differ by shape as well as colour,
which helps colour-blind players.

**Size:** the tower is 73 mm across and 48 mm tall; on its tray the set is
112 mm across.

## Printing

Four prints, one colour each, so there are no colour changes. PLA, 0.2 mm
layers, no supports, as each file opens. Times and weights are from
PrusaSlicer with the P1S settings:

| print | file | colour | time | filament |
|---|---|---|---|---|
| tower | `wrap_tower_tower.3mf` | cream `#F4F1EA` | 1 h 25 min | 50 g |
| tray | `wrap_tower_tray.3mf` | lilac `#E8D3F0` | 47 min | 32 g |
| 24 heart pieces | `wrap_tower_pieces_pink.3mf` | pink `#F6A6C1` | 52 min | 22 g |
| 24 star pieces | `wrap_tower_pieces_lilac.3mf` | lilac `#B79CE0` | 54 min | 22 g |

The whole set is about 4 h 9 min and 126 g.

- **The tower** prints upright. The tubes are open at top and bottom, and the
  windows run open to the top, so nothing hangs: the rim comes out
  crenellated, like a castle.
- **The tray** prints flat. The OBC mark is engraved underneath.
- **The pieces** print 24 to a plate, heart or star up.

## Fit (`check_tower.py`)

- A piece drops through every cell of every tube touching nothing. The bore
  is 17 mm and the piece 16 mm.
- Pushed 3 mm towards its window, a piece hits the tower, so it can't fall
  out. The window is 8 mm wide.
- A piece can't turn on its edge in the tube: its diagonal (17.5 mm) is
  longer than the bore.
- The tower sits in the tray's recess, 0.4 mm clear all round. Slid 1 mm, it
  meets the recess wall.
- Six pieces fill a tube to 42 mm, under the 48 mm rim. A seventh stands
  1 mm proud, so a full tube is easy to see.

## Checked before it was pushed

The results are in `checks/`.

- **Product gate: all four prints pass.** 0 supports, 0 overhang perimeters.
  - The tower first failed the wall check at 0.60 mm. The 1.5 mm funnels at
    the tubes' mouths met over the 1.6 mm wall between neighbouring tubes and
    left a knife edge.
  - The tubes now sit 3 mm apart and the funnels are 0.8 mm. The thinnest
    wall is 2.23 mm.
- **Print fidelity: 0 flags on all four prints.** Nothing dropped or filled,
  apart from 0.01 mm³ at the tip of one heart's point.
- **Fragility:** nothing high and nothing on watch on any print.
- **Not tested on the printer yet.** The fit I'd check first is how freely
  the pieces drop. If one sticks, tell me: the clearance is one number
  (`CLR`).

## Renders

`images/wrap_tower_{front,three_quarter,top}.png` show a game in progress.
`piece_heart.png` and `piece_star.png` show the two pieces. These are
design-review renders from the real exported parts, not photos.
