// Glow Headphone Stand V2 — OnBrandCraftz
// Functional redesign of glow_headphone_stand.scad.
// The original file remains unchanged.
//
// Improvements:
//   * extended headphone arm with downward-facing LED mount
//   * shallow curved headband saddle and front retaining lip
//   * base/riser/short under-arm diffuser, clear of the LED opening
//     (downlight is primary; diffuser brightness requires physical testing)
//   * removable snap-in LED puck retainer
//   * accessory tray, cable-wrap posts, rubber-foot pockets
//   * optional weighted-base pocket with removable cover
//
// Hardware target: Bambu Lab LED Lamp Kit-001, puck D59 x H18 mm.
// Select one part for export: "shell", "diffuser", "weight_cover",
// "puck_retainer", "all", or "assembled".

$fn = 64;
part = "all";

// ---------- fit controls ----------
puck_d = 59;
puck_h = 18;
fit_clearance = 0.30;       // per side for diffuser parts
press_clearance = 0.20;     // per side for snap/press-fit parts

// ---------- main proportions ----------
ch_w = 68;
ch_t = 68;
corner_r = 8;
base_h = 14;
base_len = 135;             // longer than V1 for tray room and stability
base_w = 76;
total_h = 226;
arm_z0 = total_h - ch_t;
riser_h = arm_z0 - base_h;
back_x = 15;
arm_total_len = 145;        // +30 mm reach; puck clears the upright
riser_front_x = back_x + ch_t;
arm_tip_x = back_x + arm_total_len;

// ---------- light path ----------
window_rim = 5;
window_w = ch_w - 2 * window_rim;
window_recess_d = 8;
base_recess_d = 6;
upper_recess_d = 6;
puck_hole_d = puck_d + 2;
puck_center_x = riser_front_x + 40;  // 123 mm, above the front of the base
puck_pocket_depth = puck_h + 9;      // 18 mm puck plus cable access headroom
upper_window_end_x = riser_front_x + 6;
retainer_flange_t = 2.4;
retainer_z = arm_z0 - retainer_flange_t;

assert(puck_center_x - (ch_w-1)/2 > riser_front_x,
       "LED retainer must clear the upright");
assert(arm_tip_x - (puck_center_x+puck_hole_d/2) >= 5,
       "Keep at least 5 mm at the closed front end");
assert(puck_center_x < base_len, "LED center must remain over the base");
assert(upper_window_end_x < puck_center_x-(ch_w-1)/2,
       "Diffuser must not obstruct the retainer");

// ---------- cable path ----------
cable_ch_d = 13;
cable_bore_x = back_x + 20;
cable_groove_w = 13;
cable_groove_d = 4.2;

// ---------- utility features ----------
tray_x0 = 94;
tray_x1 = 126;
tray_w = 48;
tray_d = 3.2;

weight_x0 = 22;
weight_x1 = 84;
weight_w = 50;
weight_depth = 6.5;
cover_lip = 1.2;

// Rounded rectangle extruded in Z. Keeps V2 standalone (no BOSL2 needed).
module rounded_box_z(size=[10,10,10], r=2) {
    x = size[0]; y = size[1]; z = size[2];
    hull()
        for (sx=[-1,1], sy=[-1,1])
            translate([sx*(x/2-r), sy*(y/2-r), 0])
                cylinder(r=r, h=z);
}

module base_solid() {
    translate([base_len/2, 0, 0])
        rounded_box_z([base_len, base_w, base_h], 6);
}

module riser_solid() {
    // 1 mm overlap into the base avoids touching-only geometry.
    translate([back_x + ch_t/2, 0, base_h-1])
        rounded_box_z([ch_t, ch_w, riser_h+1], corner_r);
}

module elbow_solid() {
    mid_x = back_x + ch_t/2;
    mid_z = arm_z0 + ch_t/2;
    module mid_slab() {
        translate([mid_x, 0, mid_z])
            rotate([0,45,0]) cube([ch_t, ch_w, 0.3], center=true);
    }
    hull() {
        translate([back_x + ch_t/2, 0, arm_z0])
            cube([ch_t, ch_w, 0.3], center=true);
        mid_slab();
    }
    hull() {
        mid_slab();
        translate([back_x, 0, arm_z0 + ch_t/2])
            cube([0.3, ch_w, ch_t], center=true);
    }
}

module arm_solid() {
    translate([back_x, -ch_w/2, arm_z0])
        cube([arm_total_len, ch_w, ch_t]);
}

