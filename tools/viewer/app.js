/* Virtual P1S Chamber -- replays real sliced G-code.
   Data comes from tools/gcode_viewer_data.py; geometry and playback are here. */
(function () {
'use strict';

// \u2500\u2500 palette \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
// Index order must match TYPES in tools/gcode_viewer_data.py.
var TYPE_COLOR = ['#ff7a45','#ffc04d','#4fd2ff','#6a7285','#c9d64f','#9be36a',
                  '#3affc8','#7b5cd6','#a98cf0','#5a6070','#d8d8d8','#d8d8d8',
                  '#b08968'];
var N_TYPE = TYPE_COLOR.length;

// One palette for both the spools in the AMS and the filament colour mode, so
// the bead on the plate is the colour of the spool it came off. Illustrative,
// not read from any machine -- the printer panel says so.
var FILAMENT = ['#d9dbe0','#24272d','#8d939d','#c08a5a','#e0553d',
                '#6fa8dc','#8bc34a','#f2c14e'];
var MAX_FILAMENT = FILAMENT.length;
var TYPE_HELP = {
  'External perimeter':'The outermost wall loop. The only extrusion a customer ever sees, and the one worth slowing down for.',
  'Perimeter':'Inner wall loops. Strength and a backing for the external wall.',
  'Overhang perimeter':'A wall printed out over air. The slicer slows it and cools it harder; past 45 degrees it wants support instead.',
  'Internal infill':'The sparse lattice inside. 15% grid here \u2014 invisible, and most of what you can cut to save time.',
  'Solid infill':'Fully filled layers directly under or over a surface, so the sparse infill has something to close against.',
  'Top solid infill':'The last visible pass across a top face. Ironing, if enabled, runs over this.',
  'Bridge infill':'Extruded across a gap with nothing underneath, stretched between two anchors and fan-cooled hard.',
  'Support material':'Temporary scaffolding. Printed, then snapped off and binned \u2014 every move here is filament and time you do not sell.',
  'Support material interface':'The denser layer between support and part. Makes supports release cleanly instead of scarring the surface.',
  'Skirt/Brim':'The loop laid down before the part. Primes the nozzle and proves the first layer before anything that matters begins.',
  'Custom':'Start/end G-code the profile injects, not part geometry.',
  'Other':'An untagged move.',
  'Wipe tower':'The purge block. On every filament change the nozzle wipes the old colour out into this tower \u2014 it is thrown away, and on a multi-colour print it is most of the filament you buy.'
};

// \u2500\u2500 printers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
// Only profiles with a documented build volume are listed. "Custom" exists so a
// machine can be dialled in without editing this file; nothing here is guessed.
var PRINTERS = {
  p1s: {label:'Bambu Lab P1S', bed:[256,256,256], enclosed:true, nozzle:0.4, hingeLeft:true,
        motion:'CoreXY', chamber:'Passive, ~40 \u00b0C', plate:'Textured PEI',
        // Standard 4-slot AMS, the one Scott owns. 368 x 283 x 224 mm, 2.5 kg,
        // from Bambu Lab's own "AMS Tech Specs" table (us.store.bambulab.com,
        // checked 2026-09-16). Not the AMS 2 Pro (372 x 280 x 226) and not the
        // AMS HT (114 x 280 x 245) -- three different boxes, easy to conflate.
        ams: {slots: 4, w: 368, d: 283, h: 224, kg: 2.5},
        note:'The machine every job on this page was sliced for.'},
  // Open frame, bed-slinger, no heated chamber (bed tops out at 80 \u00b0C), real
  // footprint 544 x 529 x 505 mm. Verified 2026-09-17. Everything drawn for
  // this machine comes from that line and nothing else -- see buildOpenFrame.
  a2l: {label:'Bambu Lab A2L', bed:[330,320,325], enclosed:false, nozzle:0.4,
        motion:'Bedslinger', chamber:'None (open frame)', plate:'\u2014',
        bedslinger:true, footprint:[544,529,505],
        note:'Open frame, bed-slinger, no enclosure. Only its build volume, footprint and motion are modelled \u2014 and the toolpath was still sliced for the P1S.'},
  custom:{label:'Custom', bed:[256,256,256], enclosed:true, nozzle:0.4,
        motion:'\u2014', chamber:'\u2014', plate:'\u2014',
        note:'Enter a build volume to redraw the chamber. This is the hook for the rest of the market \u2014 it changes what is drawn, not how the file was sliced.'}
};

// Starting points only. Scott's own tuned profiles override every one of these.
var MATERIALS = [
  {n:'PLA', rho:1.24,     noz:'190\u2013230', bed:'35\u201360',  dry:'45 \u00b0C / 6\u20138 h',  plate:'Smooth PEI', use:'Decorative, sharpest detail, lowest failure rate'},
  {n:'Silk PLA', rho:1.24, noz:'200\u2013230', bed:'35\u201360',  dry:'45 \u00b0C / 6\u20138 h',  plate:'Smooth PEI', use:'Premium metallic finish, no post-processing'},
  {n:'PETG', rho:1.27,    noz:'230\u2013260', bed:'70\u201390',  dry:'65 \u00b0C / 6\u20138 h',  plate:'Textured PEI', use:'Functional, moisture and heat resistant'},
  {n:'TPU', rho:1.21,     noz:'200\u2013240', bed:'30\u201350',  dry:'\u2014',              plate:'Textured PEI', use:'Flexible \u2014 koozies, grips, gaskets'},
  {n:'ABS', rho:1.04,     noz:'240\u2013270', bed:'90\u2013100', dry:'60 \u00b0C / 4\u20136 h',  plate:'Textured PEI', use:'Heat resistant; needs the enclosure'},
  {n:'ASA', rho:1.07,     noz:'240\u2013280', bed:'90\u2013100', dry:'60 \u00b0C / 4\u20136 h',  plate:'Textured PEI', use:'Outdoor, UV stable; needs the enclosure'},
  {n:'PA / PC', rho:1.17, noz:'270\u2013300', bed:'90\u2013100', dry:'80 \u00b0C / 12+ h',  plate:'Textured PEI', use:'Engineering parts; wet filament ruins these'}
];

// \u2500\u2500 dom \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var $ = function (id) { return document.getElementById(id); };
var stage = $('stage'), loading = $('loading');

// \u2500\u2500 three.js scene \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var renderer, scene, camera, chamber, plate, grid, nozzle, gantry;
var bedGroup, shadowPlane, glowSprite, headScale = 1;
var doorGroup, extPanels = [], machineBounds = null;
var amsGroup, yRails, chamberLamp;
var doorOpen = false, doorAngle = 0, doorTarget = 0;
var viewMode = 'machine';   // 'machine' = solid exterior, 'chamber' = cutaway
var jobMesh = null, ghostMesh = null, jobGeom = null;
// `cam` is the TARGET the whole page writes to; `view` is what actually gets
// rendered, easing toward it every frame. Two objects rather than one because
// every existing caller -- frameJob, setDoor, the view buttons, the orbit
// handler -- already sets cam directly, and damping them all at once is a
// property of the renderer, not of any one of them.
var cam = {theta: -0.72, phi: 1.06, r: 430, tx: 0, ty: 0, tz: 90};
var view = {theta: -0.72, phi: 1.06, r: 430, tx: 0, ty: 0, tz: 90};
var spin = {theta: 0, phi: 0};
var moveUntil = 0, lowRes = false, basePixelRatio = 1;

function initScene() {
  renderer = new THREE.WebGLRenderer({antialias:true, powerPreference:'high-performance'});
  basePixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(basePixelRatio);
  renderer.setClearColor(0x07080a, 1);
  stage.appendChild(renderer.domElement);

  // Deterministic render stats and named scene objects for the test harness.
  // Everything else stays inside the closure.
  window.__R = renderer;
  scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x07080a, 950, 2200);
  camera = new THREE.PerspectiveCamera(38, 1, 1, 4000);
  camera.up.set(0, 0, 1);
  scene.add(new THREE.AmbientLight(0xffffff, 0.46));
  var key = new THREE.DirectionalLight(0xfff0dd, 0.85);
  key.position.set(-260, -420, 520);
  scene.add(key);
  var rim = new THREE.DirectionalLight(0x8fb4ff, 0.32);
  rim.position.set(430, 300, 140);
  scene.add(rim);

  // buildChamber owns the toolhead now -- it has to, because which head gets
  // built depends on which machine is selected.
  buildChamber(PRINTERS.p1s.bed);

  window.__VP = {scene: scene, camera: camera, cam: cam, view: view, spin: spin,
                 basePixelRatio: function () { return basePixelRatio; }};
  onResize();
  window.addEventListener('resize', onResize);
  attachOrbit(renderer.domElement);
  renderer.setAnimationLoop(tick);
}

// ── the machine ────────────────────────────────────────────────────────────
// Real P1S outside dimensions, 389 x 389 x 458 mm, around a 256mm cube of
// build volume (bambulab.com / us.store.bambulab.com, checked 2026-09-16).
// The nozzle plane is world z=0; the bed hangs below it and travels down.
// Deliberately unbranded: the proportions are the machine's, the logo is not
// mine to reproduce.
var EXT = {w: 389, d: 389, h: 458, wall: 6};

function buildChamber(bed) {
  [chamber, plate, grid, gantry, bedGroup, doorGroup, amsGroup, yRails].forEach(function (o) {
    if (o) { scene.remove(o); }
  });
  doorGroup = null;
  // Only the P1S is drawn as itself. Every other profile gets an honest
  // envelope instead -- build volume, footprint, bed, gantry, correct
  // kinematics, nothing invented. Before this, selecting the A2L drew a full
  // enclosed case with a smoked glass door while the panel two inches to the
  // right of it read "Enclosed: No / Chamber: None (open frame)". A viewer
  // whose whole job is teaching how a machine works cannot contradict its own
  // caption, and detailing a second machine is a research job per machine, not
  // a reskin of this one.
  var detailed = printerId === 'p1s';
  var X = bed[0], Y = bed[1], Z = bed[2];
  var ox = X / 2, oy = Y / 2;
  // Vertical layout follows the kinematics, because the two machines are
  // upside down relative to each other. Descending bed: the plate starts at
  // z=0 and travels down to -Z, so the case has to reach that far below.
  // Bed-slinger: the plate never moves in Z, so the machine stands UP from
  // just under it and the gantry is what climbs.
  var slinger = !!PRINTERS[printerId].bedslinger;
  var fp = PRINTERS[printerId].footprint;
  var zBot = slinger ? -72 : -(Z + 44);
  var zTop = slinger ? zBot + (fp ? fp[2] : Z + 200)
                     : zBot + Math.max(EXT.h, Z + 200);
  var x0 = ox - EXT.w / 2, x1 = ox + EXT.w / 2;
  var y0 = oy - EXT.d / 2, y1 = oy + EXT.d / 2;
  var t = EXT.wall;

  chamber = new THREE.Group();
  extPanels = [];

  function slab(w, d, h, color, x, y, z, normal) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(w, d, h),
      new THREE.MeshLambertMaterial({color: color}));
    m.position.set(x, y, z);
    chamber.add(m);
    if (normal) { extPanels.push({mesh: m, n: normal}); }
    return m;
  }

  if (!detailed) {
    buildOpenFrame(PRINTERS[printerId], X, Y, Z, ox, oy, zBot, slinger);
    scene.add(chamber);
    buildBed(X, Y, ox, oy);
    buildGantry(Math.max(X + 90, 260), ox, oy);
    buildInterior(X, Y, ox, oy, zBot, zTop, x0, x1, y0, y1, t, false);
    rebuildToolhead(false);
    machineBounds = {zBot: zBot, zTop: zTop, ox: ox, oy: oy, zOuter: zTop};
    cam.tx = ox; cam.ty = oy;
    cam.tz = (machineBounds.zBot + machineBounds.zOuter) / 2;
    cam.r = machineRadius();
    restoreMotionVisibility();
    syncDoorControl();
    return;
  }

  var BODY = 0x26282e, TRIM = 0x171a1f;
  var cz = (zBot + zTop) / 2, ch = zTop - zBot;

  slab(t, EXT.d, ch, BODY, x0 + t / 2, oy, cz, new THREE.Vector3(-1, 0, 0));
  slab(t, EXT.d, ch, BODY, x1 - t / 2, oy, cz, new THREE.Vector3(1, 0, 0));
  slab(EXT.w, t, ch, BODY, ox, y1 - t / 2, cz, new THREE.Vector3(0, 1, 0));
  slab(EXT.w, EXT.d, t, TRIM, ox, oy, zBot + t / 2, new THREE.Vector3(0, 0, -1));

  // Front face: bezel below and above the door opening, narrow side stiles.
  var dz0 = zBot + 56, dz1 = zTop - 54;              // door opening in Z
  var dx0 = x0 + 9, dx1 = x1 - 9;                    // door opening in X
  slab(EXT.w, t, dz0 - zBot, BODY, ox, y0 + t / 2, (zBot + dz0) / 2, new THREE.Vector3(0, -1, 0));
  slab(EXT.w, t, zTop - dz1, BODY, ox, y0 + t / 2, (dz1 + zTop) / 2, new THREE.Vector3(0, -1, 0));
  slab(dx0 - x0, t, dz1 - dz0, BODY, (x0 + dx0) / 2, y0 + t / 2, (dz0 + dz1) / 2, new THREE.Vector3(0, -1, 0));
  slab(x1 - dx1, t, dz1 - dz0, BODY, (dx1 + x1) / 2, y0 + t / 2, (dz0 + dz1) / 2, new THREE.Vector3(0, -1, 0));

  // Top cover, inset and lighter, the way the removable lid reads.
  slab(EXT.w - 26, EXT.d - 26, 4, 0x3b4048, ox, oy, zTop - 2, new THREE.Vector3(0, 0, 1));
  slab(EXT.w, EXT.d, 10, TRIM, ox, oy, zTop - 9, new THREE.Vector3(0, 0, 1));

  // Interior liner: one inverted box so the inside is its own darker surface.
  // LAMBERT, not Basic. It is by far the largest surface in the chamber, and
  // as an unlit material it made the chamber lamp measurably pointless -- a
  // frame with the lamp on differed from one with it off by 0.79 of a level
  // out of 255, which is a light that is not a light.
  var liner = new THREE.Mesh(
    new THREE.BoxGeometry(EXT.w - 2 * t, EXT.d - 2 * t, ch - 2 * t),
    new THREE.MeshLambertMaterial({map: shellTexture(), side: THREE.BackSide}));
  liner.position.set(ox, oy, cz);
  chamber.add(liner);

  // Screen and knob, bottom right of the front bezel -- the one detail that
  // makes the front read as this machine rather than a generic box. The P1S
  // screen is a 2.7-inch 192x64 panel (Bambu's own P1 spec list), which is a
  // 3:1 letterbox -- the first pass drew it nearly square.
  slab(65, 2, 22, 0x0b0d10, x1 - 66, y0 - 0.6, zBot + 28, null);
  var knob = new THREE.Mesh(new THREE.CylinderGeometry(11, 11, 4, 24),
    new THREE.MeshLambertMaterial({color: 0x666e7c}));
  knob.rotation.x = Math.PI / 2;
  knob.position.set(x1 - 22, y0 - 1.5, zBot + 28);
  chamber.add(knob);

  // Feet and the rear spool holder
  [[x0 + 24, y0 + 24], [x1 - 24, y0 + 24], [x0 + 24, y1 - 24], [x1 - 24, y1 - 24]]
    .forEach(function (p) {
      var f = new THREE.Mesh(new THREE.CylinderGeometry(13, 13, 9, 16),
        new THREE.MeshLambertMaterial({color: 0x101216}));
      f.rotation.x = Math.PI / 2;
      f.position.set(p[0], p[1], zBot - 4);
      chamber.add(f);
    });
  var spool = new THREE.Mesh(new THREE.CylinderGeometry(34, 34, 62, 24),
    new THREE.MeshLambertMaterial({color: 0x2b2f36}));
  spool.rotation.z = Math.PI / 2;
  spool.rotation.x = Math.PI / 2;
  spool.position.set(ox, y1 + 34, zBot + 96);
  chamber.add(spool);
  scene.add(chamber);

  // ── the door ─────────────────────────────────────────────────────────────
  // Hinged at one vertical edge and swung by a real rotation, so "open the
  // door" is the machine's own motion rather than a fade. Which edge is a
  // PROFILE SETTING, not a baked assumption: no primary source I could reach
  // stated the P1S hinge side, so it is exposed rather than guessed at.
  var hingeLeft = PRINTERS[printerId].hingeLeft !== false;
  doorGroup = new THREE.Group();
  var dw = dx1 - dx0, dh = dz1 - dz0;
  var glass = new THREE.Mesh(new THREE.BoxGeometry(dw, 3, dh),
    new THREE.MeshBasicMaterial({color: 0x6f7f8c, transparent: true,
      opacity: 0.17, depthWrite: false, side: THREE.DoubleSide}));
  glass.position.set(hingeLeft ? dw / 2 : -dw / 2, 0, 0);
  glass.userData.door = true;
  doorGroup.add(glass);
  var frameCol = 0x1d2026;
  [[dw, 7, 0, (dh - 7) / 2], [dw, 7, 0, -(dh - 7) / 2],
   [7, dh, -(dw - 7) / 2, 0], [7, dh, (dw - 7) / 2, 0]].forEach(function (f) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(f[0], 5, f[1]),
      new THREE.MeshLambertMaterial({color: frameCol}));
    m.position.set((hingeLeft ? dw / 2 : -dw / 2) + f[2], 0, f[3]);
    m.userData.door = true;
    doorGroup.add(m);
  });
  var grip = new THREE.Mesh(new THREE.BoxGeometry(9, 13, 74),
    new THREE.MeshLambertMaterial({color: 0x7b8493}));
  grip.position.set(hingeLeft ? dw - 16 : -dw + 16, -7, 0);
  grip.userData.door = true;
  doorGroup.add(grip);
  doorGroup.position.set(hingeLeft ? dx0 : dx1, y0 + 1, (dz0 + dz1) / 2);
  doorGroup.userData.sign = hingeLeft ? 1 : -1;
  doorGroup.name = 'door';
  scene.add(doorGroup);

  buildBed(X, Y, ox, oy);
  buildGantry(EXT.w, ox, oy);
  buildInterior(X, Y, ox, oy, zBot, zTop, x0, x1, y0, y1, t, true);
  buildAMS(PRINTERS[printerId].ams, ox, oy, y1, zTop);
  rebuildToolhead(true);
  restoreMotionVisibility();
  syncDoorControl();

  // An AMS on the lid makes the machine half again as tall, so the framing has
  // to come from the real outer extent rather than a number tuned to a bare
  // printer -- otherwise the AMS hangs off the top of the frame as a dark slab.
  var amsSpec = PRINTERS[printerId].ams;
  machineBounds = {zBot: zBot, zTop: zTop, ox: ox, oy: oy,
                   zOuter: zTop + (amsSpec ? amsSpec.h + 8 : 0)};
  cam.tx = ox; cam.ty = oy;
  cam.tz = (machineBounds.zBot + machineBounds.zOuter) / 2;
  cam.r = machineRadius();
}

