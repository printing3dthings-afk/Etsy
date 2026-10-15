// Christmas Village -- STYLE CONCEPTS (2026-09-27).
// One cottage, dressed five ways, so Scott can pick a look for the village
// before any real building is modelled (openscad_models/christmas_village/
// CHRISTMAS_VILLAGE.md). The footprint, door, windows, chimney and snow base
// are identical in every style; only the surface, roof, openings' shape and
// decorations change.
//
// THIS IS A LOOK STUDY, NOT A PRINTABLE MODEL. It has not been through
// tools/product_gate.py and parts of it would fail: flat-bottomed sills and
// balconies, bars standing free in their openings, a 26 deg chalet roof with a
// 12 mm eave, and pieces that overlap one another. The style Scott picks gets
// rebuilt to the Haunted Town rules (disjoint colour parts, 45 deg undersides,
// panes behind every window, OBC mark) before anything is printed.
//
// Rendered as many small PIECES, one colour each, not four fused colour parts:
// this OpenSCAD is 2021.01 on CGAL, where a union of dozens of spheres and
// cylinders takes many minutes, and for a look study nothing needs fusing.
//   -D style="victorian" | "gingerbread" | "nordic" | "chalet" | "kawaii"
//   -D piece="walls" | "tex" | "plaster" | "base" | "roof" | "shingles" |
//            "chimney" | "snow" | "drips" | "frames" | "barge" | "door" |
//            "deco" | "deco2"
// Which filament colour each piece takes, per style, is in render_styles.py.
// The front of the building faces -Y, as in the Haunted Town.

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.5;

style = "victorian";
piece = "walls";

STYLES = ["victorian", "gingerbread", "nordic", "chalet", "kawaii"];
si = search([style], STYLES)[0];
function pick(v) = v[si];

// ---- the building, shared by every style --------------------------------
W = 64;  D = 58;  H = 50;        // walls: width (X), depth (Y), eave height
wall = 1.68;
base_h = 5;                       // the snow base every building stands on
b = W / 2;

// ---- roof ----------------------------------------------------------------
P = pick([56, 50, 46, 26, 50]);   // pitch
E = pick([4, 4.5, 4, 12, 5]);     // eave overhang at the sides
R = pick([3, 3.5, 3, 10, 4]);     // rake overhang front and back
T = 2.4;                          // slab thickness
tP = tan(P);  cP = cos(P);
zr = H + b * tP;                  // ridge, underside
zt = zr + T / cP;                 // ridge, top
L  = (b + E) / cP;                // slope length, ridge to eave
U  = D / 2 + R;                   // half the roof's length along the ridge
ts = 0.8;                         // shingle relief
function z_under(x) = H + (b - abs(x)) * tP;
function z_top(x)   = z_under(x) + T / cP;
ze_top = z_top(b + E);            // top of the eave edge

// ---- openings ------------------------------------------------------------
corner_r = pick([0, 0, 0, 0, 6]);
fw = pick([1.6, 1.4, 1.6, 1.8, 1.8]);   // frame width
fd = pick([1.6, 1.6, 1.4, 2.4, 1.6]);   // frame stands proud of the wall
DW = pick([14, 15, 14, 14, 15]);  DH = pick([26, 27, 25, 25, 27]);
dk = pick(["arch", "arch", "rect", "rect", "arch"]);
WW = 11;  WH = pick([15, 15, 15, 14, 12]);  WZ = pick([18, 18, 18, 18, 20]);
wk = pick(["seg", "arch", "rect", "rect", "circle"]);
wx = 19;                          // front windows either side of the door
sx = 13;                          // side windows either side of centre
ak = pick(["lancet", "circle", "heart", "rect", "circle"]);
aw = pick([9, 12, 12, 8, 13]);  ah = pick([17, 12, 11, 9, 13]);
az = H + pick([6, 9, 4, 1.5, 7]);

// ---- chimney -------------------------------------------------------------
cx = -b * 0.45;  cy = D / 4;  cw = 9;
c_top = z_top(cx + cw / 2) + pick([11, 8, 9, 7, 8]);

FACES = ["front", "back", "left", "right"];

