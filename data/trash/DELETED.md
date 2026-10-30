# Deletion Recycle Bin

> Everything deleted by an automated edit (code blocks or whole files) is
> archived here first, kept for **30 days**, then auto-pruned. To recover
> something, run `python tools/trash.py --restore <id>` (or just copy it back
> out of the fenced block below). Byte-exact copies also live in
> `data/trash/files/`.

<!-- TRASH id=20260930-001 date=2026-09-30 kind=file source="openscad_models/christmas_village/victorian/shop_house/victorian_shop_house.scad" reason="Replaced by the rounded shop-house (Scott, 2026-09-30: not squared). This is the finished, gated square version (commit 16df111)." -->
## 20260930-001 · 2026-09-30 · file · `openscad_models/christmas_village/victorian/shop_house/victorian_shop_house.scad`
**Reason:** Replaced by the rounded shop-house (Scott, 2026-09-30: not squared). This is the finished, gated square version (commit 16df111).  
**Payload:** `data/trash/files/20260930-001__victorian_shop_house.scad`

```
// Victorian Shop-House -- the Dickens Victorian village's first building with
// "more shape" (Scott, 2026-09-30, picked from four shapes against his
// reference photos in ../../references/). A two-storey shop: a brick shop floor
// with a bay window and a panelled door; above it a white plaster storey with
// dark timbers that JUTS OUT over the street on brackets; a steep front gable
// with a scalloped bargeboard and a finial; a tall stepped chimney stack. On a
// snow base.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on.
//
// The machinery is the first Victorian cottage's (../cottage/victorian_cottage
// .scad), itself the chapel's; every trap it met is written up in
// .claude/skills/3d-print-design/SKILL.md Technique 79 and applied here from
// the start: parts overlap and are cut by priority, never abut; reliefs rise
// from the wall plane; nothing reaches below a ceiling.
//
// COLOUR PARTS, ONE PRINT (victorian_shop_house.3mf), priority roof > accent >
// trim > body:
//   body    brick shop floor, the bay's stall riser, the chimney, the step
//   roof    slate roof, and the "timber": the jetty's beam, cove and
//           brackets, the upper storey's framing, window frames and lattice,
//           the door
//   trim    snow base and drifts, the upper storey's plaster walls, soffits,
//           kneelers, bargeboards and finials, snow on the roof, every pane,
//           the shop floor's window and door frames
//   accent  evergreen: the bay window's frame and bars, the wreath, the
//           window boxes
//
// FRAMES. The shop floor is the brick box, centred on the origin. The upper
// storey and roof are the cottage's roof machinery in their own frame, moved
// forward by the jetty: upper() puts a child there.

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts

$fa = 4;  $fs = 0.4;
part = "all";

// ---- the shop floor --------------------------------------------------------------
W        = 56;              // across the front, both storeys
Wh       = W/2;
Dg       = 50;              // shop floor depth
Dgh      = Dg/2;
wall     = 1.68;
corner_r = 1;
plinth_h = 8;
H1       = 38;              // top of the shop floor; the jetty starts here
SH       = 1.2;

// ---- brick -----------------------------------------------------------------------
bd    = 0.6;
bp    = 2.6;
br    = bd * tan(58);
bj    = 0.6;
bl    = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

// ---- the upper storey and roof -------------------------------------------------------
J     = 4;                  // the jetty: the upper storey stands this far out in front
Du    = Dgh + J/2;          // its half-depth ...
yc    = -J/2;               // ... about this centre
H     = 70;                 // its eave (the side windows' heads clear the eave's flare)
r_ang = 58;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + e;             // plaster: no brick face
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Du - wall;
y_rr  = y_r + 0.4;
cp_lo = -0.2;  cp_hi = 2.6;
module upper() translate([0, yc, 0]) children();

// ---- placement -------------------------------------------------------------------------
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
module ftf(cy, hy, face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, cy + hy, z] : face == 1 ? [u, cy - hy, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module nf(face, u, z) ftf(0, Dgh, face, u, z) children();      // shop floor
module uf(face, u, z) ftf(yc, Du, face, u, z) children();      // upper storey
function loc(f, u) = (f == 0 || f == 3) ? -u : u;

module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260930-001 -->
<!-- TRASH id=20260930-002 date=2026-09-30 kind=file source="openscad_models/christmas_village/victorian/cottage/victorian_cottage.scad" reason="Square Victorian cottage, gated and finished; Scott 2026-09-30 asked for the cottages round (drum + front gable). Also at git commit a8eea51." -->
## 20260930-002 · 2026-09-30 · file · `openscad_models/christmas_village/victorian/cottage/victorian_cottage.scad`
**Reason:** Square Victorian cottage, gated and finished; Scott 2026-09-30 asked for the cottages round (drum + front gable). Also at git commit a8eea51.  
**Payload:** `data/trash/files/20260930-002__victorian_cottage.scad`

```
// Victorian Cottage -- building #1 of the Dickens Victorian Christmas village
// (openscad_models/christmas_village/CHRISTMAS_VILLAGE.md). The cottage from
// the style study, rebuilt to print: brick walls with white quoins, a steep
// slate gable under snow, a pierced white bargeboard with a finial on both
// gables, segmental-arched sash windows with keystones, gothic lancets in the
// gables, a round-arched black door with a wreath and a garland, window boxes,
// icicles under the eaves, a chimney with two pots, on a snow base.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on (the chapel's first print,
// 2026-09-27: free-standing bars snap).
//
// The machinery -- V-course walls, sheared reliefs, the eave flare, kneelers,
// the coping over the gables, frames and panes -- is the Haunted Town chapel's
// (haunted_town/chapel/haunted_chapel.scad), proven on Scott's printer, and
// its WHY comments are there. What is new here is commented here.
//
// COLOUR PARTS, ONE PRINT (victorian_cottage.3mf):
//   body    brick walls, chimney and pots, the kneelers, the bows
//   roof    slate slab and courses, the front door
//   trim    snow base and drifts, quoins, bargeboards and finials, window and
//           door frames, sills, keystones, panes and bars, the eave soffit and
//           icicles, the snow on the roof
//   accent  evergreen: the wreath, the garland, the window boxes
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// TEALIGHT. 60.6 x 54.6 mm clear inside from the table to the 52 mm eave; the
// 58 deg ceiling is 60 mm up at the edge of a 46 mm circle round the centre.

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts; lives in openscad_models/

$fa = 4;  $fs = 0.4;
part = "all";

// ---- walls ---------------------------------------------------------------------
W        = 64;              // along X, the front gable's width
D        = 58;              // along Y, front (-Y) to back
wall     = 1.68;            // 4 x 0.42
corner_r = 1;
plinth_h = 8;               // the snow base; the walls stand on it
Wh = W/2;  Dh = D/2;
SH       = 1.2;             // relief shear (see relief_up)

// ---- brick -----------------------------------------------------------------------
// The post office's brick: V courses ramping out at 58 deg, flat, chamfered
// back in at 45; stretcher bond.
bd    = 0.6;                // brick face, proud of plan(0)
bp    = 2.6;                // course height
br    = bd * tan(58);
bj    = 0.6;                // joint width
bl    = 7;                  // brick length, joint to joint
// The first groove sits 0.4 above the snow: exactly on the base's top it left
// a zero-thickness sheet of brick along the front wall where the two met.
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

// ---- roof --------------------------------------------------------------------------
// A 58 deg gable: the chapel's roof at the post office's steepest safe angle.
// Its inside is the lantern's ceiling.
H     = 52;
r_ang = 58;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + bd + e;
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Dh - wall;
cp_lo = -0.2;  cp_hi = 2.6;

// ---- placement ---------------------------------------------------------------------
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
module nf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
function loc(f, u) = (f == 0 || f == 3) ? -u : u;

module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0,
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260930-002 -->
<!-- TRASH id=20260930-003 date=2026-09-30 kind=file source="openscad_models/christmas_village/gingerbread/cottage/gingerbread_cottage.scad" reason="Square gingerbread cottage, gated and finished; Scott 2026-09-30 asked for the cottages round (cupcake drum + dome). Also at git commit 7de06df." -->
## 20260930-003 · 2026-09-30 · file · `openscad_models/christmas_village/gingerbread/cottage/gingerbread_cottage.scad`
**Reason:** Square gingerbread cottage, gated and finished; Scott 2026-09-30 asked for the cottages round (cupcake drum + dome). Also at git commit 7de06df.  
**Payload:** `data/trash/files/20260930-003__gingerbread_cottage.scad`

```
// Gingerbread Cottage -- building #1 of the Gingerbread Christmas village
// (openscad_models/christmas_village/CHRISTMAS_VILLAGE.md). The cottage from
// the style study, rebuilt to print: smooth gingerbread walls with piped
// icing beads down every corner and round every window and the door, a steep
// roof of chocolate scallop tiles, icing on the ridge and dripping off the
// eaves and rakes, gumdrops along the ridge, a chocolate-bar door between two
// candy canes, a peppermint round window in each gable, peppermint candies on
// the snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on.
//
// Same frame as the Victorian cottage (victorian/cottage/victorian_cottage.scad)
// and so the chapel's machinery; its WHY comments are in those two files. What
// is new is commented here.
//
// COLOUR PARTS, ONE PRINT (gingerbread_cottage.3mf):
//   body    gingerbread walls, the kneelers
//   roof    chocolate slab and scallop tiles, the chocolate-bar door
//   trim    icing: snow base, corner beads, window and door frames and their
//           beads, panes and bars, eave soffit and drips, rake bands and
//           drips, icing on the roof, the candy canes' white, the
//           peppermints' white
//   accent  candy red: gumdrops, cane stripes, peppermint stripes
// Every part is built DISJOINT from the others (part="chk_*").
//
// TEALIGHT. 60.6 x 54.6 mm clear inside from the table to the 52 mm eave.

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";

// ---- walls ---------------------------------------------------------------------
W        = 64;
D        = 58;
wall     = 1.68;
corner_r = 2.5;             // softer than brick: a baked edge
plinth_h = 8;
Wh = W/2;  Dh = D/2;
SH       = 1.2;
bd       = 0;               // the walls are smooth: no brick face

// ---- roof --------------------------------------------------------------------------
H     = 52;
r_ang = 58;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + bd + e;
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Dh - wall;
cp_lo = -0.2;  cp_hi = 2.2;

// ---- placement ---------------------------------------------------------------------
module nf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
function loc(f, u) = (f == 0 || f == 3) ? -u : u;

module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
module relief_hole(d0, a, b, sh = SH) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up(sh) translate([0, 0, a]) linear_extrude(b - a) translate([0, -sh * d0]) children();
}
module relief_up(d0, d1, sh = SH) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up(sh) translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1, sh) children(1);
    }
}
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();

// ---- nave regions -------------------------------------------------------------------------
module below_ceil() xz(-60, 60) polygon([[-40, -5], [40, -5], [40, z_ceil(40)], [0, z_ceil(0)], [-40, z_ceil(-40)]]);
module gable_keep() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
        xz(Dh - wall, Dh + 5) polygon([[-xe, -5], [xe, -5], [xe, z_out(xe) + 1], [0, z_out(0) + 1], [-xe, z_out(xe) + 1]]);
}
fl_ang = 52;
xf  = xe - 0.08;
zf0 = z_ceil(xf) - (xf - Wh) * tan(fl_ang);
fl_xe = z_ceil(xf) + (xe - xf) * tan(fl_ang);
module kneelers() {
    for (s = [-1, 1], m = [0, 1]
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260930-003 -->
<!-- TRASH id=20261001-001 date=2026-10-01 kind=snippet source="openscad_models/christmas_village/victorian/church/victorian_church.scad" reason="church tower quoins removed: skipped round windows and bands they left isolated white squares that read as noise (render 2026-10-01)" -->
## 20261001-001 · 2026-10-01 · snippet · `openscad_models/christmas_village/victorian/church/victorian_church.scad`
**Reason:** church tower quoins removed: skipped round windows and bands they left isolated white squares that read as noise (render 2026-10-01)  
**Payload:** `data/trash/files/20261001-001__snippet.txt`

```
// QUOINS on its two free corners, short ones (the windows are near), skipped
// where a window's frame or a band is
tq_long = 4.0;  tq_short = 2.4;
function tq_free(z0, z1) = len([for (w = TWIN) if (w[0] != 2 && z1 > w[2] - fr_w - 0.5 && z0 < w[2] + w_top(w) + fr_w + 0.5) 1]) == 0
                         && len([for (b = TB_BANDS) if (z1 > b - 2.6 && z0 < b + 1.8) 1]) == 0;