function machineRadius() {
  var mb = machineBounds;
  return mb ? Math.max(980, (mb.zOuter - mb.zBot) * 1.95) : 1260;
}

// Two machine-view framings: the whole stack when the door is shut, and a
// close stand-in-front-of-it framing when it is open. Loading a job runs this
// too, so opening the door and then switching plates doesn't fly back out.
function machineCamera(open) {
  var mb = machineBounds;
  if (open) {
    cam.theta = -1.15; cam.phi = 1.33;
    cam.r = 880;
    cam.tz = mb ? mb.zBot * 0.36 : -100;
  } else {
    cam.tz = mb ? (mb.zBot + mb.zOuter) / 2 : 40;
    cam.r = machineRadius();
  }
}

function buildBed(X, Y, ox, oy) {
  bedGroup = new THREE.Group();
  plate = new THREE.Mesh(new THREE.BoxGeometry(X + 14, Y + 14, 7),
    new THREE.MeshLambertMaterial({map: peiTexture()}));
  plate.position.set(ox, oy, -3.6);
  bedGroup.add(plate);
  var carrier = new THREE.Mesh(new THREE.BoxGeometry(X + 30, Y + 30, 10),
    new THREE.MeshBasicMaterial({color: 0x191d25}));
  carrier.position.set(ox, oy, -12);
  bedGroup.add(carrier);

  grid = new THREE.Group();
  var gp = [];
  for (var i = 0; i <= X; i += 32) { gp.push(i, 0, 0.06, i, Y, 0.06); }
  for (var k = 0; k <= Y; k += 32) { gp.push(0, k, 0.06, X, k, 0.06); }
  var gg = new THREE.BufferGeometry();
  gg.setAttribute('position', new THREE.Float32BufferAttribute(gp, 3));
  grid.add(new THREE.LineSegments(gg, new THREE.LineBasicMaterial({
    color: 0x5b6475, transparent: true, opacity: 0.7})));
  var edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.PlaneGeometry(X, Y)),
    new THREE.LineBasicMaterial({color: 0x99a3b5}));
  edge.position.set(X / 2, Y / 2, 0.08);
  grid.add(edge);
  bedGroup.add(grid);

  shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({map: blobTexture(), transparent: true,
      opacity: 0.5, depthWrite: false}));
  shadowPlane.position.z = 0.12;
  shadowPlane.visible = false;
  bedGroup.add(shadowPlane);
  bedGroup.name = 'bed';
  scene.add(bedGroup);
}

function buildGantry(W, ox, oy) {
  gantry = new THREE.Group();
  gantry.add(new THREE.Mesh(new THREE.BoxGeometry(W - 40, 9, 6.5),
    new THREE.MeshLambertMaterial({color: 0x3a404b})));
  var railTop = new THREE.Mesh(new THREE.BoxGeometry(W - 40, 9, 1.3),
    new THREE.MeshBasicMaterial({color: 0x454b58}));
  railTop.position.z = 3.8;
  gantry.add(railTop);
  gantry.position.set(ox, oy, 0);
  gantry.name = 'gantry';
  gantry.visible = false;
  scene.add(gantry);
}