// ==== 2D helpers ==========================================================
// Every opening shape has its origin at bottom-centre.
module shp(k, w, h) {
    if (k == "rect") translate([-w / 2, 0]) square([w, h]);
    else if (k == "arch") union() {
        translate([-w / 2, 0]) square([w, h - w / 2]);
        translate([0, h - w / 2]) circle(d = w);
    }
    else if (k == "seg") {
        s = w * 0.22;  rr = (w * w / 4 + s * s) / (2 * s);
        union() {
            translate([-w / 2, 0]) square([w, h - s]);
            intersection() {
                translate([-w / 2, h - s - 0.01]) square([w, s + 0.01]);
                translate([0, h - rr]) circle(r = rr);
            }
        }
    }
    else if (k == "lancet") {
        hs = h - w * sin(60);
        union() {
            translate([-w / 2, 0]) square([w, hs]);
            intersection() {
                translate([-w / 2, hs - 0.01]) square([w, h - hs + 0.01]);
                translate([-w / 2, hs]) circle(r = w);
                translate([w / 2, hs]) circle(r = w);
            }
        }
    }
    else if (k == "circle") translate([0, h / 2]) circle(d = h);
    else if (k == "heart") heart2d(h);
}

module heart2d(h) {                // tip at the origin, h tall
    s = h / 1.561;
    rotate(45) union() {
        square(s);
        translate([s / 2, s]) circle(d = s);
        translate([s, s / 2]) circle(d = s);
    }
}

module star2d(ro, ri, n = 5) {
    polygon([for (i = [0 : 2 * n - 1])
        let(a = 90 + i * 180 / n, r = i % 2 ? ri : ro) [r * cos(a), r * sin(a)]]);
}

module off(p) { if (p > 0) offset(r = p) children(); else children(); }

module pent2d() polygon([[-b, 0], [b, 0], [b, H], [0, zr], [-b, H]]);

module face_outline(f) {
    if (f == "front" || f == "back") pent2d();
    else translate([-D / 2, 0]) square([D, H]);
}

// Openings of one face, in that face's own (u, z) coordinates.
module face_open(f, pad = 0, doors = true) {
    if (f == "front") {
        if (doors) translate([0, base_h]) off(pad) shp(dk, DW, DH);
        for (s = [-1, 1]) translate([s * wx, WZ]) off(pad) shp(wk, WW, WH);
        translate([0, az]) off(pad) shp(ak, aw, ah);
    } else if (f == "back") {
        translate([0, WZ]) off(pad) shp(wk, WW, WH);
        translate([0, az]) off(pad) shp(ak, aw, ah);
    } else
        for (s = [-1, 1]) translate([s * sx, WZ]) off(pad) shp(wk, WW, WH);
}

// The window centres of a face, for the per-window details.
function face_windows(f) =
    f == "front" ? [[-wx, WZ, wk, WW, WH], [wx, WZ, wk, WW, WH], [0, az, ak, aw, ah]] :
    f == "back"  ? [[0, WZ, wk, WW, WH], [0, az, ak, aw, ah]] :
                   [[-sx, WZ, wk, WW, WH], [sx, WZ, wk, WW, WH]];

// Extrude a face's 2D children OUTWARD from that face by t, starting `inset`
// inside the wall.
module face(f, t, inset = 0) {
    if (f == "front")
        translate([0, -D / 2 + inset, 0]) rotate([90, 0, 0]) linear_extrude(t) children();
    else if (f == "back")
        mirror([0, 1, 0]) translate([0, -D / 2 + inset, 0]) rotate([90, 0, 0])
            linear_extrude(t) children();
    else if (f == "right")
        translate([b - inset, 0, 0]) rotate([90, 0, 90]) linear_extrude(t) children();
    else
        mirror([1, 0, 0]) translate([b - inset, 0, 0]) rotate([90, 0, 90])
            linear_extrude(t) children();
}

// Local frame of one roof slope: x runs DOWN the slope from the ridge, y along
// the ridge, z out of the roof. side = +1 right (+X), -1 left.
module slope(side) {
    mirror([side < 0 ? 1 : 0, 0, 0]) translate([0, 0, zt]) rotate([0, P, 0]) children();
}

// ==== the walls ===========================================================
module shell_solid(o, inner) {
    if (corner_r > 0)
        intersection() {
            shell_prism(o, inner);
            translate([0, 0, -10])
                cuboid([W - 2 * o, D - 2 * o, 200], rounding = corner_r - o,
                       edges = "Z", anchor = BOTTOM);
        }
    else shell_prism(o, inner);
}

