/* Virtual P1S Chamber -- replays real sliced G-code.
   Data comes from tools/gcode_viewer_data.py; geometry and playback are here. */
(function () {
'use strict';

// \u2500\u2500 palette \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
// Index order must match TYPES in tools/gcode_viewer_data.py.
var TYPE_COLOR = ['#ff7a45','#ffc04d','#4fd2ff','#6a7285','#c9d64f','#9be36a',
                  '#3affc8','#7b5cd6','#a98cf0','#5a6070','#d8d8d8','#d8d8d8'];
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
  'Other':'An untagged move.'
};

// \u2500\u2500 printers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
// Only profiles with a documented build volume are listed. "Custom" exists so a
// machine can be dialled in without editing this file; nothing here is guessed.
var PRINTERS = {
  p1s: {label:'Bambu Lab P1S', bed:[256,256,256], enclosed:true, nozzle:0.4,
        motion:'CoreXY', chamber:'Passive, ~40 \u00b0C', plate:'Textured PEI',
        note:'The machine every job on this page was sliced for.'},
  a2l: {label:'Bambu Lab A2L', bed:[330,320,325], enclosed:false, nozzle:0.4,
        motion:'Bedslinger', chamber:'None (open frame)', plate:'\u2014',
        note:'Larger format, AMS Lite and AMS 2 Pro compatible. Chamber redraws; the toolpath was still sliced for the P1S.'},
  custom:{label:'Custom', bed:[256,256,256], enclosed:true, nozzle:0.4,
        motion:'\u2014', chamber:'\u2014', plate:'\u2014',
        note:'Enter a build volume to redraw the chamber. This is the hook for the rest of the market \u2014 it changes what is drawn, not how the file was sliced.'}
};

// Starting points only. Scott's own tuned profiles override every one of these.
var MATERIALS = [
  {n:'PLA',      noz:'190\u2013230', bed:'35\u201360',  dry:'45 \u00b0C / 6\u20138 h',  plate:'Smooth PEI', use:'Decorative, sharpest detail, lowest failure rate'},
  {n:'Silk PLA', noz:'200\u2013230', bed:'35\u201360',  dry:'45 \u00b0C / 6\u20138 h',  plate:'Smooth PEI', use:'Premium metallic finish, no post-processing'},
  {n:'PETG',     noz:'230\u2013260', bed:'70\u201390',  dry:'65 \u00b0C / 6\u20138 h',  plate:'Textured PEI', use:'Functional, moisture and heat resistant'},
  {n:'TPU',      noz:'200\u2013240', bed:'30\u201350',  dry:'\u2014',              plate:'Textured PEI', use:'Flexible \u2014 koozies, grips, gaskets'},
  {n:'ABS',      noz:'240\u2013270', bed:'90\u2013100', dry:'60 \u00b0C / 4\u20136 h',  plate:'Textured PEI', use:'Heat resistant; needs the enclosure'},
  {n:'ASA',      noz:'240\u2013280', bed:'90\u2013100', dry:'60 \u00b0C / 4\u20136 h',  plate:'Textured PEI', use:'Outdoor, UV stable; needs the enclosure'},
  {n:'PA / PC',  noz:'270\u2013300', bed:'90\u2013100', dry:'80 \u00b0C / 12+ h',  plate:'Textured PEI', use:'Engineering parts; wet filament ruins these'}
];

// \u2500\u2500 dom \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var $ = function (id) { return document.getElementById(id); };
var stage = $('stage'), loading = $('loading');

// \u2500\u2500 three.js scene \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var renderer, scene, camera, chamber, plate, grid, nozzle, gantry;
var jobMesh = null, ghostMesh = null, jobGeom = null;
var cam = {theta: -0.72, phi: 1.06, r: 430, tx: 0, ty: 0, tz: 90};
var headScale = 1;

function initScene() {
  renderer = new THREE.WebGLRenderer({antialias:true, powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x08090b, 1);
  stage.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x08090b, 700, 1600);
  camera = new THREE.PerspectiveCamera(38, 1, 1, 3000);
  camera.up.set(0, 0, 1);

  buildChamber(PRINTERS.p1s.bed);

  var ncone = new THREE.Mesh(
    new THREE.ConeGeometry(2.6, 9, 14),
    new THREE.MeshBasicMaterial({color:0xff8a2b}));
  ncone.rotation.x = Math.PI;           // tip down, Z-up world
  ncone.position.z = 4.5;
  var nblock = new THREE.Mesh(
    new THREE.BoxGeometry(11, 9, 11),
    new THREE.MeshBasicMaterial({color:0x22252c}));
  nblock.position.z = 13;
  var nedge = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(11, 9, 11)),
    new THREE.LineBasicMaterial({color:0x4a505e}));
  nedge.position.z = 13;
  nozzle = new THREE.Group();
  nozzle.add(ncone); nozzle.add(nblock); nozzle.add(nedge);
  nozzle.visible = false;
  scene.add(nozzle);

  onResize();
  window.addEventListener('resize', onResize);
  attachOrbit(renderer.domElement);
  renderer.setAnimationLoop(tick);
}

