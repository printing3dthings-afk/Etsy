// Pie Drum Caddy v2 (2026-11-24): v1 plus a keeper, so it travels in one piece. v1
// (pie_caddy.scad) is live on MakerWorld (model 3621416) and stays untouched beside this.
//
// Scott: "Can it be designed to latch in somehow. So when it's moved it stays in one piece."
// He picked a keeper knob on the centre post (Benson's brief, 2026-11-22). The brief's knob
// sat on the centre well's floor, 97.5 mm down a 23 mm tube, out of a finger's reach, so
// Scott picked the tall keeper cup (2026-11-24): the knob is a tube filling the centre well,
// screwed onto the post at the bottom and turned by a knurled collar above the drum. It is
// still a pen cup, and it stands still while the drum turns round it.
//   - the post grows up through the drum and carries a thread (the jar tower's tested
//     profile: 4 mm pitch, 1.2 deep, 35 deg flanks, on a 16 mm post);
//   - the drum's bore runs through to a ledge, LEDGE above its underside;
//   - the cup screws down until its cone roof lands on the post's cone tip. That stop, not
//     how hard it's turned, sets the cup's foot KEEP_GAP above the ledge: it traps the drum
//     without clamping it, so the drum still spins. Unscrewed, the drum lifts off as v1.
// Engineering: ENGINEERING_v2.md. v1's notes follow.
//
// Pie Drum Caddy (2026-11-15). Scott's pick 4B: a round desk caddy split like a pie into wells
// of different heights, turning on a ball bearing. Engineering: ENGINEERING.md.
//
// The bearing is the one Scott tested (bearing_coupon.scad, 2026-11-15: "the test works"): 6 mm
// airsoft BBs in a channel 0.3 clear each side, the channel's floor (a top surface, ironed)
// under them and the drum's bed face over them. A post keeps the drum centred; nothing holds
// it down, so it lifts off for cleaning. Here the ball ring is 100 across (the test's was 60).
//
// The drum: six wedge wells round a centre well. Their heights climb 60 to 110 mm round the
// drum, a spiral staircase of slices. The centre well stands tallest.
//
//   part = "base" | "drum" | "keeper" (as printed: foot down) | "seated" | "section"
//          | "coupon_base" | "coupon_ring" | "coupon_keeper" (with CL)

part = "seated";
$fn = 200;

// ---- the bearing (the test print's numbers) ----------------------------------------------
BALL = 6.0;
RING_R = 50;                // the ball circle: 46 balls (10 % of the ring left empty)
N_BALLS = 46;
CH_W = BALL + 0.6;          // 0.3 each side
BASE_T = 3;
CH_D = 4;
RIM = BASE_T + CH_D;
LIFT = BALL - CH_D;         // the drum's underside above the base's rim
BASE_R = 60;
POST_R = 8;
POST_GAP = 0.4;
HOLE_COMP = 0.15;           // vertical holes print this much small on the radius
BORE_R = POST_R + POST_GAP + HOLE_COMP;

// ---- the drum -----------------------------------------------------------------------------
DRUM_R = 75;
FLOOR = 3;                  // the drum's floor; its underside is the bed face the balls run on
WALL = 1.6;                 // outer wall and dividers: four beads
N_WELLS = 6;
HEIGHTS = [45, 59, 73, 87, 101, 115];   // each wedge's height, above the drum's underside: 14 a step
                                        // (10 a step read as a plain cylinder in the first render)
FLUTES = 48;                // the outer wall fluted like a pie dish: 48 scallops,
FLUTE_A = 1.2;              // 1.2 deep (vertical detail: it prints exactly)
HUB_R = 14;                 // the centre tube's outside
HUB_WALL = 2.4;
HUB_H = 122;
// ---- v2: the keeper ------------------------------------------------------------------------
LEDGE = 15;                 // the drum's bore runs up to here; above it, the centre well
WELL_R = HUB_R - HUB_WALL;  // 11.6
TH_P = 4; TH_D = 1.2; TH_A = 35;           // exactly the jar tower's tested profile (Scott's pick, Nov 13)
TH_LEN = 12.5;              // over 3 turns on the post
// At 3 mm pitch and 1.0 deep, a 0.3 clearance left 0.7 of tooth: 2.98 x the tolerance stack, under
// the 3x rule. The jar's 4 mm / 1.2 leaves 0.9 (3.9 x) at 0.3 and 1.0 (4.3 x) at 0.2.
CL = 0.2;                   // radial thread clearance: the jar tower's tested 0.2 (the coupon tries 0.3 too)
KEEP_GAP = 0.5;             // the cup's foot above the ledge, set by the stop
KEEP_R = WELL_R - 0.6;      // 11.0: the drum turns round the cup. At 0.5 the worst case left 0.25, under the 0.3 rule
CAP_LIFT = 1.0;             // the collar's flare starts this far above the hub's top
COLLAR_H = 8; COLLAR_R = 15;
FLARE = COLLAR_R - KEEP_R;  // the 45 deg flare from the tube out to the collar, all above the hub
CUP_FLOOR = 1.6;            // above the stop cone's apex
// in the drum's frame (its underside at 0)
PT = LEDGE + TH_LEN;        // the post's thread ends here; its 45 deg cone tip rises above
TIP_H = POST_R - TH_D;      // the cone, from just inside the thread's root (0.02: level with it, the
                            // two surfaces left zero-volume slivers) to a point
