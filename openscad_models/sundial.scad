include <BOSL2/std.scad>

latitude = 35;
plate_w = 248; plate_h = 50; plate_t = 6;
tube_r = 1.1;

function solar_altitude(lat, hour) = asin(cos(lat) * cos(15 * (hour - 12)));
function solar_azimuth(lat, hour) =
    let(H = 15 * (hour - 12), sin_az = -sin(H), cos_az = -sin(lat) * cos(H))
    atan2(sin_az, cos_az);
function sun_dir(lat, hour) =
    let(alt = solar_altitude(lat, hour), az = solar_azimuth(lat, hour))
    [cos(alt) * sin(az), cos(alt) * cos(az), sin(alt)];

module sun_tube(cx, cy, dir) {
    d = dir / norm(dir);
    t = 20;
    a = [cx, cy, -3];
    b = a + d * t;
    hull() {
        translate(a) sphere(r = tube_r, $fn = 16);
        translate(b) sphere(r = tube_r, $fn = 16);
    }
}

// hour 9 (9) -- alt=35.40 az=119.84
module hour_9_digits() {
    dir = sun_dir(latitude, 9);
    sun_tube(-105.200, -2.200, dir);
    sun_tube(-102.000, -2.200, dir);
    sun_tube(-98.800, -2.200, dir);
    sun_tube(-105.200, -5.400, dir);
    sun_tube(-98.800, -5.400, dir);
    sun_tube(-105.200, -8.600, dir);
    sun_tube(-102.000, -8.600, dir);
    sun_tube(-98.800, -8.600, dir);
    sun_tube(-98.800, -11.800, dir);
    sun_tube(-105.200, -15.000, dir);
    sun_tube(-102.000, -15.000, dir);
    sun_tube(-98.800, -15.000, dir);
}

// hour 10 (10) -- alt=45.19 az=134.81
module hour_10_digits() {
    dir = sun_dir(latitude, 10);
    sun_tube(-72.700, -2.200, dir);
    sun_tube(-75.900, -5.400, dir);
    sun_tube(-72.700, -5.400, dir);
    sun_tube(-72.700, -8.600, dir);
    sun_tube(-72.700, -11.800, dir);
    sun_tube(-75.900, -15.000, dir);
    sun_tube(-72.700, -15.000, dir);
    sun_tube(-69.500, -15.000, dir);
    sun_tube(-66.500, -2.200, dir);
    sun_tube(-63.300, -2.200, dir);
    sun_tube(-60.100, -2.200, dir);
    sun_tube(-66.500, -5.400, dir);
    sun_tube(-60.100, -5.400, dir);
    sun_tube(-66.500, -8.600, dir);
    sun_tube(-60.100, -8.600, dir);
    sun_tube(-66.500, -11.800, dir);
    sun_tube(-60.100, -11.800, dir);
    sun_tube(-66.500, -15.000, dir);
    sun_tube(-63.300, -15.000, dir);
    sun_tube(-60.100, -15.000, dir);
}

// hour 11 (11) -- alt=52.30 az=154.96
module hour_11_digits() {
    dir = sun_dir(latitude, 11);
    sun_tube(-38.700, -2.200, dir);
    sun_tube(-41.900, -5.400, dir);
    sun_tube(-38.700, -5.400, dir);
    sun_tube(-38.700, -8.600, dir);
    sun_tube(-38.700, -11.800, dir);
    sun_tube(-41.900, -15.000, dir);
    sun_tube(-38.700, -15.000, dir);
    sun_tube(-35.500, -15.000, dir);
    sun_tube(-29.300, -2.200, dir);
    sun_tube(-32.500, -5.400, dir);
    sun_tube(-29.300, -5.400, dir);
    sun_tube(-29.300, -8.600, dir);
    sun_tube(-29.300, -11.800, dir);
    sun_tube(-32.500, -15.000, dir);
    sun_tube(-29.300, -15.000, dir);
    sun_tube(-26.100, -15.000, dir);
}