// The Z stage and the rails the gantry rides on. What is VERIFIED here is the
// motion, not the ironmongery: a P1S has a fixed gantry and a heatbed that
// descends on a Z stage, so the print sinks away from a nozzle that holds one
// height. The exact internal layout of that stage is drawn schematically --
// two rear lead screws and a carriage -- because no primary source I could
// reach documents it, and the printer panel says so on screen rather than
// letting a learner read this as a photograph.
function buildInterior(X, Y, ox, oy, zBot, zTop, x0, x1, y0, y1, t, detailed) {
  var METAL = 0x555c69, DARK = 0x21252c, FRAME = 0x2c313a;
  if (!detailed) {
    // An envelope has rails for the gantry to ride and nothing else. The Z
    // stage below is the P1S's own, read off its service pages; drawing it
    // around another machine would be inventing that machine's insides.
    yRails = new THREE.Group();
    [ox - X / 2 - 24, ox + X / 2 + 24].forEach(function (x) {
      var r = new THREE.Mesh(new THREE.BoxGeometry(11, Y + 60, 9),
        new THREE.MeshLambertMaterial({color: DARK}));
      r.position.set(x, oy, 0);
      yRails.add(r);
    });
    yRails.visible = false;
    yRails.name = 'yrails';
    scene.add(yRails);
    return;
  }

  // Z stage. Bambu's own service docs are specific about this one: "The Z-axis
  // is comprised of THREE lead screws connected to a single stepper motor using
  // a belt" (wiki, Introduction to P1 series), the motor "on the bottom base of
  // the printer" with "the Z belt around the driving pulley", a tensioner also
  // on the bottom, and three Z-axis sliders carrying the bed (wiki, Z motor /
  // Z timing belt / Z tensioner). All of that is drawn. What is NOT published
  // anywhere I could reach is where the three sit around the base, so they are
  // placed to leave the doorway clear and the panel says they are placed, not
  // documented.
  var zPosts = [[x0 + 34, y1 - t - 26], [x1 - 34, y1 - t - 26], [x1 - 34, y0 + t + 46]];
  var zLo = zBot + 16, zHi = zTop - 92;

  zPosts.forEach(function (p) {
    var screw = new THREE.Mesh(new THREE.CylinderGeometry(5, 5, zHi - zLo, 12),
      new THREE.MeshLambertMaterial({color: METAL}));
    screw.rotation.x = Math.PI / 2;
    screw.position.set(p[0], p[1], (zLo + zHi) / 2);
    chamber.add(screw);
    var post = new THREE.Mesh(new THREE.BoxGeometry(14, 14, zHi - zLo),
      new THREE.MeshLambertMaterial({color: DARK}));
    post.position.set(p[0] + (p[0] > ox ? 20 : -20), p[1], (zLo + zHi) / 2);
    chamber.add(post);
    var pulley = new THREE.Mesh(new THREE.CylinderGeometry(11, 11, 9, 14),
      new THREE.MeshLambertMaterial({color: 0x3d4552}));
    pulley.rotation.x = Math.PI / 2;
    pulley.position.set(p[0], p[1], zLo - 6);
    chamber.add(pulley);
  });

  // One motor, one belt, both under the base -- which is why all three screws
  // turn together and the bed cannot tilt out of tram on its own.
  var zMotor = new THREE.Mesh(new THREE.BoxGeometry(34, 34, 30),
    new THREE.MeshLambertMaterial({color: 0x1b1e24}));
  zMotor.position.set(ox + 46, y1 - t - 30, zLo - 22);
  chamber.add(zMotor);
  var beltPath = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
      new THREE.Vector3(zPosts[0][0], zPosts[0][1], zLo - 6),
      new THREE.Vector3(ox + 46, y1 - t - 30, zLo - 6),
      new THREE.Vector3(zPosts[1][0], zPosts[1][1], zLo - 6),
      new THREE.Vector3(zPosts[2][0], zPosts[2][1], zLo - 6),
      new THREE.Vector3(zPosts[0][0], zPosts[0][1], zLo - 6)], true), 30, 2.4, 6, true),
    new THREE.MeshLambertMaterial({color: 0x15171c}));
  chamber.add(beltPath);

  // Three sliders, on the bed, descending with it -- the whole point of
  // drawing the stage at all is that this is the part that actually moves.
  var beam = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0 - 46, 15, 11),
    new THREE.MeshLambertMaterial({color: FRAME}));
  beam.position.set(ox, y1 - t - 39, -14);
  bedGroup.add(beam);
  zPosts.forEach(function (p) {
    var slider = new THREE.Mesh(new THREE.BoxGeometry(24, 28, 19),
      new THREE.MeshLambertMaterial({color: 0x3d4552}));
    slider.position.set(p[0], p[1], -14);
    bedGroup.add(slider);
    var arm = new THREE.Mesh(new THREE.BoxGeometry(13, Math.abs(p[1] - oy), 9),
      new THREE.MeshLambertMaterial({color: FRAME}));
    arm.position.set(p[0], (oy + p[1]) / 2, -14);
    bedGroup.add(arm);
  });

  // The two Y rails the CoreXY gantry beam travels on, and the pair of belts --
  // one per stepper, independent, which is what makes it CoreXY rather than
  // cartesian (wiki: "Every stepper motor has an independent belt connected to
  // the print head"). They hold a fixed height, so they cannot live inside the
  // gantry group; setSeg keeps them level with it instead.
  yRails = new THREE.Group();
  [x0 + t + 7, x1 - t - 7].forEach(function (x) {
    var r = new THREE.Mesh(new THREE.BoxGeometry(11, y1 - y0 - 2 * t - 16, 9),
      new THREE.MeshLambertMaterial({color: DARK}));
    r.position.set(x, oy, 0);
    yRails.add(r);
    [-3.5, 3.5].forEach(function (dy) {
      var b = new THREE.Mesh(new THREE.BoxGeometry(2.5, y1 - y0 - 2 * t - 16, 5),
        new THREE.MeshLambertMaterial({color: 0x15171c}));
      b.position.set(x + (x < ox ? 8 : -8), oy, dy + 6);
      yRails.add(b);
    });
  });
  yRails.visible = false;
  yRails.name = 'yrails';
  scene.add(yRails);

  // Chamber LED -- on the LEFT beam, not centred on the front where the first
  // pass put it. Bambu's P1 service guide has the LED and the chamber camera
  // both behind the left panel, wired to the same AP board, close enough that
  // the LED "will get caught by the camera" if you slide it the wrong way; the
  // camera seats into a notch on the front column with its flex cable tucked
  // behind the front cover. So: light bar down the left beam, camera at the
  // front-left corner beside it. It is a 5V 0.3A strip, which is why the real
  // chamber is lit but not floodlit.
  var ledLen = (y1 - y0) * 0.52;
  var ledY = y0 + t + ledLen / 2 + 18;
  var bar = new THREE.Mesh(new THREE.BoxGeometry(5, ledLen, 9),
    new THREE.MeshBasicMaterial({color: 0xffe9c6}));
  bar.position.set(x0 + t + 9, ledY, zTop - 30);
  chamber.add(bar);
  var shell = new THREE.Mesh(new THREE.BoxGeometry(11, ledLen + 10, 14),
    new THREE.MeshLambertMaterial({color: 0x2b2f36}));
  shell.position.set(x0 + t + 5, ledY, zTop - 30);
  chamber.add(shell);
  // Tight falloff on purpose. A 5V 0.3A strip pools light near itself and
  // leaves the far corners dim; the first pass's wide, bright lamp flattened
  // the whole chamber into even grey, which reads as a lightbox, not a P1S.
  chamberLamp = new THREE.PointLight(0xffdcae, 3.0, 560, 1.5);
  chamberLamp.position.set(x0 + 58, ledY, zTop - 46);
  chamber.add(chamberLamp);

  var cam2 = new THREE.Mesh(new THREE.BoxGeometry(17, 15, 15),
    new THREE.MeshLambertMaterial({color: 0x23262d}));
  cam2.position.set(x0 + t + 12, y0 + t + 12, zTop - 30);
  chamber.add(cam2);
  var lens = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 3, 12),
    new THREE.MeshBasicMaterial({color: 0x0a0c10}));
  lens.rotation.x = Math.PI / 2;
  lens.position.set(x0 + t + 16, y0 + t + 16, zTop - 36);
  chamber.add(lens);
}

// The AMS, at its real size, sitting where one actually sits. The spools drawn
// inside are illustrative -- nothing here reads the machine, so they are four
// plausible colours and the panel says as much rather than implying a feed.
function buildAMS(spec, ox, oy, y1, zTop) {
  amsGroup = null;
  if (!spec) { return; }
  amsGroup = new THREE.Group();
  var cy = y1 - spec.d / 2 - 6, cz = zTop + 4 + spec.h / 2;

  // Built as panels, not a solid block: a closed box would hide the spools
  // behind its own lit top face no matter how transparent the lid above it is.
  var wall = 8, shell = new THREE.MeshLambertMaterial({color: 0x2a2e35});
  function panel(w, d, h, x, y, z) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), shell);
    m.position.set(x, y, z);
    amsGroup.add(m);
  }
  panel(spec.w, spec.d, wall, ox, cy, cz - spec.h / 2 + wall / 2);
  panel(wall, spec.d, spec.h, ox - spec.w / 2 + wall / 2, cy, cz);
  panel(wall, spec.d, spec.h, ox + spec.w / 2 - wall / 2, cy, cz);
  panel(spec.w, wall, spec.h, ox, cy + spec.d / 2 - wall / 2, cz);
  panel(spec.w, wall, spec.h, ox, cy - spec.d / 2 + wall / 2, cz);
  var amsEdge = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(spec.w, spec.d, spec.h)),
    new THREE.LineBasicMaterial({color: 0x4a515e}));
  amsEdge.position.set(ox, cy, cz);
  amsGroup.add(amsEdge);

  var spools = [], cores = [];
  for (var i = 0; i < spec.slots; i++) {
    var x = ox - (spec.slots - 1) * 46 + i * 92;
    // Spool size is the AMS's own published compatibility range -- 197-202 mm
    // across, 50-68 mm wide -- which is why they very nearly fill the box.
    var fil = new THREE.Mesh(new THREE.CylinderGeometry(99, 99, 56, 28),
      new THREE.MeshLambertMaterial({color: FILAMENT[i % FILAMENT.length]}));
    // Rotated onto X by the PARENT, so the mesh's own X rotation is free to be
    // the spool turning as filament is pulled off it.
    var hub = new THREE.Group();
    hub.rotation.z = Math.PI / 2;
    hub.position.set(x, cy, cz - 2);
    hub.add(fil);
    amsGroup.add(hub);
    spools.push(fil);
    var core = new THREE.Mesh(new THREE.CylinderGeometry(34, 34, 60, 20),
      new THREE.MeshLambertMaterial({color: 0x15171c}));
    core.rotation.z = Math.PI / 2;
    core.position.set(x, cy, cz - 2);
    amsGroup.add(core);
    cores.push(core);
  }

  // Smoked lid over the spools -- the reason you can see them at all.
  var lid = new THREE.Mesh(new THREE.BoxGeometry(spec.w - 22, spec.d - 22, 5),
    new THREE.MeshLambertMaterial({color: 0x59616e, transparent: true,
      opacity: 0.36, depthWrite: false}));
  lid.position.set(ox, cy, cz + spec.h / 2 - 3);
  amsGroup.add(lid);
  var lz = cz + spec.h / 2 - 3, fm = new THREE.MeshLambertMaterial({color: 0x21252b});
  [[spec.w, 11, ox, cy - spec.d / 2 + 5.5], [spec.w, 11, ox, cy + spec.d / 2 - 5.5],
   [11, spec.d, ox - spec.w / 2 + 5.5, cy], [11, spec.d, ox + spec.w / 2 - 5.5, cy]]
    .forEach(function (f) {
      var m = new THREE.Mesh(new THREE.BoxGeometry(f[0], f[1], 7), fm);
      m.position.set(f[2], f[3], lz);
      amsGroup.add(m);
    });

  // PTFE bundle looping out of the back and into the top of the machine.
  var curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(ox, cy + spec.d / 2 - 4, cz - 40),
    new THREE.Vector3(ox, y1 + 54, cz - 74),
    new THREE.Vector3(ox, y1 - 26, zTop + 3)]);
  var feed = new THREE.Mesh(new THREE.TubeGeometry(curve, 22, 7, 10, false),
    new THREE.MeshLambertMaterial({color: 0x171a20}));
  amsGroup.add(feed);

  amsGroup.userData.spools = spools;
  amsGroup.userData.cores = cores;
  amsGroup.userData.feed = feed;
  amsGroup.name = 'ams';
  scene.add(amsGroup);
}

// An envelope, not a portrait: the machine's real outside footprint as an
// edge outline, a base under the bed, and nothing else. Everything here is a
// number the manufacturer publishes; no panels, no door, no chamber light, no
// screen, because none of those are known for this machine at this level of
// detail and a drawn guess would contradict the panel beside it.
function buildOpenFrame(prof, X, Y, Z, ox, oy, zBot, slinger) {
  var f = prof.footprint;
  if (f) {
    var box = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(f[0], f[1], f[2])),
      new THREE.LineBasicMaterial({color: 0x39404d}));
    box.position.set(ox, oy, zBot + f[2] / 2);
    chamber.add(box);
  }
  var baseW = f ? f[0] : X + 90, baseD = f ? f[1] : Y + 90;
  var base = new THREE.Mesh(new THREE.BoxGeometry(baseW, baseD, 46),
    new THREE.MeshLambertMaterial({color: 0x23262d}));
  base.position.set(ox, oy, zBot + 23);
  chamber.add(base);
  // Build volume, drawn as the volume it is rather than as a box that pretends
  // to be a chamber. It sits where the machine can actually reach: up from the
  // plate on a slinger, down from it on a descending bed.
  var vol = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(X, Y, Z)),
    new THREE.LineBasicMaterial({color: 0x2b3f52}));
  vol.position.set(ox, oy, slinger ? Z / 2 : -Z / 2);
  chamber.add(vol);
}

// A machine without a door must not offer to open one.
// Switching machines mid-print rebuilds the gantry hidden, because that is the
// state it starts in before any job is mounted. If a job IS mounted the motion
// system has to come back with it -- otherwise changing printers halfway
// through a replay silently loses the gantry and the rails.
function restoreMotionVisibility() {
  if (!JOB) { return; }
  if (gantry) { gantry.visible = true; }
  if (yRails) { yRails.visible = true; }
}

function syncDoorControl() {
  var b = $('door');
  if (!b) { return; }
  b.hidden = !doorGroup;
  if (!doorGroup && doorOpen) { setDoor(false); }
}

// The P1S toolhead, built from Bambu's own service breakdown rather than a
// generic hotend: a front housing assembly that carries the part-cooling fan
// (its connector is what you unplug to remove it), a middle housing with the
// filament cutter lever and its protruding blade, a rear housing over the
// extruder, a PTFE pneumatic joint on top, and the all-in-one hotend -- nozzle
// integrated into the heat block, joined to the heatsink by a thin metal tube.
// There is no LiDAR here on purpose: that is the X1 Carbon, not this machine.
// Bambu publishes no toolhead dimensions, so the proportions are read off the
// assembly order and the part list, not measured.
// Swapping the head with the machine: the detailed one above is the P1S's own
// and carrying it onto another profile would be the same contradiction the
// enclosure was. Visibility survives the swap so changing machines mid-print
// does not blank the nozzle.
function rebuildToolhead(detailed) {
  var wasVisible = nozzle ? nozzle.visible : false;
  var scale = nozzle ? nozzle.scale.x : 1;
  if (nozzle) { scene.remove(nozzle); }
  nozzle = detailed ? buildToolhead() : buildSimpleHead();
  nozzle.visible = wasVisible;
  nozzle.scale.setScalar(scale);
  scene.add(nozzle);
}

// Enough head to show where the nozzle is and nothing that claims to be a
// specific machine's hardware.
function buildSimpleHead() {
  var g = new THREE.Group();
  var body = new THREE.Mesh(new THREE.BoxGeometry(22, 18, 26),
    new THREE.MeshLambertMaterial({color: 0x22262e}));
  body.position.z = 20;
  g.add(body);
  g.add(new THREE.Mesh(new THREE.BoxGeometry(10, 10, 6),
    new THREE.MeshLambertMaterial({color: 0x4a3a22})).translateZ(4.6));
  var tip = new THREE.Mesh(new THREE.ConeGeometry(2.4, 5, 16),
    new THREE.MeshBasicMaterial({color: 0xc98b46}));
  tip.rotation.x = Math.PI;
  tip.position.z = 1.4;
  g.add(tip);
  glowSprite = new THREE.Sprite(new THREE.SpriteMaterial({map: glowTexture(),
    transparent: true, depthWrite: false,
    blending: THREE.AdditiveBlending, opacity: 0.85}));
  glowSprite.scale.set(26, 26, 1);
  glowSprite.position.z = 0.6;
  g.add(glowSprite);
  return g;
}

