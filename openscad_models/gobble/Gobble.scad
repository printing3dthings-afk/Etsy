// OnBrandCraftz | Gobble Hungry Monster Desk Buddy | original prototype
// mm. Keep OBC.svg alongside. Print outputs are oriented; assembly is VIEW ONLY.
part="assembly"; // body, tongue, tray, eye, pupil, tooth, assembly
$fa=2; $fs=0.45;
back_y=55;
eye_x=51; eye_z=179;
phone_width=85; phone_thickness=14; phone_height=165; phone_tilt=15;
// Nominal phone local centre-bottom [0,-55,32], rotated back 15 degrees.
module rr(w,h,r){offset(r=r) square([w-2*r,h-2*r],center=true);}
module along_y(y0,y1){translate([0,y1,0]) rotate([90,0,0]) linear_extrude(y1-y0) children();}
module body_profile(){
 union(){
  hull(){for(s=[-1,1]){
   translate([s*44,125]) circle(r=39);
   translate([s*42,58]) circle(r=44);
  }translate([0,35]) circle(r=24);}
  for(s=[-1,1]) translate([s*eye_x,eye_z]) scale([25,31]) circle(r=1,$fn=128);
 }
}
module mouth_profile(){translate([0,88]) rr(120,116,22);}
module obc(width){rotate([0,0,180]) mirror([0,1,0]) resize([width,0],auto=true) import("OBC.svg",center=true);}
module mark(x,y,z,w){translate([x,y,z-0.5]) linear_extrude(1.2) obc(w);}
module foot(s){
 intersection(){
  along_y(-55,back_y) translate([s*50,12]) rr(58,24,9);
  translate([s*50,0,-1]) linear_extrude(27)
   polygon(concat([[-29,55],[29,55],[29,-34]],
    [for(a=[0:-5:-180]) [29*cos(a),-34+20*sin(a)]]));
 }
}
module body(){
 difference(){
  union(){along_y(0,back_y) body_profile();foot(-1);foot(1);}
  along_y(-2,back_y-3.2) mouth_profile();
  // Low rectangular tongue seat intersects the round mouth without cutting the base apart.
  translate([-56.5,-2,25.6]) cube([113,27,5.0]);
  // Eye sockets are 0.3 mm clearance per side and retain a 3.2 mm rear wall.
  for(s=[-1,1]) along_y(-2,2.4) translate([s*eye_x,eye_z]) scale([15.3,20.3]) circle(r=1,$fn=128);
  // Two shallow grooves suggest toes; they open toward the foot tip.
  for(s=[-1,1],dx=[-9,9]) translate([s*50+dx,-54.2,10]) scale([1,1.8,1]) sphere(r=2);
  // Hidden rear face, bed-facing in the body print pose. Keep the reversed mark orientation.
  translate([0,back_y,20]) rotate([90,0,0]) mark(0,0,0,26);
 }
}
module tongue_shape(){
 // One broad lower platform and two back supports, not a solid wedge filling the grin.
 union(){
  translate([0,-25,0]) linear_extrude(4) rr(112,100,13);
  // Front retaining lip is open in the centre for an attached charging cable.
  for(s=[-1,1]) translate([s*31,-69,3.5]) linear_extrude(8.5) rr(47,10,4);
  // Back-bearing slope follows the back of a 14 mm case tilted 15 degrees.
  for(s=[-1,1]) translate([s*28,0,0]) rotate([90,0,90]) linear_extrude(13,center=true)
   polygon([[-47.75,3.5],[20,3.5],[20,75],[-28.65,75]]);
 }
}
module tongue(){
 difference(){
  tongue_shape();
  translate([-7,-80,-1]) cube([14,39,15]);
  mark(0,-16,0,22);
 }
}
module tray(){
 difference(){
  linear_extrude(31) rr(108,52,8);
  translate([0,0,3]) linear_extrude(30) rr(102,46,5);
  mark(0,0,0,22);
 }
}
module eye(){
 difference(){
  union(){
   linear_extrude(1.8) scale([15,20]) circle(r=1,$fn=128);
   translate([0,0,1.8]) linear_extrude(1.2,scale=0.96) scale([15,20]) circle(r=1,$fn=128);
  }
  translate([2,-1,1.8]) cylinder(d=13.6,h=3);
 }
}
module pupil(){difference(){cylinder(d=13,h=1.8);translate([-2.3,2.3,-1]) cylinder(d=2.6,h=4);}}
module tooth(){
 // Print on its flat rear face, then glue onto the lower mouth corners clear of the phone.
 intersection(){scale([7,14,4]) sphere(r=1,$fn=64);translate([-10,-20,0]) cube([20,40,5]);}
}
module assembled(){
 color([.12,.42,.37]) body();
 color([.75,.25,.12]) translate([0,0,26]) tongue();
 color([.12,.42,.37]) translate([0,81.2,0]) tray();
 for(s=[-1,1]){
  color("ivory") translate([s*eye_x,2.1,eye_z]) rotate([90,0,0]) eye();
  color([.035,.04,.04]) translate([s*eye_x+2,.3,eye_z-1]) rotate([90,0,0]) pupil();
  color("ivory") translate([s*65,-0.15,44]) rotate([90,0,0]) tooth();
 }
}
if(part=="body") translate([0,0,back_y]) rotate([-90,0,0]) body();
else if(part=="tongue") tongue();
else if(part=="tray") tray();
else if(part=="eye") eye();
else if(part=="pupil") pupil();
else if(part=="tooth") tooth();
else if(part=="assembly") assembled();
