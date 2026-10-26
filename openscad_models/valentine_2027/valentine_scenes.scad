// Valentine's silhouette scenes (2026-10-26). Filled 2D shapes in mm, origin
// at the bottom centre of the scene, drawn at the size they print. Picked from
// the concepts (concepts/scenes.py) and redrawn here for a 0.4 mm nozzle: no
// stroke under SW (1.3 mm), no gap under 1.6 mm.
//
// On the Valentine's pieces these are built on the BACK of a thin pane (Scott,
// 2026-10-26): unlit the pane looks plain; lit, the thick plastic shows the
// scene dark on the glow.
// Needs SW from ../christmas_lanterns/lantern_scenes.scad.

// a heart w wide, point at the origin, lobes up: two circles and the lines from
// the point tangent to them. kr is the lobes' radius over w, kz their centres'
// height over w.
module heart2(w, kr = 0.28, kz = 0.68) let (r = w * kr, c = w / 2 - r)
    for (s = [-1, 1]) hull() { translate([s * c, w * kz]) circle(r, $fn = 64); circle(0.01); }
function heart2_h(w, kr = 0.28, kz = 0.68) = w * (kz + kr);
// centred on (x, y) instead
module heart_at(x, y, w) translate([x, y - heart2_h(w) / 2]) heart2(w);

module seg(a, b, w = SW) hull() { translate(a) circle(d = w, $fn = 16); translate(b) circle(d = w, $fn = 16); }
module path(pts, w = SW) for (i = [0 : len(pts) - 2]) seg(pts[i], pts[i + 1], w);
module dot(x, y, r = 0.9) translate([x, y]) circle(r, $fn = 16);

// gently rolling ground, its top at y
module ground(w, y, amp = 1.0) polygon(concat([for (i = [0 : 40]) let (u = -w / 2 + w * i / 40)
    [u, y + amp * sin(u / w * 540)]], [[w / 2, 0], [-w / 2, 0]]));

// a standing person, feet at (x, y), s tall
module figure(x, y, s, dress = false) translate([x, y]) {
    translate([0, s * 0.89]) circle(s * 0.11, $fn = 32);
    translate([-s * 0.045, s * 0.70]) square([s * 0.09, s * 0.11]);
    if (dress) polygon([[-s * 0.21, 0], [s * 0.21, 0], [s * 0.08, s * 0.73], [-s * 0.08, s * 0.73]]);
    else {
        polygon([[-s * 0.14, s * 0.38], [s * 0.14, s * 0.38], [s * 0.12, s * 0.75], [-s * 0.12, s * 0.75]]);
        for (k = [-1, 1]) seg([k * s * 0.065, 0.5], [k * s * 0.055, s * 0.40], max(SW, s * 0.10));
    }
}

module lamppost(x, y, h) translate([x, y]) {
    seg([0, 0], [0, h * 0.82], SW + 0.4);
    polygon([[-2.4, 0], [2.4, 0], [1.2, 3.5], [-1.2, 3.5]]);
    difference() {   // the lamp's glass left open, so it glows in the dark post
        polygon([[-3.4, h * 0.82], [3.4, h * 0.82], [4.2, h * 0.95], [-4.2, h * 0.95]]);
        translate([-2.0, h * 0.84]) square([4.0, h * 0.09]);
    }
    polygon([[-4.6, h * 0.95], [4.6, h * 0.95], [0, h]]);
}

// a couple under a lamppost in falling snow, a heart over them
module couple_lamppost(w, h) intersection() {
    translate([-w / 2, 0]) square([w, h]);
    let (s = h * 0.50) union() {
        ground(w, 6.0, 1.0);
        lamppost(w * 0.27, 5.0, h * 0.86);
        figure(-w * 0.12, 5.6, s);
        figure(w * 0.05, 5.6, s * 0.94, dress = true);
        seg([-w * 0.12 + s * 0.13, 5.6 + s * 0.55], [w * 0.05 - s * 0.11, 5.6 + s * 0.55]);   // holding hands
        heart_at(-w * 0.035, 5.6 + s * 1.24, w * 0.15);
        for (p = [[-0.36, 0.84], [-0.26, 0.64], [0.40, 0.70], [0.10, 0.93], [-0.40, 0.42], [0.39, 0.40]]) dot(p[0] * w, p[1] * h);
    }
}

// two swans facing, the curves of their necks drawing a heart, on rippled water
module swans_heart(w, h) intersection() {
    translate([-w / 2, 0]) square([w, h]);
    let (hw = w * 0.56, hb = h * 0.24, nw = SW * 1.35) union() {
        // the necks: the heart's outline; at its cusp the two heads bow in and
        // their beaks touch
        translate([0, hb]) difference() { heart2(hw); offset(delta = -nw) heart2(hw); }
        let (r = hw * 0.28, c = hw / 2 - r, cz = hb + hw * 0.68 + sqrt(r * r - c * c), hr = hw * 0.062)
            for (s = [-1, 1]) {
                hull() { translate([s * hw * 0.03, cz]) circle(nw / 2, $fn = 16); translate([s * (hr + 0.5), cz - hr * 1.6]) circle(hr, $fn = 24); }
                polygon([[s * 0.4, cz - hr * 1.9], [s * (hr + 0.6), cz - hr * 1.0], [s * (hr + 0.6), cz - hr * 2.3]]);
            }
        // the bodies, tails up, a wing line each
        for (s = [-1, 1]) {
            translate([s * w * 0.21, hb + 2.4]) scale([w * 0.21, 5.2]) circle(1, $fn = 48);
            polygon([[s * w * 0.30, hb + 0.6], [s * w * 0.45, hb + 9.5], [s * w * 0.41, hb + 3.0], [s * w * 0.34, hb + 0.2]]);
        }
        // the water
        for (k = [0 : 2], i = [0 : 2]) let (u = -w * 0.44 + k * 3 + i * w * 0.30)
            seg([u, hb - 2.0 - 2.6 * k], [u + w * 0.12, hb - 2.0 - 2.6 * k]);
        heart_at(0, h * 0.93, w * 0.11);
    }
}

// a cottage in silhouette; its round window glows, a dark heart in it
module cottage_heart(w, h) intersection() {
    translate([-w / 2, 0]) square([w, h]);
    let (cw = w * 0.70, ch = h * 0.42, wc = [cw * 0.14, 4 + ch * 0.55], wr = ch * 0.30) union() {
        ground(w, 4.5, 0.8);
        difference() {
            union() {
                translate([-cw / 2, 4]) square([cw, ch]);
                translate([0, 4 + ch]) polygon([[-cw / 2 - 3, 0], [cw / 2 + 3, 0], [0, cw * 0.48]]);
                translate([cw * 0.22, 4 + ch + cw * 0.10]) square([cw * 0.10, cw * 0.32]);
            }
            translate([-cw * 0.32, 3.9]) square([cw * 0.18, ch * 0.62]);    // the door, lit
            translate(wc) circle(wr, $fn = 48);
        }
        translate([wc[0], wc[1] - heart2_h(ch * 0.38) / 2]) heart2(ch * 0.38);
        for (k = [0 : 2]) translate([cw * 0.27 + 1.5 * k, 4 + ch + cw * 0.48 + 3.4 * k]) circle(1.2 + 0.3 * k, $fn = 16);
    }
}