function buildToolhead() {
  var g = new THREE.Group();
  function part(w, d, h, color, z, y) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(w, d, h),
      new THREE.MeshLambertMaterial({color: color}));
    m.position.set(0, y || 0, z);
    g.add(m);
    return m;
  }
  // Heights stack from the nozzle up: the hotend hangs BELOW the housings,
  // which is the whole shape of a real toolhead. Burying the heatsink inside
  // the middle housing was the first pass's mistake and it showed immediately
  // on screen -- a dark box with nothing under it.
  part(26, 15, 15, 0x2d323c, 44, 9);           // X-carriage on the gantry beam
  part(27, 19, 30, 0x1b1e25, 40, 11);          // rear housing over the extruder
  var mid = part(25, 17, 26, 0x22262e, 38, 0);    // middle housing
  var edges = new THREE.LineSegments(new THREE.EdgesGeometry(mid.geometry),
    new THREE.LineBasicMaterial({color: 0x4b5261}));
  edges.position.set(0, 0, 38);
  g.add(edges);
  part(25, 8, 25, 0x15181e, 37, -12);          // front housing assembly

  // Part-cooling fan, in the front housing where the real one lives.
  var fan = new THREE.Mesh(new THREE.CylinderGeometry(8.6, 8.6, 2.4, 18),
    new THREE.MeshLambertMaterial({color: 0x0c0e12}));
  fan.rotation.x = Math.PI / 2;
  fan.position.set(0, -16.4, 37);
  g.add(fan);
  var hub = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 3, 12),
    new THREE.MeshLambertMaterial({color: 0x3a4049}));
  hub.rotation.x = Math.PI / 2;
  hub.position.set(0, -17, 37);
  g.add(hub);

  // Filament cutter lever, on the side of the middle housing.
  var lever = part(5, 13, 3.4, 0x596270, 46, -2);
  lever.position.x = 14;

  // PTFE pneumatic joint on top, where the AMS tube lands.
  var joint = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 5, 6, 14),
    new THREE.MeshLambertMaterial({color: 0x6e7683}));
  joint.rotation.x = Math.PI / 2;
  joint.position.set(0, 8, 57);
  g.add(joint);

  // All-in-one hotend: finned heatsink, thin metal tube, integrated heat
  // block and nozzle. This is the geometry the wiki describes in words.
  for (var i = 0; i < 5; i++) {
    part(15, 13, 1.4, 0x8e96a3, 13 + i * 2.5, 0);
  }
  var neck = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 2.1, 4.4, 12),
    new THREE.MeshLambertMaterial({color: 0x9aa2af}));
  neck.rotation.x = Math.PI / 2;
  neck.position.set(0, 0, 9.4);
  g.add(neck);
  part(11, 11, 5.4, 0x4a3a22, 4.6, 0);         // heat block, silicone-socked
  var tip = new THREE.Mesh(new THREE.ConeGeometry(2.4, 5, 16),
    new THREE.MeshBasicMaterial({color: 0xc98b46}));
  tip.rotation.x = Math.PI;
  tip.position.set(0, 0, 1.4);
  g.add(tip);

  glowSprite = new THREE.Sprite(new THREE.SpriteMaterial({map: glowTexture(),
    transparent: true, depthWrite: false,
    blending: THREE.AdditiveBlending, opacity: 0.85}));
  glowSprite.scale.set(26, 26, 1);
  glowSprite.position.set(0, 0, 0.6);
  g.add(glowSprite);
  return g;
}

// Textures are generated, never fetched: the artifact CSP blocks image hosts,
// and a canvas costs nothing.
function shellTexture() {
  var c = document.createElement('canvas');
  c.width = 4; c.height = 128;
  var g = c.getContext('2d');
  var lg = g.createLinearGradient(0, 0, 0, 128);
  lg.addColorStop(0, '#0a0c11');
  lg.addColorStop(0.55, '#111420');
  lg.addColorStop(1, '#161a24');
  g.fillStyle = lg; g.fillRect(0, 0, 4, 128);
  return new THREE.CanvasTexture(c);
}

function peiTexture() {
  var c = document.createElement('canvas');
  c.width = c.height = 256;
  var g = c.getContext('2d');
  g.fillStyle = '#343943'; g.fillRect(0, 0, 256, 256);
  var img = g.getImageData(0, 0, 256, 256), d = img.data;
  for (var i = 0; i < d.length; i += 4) {
    var n = (Math.random() - 0.5) * 54;
    d[i] += n; d[i + 1] += n; d[i + 2] += n * 0.9;
  }
  g.putImageData(img, 0, 0);
  var tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(9, 9);
  return tex;
}

function blobTexture() {
  var c = document.createElement('canvas');
  c.width = c.height = 128;
  var g = c.getContext('2d');
  var rg = g.createRadialGradient(64, 64, 4, 64, 64, 62);
  rg.addColorStop(0, 'rgba(0,0,0,0.85)');
  rg.addColorStop(0.55, 'rgba(0,0,0,0.35)');
  rg.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = rg; g.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}

function glowTexture() {
  var c = document.createElement('canvas');
  c.width = c.height = 64;
  var g = c.getContext('2d');
  var rg = g.createRadialGradient(32, 32, 1, 32, 32, 31);
  rg.addColorStop(0, 'rgba(255,196,120,0.95)');
  rg.addColorStop(0.35, 'rgba(255,132,40,0.42)');
  rg.addColorStop(1, 'rgba(255,110,20,0)');
  g.fillStyle = rg; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}

