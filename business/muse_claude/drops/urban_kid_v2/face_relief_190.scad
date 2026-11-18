// Urban Kid v2 face relief — Benson pass, 190 mm figure, head-local mm
// Grooves are NEGATIVE solids: difference() them from the head.
// Raises are POSITIVE solids: union() them. Origin: chin centre,
// face plane y=0, +x = figure's left, z up. Head 63.3 tall x 54 wide.
$fn = 48;

// lip_line_groove: width 1.4 mm, depth 1.0 mm
module lip_line_groove() {
  pts = [[-15.0, 19.2], [-8.0, 18.1], [0.0, 17.8], [8.0, 18.6], [15.0, 22.3]];
  for (i = [0 : len(pts) - 2]) hull() {
    translate([pts[i][0], 0, pts[i][1]]) sphere(d = 1.4);
    translate([pts[i+1][0], 0, pts[i+1][1]]) sphere(d = 1.4);
  }
}

// dimple_L: dia 3.2 mm, depth 1.3 mm
module dimple_L() { translate([16.8, 0, 23.2]) scale([1, 0.81, 1]) sphere(d = 3.2); }

// dimple_R: dia 2.6 mm, depth 0.9 mm
module dimple_R() { translate([-16.2, 0, 20.2]) scale([1, 0.69, 1]) sphere(d = 2.6); }

// smile_line_L: width 1.1 mm, depth 0.8 mm
module smile_line_L() {
  pts = [[16.8, 23.2], [19.5, 26.5], [20.5, 30.5]];
  for (i = [0 : len(pts) - 2]) hull() {
    translate([pts[i][0], 0, pts[i][1]]) sphere(d = 1.1);
    translate([pts[i+1][0], 0, pts[i+1][1]]) sphere(d = 1.1);
  }
}

// smile_line_R: width 1.1 mm, depth 0.7 mm
module smile_line_R() {
  pts = [[-16.2, 20.2], [-18.5, 23.0], [-19.3, 26.0]];
  for (i = [0 : len(pts) - 2]) hull() {
    translate([pts[i][0], 0, pts[i][1]]) sphere(d = 1.1);
    translate([pts[i+1][0], 0, pts[i+1][1]]) sphere(d = 1.1);
  }
}

// pupil_dish_L: dia 3.4 mm, depth 1.2 mm
module pupil_dish_L() { translate([11.2, 0, 39.5]) scale([1, 0.71, 1]) sphere(d = 3.4); }

// pupil_dish_R: dia 3.4 mm, depth 1.2 mm
module pupil_dish_R() { translate([-11.2, 0, 39.5]) scale([1, 0.71, 1]) sphere(d = 3.4); }

// upper_lid_line_L: width 1.3 mm, depth 0.9 mm
module upper_lid_line_L() {
  pts = [[7.5, 42.8], [11.0, 43.8], [15.0, 43.2], [18.5, 41.8]];
  for (i = [0 : len(pts) - 2]) hull() {
    translate([pts[i][0], 0, pts[i][1]]) sphere(d = 1.3);
    translate([pts[i+1][0], 0, pts[i+1][1]]) sphere(d = 1.3);
  }
}

// upper_lid_line_R: width 1.3 mm, depth 0.9 mm
module upper_lid_line_R() {
  pts = [[-18.5, 41.8], [-15.0, 43.2], [-11.0, 43.8], [-7.5, 42.8]];
  for (i = [0 : len(pts) - 2]) hull() {
    translate([pts[i][0], 0, pts[i][1]]) sphere(d = 1.3);
    translate([pts[i+1][0], 0, pts[i+1][1]]) sphere(d = 1.3);
  }
}

// Raises (brows, lid/cheek, lower lip) are specified in the
// printed table — apply as mesh_sculpt draw strokes with the
// listed diameters/heights; boolean spheres distort on a
// curved face and Claude's brush tools already do this better.