module tower_quoins() intersection() {
    at_tw() brick_skin(tw_s, tw_s, z_tw - 2);
    for (j = [0 : floor((z_tw - 6 - zc(0)) / (2 * bp)) - 1], sy = [-1, 1]) let (z0 = zc(2 * j), z1 = zc(2 * j + 2))
        if (tq_free(z0, z1)) let (lx = j % 2 == 0 ? tq_long : tq_short, ly = j % 2 == 0 ? tq_short : tq_long) {
            translate([TB[0] - 3, sy > 0 ? TB[3] - 0.5 : TB[2] - 3, z0 + q_off]) cube([lx + 3, 3.5, z1 - z0]);
            translate([TB[0] - 3, sy > 0 ? TB[3] - ly : TB[2] - 3, z0 + q_off]) cube([3.5, ly + 3, z1 - z0]);
        }
}
```

<!-- /TRASH 20261001-001 -->
<!-- TRASH id=20261001-002 date=2026-10-01 kind=snippet source="openscad_models/christmas_village/victorian/church/victorian_church.scad" reason="church door_hole removed: cut outward through the door's face it erased the wreath's brick bow (two loose fragments, slicer supports); the slate leaf fills the opening so no frame hole is needed" -->
## 20261001-002 · 2026-10-01 · snippet · `openscad_models/christmas_village/victorian/church/victorian_church.scad`
**Reason:** church door_hole removed: cut outward through the door's face it erased the wreath's brick bow (two loose fragments, slicer supports); the slate leaf fills the opening so no frame hole is needed  
**Payload:** `data/trash/files/20261001-002__snippet.txt`

```
module door_hole() nf(1, 0, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) door_outline();
```

<!-- /TRASH 20261001-002 -->
<!-- TRASH id=20261007-001 date=2026-10-07 kind=snippet source="openscad_models/haunted_town/bakery/haunted_bakery.scad" reason="Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print." -->
## 20261007-001 · 2026-10-07 · snippet · `openscad_models/haunted_town/bakery/haunted_bakery.scad`
**Reason:** Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print.  
**Payload:** `data/trash/files/20261007-001__snippet.txt`

```
// The letters are CARVED 0.6 into the board and lined with the accent part
// (2026-09-26). As a flush inlay they were colour alone: a one-colour print,
// or a slicer that put every part on one filament, lost the sign entirely.
// The cut's ceilings rise outward at 58 deg -- a straight-cut 0.6
// recess drew 1,528 support moves on a test block, the sheared one none.
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(58);  lt_n = 8;
module sign_text() text("BAKERY", size = 5.2, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.06);
module sign_at() face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0, fr_t]) children();
// 2D: the part of the letters whose whole climb of h above it stays inside
// them, sampled every lt_step. The same steps for every slab, so each deeper
// slab lies inside the one in front of it and no cut can close over a pocket.
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
// The cut, in lt_n slabs, each as deep as its ceiling allows. Built from 2D
// slabs rather than sheared copies of one prism: the copies' sides lay in
// shared planes and left zero-area faces.
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
// The letters and the board's hole are cut from the SAME placed cutter, so
// their faces are one computation (placed as one already-cut solid, the
// cemetery's linings came out a rounding error off their holes).
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}
```

<!-- /TRASH 20261007-001 -->
<!-- TRASH id=20261007-002 date=2026-10-07 kind=snippet source="openscad_models/haunted_town/post_office/haunted_post_office.scad" reason="Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print." -->
## 20261007-002 · 2026-10-07 · snippet · `openscad_models/haunted_town/post_office/haunted_post_office.scad`
**Reason:** Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print.  
**Payload:** `data/trash/files/20261007-002__snippet.txt`

```
// The letters are CARVED 0.6 into the board and lined with the accent part
// (2026-09-26). As a flush inlay they were colour alone: a one-colour print,
// or a slicer that put every part on one filament, lost the sign entirely.
// The cut's ceilings rise outward at 58 deg -- a straight-cut 0.6
// recess drew 1,528 support moves on a test block, the sheared one none.
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(58);  lt_n = 8;
module sign_text() text("POST OFFICE", size = 4.4, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.04);
module sign_at() face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0.3, fr_t]) children();
// 2D: the part of the letters whose whole climb of h above it stays inside
// them, sampled every lt_step. The same steps for every slab, so each deeper
// slab lies inside the one in front of it and no cut can close over a pocket.
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
// The cut, in lt_n slabs, each as deep as its ceiling allows. Built from 2D
// slabs rather than sheared copies of one prism: the copies' sides lay in
// shared planes and left zero-area faces.
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
// The letters and the board's hole are cut from the SAME placed cutter, so
// their faces are one computation (placed as one already-cut solid, the
// cemetery's linings came out a rounding error off their holes).
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}
```

<!-- /TRASH 20261007-002 -->
<!-- TRASH id=20261007-003 date=2026-10-07 kind=snippet source="openscad_models/haunted_town/general_store/haunted_general_store.scad" reason="Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print." -->
## 20261007-003 · 2026-10-07 · snippet · `openscad_models/haunted_town/general_store/haunted_general_store.scad`
**Reason:** Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print.  
**Payload:** `data/trash/files/20261007-003__snippet.txt`

```
// The letters are CARVED 0.6 into the board and lined with the accent part
// (2026-09-26). As a flush inlay they were colour alone: a one-colour print,
// or a slicer that put every part on one filament, lost the sign entirely.
// The cut's ceilings rise outward at 61 deg, 58 plus the front's forward lean, -- a straight-cut 0.6
// recess drew 1,528 support moves on a test block, the sheared one none.
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(61);  lt_n = 8;
// Spacing 1.06, not 1.04 (2026-09-26): at 1.04 the carve's stepped ceilings
// left a knife edge where CGAL joined the lining to the board, and the union
// failed the watertight gate. Nudging the sign, the step (0.19 drew supports
// under every letter: only 0.2 steps sit on the layers) or a proud lining all
// just moved it; 1.06 closed it, and MERCANTILE is 51.5 of the board's 56 mm.
module sign_text() text("MERCANTILE", size = 5.2, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.06);
module sign_at() on_face(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0.3, fr_t]) children();
// 2D: the part of the letters whose whole climb of h above it stays inside
// them, sampled every lt_step. The same steps for every slab, so each deeper
// slab lies inside the one in front of it and no cut can close over a pocket.
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
// The cut, in lt_n slabs, each as deep as its ceiling allows. Built from 2D
// slabs rather than sheared copies of one prism: the copies' sides lay in
// shared planes and left zero-area faces.
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
// The letters and the board's hole are cut from the SAME placed cutter, so
// their faces are one computation (placed as one already-cut solid, the
// cemetery's linings came out a rounding error off their holes).
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}
```

<!-- /TRASH 20261007-003 -->
<!-- TRASH id=20261007-004 date=2026-10-07 kind=snippet source="openscad_models/haunted_town/undertaker/haunted_undertaker.scad" reason="Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print." -->
## 20261007-004 · 2026-10-07 · snippet · `openscad_models/haunted_town/undertaker/haunted_undertaker.scad`
**Reason:** Haunted Town sign letters changed from carved-and-lined to raised (Scott, 2026-10-07): the carve read poorly on the one-colour post office print.  
**Payload:** `data/trash/files/20261007-004__snippet.txt`

```
// carved 0.6 into the board and lined with the accent (the bakery's method)
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(58);  lt_n = 8;
module sign_text() text("UNDERTAKER", size = 4.0, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.06);
module sign_at() face_tf(1, 0, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0, fr_t]) children();
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}
```

<!-- /TRASH 20261007-004 -->
<!-- TRASH id=20261007-005 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/coaching_inn/victorian_coaching_inn.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-005 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/coaching_inn/victorian_coaching_inn.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-005__snippet.txt`

```
// the sign: a brick-red board on the plaster, INN inlaid white and flush
```

<!-- /TRASH 20261007-005 -->
<!-- TRASH id=20261007-006 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/coaching_inn/victorian_coaching_inn.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-006 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/coaching_inn/victorian_coaching_inn.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-006__snippet.txt`

```
module sign_text() intersection() {
    sign_board();
    nf(3, dr_u, sg_z + sg_h / 2) translate([0, 0, 0.2]) linear_extrude(2)
        text("INN", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.0);
}
```

<!-- /TRASH 20261007-006 -->
<!-- TRASH id=20261007-007 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/santas_workshop/victorian_santas_workshop.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-007 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/santas_workshop/victorian_santas_workshop.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-007__snippet.txt`

```
// the sign: a slate board, SANTA'S / WORKSHOP inlaid white and flush
```

<!-- /TRASH 20261007-007 -->
<!-- TRASH id=20261007-008 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/santas_workshop/victorian_santas_workshop.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-008 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/santas_workshop/victorian_santas_workshop.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-008__snippet.txt`

```
module sign_text() intersection() {
    sign_board();
    nf(3, dr_u, sg_z + sg_h / 2) translate([0, 0, 0.2]) linear_extrude(2)
        for (l = [["SANTA'S", 2.6], ["WORKSHOP", -2.6]]) translate([0, l[1]])
            text(l[0], size = 3.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.0);
}
```

<!-- /TRASH 20261007-008 -->
<!-- TRASH id=20261007-009 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/victorian/toy_shop/victorian_toy_shop.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-009 · 2026-10-07 · snippet · `openscad_models/christmas_village/victorian/toy_shop/victorian_toy_shop.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-009__snippet.txt`

```
// the letters, raised on the fascia
module toys() bplace(1, (by_g[1] + by_t) / 2 + 0.2) relief_up(-0.4, 0.6)
```

<!-- /TRASH 20261007-009 -->
<!-- TRASH id=20261007-010 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/gingerbread/sweet_shop/gingerbread_sweet_shop.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-010 · 2026-10-07 · snippet · `openscad_models/christmas_village/gingerbread/sweet_shop/gingerbread_sweet_shop.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-010__snippet.txt`

```
// SWEETS round the front, over the shop's ridge, inlaid flush: raised, every
// level stroke (the E's arms, the T's bar) came to a knife edge under its
// sloped underside, down to 0.01 mm
module sweets() intersection() {
    difference() { cylinder(r = T(0)[0] + 0.01, h = 100, $fn = FNC); cylinder(r = T(0)[0] - 0.6, h = 100, $fn = FNC); }
    cyl_relief(T(0)[0], 270, 56.2, 12.5, 0.6) translate([0, 0, -1.5]) linear_extrude(2)
        text("SWEETS", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.08);
}
```

<!-- /TRASH 20261007-010 -->
<!-- TRASH id=20261007-011 date=2026-10-07 kind=snippet source="openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad" reason="Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print." -->
## 20261007-011 · 2026-10-07 · snippet · `openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad`
**Reason:** Christmas village signs changed to raised letters (Scott, 2026-10-07): flush inlays vanish on a one-colour print.  
**Payload:** `data/trash/files/20261007-011__snippet.txt`

```
module cocoa_text() press(270, 55.8)
    text("COCOA", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.08);