module shell_prism(o, inner) {
    rotate([90, 0, 0]) linear_extrude(D - 2 * o, center = true) union() {
        offset(delta = -o) pent2d();
        if (inner) translate([-b + o, -5]) square([W - 2 * o, 10]);
    }
}

module walls() difference() {
    shell_solid(0, false);
    shell_solid(wall, true);
    for (f = FACES) face(f, 10, inset = 5) face_open(f);
}

// Relief on the wall faces: brick, board-and-batten or nothing.
module tex_pattern(f) {
    if (style == "victorian")         // brick, 3.0 mm courses, stretcher bond
        for (r = [0 : 32], c = [-7 : 7])
            translate([c * 6 + (r % 2) * 3 - 2.7, r * 3.0 + 0.3]) square([5.4, 2.4]);
    else if (style == "nordic")       // board and batten
        for (u = [-33 : 5.5 : 33]) translate([u - 0.65, 0]) square([1.3, 120]);
}

module tex() {
    if (style == "victorian" || style == "nordic")
        for (f = FACES) face(f, pick([0.7, 0, 0.8, 0, 0]), inset = 0.01) difference() {
            intersection() { face_outline(f); tex_pattern(f); }
            face_open(f, fw + 0.3);
        }
    if (style == "chalet") logs();
}

// Chalet: white plaster below 24 mm, round logs above, their ends crossing
// at the corners.
chalet_split = 24;
module plaster() {
    if (style == "chalet")
        for (f = FACES) face(f, 0.9, inset = 0.01) difference() {
            intersection() {
                face_outline(f);
                translate([-50, 0]) square([100, chalet_split]);
            }
            face_open(f, fw + 0.2);
        }
}

log_r = 1.9;  log_p = 3.9;
module logs() {
    n = ceil((zr - chalet_split) / log_p);
    for (f = ["front", "back"]) {
        mirror([0, f == "back" ? 1 : 0, 0]) intersection() {
            rotate([90, 0, 90]) linear_extrude(W + 7, center = true)
                for (k = [0 : n]) translate([-D / 2, chalet_split + log_r + k * log_p])
                    circle(r = log_r, $fn = 16);
            face("front", 5, inset = 2.5) difference() {
                union() {
                    intersection() {
                        pent2d();
                        translate([-50, chalet_split]) square([100, 100]);
                    }
                    translate([-b - 3.5, chalet_split]) square([W + 7, H - chalet_split]);
                }
                face_open(f, fw + 0.2);
            }
        }
    }
    m = ceil((H - chalet_split) / log_p);
    for (sd = [-1, 1]) mirror([sd < 0 ? 1 : 0, 0, 0]) intersection() {
        rotate([90, 0, 0]) linear_extrude(D + 7, center = true)
            for (k = [0 : m - 1])
                translate([b, chalet_split + log_r + log_p / 2 + k * log_p])
                    circle(r = log_r, $fn = 16);
        face("right", 5, inset = 2.5) difference() {
            translate([-D / 2 - 3.5, chalet_split]) square([D + 7, H - chalet_split - 0.5]);
            face_open("right", fw + 0.2);
        }
    }
}

// ==== the snow base =======================================================
module base2d() {
    translate([0, -3]) offset(r = 4) square([W + 8, D + 10], center = true);
    for (i = [0 : 13]) {
        a = i * 360 / 14;
        translate([(b + 8) * cos(a) * 1.02, -3 + (D / 2 + 9) * sin(a)])
            circle(r = 3.5 + 1.5 * sin(i * 131));
    }
}

module base() difference() {
    union() {
        linear_extrude(base_h) base2d();
        for (p = [[-b - 5, -D / 2 - 6, 1.3], [b + 5, D / 2 - 4, 1.0],
                  [b + 6, -D / 2 + 2, 0.8], [-b - 6, D / 2 - 8, 0.9]])
            translate([p[0], p[1], base_h - 0.5]) scale([1.4 * p[2], p[2], 0.5 * p[2]])
                sphere(r = 5, $fn = 24);
    }
    translate([0, 0, -1]) linear_extrude(base_h + 2)
        offset(r = corner_r > 0 ? corner_r - wall : 0.01)
            offset(delta = corner_r > 0 ? -(corner_r - wall) : 0)
                square([W - 2 * wall, D - 2 * wall], center = true);
}