function onResize() {
  var w = stage.clientWidth, h = stage.clientHeight;
  if (!w || !h) { return; }
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

// \u2500\u2500 orbit (hand-rolled: OrbitControls is not on the allowed CDN as a UMD) \u2500\u2500\u2500
// A door you can see is a door you expect to be able to touch. A tap is an
// orbit drag that never moved, so the threshold is in pixels, not timing --
// on a phone a "tap" always carries a few pixels of finger travel.
var _ray = new THREE.Raycaster(), _ndc = new THREE.Vector2();
function pickDoor(clientX, clientY) {
  if (!doorGroup || !doorGroup.visible) { return false; }
  var r = renderer.domElement.getBoundingClientRect();
  _ndc.set((clientX - r.left) / r.width * 2 - 1,
           -((clientY - r.top) / r.height) * 2 + 1);
  _ray.setFromCamera(_ndc, camera);
  var hits = _ray.intersectObjects(doorGroup.children, false);
  for (var i = 0; i < hits.length; i++) {
    if (hits[i].object.userData.door) { return true; }
  }
  return false;
}

function attachOrbit(el) {
  var down = null, touches = {}, pinch = null, travel = 0, start = null;
  var fling = null;
  el.style.touchAction = 'none';
  function pinchDist() {
    var k = Object.keys(touches);
    var a = touches[k[0]], b2 = touches[k[1]];
    return Math.hypot(a.x - b2.x, a.y - b2.y);
  }
  el.addEventListener('pointerdown', function (e) {
    el.setPointerCapture(e.pointerId);
    touches[e.pointerId] = {x:e.clientX, y:e.clientY};
    if (Object.keys(touches).length === 2) {
      pinch = {d: pinchDist(), r: cam.r};
      down = null;
      return;
    }
    down = {x:e.clientX, y:e.clientY, pan:e.shiftKey || e.button === 2 || e.button === 1};
    start = {x:e.clientX, y:e.clientY};
    travel = 0;
    spin.theta = spin.phi = 0;   // grabbing it stops a fling, like a real dial
    fling = null;
  });
  el.addEventListener('pointermove', function (e) {
    if (touches[e.pointerId]) { touches[e.pointerId] = {x:e.clientX, y:e.clientY}; }
    if (pinch && Object.keys(touches).length === 2) {
      var d = pinchDist();
      if (d > 4) { cam.r = Math.max(40, Math.min(1600, pinch.r * pinch.d / d)); }
      moveUntil = performance.now() + 150;
      return;
    }
    if (!down) { return; }
    var dx = e.clientX - down.x, dy = e.clientY - down.y;
    down.x = e.clientX; down.y = e.clientY;
    travel += Math.abs(dx) + Math.abs(dy);
    if (down.pan) {
      var s = cam.r * 0.0016;
      var st = Math.sin(cam.theta), ct = Math.cos(cam.theta);
      cam.tx -= (-st * dx) * s; cam.ty -= (ct * dx) * s;
      cam.tz += dy * s;
    } else {
      cam.theta -= dx * 0.006;
      cam.phi = Math.max(0.05, Math.min(Math.PI - 0.05, cam.phi - dy * 0.006));
      // Record the angle covered AND how long it took. A flick has to be
      // measured as a velocity, not as a per-event delta: the browser coalesces
      // pointermove while a frame is busy, so on a slow device one event can
      // carry half a second of finger travel.
      var mnow = performance.now();
      fling = {t: mnow, theta: -dx * 0.006, phi: -dy * 0.006,
               dt: Math.max(mnow - (fling ? fling.t : mnow - 16), 8)};
    }
    moveUntil = performance.now() + 150;
  });
  el.addEventListener('pointerup', function (e) {
    if (start && travel < 7 && !pinch && pickDoor(e.clientX, e.clientY)) {
      setDoor(!doorOpen);
    } else if (fling && performance.now() - fling.t < Math.max(130, fling.dt * 1.6)) {
      // Let go mid-drag and it keeps turning, decaying. Only a release that was
      // still moving flings -- stopping first and then lifting holds. The
      // window scales with the gap between moves for the same reason the
      // velocity does: measured here, a 2fps page took 377ms to deliver
      // pointerup after the last pointermove, so a fixed 90ms window (tuned on
      // a fast machine) never opened at all on a slow one.
      var perFrame = 16.67 / fling.dt;
      spin.theta = fling.theta * perFrame * 0.88;
      spin.phi = fling.phi * perFrame * 0.88;
    }
    fling = null;
    start = null;
  });
  ['pointerup','pointercancel'].forEach(function (t) {
    el.addEventListener(t, function (e) {
      delete touches[e.pointerId];
      if (Object.keys(touches).length < 2) { pinch = null; }
      down = null;
    });
  });
  // Mouse only: the cursor is the one affordance that says the door is live.
  // A phone has no hover, and a raycast per touchmove would be waste.
  el.addEventListener('pointermove', function (e) {
    if (down || pinch || e.pointerType !== 'mouse') { return; }
    el.style.cursor = pickDoor(e.clientX, e.clientY) ? 'pointer' : '';
  });
  el.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  el.addEventListener('wheel', function (e) {
    e.preventDefault();
    cam.r = Math.max(40, Math.min(1600, cam.r * (1 + Math.sign(e.deltaY) * 0.11)));
    moveUntil = performance.now() + 150;
  }, {passive:false});
}

// The door swings on a real hinge rather than fading, so the motion is the
// machine's own. Eased toward the target every frame; no tween library.
function updateDoor() {
  if (!doorGroup) { return; }
  var want = doorOpen ? doorTarget : 0;
  if (Math.abs(doorAngle - want) > 0.0015) {
    doorAngle += (want - doorAngle) * 0.13;
  } else {
    doorAngle = want;
  }
  doorGroup.rotation.z = doorAngle;
}

// Machine view keeps the exterior solid, because Scott asked for a printer
// that looks like the printer. Chamber view hides whichever panels sit
// between the camera and the build volume, which is the only way to watch a
// print from an arbitrary angle without the case in the way.
function updateCutaway() {
  var cut = viewMode === 'chamber';
  var c = machineBounds;
  // The AMS is furniture on the lid, not chamber content. In cutaway it would
  // simply sit on top of the hole the cutaway just opened.
  if (amsGroup) { amsGroup.visible = !cut; }
  for (var i = 0; i < extPanels.length; i++) {
    var p = extPanels[i];
    if (!cut) { p.mesh.visible = true; continue; }
    var toCam = camera.position.clone().sub(
      new THREE.Vector3(c ? c.ox : 128, c ? c.oy : 128, 0));
    p.mesh.visible = p.n.dot(toCam) <= 0;
  }
}

// A flick keeps spinning and a jump eases in. Both are feel, not frame rate,
// and they are what "smoother when rotating" mostly means: raw pointer deltas
// written straight into an angle look stepped no matter how fast the machine
// draws them.
// Both rates are per SIXTIETH OF A SECOND and converted against the real frame
// time, never applied once per frame. That difference is the whole feature on a
// slow device: a flat 0.19 per frame means a phone rendering at 9fps takes a
// second and a half to catch up with a finger that has already stopped, which
// is worse than no damping at all. Measured 9fps in this container's software
// renderer, which is exactly the case that would have shipped broken.
var DAMP = 0.19, SPIN_DECAY = 0.92;
var _lastCam = 0;

function updateCamera(now) {
  var frames = _lastCam ? Math.min((now - _lastCam) / 16.67, 8) : 1;
  _lastCam = now;
  var damp = 1 - Math.pow(1 - DAMP, frames);
  var decay = Math.pow(SPIN_DECAY, frames);

  if (spin.theta || spin.phi) {
    cam.theta += spin.theta * frames;
    cam.phi = Math.max(0.05, Math.min(Math.PI - 0.05, cam.phi + spin.phi * frames));
    spin.theta *= decay;
    spin.phi *= decay;
    if (Math.abs(spin.theta) < 0.00035 && Math.abs(spin.phi) < 0.00035) {
      spin.theta = spin.phi = 0;
    } else {
      moveUntil = now + 90;
    }
  }
  var settled = true;
  ['theta', 'phi', 'r', 'tx', 'ty', 'tz'].forEach(function (k) {
    var d = cam[k] - view[k];
    if (Math.abs(d) < (k === 'r' ? 0.05 : 0.0004)) { view[k] = cam[k]; return; }
    view[k] += d * damp;
    settled = false;
  });
  if (!settled) { moveUntil = Math.max(moveUntil, now + 60); }

  var sp = Math.sin(view.phi), cp = Math.cos(view.phi);
  camera.position.set(
    view.tx + view.r * sp * Math.cos(view.theta),
    view.ty + view.r * sp * Math.sin(view.theta),
    view.tz + view.r * cp);
  camera.lookAt(view.tx, view.ty, view.tz);
}

// While the view is actually moving, render fewer pixels. A phone caps out at
// pixel ratio 2, which is four times the fragments of 1 -- and a moving frame
// is the one frame nobody is studying. It snaps back the moment you let go.
function setResolution(now) {
  var moving = now < moveUntil;
  if (moving === lowRes) { return; }
  lowRes = moving;
  renderer.setPixelRatio(moving ? Math.min(basePixelRatio, 1) : basePixelRatio);
  onResize();
}

// \u2500\u2500 shader \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
// Positions arrive as Int16 hundredths of a millimetre -- see the exporter's
// note on why. uScale converts back; nothing else in the page sees raw units.
var VERT = [
  'attribute float aType;',
  'attribute float aSpeed;',
  'attribute float aTool;',
  'uniform vec3 uColor[13];',
  'uniform float uVis[13];',
  'uniform vec3 uTool[8];',
  'uniform float uMode;',      // 0 = feature, 1 = speed, 2 = filament
  'uniform vec2 uSpd;',        // slowest / fastest mm/s in this job
  'varying vec3 vColor;',
  'varying float vVis;',
  'varying vec3 vPos;',
  // Magma, reversed, with the ends pulled in. Reversed so the BRIGHT end is
  // slow -- the outer wall and top surface, the parts a customer actually
  // sees. Ends clamped so the fast end lands on deep violet rather than black,
  // which would make infill invisible against the chamber.
  'vec3 magma(float t){',
  '  const vec3 c0=vec3(-0.002136,-0.000750,-0.005386);',
  '  const vec3 c1=vec3(0.251661,0.677523,2.494027);',
  '  const vec3 c2=vec3(8.353717,-3.577720,0.314468);',
  '  const vec3 c3=vec3(-27.668733,14.264731,-13.649213);',
  '  const vec3 c4=vec3(52.176140,-27.943606,12.944169);',
  '  const vec3 c5=vec3(-50.768525,29.046583,4.234153);',
  '  const vec3 c6=vec3(18.655705,-11.489774,-5.601962);',
  '  return clamp(c0+t*(c1+t*(c2+t*(c3+t*(c4+t*(c5+t*c6))))),0.0,1.0);',
  '}',
  'void main(){',
  '  int t = int(aType + 0.5);',
  '  float f = clamp((aSpeed - uSpd.x) / max(uSpd.y - uSpd.x, 1.0), 0.0, 1.0);',
  '  vec3 byFeature = uColor[t];',
  '  vec3 bySpeed = magma(mix(0.92, 0.28, f));',
  '  vec3 byFilament = uTool[int(aTool + 0.5)];',
  '  vColor = uMode < 0.5 ? byFeature : (uMode < 1.5 ? bySpeed : byFilament);',
  '  vVis = uVis[t];',
  '  vec3 p = position * 0.01;',
  '  vPos = p;',
  '  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);',
  '}'
].join('\n');

var FRAG = [
  'varying vec3 vColor;',
  'varying float vVis;',
  'varying vec3 vPos;',
  'uniform float uDim;',
  'uniform vec3 uEye;',
  'void main(){',
  '  if (vVis < 0.5) discard;',
  '  vec3 N = normalize(cross(dFdx(vPos), dFdy(vPos)));',
  '  if (!gl_FrontFacing) N = -N;',
  '  vec3 V = normalize(uEye - vPos);',
  // Key stands in for the chamber LED (high, forward of the door); the fill
  // comes from below because it stands in for bounce off the plate.
  '  vec3 Lk = normalize(vec3( 0.32,-0.72, 0.62));',
  '  vec3 Lf = normalize(vec3(-0.58, 0.34, 0.18));',
  '  float key  = max(dot(N, Lk), 0.0);',
  '  float fill = max(dot(N, Lf), 0.0);',
  '  float amb  = 0.26 + 0.20 * max(N.z, 0.0);',
  '  vec3 c = vColor * (amb + 0.66 * key + 0.24 * fill);',
  // Plastic is not chalk: a tight specular lobe plus a Fresnel edge is what
  // separates an extruded bead from a flat coloured ribbon. It is also the
  // whole cost difference between the two quality levels -- two pow() calls
  // per fragment over a few million triangles.
  '#ifdef RICH',
  '  float spec = pow(max(dot(reflect(-Lk, N), V), 0.0), 34.0);',
  '  c += vec3(1.0, 0.94, 0.85) * spec * 0.40;',
  '  float fres = pow(1.0 - max(dot(N, V), 0.0), 3.4);',
  '  c += mix(vColor, vec3(1.0, 0.86, 0.66), 0.45) * fres * 0.28;',
  '#endif',
  '  gl_FragColor = vec4(mix(c, vec3(0.055,0.06,0.072), uDim), 1.0);',
  '}'
].join('\n');

function makeMaterial(dim, rich) {
  var cols = TYPE_COLOR.map(function (h) { return new THREE.Color(h); });
  return new THREE.ShaderMaterial({
    uniforms: {
      uColor: {value: cols},
      uVis:   {value: new Array(N_TYPE).fill(1)},
      uTool:  {value: FILAMENT.map(function (h) { return new THREE.Color(h); })},
      uMode:  {value: 0},
      uSpd:   {value: new THREE.Vector2(15, 80)},
      uEye:   {value: new THREE.Vector3()},
      uDim:   {value: dim}
    },
    vertexShader: VERT, fragmentShader: FRAG,
    defines: rich ? {RICH: 1} : {},
    side: THREE.DoubleSide,
    extensions: {derivatives: true}
  });
}

// \u2500\u2500 geometry build \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
function b64(str, Ctor) {
  var bin = atob(str), n = bin.length, u8 = new Uint8Array(n);
  for (var i = 0; i < n; i++) { u8[i] = bin.charCodeAt(i); }
  return new Ctor(u8.buffer);
}

var JOB = null;           // decoded payload + derived arrays

function buildJob(raw) {
  var pts = b64(raw.pts, Int16Array);
  var polys = b64(raw.polys, Int32Array);
  var spd = b64(raw.speeds, Uint8Array);
  var polyTool = raw.polyTool ? b64(raw.polyTool, Uint8Array) : null;
  var layers = raw.layers;               // [z*100, polyStart, polyCount, sec, mm, h]
  var nPoly = polys.length / 3;

  // Pass 1: count points so the typed arrays are allocated once.
  var nPt = 0, nSeg = 0, i, k;
  for (k = 0; k < nPoly; k++) { nPt += polys[k * 3 + 2]; nSeg += polys[k * 3 + 2] - 1; }

  var vPos  = new Int16Array(nPt * 3 * 3);   // 3 verts across the bead tent
  var vType = new Uint8Array(nPt * 3);
  var vSpd  = new Uint8Array(nPt * 3);
  var vTool = new Uint8Array(nPt * 3);
  var index = new Uint32Array(nSeg * 12);
  var segEnd = new Float32Array(nSeg * 3);
  var segLen = new Float32Array(nSeg);
  var segCum = new Float32Array(nSeg + 1);
  var segLayer = new Int32Array(nSeg);
  var segTool = new Uint8Array(nSeg);
  var layerSeg = new Int32Array(layers.length + 1);

  var hw = (raw.beadWidth || 0.42) * 50;     // half width, in 0.01mm units
  var vi = 0, ii = 0, si = 0;
  var nx = new Float32Array(2), px = new Float32Array(2);

  for (var li = 0; li < layers.length; li++) {
    var L = layers[li];
    var ztop = L[0];
    var zlow = ztop - Math.round((L[5] || 0.2) * 85);
    layerSeg[li] = si;
    for (var pi = L[1]; pi < L[1] + L[2]; pi++) {
      var t = polys[pi * 3], s = polys[pi * 3 + 1], n = polys[pi * 3 + 2];
      var tool = polyTool ? polyTool[pi] : 0;
      var base = vi;
      for (i = 0; i < n; i++) {
        var x = pts[(s + i) * 2], y = pts[(s + i) * 2 + 1];
        // Miter normal: average the incoming and outgoing segment normals so
        // corners close instead of leaving a wedge-shaped gap.
        var ax = 0, ay = 0;
        if (i > 0) {
          var dx = x - pts[(s + i - 1) * 2], dy = y - pts[(s + i - 1) * 2 + 1];
          var d = Math.hypot(dx, dy) || 1; ax += -dy / d; ay += dx / d;
        }
        if (i < n - 1) {
          var ex = pts[(s + i + 1) * 2] - x, ey = pts[(s + i + 1) * 2 + 1] - y;
          var e = Math.hypot(ex, ey) || 1; ax += -ey / e; ay += ex / e;
        }
        var m = Math.hypot(ax, ay);
        if (m < 1e-4) { ax = 1; ay = 0; m = 1; }
        // 1/|sum| is the standard miter extension; clamp so a hairpin does not
        // fire a spike halfway across the plate.
        var sc = Math.min(2.4, 2 / m) * hw;
        ax = ax / m * sc; ay = ay / m * sc;

        vPos[vi * 3] = x + ax; vPos[vi * 3 + 1] = y + ay; vPos[vi * 3 + 2] = zlow;
        vPos[vi * 3 + 3] = x;  vPos[vi * 3 + 4] = y;      vPos[vi * 3 + 5] = ztop;
        vPos[vi * 3 + 6] = x - ax; vPos[vi * 3 + 7] = y - ay; vPos[vi * 3 + 8] = zlow;
        // A point is shared by two segments; take the one ENDING here so the
        // colour changes at the same place the slowdown starts.
        var sv = spd[Math.min(si + Math.max(i - 1, 0), spd.length - 1)];
        vType[vi] = t; vType[vi + 1] = t; vType[vi + 2] = t;
        vSpd[vi] = sv; vSpd[vi + 1] = sv; vSpd[vi + 2] = sv;
        vTool[vi] = tool; vTool[vi + 1] = tool; vTool[vi + 2] = tool;
        vi += 3;

        if (i > 0) {
          var a = base + (i - 1) * 3, b = base + i * 3;
          index[ii++] = a;     index[ii++] = b;     index[ii++] = a + 1;
          index[ii++] = a + 1; index[ii++] = b;     index[ii++] = b + 1;
          index[ii++] = a + 1; index[ii++] = b + 1; index[ii++] = a + 2;
          index[ii++] = a + 2; index[ii++] = b + 1; index[ii++] = b + 2;
          var lx = (x - pts[(s + i - 1) * 2]) / 100;
          var ly = (y - pts[(s + i - 1) * 2 + 1]) / 100;
          segLen[si] = Math.hypot(lx, ly);
          segEnd[si * 3] = x / 100; segEnd[si * 3 + 1] = y / 100;
          segEnd[si * 3 + 2] = ztop / 100;
          segLayer[si] = li;
          segTool[si] = tool;
          si++;
        }
      }
    }
  }
  layerSeg[layers.length] = si;

  // Time: each layer's own duration, distributed inside it by extruded length.
  var cum = 0;
  for (li = 0; li < layers.length; li++) {
    var a0 = layerSeg[li], a1 = layerSeg[li + 1], tot = 0;
    for (k = a0; k < a1; k++) { tot += segLen[k]; }
    var dur = layers[li][3];
    for (k = a0; k < a1; k++) {
      segCum[k] = cum;
      cum += tot > 0 ? dur * segLen[k] / tot : 0;
    }
  }
  segCum[si] = cum;

  var g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Int16BufferAttribute(vPos, 3));
  g.setAttribute('aType', new THREE.Uint8BufferAttribute(vType, 1));
  g.setAttribute('aSpeed', new THREE.Uint8BufferAttribute(vSpd, 1));
  g.setAttribute('aTool', new THREE.Uint8BufferAttribute(vTool, 1));
  g.setIndex(new THREE.BufferAttribute(index, 1));
  g.boundingSphere = new THREE.Sphere(
    new THREE.Vector3(128, 128, 128), 400);   // set by hand: positions are raw int16

  return {raw:raw, geom:g, nSeg:si, segEnd:segEnd, segCum:segCum,
          segLayer:segLayer, layerSeg:layerSeg, total:cum,
          segSpeed:spd, segTool:segTool, layers:layers};
}

