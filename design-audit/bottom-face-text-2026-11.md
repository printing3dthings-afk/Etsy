# Bed-face text audit (Brief A), 2026-11-14

**Question:** does any shipped file print text or a mark that reads backwards on the face
that lies on the bed?

**Scope:** every shipped 3MF in `openscad_models/` — 210 files, not counting slices or
fidelity scratch files under `logs/` and `checks/`.

**Method:** `tools/underside_view.py`, new for this audit.
- It slices each file 0.3 mm above the bed, every colour part separately, so both inlays
  and engravings show.
- It draws that slice as it reads once the part is printed and turned over.
- With `--marks` it measures every "OBC" mark instead of trusting a picture. It checks the
  letter order and the B's spine side and bowl sizes, the same test as
  `tests/test_obc_mark_reading.py`, and gives one of three verdicts:
  - **correct:** reads OBC upright when the piece is tipped back (Scott's convention since
    2026-10-25, `brand/obc_mark.scad`);
  - **upside down:** reads correctly, but only when the piece is turned side to side. This
    is the older convention, not a mirror;
  - **mirrored:** reads backwards whichever way you turn it. This is Brief A's defect.

**Why measure:** Montserrat "OBC" looks almost the same flipped top to bottom, so a picture
of a mirrored mark can look correct. That happened with the Love Monster during this audit:
the picture looked fine and the measurement caught it. The full per-file results are in
`obc-marks-measured-2026-11-14.tsv`. Text other than OBC (signatures, labels, days) was
read from the pictures and checked against each source.

## Verdicts

### Mirrored: fixed at source, re-exported, all gates re-run

| design | text | cause | fix | route |
|---|---|---|---|---|
| **Label Tile** (`label_bin.scad`, `label_tile.3mf`; MakerWorld 3555518) | "PARTS" | prints text face down; the text was drawn reading from above, so the printed face read "STRAP" backwards | the tile's text is now `mirror([1, 0, 0])` | (a) mirrored glyphs on the bed face. Kept face-down because that face is the point of the design: a mirror-smooth label in 3 layers. |
| **Day Pods lids** (`day_pods.scad`, `day_pods_lids.3mf`) | SU MO TU WE TH FR SA | `lid_print()` turned the lid over with `mirror([0, 0, 1])`, which makes a mirror image: every day printed reversed | `rotate([0, 180, 0])`: a real turn, so the engraved day reads | Engraved into the face that prints on the bed, as before. The text was already right in the source; only the flip was wrong. |
| **Love Monster body** (`love_monster.scad`, `love_monster_body.3mf`) | OBC on its back | an extra `mirror([1, 0, 0])` undid the library's own mirroring | `rotate([0, 0, 180])`. Checked seen from behind, standing up: O-B-C, the B's spine on the left and its bigger bowl at the bottom. | Kept on the back, which prints on the bed. |

Each was re-checked after the fix:
- **Label Tile:** watertight; Bambu slice 14 min 19 s, 2.1 g + 0.9 g, no supports.
- **Day Pods lids 0 and 3:** product gate PASS, print fidelity 0 flags, fragility 0.
- **Love Monster body:** fit check OK, product gate PASS, print fidelity 0 dropped,
  fragility 0. Its volume is unchanged (182,826.60 mm³).

The old files are in `data/trash` (Label Tile) and in git history.
`bottom-face-text-2026-11-before-after.png` shows all three before and after.

### Monogram Keychain (MakerWorld 3555680): no change, and why

**Measured: the shipped `monogram_keychain_J.3mf` reads OBC correctly when turned side to
side.**
- Its mark has been `mirror([1, 0, 0])` since 2026-09-09.
- That fix came from Scott's own printed J: the earlier `mirror([0, 1, 0])` "printed
  backwards and unreadable" the way he turned it.
- A keychain is flipped over side to side, by its ring, not tipped back like a building.
- Seen tipped back, it reads upside down. That is most likely what Benson's render
  showed. It is not a mirror.

**If the file on MakerWorld differs from the repo's**, compare it with this one's
SHA-256 before swapping anything:

```
abf241d58702d6a6a99abc8ff2666619b63cd05ae487cfcc98311b6fe53c24c2  monogram_keychain_J.3mf
```

### Upside down (the older side-to-side convention): 30 files, Scott's call

These read correctly turned side to side, and upside down when tipped back. None is
mirrored.

- **Haunted Town:**
  - bakery, cemetery, chapel, post office, general store, undertaker, schoolhouse.
- **Christmas village:**
  - frozen fountain, horse sleigh, steam train, chestnut cart, town tree, bandstand,
    carolers;
  - gingerbread sweet shop, Santa's workshop (v1 and current), turret house.
- **Ornaments, nativity, lanterns:**
  - name ornament, mini lanterns;
  - nativity: stable, kings and shepherd, holy family;
  - gift box lantern v1, drum lantern.
- **Gobble:**
  - tongue, body, tray, and the view-only assembly.
- **Monogram Keychain J:** deliberately, as above.

**Recommendation:** leave them until each design's next re-export, then switch to the
library's current mark. The standing rule is that existing listed designs aren't touched
before Dec 25.

(The TSV also lists the fixed Love Monster body as "upside down". That verdict is for the
print, tipped back on the bed. Its mark is on a wall and is read with the mailbox
standing up; that reading was checked separately and is correct.)

### Correct: 66 files

These read OBC upright when tipped back. Every design built since the library change
reads correctly. The full list is in the TSV.

### Script signatures and script "OBC": correct, not mirrored

| design | text | source |
|---|---|---|
| sauce bowl, sauce bowl 1 oz, sauce tray, sauce tray 1 oz | script OBC | `mirror([0, 1, 0])` |
| dumpling clicker, dumpling basket | script OBC | `mirror([0, 1, 0])` |
| kawaii cloud, mochi fox, ribbed organizer, mushroom lamp | "OnBrandCraftz", Caveat | `mirror([0, 1, 0])` |
| honeycomb pen holder, cable clip, sundial signature | "OnBrandCraftz", Dancing Script | `mirror([0, 1, 0])` |
| gauntlet tile, snap box base, snap box | "OnBrandCraftz", sans | `mirror([0, 1, 0])` |
| **phone stand, spiral fluted vase** | "OnBrandCraftz", Dancing Script | **no source in the repo.** Checked by stroke lean instead: plain text keeps a script's right lean, mirroring reverses it. Both lean exactly as the honeycomb pen holder (−0.32), so they are not mirrored. |

### Not text

- **Sundial:** its "numerals" are digit-shaped light tubes through the gnomon, read by the
  sun, not printed text. MakerWorld already removed this model.

### No text on the bed face: 113 files

## What changes in the pipeline

`tools/underside_view.py` and `tests/test_underside_view.py` (the calibration and the three
fixes) are the export-time check Benson asked for in ask 9. The `--marks` verdict runs on
any 3MF or STL. Run it on every new design's shipping file and include the underside
picture with its renders.