// ==== roof ================================================================
module roof_poly() polygon([
    [-b - E, z_under(b + E)], [0, zr], [b + E, z_under(b + E)],
    [b + E, ze_top], [0, zt], [-b - E, ze_top]]);

module roof() {
    rotate([90, 0, 0]) linear_extrude(2 * U, center = true) roof_poly();
    if (style != "kawaii")
        translate([0, 0, zt - 0.6]) rotate([90, 0, 0])
            cylinder(r = 1.8, h = 2 * U, center = true, $fn = 16);
}

module shingle2d() {
    if (style == "victorian" || style == "chalet") {       // square slates
        cp = pick([4.2, 0, 0, 4.6, 0]);  tw = 5;
        for (i = [0 : ceil(L / cp)], j = [-8 : 8])
            translate([i * cp + 0.3, j * tw + (i % 2) * tw / 2 + 0.3])
                square([cp - 0.6, tw - 0.6]);
    } else if (style == "gingerbread" || style == "kawaii") {  // scallops
        cp = 4.4;  tw = 5.2;
        for (i = [0 : ceil(L / cp)], j = [-8 : 8])
            translate([i * cp, j * tw + (i % 2) * tw / 2]) {
                translate([0.3, 0.3]) square([cp * 0.55, tw - 0.6]);
                translate([cp * 0.55 + 0.3, tw / 2]) circle(d = tw - 0.6, $fn = 20);
            }
    } else if (style == "nordic")                            // standing seams
        for (u = [-U : 5 : U]) translate([0, u - 0.5]) square([L, 1.0]);
}

module shingles() for (sd = [-1, 1]) slope(sd) linear_extrude(ts)
    intersection() {
        translate([0.5, -U]) square([L - 0.5, 2 * U]);
        shingle2d();
    }

// ---- snow ----------------------------------------------------------------
sn    = pick([1.8, 1.3, 2.2, 3.0, 2.6]);            // snow depth
vs    = pick([0.5, 0.3, 0.7, 1.02, 0.62]) * L;      // how far down it reaches
scal  = pick([2.6, 1.6, 3.0, 0, 3.6]);              // lower-edge scallop radius
sgap  = pick([5.0, 3.6, 6.0, 5, 5.6]);

module snow2d() {
    translate([0, -U - 0.8]) square([vs, 2 * U + 1.6]);
    if (scal > 0)
        for (y = [-U : sgap : U])
            translate([vs, y]) circle(r = scal * (0.8 + 0.25 * sin(y * 97)), $fn = 20);
}

module snow() {
    for (sd = [-1, 1]) slope(sd) {
        translate([0, 0, ts - 0.3]) linear_extrude(sn) snow2d();
        if (vs >= L)            // a full blanket rolls over the eave
            translate([L, 0, (ts + sn) / 2 - 0.4]) rotate([90, 0, 0])
                cylinder(r = (ts + sn) / 2 + 0.6, h = 2 * U + 1.6, center = true, $fn = 16);
    }
    translate([0, 0, zt + ts]) scale([1, 1, 0.8]) rotate([90, 0, 0])
        cylinder(r = style == "kawaii" ? 3.6 : 2.6, h = 2 * U + 1.6, center = true, $fn = 20);
    translate([cx, cy, c_top]) scale([1, 1, 0.45]) sphere(r = cw * 0.72, $fn = 24);
}

// ---- icicles and drips ---------------------------------------------------
function len_at(i) = 2.5 + ((i * 7) % 5) * 1.1;