// hour 12 (12) -- alt=55.00 az=180.00
module hour_12_digits() {
    dir = sun_dir(latitude, 12);
    sun_tube(-4.700, -2.200, dir);
    sun_tube(-7.900, -5.400, dir);
    sun_tube(-4.700, -5.400, dir);
    sun_tube(-4.700, -8.600, dir);
    sun_tube(-4.700, -11.800, dir);
    sun_tube(-7.900, -15.000, dir);
    sun_tube(-4.700, -15.000, dir);
    sun_tube(-1.500, -15.000, dir);
    sun_tube(1.500, -2.200, dir);
    sun_tube(4.700, -2.200, dir);
    sun_tube(7.900, -2.200, dir);
    sun_tube(7.900, -5.400, dir);
    sun_tube(1.500, -8.600, dir);
    sun_tube(4.700, -8.600, dir);
    sun_tube(7.900, -8.600, dir);
    sun_tube(1.500, -11.800, dir);
    sun_tube(1.500, -15.000, dir);
    sun_tube(4.700, -15.000, dir);
    sun_tube(7.900, -15.000, dir);
}

// hour 13 (1) -- alt=52.30 az=205.04
module hour_13_digits() {
    dir = sun_dir(latitude, 13);
    sun_tube(34.000, -2.200, dir);
    sun_tube(30.800, -5.400, dir);
    sun_tube(34.000, -5.400, dir);
    sun_tube(34.000, -8.600, dir);
    sun_tube(34.000, -11.800, dir);
    sun_tube(30.800, -15.000, dir);
    sun_tube(34.000, -15.000, dir);
    sun_tube(37.200, -15.000, dir);
}

// hour 14 (2) -- alt=45.19 az=225.19
module hour_14_digits() {
    dir = sun_dir(latitude, 14);
    sun_tube(64.800, -2.200, dir);
    sun_tube(68.000, -2.200, dir);
    sun_tube(71.200, -2.200, dir);
    sun_tube(71.200, -5.400, dir);
    sun_tube(64.800, -8.600, dir);
    sun_tube(68.000, -8.600, dir);
    sun_tube(71.200, -8.600, dir);
    sun_tube(64.800, -11.800, dir);
    sun_tube(64.800, -15.000, dir);
    sun_tube(68.000, -15.000, dir);
    sun_tube(71.200, -15.000, dir);
}

// hour 15 (3) -- alt=35.40 az=240.16
module hour_15_digits() {
    dir = sun_dir(latitude, 15);
    sun_tube(98.800, -2.200, dir);
    sun_tube(102.000, -2.200, dir);
    sun_tube(105.200, -2.200, dir);
    sun_tube(105.200, -5.400, dir);
    sun_tube(98.800, -8.600, dir);
    sun_tube(102.000, -8.600, dir);
    sun_tube(105.200, -8.600, dir);
    sun_tube(105.200, -11.800, dir);
    sun_tube(98.800, -15.000, dir);
    sun_tube(102.000, -15.000, dir);
    sun_tube(105.200, -15.000, dir);
}

module all_hour_tubes() {
    hour_9_digits();
    hour_10_digits();
    hour_11_digits();
    hour_12_digits();
    hour_13_digits();
    hour_14_digits();
    hour_15_digits();
}

// size fitted to the plate per the 3d-print-design skill's standing rule --
// size=5 measured a real 212.56mm wide on this 248mm plate (85.7% of its
// length), confirmed too large. Re-measure after any further change
// rather than trusting a linear projection from one data point (see the
// cable clip's own mark-sizing fix for why: a single measurement can be
// an artifact of how it was filtered, not the true font scaling).
module brand_mark() {
    translate([0, -20.0, -3.5])
        linear_extrude(height = 1.2)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = 2.4, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

color([0.85, 0.82, 0.78])
difference() {
    cuboid([plate_w, plate_h, plate_t], rounding=4, edges="Z", anchor=CENTER);
    all_hour_tubes();
    brand_mark();
}