POST_TOP = BASE_T + BALL + PT + TIP_H;     // in the base's frame
WELL0 = LEDGE;
KEEP_Z = LEDGE + KEEP_GAP;  // the cup's foot
KEEP_H = HUB_H + CAP_LIFT + FLARE + COLLAR_H - KEEP_Z;

module base() difference() {
    union() {
        linear_extrude(RIM) fluted2d(BASE_R);   // fluted to match the drum
        // plain up through the drum's bore, threaded above its ledge, a 45 deg tip on top
        cylinder(h = BASE_T + BALL + LEDGE, r = POST_R);
        translate([0, 0, BASE_T + BALL + LEDGE - 0.01]) post_thread();   // 0.01 into the post: level, the two stayed separate shells
        translate([0, 0, BASE_T + BALL + PT - 0.03]) cylinder(h = TIP_H, r1 = POST_R - TH_D - 0.02, r2 = 0.01);
    }
    translate([0, 0, BASE_T]) difference() {
        cylinder(h = CH_D + 1, r = RING_R + CH_W / 2);
        translate([0, 0, -1]) cylinder(h = CH_D + 3, r = RING_R - CH_W / 2);
    }
    // hollow inside the channel, down to a 1.6 floor, round the post (as the test print)
    translate([0, 0, 1.6]) difference() {
        cylinder(h = RIM, r = RING_R - CH_W / 2 - 2);
        cylinder(h = RIM, r = POST_R + 2);
    }
    // a 0.4 chamfer at the foot (elephant's foot)
    translate([0, 0, -0.01]) difference() {
        cylinder(h = 0.41, r = BASE_R + 1);
        linear_extrude(0.41, scale = BASE_R / (BASE_R - 0.4)) offset(delta = -0.4) fluted2d(BASE_R);
    }
}

// one wedge's footprint, angles a0..a1, from the hub to the drum's edge
module wedge2d(a0, a1, r0, r1) polygon(concat(
    [for (k = [0 : 24]) let (a = a0 + (a1 - a0) * k / 24) r1 * [cos(a), sin(a)]],
    [for (k = [24 : -1 : 0]) let (a = a0 + (a1 - a0) * k / 24) r0 * [cos(a), sin(a)]]));

// the fluted outline, and the wall inside it (a constant 1.6 all round the scallops)
module fluted2d(r) polygon([for (k = [0 : FLUTES * 12 - 1]) let (a = 360 * k / (FLUTES * 12))
    (r - FLUTE_A / 2 + FLUTE_A / 2 * cos(FLUTES * a)) * [cos(a), sin(a)]]);
module wall2d() difference() { fluted2d(DRUM_R); offset(delta = -WALL) fluted2d(DRUM_R); }
module sector2d(a0, a1) polygon(concat([[0, 0]], [for (k = [0 : 24]) let (a = a0 + (a1 - a0) * k / 24) 2 * DRUM_R * [cos(a), sin(a)]]));

