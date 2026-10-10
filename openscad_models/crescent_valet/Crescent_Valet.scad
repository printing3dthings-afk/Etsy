// OnBrandCraftz | Crescent bedside valet | prototype 2 — engraved maker marks
// Original parametric design. Units: mm. No external SCAD libraries.
// Print base and tray independently, flat on their modeled z=0 surfaces.
// part: base / tray / assembly / fit_test. Print each main part on its own plate.
part = "assembly";
$fn = 96;
curve_samples = 32; // samples per cubic; 192 around the tray
base_rx = 105;
base_ry = 77;
base_h = 10;
tray_h = 18;
tray_wall = 2.8;
tray_floor = 3;
tray_clearance = 0.45; // per side, lift-out fit; verify with coupon
seat_depth = 2.4;
phone_x = 52;
phone_tilt = 15; // degrees from vertical
phone_seat_z = 28;
phone_support_h = 100;
phone_support_w = 74;
phone_back_y = -6;
cradle_front_y = -26;
cable_slot_w = 14;
cord_channel_w = 8;
// Keep OBC.svg beside this source. Approved Montserrat Black print vector.
// Recessed into the hidden underside; 0.7 mm deep, no raised geometry.
module brand_mark(x,y,width) {
 translate([x,y,-0.5]) linear_extrude(1.2)
  mirror([0,1,0]) resize([width,0],auto=true) import("OBC.svg",center=true);
}

assert(tray_wall>=2.4 && tray_floor>=2.4);
assert(tray_clearance>=0.2);
assert(phone_tilt<=25);
assert(base_rx*2<250 && base_ry*2<250);

function bez(a,b,c,d,t) = a*pow(1-t,3)+3*b*t*pow(1-t,2)+3*c*t*t*(1-t)+d*t*t*t;
curves = [
 [[22,-58],[-5,-76],[-68,-65],[-85,-40]],
 [[-85,-40],[-108,-8],[-91,44],[-57,60]],
 [[-57,60],[-32,71],[5,66],[16,54]],
 [[16,54],[25,46],[14,34],[0,26]],
 [[0,26],[-14,17],[-16,-5],[-4,-18]],
 [[-4,-18],[4,-29],[36,-43],[22,-58]]
];
// Reverse the clockwise Bezier outline to CCW for outward normal offsets.
raw = [for(c=curves) for(i=[0:curve_samples-1]) bez(c[0],c[1],c[2],c[3],i/curve_samples)];
outline = [for(i=[len(raw)-1:-1:0]) raw[i]];
function unit(v)=v/norm(v);
function outward(v)=[v.y,-v.x];
function shifted(p,i,d) = let(n=len(p),a=outward(unit(p[i]-p[(i+n-1)%n])),b=outward(unit(p[(i+1)%n]-p[i])),v=unit(a+b)) p[i]+v*d/(v*a);
function loop_at(p,d,z)=[for(i=[0:len(p)-1]) let(q=shifted(p,i,d)) [q.x,q.y,z]];
// Ring surface loft: explicit triangles preserve the concave crescent.
// Never hull the tray outline: a convex hull would erase its inner curve.
module loft(p,rings,cap_start=true,cap_end=true) {
 n=len(p);nr=len(rings);
 pts=[for(r=rings) each loop_at(p,r[0],r[1])];
 fs=concat(
 [for(k=[0:nr-2]) for(i=[0:n-1]) each
   [[k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n],
    [k*n+i,(k+1)*n+(i+1)%n,(k+1)*n+i]]],
 cap_start?[[for(i=[n-1:-1:0]) i]]:[],
 cap_end?[[for(i=[0:n-1]) (nr-1)*n+i]]:[]);
 polyhedron(pts,[for(f=fs) [for(i=[len(f)-1:-1:0]) f[i]]],convexity=12);
}
ellipse=[for(i=[0:191]) [base_rx*cos(i*360/192),base_ry*sin(i*360/192)]];
module base_blank() {
 // 0.4 mm bottom chamfer for first-layer clearance; rounded top perimeter.
 loft(ellipse,concat([[-0.4,0],[0,0.4],[0,base_h-2]],
   [for(a=[15:15:90]) [-2+2*cos(a),base_h-2+2*sin(a)]]));
}
module crescent_tray() {
 // Outer wall, rounded rim, inside wall, rounded floor transition.
 rings=concat([[-0.4,0],[0,0.4],[0,tray_h-1.2]],
 [for(a=[15:15:90]) [-1.2+1.2*cos(a),tray_h-1.2+1.2*sin(a)]],
 [[-tray_wall+1.2,tray_h]],
 [for(a=[15:15:90]) [-tray_wall+1.2-1.2*sin(a),tray_h-1.2+1.2*cos(a)]],
 [[-tray_wall,tray_floor+2]],
 [for(a=[15:15:90]) [-tray_wall-2+2*cos(a),tray_floor+2-2*sin(a)]]);
 difference() {
  loft(outline,rings);
  brand_mark(-60,0,24);
 }
}
module round_box(w,d,h,r=3) {
 linear_extrude(h) offset(r=r) square([w-2*r,d-2*r],center=true);
}
module phone_back() {
 // Rounded solid wedge. 15-degree front slope is self-supporting upright.
 top_y=phone_back_y+(phone_support_h-phone_seat_z)*tan(phone_tilt);
 translate([phone_x,0,0])
 minkowski() {
   rotate([90,0,90]) linear_extrude(phone_support_w-3,center=true)
    offset(r=1.5) offset(delta=-1.5)
     polygon([[phone_back_y+1.5,9.5],
       [phone_back_y+1.5,phone_seat_z],
       [top_y+1.5,phone_support_h-1.5],
       [top_y+8,phone_support_h-1.5],[37,9.5]]);
   sphere(r=1.5,$fn=24);
 }
}
module cradle() {
 // Wide front cradle with a central connector opening; no device-specific plug.
 translate([phone_x,-16,8]) round_box(phone_support_w,28,phone_seat_z-8,3);
 translate([phone_x,cradle_front_y,phone_seat_z-1])
  round_box(phone_support_w-4,6,9,2);
}
module cable_cuts() {
 // Open connector well; connector is connected manually before seating phone.
 translate([phone_x-cable_slot_w/2,-43,-1])
  cube([cable_slot_w,38,phone_seat_z+12]);
 // Underside cord route with a 60-degree roof (30 degrees from vertical), open at the back edge.
 translate([phone_x,82,0]) rotate([90,0,0]) linear_extrude(112)
  polygon([[-cord_channel_w/2,-1],[cord_channel_w/2,-1],
           [cord_channel_w/2,0.5],[0,7.5],[-cord_channel_w/2,0.5]]);
}
module base() {
 difference() {
  union(){base_blank();phone_back();cradle();}
  translate([0,0,base_h-seat_depth]) linear_extrude(tray_h+2)
   offset(delta=tray_clearance) polygon(outline);
  cable_cuts();
  brand_mark(-45,0,28);
 }
}
module fit_test() {
 // Two separate coupon pieces checking the 0.45 mm tray-fit spacing.
 difference(){
  translate([-19,0,0]) round_box(34,30,8,5);
  translate([-19,0,2]) linear_extrude(7) offset(r=3+tray_clearance)
   square([22-6,18-6],center=true);
  translate([-38,-3,2]) cube([10,6,7]);
 }
 translate([19,0,0]) round_box(22,18,5,3);
}
if(part=="base") base();
else if(part=="tray") crescent_tray();
else if(part=="fit_test") fit_test();
else {color("slategray") base();color("tan") translate([0,0,base_h-seat_depth]) crescent_tray();}