module drips() {
    if (style == "victorian" || style == "nordic" || style == "chalet") {
        ze = z_under(b + E) - (vs >= L ? 1.2 : 0) + 0.3;
        for (s = [-1, 1], i = [0 : floor((2 * U - 4) / 4.3)])
            translate([s * (b + E - 0.8), -U + 2 + i * 4.3, ze])
                mirror([0, 0, 1]) cylinder(h = len_at(i + (s > 0 ? 2 : 0)), r1 = 0.9, r2 = 0.1, $fn = 6);
        for (i = [0 : floor((2 * (b + E) - 4) / 4.3)]) {
            x = -(b + E) + 2 + i * 4.3;
            translate([x, -U + 0.9, z_under(x) + 0.3])
                mirror([0, 0, 1]) cylinder(h = len_at(i + 1), r1 = 0.9, r2 = 0.1, $fn = 6);
        }
    }
    if (style == "gingerbread" || style == "kawaii") {
        r1 = pick([0, 1.1, 0, 0, 1.5]);
        k  = pick([0, 0.8, 0, 0, 1.4]);          // drip length multiplier
        // along both side eaves
        for (s = [-1, 1]) {
            translate([s * (b + E + 0.2), 0, ze_top - 0.3]) rotate([90, 0, 0])
                cylinder(r = r1, h = 2 * U, center = true, $fn = 12);
            for (i = [0 : floor((2 * U - 3) / 4)])
                hull() {
                    translate([s * (b + E + 0.2), -U + 1.5 + i * 4, ze_top - 0.3]) sphere(r = r1, $fn = 12);
                    translate([s * (b + E + 0.2), -U + 1.5 + i * 4, ze_top - 0.3 - k * len_at(i)])
                        sphere(r = r1 * 0.75, $fn = 12);
                }
        }
        // along the front and back rakes
        for (fy = [-1, 1]) {
            y = fy * (U + 0.2);
            for (sd = [-1, 1]) hull() {
                translate([sd * (b + E), y, ze_top - 0.3]) sphere(r = r1, $fn = 12);
                translate([0, y, zt - 0.3]) sphere(r = r1, $fn = 12);
            }
            for (i = [0 : floor((2 * (b + E) - 3) / 4)]) {
                x = -(b + E) + 1.5 + i * 4;
                hull() {
                    translate([x, y, z_top(x) - 0.3]) sphere(r = r1, $fn = 12);
                    translate([x, y, z_top(x) - 0.3 - k * len_at(i + 3)]) sphere(r = r1 * 0.75, $fn = 12);
                }
            }
        }
    }
    if (style == "gingerbread")              // piped icing down each corner
        for (f = ["front", "back"]) face(f, 1.3, inset = 0.01)
            for (s = [-1, 1], z = [base_h + 1.2 : 2.6 : H - 1]) translate([s * (b - 1.3), z])
                circle(r = 1.2, $fn = 14);
}

// ==== chimney =============================================================
module chimney() {
    z0 = z_under(cx - cw / 2) - 4;
    translate([cx, cy, z0]) {
        if (style == "kawaii") cylinder(r = cw / 2 + 0.5, h = c_top - z0, $fn = 32);
        else {
            translate([-cw / 2, -cw / 2, 0]) cube([cw, cw, c_top - z0]);
            translate([-cw / 2 - 0.9, -cw / 2 - 0.9, c_top - z0 - 2.4]) cube([cw + 1.8, cw + 1.8, 2.4]);
        }
    }
    if (style == "victorian")                 // two clay pots
        for (dx = [-2.2, 2.2]) translate([cx + dx, cy, c_top]) cylinder(r1 = 1.6, r2 = 1.3, h = 5, $fn = 20);
}

// ==== frames, bargeboards, door ===========================================
module muntins(f) for (wd = face_windows(f)) if (wd[2] != "heart") {
    k = wd[2];  w = wd[3];  h = wd[4];
    cz = k == "arch" ? (h - w / 2) * 0.72 : k == "lancet" ? h * 0.45 : h / 2;
    translate([wd[0], wd[1]]) intersection() {
        shp(k, w, h);
        union() {
            translate([-0.6, 0]) square([1.2, h]);
            translate([-w / 2, cz - 0.6]) square([w, 1.2]);
        }
    }
}

// Points around an opening's outline, for piped icing.
function ring_pts(k, w, h, pad, step) =
    k == "circle" ?
        [for (a = [0 : 360 / round(PI * (h + 2 * pad) / step) : 359.9])
            [(h / 2 + pad) * cos(a), h / 2 + (h / 2 + pad) * sin(a)]] :
    concat(
        [for (z = [0 : step : h - w / 2]) [-w / 2 - pad, z]],
        [for (a = [180 : -180 / round(PI * (w / 2 + pad) / step) : 0.1])
            [(w / 2 + pad) * cos(a), h - w / 2 + (w / 2 + pad) * sin(a)]],
        [for (z = [h - w / 2 : -step : 0]) [w / 2 + pad, z]],
        [for (x = [w / 2 : -step : -w / 2]) [x, -pad]]);