```

<!-- /TRASH 20261007-011 -->
<!-- TRASH id=20261008-001 date=2026-10-08 kind=snippet source="victorian_santas_workshop.scad" reason="Toy window art given relief so a white print shows it (2026-10-08)." -->
## 20261008-001 · 2026-10-08 · snippet · `victorian_santas_workshop.scad`
**Reason:** Toy window art given relief so a white print shows it (2026-10-08).  
**Payload:** `data/trash/files/20261008-001__snippet.txt`

```
module bw_art() nf(3, BW_u, BW_z) translate([0, 0, -recess - pane_t]) linear_extrude(pane_t) pane_art2d();
```

<!-- /TRASH 20261008-001 -->
<!-- TRASH id=20261008-002 date=2026-10-08 kind=snippet source="openscad_models/christmas_village/gingerbread/candy_cane_chapel/gingerbread_candy_cane_chapel.scad" reason="Crook's raised rings removed: an 11 mm rod leaning to 40 deg; the rings needed 1,413 support moves even clipped clear of base and tip (2026-10-08)" -->
## 20261008-002 · 2026-10-08 · snippet · `openscad_models/christmas_village/gingerbread/candy_cane_chapel/gingerbread_candy_cane_chapel.scad`
**Reason:** Crook's raised rings removed: an 11 mm rod leaning to 40 deg; the rings needed 1,413 support moves even clipped clear of base and tip (2026-10-08)  
**Payload:** `data/trash/files/20261008-002__snippet.txt`

```
module cr_at_g(i, d) let (p = cr_pts(i)) translate([TC[0] + p[0], TC[1], cr_z0 + p[1]]) sphere(r = cr_r(i) + d, $fn = 24);
module crook_g(d) for (i = [0 : cr_n - 1]) hull() { cr_at_g(i, d); cr_at_g(i + 1, d); }
// Climbing 2 SH per 1 out, not SH: on stripes tilted 28 deg, SH alone left the
// slicer propping a test column's (the turret house, 2026-10-08); twice that
// sliced clean. And clear of the tip's end cap, which faces down past the rod.
module crook_stripes_up() for (k = [0 : 1]) intersection() {
    difference() { crook_g((k + 1) * 0.15); crook_g(k * 0.15); }
    crook_stripes();
    translate([0, 0, 2 * SH * (k + 1) * 0.15]) crook_stripes();
    translate([-100, -100, 0]) cube([200, 200, cr_z0 + cr_pts(cr_n)[1] - cr_r(cr_n)]);
}
```

<!-- /TRASH 20261008-002 -->
<!-- TRASH id=20261008-003 date=2026-10-08 kind=snippet source="openscad_models/christmas_village/gingerbread/turret_house/gingerbread_turret_house.scad" reason="Turret spire's raised rings removed, as the chapel crook's: a bent candy-cane rod leaning to 40 deg (2026-10-08)" -->
## 20261008-003 · 2026-10-08 · snippet · `openscad_models/christmas_village/gingerbread/turret_house/gingerbread_turret_house.scad`
**Reason:** Turret spire's raised rings removed, as the chapel crook's: a bent candy-cane rod leaning to 40 deg (2026-10-08)  
**Payload:** `data/trash/files/20261008-003__snippet.txt`

```
module sp_at_g(i, d) let (p = sp_pts(i)) translate([tx + p[0] * cos(tc_ang), ty + p[0] * sin(tc_ang), sp_z0 + p[1]]) sphere(r = sp_r(i) + d, $fn = 24);
module spire_g(d) for (i = [0 : sp_n - 1]) hull() { sp_at_g(i, d); sp_at_g(i + 1, d); }
module spire_stripes_up() for (k = [0 : 1]) lean() intersection() {
    difference() { spire_g((k + 1) * 0.15); spire_g(k * 0.15); }
    stripe_slabs([tx, ty], sp_z0 + 1, sp_z0 + 12, 2.2, 0.9, 28);
    translate([0, 0, 2 * SH * (k + 1) * 0.15]) stripe_slabs([tx, ty], sp_z0 + 1, sp_z0 + 12, 2.2, 0.9, 28);
    translate([-100, -100, 0]) cube([200, 200, sp_z0 + sp_pts(sp_n)[1] - sp_r(sp_n)]);
}
```

<!-- /TRASH 20261008-003 -->
<!-- TRASH id=20261008-004 date=2026-10-08 kind=snippet source="openscad_models/christmas_village/gingerbread/candy_cane_chapel/gingerbread_candy_cane_chapel.scad" reason="Chapel tower's raised spiral bands (wall, inner and swept spire): sliced on the old chapel they needed ~21,000 support moves (outer) and ~56,000 (with inner) at every lower edge; steeper climb, 0.1 steps, a lower top and clipping to outside the nave did not clear them (2026-10-08)" -->
## 20261008-004 · 2026-10-08 · snippet · `openscad_models/christmas_village/gingerbread/candy_cane_chapel/gingerbread_candy_cane_chapel.scad`
**Reason:** Chapel tower's raised spiral bands (wall, inner and swept spire): sliced on the old chapel they needed ~21,000 support moves (outer) and ~56,000 (with inner) at every lower edge; steeper climb, 0.1 steps, a lower top and clipping to outside the nave did not clear them (2026-10-08)  
**Payload:** `data/trash/files/20261008-004__snippet.txt`

```
module tower_prof2d() {
    polygon([[rti - 0.3, plinth_h - 0.5], [rt, plinth_h - 0.5], [rt, R_zc(RS, rt) + 0.6], [rti - 0.3, R_zc(RS, rti - 0.3) + 0.6]]);
    R_full(RS, kv0s);
}
module tower_shell(t0, t1) at_tc() rotate_extrude($fn = FNT) difference() {
    intersection() { offset(delta = t1) tower_prof2d(); translate([0, plinth_h]) square([100, 300]); }
    offset(delta = t0) tower_prof2d();
    R_room(RS);
}
// 0.05 on into the wall: one that ends at the wall's face only touches it, and
// the union can keep the face between (the coaching inn, 2026-10-08)
module tower_in_shell(t0, t1) at_tc() rotate_extrude($fn = FNT)
    translate([rti - t1, plinth_h]) square([t1 - t0 + 0.05, RS[0] - 1 - plinth_h]);
// A band raised t its stripe moved up SH * t: the stripe narrowed by the angle
// that climb turns through, so its upper edge (in angle) is the one that steps.
// Built narrowed rather than as the stripe intersected with a raised copy of
// itself: the two copies' twisted facets crossed, and left 1,838 crumbs of
// band up the spire and round the door (2026-10-08).
function st_climb(t) = st_w - 360 * SH * t / st_P;
// the straight wall's bands stop under the eave's flare (st_zw); the spire's
// are swept (spire_bands)
st_zw = 87.9;
module stripe_bands() {
    zt = R_top(RS, 0) + 1;
    for (i = [0 : 1]) intersection() {
        tower_shell(i * 0.2, (i + 1) * 0.2); helix(plinth_h - 1, zt, st_climb((i + 1) * 0.2));
        translate([-100, -100, 0]) cube([200, 200, st_zw]);
    }
    spire_bands();
    difference() {
        for (i = [0 : 2]) intersection() { tower_in_shell(i * 0.2, (i + 1) * 0.2); helix(plinth_h - 1, zt, st_climb((i + 1) * 0.2)); }
        // through the doorway, the inner bands stop at its edge, the cut over
        // its head climbing SH per 1 into the room
        cyl_relief(rt, dth, plinth_h, door_a + 2.4) relief_hole(-wall, -wall - 1.2, 0.5, -SH) offset(delta = 0.2) polygon(arch_pts(door_a, door_h));
    }
}
// No band over the door and the windows: there it stood as a skin over their
// frames, the door's leaf and the panes. It stops at each frame's edge, and
// the frame below holds up whatever runs over a head.
module tower_frames_clear() {
    tw_frames(); door_frame();
    for (w = TW) cyl_relief(rt, w[0], w[1], tframe_U(w)) translate([0, 0, -1]) linear_extrude(3) offset(r = fr_w) win_outline(tw(w));
    cyl_relief(rt, dth, plinth_h, door_a + fr_w + 1.2) translate([0, 0, -1]) linear_extrude(3) offset(r = fr_w) polygon(arch_pts(door_a, door_h));
}
// THE SPIRE'S BANDS, swept along its profile rather than cut from a shell: a
// 0.2 mm shell on the 68 deg spire, cut by the twisted prism's facets, came
// apart into 1,274 crumbs (2026-10-08). Each band is one solid from the eave's
// edge to below the crook: its inner face 0.05 inside the spire, its outer
// 0.4 out along the profile's normal, and its upper edge in angle trimmed by
// the climb, so that side slopes SH up per 1 out like every band below it.
sp_h = 0.4;  sp_n = 110;  sp_J = 8;
function sp_v(i) = RS[5] - 0.2 - (RS[5] - 1.6) * i / (sp_n - 1);
function sp_p(i) = [sp_v(i), R_top(RS, sp_v(i))];
function sp_nrm(i) = let (a = sp_p(max(i - 1, 0)), b = sp_p(min(i + 1, sp_n - 1)), t = (b - a) / norm(b - a)) [t[1], -t[0]];
function sp_last() = max([for (i = [0 : sp_n - 1]) if (sp_p(i)[1] < cr_z0 - 1) i]);
function sp_pt(i, j, s) = let (q = sp_p(i) + sp_nrm(i) * (s == 0 ? -0.05 : sp_h),
        a = 360 * (q[1] - (plinth_h - 1)) / st_P + j / sp_J * (s == 0 ? st_w : st_climb(sp_h)))
    [q[0] * cos(a), q[0] * sin(a), q[1]];
module spire_band() let (N = sp_last() + 1, J = sp_J, id = function (i, j, s) (i * (J + 1) + j) * 2 + s)
    polyhedron([for (i = [0 : N - 1], j = [0 : J], s = [0 : 1]) sp_pt(i, j, s)], concat(
        [for (i = [0 : N - 2], j = [0 : J - 1]) [id(i, j, 1), id(i + 1, j, 1), id(i + 1, j + 1, 1), id(i, j + 1, 1)]],
        [for (i = [0 : N - 2], j = [0 : J - 1]) [id(i, j + 1, 0), id(i + 1, j + 1, 0), id(i + 1, j, 0), id(i, j, 0)]],
        [for (i = [0 : N - 2]) [id(i, 0, 0), id(i + 1, 0, 0), id(i + 1, 0, 1), id(i, 0, 1)]],
        [for (i = [0 : N - 2]) [id(i, J, 1), id(i + 1, J, 1), id(i + 1, J, 0), id(i, J, 0)]],
        [for (j = [0 : J - 1]) [id(0, j, 0), id(0, j, 1), id(0, j + 1, 1), id(0, j + 1, 0)]],
        [for (j = [0 : J - 1]) [id(N - 1, j + 1, 0), id(N - 1, j + 1, 1), id(N - 1, j, 1), id(N - 1, j, 0)]]));
