// Shared geometry helpers for this shop's wall-mounted parts.
//
// Extracted 2026-09-10 when the outlet shelf became the second caller of the
// lattice code the wall charging shelf introduced -- not speculatively; the
// house rule is that three similar lines beat a helper until a real second
// case turns up.
//
// AXIS CONVENTION these helpers assume, and the reason for it: parts that
// mount on a wall are modelled in the orientation they PRINT in, which is
// back-flat. So world +Z is depth out from the wall AND the build direction,
// world +Y is up the wall, world +X is along it. Every overhang judgement in
// a caller is then a plain statement about z.

// ---- extrusion helpers ---------------------------------------------------
// child 2D is drawn as (x, z); result spans y in [0, thk]
module extrude_xz(thk) { rotate([90,0,0]) translate([0,0,-thk]) linear_extrude(thk) children(); }

// child 2D is drawn as (z, y); result spans x in [-thk, 0].
// rotate([0,90,0]) is the trap here and it renders, gates watertight and
// slices: it sends the profile's x to world MINUS z, so a part comes out
// mirrored into negative depth while every other check passes.
module extrude_zy(thk) { rotate([0,-90,0]) linear_extrude(thk) children(); }

// rounded slot between two points, in 2D
module slot2d(x0, y0, x1, y1, d) {
    hull() { translate([x0,y0]) circle(d=d); translate([x1,y1]) circle(d=d); }
}

// ---- polygon predicates, for placing cells by containment ----------------
function rot2(p, a) = [p.x*cos(a) - p.y*sin(a), p.x*sin(a) + p.y*cos(a)];

function pip(p, pts) =
    (len([for (i = [0 : len(pts)-1])
        let (a = pts[i], b = pts[(i+1) % len(pts)])
        if (((a.y > p.y) != (b.y > p.y)) &&
            (p.x < (b.x-a.x) * (p.y-a.y) / (b.y-a.y) + a.x)) 1]) % 2) == 1;

function seg_d(p, a, b) =
    let (v = b - a, w = p - a, L2 = v*v,
         t = L2 == 0 ? 0 : max(0, min(1, (w*v) / L2)))
    norm(p - (a + t*v));

function edge_d(p, pts) =
    min([for (i = [0 : len(pts)-1]) seg_d(p, pts[i], pts[(i+1) % len(pts)])]);

function far_in(p, pts, d)  =  pip(p, pts) && edge_d(p, pts) >= d;
function far_out(p, pts, d) = !pip(p, pts) && edge_d(p, pts) >= d;

function cell_fits(c, vs, outline, keepouts, d) =
    len([for (v = vs) if (!far_in(c + v, outline, d)) 1]) == 0 &&
    len([for (k = keepouts) for (v = vs) if (!far_out(c + v, k, d)) 1]) == 0;

function rrect_pts(w, h, r, seg = 6) =
    [for (q = [0 : 3], i = [0 : seg])
        let (cx = (q == 0 || q == 3 ? 1 : -1) * (w/2 - r),
             cy = (q < 2 ? 1 : -1) * (h/2 - r),
             a  = (q == 0 ? 0 : q == 1 ? 90 : q == 2 ? 180 : 270) + 90 * i / seg)
        [cx + r*cos(a), cy + r*sin(a)]];

function rect_pts(cx, cy, w, h) =
    [[cx-w/2, cy-h/2], [cx+w/2, cy-h/2], [cx+w/2, cy+h/2], [cx-w/2, cy+h/2]];

// ---- the lattice itself --------------------------------------------------
// Cells are PLACED ONLY IF THEY FIT WHOLE. The obvious construction --
// intersect an infinite hex field with the region -- renders, gates and slices
// fine, and looks wrong: a cell clipped by the region boundary leaves a
// tapering needle of material between it and its neighbour. Measured on the
// wall shelf's first build, those needles were 1.26-1.68mm wide, so nothing
// flagged them; they are perfectly printable, they just read as a modelling
// mistake. Testing each cell's six real vertices costs ~30 lines and removes
// them, and the solid frame is then whatever is left over rather than a
// separate inset shape to keep in sync.
//
// A lattice cut ALONG the build axis is a plain vertical hole and wants k = 1.
// A lattice cut ACROSS it has a roof: a regular pointy-up hexagon puts its top
// edges at 60 deg from vertical, past what the P1S holds, and k = 1.5 brings
// them to a measured 49.1 deg. Size the stretch to the real 55 deg limit with
// margin, not to 45 -- k = 1.73 hits 45 exactly and squashes the cell to
// 2.2:1 for nothing.
module cell_2d(R, k, rib) { offset(r = -rib/2) scale([1, k]) rotate(30) circle(r = R, $fn = 6); }

module lattice(outline, keepouts, R, k, brd, rib, turn = 0, reach = 130) {
    px = sqrt(3) * R;
    py = 1.5 * R * k;
    vs = [for (j = [0:5]) rot2([R*cos(30 + 60*j), k*R*sin(30 + 60*j)], turn)];
    for (j = [-ceil(reach/py) : ceil(reach/py)], i = [-ceil(reach/px) : ceil(reach/px)])
        let (c = rot2([(i + (j % 2 == 0 ? 0 : 0.5)) * px, j * py], turn))
            if (cell_fits(c, vs, outline, keepouts, brd))
                translate(c) rotate(turn) cell_2d(R, k, rib);
}

// The 3D version, for a lattice cut along the build axis. Every cell gets a
// 45 deg lead-in on the room-facing face, so nothing resting against the part
// meets a raw cut edge. It is a hull between the plain cell and an offset()
// one, NOT linear_extrude(scale=): scale ramps over the whole extrude height,
// so a 0.6mm chamfer asked for that way delivered 0.22mm inside a 2.52mm
// plate -- measured, not assumed. The flare faces the room, so in the print
// it is a 45 deg downward face, inside the 55 deg limit.
module lattice_cut(outline, keepouts, R, k, brd, rib, h, cham, turn = 0, reach = 130) {
    px = sqrt(3) * R;
    py = 1.5 * R * k;
    vs = [for (j = [0:5]) rot2([R*cos(30 + 60*j), k*R*sin(30 + 60*j)], turn)];
    for (j = [-ceil(reach/py) : ceil(reach/py)], i = [-ceil(reach/px) : ceil(reach/px)])
        let (c = rot2([(i + (j % 2 == 0 ? 0 : 0.5)) * px, j * py], turn))
            if (cell_fits(c, vs, outline, keepouts, brd))
                translate(c) rotate(turn) {
                    translate([0, 0, -1]) linear_extrude(h + 2) cell_2d(R, k, rib);
                    hull() {
                        translate([0, 0, h - cham]) linear_extrude(0.01) cell_2d(R, k, rib);
                        translate([0, 0, h + 0.5]) linear_extrude(0.01)
                            offset(r = cham + 0.5) cell_2d(R, k, rib);
                    }
                }
}