function buildChamber(bed) {
  [chamber, plate, grid, gantry].forEach(function (o) {
    if (o) { scene.remove(o); }
  });
  var X = bed[0], Y = bed[1], Z = bed[2];

  plate = new THREE.Mesh(
    new THREE.BoxGeometry(X, Y, 6),
    new THREE.MeshBasicMaterial({color:0x181b21}));
  plate.position.set(X / 2, Y / 2, -3.2);
  scene.add(plate);

  grid = new THREE.Group();
  var gm = new THREE.LineBasicMaterial({color:0x282c35});
  var gp = [];
  for (var i = 0; i <= X; i += 32) { gp.push(i, 0, 0.02, i, Y, 0.02); }
  for (var j = 0; j <= Y; j += 32) { gp.push(0, j, 0.02, X, j, 0.02); }
  var gg = new THREE.BufferGeometry();
  gg.setAttribute('position', new THREE.Float32BufferAttribute(gp, 3));
  grid.add(new THREE.LineSegments(gg, gm));
  var edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.PlaneGeometry(X, Y)),
    new THREE.LineBasicMaterial({color:0x5a616f}));
  edge.position.set(X / 2, Y / 2, 0.05);
  grid.add(edge);
  scene.add(grid);

  var box = new THREE.BoxGeometry(X, Y, Z);
  chamber = new THREE.LineSegments(
    new THREE.EdgesGeometry(box),
    new THREE.LineBasicMaterial({color:0x3c424f}));
  chamber.position.set(X / 2, Y / 2, Z / 2);
  scene.add(chamber);

  gantry = new THREE.Mesh(
    new THREE.BoxGeometry(X, 2.5, 2.5),
    new THREE.MeshBasicMaterial({color:0x2a2e37}));
  gantry.position.set(X / 2, Y / 2, 0);
  gantry.visible = false;
  scene.add(gantry);

  cam.tx = X / 2; cam.ty = Y / 2; cam.tz = Z * 0.28;
  cam.r = Math.max(X, Y) * 1.75;
}

function onResize() {
  var w = stage.clientWidth, h = stage.clientHeight;
  if (!w || !h) { return; }
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

// \u2500\u2500 orbit (hand-rolled: OrbitControls is not on the allowed CDN as a UMD) \u2500\u2500\u2500
function attachOrbit(el) {
  var down = null, touches = {}, pinch = null;
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
  });
  el.addEventListener('pointermove', function (e) {
    if (touches[e.pointerId]) { touches[e.pointerId] = {x:e.clientX, y:e.clientY}; }
    if (pinch && Object.keys(touches).length === 2) {
      var d = pinchDist();
      if (d > 4) { cam.r = Math.max(40, Math.min(1600, pinch.r * pinch.d / d)); }
      return;
    }
    if (!down) { return; }
    var dx = e.clientX - down.x, dy = e.clientY - down.y;
    down.x = e.clientX; down.y = e.clientY;
    if (down.pan) {
      var s = cam.r * 0.0016;
      var st = Math.sin(cam.theta), ct = Math.cos(cam.theta);
      cam.tx -= (-st * dx) * s; cam.ty -= (ct * dx) * s;
      cam.tz += dy * s;
    } else {
      cam.theta -= dx * 0.006;
      cam.phi = Math.max(0.05, Math.min(Math.PI - 0.05, cam.phi - dy * 0.006));
    }
  });
  ['pointerup','pointercancel'].forEach(function (t) {
    el.addEventListener(t, function (e) {
      delete touches[e.pointerId];
      if (Object.keys(touches).length < 2) { pinch = null; }
      down = null;
    });
  });
  el.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  el.addEventListener('wheel', function (e) {
    e.preventDefault();
    cam.r = Math.max(40, Math.min(1600, cam.r * (1 + Math.sign(e.deltaY) * 0.11)));
  }, {passive:false});
}

