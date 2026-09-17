// OnBrandCraftz Soft Frame — original modular craft drawer, prototype 1.
// Units mm. Keep OBC.svg beside this file. No external SCAD libraries.
// Individual part outputs are PRINT ORIENTED. Assembly is for viewing only.
part="assembly"; // housing, drawer, divider_long, divider_cross, label, fit_test, assembly
$fa=2; $fs=0.35;
W=160; D=125; H=62; wall=2.8; radius=12;
slide_side_clearance=0.45; slide_lift_clearance=0.5;
plate=7; floor=2.8; body_wall=2.4;
cav_w=W-2*wall; cav_d=D-wall;
runner_h=2.2; runner_x=58;
floor_z=wall+runner_h; flange_top=floor_z+floor;
cap_proud=3; cap_z=flange_top+slide_lift_clearance;
body_w=cav_w-2*cap_proud-2*slide_side_clearance;
body_top=H-wall-6;
rear=cav_d-0.5;
inside_w=body_w-2*body_wall;
inside_d=rear-plate-2*body_wall;
divider_h=30; divider_t=2; divider_slot=2.6;
stack_x=54; tongue_w=3; tongue_h=1.4; groove_w=3.8; groove_d=1.8;
assert(wall+1.4-groove_d>=2.2); // include the actual internal backing pads
assert(slide_side_clearance>=0.3 && slide_lift_clearance>=0.3);

module rounded_rect(w,h,r){offset(r=r) square([w-2*r,h-2*r],center=true);}
module face_profile(){rounded_rect(W,H,radius);}
module cavity_profile(){offset(delta=-wall) face_profile();}
module drawer_profile(){offset(delta=-slide_side_clearance) cavity_profile();}
module drawer_envelope(){
 intersection(){
  drawer_profile();
  // 35-degree lower edge leaves margin below the slicer's 45-degree limit.
  polygon([[-73.2,floor_z-H/2],[73.2,floor_z-H/2],
   [W/2,floor_z-H/2+9.715],[W/2,H/2],[-W/2,H/2],[-W/2,floor_z-H/2+9.715]]);
 }
}
module depth(y0,y1){translate([0,y1,H/2]) rotate([90,0,0]) linear_extrude(y1-y0) children();}
module bottom_mark(x,y,z,w=24){
 translate([x,y,z-0.5]) linear_extrude(1.2)
 mirror([0,1,0]) resize([w,0],auto=true) import("OBC.svg",center=true);
}
module rails(){
 for(s=[-1,1]){
  translate([s*runner_x-2.5,0,wall-0.4]) cube([5,cav_d+0.2,runner_h+0.4]);
  translate([s*(cav_w/2-cap_proud/2+0.4)-(cap_proud+0.8)/2,plate+1,cap_z])
   cube([cap_proud+0.8,cav_d-plate-0.8,3.2]);
 }
}
// Rounded outside silhouette; constant-offset cavity preserves actual wall thickness.
module housing(){
 difference(){
  union(){
   difference(){depth(0,D) face_profile();depth(-1,cav_d) cavity_profile();}
   rails();
   // Backing under the top grooves maintains >2 mm solid material.
   for(s=[-1,1]) translate([s*stack_x-4,plate+1,H-wall-1.4]) cube([8,D-plate-1,1.8]);
   // Longitudinal locating tongues. Ends slope over 2 mm in the print direction.
   for(s=[-1,1]) hull(){
    translate([s*stack_x-tongue_w/2,11,-tongue_h]) cube([tongue_w,D-18,tongue_h+0.1]);
    translate([s*stack_x-tongue_w/2,9,-0.01]) cube([tongue_w,D-14,0.11]);
   }
  }
  for(s=[-1,1]) translate([s*stack_x,0,0]) rotate([90,0,90]) linear_extrude(groove_w,center=true)
   polygon([[8,H+1],[8,H],[10,H-groove_d],[D-6,H-groove_d],[D-4,H],[D-4,H+1]]);
  // Hidden rear mark becomes a bed-facing engraving in the print orientation.
  translate([0,D,H/2]) rotate([90,0,0]) bottom_mark(0,0,0,26);
 }
}
module pull_cut(){
 // Open scallop leaves finger access from the FRONT under another stacked module.
 depth(-1,plate+body_wall+0.3)
 polygon([[-40,H/2+1],[-40,28],[-34,17],[34,17],[40,28],[40,H/2+1]]);
}
module label_cut(){
 // 32 x 12 mm pocket, front window, top loading mouth; no adhesive required.
 translate([37,0.9,17]) cube([32,1.5,12]);
 translate([38,-0.1,18]) cube([30,1.2,10]);
 translate([53,0,0]) rotate([90,0,90]) linear_extrude(32,center=true)
  polygon([[-0.1,28],[2.4,28],[2.4,30],[-0.1,34]]);
}
module drawer(){
 difference(){
  union(){
   intersection(){depth(0,plate) drawer_envelope();translate([-W/2,-1,floor_z]) cube([W,D+2,H]);}
   intersection(){depth(plate-0.2,rear) drawer_envelope();translate([-W/2,0,floor_z]) cube([W,D,floor]);}
   translate([-body_w/2,plate,flange_top-0.1]) cube([body_w,rear-plate,body_top-flange_top+0.1]);
  }
  translate([-inside_w/2,plate+body_wall,flange_top]) cube([inside_w,inside_d,body_top]);
  pull_cut(); label_cut();
  bottom_mark(0,64,floor_z,26);
 }
}
// Half-lap pair prints flat, then slots together into a removable four-cell grid.
// Gap of 0.4 mm at each end; this is a loose insert, not a snap fit.
module divider(length,from_top=true){
 difference(){
  linear_extrude(divider_t) rounded_rect(length,divider_h,1.2);
  translate([-divider_slot/2,from_top?0:-divider_h,-1]) cube([divider_slot,divider_h,divider_t+2]);
  bottom_mark(length/2-18,0,0,12);
 }
}
module label(){linear_extrude(0.8) rounded_rect(31.2,11.2,0.7);}
module fit_test(){
 // Short representative captured slide: separate rail and flange sample.
 difference(){
  union(){cube([18,25,2.8]);translate([0,0,2.5]) cube([3,25,6.6]);translate([0,0,6.1]) cube([6,25,3]);}
 }
 translate([25,0,0]) union(){cube([14,25,2.8]);translate([0,0,2.7]) cube([8.5,25,4]);}
}
module installed_dividers(){
 translate([0,plate+body_wall+inside_d/2+divider_t/2,flange_top+divider_h/2])
  rotate([90,0,0]) divider(inside_w-0.8,true);
 translate([-divider_t/2,plate+body_wall+inside_d/2,flange_top+divider_h/2])
  rotate([90,0,90]) divider(inside_d-0.8,false);
}
module assembled(drawer_open=0){
 color("slategray") housing();
 translate([0,-drawer_open,0]){
  color("tan") drawer();color("dimgray") installed_dividers();
  color("ivory") translate([53,1.9,23]) rotate([90,0,0]) label();
 }
}
if(part=="housing") translate([0,0,D]) rotate([-90,0,0]) housing();
else if(part=="drawer") translate([0,0,-floor_z]) drawer();
else if(part=="divider_cross") divider(inside_w-0.8,true);
else if(part=="divider_long") divider(inside_d-0.8,false);
else if(part=="label") label();
else if(part=="fit_test") rotate([90,0,0]) fit_test();
else if(part=="assembly"){assembled(42);translate([0,0,H]) assembled(0);}