module frames() {
    if (style == "gingerbread") {
        for (f = FACES) face(f, 1.5, inset = 0.01) {
            for (wd = face_windows(f)) if (!(f == "front" && wd[1] == az))
                translate([wd[0], wd[1]])
                    for (p = ring_pts(wd[2], wd[3], wd[4], 1.3, 2.3)) translate(p) circle(r = 1.2, $fn = 14);
            if (f == "front") translate([0, base_h])
                for (p = ring_pts("arch", DW, DH, 1.3, 2.3)) if (p[1] > 0) translate(p) circle(r = 1.2, $fn = 14);
        }
        face("front", 1.5, inset = 0.01) translate([0, az])  // the peppermint's white
            difference() { off(3) shp(ak, aw, ah); shp(ak, aw, ah); }
    } else {
        for (f = FACES) face(f, fd, inset = 0.01)
            difference() { face_open(f, fw); face_open(f, 0); }
    }
    for (f = FACES) face(f, 1.2, inset = 0.4) muntins(f);
    // sills under the rectangular-ish windows
    if (wk != "circle" && style != "gingerbread")
        for (f = FACES) for (wd = face_windows(f)) if (wd[1] == WZ)
            face(f, fd + 1.2, inset = 0.01)
                translate([wd[0] - WW / 2 - fw - 1, WZ - fw - 2.2]) square([WW + 2 * fw + 2, 2.2]);
    if (style == "victorian") {
        for (f = FACES) {                                       // keystones
            face(f, fd + 0.5, inset = 0.01) {
                for (wd = face_windows(f)) if (wd[1] == WZ)
                    translate([wd[0], WZ + WH + fw - 1.6])
                        polygon([[-1.5, 0], [1.5, 0], [2.1, 4], [-2.1, 4]]);
                if (f == "front") translate([0, base_h + DH + fw - 1.6])
                    polygon([[-1.7, 0], [1.7, 0], [2.4, 4.6], [-2.4, 4.6]]);
            }
            e = (f == "front" || f == "back") ? b : D / 2;     // quoins
            face(f, 1.3, inset = 0.01)
                for (k = [0 : floor((H - base_h - 1) / 3.6)], s = [-1, 1]) {
                    qw = k % 2 ? 3.6 : 5.6;
                    // the front and back blocks run 1.3 past the corner, over
                    // the side blocks' edges, so the quoin wraps with no seam
                    wr = (f == "front" || f == "back") ? 1.3 : 0;
                    translate([s > 0 ? e - qw : -e - wr, base_h + 0.4 + k * 3.6]) square([qw + wr, 3.0]);
                }
        }
    }
    if (style == "nordic")                                      // corner boards
        for (f = FACES) {
            e = (f == "front" || f == "back") ? b : D / 2;
            face(f, 1.3, inset = 0.01) for (s = [-1, 1])
                translate([s > 0 ? e - 2.6 : -e, 0]) square([2.6, H]);
        }
}

// Bargeboards follow the front and back rakes.
module rake_band(db) polygon([
    [-b - E, ze_top], [0, zt], [b + E, ze_top],
    [b + E, z_under(b + E) - db], [0, zr - db], [-b - E, z_under(b + E) - db]]);

module barge() {
    db = pick([4.2, 0, 2.2, 5.5, 0]);
    if (db > 0) for (fy = [0, 1]) mirror([0, fy, 0]) translate([0, -R, 0])
        face("front", 1.6, inset = 0.01) difference() {
            rake_band(db);
            if (style == "victorian") {              // pierced trefoils and a scalloped hem
                for (x = [-b - E + 3 : 4.2 : b + E - 3]) if (abs(x) > 3)
                    translate([x, z_under(x) - 2]) circle(r = 0.9, $fn = 12);
                for (x = [-b - E + 1 : 2.8 : b + E - 1])
                    translate([x, z_under(x) - db - 0.7]) circle(r = 1.4, $fn = 14);
            }
            if (style == "chalet")                   // carved scallops
                for (x = [-b - E + 2 : 4.6 : b + E - 2])
                    translate([x, z_under(x) - db - 1.2]) circle(r = 2.6, $fn = 20);
        }
    if (style == "victorian") {                      // finial and drop at the peak
        translate([0, -U - 0.8, zt - 0.5]) cylinder(r1 = 1.0, r2 = 0.25, h = 7, $fn = 12);
        translate([0, -U - 0.8, zt + 1.5]) sphere(r = 1.2, $fn = 14);
        translate([0, -U - 0.8, zr - 4.2]) mirror([0, 0, 1]) cylinder(r1 = 1.0, r2 = 0.3, h = 4, $fn = 12);
    }
}

