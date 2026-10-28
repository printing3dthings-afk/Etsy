// Nesting Characters, forms 1 and 3 (2026-10-28): concept blockouts for Scott
// to pick from. Shape studies only: no threads, no hollows, nothing here is
// the printable model. A set of 5, each 0.8 of the last, the largest opened.
//   form 1  egg matryoshka with cat ears, face, scarf and paws
//   form 3  mushroom folk: a little person under a cap; the cap is the top half

form = 1;           // 1 | 3
part = "all";       // body0..body4 | cap0..cap4 | trim | dark | pink | all
$fn = 72;
HS = [90, 72, 57.6, 46.1, 36.9];
GAP = 9;
LIFT = 26;          // the largest's top half, lifted to show it opens

// ---- profiles: radius at t (0 = foot, 1 = top), in units of the height ----
function smax(a, b, p = 7) = pow(pow(max(a, 0), p) + pow(max(b, 0), p), 1 / p);
function ell(t, c, h, r) = abs(t - c) >= h ? 0 : r * sqrt(1 - pow((t - c) / h, 2));
function egg_r(t) = smax(ell(t, 0.30, 0.40, 0.37), ell(t, 0.74, 0.26, 0.30));
function egg_rs(t) = t <= 0 ? egg_r(0.001) : egg_r(t);
EGG_SPLIT = 0.53;
// mushroom: a bean of a body under a domed cap
function bean_r(t) = ell(t, 0.30, 0.40, 0.25);
CAP0 = 0.50;                         // the brim
function cap_top_r(t) = ell(t, CAP0, 0.50, 0.46);   // the dome over the brim

N = 48;
module revolve(f, t0, t1) rotate_extrude($fn = 96)
    polygon(concat([[0, t0]], [for (i = [0 : N]) let (t = t0 + (t1 - t0) * i / N) [f(t), t]], [[0, t1]]));

// ---- form 1 ----
module egg_half(h, top) scale(h) {
    if (top) revolve(function (t) egg_rs(t), EGG_SPLIT, 1);
    else revolve(function (t) egg_rs(t), 0, EGG_SPLIT);
}
function surf(h, t, dx) = -sqrt(max(pow(egg_r(t) * h, 2) - dx * dx, 0));
module ears(h) for (s = [-1, 1]) let (a = 34, tc = 0.74, rr = 0.30 * h, zc = tc * h)
    translate([0, 0, zc]) rotate([0, s * a, 0]) translate([0, 0, rr * 0.86]) rotate([0, 0, 0])
        hull() { scale([1, 0.6, 1]) cylinder(r = 0.11 * h, h = 0.01); translate([0, 0, 0.16 * h]) sphere(r = 0.025 * h); }
module eyes(h) for (s = [-1, 1]) let (t = 0.73, dx = s * 0.10 * h) translate([dx, surf(h, t, dx) + 0.01 * h, t * h]) scale([0.034, 0.03, 0.046] * h) sphere(1);
module nose(h) let (t = 0.68) translate([0, surf(h, t, 0) + 0.005 * h, t * h]) scale([0.024, 0.02, 0.016] * h) sphere(1);
module cheeks(h) for (s = [-1, 1]) let (t = 0.67, dx = s * 0.17 * h) translate([dx, surf(h, t, dx) + 0.012 * h, t * h]) scale([0.04, 0.02, 0.026] * h) sphere(1);
module scarf(h) let (t = EGG_SPLIT + 0.025) {
    translate([0, 0, t * h]) rotate_extrude($fn = 96) translate([egg_r(t) * h - 0.01 * h, 0]) scale([0.05, 0.045] * h) circle(1);
    translate([0.10 * h, surf(h, t - 0.09, 0.10 * h) - 0.012 * h, (t - 0.09) * h]) rotate([-8, 12, 0]) scale([0.045, 0.02, 0.10] * h) sphere(1);
}
module paws(h) for (s = [-1, 1]) let (t = 0.40, dx = s * 0.12 * h) translate([dx, surf(h, t, dx) + 0.005 * h, t * h]) scale([0.07, 0.05, 0.05] * h) sphere(1);

// ---- form 3 ----
module bean(h) scale(h) revolve(function (t) bean_r(t), 0, CAP0 + 0.02);
module cap(h) scale(h) {
    revolve(function (t) cap_top_r(t), CAP0, 1);
    // the gills: a cone from the brim in to the body, 50 deg, so it prints
    translate([0, 0, CAP0]) mirror([0, 0, 1]) cylinder(r1 = 0.46, r2 = 0.20, h = (0.46 - 0.20) * tan(40));
}
function bsurf(h, t, dx) = -sqrt(max(pow(bean_r(t) * h, 2) - dx * dx, 0));
module m_eyes(h) for (s = [-1, 1]) let (t = 0.30, dx = s * 0.085 * h) translate([dx, bsurf(h, t, dx) + 0.008 * h, t * h]) scale([0.028, 0.025, 0.04] * h) sphere(1);
module m_cheeks(h) for (s = [-1, 1]) let (t = 0.25, dx = s * 0.15 * h) translate([dx, bsurf(h, t, dx) + 0.01 * h, t * h]) scale([0.034, 0.02, 0.022] * h) sphere(1);
module m_arms(h) for (s = [-1, 1]) let (t = 0.17) translate([s * bean_r(t) * h * 0.95, 0, t * h]) scale([0.05, 0.045, 0.07] * h) sphere(1);
SPOTS = [[0, 0.80, 0.9], [60, 0.66, 0.8], [140, 0.72, 0.75], [210, 0.62, 0.7], [290, 0.74, 0.85], [100, 0.88, 0.6], [250, 0.88, 0.6], [330, 0.62, 0.6], [180, 0.86, 0.55]];
module spots(h) for (sp = SPOTS) let (a = sp[0], t = sp[1], s = sp[2], r = cap_top_r(t) * h)
    rotate([0, 0, a - 90]) translate([r - 0.012 * h, 0, t * h]) rotate([0, 90 - atan2((t - CAP0) * h, r) * 0.9, 0]) scale([0.07 * s, 0.07 * s, 0.03] * h) sphere(1);

// ---- the line-up ----
function xs(i) = i == 0 ? 0 : xs(i - 1) + HS[i - 1] * 0.42 + HS[i] * 0.42 + GAP;
module at(i, top = false) translate([xs(i), 0, (top && i == 0) ? LIFT : 0]) children();
module figure_part(i, what) let (h = HS[i]) {
    if (form == 1) {
        if (what == "body") { at(i) egg_half(h, false); at(i, true) egg_half(h, true); at(i, true) ears(h); }
        if (what == "trim") { at(i) paws(h); at(i, true) scarf(h); }
        if (what == "dark") at(i, true) { eyes(h); nose(h); }
        if (what == "pink") at(i, true) cheeks(h);
    } else {
        if (what == "body") { at(i) bean(h); at(i) m_arms(h); }
        if (what == "cap") at(i, true) cap(h);
        if (what == "trim") at(i, true) spots(h);
        if (what == "dark") at(i) m_eyes(h);
        if (what == "pink") at(i) m_cheeks(h);
    }
}
for (i = [0 : 4]) {
    if (part == str("body", i) || part == "all") figure_part(i, "body");
    if (part == str("cap", i) || part == "all") figure_part(i, "cap");
}
for (w = ["trim", "dark", "pink"]) if (part == w || part == "all") for (i = [0 : 4]) figure_part(i, w);
