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

module lamppost(x, y, h) translate([x, y]) {
    seg([0, 0], [0, h * 0.82], SW + 0.4);
    polygon([[-2.4, 0], [2.4, 0], [1.2, 3.5], [-1.2, 3.5]]);
    difference() {   // the lamp's glass left open, so it glows in the dark post
        polygon([[-3.4, h * 0.82], [3.4, h * 0.82], [4.2, h * 0.95], [-4.2, h * 0.95]]);
        translate([-1.8, h * 0.82 + SW + 0.2]) square([3.6, h * 0.13 - 2 * SW - 0.4]);   // every bar over SW (the top and bottom were 0.02 h, 1.1 mm)
    }
    polygon([[-4.6, h * 0.95], [4.6, h * 0.95], [0, h]]);
}

// a couple under a lamppost in falling snow, a heart over them. Redrawn 2026-11-17 (Scott,
// 2026-10-30: "remodelled with real detail"; the first pair read as round-head cutouts):
// two profiles face to face, so nose, lips and chin carry the read; his long coat and
// blown scarf, her long hair and flared skirt, on tiptoe, one foot kicked up behind;
// their hands joined. Every detail runs sideways: lit, the art smears 3.2 mm downwards
// (art_in), so a gap under a feature fills, and one beside it doesn't.
module couple_lamppost(w, h) intersection() {
    translate([-w / 2, 0]) square([w, h]);
    let (s = h * 0.62, g = 5.6) union() {
        ground(w, 6.0, 1.0);
        lamppost(w * 0.29, 5.0, h * 0.92);
        translate([-w * 0.095, g]) man_profile(s);
        translate([w * 0.080, g]) mirror([1, 0]) woman_profile(s * 0.95);
        heart_at(0, g + s * 1.13, w * 0.13);
        for (p = [[-0.40, 0.86], [-0.30, 0.62], [0.42, 0.62], [0.16, 0.97], [-0.43, 0.40], [0.18, 0.80], [-0.18, 0.98]]) dot(p[0] * w, p[1] * h);
    }
}

// a man in profile facing +x, feet at the origin, s tall: long coat, scarf blown back,
// one arm reaching forward to hold a hand
module man_profile(s) offset(r = -0.8) offset(r = 0.8) offset(r = 0.35) offset(delta = -0.35) scale([s, s]) {
    // trousers, one shape: a notch between the legs closed into a hole where the shoes meet
    polygon([[-0.074, 0.03], [0.066, 0.03], [0.052, 0.33], [-0.068, 0.33]]);
    // shoes: the front one pointing forward, the back one behind; sunk 0.04 into the ground,
    // whose wave left a 0.4 mm sliver of light under them
    translate([-0.098, -0.04]) square([0.200, 0.045]);
    polygon([[0.006, 0], [0.105, 0], [0.104, 0.022], [0.072, 0.040], [0.012, 0.040]]);
    polygon([[-0.098, 0], [0.010, 0], [0.010, 0.030], [-0.020, 0.040], [-0.082, 0.040], [-0.100, 0.020]]);   // meets the front shoe: a slit between them filled
    // the coat, knee length, flaring a little at the hem
    polygon([[-0.108, 0.30], [0.092, 0.30], [0.062, 0.50], [0.066, 0.56], [0.080, 0.70], [0.058, 0.762],
             [0.010, 0.785], [-0.058, 0.772], [-0.088, 0.725], [-0.082, 0.56], [-0.074, 0.50]]);
    // the belt line: a notch at the waist, front and back
    polygon([[0.060, 0.505], [0.080, 0.522], [0.064, 0.540]]);
    // scarf: wrapped high round the neck, its tail blown back
    polygon([[-0.050, 0.745], [0.050, 0.760], [0.052, 0.815], [-0.040, 0.812]]);
    polygon([[-0.045, 0.805], [-0.010, 0.792], [-0.075, 0.730], [-0.118, 0.700], [-0.140, 0.716], [-0.098, 0.752]]);
    // the near arm, down and forward to the joined hands
    hull() { translate([0.030, 0.700]) circle(0.042, $fn = 24); translate([0.160, 0.530]) circle(0.030, $fn = 24); }
    // head in profile: crown, brow, nose, lips, chin
    polygon([[-0.050, 0.835], [-0.068, 0.885], [-0.060, 0.935], [-0.025, 0.972], [0.025, 0.978], [0.060, 0.955],
             [0.074, 0.925], [0.080, 0.905], [0.112, 0.874], [0.084, 0.862], [0.090, 0.851], [0.082, 0.842],
             [0.088, 0.832], [0.078, 0.814], [0.045, 0.806], [0.030, 0.790], [-0.020, 0.790]]);
    // hair: short, swept up at the front
    polygon([[-0.072, 0.875], [-0.070, 0.935], [-0.040, 0.978], [0.010, 0.995], [0.055, 0.988], [0.080, 0.965],
             [0.076, 0.945], [0.040, 0.950], [-0.020, 0.930], [-0.050, 0.880]]);
}