module door() {
    face("front", wall - 0.6, inset = wall) translate([0, base_h]) shp(dk, DW, DH);
    // panels / planks, standing 0.5 on the leaf
    face("front", 0.5, inset = 0.6) translate([0, base_h]) {
        if (style == "victorian" || style == "kawaii")
            for (s = [-1, 1]) translate([s * 3.4 - 2.4, 3]) square([4.8, DH * 0.42]);
        if (style == "gingerbread")                 // a chocolate bar
            for (i = [0 : 1], j = [0 : 3])
                translate([-DW / 2 + 1.6 + i * (DW / 2 - 0.8), 2 + j * 5.2])
                    square([DW / 2 - 2.4, 4.4]);
        if (style == "nordic" || style == "chalet")   // planks and a Z brace
            for (x = [-DW / 2 + 0.5 : 3.3 : DW / 2 - 2]) translate([x, 0]) square([2.7, DH - 0.5]);
    }
    translate([DW / 2 - 3, -D / 2 + 0.6 - 0.8, base_h + DH * 0.45]) sphere(r = 0.9, $fn = 14);
}

// ==== decorations =========================================================
module deco() {
    if (style == "victorian") {
        // shutters beside the front windows
        for (s = [-1, 1]) {
            xc = s * (wx + WW / 2 + fw + 3.3);
            face("front", 1.0, inset = 0.01) translate([xc - 2.6, WZ]) square([5.2, WH - 1]);
            face("front", 1.5, inset = 0.01)
                for (z = [WZ + 1 : 1.8 : WZ + WH - 2.5]) translate([xc - 2.1, z]) square([4.2, 0.8]);
        }
        // wreath on the door
        translate([0, -D / 2 + 0.6 - 1.3, base_h + DH - 9]) rotate([90, 0, 0])
            rotate_extrude($fn = 28) translate([3.6, 0]) circle(r = 1.3, $fn = 10);
        // garland swag over the door frame
        for (x = [-9 : 1.5 : 9])
            translate([x, -D / 2 - fd - 0.9, base_h + DH + fw + 4.2 - 3 * (1 - pow(x / 9, 2))])
                sphere(r = 1.35, $fn = 10);
        // lamp post
        translate([-b - 3, -D / 2 - 6, base_h]) {
            cylinder(r = 1.8, h = 2, $fn = 16);
            cylinder(r = 0.85, h = 30, $fn = 12);
            translate([0, 0, 35.4]) cylinder(r1 = 3.2, r2 = 0.4, h = 3, $fn = 4);
            translate([0, 0, 29]) cylinder(r1 = 1.0, r2 = 2.2, h = 1.2, $fn = 4);
        }
    }
    if (style == "gingerbread") {
        // gumdrops along the ridge
        for (y = [-U + 4 : 7.5 : U - 3]) translate([0, y, zt + 1.2]) scale([1, 1, 0.95])
            sphere(r = 2.4, $fn = 18);
        // the peppermint's red swirl, over the white ring
        face("front", 1.9, inset = 0.01) translate([0, az]) intersection() {
            difference() { off(3) shp(ak, aw, ah); shp(ak, aw, ah); }
            translate([0, ah / 2]) for (a = [0 : 60 : 359]) rotate(a) polygon([[0, 0], [20, 0], [20 * cos(25), 20 * sin(25)]]);
        }
        // candy canes either side of the door: red here, white stripes in deco2
        for (s = [-1, 1]) {
            x = s * (DW / 2 + 4.5);
            for (k = [0 : 2 : 10]) translate([x, -D / 2 - 2.4, base_h + k * 2.5])
                cylinder(r = 1.3, h = 2.5, $fn = 14);
            translate([x - s * 2.6, -D / 2 - 2.4, base_h + 27.5]) rotate([90, 0, 0])
                rotate_extrude(angle = 180, $fn = 24) translate([2.6, 0]) circle(r = 1.3, $fn = 12);
        }
        // gumdrops on the corners of the base
        for (p = [[-b - 4, -D / 2 - 5], [b + 4, -D / 2 - 5]])
            translate([p[0], p[1], base_h]) scale([1, 1, 0.9]) sphere(r = 2.8, $fn = 18);
    }
    if (style == "nordic") {
        face("front", 1.6, inset = 0.01) translate([0, H + 22.5]) star2d(4.8, 2.0);
        face("front", 0.9, inset = 0.6) translate([0, base_h + DH * 0.62]) heart2d(5);
        // candle bridges on the front sills
        for (s = [-1, 1]) face("front", 1.0, inset = -fd - 0.2) translate([s * wx, WZ])
            for (i = [-2 : 2]) translate([i * 1.9 - 0.4, 0]) square([0.8, 5 - abs(i) * 0.9]);
    }
    if (style == "chalet") {
        // red shutters with a heart cut through
        for (s = [-1, 1]) {
            xc = s * (wx + WW / 2 + fw + 3.4);
            face("front", 1.2, inset = 0.01) translate([xc, WZ]) difference() {
                translate([-2.8, 0]) square([5.6, WH]);
                translate([0, WH * 0.55]) heart2d(2.8);
            }
        }
        // red berries in the window boxes (deco2 is the box)
        for (s = [-1, 1], i = [-2 : 2])
            translate([s * wx + i * 2.4, -D / 2 - fd - 2.4, WZ - fw - 0.2]) sphere(r = 1.1, $fn = 10);
        face("front", 0.9, inset = 0.6) translate([0, base_h + DH * 0.6]) heart2d(4.5);
    }
    if (style == "kawaii") {
        translate([0, -U + 2.5, zt + ts + 2.6]) rotate([90, 0, 0])
            linear_extrude(1.8, center = true) offset(r = 0.6) star2d(5.2, 2.5);
        translate([cx, cy, c_top - 3]) cylinder(r = cw / 2 + 1.1, h = 2, $fn = 32);
    }
}