module spire_bands() at_tc() for (k = [0 : st_n - 1]) rotate(k * 360 / st_n) spire_band();
// where the tower's wall is cut away inside the nave (its doorway), no band
module stripe_relief() difference() { stripe_bands(); difference() { nave_room(); turret_partition(); } tower_frames_clear(); }
```

<!-- /TRASH 20261008-004 -->
<!-- TRASH id=20261008-005 date=2026-10-08 kind=snippet source="openscad_models/christmas_village/gingerbread/cottage/gingerbread_cottage.scad" reason="Cottage canes' raised stripes removed: trimmed to a narrow cane's flat front they left slivers (0.04-0.89 mm spans) and the 1st-percentile wall at 1.19 mm (2026-10-08)" -->
## 20261008-005 · 2026-10-08 · snippet · `openscad_models/christmas_village/gingerbread/cottage/gingerbread_cottage.scad`
**Reason:** Cottage canes' raised stripes removed: trimmed to a narrow cane's flat front they left slivers (0.04-0.89 mm spans) and the 1st-percentile wall at 1.19 mm (2026-10-08)  
**Payload:** `data/trash/files/20261008-005__snippet.txt`

```
module cane_stripes_up() sclip(Rw, fr_t + 0.81) for (s = [-1, 1]) srelief(Rw, s * cane_s, plinth_h, cane_R * 2 + cane_w + 0.6)
    translate([0, 0, fr_t + 0.5]) art_skirt(0.3, 2) w12() intersection() { top_face(fr_t + 0.8) cane2d(-s); stripes2d(); }
```

<!-- /TRASH 20261008-005 -->
<!-- TRASH id=20261009-001 date=2026-10-09 kind=snippet source="tools/viewer/app.js" reason="Replaced by the fetch-and-parse loader (plates read as data, real progress); the <script> path survives as loadJobScriptTag for file://" -->
## 20261009-001 · 2026-10-09 · snippet · `tools/viewer/app.js`
**Reason:** Replaced by the fetch-and-parse loader (plates read as data, real progress); the <script> path survives as loadJobScriptTag for file://  
**Payload:** `data/trash/files/20261009-001__snippet.txt`

```javascript
function loadJob(id) {
  if (id === currentId && JOB) { return; }
  currentId = id;
  loading.hidden = false;
  loading.firstChild.textContent = 'Loading ' +
    (INDEX.filter(function (j) { return j.id === id; })[0] || {name:id}).name;
  paintJobList();
  setPlaying(false);
  var s = document.createElement('script');
  s.setAttribute('data-job', id);
  s.src = 'jobs/' + id + '.js';
  s.onerror = function () {
    loading.innerHTML = '<div style="text-align:center;color:var(--bad)">' +
      'Could not load jobs/' + id + '.js</div>';
  };
  document.body.appendChild(s);
}
```

<!-- /TRASH 20261009-001 -->
<!-- TRASH id=20261009-002 date=2026-10-09 kind=snippet source="openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad" reason="Cocoa cafe: mug windows' inner thickening (art_in) overhung on the curved inner wall; the slicer propped it from the mug floor (gate 2026-10-09)" -->
## 20261009-002 · 2026-10-09 · snippet · `openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad`
**Reason:** Cocoa cafe: mug windows' inner thickening (art_in) overhung on the curved inner wall; the slicer propped it from the mug floor (gate 2026-10-09)  
**Payload:** `data/trash/files/20261009-002__snippet.txt`

```
    cyl_relief(MRi, w[0], w[1], w[2] + 2.2, 0.6) art_in(0.8, 4) mw2d(w);
```

<!-- /TRASH 20261009-002 -->
<!-- TRASH id=20261009-003 date=2026-10-09 kind=snippet source="openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad" reason="Cocoa cafe: stirrer stripe relief on the tilted cane needed supports; stripes left to paint" -->
## 20261009-003 · 2026-10-09 · snippet · `openscad_models/christmas_village/gingerbread/cocoa_cafe/gingerbread_cocoa_cafe.scad`
**Reason:** Cocoa cafe: stirrer stripe relief on the tilted cane needed supports; stripes left to paint  
**Payload:** `data/trash/files/20261009-003__snippet.txt`

```
module st_at_g(i, d) let (p = st_pts(i)) rotate(st_th) translate([st_r0 + p[0], 0, st_z0 + p[1]]) sphere(r = 1.9 + d, $fn = 24);
module stirrer_g(d) for (i = [0 : st_n - 1]) hull() { st_at_g(i, d); st_at_g(i + 1, d); }
module stirrer_stripes_up() for (k = [0 : 1]) intersection() {
    difference() { stirrer_g((k + 1) * 0.15); stirrer_g(k * 0.15); }
    stirrer_stripes();
    translate([0, 0, SH * (k + 1) * 0.15]) stirrer_stripes();
}
    stirrer_stripes_up();
```

<!-- /TRASH 20261009-003 -->
<!-- TRASH id=20261009-004 date=2026-10-09 kind=snippet source="openscad_models/christmas_village/gingerbread/cookie_clock_tower/gingerbread_cookie_clock_tower.scad" reason="Cookie clock tower: stripe relief on the tilted cane needed 4,638 support moves on a fresh union (2026-10-09); stripes left to paint" -->
## 20261009-004 · 2026-10-09 · snippet · `openscad_models/christmas_village/gingerbread/cookie_clock_tower/gingerbread_cookie_clock_tower.scad`
**Reason:** Cookie clock tower: stripe relief on the tilted cane needed 4,638 support moves on a fresh union (2026-10-09); stripes left to paint  
**Payload:** `data/trash/files/20261009-004__snippet.txt`

```
module cr_at_g(i, d) let (p = cr_pts(i)) translate([p[0], 0, cr_z0 + p[1]]) sphere(r = cr_r(i) + d, $fn = 24);
module cane_g(d) {
    translate([0, 0, z_co(0) - 3]) cylinder(r = 1.9 + d, h = cn_z0 + cn_h - z_co(0) + 3, $fn = 24);
    for (i = [0 : cr_n - 1]) hull() { cr_at_g(i, d); cr_at_g(i + 1, d); }
}
module cane_slabs(dz) for (z = [cn_z0 + 1.0 : 2.4 : cr_z0 + cr_L + 2]) translate([0, 0, z + dz]) rotate([0, -28, 0]) cube([20, 20, 1.0], center = true);
// above the cone's cap only: below it the rod is buried in the icing
module cane_stripes_up() for (k = [0 : 1]) intersection() {
    difference() { cane_g((k + 1) * 0.15); cane_g(k * 0.15); }
    cane_slabs(0);
    cane_slabs(SH * (k + 1) * 0.15);
    translate([-50, -50, cn_z0]) cube([100, 100, 100]);
}
    cane_stripes_up();
