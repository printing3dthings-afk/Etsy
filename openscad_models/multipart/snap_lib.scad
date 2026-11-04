// Split snap pins and their sockets (2026-11-04), first drawn for the gift box
// lantern v2 and shared from the Penny Spinner on. A pin stands on +z from
// z = 0; its socket opens at z = 0 and runs up +z. Mirror both to point down.
// Both print with their axis upright: the pin standing on its part, the
// socket from its mouth.
// A pin 3.4 across, split by a 1.0 slot that runs 3.0 down into what it stands
// on, so each prong is 1.2 thick (three beads) and flexes over about 5 mm. The
// barb stands 0.4 proud and squeezes 0.25 through the throat: 1.7% strain in
// PLA, a firm click. At 3.0 across the prongs were 1.0 and failed the wall
// floor, and the slicer dropped the sharp edges where the slot met the round
// (2026-11-04); the slot's ends now flare, a 0.4 chamfer on each prong's edge.
SP_D = 3.4; SP_SLIT = 1.0; SP_SLIT_IN = 3.0; SP_B = 0.4; SP_FL = 0.4;
module slit2d(len) let (w = SP_SLIT / 2, r = SP_D / 2) union() {
    translate([-w, -len / 2]) square([SP_SLIT, len]);
    for (s = [-1, 1]) polygon([[-w, s * (r - SP_FL - 0.3)], [w, s * (r - SP_FL - 0.3)],
                              [w + SP_FL + 0.4, s * (r + 0.1)], [w + SP_FL + 0.4, s * len / 2],
                              [-w - SP_FL - 0.4, s * len / 2], [-w - SP_FL - 0.4, s * (r + 0.1)]]);
}
// throat: the length of the narrow part of the socket the barb passes
module snap_pin(throat) let (r = SP_D / 2, c = throat + 0.1, f = SP_B / tan(37), top = c + f + 0.4 + 1.2)
    difference() {
        rotate_extrude($fn = 40) polygon([
            [0, -0.01], [r, -0.01], [r, c],      // the shaft
            [r + SP_B, c + f],                   // the barb's catch, 37 deg off upright
            [r + SP_B, c + f + 0.4],
            [r - 0.3, top],                      // the lead-in
            [0, top]]);
        translate([0, 0, -SP_SLIT_IN]) linear_extrude(top + SP_SLIT_IN + 1) slit2d(10);
    }
function snap_top(throat) = throat + 0.1 + SP_B / tan(37) + 1.6;
// the slot the pin's prongs flex into, cut into what the pin stands on
module snap_slit() translate([-SP_SLIT / 2, -SP_D / 2, -SP_SLIT_IN]) cube([SP_SLIT, SP_D, SP_SLIT_IN + 0.01]);
// The socket: a throat the barb squeezes through, a chamber it opens into,
// and a roof at 37 deg. Printed upright from its mouth, the chamber's floor
// faces up, so the catch is a real edge.
SK_T = 0.15;                // throat clearance round the shaft
module snap_socket(throat) let (rt = SP_D / 2 + SK_T, rc = SP_D / 2 + SP_B + 0.2, ch = 1.0)
    rotate_extrude($fn = 40) polygon([
        [0, -0.01], [rt + 0.3, -0.01], [rt, 0.4], [rt, throat],
        [rc, throat], [rc, throat + ch], [0, throat + ch + rc / tan(37)]]);
function socket_top(throat) = throat + 1.0 + (SP_D / 2 + SP_B + 0.2) / tan(37);