// Second-colour decorations.
module deco2() {
    if (style == "victorian")                        // the lamp's glass
        translate([-b - 3, -D / 2 - 6, base_h + 30.2]) cylinder(r1 = 1.6, r2 = 2.2, h = 5.2, $fn = 4);
    if (style == "gingerbread")                      // white stripes on the canes
        for (s = [-1, 1], k = [1 : 2 : 10])
            translate([s * (DW / 2 + 4.5), -D / 2 - 2.4, base_h + k * 2.5]) cylinder(r = 1.3, h = 2.5, $fn = 14);
    if (style == "chalet") {
        // balcony across the gable: floor, railing with hearts, brackets
        translate([-22, -D / 2 - 7, H - 0.4]) cube([44, 7.01, 1.6]);
        translate([0, -D / 2 - 5.8, H + 1.2]) rotate([90, 0, 0]) linear_extrude(1.2) difference() {
            translate([-22, 0]) square([44, 7]);
            for (x = [-18 : 6 : 18]) translate([x, 1.4]) heart2d(4);
        }
        for (s = [-1, 1]) translate([s * 22 - (s > 0 ? 1.2 : 0), -D / 2 - 7, H + 1.2]) cube([1.2, 7.01, 7]);
        for (x = [-18, 0, 18]) translate([x + 0.8, -D / 2, H - 0.4]) rotate([0, -90, 0])
            linear_extrude(1.6) polygon([[0, 0], [0, -7], [-7, 0]]);
        // window boxes
        for (s = [-1, 1]) translate([s * wx - WW / 2 - 1.5, -D / 2 - fd - 3.6, WZ - fw - 3.2])
            cube([WW + 3, 3.6 + fd, 3]);
    }
    if (style == "kawaii")                           // a pink heart on the lemon door
        face("front", 0.9, inset = 0.6) translate([0, base_h + DH * 0.55]) heart2d(5.5);
}

// ==== dispatch ============================================================
if      (piece == "walls")    walls();
else if (piece == "tex")      tex();
else if (piece == "plaster")  plaster();
else if (piece == "base")     base();
else if (piece == "roof")     roof();
else if (piece == "shingles") shingles();
else if (piece == "chimney")  chimney();
else if (piece == "snow")     snow();
else if (piece == "drips")    drips();
else if (piece == "frames")   frames();
else if (piece == "barge")    barge();
else if (piece == "door")     door();
else if (piece == "deco")     deco();
else if (piece == "deco2")    deco2();