function mountJob(job) {
  if (jobMesh) { scene.remove(jobMesh); scene.remove(ghostMesh); jobGeom.dispose(); }
  jobGeom = job.geom;
  ghostMesh = new THREE.Mesh(jobGeom, makeMaterial(0.86, richShading));
  ghostMesh.material.polygonOffset = true;
  ghostMesh.material.polygonOffsetFactor = 2;
  ghostMesh.material.polygonOffsetUnits = 2;
  ghostMesh.frustumCulled = false;
  ghostMesh.visible = false;
  jobMesh = new THREE.Mesh(jobGeom, makeMaterial(0.0, richShading));
  jobMesh.frustumCulled = false;
  scene.add(ghostMesh); scene.add(jobMesh);
  nozzle.visible = true; gantry.visible = true;
  JOB = job;
  applyVisibility();
  var bb = job.raw.bbox;
  shadowPlane.geometry.dispose();
  shadowPlane.geometry = new THREE.PlaneGeometry(
    (bb[2] - bb[0]) * 1.5 + 30, (bb[3] - bb[1]) * 1.5 + 30);
  shadowPlane.position.set((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, 0.12);
  shadowPlane.visible = true;
  frameJob(job);
}

function frameJob(job) {
  var b = job.raw.bbox, z = job.layers[job.layers.length - 1][0] / 100;
  var w = Math.max(b[2] - b[0], b[3] - b[1], z * 1.2, 40);
  cam.tx = (b[0] + b[2]) / 2;
  cam.ty = (b[1] + b[3]) / 2;
  // Bed-drop keeps the action at the nozzle near z=0, so the target sits low
  // and fixed. The radius has a floor: framing tightly on a small part cropped
  // the enclosure out entirely and the machine stopped reading as a machine.
  if (viewMode === 'machine') {
    machineCamera(doorOpen);
  } else {
    cam.tz = machineMotion ? 8 : z * 0.45;
    cam.r = Math.max(w * 2.55, machineMotion ? 410 : 320);
  }
  headScale = Math.max(0.42, Math.min(1.0, w / 170));
  nozzle.scale.setScalar(headScale);
  gantry.scale.set(1, headScale, headScale);
  gantry.visible = true;
  if (yRails) { yRails.visible = true; }
  if (!(viewMode === 'machine' && doorOpen)) { cam.theta = -0.72; cam.phi = 1.06; }
}

// \u2500\u2500 playback state \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var SPEEDS = [
  {v:1, l:'1\u00d7'}, {v:50, l:'50\u00d7'}, {v:250, l:'250\u00d7'},
  {v:1000, l:'1k\u00d7'}, {v:4000, l:'4k\u00d7'}, {v:15000, l:'15k\u00d7'}
];
var play = {on:false, t:0, speed:1000, seg:0, last:0, scrubbing:false};
var visible = new Array(N_TYPE).fill(true);
var machineMotion = true;
var richShading = true, autoQualityDone = false;
var colorMode = 'feature';
var COLOR_MODE_ID = {feature: 0, speed: 1, filament: 2};
var layerFilCum = null;

function segAtTime(t) {
  var lo = 0, hi = JOB.nSeg, c = JOB.segCum;
  while (lo < hi) {
    var mid = (lo + hi) >> 1;
    if (c[mid] <= t) { lo = mid + 1; } else { hi = mid; }
  }
  return Math.max(0, lo - 1);
}

function setSeg(seg) {
  seg = Math.max(0, Math.min(JOB.nSeg, seg));
  play.seg = seg;
  jobGeom.setDrawRange(0, seg * 12);
  if (seg > 0) {
    var i = (seg - 1) * 3;
    var px = JOB.segEnd[i], py = JOB.segEnd[i + 1], zTop = JOB.segEnd[i + 2];
    var oy = machineBounds ? machineBounds.oy : py;
    if (PRINTERS[printerId].bedslinger) {
      // A bed-slinger is the other machine entirely: the BED travels in Y and
      // the gantry climbs in Z. Replaying a P1S's motion on it would be the
      // same lie as drawing it with a door.
      var slide = machineMotion ? py - oy : 0;
      bedGroup.position.set(0, -slide, 0);
      jobMesh.position.set(0, -slide, 0);
      ghostMesh.position.set(0, -slide, 0);
      nozzle.position.set(px, py - slide, zTop);
      gantry.position.y = py - slide;
      gantry.position.z = zTop + 44 * headScale;
    } else {
      // The P1S: the gantry is fixed and the BED descends, so the nozzle holds
      // one height and everything printed sinks away from it.
      var drop = machineMotion ? zTop : 0;
      bedGroup.position.set(0, 0, -drop);
      jobMesh.position.set(0, 0, -drop);
      ghostMesh.position.set(0, 0, -drop);
      nozzle.position.set(px, py, zTop - drop);
      gantry.position.y = py;
      gantry.position.z = zTop - drop + 44 * headScale;
    }
    if (yRails) { yRails.position.z = gantry.position.z; }
  }
  updateAMS(seg);
}

function tick(now) {
  if (JOB && play.on && !play.scrubbing) {
    var dt = play.last ? Math.min((now - play.last) / 1000, 0.1) : 0;
    play.t += dt * play.speed;
    if (play.t >= JOB.total) { play.t = JOB.total; setPlaying(false); }
    setSeg(segAtTime(play.t));
  }
  play.last = now;
  if (JOB) { refreshReadout(); }
  updateCamera(now);
  setResolution(now);
  updateDoor();
  updateCutaway();
  if (jobMesh) {
    jobMesh.material.uniforms.uEye.value.copy(camera.position);
    ghostMesh.material.uniforms.uEye.value.copy(camera.position);
  }
  renderer.render(scene, camera);
}

function setPlaying(on) {
  play.on = on;
  $('playicon').innerHTML = on
    ? '<path d="M3 1.5h4v13H3zM9 1.5h4v13H9z"/>'
    : '<path d="M3 1.5v13l11-6.5z"/>';
  $('play').setAttribute('title', on ? 'Pause (space)' : 'Play (space)');
}

// \u2500\u2500 readout \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var lastPaint = 0, _lastFeat = null;
function hms(s) {
  s = Math.max(0, Math.round(s));
  var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h ? h + 'h ' + String(m).padStart(2, '0') + 'm' : m + 'm ' + String(s % 60).padStart(2, '0') + 's';
}
function refreshReadout(force) {
  var now = performance.now();
  if (!force && now - lastPaint < 90) { return; }
  lastPaint = now;
  var seg = play.seg, li = seg > 0 ? JOB.segLayer[seg - 1] : 0;
  var L = JOB.layers[li];
  $('r-layer').innerHTML = (seg ? li + 1 : 0) + ' <small>/ ' + JOB.layers.length + '</small>';
  $('r-z').innerHTML = (seg ? (L[0] / 100).toFixed(2) : '0.00') + ' <small>mm</small>';
  $('r-el').innerHTML = hms(play.t);
  $('r-rem').innerHTML = hms(JOB.total - play.t);
  var a0 = JOB.layerSeg[li], a1 = JOB.layerSeg[li + 1];
  var fil = layerFilCum[li] + (L[4] * ((seg - a0) / Math.max(1, a1 - a0)));
  $('r-fil').innerHTML = grams(fil).toFixed(1) + ' <small>g</small>';
  var v = seg > 0 ? JOB.segSpeed[seg - 1] : 0;
  $('r-spd').innerHTML = v + ' <small>mm/s</small>';
  $('r-seg').textContent = seg.toLocaleString() + ' moves';
  var tIdx = seg > 0 ? typeOfSeg(seg - 1) : -1;
  var nf = $('nowfeat');
  nf.firstElementChild.style.background = tIdx >= 0 ? TYPE_COLOR[tIdx] : 'var(--faint)';
  var fname = tIdx >= 0 ? JOB.raw.types[tIdx] : null;
  $('r-feat').textContent = fname || 'idle';
  if (fname !== _lastFeat) {
    _lastFeat = fname;
    $('featnote').textContent = fname ? (TYPE_HELP[fname] || '') : 'Press play to start the job.';
  }
  paintAMS();
  $('lnum').textContent = seg ? li + 1 : 0;
  var pct = JOB.total ? play.t / JOB.total : 0;
  if (!play.scrubbing) { $('scrub').value = Math.round(pct * 1000); }
  $('scrub').style.setProperty('--pct', (pct * 100).toFixed(1) + '%');
}

// Segment -> feature type. Polylines are stored in draw order, so a walk of
// the layer's polys finds it without another per-segment array.
var _polys = null;
function typeOfSeg(seg) {
  var li = JOB.segLayer[seg], L = JOB.layers[li], at = JOB.layerSeg[li];
  for (var pi = L[1]; pi < L[1] + L[2]; pi++) {
    var n = _polys[pi * 3 + 2] - 1;
    if (seg < at + n) { return _polys[pi * 3]; }
    at += n;
  }
  return 0;
}

// \u2500\u2500 ui \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
function el(tag, cls, html) {
  var e = document.createElement(tag);
  if (cls) { e.className = cls; }
  if (html != null) { e.innerHTML = html; }
  return e;
}

var INDEX = window.__PRINT_INDEX || [];
var currentId = null;

// How many cards are fully inside the list's own viewport. Measured rather than
// assumed: the card height is not a constant the JS should be repeating.
function platesOutOfView() {
  var host = $('jobs');
  if (!host) { return 0; }
  var br = host.getBoundingClientRect(), n = 0;
  var cards = host.getElementsByClassName('job');
  for (var i = 0; i < cards.length; i++) {
    var r = cards[i].getBoundingClientRect();
    if (r.top < br.top - 1 || r.bottom > br.bottom + 1) { n++; }
  }
  return n;
}

function updatePlateMore() {
  var btn = $('platemore'), host = $('jobs');
  if (!btn || !host) { return; }
  var hidden = platesOutOfView();
  btn.hidden = hidden === 0;
  if (hidden) {
    var atEnd = host.scrollTop + host.clientHeight >= host.scrollHeight - 2;
    btn.textContent = (atEnd ? '\u2191 ' : '\u2193 ') + hidden + ' more plate' +
      (hidden === 1 ? '' : 's') + ' \u2014 scroll the list';
  }
}

function paintJobList() {
  var host = $('jobs');
  host.innerHTML = '';
  host.removeAttribute('data-at');   // or a stale index survives a re-render
  var current = null;
  INDEX.forEach(function (j, i) {
    var b = el('button', 'job');
    b.type = 'button';
    b.setAttribute('aria-current', String(j.id === currentId));
    if (j.id === currentId) { host.setAttribute('data-at', i + 1); current = b; }
    var tags = '';
    if (j.toolChanges) { tags += ' <span class="tagmc">' + (j.filamentByTool || []).length
      + ' FILAMENTS</span>'; }
    if (j.needsSupport) { tags += ' <span class="tagsup">SUPPORT</span>'; }
    if (j.segments > 400000) { tags += ' <span class="taghv">HEAVY</span>'; }
    b.innerHTML = '<span class="n">' + j.name + '</span>' + tags +
      '<span class="m"><span><b>' + j.layers + '</b> layers</span>' +
      '<span><b>' + j.maxZ.toFixed(0) + '</b> mm</span>' +
      '<span><b>' + (j.segments / 1000).toFixed(0) + 'k</b> moves</span>' +
      '<span><b>' + j.filamentG.toFixed(0) + '</b> g</span></span>';
    b.addEventListener('click', function () { loadJob(j.id); });
    host.appendChild(b);
  });
  // Pick a plate near the bottom of eleven and the list must not leave it
  // offscreen -- "which one am I on" should never need a scroll to answer.
  if (current && current.scrollIntoView) {
    current.scrollIntoView({block: 'nearest'});
  }
  // Says where you are in the list, so eleven plates behind a scrollbar read
  // as eleven plates rather than as however many happen to fit.
  var pc = $('platecount');
  if (pc) { pc.textContent = (host.getAttribute('data-at') || '1') + ' / ' + INDEX.length; }
  updatePlateMore();
  $('buildchip').textContent = INDEX.length + ' plates \u00b7 ' +
    INDEX.reduce(function (a, j) { return a + j.segments; }, 0).toLocaleString() +
    ' extrusion moves on file';
}

var MAGMA = [
  [-0.002136,-0.000750,-0.005386],[0.251661,0.677523,2.494027],
  [8.353717,-3.577720,0.314468],[-27.668733,14.264731,-13.649213],
  [52.176140,-27.943606,12.944169],[-50.768525,29.046583,4.234153],
  [18.655705,-11.489774,-5.601962]];

var FIL_AREA_MM2 = Math.PI * Math.pow(1.75 / 2, 2);   // 1.75mm filament

function density() {
  var m = MATERIALS.filter(function (x) { return x.n === materialId; })[0];
  return m && m.rho ? m.rho : 1.24;
}

function grams(mm) {
  return mm * FIL_AREA_MM2 / 1000 * density();
}

function speedColor(v) {
  if (!JOB) { return '#888'; }
  var lo = JOB.raw.speedMin, hi = JOB.raw.speedMax;
  var f = Math.min(1, Math.max(0, (v - lo) / Math.max(hi - lo, 1)));
  var t = 0.92 + (0.28 - 0.92) * f;      // same clamped, reversed mapping
  var c = [0, 0, 0];
  for (var k = 0; k < 3; k++) {
    var acc = 0;
    for (var i = 6; i >= 0; i--) { acc = acc * t + MAGMA[i][k]; }
    c[k] = Math.round(Math.min(1, Math.max(0, acc)) * 255);
  }
  return 'rgb(' + c[0] + ',' + c[1] + ',' + c[2] + ')';
}