module drum() {
    step = 360 / N_WELLS;
    difference() {
        union() {
            linear_extrude(FLOOR) fluted2d(DRUM_R);
            // the outer wall, each well's slice at its own height
            for (i = [0 : N_WELLS - 1]) linear_extrude(HEIGHTS[i])
                intersection() { wall2d(); sector2d(i * step, (i + 1) * step); }
            // dividers, each as tall as the taller well it parts
            for (i = [0 : N_WELLS - 1]) rotate(i * step)
                translate([HUB_R - 0.5, -WALL / 2, 0]) cube([DRUM_R - FLUTE_A - HUB_R, WALL, max(HEIGHTS[i], HEIGHTS[(i + N_WELLS - 1) % N_WELLS])]);
            cylinder(h = HUB_H, r = HUB_R);
        }
        // the centre well
        translate([0, 0, LEDGE]) cylinder(h = HUB_H, r = WELL_R);
        // the post's bore, now right through to the ledge, and a 0.5 lead-in
        translate([0, 0, -0.01]) cylinder(h = LEDGE + 0.02, r = BORE_R);
        translate([0, 0, -0.01]) cylinder(h = 0.51, r1 = BORE_R + 0.5, r2 = BORE_R);
        // a 0.4 chamfer at the drum's foot (elephant's foot)
        translate([0, 0, -0.01]) difference() {
            cylinder(h = 0.41, r = DRUM_R + 1);
            linear_extrude(0.41, scale = DRUM_R / (DRUM_R - 0.4)) offset(delta = -0.4) fluted2d(DRUM_R);
        }
    }
}

// ---- the thread: the jar tower coupon's th_r() profile, a 35 deg lead-in at each end ----------
TH_F = TH_D / tan(TH_A);
TH_FLAT = (TH_P - 2 * TH_F) / 2;
function th_r(R, u) = let (r0 = R - TH_D)
    u < TH_FLAT ? r0 :
    u < TH_FLAT + TH_F ? r0 + TH_D * (u - TH_FLAT) / TH_F :
    u < 2 * TH_FLAT + TH_F ? R :
    R - TH_D * (u - 2 * TH_FLAT - TH_F) / TH_F;
// 180 points round and 48 slices a pitch: 0.08 mm steps up the axis. At the jar's 360 x 96 one
// keeper came out at 48 MB and took over ten minutes to export.
module thread(R, h) linear_extrude(h, twist = -360 * h / TH_P, slices = ceil(h / TH_P * 48), convexity = 4)
    polygon([for (i = [0 : 2 : 359]) let (u = i / 360 * TH_P) th_r(R, u) * [cos(i), sin(i)]]);
// the post's thread, its first tooth eased in from the root at the flank angle
module post_thread() intersection() {
    thread(POST_R, TH_LEN);
    cylinder(h = TH_LEN, r1 = POST_R - TH_D + 0.01, r2 = POST_R - TH_D + 0.01 + TH_LEN * tan(TH_A));
}

// ---- the keeper cup, in its own frame (foot at 0), as it prints: foot on the bed ------------
// Inside its foot: the thread cut CL out, then a 45 deg cone roof matching the post's tip, so
// screwing it home lands cone on cone; above, a 1.6 floor and the pen cup.
module keeper(h = KEEP_H, cl = CL, coupon = false) let (stop = PT - KEEP_Z) difference() {
    if (coupon) union() {           // the test's keeper: no collar, a knurled band at the top to grip
        cylinder(h = h - 6, r = KEEP_R);
        translate([0, 0, h - 6.01]) knurl(KEEP_R + 0.2, 6.01);
    } else union() {
        cylinder(h = h - COLLAR_H, r = KEEP_R);
        // the collar: knurled, under it a 45 deg flare from the tube (it prints with no support)
        // (it starts CAP_LIFT above the hub: started below, it cut 328 mm3 into the hub's top)
        translate([0, 0, h - COLLAR_H - FLARE]) cylinder(h = FLARE + 0.01, r1 = KEEP_R, r2 = COLLAR_R - 1);
        translate([0, 0, h - COLLAR_H]) knurl(COLLAR_R, COLLAR_H);
    }
    // the nut: crests at root + CL, the thread grown CL, a lead-in at the foot
    // 0.02 inside the thread's root: level with it, the two surfaces left zero-volume slivers
    translate([0, 0, -0.01]) cylinder(h = stop + 0.02, r = POST_R - TH_D + cl - 0.02);
    translate([0, 0, -0.01]) thread(POST_R + cl, stop + 0.02);
    translate([0, 0, -0.01]) cylinder(h = 1.0, r1 = POST_R + cl + 0.4, r2 = POST_R - TH_D + cl);
    // the stop: exactly the post's tip, so cone lands on cone with the foot KEEP_GAP above the
    // ledge. Grown by CL like the thread, it would let the cup sink CL / tan 45 = 0.2 lower.
    translate([0, 0, stop - 0.01]) cylinder(h = TIP_H + 0.02, r1 = POST_R - TH_D - 0.02, r2 = 0.01);
    // the pen cup, from above the stop's apex to the top
    translate([0, 0, stop + TIP_H + CUP_FLOOR]) cylinder(h = h, r = KEEP_R - 2.0);
}
module knurl(r, h, n = 36) intersection() {
    cylinder(h = h, r = r);
    linear_extrude(h) polygon([for (k = [0 : 2 * n - 1]) (k % 2 ? r - 0.8 : r + 0.2) * [cos(180 * k / n), sin(180 * k / n)]]);
}