```

<!-- /TRASH 20261009-004 -->
<!-- TRASH id=20261010-001 date=2026-10-10 kind=snippet source="tools/viewer/app.js" reason="buildEnvironment's softbox room: every panel sat beyond r128 PMREM fromScene's far plane (100) and never rendered; replaced by the captured Poly Haven studio with a uniform-dark placeholder" -->
## 20261010-001 · 2026-10-10 · snippet · `tools/viewer/app.js`
**Reason:** buildEnvironment's softbox room: every panel sat beyond r128 PMREM fromScene's far plane (100) and never rendered; replaced by the captured Poly Haven studio with a uniform-dark placeholder  
**Payload:** `data/trash/files/20261010-001__snippet.txt`

```javascript
// ── environment ────────────────────────────────────────────────────────────
// The thing that actually makes metal look like metal. Without an environment
// map a MeshStandardMaterial with metalness 0.9 has nothing to reflect and
// renders nearly black -- which is the classic "I switched to PBR and it got
// worse" failure. This builds a small studio by hand (overhead softbox, cool
// fill from one side, warm bounce from below) and runs it through PMREM so
// rough surfaces get a properly blurred version of it.
function buildEnvironment() {
  var pmrem = new THREE.PMREMGenerator(renderer);
  var room = new THREE.Scene();
  room.background = new THREE.Color(lin(0x0b0d12));

  function panel(w, h, d, color, intensity, x, y, z, rx, ry) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d),
      new THREE.MeshBasicMaterial({color: lin(color)}));
    m.material.color.multiplyScalar(intensity);
    m.position.set(x, y, z);
    if (rx) { m.rotation.x = rx; }
    if (ry) { m.rotation.y = ry; }
    room.add(m);
    return m;
  }

  // First pass at these numbers had a 1.5-intensity cool fill and it turned
  // the whole machine powder blue -- an environment map lights EVERYTHING, so
  // a tint that looks like a tasteful accent in isolation becomes the colour
  // of the product. Warm key, restrained cool, and a dark back wall so metal
  // has something black to reflect: without a dark region in the environment,
  // polished surfaces have no contrast and read as flat grey plastic.
  panel(600, 10, 420, 0xfff2de, 2.2,    0,  360,   40, 0, 0);   // key softbox
  panel(10, 460, 420, 0xa8c0e0, 0.45, -420,  60,    0, 0, 0);   // cool fill
  panel(10, 460, 420, 0xffcfa0, 0.30,  420,  40,    0, 0, 0);   // warm kicker
  panel(600, 10, 420, 0x5a6270, 0.18,   0, -300,    0, 0, 0);   // floor bounce
  panel(600, 460, 10, 0x05070b, 1.0,    0,   40, -360, 0, 0);   // back wall

  envRT = pmrem.fromScene(room, 0.5);
  scene.environment = envRT.texture;
  room.traverse(function (o) {
    if (o.geometry) { o.geometry.dispose(); }
    if (o.material) { o.material.dispose(); }
  });
  pmrem.dispose();
}
```

<!-- /TRASH 20261010-001 -->
<!-- TRASH id=20261010-002 date=2026-10-10 kind=snippet source="tools/viewer/virtual_p1s.html" reason="View-options popover CSS and the stacked phone layout, replaced by stage camera tools, tabbed rails and the app-style phone layout (Scott, 2026-10-10: too much scrolling)" -->
## 20261010-002 · 2026-10-10 · snippet · `tools/viewer/virtual_p1s.html`
**Reason:** View-options popover CSS and the stacked phone layout, replaced by stage camera tools, tabbed rails and the app-style phone layout (Scott, 2026-10-10: too much scrolling)  
**Payload:** `data/trash/files/20261010-002__snippet.txt`

```html
/* ── view menu ────────────────────────────────────── */
.viewbtns button[aria-pressed="true"]{background:#241a0f;color:var(--amber-soft)}
.viewmenu{position:relative}
.viewmenu summary{list-style:none;padding:7px 10px;border:1px solid var(--line-hi);border-radius:3px;
  background:var(--rail);font-size:11.5px;cursor:pointer;color:var(--dim)}
.viewmenu summary::-webkit-details-marker{display:none}
.viewmenu summary::after{content:' +';color:var(--amber-soft)}
.viewmenu[open] summary::after{content:' −'}
.viewmenu .viewbtns{position:absolute;right:0;bottom:calc(100% + 8px);z-index:8;width:420px;
  padding:6px;background:var(--panel);border:1px solid var(--line-hi);border-radius:4px;
  box-shadow:0 14px 34px rgba(0,0,0,.48)}
.viewbtns{display:flex;gap:1px;background:var(--line);border:1px solid var(--line);
  flex-wrap:wrap;min-width:0}
.speeds{flex-wrap:wrap;min-width:0}
.viewbtns button{padding:6px 10px;background:var(--rail);font-size:11.5px}
.viewbtns button:hover{color:var(--amber)}
@media (max-width:1180px){
  /* Source order puts both rails before the viewport; on a phone the print
     itself has to come first, so the narrow layout re-places by area. */
  #app{grid-template-columns:minmax(0,1fr);
    grid-template-areas:"h" "s" "f" "l" "r";
    grid-template-rows:auto 56vh auto auto auto;height:auto}
  header{grid-area:h} #stage{grid-area:s} footer{grid-area:f}
  #left{grid-area:l} #right{grid-area:r}
  aside{max-height:none;overflow:visible}
  #jobs{max-height:none}
  #stage{min-height:340px}
  header{padding:8px 14px;gap:8px}
  header h1{font-size:15px}
  /* The subtitle is explanatory, not operational; on a phone it costs
     ~50px of the 3D viewport for nothing. */
  header .sub{display:none}
  #buildchip{font-size:10px}
  .scrub{order:5;flex-basis:100%;min-width:0}

  /* The transport is the only control you use continuously, and the page is
     ~2700px tall on a phone -- letting it scroll away means scrolling back up
     to pause. Pinned, with the last rail padded so nothing hides under it. */
  footer{position:sticky;bottom:0;z-index:6;
    box-shadow:0 -10px 22px rgba(0,0,0,.5)}
  #right{padding-bottom:72px}

  /* Thumb-sized targets. Measured at 22-29px before this; 44 is the floor. */
  .leg{min-height:44px;padding:4px 6px}
  .modeswap button{padding:13px 4px}
  .speeds button,.viewbtns button{padding:13px 11px;font-size:11px}
  .viewbtns,.speeds{flex:1 1 100%}
  /* The new controls, sized for a thumb. The view menu drops out of its
     popover and becomes an inline block, because a 420px popover anchored to
     the bottom of a phone viewport has nowhere to go. */
  .viewmenu{flex:1 1 100%}
  .viewmenu summary{padding:13px 11px;text-align:center}
  .viewmenu .viewbtns{position:static;width:auto;margin-top:5px;box-shadow:none}
  .header-actions{width:100%;order:5}
  .shellbtn{flex:1;justify-content:center;min-height:40px}
  .layernav{flex:1 1 100%}
  .layernav button{flex:1;height:44px}
  .layernav label{flex:2;justify-content:center;height:44px}
  .plate-tools{grid-template-columns:minmax(0,1fr) 112px}
  .jobfav{width:40px;height:40px;font-size:19px}
  .job{padding-right:50px}
  /* Collapsing a rail is a desktop affordance: at this width the rails are
     stacked sections of one scrolling page, and hiding one just removes
     content with no space reclaimed. The buttons stay for Copy view / Help. */
  #app.left-collapsed,#app.right-collapsed,#app.left-collapsed.right-collapsed{
    grid-template-columns:minmax(0,1fr)}
  #app.left-collapsed #left,#app.right-collapsed #right{display:block}
  .tbtn{width:46px;height:46px}
  .tabs button{padding:15px 4px}
  select,input[type=number]{padding:12px 9px}
  input[type=range]{height:44px}
  input[type=range]::-webkit-slider-thumb{width:20px;height:20px;margin-top:-8px}
  input[type=range]::-moz-range-thumb{width:18px;height:18px}
  .mat td{padding:9px 6px 9px 0}
  .kv td{padding:7px 0}
  #hint{font-size:10px}
}
```

<!-- /TRASH 20261010-002 -->
<!-- TRASH id=20261014-001 date=2026-10-14 kind=file source="openscad_models/christmas_village/accessories/horse_sleigh/HORSE_SLEIGH_LEFT_OUT.md" reason="Superseded: the horse sleigh was built after all (split horse, 2026-10-14); see HORSE_SLEIGH_PRINTING.md" -->
## 20261014-001 · 2026-10-14 · file · `openscad_models/christmas_village/accessories/horse_sleigh/HORSE_SLEIGH_LEFT_OUT.md`
**Reason:** Superseded: the horse sleigh was built after all (split horse, 2026-10-14); see HORSE_SLEIGH_PRINTING.md  
**Payload:** `data/trash/files/20261014-001__HORSE_SLEIGH_LEFT_OUT.md`

```
# Horse sleigh — left out (2026-10-13)

Scott circled the horse sleigh from the second batch of accessory studies
with one condition: "If the horse and carriage can't look better then leave
them out." They are left out. This folder keeps the attempt so it is not
repeated blind.

## Why

A horse standing on four legs has two things that hang in the air: its belly
between the legs, and its head held out in front of its neck. At village
scale, with no supports, both have to be closed off:

- **The belly** can be closed into a point between the legs, if the legs
  splay fore and aft: they meet the body close together and stand apart.
  That part works, Dala-horse fashion.
- **The head** is the problem. Its muzzle is the lowest point of a shape held
  out in front, an island the slicer must prop. The only printable cure is to
  carry the jaw straight down into the chest, as a chess knight's is. That
  turns head, throat and neck into one thick column, and the horse loses the
  one line that makes it read as a horse.

Two passes (`horse_study.scad`, renders in `images/`, from OpenSCAD's preview,
not a print) came out as a toy cow and then a llama. Neither is better than
the study it was meant to improve on.

## What would change the answer

- **Supports.** With tree supports under the muzzle and belly, a proper horse
  prints; the shop's standard is no supports on anything sold, so that is
  Scott's call.
- **The sleigh alone.** A red sleigh piled with presents, waiting in the
  snow, prints without support (runners sunk in snow, the dash leaning
  forward under 40 degrees). Not built: Scott's "leave them out" covered both.
```

<!-- /TRASH 20261014-001 -->
<!-- TRASH id=20261014-002 date=2026-10-14 kind=file source="openscad_models/christmas_lanterns/lantern_mesh.py" reason="Moved to tools/part_mesh.py (identical code, generic docstring) when the village accessories became its second user" -->
## 20261014-002 · 2026-10-14 · file · `openscad_models/christmas_lanterns/lantern_mesh.py`
**Reason:** Moved to tools/part_mesh.py (identical code, generic docstring) when the village accessories became its second user  
**Payload:** `data/trash/files/20261014-002__lantern_mesh.py`

```
#!/usr/bin/env python3
"""Mesh steps the lanterns need that OpenSCAD 2021 does badly (2026-10-13).

    lantern_mesh.py check part.stl ...              each part closed; every pair disjoint
    lantern_mesh.py union out.stl part.stl ...      one body, for product_gate
    lantern_mesh.py wrap flat.stl out.stl --radius R --z Z [--minus m.stl ...]

check and union use manifold3d. CGAL took 3.5 hours to union Santa's
workshop's four parts and would not union imported STLs at all; manifold
does both in seconds and refuses an open mesh rather than guessing.

wrap bends a relief built flat (x along a face, y up, z out of it) round a
cylinder: x becomes the angle x / radius, y height above --z, z the distance
out from --radius. The flat mesh is subdivided first so its long triangles
follow the curve, and anything named by --minus is cut from the result, so a
relief wrapped a hair into its glass comes out touching it, not inside it.
"""
import argparse, itertools, math, sys
import numpy as np
import trimesh
import manifold3d as mf


def to_manifold(m: trimesh.Trimesh, name: str) -> mf.Manifold:
    # From the raw triangle soup, merged by manifold itself: CGAL writes two
    # solids that touch along a line as one edge shared by four faces, which
    # trimesh's own vertex merge turns into a non-manifold mesh manifold refuses.
    tri = np.asarray(m.vertices, np.float64)[np.asarray(m.faces)].reshape(-1, 3)
    mesh = mf.Mesh(vert_properties=tri.astype(np.float32), tri_verts=np.arange(len(tri), dtype=np.uint32).reshape(-1, 3))
    mesh.merge()
    out = mf.Manifold(mesh)
    if out.status() != mf.Error.NoError:
        sys.exit(f"{name}: manifold3d refuses it ({out.status()}) -- not a closed mesh")
    return out


def to_trimesh(m: mf.Manifold) -> trimesh.Trimesh:
    g = m.to_mesh()
    t = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)
    # Drop sheets that enclose nothing. The drum's welded union came back with
    # thirteen two-triangle back-to-back slivers beside its one real body, each
    # sharing an edge with it, so the body read as open (2026-10-13).
    cc = trimesh.graph.connected_components(t.face_adjacency, nodes=np.arange(len(t.faces)), min_len=1)
    keep = [c for c in cc if len(c) > 4 or abs(t.submesh([c], append=True).volume) > 1e-6]
    if len(keep) < len(cc):
        t = t.submesh(keep, append=True)
    return t


def load(path: str) -> mf.Manifold:
    return to_manifold(trimesh.load(path, force="mesh"), path)


def check(paths):
    ok = True
    ms = {}
    for p in paths:
        t = trimesh.load(p, force="mesh")
        ms[p] = to_manifold(t, p)
        print(f"  {'ok  ' if t.is_watertight else 'OPEN'}  {p}: {ms[p].volume():.1f} mm3, {len(t.faces)} faces")
        ok &= t.is_watertight
    for a, b in itertools.combinations(paths, 2):
        # parts that only touch come back with float32 noise: the hex lantern's
        # art, built on its glass's face, read 0.06 mm3 over ~1500 mm2 of contact
        v = (ms[a] ^ ms[b]).volume()
        if v > 0.1:
            ok = False
            print(f"  OVERLAP {a} / {b}: {v:.3f} mm3")
    print("PARTS OK: closed, no two overlap" if ok else "PARTS FAIL")
    return ok


def union(out, paths):
    u = mf.Manifold.batch_boolean([load(p) for p in paths], mf.OpType.Add)
    t = to_trimesh(u)
    t.export(out)
    print(f"{out}: {u.volume():.1f} mm3, {len(t.faces)} faces, watertight {t.is_watertight}, bodies {len(t.split(only_watertight=False))}")


def wrap(flat, out, radius, z, minus, step):
    # Weld first: where two pieces of the stepped relief touch along a line (the
    # drum's snowman, at its waist), the line stays a four-face edge through any
    # boolean, and trimesh -- and so product_gate -- reads the part as open. A
    # copy shifted 0.003 mm across the face turns each such line into a sliver
    # of overlap, and the union closes it (2026-10-13).
    m0 = to_manifold(trimesh.load(flat, force="mesh"), flat)
    m0
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261014-002 -->
<!-- TRASH id=20261025-001 date=2026-10-25 kind=file source="tools/api_server/main.py" reason="Before removing the digital-art workflows from Frank (Scott, 2026-10-25: switching to 3D prints and 3D print files). git history keeps it too." -->
## 20261025-001 · 2026-10-25 · file · `tools/api_server/main.py`
**Reason:** Before removing the digital-art workflows from Frank (Scott, 2026-10-25: switching to 3D prints and 3D print files). git history keeps it too.  
**Payload:** `data/trash/files/20261025-001__main.py`