function updateCamera() {
  var sp = Math.sin(cam.phi), cp = Math.cos(cam.phi);
  camera.position.set(
    cam.tx + cam.r * sp * Math.cos(cam.theta),
    cam.ty + cam.r * sp * Math.sin(cam.theta),
    cam.tz + cam.r * cp);
  camera.lookAt(cam.tx, cam.ty, cam.tz);
}

// \u2500\u2500 shader \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
// Positions arrive as Int16 hundredths of a millimetre -- see the exporter's
// note on why. uScale converts back; nothing else in the page sees raw units.
var VERT = [
  'attribute float aType;',
  'attribute float aSpeed;',
  'uniform vec3 uColor[12];',
  'uniform float uVis[12];',
  'uniform float uMode;',      // 0 = colour by feature, 1 = colour by speed
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
  '  vColor = mix(uColor[t], magma(mix(0.92, 0.28, f)), uMode);',
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
  'void main(){',
  '  if (vVis < 0.5) discard;',
  // Face normal from screen-space derivatives: the bead tent is faceted, so
  // this IS the real surface normal, and it costs no vertex attribute.
  '  vec3 N = normalize(cross(dFdx(vPos), dFdy(vPos)));',
  '  if (!gl_FrontFacing) N = -N;',
  '  float key  = max(dot(N, normalize(vec3( 0.42,-0.58, 0.70))), 0.0);',
  '  float fill = max(dot(N, normalize(vec3(-0.62, 0.40, 0.22))), 0.0);',
  '  float amb  = 0.30 + 0.20 * max(N.z, 0.0);',
  '  vec3 c = vColor * (amb + 0.70 * key + 0.26 * fill);',
  '  c += vColor * 0.16 * pow(1.0 - abs(N.z), 3.0);',
  '  gl_FragColor = vec4(mix(c, vec3(0.055,0.06,0.072), uDim), 1.0);',
  '}'
].join('\n');