module saddle_and_lip() {
    saddle_x0 = riser_front_x + 2;
    saddle_x1 = arm_tip_x - 3;
    saddle_len = saddle_x1 - saddle_x0;
    saddle_cx = (saddle_x0 + saddle_x1)/2;

    // The large transverse cylinder removes a shallow longitudinal arc,
    // spreading headband load while raised ends resist sliding.
    difference() {
        translate([saddle_cx, 0, total_h-1])
            rounded_box_z([saddle_len, ch_w-4, 9], 5);
        translate([saddle_cx, -(ch_w+2)/2, total_h+62])
            rotate([-90,0,0]) cylinder(r=61, h=ch_w+2);
    }

    // 7 mm front stop measured from the saddle's low contact surface.
    translate([arm_tip_x-3.5, 0, total_h-1])
        rounded_box_z([7, ch_w-4, 10], 3);
}

module cable_wrap_posts() {
    // Two vertical posts allow a wired-headphone cable to wrap in a
    // compact figure-eight without introducing support-heavy geometry.
    for (x=[108,124]) {
        translate([x, -base_w/2+7, base_h-1]) cylinder(d=8, h=13);
        translate([x, -base_w/2+7, base_h+8.5]) cylinder(d=12, h=3.5);
    }
}

module puck_downward_pocket() {
    // Blind cylindrical pocket opens only on the underside (axis Z).
    // The front face stays closed. Insert the puck from below, with its
    // emitting face toward -Z, then install the removable retaining ring.
    translate([puck_center_x, 0, arm_z0-1])
        cylinder(d=puck_hole_d, h=puck_pocket_depth+1);
    // Mating groove for the retaining collar's flexible bead.
    translate([puck_center_x, 0, retainer_z+7.2])
        cylinder(d=puck_hole_d+0.5, h=1.4);
}

module riser_window_cut() {
    translate([riser_front_x-window_recess_d, -window_w/2, base_h-1])
        cube([window_recess_d+1, window_w, riser_h+2]);
}

module base_window_cut() {
    translate([back_x, -window_w/2, base_h-base_recess_d])
        cube([base_len-back_x+1, window_w, base_recess_d+1]);
}

module upper_window_cut() {
    // Diffuser turns the inside corner, stopping before the LED retaining
    // ring so neither insert nor upright blocks the downward light.
    translate([riser_front_x-window_recess_d,
               -window_w/2,
               arm_z0-1])
        cube([upper_window_end_x-(riser_front_x-window_recess_d),
              window_w,
              upper_recess_d+1]);
}

module light_duct() {
    // Keep the original internal transfer space behind the diffuser.
    // End below the top skin; avoid the previous open slot on the top.
    translate([riser_front_x-window_recess_d, -14, arm_z0-1])
        cube([window_recess_d, 28, ch_t-7]);
    translate([back_x+4, -14, arm_z0+upper_recess_d-0.5])
        cube([upper_window_end_x-(back_x+4), 28, 42]);
}

module cable_bore(z0, z1) {
    translate([cable_bore_x, 0, z0])
        cylinder(d=cable_ch_d, h=z1-z0, $fn=40);
}

module cable_route() {
    cable_bore(-1, arm_z0+28);
    // 13 mm horizontal feed connects the spine to the pocket. Cable is
    // routed before inserting the puck; the front wall is never pierced.
    translate([cable_bore_x, 0, arm_z0+puck_h+2])
        rotate([0,90,0]) cylinder(d=cable_ch_d,
                                  h=puck_center_x-cable_bore_x+1);
    groove_x0 = cable_bore_x-cable_ch_d/2-1;
    translate([groove_x0, -cable_groove_w/2, -1])
        cube([base_len-groove_x0+1, cable_groove_w, cable_groove_d+1]);
}

module accessory_tray_cut() {
    translate([(tray_x0+tray_x1)/2, 0, base_h-tray_d])
        rounded_box_z([tray_x1-tray_x0, tray_w, tray_d+1], 6);
}

module weight_pocket_cut() {
    // Main cavity accepts stacked steel washers or a flat steel plate.
    translate([(weight_x0+weight_x1)/2, 0, -0.5])
        rounded_box_z([weight_x1-weight_x0, weight_w, weight_depth+0.5], 5);

    // Shallow perimeter ledge receives the removable cover.
    translate([(weight_x0+weight_x1)/2, 0, -0.5])
        rounded_box_z([weight_x1-weight_x0+2*cover_lip,
                       weight_w+2*cover_lip, 2.0], 5.5);
}