function paintSpeedPanel() {
  var s = JOB.raw.speedByType, lo = JOB.raw.speedMin, hi = JOB.raw.speedMax;
  var rows = Object.keys(s).sort(function (a, b) { return s[a].med - s[b].med; })
    .map(function (n) {
      var e = s[n];
      var range = e.min === e.max ? e.med + '' : e.min + '\u2013' + e.max;
      return '<tr><td><span class="sw" style="background:' + speedColor(e.med) +
        '"></span>' + n + '</td><td>' + range + '</td></tr>';
    }).join('');
  $('speedpanel').innerHTML =
    '<div class="ramp"></div><div class="ends"><span>' + lo +
    ' mm/s \u00b7 slow</span><span>fast \u00b7 ' + hi + ' mm/s</span></div>' +
    '<table>' + rows + '</table>';
}

function paintLegend() {
  var host = $('legend');
  host.innerHTML = '';
  var counts = JOB.raw.segmentsByType;
  JOB.raw.types.forEach(function (name, i) {
    var c = counts[name];
    if (!c) { return; }
    var b = el('button', 'leg');
    b.type = 'button';
    b.setAttribute('aria-pressed', String(visible[i]));
    b.title = TYPE_HELP[name] || '';
    b.innerHTML = '<span class="sw" style="background:' + TYPE_COLOR[i] + '"></span>' +
      '<span class="lb">' + name + '</span>' +
      '<span class="ct">' + (c / 1000).toFixed(1) + 'k</span>';
    b.addEventListener('click', function () {
      visible[i] = !visible[i];
      b.setAttribute('aria-pressed', String(visible[i]));
      applyVisibility();
    });
    host.appendChild(b);
  });
}

function setQuality(rich) {
  richShading = rich;
  [[jobMesh, 0.0], [ghostMesh, 0.86]].forEach(function (pair) {
    var m = pair[0];
    if (!m) { return; }
    var old = m.material;
    m.material = makeMaterial(pair[1], rich);
    m.material.uniforms.uVis.value = old.uniforms.uVis.value;
    m.material.uniforms.uMode.value = old.uniforms.uMode.value;
    m.material.uniforms.uSpd.value.copy(old.uniforms.uSpd.value);
    m.material.polygonOffset = old.polygonOffset;
    m.material.polygonOffsetFactor = old.polygonOffsetFactor;
    m.material.polygonOffsetUnits = old.polygonOffsetUnits;
    old.dispose();
  });
  var b = $('quality');
  if (b) {
    b.setAttribute('aria-pressed', String(rich));
    b.textContent = rich ? 'Detail: high' : 'Detail: fast';
  }
}

// One automatic step down, never up: a device that cannot hold a readable
// frame rate on the heaviest plate should not be asked to render two pow()
// calls per fragment for a highlight. Measured over real frames after a job
// loads, and only ever done once so it cannot oscillate.
function autoQuality() {
  if (autoQualityDone || !richShading) { return; }
  autoQualityDone = true;
  var n = 0, t0 = performance.now();
  (function sample() {
    n++;
    if (performance.now() - t0 < 1600) { requestAnimationFrame(sample); return; }
    var fps = n / ((performance.now() - t0) / 1000);
    if (fps < 22) {
      setQuality(false);
      var note = $('legnote');
      if (note) {
        note.innerHTML = '<b style="color:var(--warn)">Detail stepped down to keep '
          + 'the frame rate readable (' + fps.toFixed(0) + ' fps measured).</b> '
          + 'Put it back with Detail in the toolbar.<br>' + note.innerHTML;
      }
    }
  })();
}

// ── the AMS, as a thing that works ──────────────────────────────────────────
// It feeds the nozzle on every job, so none of this is conditional on the plate
// being multi-colour: a single-filament print is simply one slot doing all the
// work. What changes with a multi-colour plate is which slot is live and how
// much goes into the purge.
var amsSlots = [];          // [{tool, used_mm, total_mm, spool, core}]
var amsActive = 0;

// Cumulative filament per slot at every layer boundary, built once per job.
// Exact at each boundary because the exporter measured it there; only the layer
// currently being printed is estimated. Attributing by segment index instead --
// the first attempt -- charged slot 1 with 24.4 g against its real 17.0 g,
// because the purge is a lot of filament laid down over very few moves.
var filToolCum = null;

function buildFilamentCum(raw) {
  var rows = raw.filByToolLayer || [];
  var w = (raw.filamentByTool || [0]).length;
  filToolCum = [];
  var run = new Float64Array(w);
  filToolCum.push(Float64Array.from(run));
  for (var i = 0; i < rows.length; i++) {
    for (var t = 0; t < w; t++) { run[t] += rows[i][t] || 0; }
    filToolCum.push(Float64Array.from(run));
  }
}

function amsUsage(seg) {
  var used = new Float64Array(MAX_FILAMENT);
  if (!JOB || !filToolCum || seg <= 0) { return used; }
  var li = JOB.segLayer[seg - 1];
  var a0 = JOB.layerSeg[li], a1 = JOB.layerSeg[li + 1];
  var frac = (seg - a0) / Math.max(1, a1 - a0);
  var row = JOB.raw.filByToolLayer[li] || [];
  var base = filToolCum[li];
  for (var t = 0; t < used.length && t < base.length; t++) {
    used[t] = base[t] + (row[t] || 0) * frac;
  }
  return used;
}

function buildAMSState() {
  amsSlots = [];
  if (!JOB || !amsGroup) { return; }
  var totals = JOB.raw.filamentByTool || [];
  var n = Math.max(1, totals.length);
  for (var i = 0; i < n && i < MAX_FILAMENT; i++) {
    amsSlots.push({tool: i, used: 0, total: totals[i] || 0,
                   spool: amsGroup.userData.spools[i] || null,
                   core: amsGroup.userData.cores[i] || null});
  }
  // A spool the job never touches is not in the machine's way -- hide it, so
  // the four-slot box shows the filaments this plate actually needs.
  (amsGroup.userData.spools || []).forEach(function (m, i) {
    var on = i < amsSlots.length;
    if (m) { m.visible = on; }
    if (amsGroup.userData.cores[i]) { amsGroup.userData.cores[i].visible = on; }
  });
  paintAMS();
}

// A spool of filament is a coil: the outside radius falls as it empties. 1kg of
// PLA is about 320 m, which is what sets how little a 30g print visibly takes
// off -- and that is worth seeing rather than being told.
var SPOOL_FULL_MM = 320000, SPOOL_R_FULL = 99, SPOOL_R_CORE = 36;

function updateAMS(seg) {
  if (!amsSlots.length) { return; }
  var used = amsUsage(seg);
  amsActive = seg > 0 ? JOB.segTool[seg - 1] : 0;
  for (var i = 0; i < amsSlots.length; i++) {
    var sl = amsSlots[i];
    sl.used = used[sl.tool];
    if (sl.spool) {
      // Area on the coil falls linearly with length, so the radius goes as a
      // square root -- a spool does not shrink evenly as it empties.
      var left = Math.max(0, 1 - sl.used / SPOOL_FULL_MM);
      var r = Math.sqrt(SPOOL_R_CORE * SPOOL_R_CORE +
                        left * (SPOOL_R_FULL * SPOOL_R_FULL - SPOOL_R_CORE * SPOOL_R_CORE));
      // The cylinder's own axis is local Y, so the RADIUS is x and z and the
      // width is y. Scaling y here would have made the spool narrower instead
      // of emptier, and spinning x would have tumbled it end over end.
      var k = r / SPOOL_R_FULL;
      sl.spool.scale.set(k, 1, k);
      // Rotation is real too: one turn per circumference of filament pulled.
      sl.spool.rotation.y = -sl.used / (2 * Math.PI * r);
    }
  }
  paintFeed();
}

// The feed line from the live slot to the toolhead, in that slot's colour. On a
// single-colour job it simply never moves, which is exactly what the machine
// does.
function paintFeed() {
  if (!amsGroup || !amsGroup.userData.feed) { return; }
  var f = amsGroup.userData.feed;
  var col = FILAMENT[amsActive % FILAMENT.length];
  f.material.color.set(col);
  (amsGroup.userData.spools || []).forEach(function (m, i) {
    if (m) { m.material.emissive && m.material.emissive.setHex(i === amsActive ? 0x241a08 : 0x000000); }
  });
}

function paintAMS() {
  var host = $('amsslots');
  if (!host) { return; }
  var cap = (PRINTERS[printerId].ams || {}).slots || 0;
  host.innerHTML = '';
  amsSlots.forEach(function (sl, i) {
    var row = el('div', 'amsrow');
    row.setAttribute('data-active', String(i === amsActive));
    row.innerHTML = '<span class="sw" style="background:' + FILAMENT[i % FILAMENT.length] +
      '"></span><span class="lb">Slot ' + (i + 1) + '</span>' +
      '<span class="bar"><i style="width:' +
      (sl.total ? Math.min(100, sl.used / sl.total * 100).toFixed(1) : 0) + '%"></i></span>' +
      '<span class="g">' + grams(sl.used).toFixed(1) + ' g</span>';
    host.appendChild(row);
  });
  var note = $('amsnote');
  if (!note) { return; }
  if (amsSlots.length > cap && cap) {
    note.innerHTML = '<span class="amsover">This plate needs ' + amsSlots.length +
      ' filaments and one AMS holds ' + cap + '.</span> A second unit would have to be ' +
      'chained to print it as sliced.';
  } else if (amsSlots.length > 1) {
    var purge = (JOB.raw.filamentByType || {})['Wipe tower'] || 0;
    note.innerHTML = 'Every filament change wipes the old colour into the purge tower. ' +
      '<b>' + grams(purge).toFixed(1) + ' g</b> of this plate is purge \u2014 ' +
      (JOB.raw.toolChanges || 0) + ' changes.';
  } else {
    // The bar is progress through THIS plate's filament, which is what it
    // measures -- saying "off a full spool" while showing plate progress would
    // be two different numbers wearing the same label.
    var spoolPct = amsSlots[0] ? amsSlots[0].total / SPOOL_FULL_MM * 100 : 0;
    note.innerHTML = 'One filament, one slot \u2014 the bar is this plate\u2019s progress ' +
      'through it. The whole job is <b>' + spoolPct.toFixed(1) + '%</b> of a 1 kg spool.';
  }
}

function setDoor(open) {
  doorOpen = open;
  doorTarget = (doorGroup ? doorGroup.userData.sign : 1) * -1.92;   // ~110 degrees
  $('door').setAttribute('aria-pressed', String(open));
  $('door').textContent = open ? 'Close door' : 'Open door';
  // Opening the door is a request to see inside, so swing the camera round to
  // the front where the opening actually is.
  if (viewMode === 'machine') { machineCamera(open); }
}

function setViewMode(mode) {
  viewMode = mode;
  $('viewmode').textContent = mode === 'machine' ? 'View: machine' : 'View: chamber';
  $('viewmode').setAttribute('aria-pressed', String(mode === 'machine'));
  if (JOB) { frameJob(JOB); }
}

function setColorMode(mode) {
  colorMode = mode;
  Array.prototype.forEach.call($('modeswap').children, function (b) {
    b.setAttribute('aria-pressed', String(b.getAttribute('data-mode') === mode));
  });
  var speedy = mode === 'speed', fil = mode === 'filament';
  $('speedpanel').hidden = !speedy;
  $('legend').hidden = speedy || fil;
  $('legnote').innerHTML = speedy
    ? 'Feedrate straight out of the G-code. Brightest is slowest \u2014 the outer '
      + 'wall and the top surface, the parts a buyer actually sees. The dark, fast '
      + 'paths are infill nobody will ever look at.'
    : fil
    ? 'Every bead in the colour of the slot it came off. A single-filament plate '
      + 'is one colour throughout \u2014 that is not the viewer simplifying, it is '
      + 'the machine pulling from one spool all the way down.'
    : 'Click a type to hide it. Every colour here is the slicer\'s own '
      + '<span class="mono">;TYPE:</span> tag \u2014 nothing is inferred from the shape.';
  applyVisibility();
}

function applyVisibility() {
  [jobMesh, ghostMesh].forEach(function (m) {
    if (!m) { return; }
    var u = m.material.uniforms.uVis.value;
    for (var i = 0; i < 12; i++) { u[i] = visible[i] ? 1 : 0; }
    m.material.uniforms.uMode.value = COLOR_MODE_ID[colorMode] || 0;
    if (JOB) { m.material.uniforms.uSpd.value.set(JOB.raw.speedMin, JOB.raw.speedMax); }
  });
}

