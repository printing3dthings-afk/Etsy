// OnBrandCraftz F1 Pebble Gecko / C1 Mushroom Pop -- prototype, mm
// Keep OBC.svg alongside. All tolerances require a physical coupon test.
part="gecko"; // gecko, gecko_coupon, mushroom_base, mushroom_cap, switch_coupon, stem_coupon
$fn=48;
segment_id=0;
gap=0.5; ball_r=5; socket_r=7.2; neck_r=2.2;
switch_hole=14.1; plate_t=1.5; stem_long=4.15; stem_short=1.35;
module obc(w){rotate([0,0,180]) mirror([0,1,0]) resize([w,0],auto=true) import("OBC.svg",center=true);}
module brand(w){translate([0,0,-.1]) linear_extrude(.8) obc(w);}
module ell(p,r){translate(p) scale(r) sphere(1);}
module floor_clip(){intersection(){children();translate([-100,-100,0]) cube([400,200,100]);}}
module ball(x){ell([x,0,4],[ball_r,ball_r,ball_r]);}
module neck(x,c){translate([x,0,4]) rotate([0,90,0]) cylinder(r=neck_r,h=c-x);}
module cavity(x){
 ell([x,0,4],[ball_r+gap,ball_r+gap,ball_r+gap]);
 translate([x,0,4]) rotate([0,90,0]) cylinder(r=3.4,h=12);
}
module socket(x){ell([x,0,4],[socket_r,socket_r,socket_r]);}
module feet(c,w){for(s=[-1,1]){
 hull(){ell([c,s*(w-2),3.5],[5,5,4]);ell([c-3,s*(w+7),2.7],[6,5,3.7]);}
 for(dx=[-4,0,4]) ell([c+dx-3,s*(w+10),2.3],[2.6,4,3.3]);
}}
function smile_pt(a)=let(y=8*sin(a),z=5+3*(1-cos(a))) [-3-22*sqrt(1-y*y/(19*19)-(z-6)*(z-6)/144)+.3,y,z];
module head(){difference(){floor_clip(){union(){
 ell([-3,0,6],[22,19,12]);socket(18);feet(8,14);
 for(s=[-1,1]) ell([-10,s*13,11],[6,6,6]);
 }}cavity(18);
 // Engraved eye outlines and smile allow a single-color print or paint fill.
 for(s=[-1,1]) translate([-13,s*13,15]) sphere(r=3);
 for(a=[-60:15:45]) hull(){translate(smile_pt(a)) sphere(r=.8,$fn=16);translate(smile_pt(a+15))sphere(r=.8,$fn=16);}
 translate([-3,0,0]) brand(17);
}}
module segment(i){c=34+26*i;j=c+10;w=13-i*1.15;
 difference(){floor_clip(){union(){
 ell([c,0,4],[8.5,w,8-i*.45]);ball(c-16);neck(c-16,c);
 if(i<5) socket(j);else hull(){ell([c,0,3],[6,w,6]);ell([c+16,0,1],[2.5,2.5,2.5]);}
 if(i==2) feet(c,w);
 }}if(i<5)cavity(j);
 }
}
module gecko(){head();for(i=[0:5])segment(i);}
module gecko_coupon(){difference(){floor_clip(){union(){ell([0,0,4],[7,9,7]);socket(10);}}cavity(10);}floor_clip(){union(){ball(10);neck(10,26);ell([26,0,3],[6,7,5]);}}}
module rounded_cyl(r,h,fillet){hull(){translate([0,0,fillet]) rotate_extrude() translate([r-fillet,0]) circle(fillet);translate([0,0,h-fillet]) rotate_extrude() translate([r-fillet,0]) circle(fillet);}}
// Open underside gives access to switch clips and electrical pins; no soldering.
module mushroom_base(){difference(){
 union(){cylinder(r=20,h=2);rounded_cyl(20,26,4);translate([0,0,22]) cylinder(r=17,h=4);}
 translate([0,0,-1]) cylinder(r=15.5,h=25.5);
 translate([-switch_hole/2,-switch_hole/2,24]) cube([switch_hole,switch_hole,5]);
 // Mark sits on a wider hidden annular foot surface.
 translate([0,-17.5,0]) brand(10);
}}
module stem_cut(z=0){translate([0,0,z]) linear_extrude(5.0) union(){square([stem_long,stem_short],center=true);square([stem_short,stem_long],center=true);}}
module mushroom_cap(){difference(){union(){
 // Flat underside and a smooth low dome; central mounting boss is integrated.
 intersection(){ell([0,0,0],[25,25,14],$fn=128);translate([-30,-30,0])cube([60,60,20]);}
 }stem_cut(-.1);
 // Recess clears the stationary base through the switch stroke; leave a central stem boss.
 difference(){translate([0,0,-.1])cylinder(r=20.6,h=6.1);translate([0,0,-1])cylinder(r=3.2,h=8);}
 // Shallow dots can be paint-filled, keeping tiny loose pieces out of the build.
 for(a=[20,140,260]) translate([14*cos(a),14*sin(a),11.7]) sphere(r=4.2);
 translate([0,0,13.8]) sphere(r=4);
}}
module switch_coupon(){difference(){translate([-12,-12,0])cube([24,24,plate_t]);translate([-switch_hole/2,-switch_hole/2,-1])cube([switch_hole,switch_hole,4]);}}
module stem_coupon(){difference(){cylinder(r=5,h=6);stem_cut(-.1);}}
if(part=="gecko")gecko();
else if(part=="gecko_coupon")gecko_coupon();
else if(part=="mushroom_base")translate([0,0,26])rotate([180,0,0])mushroom_base();
else if(part=="mushroom_cap")mushroom_cap();
else if(part=="switch_coupon")switch_coupon();
else if(part=="stem_coupon")stem_coupon();
else if(part=="gecko_head")head();
else if(part=="gecko_segment")segment(segment_id);