// ---- the coupon: the joint only, at the real sizes (the critical part, under 30 minutes) -----
// a disc with the post (LEDGE of plain post, then the thread and tip), a ring standing in for
// the drum's hub round the bore, and a short keeper (its foot, nut, stop and a short collar).
C_RING_H = 4;
module coupon_base() union() {
    cylinder(h = 2.4, r = 16);
    translate([0, 0, 2.4]) cylinder(h = C_RING_H, r = POST_R);
    translate([0, 0, 2.4 + C_RING_H - 0.01]) post_thread();
    translate([0, 0, 2.4 + C_RING_H + TH_LEN - 0.03]) cylinder(h = TIP_H, r1 = POST_R - TH_D - 0.02, r2 = 0.01);
}
module coupon_ring() difference() {     // the drum's hub round its bore: it must spin under the keeper
    cylinder(h = C_RING_H, r = HUB_R);
    translate([0, 0, -1]) cylinder(h = C_RING_H + 2, r = BORE_R);
    translate([0, 0, -0.01]) cylinder(h = 0.51, r1 = BORE_R + 0.5, r2 = BORE_R);
}
// the ring stands on the disc and is as tall as the plain stub, so its top is the ledge and the
// keeper's foot sits KEEP_GAP over it, exactly as on the caddy
C_KEEP_H = (PT - KEEP_Z) + TIP_H + CUP_FLOOR;   // shut at the top: the nut, the stop and the floor only

module balls() for (i = [0 : N_BALLS - 1]) rotate(i * 360 / N_BALLS) translate([RING_R, 0, BASE_T + BALL / 2]) sphere(d = BALL, $fn = 32);

if (part == "base") base();
else if (part == "drum" || part == "gate_drum") drum();
else if (part == "keeper") keeper();
else if (part == "seated" || part == "section") intersection() {
    union() {
        base(); translate([0, 0, BASE_T + BALL]) drum(); color("gold") balls();
        // turned to the post's thread phase (the post's helix starts at the ledge)
        color("lightblue") translate([0, 0, BASE_T + BALL + KEEP_Z]) rotate(360 * KEEP_GAP / TH_P) keeper();
    }
    if (part == "section") translate([0, -200, -1]) cube([400, 400, 400]); else cube(1000, center = true);
}
else if (part == "coupon_base") coupon_base();
else if (part == "coupon_ring") coupon_ring();
else if (part == "coupon_keeper") difference() {     // one notch per 0.1 over 0.1: 0.2 one, 0.3 two
    keeper(C_KEEP_H, CL, coupon = true);
    for (k = [1 : round(CL * 10) - 1]) rotate(k * 12) translate([KEEP_R, 0, C_KEEP_H - 2]) cube([2.4, 1.2, 5], center = true);
}
else if (part == "keeper_seated") translate([0, 0, BASE_T + BALL + KEEP_Z]) rotate(360 * KEEP_GAP / TH_P) keeper();
else if (part == "drum_seated") translate([0, 0, BASE_T + BALL]) drum();
// the drum within the hub's radius, for the fit check: drum() there is just this
else if (part == "hub_seated") translate([0, 0, BASE_T + BALL]) difference() {
    cylinder(h = HUB_H, r = HUB_R);
    translate([0, 0, LEDGE]) cylinder(h = HUB_H, r = WELL_R);
    translate([0, 0, -0.01]) cylinder(h = LEDGE + 0.02, r = BORE_R);
    translate([0, 0, -0.01]) cylinder(h = 0.51, r1 = BORE_R + 0.5, r2 = BORE_R);
}
echo("RIM", RIM, "drum underside", BASE_T + BALL, "post tip", POST_TOP, "ledge", LEDGE, "thread", LEDGE, PT,
     "keeper foot", KEEP_Z, "keeper height", KEEP_H, "cup depth", KEEP_H - (PT - KEEP_Z) - TIP_H - CUP_FLOOR);
