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
// (a heart over their heads read as a clover with them; left out, 2026-10-26).
// nw the necks' width; wing cuts a wing line in each body, for where the scene
// is not built into a pane (the Swan Crown's crown), since in a pane the line
// above fills it. bh the bodies' height, w * 0.09 if not given.
module swans_heart(w, h, nw = SW * 1.35, water = true, wing = false, bh = 0) intersection() {
    translate([-w / 2, 0]) square([w, h]);
    let (hw = w * 0.56, hb = h * 0.24) union() {
        // the necks: the heart's outline; at its cusp the two heads bow in and
        // their beaks touch
        translate([0, hb]) difference() { heart2(hw); offset(delta = -nw) heart2(hw); }
        let (r = hw * 0.28, c = hw / 2 - r, cz = hb + hw * 0.68 + sqrt(r * r - c * c), hr = hw * 0.062)
            for (s = [-1, 1]) {
                hull() { translate([s * hw * 0.03, cz]) circle(nw / 2, $fn = 16); translate([s * (hr + 0.5), cz - hr * 1.6]) circle(hr, $fn = 24); }
                polygon([[s * 0.4, cz - hr * 1.9], [s * (hr + 0.6), cz - hr * 1.0], [s * (hr + 0.6), cz - hr * 2.3]]);
            }
        // the bodies, breast to breast where the necks meet, tails up
        for (s = [-1, 1]) mirror([s < 0 ? 1 : 0, 0]) translate([1.2, hb - 1.0]) swan_body(w * 0.36, bh > 0 ? bh : w * 0.09, wing);
        // the water: two rows of ripples. Built into the back of a pane, every
        // line carries a fillet 3.2 mm down the glass (relief_lib art_in), so
        // the rows sit further apart than that or they run together lit.
        if (water) for (k = [0 : 1], i = [0 : 2]) let (u = -w * 0.43 + k * 4.5 + i * w * 0.30)
            seg([u, hb - 6.0 - 5.0 * k], [u + w * 0.11, hb - 6.0 - 5.0 * k]);
    }
}

// a swan's body facing -x, breast at the origin, waterline on y = 0, L long, H
// high at the back. In a pane it stays a plain silhouette: a wing line there
// fills with the fillet of the line above it and does not show lit
// (2026-10-26). Where it stands free (wing = true, the Swan Crown's crown) it
// carries a raised wing arched over its back, feathers cut into it.
module swan_body(L, H, wing = false) {
    offset(r = 2.0) offset(delta = -2.0) polygon(wing
        ? [[2.0, 0], [L * 0.80, 0], [L * 0.98, H * 0.60], [L * 0.86, H * 0.80], [L * 0.50, H * 0.85], [L * 0.15, H * 0.98], [0, H * 0.62]]
        : [[2.0, 0], [L * 0.80, 0], [L, H * 1.40], [L * 0.90, H * 1.32], [L * 0.68, H * 1.02], [L * 0.38, H * 1.08], [L * 0.14, H * 1.00], [0, H * 0.62]]);
    if (wing) difference() {
        offset(r = 1.2) offset(delta = -1.2) polygon([[L * 0.18, H * 0.55], [L * 0.40, H * 1.00], [L * 0.62, H * 1.42],
            [L * 0.86, H * 1.88], [L * 1.04, H * 2.05], [L * 0.98, H * 1.45], [L * 0.86, H * 0.85], [L * 0.52, H * 0.50]]);
        // three feather lines, each stopping short of the wing's edges
        for (k = [0 : 2]) path([[L * (0.42 + 0.15 * k), H * (0.70 + 0.06 * k)], [L * (0.52 + 0.15 * k), H * (1.02 + 0.22 * k)]], 1.4);
    }
}

// a swan gliding, facing +x when s = 1, -x when s = -1, its waterline at (x, y)
module swan_glide(x, y, s = 1) translate([x, y]) mirror([s < 0 ? 1 : 0, 0]) {
    scale([13, 5]) translate([0, 0.9]) circle(1, $fn = 48);                              // body
    polygon([[-10.5, 3.2], [-17, 11], [-12.5, 6.5]]);                                    // tail
    path([[8, 5.5], [12.5, 14.5], [10.5, 22.5], [12.5, 25.5]], SW + 0.6);                // neck
    translate([13, 26]) circle(2.1, $fn = 20);                                           // head
    polygon([[14.5, 26.7], [18.2, 25.5], [14.5, 24.8]]);                                 // beak
}

// a reed clump at x: three stems, a bulrush head on the tallest
module reeds(x, h) {
    for (r = [[0, 0.46], [2.2, 0.36], [-2.0, 0.30]]) seg([x + r[0], 4], [x + r[0] * 1.4, h * r[1]]);
    seg([x, h * 0.46 - 6], [x, h * 0.46], SW + 1.2);
}

// a pond at night, L long, wrapping a drum: two swans gliding to meet under a
// heart, reeds, a crescent moon, hearts drifting up and a few stars
module pond_panorama(L, h) intersection() {
    translate([-L / 2, 0]) square([L, h]);
    union() {
        ground(L, 5.0, 0.8);
        for (u = [-0.46, -0.42, -0.07, 0.30, 0.34, 0.44]) reeds(u * L, h);
        swan_glide(-L * 0.22, 4.5, 1);
        swan_glide(L * 0.10, 4.5, -1);
        heart_at(-L * 0.06, 34, 9);
        translate([L * 0.22, h * 0.80]) difference() { circle(7, $fn = 48); translate([3.4, 1.2]) circle(6, $fn = 48); }
        for (p = [[-0.36, 0.74], [-0.15, 0.88], [0.40, 0.66]]) heart_at(p[0] * L, p[1] * h, 5.5);
        for (p = [[-0.30, 0.90], [0.05, 0.92], [0.32, 0.88], [-0.44, 0.84]]) dot(p[0] * L, p[1] * h);
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