// a woman in profile facing +x, feet at the origin, s tall: long hair down her back,
// fitted top, flared skirt; on tiptoe, her back foot kicked up behind
module woman_profile(s) offset(r = -0.8) offset(r = 0.8) offset(r = 0.35) offset(delta = -0.35) scale([s, s]) {
    // the standing leg, on tiptoe, sunk into the ground as his shoes are
    translate([-0.008, -0.04]) square([0.040, 0.045]);
    polygon([[-0.006, 0.000], [0.034, 0.000], [0.030, 0.050], [0.026, 0.27], [-0.026, 0.27], [-0.018, 0.060]]);
    // the back leg, bent at the knee, foot up behind
    hull() { translate([-0.020, 0.240]) circle(0.030, $fn = 24); translate([-0.150, 0.300]) circle(0.025, $fn = 24); }
    polygon([[-0.150, 0.276], [-0.205, 0.300], [-0.200, 0.330], [-0.150, 0.325]]);
    // the skirt, flared from the waist
    polygon([[-0.125, 0.235], [0.115, 0.235], [0.050, 0.540], [-0.055, 0.540]]);
    // fitted top
    polygon([[-0.058, 0.530], [0.050, 0.530], [0.062, 0.660], [0.050, 0.720], [0.012, 0.745], [-0.048, 0.740],
             [-0.068, 0.690]]);
    // the near arm, forward and down to the joined hands
    hull() { translate([0.022, 0.680]) circle(0.036, $fn = 24); translate([0.140, 0.545]) circle(0.027, $fn = 24); }
    // neck and head in profile: a smaller nose, a lifted chin
    polygon([[-0.022, 0.730], [0.030, 0.730], [0.040, 0.790], [-0.010, 0.800]]);
    polygon([[-0.050, 0.810], [-0.064, 0.860], [-0.056, 0.905], [-0.020, 0.940], [0.025, 0.945], [0.058, 0.925],
             [0.070, 0.895], [0.074, 0.875], [0.098, 0.852], [0.076, 0.842], [0.082, 0.831], [0.075, 0.823],
             [0.080, 0.812], [0.068, 0.796], [0.035, 0.790], [0.020, 0.778], [-0.020, 0.780]]);
    // long hair: over the crown and down her back past the shoulders
    polygon([[0.040, 0.930], [0.064, 0.915], [0.040, 0.958], [-0.010, 0.972], [-0.060, 0.950], [-0.085, 0.900],
             [-0.098, 0.820], [-0.108, 0.720], [-0.120, 0.640], [-0.080, 0.630], [-0.058, 0.700], [-0.045, 0.790],
             [-0.040, 0.870], [-0.010, 0.920]]);
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

// ---- the chocolate shops' windows (2026-10-26) ------------------------------------------------
// A shop's display, w x h, built into the back of its pane. Two shelves; on
// the lower a heart box between piles of truffles, on the upper three wrapped
// boxes. Lit, every line carries a 3.2 mm fillet down the glass, so the upper
// shelf sits that far above the tallest thing under it.
module display(w, h) intersection() {
    translate([-w / 2, 0]) square([w, h]);
    union() {
        translate([-w / 2, 0]) square([w, 1.3]);
        translate([-w / 2, 10]) square([w, 1.3]);
        heart_at(0, 1.3 + 2.6, 5.4);
        for (s = [-1, 1], r = [0 : 2], k = [0 : 2 - r]) dot(s * (w * 0.30) + (k - (2 - r) / 2) * 2.5, 2.4 + r * 2.1, 1.05);
        for (i = [-1 : 1]) translate([i * w * 0.30, 11.3]) {
            translate([-1.9, 0]) square([3.8, 2.8]);
            for (s = [-1, 1]) translate([s * 0.9, 3.4]) circle(0.8, $fn = 12);
        }
    }
}
// Cupid's arrow through a heart window, w across: a shaft, a head, fletching
module cupid_arrow(w) rotate(28) {
    seg([-w * 0.48, 0], [w * 0.40, 0], 1.4);
    polygon([[w * 0.36, -1.9], [w * 0.52, 0], [w * 0.36, 1.9]]);
    for (s = [-1, 1]) polygon([[-w * 0.48, 0], [-w * 0.40, 0], [-w * 0.50, s * 2.2], [-w * 0.56, s * 2.2]]);
}

