union() {
	difference() {
		translate(v = [-5, -5, 0]) {
			cube(size = [142.6, 18.0, 4]);
		}
		translate(v = [-2, 3.0, -1]) {
			cylinder(h = 6, r = 3);
		}
	}
	linear_extrude(height = 6) {
		text(size = 12, text = "Frank AI Setup");
	}
}
