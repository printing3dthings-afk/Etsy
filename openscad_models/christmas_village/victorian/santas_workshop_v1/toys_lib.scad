// Toy outlines for the Victorian Santa's workshop window (2026-10-02).
// Each toy is 2D, origin at its bottom centre, about 10 mm tall, drawn in
// lines tw wide: two passes of the 0.4 mm nozzle, so every line can be laid.
// Draw them at scale 1 only: scaled, the lines would thin with them.
tw = 0.8;

module stroke(w = tw) difference() { offset(r = w / 2, $fn = 16) children(); offset(r = -w / 2, $fn = 16) children(); }
module seg(a, b, w = tw) hull() { translate(a) circle(d = w, $fn = 12); translate(b) circle(d = w, $fn = 12); }
module pline(p, w = tw) for (i = [0 : len(p) - 2]) seg(p[i], p[i + 1], w);
module dot(p, r = 0.45) translate(p) circle(r = r, $fn = 16);

module teddy() {
    stroke() union() {
        translate([0, 7.0]) circle(r = 2.3, $fn = 40);
        for (s = [-1, 1]) translate([s * 1.9, 8.7]) circle(r = 1.0, $fn = 24);
        translate([0, 3.4]) scale([2.5, 3.0]) circle(r = 1, $fn = 40);
        for (s = [-1, 1]) hull() { translate([s * 2.3, 4.8]) circle(r = 0.8, $fn = 20); translate([s * 3.5, 3.3]) circle(r = 0.8, $fn = 20); }
        for (s = [-1, 1]) translate([s * 1.5, 1.2]) circle(r = 1.2, $fn = 24);
    }
    for (s = [-1, 1]) dot([s * 0.85, 7.4]);
    dot([0, 6.2], 0.55);
    translate([0, 3.2]) stroke() circle(r = 1.4, $fn = 32);
}

module rocking_horse() {
    R = 16;
    intersection() {
        translate([0, R + 0.4]) difference() { circle(r = R, $fn = 200); circle(r = R - tw, $fn = 200); }
        translate([-7.5, 0]) square([15, 2.6]);
    }
    for (s = [-1, 1]) { seg([s * 3.6, 1.1], [s * 2.7, 4.2]); seg([s * 2.2, 1.0], [s * 1.4, 4.1]); }
    stroke() union() {
        translate([0, 5.6]) scale([4.0, 1.7]) circle(r = 1, $fn = 48);
        hull() { translate([2.8, 6.2]) circle(r = 1.3, $fn = 24); translate([4.2, 8.9]) circle(r = 1.0, $fn = 24); }
        hull() { translate([4.4, 9.1]) circle(r = 1.2, $fn = 24); translate([6.5, 7.9]) circle(r = 0.75, $fn = 20); }
        translate([3.6, 10.0]) polygon([[0, 0], [1.1, 0], [0.3, 1.5]]);
    }
    pline([[-3.8, 6.3], [-5.0, 5.9], [-5.9, 4.6]]);
    dot([4.8, 9.4], 0.45);
}

module train() {
    stroke() union() {
        translate([-1.2, 2.2]) square([6.6, 3.8]);
        translate([5.4, 2.2]) polygon([[0, 0], [1.4, -1.3], [1.4, 0], [0, 1.6]]);
        translate([-6.2, 2.2]) square([5.2, 6.4]);
        translate([-6.8, 8.4]) square([6.4, 1.0]);
        translate([3.4, 6.0]) square([1.6, 2.4]);
        translate([3.0, 8.0]) square([2.4, 1.2]);
    }
    translate([-5.0, 5.0]) stroke() square([2.8, 2.4]);
    for (w = [[-3.6, 1.7, 1.7], [1.2, 1.3, 1.3], [4.2, 1.3, 1.3]]) translate([w[0], w[1]]) stroke() circle(r = w[2], $fn = 32);
}

module soldier() {
    stroke() union() {
        translate([-1.1, 7.6]) square([2.2, 2.4]);
        translate([0, 7.0]) circle(r = 1.0, $fn = 24);
        translate([-1.5, 3.2]) square([3.0, 3.4]);
        translate([-1.2, 0]) square([2.4, 3.6]);
    }
    seg([0, 0.4], [0, 3.0]);
    seg([2.6, 1.6], [2.6, 8.8]);   // rifle
    dot([0, 10.4], 0.6);           // plume
}

module drum() {
    stroke() translate([-3.3, 0.6]) square([6.6, 4.6]);
    pline([[-2.4, 1.6], [-1.2, 4.2], [0, 1.6], [1.2, 4.2], [2.4, 1.6]]);
    seg([-3.0, 8.0], [1.4, 5.6]);
    seg([3.0, 8.0], [-1.4, 5.6]);
}

module sailboat() {
    stroke() polygon([[-4, 2.4], [4, 2.4], [2.8, 0.4], [-2.8, 0.4]]);
    seg([0, 2.4], [0, 9.6]);
    stroke() polygon([[0.9, 3.6], [0.9, 8.8], [3.9, 3.6]]);
    stroke() polygon([[-0.9, 3.8], [-0.9, 7.4], [-3.0, 3.8]]);
    translate([0, 9.0]) polygon([[0, 0], [1.8, 0.6], [0, 1.2]]);
}

module jack_in_box() {
    translate([-2.4, 0]) stroke() square([4.8, 4.4]);
    seg([-2.4, 4.4], [-4.2, 6.6]);
    pline([[0, 4.4], [-1.0, 5.0], [1.0, 5.8], [-1.0, 6.6], [0, 7.0]]);
    translate([0, 8.1]) stroke() circle(r = 1.3, $fn = 32);
    translate([0, 9.1]) polygon([[-1.0, 0], [1.0, 0], [0.3, 1.6]]);
}

module toy(name) {
    if (name == "teddy") teddy();
    else if (name == "horse") rocking_horse();
    else if (name == "train") train();
    else if (name == "soldier") soldier();
    else if (name == "drum") drum();
    else if (name == "boat") sailboat();
    else if (name == "jack") jack_in_box();
}