```
#!/usr/bin/env python3
"""
OnBrandCraftz Mobile API Server

FastAPI backend powering the mobile dashboard app. Read-only + streaming chat.

Start:
  pip install -r tools/api_server/requirements.txt
  uvicorn tools.api_server.main:app --host 0.0.0.0 --port 8000 --reload

Deploy to Railway / Render: set env vars + point start command to this file.
"""

from __future__ import annotations

import asyncio
import base64
import codecs
import hashlib
import hmac
import inspect
import io
import json
import mimetypes
import os
import random
import re as _re
import secrets
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

if getattr(sys, "frozen", False):
    # PyInstaller desktop-app bundle (tools/desktop/backend.spec, 2026-07-08): the
    # frozen entry script's own __file__ no longer sits 3 directories under the repo
    # root (tools/api_server/main.py) the way it does when run from source. sys._MEIPASS
    # is PyInstaller's own documented attribute for "where the bundled data actually
    # is" -- NOT Path(sys.executable).parent, which in onedir mode (PyInstaller 6.x)
    # is one level too shallow: the executable sits in dist/frank-backend/, but the
    # bundled tools/ tree this spec collects via `datas` lands in
    # dist/frank-backend/_internal/tools/ (verified empirically -- a static-asset
    # 404 was the first sign sys.executable's parent was wrong).
    ROOT = Path(sys._MEIPASS).resolve()  # noqa: SLF001 -- documented PyInstaller API
else:
    ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# Load .env before importing shop tools
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

import anthropic
import openai
import business_config
import db  # local persistence layer (tools/api_server/db.py)
import oauth_providers  # Google / Apple Sign-In (tools/api_server/oauth_providers.py)
import seasonal_keywords  # noqa: E402
import tax_compliance_tools  # noqa: E402
import etsy_api
from etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402
import trademark_screening  # noqa: E402 — advisory pre-publish trademark check (Scott-gated, see module docstring)
import business_tracker  # noqa: E402 — GET /api/business-tracker.xlsx workbook builder
from resilience import (  # noqa: E402
    classify_tool_exception,
    retry_with_backoff,
    TransientToolError,
    CircuitBreaker,
    CircuitBreakerOpenError,
)

# Shared breaker for every Anthropic call site -- main.py has no single chokepoint
# analogous to EtsyAPIClient._request(), so each of the ~7 call sites routes through
# _anthropic_create() below instead.
_anthropic_breaker = CircuitBreaker("anthropic_api", db_module=db)
# Same pattern, separate breaker, for xAI/Grok text calls (2026-08-05) -- one
# breaker per external text provider, same style as _anthropic_breaker above
# rather than trying to generalize a single breaker across two SDKs with
# different exception types.
_xai_breaker = CircuitBreaker("xai_api", db_module=db)


# Known-good fall
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-001 -->
<!-- TRASH id=20261025-002 date=2026-10-25 kind=file source="tools/api_server/frank_hud_mockup.py" reason="Before removing the digital-art workflows from Frank (Scott, 2026-10-25: switching to 3D prints and 3D print files). git history keeps it too." -->
## 20261025-002 · 2026-10-25 · file · `tools/api_server/frank_hud_mockup.py`
**Reason:** Before removing the digital-art workflows from Frank (Scott, 2026-10-25: switching to 3D prints and 3D print files). git history keeps it too.  
**Payload:** `data/trash/files/20261025-002__frank_hud_mockup.py`

```
"""
FRANK Command Center — static clickable HTML/CSS/JS mockup (Build Order step 0.5).

No backend wiring. This is purely a visual sign-off artifact so Scott can react to the
look of the full landscape HUD (left nav + every panel from the reference screenshots,
rebranded FRANK) before any real engineering goes in underneath it. Served at /frank,
completely separate from the live production dashboard at / so there is zero risk to
the running Hub while this is reviewed.

The whole layout is built as a fixed 1440x900 "stage" that JS scales (and letterboxes)
to fit whatever viewport opens it — phone or desktop — so the HUD always renders at its
real proportions instead of the browser's mobile viewport squishing the columns.

Real wiring (live data, approval gate, relay, voice) is Step 1+ in the approved plan —
every nav tab/panel here is a placeholder shell with the real future data source noted
in a code comment, not invented numbers presented as fact. LLM Status only lists
providers we actually have wired (Anthropic, OpenAI, Etsy) — no fake Gemini/Groq/Ollama
tiles, per the "no fake tiles anywhere" rule in the plan.

Step 2 (in progress): wiring real data into this shell, panel by panel. The page is a
plain string template (not f-string/`.format()`, since the JS below is full of literal
`{}`) rendered by `render_frank_hud()` which substitutes business-identity placeholders
(%%AGENT_NAME%%/%%AGENT_SHORT%%/%%OWNER%%) at startup. Auth uses session cookies — the
APP_SECRET_TOKEN is never injected into the page source.
"""

import json

import business_config
import check_default_branch  # tools/ is on sys.path (main.py) -- single source of
# truth for "which branch is the real active one" (see that module's docstring on
# the 2026-07-10 stale-default-branch incident), reused here so the Files screen's
# "download everything from GitHub" link can't independently drift from it.

_FRANK_HUD_MOCKUP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<!-- maximum-scale=1/user-scalable=no removed 2026-07-08 (accessibility review, WCAG 1.4.4/1.4.10):
     blocking pinch/browser zoom locks out low-vision users entirely. fitStage() below no longer
     fights a deliberate zoom either — see the isMobileMode()/devicePixelRatio guard there. -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="%%AGENT_SHORT%%">
<meta name="theme-color" id="meta-theme-color" content="#241c2e">
<link rel="manifest" href="/frank-manifest.webmanifest">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<title>%%AGENT_SHORT%% — Command Center</title>
<script type="importmap">
{"imports": {
  "onnxruntime-web": "/static/vendor/onnxruntime-web/ort.wasm.bundle.min.mjs",
  "three": "/static/vendor/three/build/three.module.js"
}}
</script>
<!-- GSAP (vendored, /static/vendor/gsap/gsap.min.js) -- a classic global script, NOT an
     importmap entry: this is GSAP's UMD/global build, and its fallback-to-globalThis path
     (`(t=t||self).window=t.window||{}`) throws `Cannot set property window of #<Window>
     which has only a getter` when evaluated as a real ES module (top-level `this` is
     undefined there, so it falls through to `self`, i.e. `window`, and then tries to
     assign `window.window` -- a read-only self-reference on the real Window object).
     Confirmed via a real headless-Chrome run before wiring this in. Loaded as a plain
     script here so it attaches `window.gsap` the way GSAP's docs actually expect. -->
<script src="/static/vendor/gsap/gsap.min.js"></script>
<!-- video.js (vendored, /static/vendor/videojs/video.min.js + video-js.min.css, Apache-2.0) --
     UMD/global build like GSAP 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-002 -->
<!-- TRASH id=20261025-003 date=2026-10-25 kind=file source="tests/test_coloring_listing_photos.py" reason="Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only)." -->
## 20261025-003 · 2026-10-25 · file · `tests/test_coloring_listing_photos.py`
**Reason:** Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only).  
**Payload:** `data/trash/files/20261025-003__test_coloring_listing_photos.py`

```
"""
Tests for staging real coloring-pack pages as Etsy listing photos (2026-07-25).

COLOR1003 published successfully (after the file-resolution fix) but ended
up with zero listing photos -- coloring_pages has no AI listing-photo
pipeline like digital_planner's. Scott's direct instruction was to use the
product's own real pack pages as the photos, not build a lifestyle-photo
pipeline. Real wrinkle found while building this: the existing pale-
background quality gate (meant to catch lazy/blank AI renders) would reject
a raw coloring page's near-white corners as "washed out" -- Scott chose to
make that gate category-aware (skip it for coloring_pages, since white paper
is the honest, real look of this product) rather than build a flat-lay
compositing pipeline.

Covers:
  - _extract_coloring_page_images(): root-level-PNG filtering, evenly-spaced
    sampling when a pack has more than 10 pages, returns everything when <=10
  - _check_no_pale_background(): category="coloring_pages" bypasses the
    check even for a genuinely near-white image; the default (no category)
    behavior is unchanged -- a real regression guard against accidentally
    weakening the gate for every other product type
  - _produce_coloring_pages_listing_photos(): staging success path, no-
    listing_id error, no-ZIP error, category mismatch error
  - _produce_listing_photos()'s category dispatch to the coloring_pages path
  - _validate_staged_action's listing_photo branch: a near-white photo
    passes when payload["category"] == "coloring_pages", fails otherwise

Run: python tests/test_coloring_listing_photos.py
"""
import asyncio
import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_coloring_photos_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "coloring-photos-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _make_white_png_bytes(size=(400, 500)) -> bytes:
    from PIL import Image as PILImage
    im = PILImage.new("RGB", size, (255, 255, 255))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _make_coloring_zip(n_pages: int) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(1, n_pages + 1):
            zf.writestr(f"page_{i:02d}.png", _make_white_png_bytes())
        # A nested/non-page file must never be counted as a page.
        zf.writestr("thumbnails/preview.png", _make_white_png_bytes())
        zf.writestr("README.txt", b"not a page")
    return buf.getvalue()


# ── _extract_coloring_page_images ────────────────────────────────────────

def test_extract_ignores_nested_and_non_png_entries():
    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = Path(tmpdir) / "pack.zip"
        zpath.write_bytes(_make_coloring_zip(5))
        pages = server._extract_coloring_page_images(zpath, 10)
    names = [name for name, _ in pages]
    check(len(pages) == 5, f"expected 5 root-level pages, got {len(pages)}")
    check(all("/" not in n for n in names), f"must never include nested entries, got {names}")
    check(all(n.lower().endswith(".png") for n in names), f"must only include PNGs, got {names}")
    check("thumbnails/preview.png" not in names, "nested thumbnail must be excluded")


def test_extract_returns_all_pages_when_at_or_under_the_cap():
    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = Path(tmpdir) / "pack.zip"
        zpath.write_bytes(_make_coloring_zip(8))
        pages = server._extract_coloring_page_images(zpath, 10)
    check(l
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-003 -->
<!-- TRASH id=20261025-004 date=2026-10-25 kind=file source="tests/test_coloring_theme_registry.py" reason="Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only)." -->
## 20261025-004 · 2026-10-25 · file · `tests/test_coloring_theme_registry.py`
**Reason:** Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only).  
**Payload:** `data/trash/files/20261025-004__test_coloring_theme_registry.py`

```
"""
Tests for the coloring-pages theme registry (2026-07-24): Scott, on the
Create screen's dynamic new-theme path: "It will be a set of 20 individual
coloring pages. Never to repeat a creation." Covers:

  - _normalize_subject() -- the exact-match dedup key.
  - The registry sidecar itself: read/write round-trip, tolerant of a
    missing/corrupt file (same volume-or-local pattern as
    _PRODUCT_CATALOG_OVERRIDES_PATH -- see .claude/rules/api-conventions.md).
  - _record_used_coloring_subjects() appends one entry per subject.
  - _generate_coloring_subjects() -- the raw Anthropic-call wrapper (mocked,
    no real API key/network involved).
  - _resolve_coloring_subjects() -- the full flow: caps at NEW_THEME_SET_SIZE,
    code-verifies the LLM's own output against the full registry and drops/
    retries anything that slips through, and surfaces a clear error when it
    can't reach the target count after a retry.

Run: python tests/test_coloring_theme_registry.py
"""
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_coloringregistry_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "coloringregistry-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _tmp_registry_path() -> Path:
    return Path(tempfile.mkdtemp(prefix="frank_coloring_registry_")) / "coloring_theme_registry.json"