function makeMaterial(dim) {
  var cols = TYPE_COLOR.map(function (h) { return new THREE.Color(h); });
  return new THREE.ShaderMaterial({
    uniforms: {
      uColor: {value: cols},
      uVis:   {value: new Array(12).fill(1)},
      uMode:  {value: 0},
      uSpd:   {value: new THREE.Vector2(15, 80)},
      uDim:   {value: dim}
    },
    vertexShader: VERT, fragmentShader: FRAG,
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
  var layers = raw.layers;               // [z*100, polyStart, polyCount, sec, mm, h]
  var nPoly = polys.length / 3;

  // Pass 1: count points so the typed arrays are allocated once.
  var nPt = 0, nSeg = 0, i, k;
  for (k = 0; k < nPoly; k++) { nPt += polys[k * 3 + 2]; nSeg += polys[k * 3 + 2] - 1; }

  var vPos  = new Int16Array(nPt * 3 * 3);   // 3 verts across the bead tent
  var vType = new Uint8Array(nPt * 3);
  var vSpd  = new Uint8Array(nPt * 3);
  var index = new Uint32Array(nSeg * 12);
  var segEnd = new Float32Array(nSeg * 3);
  var segLen = new Float32Array(nSeg);
  var segCum = new Float32Array(nSeg + 1);
  var segLayer = new Int32Array(nSeg);
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
  g.setIndex(new THREE.BufferAttribute(index, 1));
  g.boundingSphere = new THREE.Sphere(
    new THREE.Vector3(128, 128, 128), 400);   // set by hand: positions are raw int16

  return {raw:raw, geom:g, nSeg:si, segEnd:segEnd, segCum:segCum,
          segLayer:segLayer, layerSeg:layerSeg, total:cum,
          segSpeed:spd, layers:layers};
}

function mountJob(job) {
  if (jobMesh) { scene.remove(jobMesh); scene.remove(ghostMesh); jobGeom.dispose(); }
  jobGeom = job.geom;
  ghostMesh = new THREE.Mesh(jobGeom, makeMaterial(0.86));
  ghostMesh.material.polygonOffset = true;
  ghostMesh.material.polygonOffsetFactor = 2;
  ghostMesh.material.polygonOffsetUnits = 2;
  ghostMesh.frustumCulled = false;
  ghostMesh.visible = false;
  jobMesh = new THREE.Mesh(jobGeom, makeMaterial(0.0));
  jobMesh.frustumCulled = false;
  scene.add(ghostMesh); scene.add(jobMesh);
  nozzle.visible = true; gantry.visible = true;
  JOB = job;
  applyVisibility();
  frameJob(job);
}

function frameJob(job) {
  var b = job.raw.bbox, z = job.layers[job.layers.length - 1][0] / 100;
  var w = Math.max(b[2] - b[0], b[3] - b[1], z * 1.2, 40);
  cam.tx = (b[0] + b[2]) / 2;
  cam.ty = (b[1] + b[3]) / 2;
  cam.tz = z * 0.45;
  cam.r = w * 2.0;
  headScale = Math.max(0.3, Math.min(1.15, w / 150));
  nozzle.scale.setScalar(headScale);
  gantry.scale.set(1, headScale, headScale);
  cam.theta = -0.72; cam.phi = 1.06;
}

// \u2500\u2500 playback state \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
var SPEEDS = [
  {v:1, l:'1\u00d7'}, {v:50, l:'50\u00d7'}, {v:250, l:'250\u00d7'},
  {v:1000, l:'1k\u00d7'}, {v:4000, l:'4k\u00d7'}, {v:15000, l:'15k\u00d7'}
];
var play = {on:false, t:0, speed:1000, seg:0, last:0, scrubbing:false};
var visible = new Array(12).fill(true);
var colorMode = 'feature';
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
    nozzle.position.set(JOB.segEnd[i], JOB.segEnd[i + 1], JOB.segEnd[i + 2]);
    gantry.position.y = JOB.segEnd[i + 1];
    gantry.position.z = JOB.segEnd[i + 2] + 19 * headScale;
  }
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
  updateCamera();
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
  $('r-fil').innerHTML = (fil * 2.98e-3).toFixed(1) + ' <small>g</small>';
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

function paintJobList() {
  var host = $('jobs');
  host.innerHTML = '';
  INDEX.forEach(function (j) {
    var b = el('button', 'job');
    b.type = 'button';
    b.setAttribute('aria-current', String(j.id === currentId));
    var tags = '';
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
  $('buildchip').textContent = INDEX.length + ' plates \u00b7 ' +
    INDEX.reduce(function (a, j) { return a + j.segments; }, 0).toLocaleString() +
    ' extrusion moves on file';
}

var MAGMA = [
  [-0.002136,-0.000750,-0.005386],[0.251661,0.677523,2.494027],
  [8.353717,-3.577720,0.314468],[-27.668733,14.264731,-13.649213],
  [52.176140,-27.943606,12.944169],[-50.768525,29.046583,4.234153],
  [18.655705,-11.489774,-5.601962]];

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

function setColorMode(mode) {
  colorMode = mode;
  Array.prototype.forEach.call($('modeswap').children, function (b) {
    b.setAttribute('aria-pressed', String(b.getAttribute('data-mode') === mode));
  });
  var speedy = mode === 'speed';
  $('speedpanel').hidden = !speedy;
  $('legend').hidden = speedy;
  $('legnote').innerHTML = speedy
    ? 'Feedrate straight out of the G-code. Brightest is slowest \u2014 the outer '
      + 'wall and the top surface, the parts a buyer actually sees. The dark, fast '
      + 'paths are infill nobody will ever look at.'
    : 'Click a type to hide it. Every colour here is the slicer\'s own '
      + '<span class="mono">;TYPE:</span> tag \u2014 nothing is inferred from the shape.';
  applyVisibility();
}

function applyVisibility() {
  [jobMesh, ghostMesh].forEach(function (m) {
    if (!m) { return; }
    var u = m.material.uniforms.uVis.value;
    for (var i = 0; i < 12; i++) { u[i] = visible[i] ? 1 : 0; }
    m.material.uniforms.uMode.value = colorMode === 'speed' ? 1 : 0;
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
    $('ltot').textContent = '/ ' + raw.layers.length;
    _lastFeat = null;
    $('jobnote').textContent = raw.notes || '';
    paintLegend(); paintSpeedPanel(); paintJobList(); paintPrinter();
    setColorMode(colorMode);
    play.t = 0; setSeg(0); setPlaying(true);
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
    row('Nozzle', p.nozzle.toFixed(1) + ' mm brass') +
    row('Layer height', (JOB ? JOB.raw.layerHeight : 0.2).toFixed(2) + ' mm') +
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
    '</span>.</div>';
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