// \u2500\u2500 job loading \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
window.__JOB_LOADED = function (raw) {
  // Geometry build is synchronous and can take a second on the heaviest plate.
  // Yield first so the loading overlay actually paints before the main thread
  // locks -- otherwise the page looks frozen rather than busy.
  requestAnimationFrame(function () { requestAnimationFrame(function () {
    var job = buildJob(raw);
    _polys = b64(raw.polys, Int32Array);
    layerFilCum = new Float64Array(raw.layers.length + 1);
    for (var i = 0; i < raw.layers.length; i++) {
      layerFilCum[i + 1] = layerFilCum[i] + raw.layers[i][4];
    }
    mountJob(job);
    buildFilamentCum(raw);
    buildAMSState();
    $('ltot').textContent = '/ ' + raw.layers.length;
    _lastFeat = null;
    $('jobnote').textContent = raw.notes || '';
    paintLegend(); paintSpeedPanel(); paintJobList(); paintPrinter();
    setColorMode(colorMode);
    play.t = 0; setSeg(0); setPlaying(true);
    autoQuality();
    refreshReadout(true);
    loading.hidden = true;
  }); });
};

function loadJob(id) {
  if (id === currentId && JOB) { return; }
  currentId = id;
  loading.hidden = false;
  loading.firstChild.textContent = 'Loading ' +
    (INDEX.filter(function (j) { return j.id === id; })[0] || {name:id}).name;
  paintJobList();
  setPlaying(false);
  var s = document.createElement('script');
  s.src = 'jobs/' + id + '.js';
  s.onerror = function () {
    loading.innerHTML = '<div style="text-align:center;color:var(--bad)">' +
      'Could not load jobs/' + id + '.js</div>';
  };
  document.body.appendChild(s);
}

// \u2500\u2500 reference panes \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var printerId = 'p1s', materialId = 'PLA';

function paintPrinter() {
  var p = PRINTERS[printerId];
  var m = MATERIALS.filter(function (x) { return x.n === materialId; })[0];
  var opts = Object.keys(PRINTERS).map(function (k) {
    return '<option value="' + k + '"' + (k === printerId ? ' selected' : '') +
      '>' + PRINTERS[k].label + '</option>';
  }).join('');
  var custom = printerId === 'custom'
    ? '<h3>Build volume</h3>' +
      ['X','Y','Z'].map(function (ax, i) {
        return '<div class="frow"><label>' + ax + ' (mm)</label>' +
          '<input type="number" id="bv' + i + '" value="' + p.bed[i] +
          '" min="40" max="1200" step="5"></div>';
      }).join('')
    : '';
  // Two tables on purpose. The first is what actually produced the toolpath on
  // screen; the second is reference for a filament nothing here was sliced in.
  // Collapsing them into one would quietly imply the slice used the selected
  // material's numbers, which it did not.
  $('pane-printer').innerHTML =
    '<h3>Machine</h3><select id="psel" aria-label="Printer">' + opts + '</select>' +
    '<p style="margin-top:9px">' + p.note + '</p>' + custom +
    '<h3>What sliced this toolpath</h3><table class="kv">' +
    row('Build volume', p.bed[0] + ' \u00d7 ' + p.bed[1] + ' \u00d7 ' + p.bed[2] + ' mm') +
    row('Motion', p.motion) + row('Chamber', p.chamber) +
    row('Enclosed', p.enclosed ? 'Yes' : 'No') +
    row('AMS', p.ams ? p.ams.slots + ' slots, ' + p.ams.w + ' \u00d7 ' + p.ams.d +
        ' \u00d7 ' + p.ams.h + ' mm, ' + p.ams.kg.toFixed(1) + ' kg' : 'None fitted') +
    row('Nozzle', p.nozzle.toFixed(1) + ' mm brass') +
    row('Layer height', (JOB ? JOB.raw.layerHeight : 0.2).toFixed(2) + ' mm') +
    row('First layer', (JOB && JOB.raw.firstLayerHeight ?
        JOB.raw.firstLayerHeight : 0.2).toFixed(2) + ' mm') +
    row('Extrusion width', (JOB ? JOB.raw.beadWidth : 0.42).toFixed(2) + ' mm') +
    row('Perimeters', '2') +
    row('Top / bottom layers', '5 / 4') +
    row('Infill', '15% grid') +
    row('Support threshold', '45\u00b0') +
    row('Filament sliced', 'PLA, 220 \u00b0C nozzle') +
    row('Bed', '55 \u00b0C, textured PEI') +
    '</table>' +
    '<h3>Filament reference \u2014 ' + m.n + '</h3>' +
    '<p style="margin:0 0 8px">Typical ranges for comparison. Nothing on screen ' +
    'was sliced in this filament unless it says PLA above.</p>' +
    '<table class="kv">' +
    row('Nozzle', m.noz + ' \u00b0C') + row('Bed', m.bed + ' \u00b0C') +
    row('Dry before use', m.dry) + row('Plate', m.plate) +
    '</table>' +
    '<div class="caveat">Changing the machine redraws the chamber and the volume ' +
    'row. It does <b>not</b> re-slice \u2014 every toolpath here came out of the P1S ' +
    'profile above. Re-slicing lives in <span class="mono">tools/virtual_printer.py' +
    '</span>.</div>' +
    '<div class="caveat"><b>What is taken from Bambu\u2019s own documentation:</b> ' +
    'outside dimensions, build volume, AMS size, the 2.7-inch 192\u00d764 screen, ' +
    'the fixed gantry over a bed that descends, a Z axis of <b>three</b> lead ' +
    'screws turned together by one stepper through a belt under the base, three ' +
    'Z sliders carrying the bed, CoreXY with an independent belt per motor, the ' +
    '5V chamber LED on the <b>left</b> beam beside the chamber camera, and a ' +
    'toolhead of front/middle/rear housings with the part-cooling fan in the ' +
    'front one, a filament cutter, and an all-in-one hotend. No LiDAR \u2014 that ' +
    'is the X1 Carbon.<br><b>What is drawn rather than documented:</b> where the ' +
    'three lead screws sit around the base, and the toolhead\u2019s exact ' +
    'proportions \u2014 Bambu publishes neither, so these are placed to read ' +
    'correctly, not measured. The AMS spool colours are illustrative; nothing ' +
    'here is reading your machine.</div>';
  $('psel').addEventListener('change', function (e) {
    printerId = e.target.value;
    buildChamber(PRINTERS[printerId].bed);
    paintPrinter();
  });
  ['bv0','bv1','bv2'].forEach(function (id, i) {
    var inp = $(id);
    if (!inp) { return; }
    inp.addEventListener('change', function () {
      var v = Math.max(40, Math.min(1200, +inp.value || 256));
      PRINTERS.custom.bed[i] = v; inp.value = v;
      buildChamber(PRINTERS.custom.bed);
      paintPrinter();
    });
  });
}
function row(k, v) { return '<tr><td>' + k + '</td><td>' + v + '</td></tr>'; }

function paintMaterial() {
  $('pane-material').innerHTML =
    '<h3>Typical starting points</h3>' +
    '<p>Pick one to load it into the profile table. These are conservative ' +
    'ranges, not calibrated numbers \u2014 Scott\'s own tuned Bambu Studio profiles ' +
    'beat every row here, and a real print should use those.</p>' +
    '<table class="mat"><thead><tr><th>Filament</th><th>Nozzle</th><th>Bed</th>' +
    '<th>Dry</th></tr></thead><tbody>' +
    MATERIALS.map(function (m) {
      return '<tr data-m="' + m.n + '" data-sel="' + (m.n === materialId ? 1 : 0) +
        '"><td>' + m.n + '</td><td>' + m.noz + '</td><td>' + m.bed + '</td><td>' +
        m.dry + '</td></tr>';
    }).join('') + '</tbody></table>' +
    '<h3>Why it matters here</h3>' +
    '<p>Material does not change the toolpath \u2014 the same G-code prints in PLA or ' +
    'PETG. It changes temperature, cooling and speed, which is why the same file ' +
    'can come out clean in one filament and stringy in another. This view shows ' +
    'geometry; the filament column is where the rest of the answer lives.</p>' +
    '<div class="caveat"><b>Wet filament is the single most common cause of a bad ' +
    'surface.</b> Stringing, popping and micro-voids are moisture, not slicing. ' +
    'Nothing on this page can show that.</div>' +
    '<h3>Selected</h3>' +
    '<p id="matuse"></p>';
  var m = MATERIALS.filter(function (x) { return x.n === materialId; })[0];
  $('matuse').textContent = m.n + ' \u2014 ' + m.use + '. Recommended plate: ' + m.plate + '.';
  Array.prototype.forEach.call($('pane-material').querySelectorAll('tbody tr'),
    function (tr) {
      tr.addEventListener('click', function () {
        materialId = tr.getAttribute('data-m');
        paintMaterial(); paintPrinter();
      });
    });
}

// \u2500\u2500 wiring \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
function initUI() {
  // The hint has to follow the list, not just the render: scrolling it, or a
  // window resize changing how many cards fit, both change the answer.
  $('jobs').addEventListener('scroll', updatePlateMore, {passive: true});
  window.addEventListener('resize', updatePlateMore);
  $('platemore').addEventListener('click', function () {
    var host = $('jobs');
    var atEnd = host.scrollTop + host.clientHeight >= host.scrollHeight - 2;
    host.scrollTo({top: atEnd ? 0 : host.scrollTop + host.clientHeight * 0.85,
                   behavior: 'smooth'});
  });
  SPEEDS.forEach(function (s) {
    var b = el('button', null, s.l);
    b.type = 'button';
    b.setAttribute('aria-pressed', String(s.v === play.speed));
    b.addEventListener('click', function () {
      play.speed = s.v;
      Array.prototype.forEach.call($('speeds').children, function (c) {
        c.setAttribute('aria-pressed', String(c === b));
      });
    });
    $('speeds').appendChild(b);
  });

  $('play').addEventListener('click', function () { if (JOB) { setPlaying(!play.on); } });
  $('restart').addEventListener('click', function () {
    if (!JOB) { return; }
    play.t = 0; setSeg(0); refreshReadout(true);
  });

  var sc = $('scrub');
  sc.addEventListener('pointerdown', function () { play.scrubbing = true; });
  ['pointerup','pointercancel','blur'].forEach(function (t) {
    sc.addEventListener(t, function () { play.scrubbing = false; });
  });
  sc.addEventListener('input', function () {
    if (!JOB) { return; }
    play.scrubbing = true;
    play.t = (+sc.value / 1000) * JOB.total;
    setSeg(segAtTime(play.t));
    refreshReadout(true);
  });

  Array.prototype.forEach.call(document.querySelectorAll('[data-view]'),
    function (b) {
      b.addEventListener('click', function () {
        var v = b.getAttribute('data-view');
        if (v === 'top') { cam.phi = 0.08; cam.theta = -Math.PI / 2; }
        else if (v === 'front') { cam.phi = 1.5; cam.theta = -Math.PI / 2; }
        else { cam.phi = 1.06; cam.theta = -0.72; }
      });
    });

  Array.prototype.forEach.call($('modeswap').children, function (b) {
    b.addEventListener('click', function () {
      setColorMode(b.getAttribute('data-mode'));
    });
  });

  $('door').addEventListener('click', function () {
    setDoor(!doorOpen);
  });
  $('viewmode').addEventListener('click', function () {
    setViewMode(viewMode === 'machine' ? 'chamber' : 'machine');
  });

  $('quality').addEventListener('click', function () {
    setQuality($('quality').getAttribute('aria-pressed') !== 'true');
  });

  $('motion').addEventListener('click', function () {
    machineMotion = $('motion').getAttribute('aria-pressed') !== 'true';
    $('motion').setAttribute('aria-pressed', String(machineMotion));
    $('motion').textContent = machineMotion ? 'Bed drops' : 'Part grows';
    if (JOB) { frameJob(JOB); setSeg(play.seg); }
  });

  $('ghost').addEventListener('click', function () {
    var on = $('ghost').getAttribute('aria-pressed') !== 'true';
    $('ghost').setAttribute('aria-pressed', String(on));
    if (ghostMesh) { ghostMesh.visible = on; }
  });

  Array.prototype.forEach.call(document.querySelectorAll('[data-pane]'),
    function (b) {
      b.addEventListener('click', function () {
        Array.prototype.forEach.call(document.querySelectorAll('[data-pane]'),
          function (o) {
            var sel = o === b;
            o.setAttribute('aria-selected', String(sel));
            $('pane-' + o.getAttribute('data-pane')).hidden = !sel;
          });
      });
    });

  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') { return; }
    if (e.code === 'Space') { e.preventDefault(); if (JOB) { setPlaying(!play.on); } }
    if (!JOB) { return; }
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      var li = play.seg > 0 ? JOB.segLayer[play.seg - 1] : 0;
      var t = Math.max(0, Math.min(JOB.layers.length - 1, li + (e.key === 'ArrowRight' ? 1 : -1)));
      var s = JOB.layerSeg[t + 1] - 1;
      play.t = JOB.segCum[Math.max(0, s)];
      setSeg(s); refreshReadout(true); setPlaying(false);
    }
  });
}

// \u2500\u2500 boot \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
if (!window.THREE) {
  loading.innerHTML = '<div style="text-align:center;color:var(--bad);padding:0 24px">' +
    'three.js did not load. This page needs cdnjs reachable.</div>';
} else if (!INDEX.length) {
  loading.innerHTML = '<div style="text-align:center;color:var(--bad)">' +
    'No jobs found \u2014 jobs/index.js is missing.</div>';
} else {
  initScene(); initUI(); paintMaterial(); paintPrinter(); paintJobList();
  loadJob(INDEX[0].id);
}
})();