def test_normalize_subject_collapses_whitespace_and_case():
    check(server._normalize_subject("  A Sleepy   Fox ") == "a sleepy fox",
          f"got {server._normalize_subject('  A Sleepy   Fox ')!r}")
    check(server._normalize_subject("a sleepy fox") == server._normalize_subject("A SLEEPY FOX"),
          "case must not affect the normalized key")


def test_registry_read_missing_file_returns_empty_list():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        check(server._coloring_theme_registry() == [], "a never-written registry must read as []")


def test_registry_read_corrupt_file_returns_empty_list():
    path = _tmp_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        check(server._coloring_theme_registry() == [], "a corrupt registry file must read as [], not raise")


def test_registry_write_read_round_trip():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        server._write_coloring_theme_registry([{"subject": "a fox", "normalized": "a fox"}])
        got = server._coloring_theme_registry()
    check(got == [{"subject": "a fox", "normalized": "a fox"}], f"got {got}")
    check(path.exists(), "the registry file must actually be written to disk")


def test_record_used_coloring_subjects_appends_one_entry_per_subject():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        server._record_used_coloring_subjects("COLOR_TEST", "woodland animals", ["a fox", "a deer"])
        registry = server._coloring_theme_registry()
    check(len(registry) == 2, f"expected 2 entries, got {len(registry)}")
    check({e["subject"] for e in registry} == {"a fox", "a deer"}, f"got {registry}")
    check(all(e["product_id"] == "COLOR_TEST" for e in registry), f"got {registry}")
    check(all(e["theme"] == "woodland animals" for e in registry), f"got {registry}")
    check(all("created_at" in e and e["created_at"] for e in registry), f"got {r
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-004 -->
<!-- TRASH id=20261025-005 date=2026-10-25 kind=file source="tests/test_planner_photo_pipeline.py" reason="Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only)." -->
## 20261025-005 · 2026-10-25 · file · `tests/test_planner_photo_pipeline.py`
**Reason:** Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only).  
**Payload:** `data/trash/files/20261025-005__test_planner_photo_pipeline.py`