module foot_pockets() {
    for (x=[12,base_len-12], y=[-28,28])
        translate([x,y,-0.5]) cylinder(d=10, h=2.7);
}

module brand_mark() {
    // Approved print vector, underside only; clear of feet, weight pocket and cable.
    // Keep OBC.svg next to this SCAD. Engrave 0.7 mm; no raised branding.
    translate([107, -15, -0.5])
            linear_extrude(height=1.2)
                mirror([0,1,0]) import("OBC.svg", center=true);
}

module glow_stand_v2_shell() {
    difference() {
        union() {
            base_solid();
            riser_solid();
            elbow_solid();
            arm_solid();
            saddle_and_lip();
            cable_wrap_posts();
        }
        riser_window_cut();
        base_window_cut();
        upper_window_cut();
        light_duct();
        puck_downward_pocket();
        cable_route();
        accessory_tray_cut();
        weight_pocket_cut();
        foot_pockets();
        brand_mark();
    }
}

module glow_stand_v2_diffuser() {
    iw = window_w - 2*fit_clearance;
    it = window_recess_d - fit_clearance;
    bt = base_recess_d - fit_clearance;
    ut = upper_recess_d - fit_clearance;

    difference() {
        union() {
            // Base insert.
            translate([(back_x+base_len-fit_clearance)/2, 0,
                       base_h-bt])
                rounded_box_z([base_len-back_x-fit_clearance,
                               iw, bt], 2);

            // Riser insert, overlapping base and upper pieces.
            translate([riser_front_x-it, -iw/2, base_h-1+fit_clearance])
                cube([it, iw, riser_h+2-2*fit_clearance]);

            // Under-arm insert.
            translate([riser_front_x-window_recess_d+fit_clearance,
                       -iw/2, arm_z0+fit_clearance])
                cube([upper_window_end_x-
                      (riser_front_x-window_recess_d)-2*fit_clearance,
                      iw, ut]);
        }
        cable_bore(base_h-base_recess_d-1, base_h+2);
        accessory_tray_cut();
    }
}

module weight_cover() {
    cover_x = weight_x1-weight_x0 + 2*cover_lip - 2*press_clearance;
    cover_y = weight_w + 2*cover_lip - 2*press_clearance;
    rounded_box_z([cover_x, cover_y, 1.6], 5.2);
    // Finger tab for tool-free removal.
    translate([cover_x/2-2, 0, 0]) cylinder(d=8, h=1.6);
}

module puck_retainer() {
    // Print flange flat; the collar enters upward into the underside pocket.
    // Collar bore clears the 59 mm puck; the smaller flange opening holds
    // its rim. PETG fit-test required before relying on the snap retention.
    collar_od = puck_hole_d - 2*press_clearance;
    inner_d = puck_d - 4;
    collar_inner_d = puck_d + 0.6;
    difference() {
        union() {
            difference() {
                cylinder(d=ch_w-1, h=2.4);
                translate([0,0,-1]) cylinder(d=inner_d, h=4.4);
            }
            difference() {
            translate([0,0,2.2]) cylinder(d=collar_od, h=6.2);
                translate([0,0,1.4]) cylinder(d=collar_inner_d, h=8);
            }
            difference() {
                translate([0,0,7.4]) cylinder(d=collar_od+0.7, h=1.0);
                translate([0,0,7]) cylinder(d=collar_inner_d, h=2);
            }
        }
        for (a=[0,120,240])
            rotate([0,0,a]) translate([inner_d/2-1,-0.7,2.2])
                cube([(collar_od-inner_d)/2+3,1.4,7]);
    }
}

module assembled() {
    color("dimgray") glow_stand_v2_shell();
    color([0.92,0.93,0.85,0.75]) glow_stand_v2_diffuser();
    color("dimgray") translate([puck_center_x,0,retainer_z]) puck_retainer();
    // Visual-only nominal hardware envelope, never included in exports.
    if ($preview) color("ivory")
        translate([puck_center_x,0,arm_z0+fit_clearance])
            cylinder(d=puck_d,h=puck_h);
}

if (part == "shell") glow_stand_v2_shell();
else if (part == "diffuser") glow_stand_v2_diffuser();
else if (part == "weight_cover") weight_cover();
else if (part == "puck_retainer") puck_retainer();
else if (part == "assembled") assembled();
else {
    translate([0,-105,0]) glow_stand_v2_shell();
    translate([0,105,0]) glow_stand_v2_diffuser();
    translate([220,-28,0]) weight_cover();
    translate([220,45,0]) puck_retainer();
}
