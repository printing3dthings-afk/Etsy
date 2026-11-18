# Village listings: correct one-colour print times (OPEN.md row 10)

**Rewritten 2026-11-18.** The first version of this file (Nov 17) was 15–34% short, for two
reasons:
- it used the in-house checking slicer, not Bambu Studio;
- it was at 2 walls, not Scott's 3.

These are **Bambu Studio's own slice at Scott's settings**:
- 3 walls, 15% infill (Scott, 2026-11-12);
- P1S 0.4, PLA Basic (Santa v2: matte white), 0.20 mm Standard, supports off, one colour.

Each slice is committed beside the building's printing notes on the Claude branch, and opens
in Bambu Handy. Use these times in listings and posts, and don't round them down.

| Building | One-colour time | Filament | Superseded (Nov 17) | Slice file (Claude branch) |
|---|---|---|---|---|
| Gingerbread Cottage | 2 h 13 m | 51 g | 1 h 53 m | `…/gingerbread/cottage/gingerbread_cottage_one_colour.gcode.3mf` |
| Gingerbread Cocoa Café | 2 h 9 m | 46 g | 1 h 40 m | `…/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe_one_colour.gcode.3mf` |
| Gingerbread Cookie Clock Tower | 2 h 43 m | 56 g | 1 h 48 m | `…/gingerbread/cookie_clock_tower/…_one_colour.gcode.3mf` |
| Gingerbread Sweet Shop | 2 h 44 m | 53 g | 2 h 6 m | `…/gingerbread/sweet_shop/…_one_colour.gcode.3mf` |
| Gingerbread Turret House | 2 h 41 m | 58 g | 2 h 17 m | `…/gingerbread/turret_house/…_one_colour.gcode.3mf` |
| Gingerbread Candy Cane Chapel | 3 h 6 m | 65 g | 2 h 34 m | `…/gingerbread/candy_cane_chapel/…_one_colour.gcode.3mf` |
| Gingerbread Santa's Workshop | **16 h 37 m** | 361 g | 11 h 56 m | `…/gingerbread/santas_workshop/…_one_colour.gcode.3mf` |
| Victorian Cottage | 1 h 51 m | 42 g | 1 h 33 m | `…/victorian/cottage/victorian_cottage_one_colour.gcode.3mf` |
| Victorian Clock Tower | 2 h 43 m | 61 g | 2 h 12 m | `…/victorian/clock_tower/…_one_colour.gcode.3mf` |
| Victorian Shop House | 2 h 55 m | 65 g | 2 h 19 m | `…/victorian/shop_house/…_one_colour.gcode.3mf` |
| Victorian Townhouse | 3 h 35 m | 76 g | 2 h 53 m | `…/victorian/townhouse/…_one_colour.gcode.3mf` |
| Victorian Toy Shop | 3 h 44 m | 79 g | 2 h 59 m | `…/victorian/toy_shop/…_one_colour.gcode.3mf` |
| Victorian Coaching Inn | 4 h 2 m | 95 g | 3 h 7 m | `…/victorian/coaching_inn/…_one_colour.gcode.3mf` |
| Victorian Church | 4 h 3 m | 85 g | 3 h 17 m | `…/victorian/church/…_one_colour.gcode.3mf` |
| Victorian Santa's Workshop **v1** | **19 h 31 m** | 397 g | 15 h 40 m | `…/victorian/santas_workshop/victorian_santas_workshop_one_colour.gcode.3mf` |
| Victorian Santa's Workshop **v2** (matte white) | **19 h 8 m** | 375 g | 17 h 34 m | `…/victorian/santas_workshop/v2/gcode/victorian_santas_workshop_v2_matte_white.gcode.3mf` |

**Watch out for these:**
- **Victorian Santa's Workshop has two versions,** 19 h 31 m (v1) and 19 h 8 m (v2). The
  listing must give the time of the file it actually sells.
- **Both Santa's Workshops are long prints,** 16–20 hours: most of a day. Say so plainly in
  their listings.
- **Four-colour times are much longer,** and those slices are still at 2 walls (the Workshop
  v2 four-colour was 2 d 22 h). Listings with colour photos should say the time is for one
  colour.
- **The READMEs inside the sale ZIPs still carry the Nov 17 times.** I've marked the ZIPs to
  be rebuilt before they go up.
- **The printed-listing prices** in `DRAFTS_printed.md` were set against old times that were
  1.3–2.5 times these. Whether to reprice is Scott's call. The two Workshops are now by far
  the longest prints at $39.99.

**Updated on the Claude branch to these times** (`bc023b4`): every building's printing
notes, `DRAFTS_printed.md`, `DRAFTS_downloads.md` and `business/store_kit/PAYHIP_SETUP.md`.

**Still not done:** comparing these against the live listing text. Benson, if you have the
listing copy saved, mark each building where the old time differs, and Scott approves the
new lines.