```
"""
Tests for Frank upgrade Wave 4, item A1 (2026-07-17): planner listing photos
now go through the real, self-verifying AI pipeline (tools/listing_photo_
pipeline.py) instead of a pure-PIL clip-art mockup.

Root cause this closes: `tools/gen_planner_listing_photos.py`'s
generate_for_planner() -- the function `_produce_listing_photos()` (main.py)
used to call -- never called an AI image model at all. Its own docstring
said so plainly ("Pure local render"). That's the actual reason planner
photos read as fake: not AI artifacts leaking through, a total absence of
photorealistic rendering for the shop's core product line (DP1026-1034).

Covers three layers:
  1. tools/listing_photo_pipeline.py -- the cfg-driven style-anchor fallback
     (_style_anchor_for), the finish pass (_apply_finish_pass: grain +
     vignette + unsharp), and PhotoResult's new fields.
  2. tools/gen_planner_listing_photos.py -- generate_ai_photos_for_planner(),
     the new glue function: renders real PDF pages via the existing
     render_page(), locates real sticker sheet PNGs via the same 3-way
     fallback chain make_sticker_showcase() already uses, and hands
     everything to the real pipeline.
  3. tools/api_server/main.py's _produce_listing_photos() -- routes passed
     photos into the existing staged-action approval queue when a listing_id
     exists (same path SS-series photos already use), falls back to the old
     Files-screen folder-drop UX for pre-publish drafts with no listing_id
     yet (DP1030-1034), and never silently drops a failed or realism-flagged
     photo.

Run: python tests/test_planner_photo_pipeline.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_photo_pipeline_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "photo-pipeline-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import listing_photo_pipeline as lpp  # noqa: E402
import gen_planner_listing_photos as glp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── listing_photo_pipeline.py: style anchor fallback ────────────────────────
def test_hardcoded_style_anchor_unchanged_for_original_four():
    # DP1026-1029 must keep using their hand-tuned entries verbatim (plus the
    # new film-grain/commercial-photography phrase appended to each).
    anchor = lpp._style_anchor_for("DP1026", None)
    check("Lavender purple" in anchor, f"DP1026's hand-tuned anchor must be used as-is, got: {anchor[:100]!r}")
    check("sharp commercial product photography" in anchor,
          f"DP1026's anchor should carry the new vocabulary too, got: {anchor[:150]!r}")


def test_fallback_style_anchor_for_unconfigured_product_uses_cfg():
    cfg = {"theme": "Matcha Serenity", "color": (126, 200, 164), "accent": (184, 204, 142), "bg": (247, 249, 243)}
    anchor = lpp._style_anchor_for("DP1030", cfg)
    check("Matcha Serenity" in anchor, f"the fallback anchor must use the real theme name, got: {anchor[:150]!r}")
    check("#7EC8A4" in anchor, f"the fallback anchor must use the real hex color, got: {anchor[:200]!r}")
    check("cream linen desk surface" in anchor, f"a light theme should get a light desk surface, got: {anchor!r}")


def test_fallback_style_anchor_detects_dark_theme():
    cfg = {"theme": "Midnight Kawaii", "color": (128, 64, 156), "accent": (0, 229, 255), "bg": (26, 26, 46)}
    anchor = lpp._style_anchor_for("DP1032", cfg)
    check("deep charcoal desk surface" in anchor, f"a dark theme (bg sum < 400) should get a dark desk, got: {anchor!r}")


def test_no_cfg_and_no_hardcoded_entry_returns_empty_not_crash():
    anchor = lpp._style_an
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-005 -->
<!-- TRASH id=20261025-006 date=2026-10-25 kind=file source="tests/test_knowledge_base_expansion.py" reason="Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only)." -->
## 20261025-006 · 2026-10-25 · file · `tests/test_knowledge_base_expansion.py`
**Reason:** Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only).  
**Payload:** `data/trash/files/20261025-006__test_knowledge_base_expansion.py`

```
"""
Tests for the 2026-08-08 knowledge-base expansion, prompted by Scott: "I need
frank to have more knowledge... he needs more ability to make better coloring
pages... make sure we have [repos/tools/skills]."

Audited data/knowledge_base/ + CLAUDE.md first: wall art, SVG packs, digital
planners, and sticker packs already had deep, sourced research
(design_quality_research_2026-06.md, competitor_research_2026.md, CLAUDE.md's
own Sticker Pack Design Standards section). Coloring pages had NONE -- no
competitor research, no design-technique doc anywhere. Also found the monthly
competitor-research refresh (_run_competitor_research_refresh in main.py)
claimed to cover 4 product lines in its own prompt text but
_COMPETITOR_RESEARCH_SEARCH_TERMS only ever had 3 entries (no coloring pages,
no SVG packs) -- a real gap between what the automation claims to do and what
it actually searches for.

Covered here:
  1. A new, web-search-grounded knowledge_base doc for coloring pages exists
     and is auto-discoverable via read_knowledge_base_doc's glob (no
     registration step needed -- see main.py's _kb_docs()).
  2. _COMPETITOR_RESEARCH_SEARCH_TERMS now includes coloring pages + SVG packs,
     matching what the refresh prompt text already claimed to cover.
  3. All 4 coloring-page style-DNA prompt constants now include the
     closed-outline instruction sourced from real published coloring-book
     design guides (the one concrete prompt-technique gap the research found).

Run: python tests/test_knowledge_base_expansion.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_kbexpand_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "kbexpand-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import generate_coloring_pages as gcp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_coloring_page_doc_exists_and_is_kb_discoverable():
    doc_path = ROOT / "data" / "knowledge_base" / "coloring_page_design_and_market_research.md"
    check(doc_path.is_file(), f"expected {doc_path} to exist")
    text = doc_path.read_text()
    check("closed" in text.lower() and "outline" in text.lower(),
          "doc should discuss closed/enclosed outlines (the real prompt-technique gap found)")
    check("$" in text, "doc should cite real pricing data, not just qualitative claims")

    filenames = {d["filename"] for d in server._kb_docs()}
    check("coloring_page_design_and_market_research.md" in filenames,
          f"new doc must be auto-discovered by _kb_docs()'s glob, got: {sorted(filenames)}")

    resolved = server._resolve_kb_doc("coloring_page_design_and_market_research.md")
    check(resolved == doc_path.resolve(), f"_resolve_kb_doc should resolve to the real file, got {resolved}")


def test_competitor_research_search_terms_cover_all_4_product_lines():
    terms_text = " ".join(server._COMPETITOR_RESEARCH_SEARCH_TERMS).lower()
    check("coloring" in terms_text,
          f"search terms must include a coloring-pages term, got: {server._COMPETITOR_RESEARCH_SEARCH_TERMS}")
    check("svg" in terms_text,
          f"search terms must include an SVG-pack term, got: {server._COMPETITOR_RESEARCH_SEARCH_TERMS}")
    check(len(server._COMPETITOR_RESEARCH_SEARCH_TERMS) >= 5,
          f"expected at least 5 terms (3 original + 2 new), got {len(server._COMPETITOR_RESEARCH_SEARCH_TERMS)}")


def test_coloring_page_styles_all_specify_closed_outlines():
    for name, style in [
        ("_STYLE", gcp._STYLE),
        ("_STYLE_BOLD", gcp._STYLE_BOLD),
        ("_STYLE_ADULT", gcp._STYLE_ADULT),
        ("_STYLE_KIDS", gcp._STYLE_KIDS),
 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-006 -->
<!-- TRASH id=20261030-001 date=2026-10-30 kind=snippet source="openscad_models/valentine_2027/mailboxes/love_letter/cupid.scad" reason="Flat stepped cut-out Cupid replaced by a sculpted relief one at Scott's request ('I want the Cupid to have depth'), 2026-10-30" -->
## 20261030-001 · 2026-10-30 · snippet · `openscad_models/valentine_2027/mailboxes/love_letter/cupid.scad`
**Reason:** Flat stepped cut-out Cupid replaced by a sculpted relief one at Scott's request ('I want the Cupid to have depth'), 2026-10-30  
**Payload:** `data/trash/files/20261030-001__snippet.txt`

```
// Cupid for the Giant Love Letter (2026-10-30). Scott: "make it a little more
// fun ... a cartoony Cupid that is a separate print that has a slight divot in
// the front of the envelope that it would set in"; he picked that and heart
// stickers. A chubby cherub with curls, small white wings and a white wrap
// (school-appropriate), drawing a red bow with a heart-tipped arrow, aimed up
// at the child's name.
//
// He prints face up, his back flat on the bed. He is a stepped cut-out: each
// shape stands at its own height in its own colour, the nearer ones taller, so
// every level edge is on the 0.2 layer grid and the colours change only where
// the shapes meet. Four filaments: skin, white, red, dark.
//
// He sits in a pocket 1.0 deep in the envelope's front and presses onto two
// diamond pegs standing in it. His holes have crush ribs, so the fit is snug
// whatever the printer's hole shrinkage; a drop of glue makes it permanent.
// About 55 x 62, far over the small-parts size.
//
// Local frame: x across (he faces +x), y up, z out of the envelope.


// ---------- his shapes, in 2D ----------
HEAD = [2, 41]; HEAD_R = 11.5;
TORSO = [0, 20];
AIM = 22;                        // the bow and arrow tilt up toward the name
PIV = [4, 26];                   // ...about his chest
module aimed() translate(PIV) rotate(AIM) translate(-PIV) children();
function aimp(p) = PIV + [[cos(AIM), -sin(AIM)], [sin(AIM), cos(AIM)]] * (p - PIV);
module capsule(a, b, r) hull() { translate(a) circle(r, $fn = 40); translate(b) circle(r, $fn = 40); }
module ellipse(c, rx, ry, a = 0) translate(c) rotate(a) scale([rx, ry]) circle(1, $fn = 72);

module c_head() translate(HEAD) circle(HEAD_R, $fn = 96);
// curls round the top and back of his head, and one on his forehead
CURLS = [for (a = [72 : 26 : 202]) [HEAD + 10.6 * [cos(a), sin(a)], 3.6]];
module c_hair() union() {
    for (c = CURLS) translate(c[0]) circle(c[1], $fn = 40);
    intersection() { translate(HEAD) circle(HEAD_R + 0.2, $fn = 96); translate(HEAD + [-5.5, 7.5]) circle(9.0, $fn = 80); }
    translate(HEAD + [4.8, 10.2]) circle(2.6, $fn = 36);
}
module c_torso() ellipse(TORSO, 9.8, 11, 0);
module c_wrap() intersection() {        // his white wrap, round his middle
    offset(delta = 0.01) c_torso();
    translate([-20, -10]) square([40, TORSO.y - 2.5 + 10]);
}
module c_legs() { ellipse([-4.8, 8.2], 4.2, 5.4, -12); ellipse([5.0, 7.8], 4.2, 5.4, 14); }
// wings on his back: three feathers each, the upper wing then the lower
module c_wings() union() {
    for (f = [[[-9, 31], [-21, 41], 3.6], [[-9, 28], [-24, 33], 3.4], [[-9, 25], [-22, 25], 3.2]]) capsule(f[0], f[1], f[2]);
}
module c_wing_lines() for (f = [[[-12, 33.2], [-19, 38.6]], [[-12, 29.6], [-21, 32.0]], [[-12, 26.4], [-20, 25.8]]]) capsule(f[0], f[1], 0.45);
// the bow hand holds the bow out in front; the other hand draws the string
BOW_HAND = [19.5, 27]; DRAW_HAND = [4.5, 27.5];
module c_arms() aimed() { capsule([5.5, 25], BOW_HAND, 2.4); capsule([-3, 25.5], DRAW_HAND, 2.5); }
BOW_C = [7, 27]; BOW_R = 13.2; BOW_A = 58;
module c_bow() aimed() difference() {
    translate(BOW_C) intersection() {
        difference() { circle(BOW_R + 0.9, $fn = 120); circle(BOW_R - 0.9, $fn = 120); }
        polygon([[0, 0], [40 * cos(BOW_A), -40 * sin(BOW_A)], [40, 0], [40 * cos(BOW_A), 40 * sin(BOW_A)]]);
    }
}
function bow_tip(s) = BOW_C + BOW_R * [cos(BOW_A), s * sin(BOW_A)];
module c_string() aimed() { capsule(bow_tip(1), DRAW_HAND, 0.6); capsule(bow_tip(-1), DRAW_HAND, 0.6); }
module c_heart2d(s) scale(s / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 60);
}
ARROW_TIP = [33, 27];
module c_shaft() aimed() capsule([0.5, 27.5], ARROW_TIP - [3, 0], 0.8);
module c_arrowhead() aimed() translate(ARROW_TIP) rotate(-90) c_heart2d(8.5);
module c_fletch() aimed() for (s = [-1, 1]) polygon([[-1.8, 27.5], [2.4, 27.5], [-0.6, 27.5 + s * 3.0], [-3.4, 27.5 + s * 3.0]]);
// his face looks along the arrow: eyes, a smile, rosy cheeks
module c_eyes() for (e = [[4.2, -0.6], [9.6, -0.4]]) ellipse(HEAD + e, 1.3, 1.8);
module c_shine() for (e = [[4.6, 0.3], [10.0, 0.5]]) translate(HEAD + e) circle(0.45, $fn = 20);
module c_smile() for (i = [0 : 7]) let (t0 = -30 + i * 10, t1 = t0 + 10)
    capsule(HEAD + [7, -3.4] + 3.2 * [sin(t0), -cos(t0) * 0.6], HEAD + [7, -3.4] + 3.2 * [sin(t1), -cos(t1) * 0.6], 0.45);
module c_wrap_heart() translate(TORSO + [1.5, -5.5]) c_heart2d(4.6);
module c_cheeks() { translate(HEAD + [10.4, -4.4]) circle(1.5, $fn = 30); translate(HEAD + [1.0, -4.8]) circle(1.6, $fn = 30); }

// ---------- the stack: shape, height, colour (0 skin, 1 white, 2 red, 3 dark) ----------
// a point's column is the colour of the tallest shape over it, at that height
//         wings bow  str  legs torso wrap arms fletch shaft head head eyes smile shine cheeks hair wrap-heart
C_H   = [3.0,  3.6, 2.6, 4.6, 5.2,  5.6, 5.8, 6.2,   6.0,  6.0, 6.2, 6.4, 6.4,  6.4,  6.4,   6.8, 6.0];
C_COL = [1,    3,   3,   0,   0,    1,   0,   2,     3,    2,   0,   3,   3,    1,    2,     3,   2];
module c_item(i) {
    if      (i == 0)  c_wings();
    else if (i == 1)  c_bow();
    else if (i == 2)  c_string();
    else if (i == 3)  c_legs();
    else if (i == 4)  c_torso();
    else if (i == 5)  c_wrap();
    else if (i == 6)  c_arms();
    else if (i == 7)  c_fletch();
    else if (i == 8)  c_shaft();
    else if (i == 9)  c_arrowhead();
    else if (i == 10) c_head();
    else if (i == 11) c_eyes();
    else if (i == 12) c_smile();
    else if (i == 13) c_shine();
    else if (i == 14) c_cheeks();
    else if (i == 15) c_hair();
    else if (i == 16) c_wrap_heart();
}
module c_column(i) difference() {
    c_item(i);
    for (j = [0 : len(C_H) - 1]) if (j != i && (C_H[j] > C_H[i] || (C_H[j] == C_H[i] && j > i))) c_item(j);
}
module cupid_outline() union() for (i = [0 : len(C_H) - 1]) c_item(i);
// the feathers' lines are grooves 0.4 deep, 0.9 wide, cut into the wings' top
module wing_grooves() translate([0, 0, C_H[0] - 0.4]) linear_extrude(1) c_wing_lines();
// his holes take the envelope's pegs; under his head and his middle, where he
// is thickest
PEGS = [HEAD + [-2, -1], TORSO + [-1, -5]];
// A peg is a wedge standing out of the upright wall: flat on top, its
// underside climbing from the wall at 37 deg, so it grows out of the wall
// layer by layer. A diamond peg began each one as a sliver in mid-air at its
// lower point, and the slicer propped both from the bed (2026-10-30).
PEG_W = 2.4;                     // across
PEG_L = 2.2;                     // how far it stands from the pocket floor
PEG_TIP = 1.6;                   // its height at the tip
PEG_ROOT = PEG_TIP + PEG_L / tan(37);   // and at the wall, 4.5
// the peg in his frame: x across, y up (top at y = 0), z out from the floor
module peg_shape(c = 0) hull() {
    translate([-PEG_W / 2 - c, -PEG_ROOT - c, 0]) cube([PEG_W + 2 * c, PEG_ROOT + 2 * c, 0.01]);
    translate([-PEG_W / 2 - c, -PEG_TIP - c, PEG_L + c - 0.01]) cube([PEG_W + 2 * c, PEG_TIP + 2 * c, 0.01]);
}
// where a peg's top edge sits, for a peg centred on p
function peg_at(p) = p + [0, PEG_ROOT / 2];
HOLE_C = 0.25;                   // clearance round the peg; the ribs take it up
RIB_R = 0.35; RIB_IN = 0.1;      // ribs on the side walls reach 0.1 into the peg
// His hole is the peg's full root height all the way in, straight-walled:
// the wedge's 37 deg underside is 53 deg in him, printed face up, and copying
// it drew 330 support moves (2026-10-30). The peg still sits on the hole's
// sides (the ribs), its top and its root.
HOLE = [PEG_W + 2 * HOLE_C, PEG_ROOT + 2 * HOLE_C];
HOLE_D = PEG_L + HOLE_C;
ROOF = (HOLE.x / 2) / tan(37);   // a hipped roof at 37 deg on every side
module cupid_hole() translate([0, HOLE_C - HOLE.y / 2, 0]) difference() {
    union() {
        translate([-HOLE.x / 2, -HOLE.y / 2, -0.01]) cube([HOLE.x, HOLE.y, HOLE_D + 0.01]);
        translate([0, 0, HOLE_D - 0.01]) hull() {
            translate([-HOLE.x / 2, -HOLE.y / 2, 0]) cube([HOLE.x, HOLE.y, 0.01]);
            translate([-0.01, -(HOLE.y / 2 - HOLE.x / 2), ROOF]) cube([0.02, HOLE.y - HOLE.x, 0.01]);
        }
        // the mouth opens 0.3 against the first layer's squash
        hull() {
            translate([-HOLE.x / 2 - 0.3, -HOLE.y / 2 - 0.3, -0.01]) cube([HOLE.x + 0.6, HOLE.y + 0.6, 0.01]);
            translate([-HOLE.x / 2, -HOLE.y / 2, 0.4]) cube([HOLE.x, HOLE.y, 0.01]);
        }
    }
    // crush ribs, two on each side wall, reaching RIB_IN into the peg
    for (sx = [-1, 1], y = [HOLE.y / 2 - HOLE_C - PEG_TIP * 0.3, HOLE.y / 2 - HOLE_C - PEG_TIP * 0.8])
        translate([sx * (PEG_W / 2 + RIB_R - RIB_IN), y, -1]) cylinder(r = RIB_R, h = HOLE_D + ROOF + 2, $fn = 16);
}

// ---------- the colour parts, as printed ----------
module cupid_colour(c) difference() {
    union() for (i = [0 : len(C_H) - 1]) if (C_COL[i] == c) linear_extrude(C_H[i]) c_column(i);
    for (p = PEGS) translate(peg_at(p)) cupid_hole();
    wing_grooves();
}
module cupid_skin()  cupid_colour(0);
module cupid_white() cupid_colour(1);
module cupid_red()   cupid_colour(2);
module cupid_dark()  cupid_colour(3);
// merged, for the gate: every shape at full height overlaps the next, so the
// union closes
module cupid_print() difference() {
    union() for (i = [0 : len(C_H) - 1]) linear_extrude(C_H[i]) c_item(i);
    for (p = PEGS) translate(peg_at(p)) cupid_hole();
    wing_grooves();
}
```

<!-- /TRASH 20261030-001 -->
