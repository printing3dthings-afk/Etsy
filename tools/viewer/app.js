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

// ── build plates ─────────────────────────────────────────────────────────────
// The real Bambu Lab 256 x 256 plates, one entry per plate Bambu currently
// sells for this machine. Nothing here is styled from memory:
//   * the five plate types, what each is made of, and which filaments need
//     glue on which, are Bambu's own wiki -- wiki.bambulab.com/en/filament-acc/
//     acc/plates, read 2026-09-19;
//   * every `hex` is the MEDIAN COLOUR sampled out of Bambu's own product
//     photography on that page (build_plates.png, textured_plate.jpg,
//     dual.png), not picked by eye. The textured plate really is gold; the
//     smooth PEI really is mid grey and the dual plate's smooth face is much
//     darker than the standalone smooth plate, which is why they differ here.
// `grain` picks the procedural surface in plateTexture(); roughness/metalness
// are the finish the wiki describes ("textured", "smooth and matte", "nearly
// glossy") expressed for the standard material.
var PLATES = {
  textured: {
    label: 'Textured PEI', hex: 0xcca96b, grain: 'stipple', ink: 0xf0e6d2,
    rough: 0.86, metal: 0.18, bar: 'PLA/ABS/PETG',
    face: 'Textured — the part’s underside comes off with the plate’s grain in it.',
    note: 'PEI powder sprayed on both faces of a stainless sheet. The plate the P1S ships with, and the one every job here was sliced for. Adhesion without glue for most filaments; PC/PA/ABS/ASA may want a glue stick. Self-releases once the bed is back under 35 °C.'
  },
  smooth: {
    label: 'Smooth PEI', hex: 0x464646, grain: 'satin', ink: 0xd8dade,
    rough: 0.52, metal: 0.22, bar: 'PLA',
    face: 'Smooth matte — a flat, level underside.',
    note: 'A PEI sheet bonded to 0.5 mm spring steel with heat-resistant 3M adhesive. For parts that need a genuinely flat bottom. Only PLA goes on bare — everything else needs glue, or the PEI sheet tears when the part releases.'
  },
  dual: {
    label: 'Dual-Texture PEI', hex: 0x24262a, grain: 'satin', ink: 0xd8dade,
    rough: 0.48, metal: 0.24, bar: 'PLA',
    face: 'Smooth side up — flip it for the textured gold face.',
    note: 'One plate, two surfaces: textured PEI on one face, smooth PEI on the other. Shown smooth side up. Same rules as each single-surface plate depending on which way it goes in.'
  },
  engineering: {
    label: 'Engineering Plate', hex: 0x2b2c2e, grain: 'fine', ink: 0xe2e4e8,
    rough: 0.34, metal: 0.30, bar: 'ABS/ASA/PC/PA',
    face: 'Fine even texture — a nearly glossy underside.',
    note: 'A corrosion-resistant reinforced coating aimed at ABS, ASA, PC and PA. Bambu’s all-rounder when you are not sure. Glue is required before printing on it with any filament, not just the hard ones.'
  },
  supertack: {
    label: 'Cool Plate SuperTack', hex: 0x232325, grain: 'flat', ink: 0xe2e4e8,
    rough: 0.66, metal: 0.10, bar: 'PLA/PETG',
    face: 'Flat matte.',
    note: 'Spring steel coated in SuperTack. Grips hard even at low bed temperatures, which is the point — PLA and PETG without heating the bed much. Bambu quotes under 20% adhesion loss after 300 prints.'
  },
  starry: {
    label: '3D Effect Sheet (Starry)', hex: 0x1a2425, grain: 'starry', ink: 0xdfe6e8,
    rough: 0.44, metal: 0.26, bar: '',
    face: 'Decorative — the glitter pattern transfers into the part’s first layer.',
    note: 'Not a plate type so much as a finish: a textured effect sheet whose pattern is pressed into the bottom surface of the print. Here to show what the plate choice does to the part, which is the whole reason the finish column exists.'
  }
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
var _maxAniso = 1;
// P1S bed_exclude_area, front-left corner -- Bambu's own machine profile.
var EXCLUDE_W = 18, EXCLUDE_D = 28;
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
var keyLight = null, envRT = null, floorMesh = null;
var shadowDirty = true, shadowFrame = 0, _tickLast = 0;

// A flat box face samples the environment in exactly ONE direction, so it
// renders as one uniform colour however good the material is -- which is why
// the exterior stayed dead flat after the whole PBR pass. Real painted sheet
// metal has orange-peel: microscopic undulation that breaks the reflection up
// across the face. This is that, procedurally, at an amplitude low enough to
// read as finish rather than as texture.
var _panelNrm = null;
function panelNormalMap() {
  if (_panelNrm) { return _panelNrm; }
  var N = 256, c = document.createElement('canvas');
  c.width = c.height = N;
  var g = c.getContext('2d'), img = g.createImageData(N, N);
  // value noise, two octaves, turned into a tangent-space normal by finite
  // differences -- cheaper and more controllable than hashing per pixel
  var h = new Float32Array(N * N), i, x, y;
  function rnd(ix, iy) {
    var n = ix * 374761393 + iy * 668265263;
    n = (n ^ (n >> 13)) * 1274126177;
    return ((n ^ (n >> 16)) >>> 0) / 4294967295;
  }
  function smooth(fx, fy, step) {
    var x0 = Math.floor(fx / step), y0 = Math.floor(fy / step);
    var tx = fx / step - x0, ty = fy / step - y0;
    tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
    var a = rnd(x0, y0), b = rnd(x0 + 1, y0);
    var cc = rnd(x0, y0 + 1), d = rnd(x0 + 1, y0 + 1);
    return (a + (b - a) * tx) + ((cc + (d - cc) * tx) - (a + (b - a) * tx)) * ty;
  }
  for (y = 0; y < N; y++) {
    for (x = 0; x < N; x++) {
      h[y * N + x] = smooth(x, y, 16) * 0.7 + smooth(x, y, 5) * 0.3;
    }
  }
  for (y = 0; y < N; y++) {
    for (x = 0; x < N; x++) {
      var l = h[y * N + ((x + N - 1) % N)], r = h[y * N + ((x + 1) % N)];
      var u = h[((y + N - 1) % N) * N + x], d2 = h[((y + 1) % N) * N + x];
      i = (y * N + x) * 4;
      img.data[i]     = 128 + (l - r) * 120;
      img.data[i + 1] = 128 + (u - d2) * 120;
      img.data[i + 2] = 255;
      img.data[i + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  _panelNrm = new THREE.CanvasTexture(c);
  _panelNrm.wrapS = _panelNrm.wrapT = THREE.RepeatWrapping;
  _panelNrm.repeat.set(9, 9);
  return _panelNrm;
}

// A studio backdrop rather than flat black. The machine used to sit in a void,
// which is the single clearest tell that you are looking at a render: real
// objects are photographed in a space that falls off behind them. A big
// inward-facing sphere with a vertical gradient is the cheapest honest version
// of that, and it gives the metal something with structure to reflect.
function buildBackdrop() {
  var N = 8, c = document.createElement('canvas');
  c.width = 4; c.height = 256;
  var g = c.getContext('2d');
  var grd = g.createLinearGradient(0, 0, 0, 256);
  // First pass used stops from #05060a to #161b25 and was invisible: every one
  // of them sat within a couple of levels of the 0x07080a clear colour it was
  // meant to replace. A backdrop that cannot be distinguished from the void it
  // replaces is not a backdrop.
  grd.addColorStop(0.00, '#070910');
  grd.addColorStop(0.40, '#141a25');
  grd.addColorStop(0.68, '#2c3646');
  grd.addColorStop(0.88, '#171d28');
  grd.addColorStop(1.00, '#080a0f');
  g.fillStyle = grd;
  g.fillRect(0, 0, 4, 256);
  var tex = new THREE.CanvasTexture(c);
  tex.encoding = THREE.sRGBEncoding;
  var sky = new THREE.Mesh(
    new THREE.SphereGeometry(2600, 32, 24),
    new THREE.MeshBasicMaterial({map: tex, side: THREE.BackSide, fog: false}));
  sky.rotation.x = Math.PI / 2;   // the scene is Z-up; the gradient is not
  sky.name = 'backdrop';
  scene.add(sky);
  return N;
}

// ── materials ──────────────────────────────────────────────────────────────
// Three r128 predates automatic colour management: a material colour is used
// in the lighting maths exactly as given, and the renderer only converts
// linear->sRGB on the way out. Every hex in this file was picked by eye in
// sRGB, so each one has to be converted the other way on input or the whole
// scene renders washed out and milky.
function lin(hex) { return new THREE.Color(hex).convertSRGBToLinear(); }

// Every colour in this scene already stood for one real material -- 0x6e7683
// was always a steel rail, 0x101216 was always a rubber foot. Rather than
// hand-annotate fifty call sites, the mapping lives here once, keyed by the
// hex that was already there. Anything unlisted falls back to matte painted
// plastic, which is what most of the machine actually is.
//                       rough  metal
var SURFACE = {
  0x9aa2af: [0.22, 0.95],  // polished linear rail
  0x6e7683: [0.26, 0.92],  // rail / rod
  0x7b8493: [0.30, 0.88],  // door grip, brushed aluminium
  0x666e7c: [0.34, 0.85],  // control knob
  0x454b58: [0.32, 0.80],  // gantry extrusion, anodised
  0x3a404b: [0.36, 0.78],  // gantry extrusion, darker face
  0x3d4552: [0.40, 0.70],  // carriage plate
  0x59616e: [0.35, 0.60],  // AMS window frame
  0xc98b46: [0.28, 1.00],  // brass mark
  0x101216: [0.90, 0.00],  // rubber foot
  0x0c0e12: [0.85, 0.00],  // rubber / dark plastic
  0x0a0c10: [0.80, 0.00],  // screen bezel
  0x0b0d10: [0.25, 0.00],  // screen glass
  0x26282e: [0.52, 0.18],  // painted steel body panel
  0x2a2e35: [0.54, 0.16],  // AMS shell
  0x2b2f36: [0.58, 0.12],  // spool holder
  0x23262d: [0.60, 0.10],
  0x22262e: [0.62, 0.10],
  0x21252b: [0.62, 0.10],
  0x1d2026: [0.50, 0.20],  // door frame
  0x1b1e24: [0.66, 0.08],
  0x191d25: [0.70, 0.06],
  0x171a1f: [0.60, 0.10],  // trim
  0x171a20: [0.68, 0.06],
  0x15171c: [0.72, 0.05],
  0x4a3a22: [0.55, 0.30]
};

function surface(hex, extra) {
  var r = SURFACE[hex] || [0.62, 0.08];
  // Painted sheet metal picks up far less of the room than a machined rail
  // does. One flat envMapIntensity for everything is what made the first pass
  // look like the whole printer had been dipped in chrome.
  var o = {color: lin(hex), roughness: r[0], metalness: r[1],
           envMapIntensity: 0.50 + 0.80 * r[1]};
  // Only the painted panels: a machined rail is genuinely smooth, and giving
  // it orange-peel would read as dirt.
  if (r[1] < 0.5) {
    o.normalMap = panelNormalMap();
    o.normalScale = new THREE.Vector2(0.45, 0.45);
  }
  if (extra) { for (var k in extra) { o[k] = extra[k]; } }
  return new THREE.MeshStandardMaterial(o);
}

// A colour texture is sRGB data; without this flag it is read as linear and
// the PEI plate and shell liner come out visibly too bright.
function srgbMap(tex) { tex.encoding = THREE.sRGBEncoding; return tex; }

// Unlit sources -- the chamber LED and the lit logo. Emissive on a standard
// material rather than MeshBasic so they still sit on the tone curve instead
// of clipping to a flat white patch.
function emitter(hex, strength) {
  return new THREE.MeshStandardMaterial({
    color: lin(0x000000), emissive: lin(hex),
    emissiveIntensity: strength === undefined ? 1 : strength,
    roughness: 1, metalness: 0
  });
}

// The smoked front door. Real transmission needs a refraction pass three r128
// does not have, so this is a physical material leaning on the environment
// map for its reflection -- which is exactly what sells glass at this angle:
// you read the highlight sliding across it, not what is behind it.
function glassMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: lin(0x3f4a55), metalness: 0, roughness: 0.08,
    transparent: true, opacity: 0.30, clearcoat: 1, clearcoatRoughness: 0.06,
    envMapIntensity: 2.2, depthWrite: false, side: THREE.DoubleSide
  });
}

// ── environment ────────────────────────────────────────────────────────────
// The thing that actually makes metal look like metal. Without an environment
// map a MeshStandardMaterial with metalness 0.9 has nothing to reflect and
// renders nearly black -- which is the classic "I switched to PBR and it got
// worse" failure. This builds a small studio by hand (overhead softbox, cool
// fill from one side, warm bounce from below) and runs it through PMREM so
// rough surfaces get a properly blurred version of it.
function buildEnvironment() {
  var pmrem = new THREE.PMREMGenerator(renderer);
  var room = new THREE.Scene();
  room.background = new THREE.Color(lin(0x0b0d12));

  function panel(w, h, d, color, intensity, x, y, z, rx, ry) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d),
      new THREE.MeshBasicMaterial({color: lin(color)}));
    m.material.color.multiplyScalar(intensity);
    m.position.set(x, y, z);
    if (rx) { m.rotation.x = rx; }
    if (ry) { m.rotation.y = ry; }
    room.add(m);
    return m;
  }

  // First pass at these numbers had a 1.5-intensity cool fill and it turned
  // the whole machine powder blue -- an environment map lights EVERYTHING, so
  // a tint that looks like a tasteful accent in isolation becomes the colour
  // of the product. Warm key, restrained cool, and a dark back wall so metal
  // has something black to reflect: without a dark region in the environment,
  // polished surfaces have no contrast and read as flat grey plastic.
  panel(600, 10, 420, 0xfff2de, 2.2,    0,  360,   40, 0, 0);   // key softbox
  panel(10, 460, 420, 0xa8c0e0, 0.45, -420,  60,    0, 0, 0);   // cool fill
  panel(10, 460, 420, 0xffcfa0, 0.30,  420,  40,    0, 0, 0);   // warm kicker
  panel(600, 10, 420, 0x5a6270, 0.18,   0, -300,    0, 0, 0);   // floor bounce
  panel(600, 460, 10, 0x05070b, 1.0,    0,   40, -360, 0, 0);   // back wall

  envRT = pmrem.fromScene(room, 0.5);
  scene.environment = envRT.texture;
  room.traverse(function (o) {
    if (o.geometry) { o.geometry.dispose(); }
    if (o.material) { o.material.dispose(); }
  });
  pmrem.dispose();
}

function initScene() {
  renderer = new THREE.WebGLRenderer({antialias:true, powerPreference:'high-performance'});
  basePixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(basePixelRatio);
  renderer.setClearColor(0x07080a, 1);
  // The plate face is a 1:1 texture seen at a glancing angle across 256 mm;
  // without anisotropic filtering its grain smears into bands halfway back.
  _maxAniso = renderer.capabilities.getMaxAnisotropy();

  // Colour management, 2026-09-17. Everything below used to render in the
  // renderer's default linear output with Lambert materials, which is why the
  // whole machine read as one flat navy shape: no tone curve, so highlights
  // clipped and midtones crushed together. sRGB output plus an ACES curve is
  // the single biggest change here, and it is why every material colour now
  // goes through lin() -- three r128 has no automatic colour management, so a
  // hex authored in sRGB has to be converted to linear on the way in or the
  // whole scene washes out.
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  // Measured: leaving this on cost 4.4x the frame time (148ms -> 647ms median
  // on this software rasteriser). The shadow pass re-renders the whole
  // 200k-triangle toolpath EVERY frame, and between layer changes that pass
  // produces a bit-identical map. Driven manually from tick() instead.
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.needsUpdate = true;
  stage.appendChild(renderer.domElement);

  // Deterministic render stats and named scene objects for the test harness.
  // Everything else stays inside the closure.
  window.__R = renderer;
  scene = new THREE.Scene();
    // Matched to the backdrop's horizon band, not to the clear colour: the floor
  // dissolves into fog at its edges, and when the two colours disagree that
  // dissolve becomes a visible seam across the image.
  scene.fog = new THREE.Fog(0x141a25, 700, 2400);
  camera = new THREE.PerspectiveCamera(38, 1, 1, 4000);
  camera.up.set(0, 0, 1);
  // The environment map does most of the ambient work now, so the flat
  // AmbientLight that used to carry it is gone -- leaving it in on top of an
  // IBL is what makes a PBR scene look washed and plastic.
  buildEnvironment();
  buildBackdrop();
  // Directional intensity has to win over the environment or the shadow it
  // casts is invisible: an IBL contributes ambient that nothing occludes, so
  // a scene lit mostly by the env map has shadows that darken almost nothing.
  // Measured, not guessed: with the key at 1.9 the print alone rendered at
  // value 0.82 before the rim and the chamber lamp were added on top, and the
  // three together pushed it to 0.86 where ACES desaturates hard -- the vase
  // came out pale peach instead of orange. Each light alone gave saturation
  // 0.47-0.55; it was only their sum that washed out. Roughly half the total
  // budget, keeping the same ratio between them.
  var key = new THREE.DirectionalLight(0xfff0dd, 1.05);
  key.position.set(-260, -420, 520);
  key.castShadow = true;
  key.shadow.mapSize.set(1536, 1536);
  key.shadow.bias = -0.0006;
  key.shadow.normalBias = 0.6;
  var sc = key.shadow.camera;
  sc.left = -420; sc.right = 420; sc.top = 420; sc.bottom = -420;
  sc.near = 120; sc.far = 1700;
  sc.updateProjectionMatrix();
  scene.add(key);
  scene.add(key.target);
  keyLight = key;
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
  // Reachable from the machine and plate pickers, which are live a frame
  // before the scene exists now.
  if (!scene) { return; }
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
      surface(color));
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
    applyShadows(chamber); applyShadows(bedGroup); applyShadows(gantry);
    aimShadowCamera();
    buildFloor();
  shadowDirty = true;
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
    new THREE.MeshStandardMaterial({map: srgbMap(shellTexture()), side: THREE.BackSide, roughness: 0.82, metalness: 0.04, envMapIntensity: 0.35}));
  liner.position.set(ox, oy, cz);
  chamber.add(liner);

  // Screen and knob, bottom right of the front bezel -- the one detail that
  // makes the front read as this machine rather than a generic box. The P1S
  // screen is a 2.7-inch 192x64 panel (Bambu's own P1 spec list), which is a
  // 3:1 letterbox -- the first pass drew it nearly square.
  slab(65, 2, 22, 0x0b0d10, x1 - 66, y0 - 0.6, zBot + 28, null);
  var knob = new THREE.Mesh(new THREE.CylinderGeometry(11, 11, 4, 24),
    surface(0x666e7c));
  knob.rotation.x = Math.PI / 2;
  knob.position.set(x1 - 22, y0 - 1.5, zBot + 28);
  chamber.add(knob);

  // Feet and the rear spool holder
  [[x0 + 24, y0 + 24], [x1 - 24, y0 + 24], [x0 + 24, y1 - 24], [x1 - 24, y1 - 24]]
    .forEach(function (p) {
      var f = new THREE.Mesh(new THREE.CylinderGeometry(13, 13, 9, 16),
        surface(0x101216));
      f.rotation.x = Math.PI / 2;
      f.position.set(p[0], p[1], zBot - 4);
      chamber.add(f);
    });
  var spool = new THREE.Mesh(new THREE.CylinderGeometry(34, 34, 62, 24),
    surface(0x2b2f36));
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
    glassMaterial());
  glass.position.set(hingeLeft ? dw / 2 : -dw / 2, 0, 0);
  glass.userData.door = true;
  doorGroup.add(glass);
  var frameCol = 0x1d2026;
  [[dw, 7, 0, (dh - 7) / 2], [dw, 7, 0, -(dh - 7) / 2],
   [7, dh, -(dw - 7) / 2, 0], [7, dh, (dw - 7) / 2, 0]].forEach(function (f) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(f[0], 5, f[1]),
      surface(frameCol));
    m.position.set((hingeLeft ? dw / 2 : -dw / 2) + f[2], 0, f[3]);
    m.userData.door = true;
    doorGroup.add(m);
  });
  var grip = new THREE.Mesh(new THREE.BoxGeometry(9, 13, 74),
    surface(0x7b8493));
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
  // Decoration, not the point of the page. Wrapped because a throw in here
  // reaches initScene and takes the whole viewer with it -- the plate list,
  // the panels, the replay, everything -- to save a box of spools.
  try {
    buildAMS(PRINTERS[printerId].ams, ox, oy, y1, zTop);
  } catch (e) {
    amsGroup = null;
    console.warn('AMS not drawn:', e);
  }
  rebuildToolhead(true);
  applyShadows(chamber); applyShadows(bedGroup); applyShadows(gantry);
  applyShadows(amsGroup); applyShadows(doorGroup);
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
  // After the real bounds, not before: the AMS on the lid is part of what has
  // to fit inside the shadow frustum, and the floor sits on zBot.
  aimShadowCamera();
  buildFloor();
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

// ── build plate ────────────────────────────────────────────
// A real Bambu flex plate, not a grey square: the silhouette Bambu's own plates
// have (rounded corners, the slotted locating tab at the back, the printed bar
// and two angled notches along the front), the surface finish of whichever
// plate is selected, and the printable area drawn on it.
//
// The locating tab is the alignment story in hardware. The plate does not get
// positioned by eye -- its rear slot drops over the heatbed's pins, which is
// what makes the machine's 0,0 (the FRONT-LEFT corner of the printable square,
// per Bambu's own printable_area in the P1S profile) land in the same physical
// place every time you pull a print off and put the plate back.
var PLATE_TAB_W = 78, PLATE_TAB_D = 11;   // rear locating tab
var PLATE_BAR_W = 205, PLATE_BAR_D = 7;   // front printed bar
var PLATE_STEEL = 1;                      // steel overhangs the printable square

function plateShape(X, Y) {
  var s = new THREE.Shape();
  var x0 = -PLATE_STEEL, x1 = X + PLATE_STEEL;
  var y0 = -PLATE_STEEL, y1 = Y + PLATE_STEEL;
  var r = 9, cx = X / 2;
  s.moveTo(x0 + r, y0);
  // front edge, interrupted by the printed bar
  s.lineTo(cx - PLATE_BAR_W / 2, y0);
  s.lineTo(cx - PLATE_BAR_W / 2 + 4, y0 - PLATE_BAR_D);
  s.lineTo(cx + PLATE_BAR_W / 2 - 4, y0 - PLATE_BAR_D);
  s.lineTo(cx + PLATE_BAR_W / 2, y0);
  s.lineTo(x1 - r, y0);
  s.quadraticCurveTo(x1, y0, x1, y0 + r);
  s.lineTo(x1, y1 - r);
  s.quadraticCurveTo(x1, y1, x1 - r, y1);
  // back edge, interrupted by the locating tab
  s.lineTo(cx + PLATE_TAB_W / 2, y1);
  s.lineTo(cx + PLATE_TAB_W / 2 - 7, y1 + PLATE_TAB_D);
  s.lineTo(cx - PLATE_TAB_W / 2 + 7, y1 + PLATE_TAB_D);
  s.lineTo(cx - PLATE_TAB_W / 2, y1);
  s.lineTo(x0 + r, y1);
  s.quadraticCurveTo(x0, y1, x0, y1 - r);
  s.lineTo(x0, y0 + r);
  s.quadraticCurveTo(x0, y0, x0 + r, y0);
  // The slot in the locating tab -- a real hole, so it reads as one from the
  // side rather than as a painted line.
  var h = new THREE.Path();
  var sw = 56, sh = 3.4, sy = y1 + 4;
  h.moveTo(cx - sw / 2, sy); h.lineTo(cx + sw / 2, sy);
  h.lineTo(cx + sw / 2, sy + sh); h.lineTo(cx - sw / 2, sy + sh);
  s.holes.push(h);
  return s;
}

// UVs straight off ExtrudeGeometry/ShapeGeometry are world x,y in millimetres,
// so a 1:1 plate-face texture needs them remapped across the shape's own box.
function normalizeUV(geo) {
  geo.computeBoundingBox();
  var b = geo.boundingBox, uv = geo.attributes.uv;
  var w = b.max.x - b.min.x, h = b.max.y - b.min.y;
  for (var i = 0; i < uv.count; i++) {
    uv.setXY(i, (uv.getX(i) - b.min.x) / w, (uv.getY(i) - b.min.y) / h);
  }
  uv.needsUpdate = true;
  return [b.min.x, b.min.y, w, h];
}

function buildBed(X, Y, ox, oy) {
  bedGroup = new THREE.Group();
  var spec = PLATES[plateId] || PLATES.textured;
  var shape = plateShape(X, Y);

  // Steel body. Top face sits a hair below z=0 so the first layer lands on it
  // rather than inside it.
  var body = new THREE.Mesh(
    new THREE.ExtrudeGeometry(shape, {depth: 2.0, bevelEnabled: false}),
    surface(0x23262c, {roughness: 0.42, metalness: 0.72}));
  // plateShape() is already in plate coordinates (0..X, 0..Y), so unlike the
  // centred box it replaced it takes no ox/oy offset -- applying one put the
  // plate a bed-width out in front of the machine.
  body.position.set(0, 0, -2.05);
  bedGroup.add(body);

  // Printed face. Separate from the extrusion because it needs its own 1:1 UVs
  // and because the markings have to land at real plate coordinates, not on a
  // tiling texture.
  var faceGeo = new THREE.ShapeGeometry(shape, 24);
  var box = normalizeUV(faceGeo);
  var maps = plateSurface(spec, X, Y, box);
  var faceMat = {color: lin(spec.hex), roughness: spec.rough, metalness: spec.metal,
    envMapIntensity: 0.7, polygonOffset: true,
    polygonOffsetFactor: -2, polygonOffsetUnits: -2};
  if (maps) {
    faceMat.map = srgbMap(maps.color);
    faceMat.normalMap = maps.normal;
    faceMat.normalScale = new THREE.Vector2(maps.bump, maps.bump);
  }
  plate = new THREE.Mesh(faceGeo, new THREE.MeshStandardMaterial(faceMat));
  plate.position.set(0, 0, -0.045);
  bedGroup.add(plate);

  // Heatbed under the flex plate -- what the magnets grab.
  var carrier = new THREE.Mesh(new THREE.BoxGeometry(X + 22, Y + 22, 9),
    surface(0x191d25));
  carrier.position.set(ox, oy, -6.6);
  bedGroup.add(carrier);

  buildPlateGrid(X, Y, spec);
  // Switching plate or machine rebuilds this group, and the rebuild has to
  // land in whatever mode is already running -- otherwise picking a plate in
  // real-print mode paints the guides back on.
  grid.visible = colorMode !== 'real';
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

// The printable square, its 32 mm ruling, and the corner the P1S reserves.
// Lines are drawn in the plate's own ink colour so they stay legible on gold
// and on black without a second palette.
function buildPlateGrid(X, Y, spec) {
  grid = new THREE.Group();
  var gp = [];
  for (var i = 32; i < X; i += 32) { gp.push(i, 0, 0.06, i, Y, 0.06); }
  for (var k = 32; k < Y; k += 32) { gp.push(0, k, 0.06, X, k, 0.06); }
  var gg = new THREE.BufferGeometry();
  gg.setAttribute('position', new THREE.Float32BufferAttribute(gp, 3));
  grid.add(new THREE.LineSegments(gg, new THREE.LineBasicMaterial({
    color: lin(spec.ink), transparent: true, opacity: 0.22})));

  var edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.PlaneGeometry(X, Y)),
    new THREE.LineBasicMaterial({color: lin(spec.ink),
      transparent: true, opacity: 0.5}));
  edge.position.set(X / 2, Y / 2, 0.08);
  grid.add(edge);

  // bed_exclude_area from Bambu's own P1S profile: an 18 x 28 mm rectangle at
  // the front-left corner, where the toolhead parks and wipes. Nothing is
  // allowed to print here, and the first thing you notice arranging a wide
  // part is that this corner is why it will not fit flush.
  if (X >= 60 && Y >= 60) {
    var ex = new THREE.Mesh(new THREE.PlaneGeometry(EXCLUDE_W, EXCLUDE_D),
      new THREE.MeshBasicMaterial({color: lin(0xff5a3c), transparent: true,
        opacity: 0.30, depthWrite: false}));
    ex.position.set(EXCLUDE_W / 2, EXCLUDE_D / 2, 0.07);
    grid.add(ex);
    var exl = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.PlaneGeometry(EXCLUDE_W, EXCLUDE_D)),
      new THREE.LineBasicMaterial({color: lin(0xff7a55),
        transparent: true, opacity: 0.85}));
    exl.position.set(EXCLUDE_W / 2, EXCLUDE_D / 2, 0.09);
    grid.add(exl);
  }
}

function buildGantry(W, ox, oy) {
  gantry = new THREE.Group();
  gantry.add(new THREE.Mesh(new THREE.BoxGeometry(W - 40, 9, 6.5),
    surface(0x3a404b)));
  var railTop = new THREE.Mesh(new THREE.BoxGeometry(W - 40, 9, 1.3),
    surface(0x454b58));
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
        surface(DARK));
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
      surface(METAL));
    screw.rotation.x = Math.PI / 2;
    screw.position.set(p[0], p[1], (zLo + zHi) / 2);
    chamber.add(screw);
    var post = new THREE.Mesh(new THREE.BoxGeometry(14, 14, zHi - zLo),
      surface(DARK));
    post.position.set(p[0] + (p[0] > ox ? 20 : -20), p[1], (zLo + zHi) / 2);
    chamber.add(post);
    var pulley = new THREE.Mesh(new THREE.CylinderGeometry(11, 11, 9, 14),
      surface(0x3d4552));
    pulley.rotation.x = Math.PI / 2;
    pulley.position.set(p[0], p[1], zLo - 6);
    chamber.add(pulley);
  });

  // One motor, one belt, both under the base -- which is why all three screws
  // turn together and the bed cannot tilt out of tram on its own.
  var zMotor = new THREE.Mesh(new THREE.BoxGeometry(34, 34, 30),
    surface(0x1b1e24));
  zMotor.position.set(ox + 46, y1 - t - 30, zLo - 22);
  chamber.add(zMotor);
  var beltPath = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
      new THREE.Vector3(zPosts[0][0], zPosts[0][1], zLo - 6),
      new THREE.Vector3(ox + 46, y1 - t - 30, zLo - 6),
      new THREE.Vector3(zPosts[1][0], zPosts[1][1], zLo - 6),
      new THREE.Vector3(zPosts[2][0], zPosts[2][1], zLo - 6),
      new THREE.Vector3(zPosts[0][0], zPosts[0][1], zLo - 6)], true), 30, 2.4, 6, true),
    surface(0x15171c));
  chamber.add(beltPath);

  // Three sliders, on the bed, descending with it -- the whole point of
  // drawing the stage at all is that this is the part that actually moves.
  var beam = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0 - 46, 15, 11),
    surface(FRAME));
  beam.position.set(ox, y1 - t - 39, -14);
  bedGroup.add(beam);
  zPosts.forEach(function (p) {
    var slider = new THREE.Mesh(new THREE.BoxGeometry(24, 28, 19),
      surface(0x3d4552));
    slider.position.set(p[0], p[1], -14);
    bedGroup.add(slider);
    var arm = new THREE.Mesh(new THREE.BoxGeometry(13, Math.abs(p[1] - oy), 9),
      surface(FRAME));
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
      surface(DARK));
    r.position.set(x, oy, 0);
    yRails.add(r);
    [-3.5, 3.5].forEach(function (dy) {
      var b = new THREE.Mesh(new THREE.BoxGeometry(2.5, y1 - y0 - 2 * t - 16, 5),
        surface(0x15171c));
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
    emitter(0xffe9c6, 2.6));
  bar.position.set(x0 + t + 9, ledY, zTop - 30);
  chamber.add(bar);
  var shell = new THREE.Mesh(new THREE.BoxGeometry(11, ledLen + 10, 14),
    surface(0x2b2f36));
  shell.position.set(x0 + t + 5, ledY, zTop - 30);
  chamber.add(shell);
  // Tight falloff on purpose. A 5V 0.3A strip pools light near itself and
  // leaves the far corners dim; the first pass's wide, bright lamp flattened
  // the whole chamber into even grey, which reads as a lightbox, not a P1S.
  chamberLamp = new THREE.PointLight(0xffdcae, 1.55, 560, 1.5);
  chamberLamp.position.set(x0 + 58, ledY, zTop - 46);
  chamber.add(chamberLamp);

  var cam2 = new THREE.Mesh(new THREE.BoxGeometry(17, 15, 15),
    surface(0x23262d));
  cam2.position.set(x0 + t + 12, y0 + t + 12, zTop - 30);
  chamber.add(cam2);
  var lens = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 3, 12),
    surface(0x0a0c10));
  lens.rotation.x = Math.PI / 2;
  lens.position.set(x0 + t + 16, y0 + t + 16, zTop - 36);
  chamber.add(lens);
}

// The AMS, at its real size, sitting where one actually sits.
//
// Drawn from Bambu's own product photography of the 4-slot AMS (2026-09-19).
// The shape that makes it recognisable is the DOME: a half-cylinder of smoked
// plastic whose axis runs along the spool row, so its arch follows the spool
// circles exactly and the top half of every spool shows through it. It was a
// flat-lidded box here before, which from above read as an empty tray with one
// spool in it.
//
// Proportions come off the published 368 x 283 x 224 mm. The dome radius is
// half the depth (141.5), so the opaque body below it is the remaining 82.5 --
// which is the split the photographs show, and it is arithmetic rather than a
// guess. Spool size is the AMS's own published compatibility range, 197-202 mm
// across and 50-68 wide, which is why four of them very nearly fill the box.
//
// Deliberately unbranded, same as the machine: the real unit wears a Bambu Lab
// wordmark across the front band and that is not mine to reproduce.
//
// What is illustrative and says so on the panel: the filament colours, and the
// fact that anything is loaded at all. Nothing here reads the machine.
function buildAMS(spec, ox, oy, y1, zTop) {
  amsGroup = null;
  if (!spec) { return; }
  amsGroup = new THREE.Group();
  var cy = y1 - spec.d / 2 - 6;
  var z0 = zTop + 4;                       // the AMS sits on the machine lid
  var domeR = spec.d / 2;
  var bodyH = Math.max(40, spec.h - domeR);
  var wall = 7, r = 14;

  // Smoked shell. depthWrite off so four spools behind two layers of it still
  // sort correctly; renderOrder puts every transparent panel after the solid
  // hardware inside, which is the only ordering that reads right.
  function smoked(op, tint) {
    var m = new THREE.MeshPhysicalMaterial({
      color: lin(tint || 0x1a1d22), metalness: 0, roughness: 0.22,
      transparent: true, opacity: op, clearcoat: 0.6, clearcoatRoughness: 0.18,
      envMapIntensity: 0.85, depthWrite: false, side: THREE.DoubleSide
    });
    return m;
  }

  function roundedRect(w, d, rad) {
    var s = new THREE.Shape(), x = w / 2, y = d / 2;
    s.moveTo(-x + rad, -y);
    s.lineTo(x - rad, -y); s.quadraticCurveTo(x, -y, x, -y + rad);
    s.lineTo(x, y - rad);  s.quadraticCurveTo(x, y, x - rad, y);
    s.lineTo(-x + rad, y); s.quadraticCurveTo(-x, y, -x, y - rad);
    s.lineTo(-x, -y + rad); s.quadraticCurveTo(-x, -y, -x + rad, -y);
    return s;
  }

  // ── body ──────────────────────────────────────────────────────────────────
  var base = new THREE.Mesh(
    new THREE.ExtrudeGeometry(roundedRect(spec.w, spec.d, r), {depth: 9, bevelEnabled: false}),
    surface(0x1b1e24));
  base.position.set(ox, cy, z0);
  amsGroup.add(base);

  var shell = roundedRect(spec.w, spec.d, r);
  shell.holes.push(roundedRect(spec.w - wall * 2, spec.d - wall * 2, Math.max(2, r - wall)));
  var walls = new THREE.Mesh(
    new THREE.ExtrudeGeometry(shell, {depth: bodyH, bevelEnabled: false}), smoked(0.50));
  walls.position.set(ox, cy, z0);
  walls.renderOrder = 2;
  amsGroup.add(walls);

  // The opaque band around the top of the body, where the wordmark would be.
  // A FRAME, not a plate: filled, it caps the body and hides the bottom half
  // of every spool behind what looks like a closed lid -- which is the same
  // mistake the flat-lidded version made, just one level down.
  var bandShape = roundedRect(spec.w + 3, spec.d + 3, r);
  bandShape.holes.push(roundedRect(spec.w - 26, spec.d - 26, 8));
  var band = new THREE.Mesh(
    new THREE.ExtrudeGeometry(bandShape, {depth: 13, bevelEnabled: false}),
    surface(0x26292f));
  band.position.set(ox, cy, z0 + bodyH - 13);
  amsGroup.add(band);

  // The one piece of trim worth having: the round latch button, front centre.
  var latch = new THREE.Mesh(new THREE.CylinderGeometry(11, 11, 4, 20),
    surface(0xcfd3d9, {roughness: 0.45, metalness: 0.1}));
  latch.rotation.x = Math.PI / 2;
  latch.position.set(ox, cy - spec.d / 2 - 1, z0 + bodyH - 6);
  amsGroup.add(latch);

  // ── dome ──────────────────────────────────────────────────────────────────
  // Half a cylinder lying along the spool row. thetaStart/-Length cut the top
  // half only; the flat underside is the body's opening, not a surface.
  var domeZ = z0 + bodyH;
  var dome = new THREE.Mesh(
    new THREE.CylinderGeometry(domeR, domeR, spec.w, 48, 1, true, 0, Math.PI),
    smoked(0.34, 0x20242a));
  dome.rotation.z = Math.PI / 2;
  dome.position.set(ox, cy, domeZ);
  dome.renderOrder = 3;
  amsGroup.add(dome);
  // End caps, so the dome reads as a closed box rather than an open tunnel.
  [-1, 1].forEach(function (s) {
    var cap = new THREE.Mesh(new THREE.CircleGeometry(domeR, 40, 0, Math.PI),
      smoked(0.40, 0x20242a));
    // CircleGeometry's half-disc bulges toward its own +Y. rotation.y alone
    // leaves that pointing at world +Y, which stands the cap up as a flat
    // sheet off the BACK of the dome instead of closing its end. The z turn
    // (applied first, three.js composes XYZ as Rx*Ry*Rz) swings the bulge to
    // world +Z so it follows the arch.
    cap.rotation.set(0, Math.PI / 2, Math.PI / 2);
    cap.position.set(ox + s * spec.w / 2, cy, domeZ);
    cap.renderOrder = 3;
    amsGroup.add(cap);
  });
  var lipShape = roundedRect(spec.w + 2, spec.d + 2, r);
  lipShape.holes.push(roundedRect(spec.w - 12, spec.d - 12, 8));
  var lip = new THREE.Mesh(
    new THREE.ExtrudeGeometry(lipShape, {depth: 5, bevelEnabled: false}),
    surface(0x1e2127));
  lip.position.set(ox, cy, domeZ - 2);
  amsGroup.add(lip);

  // ── spools and the hardware under them ────────────────────────────────────
  var pitch = (spec.w - wall * 4) / spec.slots;
  var sz = domeZ + 16;                     // spool axis, just above the body lip
  var spools = [], cores = [], reels = [];
  for (var i = 0; i < spec.slots; i++) {
    var x = ox + (i - (spec.slots - 1) / 2) * pitch;
    var flanges = [];

    // Rotated onto X by the PARENT, so the wound coil's own Y rotation stays
    // free to be the spool turning as filament is pulled off it. updateAMS()
    // scales this mesh's x/z for the falling coil radius and spins its y --
    // both of those depend on the axis being local Y, so it has to stay a
    // plain CylinderGeometry under a z-rotated parent.
    var hub = new THREE.Group();
    hub.rotation.z = Math.PI / 2;
    hub.position.set(x, cy, sz);

    var fil = new THREE.Mesh(new THREE.CylinderGeometry(99, 99, 54, 40, 1, true),
      surface(FILAMENT[i % FILAMENT.length], {roughness: 0.52, metalness: 0.0,
        map: srgbMap(windingTexture()), side: THREE.DoubleSide}));
    hub.add(fil);
    amsGroup.add(hub);
    spools.push(fil);

    // The flanges do NOT shrink with the coil -- they are the spool, not the
    // filament, and watching them collapse was the giveaway that the old one
    // was drawing a solid cylinder of plastic rather than a reel.
    [-1, 1].forEach(function (s) {
      var fl = new THREE.Mesh(new THREE.CylinderGeometry(101, 101, 2.6, 40),
        smoked(0.46, 0x767d8a));
      fl.rotation.z = Math.PI / 2;
      fl.position.set(x + s * 29, cy, sz);
      fl.renderOrder = 1;
      amsGroup.add(fl);
      flanges.push(fl);
    });

    var core = new THREE.Mesh(new THREE.CylinderGeometry(35, 35, 58, 24),
      surface(0xc8ccd2, {roughness: 0.6, metalness: 0.05}));
    core.rotation.z = Math.PI / 2;
    core.position.set(x, cy, sz);
    amsGroup.add(core);
    cores.push(core);

    // Feeder hardware, visible through the smoked front: the drive roller and
    // the brass-toned gear block above it, one per slot.
    var roller = new THREE.Mesh(new THREE.CylinderGeometry(15, 15, 40, 20),
      surface(0x6f757e, {roughness: 0.5, metalness: 0.25}));
    roller.rotation.x = Math.PI / 2;
    roller.position.set(x, cy - spec.d / 2 + 34, z0 + 26);
    amsGroup.add(roller);
    var gearbox = new THREE.Mesh(new THREE.BoxGeometry(26, 20, 16),
      surface(0x9c7a3e, {roughness: 0.45, metalness: 0.55}));
    gearbox.position.set(x, cy - spec.d / 2 + 30, z0 + 40);
    amsGroup.add(gearbox);
    reels.push(flanges);
  }

  // PTFE bundle looping out of the back and into the top of the machine.
  var curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(ox, cy + spec.d / 2 - 4, z0 + 30),
    new THREE.Vector3(ox, y1 + 54, z0 - 34),
    new THREE.Vector3(ox, y1 - 26, zTop + 3)]);
  var feed = new THREE.Mesh(new THREE.TubeGeometry(curve, 22, 7, 10, false),
    surface(0x171a20));
  amsGroup.add(feed);

  amsGroup.userData.spools = spools;
  amsGroup.userData.cores = cores;
  // The flanges are part of the reel, so they come and go with it. Leaving
  // them behind when a slot is hidden left three empty pairs of discs hanging
  // in the dome, which reads as a fault rather than as an empty slot.
  amsGroup.userData.reels = reels;
  amsGroup.userData.feed = feed;
  amsGroup.name = 'ams';
  scene.add(amsGroup);
}

// Wound filament, not a painted drum. Fine stripes running across the coil,
// which wrap around the cylinder into the winding you actually see on a spool
// edge-on. Cheap enough to build per spool and the single thing that stops
// four coloured cylinders reading as four coloured cylinders.
function windingTexture() {
  var c = document.createElement('canvas');
  // 32 wraps across a 54 mm coil is a 1.7 mm pitch, which is 1.75 mm filament
  // laid side by side -- the real thing. The first pass used 128, a 0.4 mm
  // pitch, and it mipmapped straight back to flat paint.
  c.width = 8; c.height = 32;
  var g = c.getContext('2d');
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 8, 32);
  for (var i = 0; i < 32; i++) {
    g.fillStyle = 'rgba(0,0,0,' + (0.13 + Math.random() * 0.14).toFixed(3) + ')';
    g.fillRect(0, i, 8, 0.6);
  }
  var t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(1, 1);
  t.anisotropy = _maxAniso;
  return t;
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
    surface(0x23262d));
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
// Shadows are what put the print ON the plate instead of floating above it.
// Applied by traversal rather than at each call site because a mesh's role is
// already decided by which group it landed in: the machine casts, the plate
// and liner receive, and the smoked panels do neither -- a transparent mesh
// writing into the shadow map paints a hard black rectangle across the bed.
// The shadow camera defaults to looking at the world origin, which is not
// where this machine is -- the bed sits at (ox, oy) and the body spans zBot to
// zTop. Aiming and sizing the frustum at the real bounds is the difference
// between a crisp contact shadow and a shadow map spent mostly on empty space.
// A machine standing in pure black reads as a render of a model; the same
// machine with a floor under it and its own shadow on that floor reads as an
// object in a room. The plane is deliberately larger than the fog far distance
// so its edges dissolve into the background instead of ending on a visible
// horizon line.
function buildFloor() {
  if (!machineBounds) { return; }
  if (floorMesh) { scene.remove(floorMesh); floorMesh.geometry.dispose(); }
  floorMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(3200, 3200),
    new THREE.MeshStandardMaterial({color: lin(0x212732), roughness: 0.66,
      metalness: 0.0, envMapIntensity: 0.30}));
  floorMesh.position.set(machineBounds.ox, machineBounds.oy,
                         machineBounds.zBot - 13);
  floorMesh.material.normalMap = panelNormalMap();
  floorMesh.material.normalScale = new THREE.Vector2(0.6, 0.6);
  floorMesh.receiveShadow = true;
  floorMesh.name = 'floor';
  scene.add(floorMesh);
}

function aimShadowCamera() {
  if (!keyLight || !machineBounds) { return; }
  var b = machineBounds;
  var cz = (b.zBot + (b.zOuter || b.zTop)) / 2;
  var span = Math.max(EXT.w, EXT.d, (b.zOuter || b.zTop) - b.zBot) * 0.62;
  keyLight.target.position.set(b.ox, b.oy, b.zBot + (b.zTop - b.zBot) * 0.30);
  keyLight.target.updateMatrixWorld();
  // Steep on purpose. At a shallow angle the print throws its shadow directly
  // away from the camera, behind its own body, so the bed reads as if nothing
  // is standing on it. Chamber lighting is overhead anyway.
  keyLight.position.set(b.ox - 190, b.oy - 250, cz + 780);
  var sc = keyLight.shadow.camera;
  sc.left = -span; sc.right = span; sc.top = span; sc.bottom = -span;
  sc.near = 60; sc.far = 2200;
  sc.updateProjectionMatrix();
  keyLight.shadow.needsUpdate = true;
}

function applyShadows(root) {
  if (!root) { return; }
  root.traverse(function (o) {
    if (!o.isMesh) { return; }
    var m = o.material;
    if (m && (m.transparent || m.emissive !== undefined && m.emissiveIntensity > 1.5)) {
      o.castShadow = false; o.receiveShadow = false; return;
    }
    o.castShadow = true;
    o.receiveShadow = true;
  });
}

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
    surface(0x22262e));
  body.position.z = 20;
  g.add(body);
  g.add(new THREE.Mesh(new THREE.BoxGeometry(10, 10, 6),
    surface(0x4a3a22)).translateZ(4.6));
  var tip = new THREE.Mesh(new THREE.ConeGeometry(2.4, 5, 16),
    emitter(0xc98b46, 0.9));
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
      surface(color));
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
    surface(0x0c0e12));
  fan.rotation.x = Math.PI / 2;
  fan.position.set(0, -16.4, 37);
  g.add(fan);
  var hub = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 3, 12),
    surface(0x3a4049));
  hub.rotation.x = Math.PI / 2;
  hub.position.set(0, -17, 37);
  g.add(hub);

  // Filament cutter lever, on the side of the middle housing.
  var lever = part(5, 13, 3.4, 0x596270, 46, -2);
  lever.position.x = 14;

  // PTFE pneumatic joint on top, where the AMS tube lands.
  var joint = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 5, 6, 14),
    surface(0x6e7683));
  joint.rotation.x = Math.PI / 2;
  joint.position.set(0, 8, 57);
  g.add(joint);

  // All-in-one hotend: finned heatsink, thin metal tube, integrated heat
  // block and nozzle. This is the geometry the wiki describes in words.
  for (var i = 0; i < 5; i++) {
    part(15, 13, 1.4, 0x8e96a3, 13 + i * 2.5, 0);
  }
  var neck = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 2.1, 4.4, 12),
    surface(0x9aa2af));
  neck.rotation.x = Math.PI / 2;
  neck.position.set(0, 0, 9.4);
  g.add(neck);
  part(11, 11, 5.4, 0x4a3a22, 4.6, 0);         // heat block, silicone-socked
  var tip = new THREE.Mesh(new THREE.ConeGeometry(2.4, 5, 16),
    emitter(0xc98b46, 0.9));
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

// ── plate surfaces ───────────────────────────────────────────────────────────
// One canvas per plate covering the whole sheet 1:1, so the grain, the side
// text and the front bar all land at real plate coordinates. A tiling noise
// texture cannot do the markings, and a decal plane for the markings would
// need its own draw call and its own z-fight to manage; one canvas is both.
//
// The companion normal map matters more than the colour does. Textured PEI is
// sprayed powder -- it is the height variation that makes it read as grit
// rather than as a gold sticker, and the same trick at a tenth the amplitude
// is the difference between "smooth PEI" and "flat grey".
// 512, not 1024. A 256 mm plate at 512 px is two texels per millimetre, which
// is finer than the grain it carries; 1024 bought nothing visible and cost
// four times the canvas memory and four times the draw calls -- the fine
// octave alone was 58,000 arc fills per plate build. Canvas backing store is
// the scarcest thing in a phone webview, and this function allocates three of
// them plus an ImageData in one go.
var PLATE_PX = 512;

function _plateCanvas() {
  var c = document.createElement('canvas');
  c.width = c.height = PLATE_PX;
  return c;
}

// A phone webview hands back null here once its canvas budget is spent, and
// the very next line is a fillStyle assignment on it. Named, so the message
// that reaches the screen says what actually ran out.
function _plateCtx(c) {
  var g = c.getContext('2d');
  if (!g) { throw new Error('no 2d canvas context (canvas memory exhausted?)'); }
  return g;
}

// Each plate's finish as three octaves of the same speckle: coarse mottle,
// mid grain, fine grit. One octave is not enough and the reason is mipmapping
// -- a 1024px face texture on a 256mm plate is well under one texel per screen
// pixel at any normal zoom, so a single fine octave averages itself away into
// flat paint everywhere except the few rows nearest the camera. That was the
// first version's actual failure: grain at the front of the plate, bare gold
// at the back, with nothing wrong in the texture itself.
//
//   octaves: [radius px, coverage, colour swing, height swing, alpha]
//   bump:    normalScale for the companion height map
//
// ONLY THE MIDDLE OCTAVE CARRIES HEIGHT, and that is the whole lesson here.
// Both neighbours were tried and both are wrong for a reason worth writing
// down:
//   * the coarse octave as relief gives 30px-wide smooth bumps whose normals
//     swing the environment reflection across half a centimetre of plate at a
//     time -- every plate came out mottled in big light-grey blobs that had
//     nothing to do with its colour map;
//   * the fine octave as relief is worse, and it is the same geometric
//     aliasing the bead mesh hit: 2px features in a 1024px texture shown at
//     ~240px on screen are sub-pixel, so their normals alias into hard white
//     specular sparkle and a matte black plate renders as television static.
// Fine detail belongs in the COLOUR map, which mipmaps down to a slightly
// varied tone instead of to noise.
var GRAIN = {
  stipple: {bump: 0.70, octaves: [[30, 0.55, 19,  0, 0.34], [10, 0.65, 21, 78, 0.36], [2.0, 0.70, 24, 0, 0.42]]},
  satin:   {bump: 0.10, octaves: [[36, 0.28,  4,  0, 0.22], [7, 0.32,  5, 14, 0.22], [1.5, 0.40,  7, 0, 0.26]]},
  fine:    {bump: 0.08, octaves: [[38, 0.22,  3,  0, 0.18], [5, 0.38,  4, 12, 0.20], [1.1, 0.50,  6, 0, 0.24]]},
  flat:    {bump: 0.06, octaves: [[40, 0.20,  3,  0, 0.16], [9, 0.26,  4,  8, 0.16], [1.8, 0.28,  5, 0, 0.18]]},
  starry:  {bump: 0.26, octaves: [[32, 0.35,  9, 18, 0.25]], glitter: true}
};

// The finish is decoration. A plate that falls back to flat colour is a worse
// picture; a plate that takes the whole page down with it is a broken page,
// and on 2026-09-19 that is exactly what a phone got.
function plateSurface(spec, X, Y, box) {
  try {
    return buildPlateSurface(spec, X, Y, box);
  } catch (e) {
    console.warn('plate finish fell back to flat colour:', e);
    return null;
  }
}

function buildPlateSurface(spec, X, Y, box) {
  var g = GRAIN[spec.grain] || GRAIN.satin;
  var ct = new THREE.CanvasTexture(plateColourMap(spec, g, X, Y, box));
  var nt = grainNormalMap(spec.grain, g);
  ct.anisotropy = _maxAniso;
  return {color: ct, normal: nt, bump: g.bump};
}

// Colour and height are drawn from the same seeded sequence, so a bright fleck
// is a raised fleck -- which is what a sprayed powder coat is, and what keeps
// the shading honest when the light moves. They used to share one pass and
// Math.random() to get that; they are separate passes now because the height
// field depends only on the GRAIN and can be built once for all six plates,
// while the colour map depends on the plate's own hex and markings.
function _rng(seed) {
  var a = seed >>> 0;
  return function () {
    a = (a + 0x6D2B79F5) >>> 0;
    var t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
var GRAIN_SEED = 0x5eed;

// radius/count/jitter for one octave, at whatever PLATE_PX currently is.
// Radii are authored against a 1024 canvas, because the grain is a size on the
// plate rather than a count of texels.
function _octave(o) {
  var r = o[0] * PLATE_PX / 1024;
  return {r: r, n: Math.round(PLATE_PX * PLATE_PX * o[1] / (Math.PI * r * r))};
}

function plateColourMap(spec, g, X, Y, box) {
  var col = _plateCanvas(), cg = _plateCtx(col);
  var base = new THREE.Color(spec.hex);
  var br = base.r * 255, bgr = base.g * 255, bb = base.b * 255;
  var rnd = _rng(GRAIN_SEED);
  cg.fillStyle = '#' + base.getHexString(); cg.fillRect(0, 0, PLATE_PX, PLATE_PX);

  g.octaves.forEach(function (o) {
    var oc = _octave(o);
    for (var i = 0; i < oc.n; i++) {
      var x = rnd() * PLATE_PX, y = rnd() * PLATE_PX;
      var rr = oc.r * (0.5 + rnd());
      var d = (rnd() - 0.5) * 2;
      cg.fillStyle = 'rgba(' + _c(br + d * o[2]) + ',' + _c(bgr + d * o[2]) +
        ',' + _c(bb + d * o[2] * 0.9) + ',' + o[4] + ')';
      cg.beginPath(); cg.arc(x, y, rr, 0, 6.2832); cg.fill();
    }
  });

  // The effect sheet's glitter. Sparse, small and saturated on purpose -- the
  // first pass used big bright flecks at high density and ACES clipped every
  // one of them to white, so a decorative plate rendered as television static.
  if (g.glitter) {
    var lg = cg.createLinearGradient(0, 0, PLATE_PX * 0.4, PLATE_PX);
    lg.addColorStop(0, 'rgba(10,26,34,0.75)');
    lg.addColorStop(1, 'rgba(6,8,12,0.75)');
    cg.fillStyle = lg; cg.fillRect(0, 0, PLATE_PX, PLATE_PX);
    var gn = Math.round(5200 * PLATE_PX * PLATE_PX / 1048576);
    for (var k = 0; k < gn; k++) {
      var gx = rnd() * PLATE_PX, gy = rnd() * PLATE_PX;
      var gr = (0.7 + rnd() * 1.3) * PLATE_PX / 1024;
      cg.fillStyle = 'hsla(' + Math.floor(rnd() * 360) + ',85%,' +
        (28 + rnd() * 26).toFixed(0) + '%,' + (0.5 + rnd() * 0.5) + ')';
      cg.beginPath(); cg.arc(gx, gy, gr, 0, 6.2832); cg.fill();
    }
  }

  plateMarkings(cg, spec, X, Y, box);
  return col;
}

// One per grain, for the life of the page. Six plates share five grains, and
// switching plate used to rebuild this every time.
var _NORMAL_MAPS = {};

function grainNormalMap(grain, g) {
  if (_NORMAL_MAPS[grain]) { return _NORMAL_MAPS[grain]; }
  var bmp = _plateCanvas();
  // willReadFrequently is not a micro-optimisation here. Without it the canvas
  // is GPU-backed and the single getImageData below forces a full readback:
  // measured at 7.5 SECONDS for one plate, which is the whole reason this page
  // sat on its loading spinner for the entire length of a phone screen
  // recording on 2026-09-19. With it, 15 ms.
  var bg = bmp.getContext('2d', {willReadFrequently: true});
  if (!bg) { throw new Error('no 2d canvas context (canvas memory exhausted?)'); }
  var rnd = _rng(GRAIN_SEED);
  bg.fillStyle = '#808080'; bg.fillRect(0, 0, PLATE_PX, PLATE_PX);
  g.octaves.forEach(function (o) {
    var oc = _octave(o);
    for (var i = 0; i < oc.n; i++) {
      // Same draws as the colour pass, same seed, so the two stay registered
      // even though only some octaves carry height.
      var x = rnd() * PLATE_PX, y = rnd() * PLATE_PX;
      var rr = oc.r * (0.5 + rnd());
      var d = (rnd() - 0.5) * 2;
      if (!o[3]) { continue; }
      var h = _c(128 + d * o[3]);
      bg.fillStyle = 'rgb(' + h + ',' + h + ',' + h + ')';
      bg.beginPath(); bg.arc(x, y, rr, 0, 6.2832); bg.fill();
    }
  });
  var t = new THREE.CanvasTexture(heightToNormal(bmp, bg));
  t.anisotropy = _maxAniso;
  _NORMAL_MAPS[grain] = t;
  return t;
}

function _c(v) { return Math.max(0, Math.min(255, Math.round(v))); }

// A greyscale height field is NOT a normal map, and handing one straight to
// `normalMap` is the single worst-looking bug this viewer has had. The shader
// reads rgb*2-1 as a tangent-space vector, so a flat grey field decodes to
// (0,0,0) -- a degenerate normal -- and every slightly-lighter blob decodes to
// a steeply tilted facet that catches a hard specular off the environment.
// Every plate rendered as light-grey blotches on black, which looked like a
// colour bug and was not. This converts properly: central-difference the
// height, build the real tangent normal, encode it back.
function heightToNormal(canvas, ctx) {
  var n = canvas.width;
  var img = ctx.getImageData(0, 0, n, n);
  var src = new Uint8ClampedArray(img.data);   // read from a copy, write in place
  var d = img.data;
  // Per-texel slope, so it has to fall as resolution falls, not rise. A
  // feature spans half as many texels on a 512 map as on a 1024, so the
  // height difference between neighbours is already twice as large; the
  // constant has to halve to keep the same surface. Getting the sign of that
  // wrong (scaling UP with 1024/n) made the textured plate four times too
  // rough and turned it from gold into corrugated orange -- measured, the
  // plate centre went from rgb(119,108,87) to rgb(99,74,44).
  var strength = 6 * n / 1024;
  for (var y = 0; y < n; y++) {
    var yu = ((y - 1 + n) % n) * n, yd = ((y + 1) % n) * n, yc = y * n;
    for (var x = 0; x < n; x++) {
      var xl = (x - 1 + n) % n, xr = (x + 1) % n;
      var dx = (src[(yc + xr) * 4] - src[(yc + xl) * 4]) / 255 * strength;
      var dy = (src[(yd + x) * 4] - src[(yu + x) * 4]) / 255 * strength;
      var len = Math.sqrt(dx * dx + dy * dy + 1);
      var i = (yc + x) * 4;
      d[i]     = Math.round((-dx / len * 0.5 + 0.5) * 255);
      d[i + 1] = Math.round((-dy / len * 0.5 + 0.5) * 255);
      d[i + 2] = Math.round((1 / len * 0.5 + 0.5) * 255);
      d[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return canvas;
}

// Printed markings, placed in millimetres and converted once. Everything here
// is on Bambu's own plates: the product name up the left edge, the filament /
// HOT SURFACE bar across the front tab, and the pair of angled notches at the
// bar's right end.
function plateMarkings(g, spec, X, Y, box) {
  var ox = box[0], oy = box[1], w = box[2], h = box[3];
  // plate mm -> canvas px. Canvas y runs down, plate y runs back.
  function px(mx) { return (mx - ox) / w * PLATE_PX; }
  function py(my) { return PLATE_PX - (my - oy) / h * PLATE_PX; }
  var mm = PLATE_PX / w;
  var ink = '#' + new THREE.Color(spec.ink).getHexString();

  g.save();
  g.globalAlpha = 0.55;
  g.fillStyle = ink;
  g.translate(px(9), py(Y * 0.34));
  g.rotate(-Math.PI / 2);
  g.font = (5.2 * mm).toFixed(1) + 'px system-ui, sans-serif';
  g.textBaseline = 'middle';
  g.fillText('Bambu ' + spec.label, 0, 0);
  g.restore();

  if (spec.bar) {
    g.save();
    g.globalAlpha = 0.6;
    g.fillStyle = ink;
    g.font = (4.4 * mm).toFixed(1) + 'px system-ui, sans-serif';
    g.textBaseline = 'middle';
    var by = py(-3.4);
    g.fillText(spec.bar, px(X / 2 - PLATE_BAR_W / 2 + 22), by);
    g.textAlign = 'right';
    g.fillText('HOT SURFACE', px(X / 2 + PLATE_BAR_W / 2 - 34), by);
    g.strokeStyle = ink; g.lineWidth = Math.max(1, 0.4 * mm);
    g.globalAlpha = 0.35;
    g.strokeRect(px(X / 2 - PLATE_BAR_W / 2 + 8), py(-0.8),
      (PLATE_BAR_W - 16) * mm, 5.4 * mm);
    // the two angled cut-outs at the bar's right end
    g.globalAlpha = 0.5;
    for (var k = 0; k < 2; k++) {
      var bx = px(X / 2 + PLATE_BAR_W / 2 - 26 + k * 11);
      g.beginPath();
      g.moveTo(bx, py(-5.6)); g.lineTo(bx + 7 * mm, py(-5.6));
      g.lineTo(bx, py(-0.9)); g.closePath(); g.fill();
    }
    g.restore();
  }
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
  // This runs every frame, so it is also the thing that would quietly undo
  // the solo framing's hiding one tick after it was applied.
  var solo = colorMode === 'real' && realFraming === 'solo';
  if (amsGroup) { amsGroup.visible = !cut && !solo; }
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
// Dynamic resolution. The one-step quality downgrade below still exists and
// still fires, but it is a single cliff measured once: it cannot help a device
// that is fine on a small plate and drowning on a 3-million-move one, and it
// cannot take advantage of a machine that has headroom to spare.
//
// This scales the render buffer continuously against real measured frame time.
// It is the honest answer to "make it smooth on hardware you cannot test on":
// resolution is the one thing that can be traded for frame rate on any device,
// automatically, without changing what is drawn.
// Floored at 0.7 rather than 0.62: measured, dropping to 0.62 raised visible
// surface speckle from 1.40% to 2.24% of the part. Smooth is not worth that
// much of sharp.
var DPR_MIN = 0.7, DPR_STEP = 0.1;
var FRAME_TARGET = 34;      // ms; ~30fps, the floor for reading a moving print
var FRAME_GOOD = 21;        // ms; only scale back up with real headroom
var dprScale = 1, _ft = [], _lastAdapt = 0;

function adaptResolution(now, dt) {
  if (dt > 0 && dt < 2000) { _ft.push(dt); }
  if (_ft.length < 24 || now - _lastAdapt < 900) { return; }
  _lastAdapt = now;
  _ft.sort(function (a, b) { return a - b; });
  var med = _ft[_ft.length >> 1];
  _ft.length = 0;
  var want = dprScale;
  if (med > FRAME_TARGET) { want = Math.max(DPR_MIN, dprScale - DPR_STEP); }
  else if (med < FRAME_GOOD) { want = Math.min(1, dprScale + DPR_STEP); }
  if (Math.abs(want - dprScale) < 0.001) { return; }
  dprScale = want;
  applyPixelRatio();
}

function applyPixelRatio() {
  var r = basePixelRatio * dprScale;
  // While the camera is actually moving, cap harder still: a frame that is in
  // motion is one nobody is reading detail off.
  if (lowRes) { r = Math.min(r, 1); }
  renderer.setPixelRatio(Math.max(0.5, r));
  onResize();
}

function setResolution(now) {
  var moving = now < moveUntil;
  if (moving === lowRes) { return; }
  lowRes = moving;
  applyPixelRatio();
}

// \u2500\u2500 shader \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
// Positions arrive as Int16 hundredths of a millimetre -- see the exporter's
// note on why. uScale converts back; nothing else in the page sees raw units.

// The beads used to be a raw ShaderMaterial doing its own hand-rolled two-light
// shading against a hardcoded light direction. That is why the print never
// matched the machine around it and never cast a shadow: a raw shader sits
// outside three's lighting, tone mapping and shadow pipeline entirely, so the
// vase floated above a plate it was supposedly sitting on.
//
// It is a real MeshStandardMaterial now, with the per-vertex colour logic
// injected into it. That one change buys, correctly and for free: a shadow
// cast onto the plate, the same environment reflection every metal part uses,
// and the ACES curve. The beads carry real per-vertex normals (see the
// geometry builder) rather than deriving them per facet, which is what stopped
// the part rendering as sandpaper.
var JOB_PARS = [
  'attribute float aType;',
  'attribute float aSpeed;',
  'attribute float aTool;',
  'uniform vec3 uColor[13];',
  'uniform float uVis[13];',
  'uniform vec3 uTool[8];',
  'uniform float uMode;',
  'uniform vec2 uSpd;',
  'uniform float uDim;',
  'uniform vec3 uOverride;',   // filament colour chosen by hand; <0 = off
  'uniform float uLayerH;',    // mm; 0 disables the layer banding
  'varying float vZmm;',
  'varying vec3 vJobColor;',
  'varying float vJobVis;',
  'vec3 magma(float t){',
  '  const vec3 c0=vec3(-0.002136,-0.000750,-0.005386);',
  '  const vec3 c1=vec3(0.251661,0.677523,2.494027);',
  '  const vec3 c2=vec3(8.353717,-3.577720,0.314468);',
  '  const vec3 c3=vec3(-27.668733,14.264731,-13.649213);',
  '  const vec3 c4=vec3(52.176140,-27.943606,12.944169);',
  '  const vec3 c5=vec3(-50.768525,29.046583,4.234153);',
  '  const vec3 c6=vec3(18.655705,-11.489774,-5.601962);',
  '  return clamp(c0+t*(c1+t*(c2+t*(c3+t*(c4+t*(c5+t*c6))))),0.0,1.0);',
  '}'
].join('\n');

var JOB_VERT = [
  '  int jt = int(aType + 0.5);',
  '  float jf = clamp((aSpeed - uSpd.x) / max(uSpd.y - uSpd.x, 1.0), 0.0, 1.0);',
  '  vec3 jByFeature = uColor[jt];',
  '  vec3 jBySpeed = magma(mix(0.92, 0.28, jf));',
  '  vec3 jByFil = uTool[int(aTool + 0.5)];',
  '  vJobColor = uMode < 0.5 ? jByFeature : (uMode < 1.5 ? jBySpeed : jByFil);',
  '  if (uOverride.r >= 0.0) { vJobColor = uOverride; }',
  '  vJobColor = mix(vJobColor, vec3(0.012, 0.013, 0.017), uDim);',
  '  vJobVis = uVis[jt];',
  '  vZmm = position.z * 0.01;'
].join('\n');

function makeMaterial(dim, rich) {
  var u = {
    uColor: {value: TYPE_COLOR.map(function (h) { return lin(h); })},
    uVis:   {value: new Array(N_TYPE).fill(1)},
    uTool:  {value: FILAMENT.map(function (h) { return lin(h); })},
    uMode:  {value: 0},
    uSpd:   {value: new THREE.Vector2(15, 80)},
    uDim:   {value: dim},
    uOverride: {value: new THREE.Vector3(-1, -1, -1)},
    uSat:   {value: DIAG_SAT},
    uLayerH: {value: 0}
  };
  // Printed PLA is neither chalk nor gloss: a matte-satin dielectric. Rich
  // shading buys a tighter lobe and a real environment reflection; the cheap
  // level keeps the same material but barely samples the env map, which is
  // where the per-fragment cost actually sits.
  // The fast path is a different material CLASS, not the same one with the
  // knobs turned down, and that is the whole point. three applies
  // scene.environment to every standard material, and there is no per-material
  // way to opt out of that sample in r128 -- so the only way to stop paying
  // for image-based lighting on 200k triangles is to use a material that has
  // never heard of it. Phong still gets the real lights, the shadow and the
  // tone curve, so fast mode is dimmer in the reflections and identical
  // everywhere else.
  var m = rich
    ? new THREE.MeshStandardMaterial({
        color: 0xffffff, roughness: 0.66, metalness: 0.0,
        envMapIntensity: 0.28, side: THREE.DoubleSide})
    : new THREE.MeshPhongMaterial({
        color: 0xffffff, specular: lin(0x14161a), shininess: 16,
        side: THREE.DoubleSide});
  m.uniforms = u;
  m.onBeforeCompile = function (shader) {
    Object.keys(u).forEach(function (k) { shader.uniforms[k] = u[k]; });
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\n' + JOB_PARS)
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n' + JOB_VERT);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\n' +
               'varying vec3 vJobColor;\nvarying float vJobVis;\n' +
               'varying float vZmm;\nuniform float uSat;\n' +
               'uniform float uLayerH;')
      .replace('#include <clipping_planes_fragment>',
               '#include <clipping_planes_fragment>\n  if (vJobVis < 0.5) discard;')
      // Winding-proof normals.
      //
      // three flips the normal for back-facing triangles on a double-sided
      // material. That is correct when winding is consistent. Slicer polylines
      // are NOT consistently oriented -- some loops run clockwise, some
      // counter-clockwise -- so a correct outward normal gets flipped to point
      // INTO the part on whichever loops happen to be wound the other way, and
      // the surface renders black in patches. It is why supplying real normals
      // first made the part darker rather than cleaner.
      //
      // Orienting to the viewer sidesteps winding entirely: the surface you
      // are looking at is the one being lit, which for a closed shell is what
      // the correct winding would have produced anyway.
      .replace('#include <normal_fragment_begin>',
               '#include <normal_fragment_begin>\n' +
               '  if (dot(normal, vViewPosition) < 0.0) { normal = -normal; }')
      .replace('#include <color_fragment>',
               '#include <color_fragment>\n  diffuseColor.rgb *= vJobColor;\n' +
               // The layer seam. Each bead IS a separate tent with its own
               // normal, so the ridges are already geometrically there -- but
               // at 0.2mm on a 60mm part they are far under a pixel at any
               // sane zoom and average away to a smooth blob. This darkens the
               // real seam height so the banding survives downsampling, the
               // way it does in a photograph of the same part.
               '  if (uLayerH > 0.0) {\n' +
               // Faded out analytically as the band period approaches one
               // pixel. 300 layers across 400px is 1.3px per layer -- right at
               // Nyquist -- and without this the banding aliases into surface
               // noise that reads as a bad render rather than as layer lines.
               // fwidth gives the real on-screen period, so the lines simply
               // stop being drawn at the zoom where a camera could not resolve
               // them either.
               '    float lp = fwidth(vZmm) / uLayerH;\n' +
               '    float lf = 1.0 - smoothstep(0.30, 0.85, lp);\n' +
               '    if (lf > 0.002) {\n' +
               '      float lt = abs(fract(vZmm / uLayerH) - 0.5) * 2.0;\n' +
               '      float lb = mix(1.05, 0.72, smoothstep(0.40, 1.0, lt));\n' +
               '      diffuseColor.rgb *= mix(1.0, lb, lf);\n' +
               '    }\n' +
               '  }')
      // Tone mapping desaturates saturated colour as it brightens, which is
      // correct for a photograph of a print and wrong for a colour key you are
      // meant to read a legend against: after the PBR pass the feature colours
      // came out visibly paler than their swatches. Restored AFTER the curve,
      // where the loss happens, and only in the diagnostic modes -- uSat is 0
      // in real-print mode, which wants the photographic behaviour.
      .replace('#include <tonemapping_fragment>',
               '#include <tonemapping_fragment>\n' +
               '  if (uSat > 0.001) {\n' +
               '    float jl = dot(gl_FragColor.rgb, vec3(0.2126, 0.7152, 0.0722));\n' +
               '    gl_FragColor.rgb = clamp(mix(vec3(jl), gl_FragColor.rgb,\n' +
               '                                 1.0 + uSat), 0.0, 1.0);\n' +
               '  }');
  };
  // Without this three caches one compiled program per material type, and the
  // ghost pass would silently reuse the solid pass's program.
  m.customProgramCacheKey = function () { return 'job|' + dim + '|' + rich; };
  return m;
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
  // Real normals, one byte per component.
  //
  // The beads used to have no normal attribute at all and shaded with
  // flatShading, which derives a normal per triangle from screen-space
  // derivatives. On a bead tent that is one flat facet per extrusion segment,
  // and at any sane zoom those facets are far under a pixel -- so every pixel
  // sampled a different facet's normal and the whole part rendered as dense
  // sandpaper noise. Measured: it survived turning the layer banding off,
  // survived closing the bead's floor, and only ever improved with resolution,
  // which is the signature of sub-pixel shading noise rather than geometry.
  //
  // A tent has three genuinely different surfaces -- outer slope, ridge, inner
  // slope -- and their normals are known exactly from the miter direction that
  // built them. Writing them down makes the bead shade as the rounded extrusion
  // it actually is instead of as a field of facets.
  var vNrm  = new Int8Array(nPt * 3 * 3);
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
    // Exactly 100% of the layer height -- not 85%, and not 104%.
    //
    // The bead is a tent: two bottom corners at zlow, an apex at ztop. At 85%
    // every layer stopped 15% short of the one below it, leaving a continuous
    // horizontal slit around the whole part -- and through those slits you see
    // the unlit inside of the far wall, which is exactly the dark speckle that
    // covered every curved surface. Proved rather than guessed: rendering the
    // part against a magenta clear colour showed the speckle stayed dark grey
    // instead of turning magenta, i.e. gaps in the NEAR wall backed by the far
    // one, not holes through the model.
    //
    // The gap was doing a job -- it was what made layer lines visible. That
    // job now belongs to the shader's banding term, which is antialiased and
    // works at every zoom, so the geometry can close.
    //
    // 104% was tried first, on the reasoning that a real bead squashes into
    // the layer beneath. It made things worse in a different way: the overlap
    // puts two near-parallel 45-degree faces a hair apart, which z-fights into
    // dense speckle. Exact contact is the only value with neither failure --
    // layer pitch is a whole number of the 0.01mm units positions are stored
    // in, so 100% lands exactly and cannot round into either a slit or an
    // overlap.
    var zlow = ztop - Math.round((L[5] || 0.2) * 100);
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
        var ux = ax / m, uy = ay / m;
        var sc = Math.min(2.4, 2 / m) * hw;
        ax = ux * sc; ay = uy * sc;

        vPos[vi * 3] = x + ax; vPos[vi * 3 + 1] = y + ay; vPos[vi * 3 + 2] = zlow;
        vPos[vi * 3 + 3] = x;  vPos[vi * 3 + 4] = y;      vPos[vi * 3 + 5] = ztop;
        vPos[vi * 3 + 6] = x - ax; vPos[vi * 3 + 7] = y - ay; vPos[vi * 3 + 8] = zlow;
        // A point is shared by two segments; take the one ENDING here so the
        // colour changes at the same place the slowdown starts.
        var sv = spd[Math.min(si + Math.max(i - 1, 0), spd.length - 1)];
        // Horizontal on the shoulders, straight up on the ridge: across the
        // outer face that interpolates from facing-out to facing-up, which is
        // the quarter-round of a real extruded bead and averages to the 45
        // degrees the face actually sits at. Tilting the shoulders up as well
        // was tried and left the whole wall shading edge-on and dark.
        vNrm[vi * 3]     = (ux * 127) | 0;
        vNrm[vi * 3 + 1] = (uy * 127) | 0;
        vNrm[vi * 3 + 2] = 0;
        vNrm[vi * 3 + 3] = 0; vNrm[vi * 3 + 4] = 0; vNrm[vi * 3 + 5] = 127;
        vNrm[vi * 3 + 6] = (-ux * 127) | 0;
        vNrm[vi * 3 + 7] = (-uy * 127) | 0;
        vNrm[vi * 3 + 8] = 0;
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
  g.setAttribute('normal', new THREE.Int8BufferAttribute(vNrm, 3, true));
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
  ghostMesh.scale.setScalar(0.01);
  ghostMesh.frustumCulled = false;
  ghostMesh.visible = false;
  jobMesh = new THREE.Mesh(jobGeom, makeMaterial(0.0, richShading));
  jobMesh.scale.setScalar(0.01);
  // Fast mode keeps the machine's shadows and drops the print's. Honest note:
  // this measured as noise on the software rasteriser used for testing here
  // (413ms vs 402ms median), because that renderer is fragment-bound and the
  // shadow pass is not where its time goes. Kept because it is strictly less
  // work for the cheap path to do, not because a speedup was demonstrated.
  jobMesh.castShadow = richShading;
  jobMesh.receiveShadow = true;
  jobMesh.frustumCulled = false;
  scene.add(ghostMesh); scene.add(jobMesh);
  nozzle.visible = true; gantry.visible = true;
  JOB = job;
  applyVisibility();
  shadowDirty = true;
  probeStill(currentId);
  syncStill();
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
// Real print reuses the filament colouring (id 2) -- the beads are already the
// colour of the spool they came off, which is the whole point. What makes it
// "real" is everything around that: what is hidden, how it is lit, and how
// much of the machine is on screen.
var COLOR_MODE_ID = {feature: 0, speed: 1, filament: 2, real: 2};

// Measured against the legend swatches rather than picked by eye: see
// tools/viewer/README.md. 0 in real-print mode, which wants the photographic
// desaturation tone mapping gives it.
var DIAG_SAT = 0.42;

// Sparse infill and the skirt. Nothing else.
//
// The first version also hid the inner perimeter and the solid infill, on the
// reasoning that the outer wall is in front of them. That was wrong in a way
// only the render showed: beads are drawn as open tents, so a one-bead-thick
// shell has gaps between adjacent beads on a curved surface, and through them
// you see the unlit inside of the far wall as dark speckle across the part.
// Keeping both walls backs those gaps, and it is the more honest answer
// anyway -- they are genuinely printed. Supports stay for the same reason:
// real plastic standing on the plate until you snap it off.
var REAL_HIDDEN = {3: 1, 9: 1};

var realFraming = 'live';   // live | static | solo
var filamentOverride = null;
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
  if (!play.on) { shadowDirty = true; }
  syncStill();
  updateAMS(seg);
}

function tick(now) {
  if (JOB && play.on && !play.scrubbing) {
    var dt = play.last ? Math.min((now - play.last) / 1000, 0.1) : 0;
    play.t += dt * play.speed;
    if (play.t >= JOB.total) { play.t = JOB.total; setPlaying(false); }
    setSeg(segAtTime(play.t));
  }
  var _frameDt = _tickLast ? now - _tickLast : 0;
  _tickLast = now;
  play.last = now;
  if (JOB) { refreshReadout(); }
  updateCamera(now);
  setResolution(now);
  adaptResolution(now, _frameDt);
  updateDoor();
  updateCutaway();
  // A growing print changes the shadow every frame in principle, but at a
  // layer every few frames the difference is well under a pixel. Explicit
  // changes (new plate, scrub, door, printer) refresh it immediately.
  shadowFrame++;
  if (shadowDirty || (play.on && shadowFrame % (richShading ? 10 : 30) === 0)) {
    renderer.shadowMap.needsUpdate = true;
    shadowDirty = false;
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

// Seventy-odd plates is past the point where a list alone is browsable, so the
// filter renders only what matches -- which also keeps the out-of-view count
// honest, since it measures cards that exist rather than cards that are hidden.
var plateFilter = '';

function matchesFilter(j) {
  if (!plateFilter) { return true; }
  var hay = (j.name + ' ' + (j.source || '')).toLowerCase();
  return plateFilter.split(/\s+/).every(function (w) { return hay.indexOf(w) >= 0; });
}

function paintJobList() {
  var host = $('jobs');
  host.innerHTML = '';
  host.removeAttribute('data-at');   // or a stale index survives a re-render
  var current = null;
  var shown = INDEX.filter(matchesFilter);
  shown.forEach(function (j, i) {
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
  if (!shown.length) {
    host.innerHTML = '<p class="legnote">No plate matches that.</p>';
  }
  // Says where you are in the list, so seventy plates behind a scrollbar read
  // as seventy plates rather than as however many happen to fit.
  var pc = $('platecount');
  if (pc) {
    pc.textContent = plateFilter
      ? shown.length + ' of ' + INDEX.length
      : (host.getAttribute('data-at') || '1') + ' / ' + INDEX.length;
  }
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
  if (jobMesh) { jobMesh.castShadow = rich; }
  shadowDirty = true;
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
    ((amsGroup.userData.reels || [])[i] || []).forEach(function (f) { f.visible = on; });
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
  var real = mode === 'real';
  var speedy = mode === 'speed', fil = mode === 'filament';
  $('speedpanel').hidden = !speedy;
  $('legend').hidden = speedy || fil || real;
  $('realpanel').hidden = !real;
  applyRealMode();
  if (real) {
    $('legnote').innerHTML = 'The part as it would actually look on the plate: '
      + 'one filament colour, layer lines, and only the surfaces you could see '
      + 'with the door open. Internal walls and infill are hidden because the '
      + 'outer wall is in front of them, not because they are not printed. '
      + '<b>The lighting is still an invented studio rig</b> \u2014 see Limits.';
    applyVisibility();
    return;
  }
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

// The three framings, from "watching the machine run" to "here is the part".
// Live is the existing view untouched. Static stops the head so the part can
// be looked at rather than followed. Solo removes the machine entirely, for
// showing somebody the object rather than the process.
// Measured off the plate rather than assumed to be 0.2: a job sliced at a
// different layer height, or one with supports on its own pitch, would band at
// the wrong spacing. Two consecutive real layer z values, in 0.01mm units.
function layerPitchMm() {
  if (!JOB || !JOB.layers || JOB.layers.length < 3) { return 0.2; }
  var d = (JOB.layers[2][0] - JOB.layers[1][0]) / 100;
  return (d > 0.01 && d < 2) ? d : 0.2;
}

var _wasSolo = false;

// ── path-traced stills ─────────────────────────────────────────────────────
// The realtime view draws each bead as an open tent because it has to hold a
// frame rate; offline there is no frame budget, so the same toolpath can be
// swept as a closed solid and path-traced (tools/gcode_to_mesh.py ->
// tools/blender_render.py). Part-only framing is the one view with nothing
// moving in it, which makes it the one view a photograph can stand in for.
//
// THE STILL IS OF THE FINISHED PART. Showing it while the scrub sits at layer
// 50 would be a picture of something the machine has not built yet, so it is
// only ever shown at the end of the print -- scrub back and the live view
// returns. A plate with no still just stays live; nothing here is required.
var stillOk = {};       // id -> true/false once probed
var stillShown = false;

function stillUrl(id) { return 'stills/' + id + '.jpg'; }

function probeStill(id) {
  if (stillOk[id] !== undefined) { return; }
  stillOk[id] = null;                       // in flight
  var img = new Image();
  img.onload = function () { stillOk[id] = true; syncStill(); };
  img.onerror = function () { stillOk[id] = false; };
  img.src = stillUrl(id);
}

function printIsComplete() {
  return !!(JOB && play.seg >= JOB.nSeg - 1);
}

function syncStill() {
  var el = $('still'), note = $('stillnote');
  if (!el) { return; }
  var want = colorMode === 'real' && realFraming === 'solo'
             && printIsComplete() && stillOk[currentId] === true;
  if (want === stillShown) { return; }
  stillShown = want;
  if (want) { el.src = stillUrl(currentId); }
  el.hidden = !want;
  note.hidden = !want;
  var hint = $('hint');
  if (hint) { hint.style.visibility = want ? 'hidden' : ''; }
}

function applyRealMode() {
  var real = colorMode === 'real';
  var solo = real && realFraming === 'solo';
  var moving = !real || realFraming === 'live';

  // Leaving solo has to put the camera back. frameSolo() targets the part,
  // which after the bed-drop sits a full part-height below z=0 -- bring the
  // machine back without re-framing and you are left underneath the bed
  // looking at the dark underside of it, which is what happened. Ordered
  // before the visibility block because frameJob() re-shows the gantry.
  if (_wasSolo && !solo && JOB) { frameJob(JOB); }
  _wasSolo = solo;
  syncStill();

  // The printable-area ruling and the reserved-corner marker are annotation.
  // Real-print mode is "what this looks like in the machine", and no plate has
  // an orange rectangle painted on it -- so the plate stays, the guides go.
  if (grid) { grid.visible = !real; }
  if (gantry) { gantry.visible = moving && !solo; }
  if (nozzle) { nozzle.visible = moving && !solo; }
  if (yRails) { yRails.visible = moving && !solo; }
  [chamber, doorGroup, amsGroup, bedGroup, floorMesh].forEach(function (g) {
    if (g) { g.visible = !solo; }
  });
  if (ghostMesh) { ghostMesh.visible = ghostMesh.visible && !real; }

  Array.prototype.forEach.call(
    document.querySelectorAll('#realframing button'), function (b) {
      b.setAttribute('aria-pressed',
        String(b.getAttribute('data-framing') === realFraming));
    });
  shadowDirty = true;
}

function setRealFraming(f) {
  realFraming = f;
  if (f === 'solo' && JOB) { frameSolo(JOB); }
  applyRealMode();
}

// frameJob() frames the MACHINE -- it floors the radius so the enclosure keeps
// reading as an enclosure, and parks the target low where the nozzle works.
// With the machine gone both of those are wrong: the part ends up small and
// half out of frame. This frames the part itself.
function frameSolo(job) {
  var b = job.raw.bbox;
  var z = job.layers[job.layers.length - 1][0] / 100;
  var w = Math.max(b[2] - b[0], b[3] - b[1], z, 20);
  cam.tx = (b[0] + b[2]) / 2;
  cam.ty = (b[1] + b[3]) / 2;
  // The P1S drops the BED as it prints, which this viewer models by sinking
  // the print instead -- so a finished part is sitting a full part-height
  // BELOW z=0, not above it. Framing 0..z put the object off the bottom of
  // the screen. Read the mesh's real offset rather than assuming either.
  cam.tz = z * 0.5 + (jobMesh ? jobMesh.position.z : 0);
  cam.r = w * 2.4;
  cam.theta = -0.62;
  cam.phi = 1.12;
}

function setFilamentOverride(hex) {
  filamentOverride = hex;
  Array.prototype.forEach.call(
    document.querySelectorAll('#realswatch button'), function (b) {
      b.setAttribute('aria-pressed',
        String(b.getAttribute('data-hex') === (hex || 'auto')));
    });
  applyVisibility();
}

function applyVisibility() {
  var real = colorMode === 'real';
  [jobMesh, ghostMesh].forEach(function (m) {
    if (!m) { return; }
    var u = m.material.uniforms.uVis.value;
    for (var i = 0; i < 12; i++) {
      u[i] = (real ? !REAL_HIDDEN[i] : visible[i]) ? 1 : 0;
    }
    m.material.uniforms.uSat.value = real ? 0 : DIAG_SAT;
    // Every mode, not just real: closing the bead removed the geometric
    // groove that used to imply layers, and the diagnostic views would
    // otherwise render as one smooth unbroken surface.
    m.material.uniforms.uLayerH.value = layerPitchMm();
    var ov = m.material.uniforms.uOverride.value;
    if (real && filamentOverride) {
      var c = new THREE.Color(filamentOverride).convertSRGBToLinear();
      ov.set(c.r, c.g, c.b);
    } else {
      ov.set(-1, -1, -1);
    }
    m.material.uniforms.uMode.value = COLOR_MODE_ID[colorMode] || 0;
    if (JOB) { m.material.uniforms.uSpd.value.set(JOB.raw.speedMin, JOB.raw.speedMax); }
  });
}

// \u2500\u2500 job loading \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
window.__JOB_LOADED = function (raw) {
  if (!scene) { return; }
  // Geometry build is synchronous and can take a second on the heaviest plate.
  // Yield first so the loading overlay actually paints before the main thread
  // locks -- otherwise the page looks frozen rather than busy.
  requestAnimationFrame(function () { requestAnimationFrame(function () {
    bootStage('Building ' + (raw.name || 'the plate'));
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
    // Name the file this came off, so a plate on screen is something you can
    // go and print rather than something you can only watch.
    var meta = INDEX.filter(function (x) { return x.id === currentId; })[0] || {};
    var src = meta.source ? 'openscad_models/' + meta.source : '';
    // A plate whose path was thinned to fit the page has to say so. The default
    // 0.02mm is a twentieth of a bead and invisible; anything coarser is a real
    // approximation of the toolpath and not something to leave unstated.
    if (meta.simplifyMm && meta.simplifyMm > 0.02) {
      src += (src ? '  \u00b7  ' : '') + 'path simplified to ' +
        meta.simplifyMm.toFixed(2) + ' mm to fit the page';
    }
    $('jobsource').textContent = src;
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
var printerId = 'p1s', materialId = 'PLA', plateId = 'textured';

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
  var plateOpts = Object.keys(PLATES).map(function (k) {
    return '<option value="' + k + '"' + (k === plateId ? ' selected' : '') +
      '>' + PLATES[k].label + '</option>';
  }).join('');
  var pl = PLATES[plateId];
  $('pane-printer').innerHTML =
    '<h3>Machine</h3><select id="psel" aria-label="Printer">' + opts + '</select>' +
    '<p style="margin-top:9px">' + p.note + '</p>' + custom +
    '<h3>Build plate</h3>' +
    '<select id="platesel" aria-label="Build plate">' + plateOpts + '</select>' +
    '<p style="margin-top:9px">' + pl.note + '</p>' +
    '<table class="kv">' +
    row('Surface', pl.face) +
    row('Size', '256 \u00d7 256 mm \u2014 X2D, P2S, P1 series, X1 series, A1') +
    row('Printable area', '0\u2013256 mm in X and Y, origin at the front-left corner') +
    row('Reserved', EXCLUDE_W + ' \u00d7 ' + EXCLUDE_D + ' mm front-left corner (shown in orange)') +
    '</table>' +
    '<div class="caveat"><b>How a print gets aligned on it.</b> The plate is ' +
    'not positioned by eye \u2014 the slot in its rear tab drops over the ' +
    'heatbed\u2019s locating pins, so the machine\u2019s 0,0 lands in the same ' +
    'physical place every time. The slicer then arranges the part inside that ' +
    'square: centred on 128, 128 for a single object, and clear of the reserved ' +
    'corner. <span class="mono">tools/plate_audit.py</span> checks every plate ' +
    'on this page against exactly those two numbers, read out of Bambu\u2019s own ' +
    'P1S machine profile.</div>' +
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
    'correctly, not measured. The AMS is drawn from Bambu\u2019s own product ' +
    'photography of the 4-slot unit \u2014 the smoked dome over the spool row, ' +
    'the drive roller and gear block per slot \u2014 with its proportions taken ' +
    'from the published 368 \u00d7 283 \u00d7 224 mm and the 197\u2013202 mm spool ' +
    'compatibility range. Its spool colours are illustrative; nothing ' +
    'here is reading your machine.</div>';
  $('platesel').addEventListener('change', function (e) {
    plateId = e.target.value;
    buildChamber(PRINTERS[printerId].bed);
    paintPrinter();
  });
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
  $('platefilter').addEventListener('input', function (e) {
    plateFilter = e.target.value.trim().toLowerCase();
    paintJobList();
  });
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

  Array.prototype.forEach.call($('realframing').children, function (b) {
    b.addEventListener('click', function () {
      setRealFraming(b.getAttribute('data-framing'));
    });
  });

  // The swatch row is the real filament palette this shop prints in, so a
  // preview is a colour Scott can actually load rather than an arbitrary hue.
  // AMS stays first and stays the default: it is the only option that cannot
  // be wrong about a multi-colour plate.
  FILAMENT.forEach(function (hex) {
    var b = el('button');
    b.type = 'button';
    b.setAttribute('data-hex', hex);
    b.setAttribute('aria-pressed', 'false');
    b.setAttribute('title', 'Preview this plate in ' + hex);
    b.style.background = hex;
    b.addEventListener('click', function () { setFilamentOverride(hex); });
    $('realswatch').appendChild(b);
  });
  $('realswatch').firstChild.addEventListener('click', function () {
    setFilamentOverride(null);
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

  // The Limits tab carries every caveat that keeps this page honest, and it is
  // the one a first-time visitor is least likely to open. The dot marks it
  // until they do. localStorage can throw (private windows, blocked site data)
  // and the artifact host, GitHub Pages and a file:// folder are three
  // different origins, so a read that fails just shows the dot again -- never
  // breaks the tab.
  var SEEN_LIMITS = 'vp1s.limits.seen';
  try {
    if (localStorage.getItem(SEEN_LIMITS)) { clearLimitsDot(); }
  } catch (e) { /* no storage: the dot stays, which is the safe direction */ }

  function clearLimitsDot() {
    var t = document.querySelector('[data-pane="limits"]');
    if (t) { t.removeAttribute('data-unread'); }
  }

  Array.prototype.forEach.call(document.querySelectorAll('[data-pane]'),
    function (b) {
      b.addEventListener('click', function () {
        Array.prototype.forEach.call(document.querySelectorAll('[data-pane]'),
          function (o) {
            var sel = o === b;
            o.setAttribute('aria-selected', String(sel));
            $('pane-' + o.getAttribute('data-pane')).hidden = !sel;
          });
        if (b.getAttribute('data-pane') === 'limits') {
          clearLimitsDot();
          try { localStorage.setItem(SEEN_LIMITS, '1'); } catch (e) { /* ignore */ }
        }
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
// A throw anywhere in this sequence used to leave the page on its "slicing
// data" spinner forever, with an empty plate list, an empty Printer pane and
// nothing on screen saying why -- reported from an iPhone 2026-09-19 as, with
// complete justification, "it isn't working". A viewer that cannot say what
// went wrong is worse than one that crashed visibly, so it says.
// The overlay's own text node, so a long stage cannot be mistaken for a hang.
function bootStage(label) {
  if (loading.firstChild && loading.firstChild.nodeType === 3) {
    loading.firstChild.textContent = label;
  }
}

function bootFailed(e) {
  var msg = (e && (e.message || e)) + '';
  var at = (e && e.stack || '').split('\n')[1] || '';
  loading.hidden = false;
  loading.innerHTML =
    '<div style="text-align:center;color:var(--bad);padding:0 24px;' +
    'font-family:var(--fm);text-transform:none;letter-spacing:0;line-height:1.55">' +
    '<b>This page failed to start.</b><br>' +
    msg.replace(/[<>&]/g, ' ') + '<br>' +
    '<span style="color:var(--faint);font-size:11px">' +
    at.replace(/[<>&]/g, ' ').trim() + '</span></div>';
}

if (!window.THREE) {
  loading.innerHTML = '<div style="text-align:center;color:var(--bad);padding:0 24px">' +
    'three.js did not load. This page needs cdnjs reachable.</div>';
} else if (!INDEX.length) {
  loading.innerHTML = '<div style="text-align:center;color:var(--bad)">' +
    'No jobs found \u2014 jobs/index.js is missing.</div>';
} else {
  // Order matters, and it used to be wrong. initScene() is by far the most
  // expensive thing on this page and it ran FIRST, so a slow or failing scene
  // left the entire page -- plate list, panels, transport, everything --
  // blank behind a spinner with nothing to read. Painted first, the page is
  // visibly alive within a frame and the spinner is plainly about the 3D view
  // alone. The stage label means a screenshot of a stall says where it stalled.
  try {
    initUI(); paintMaterial(); paintPrinter(); paintJobList();
  } catch (e) { bootFailed(e); throw e; }
  bootStage('Building the machine');
  // Yielding here is what lets that first paint actually happen: initScene()
  // holds the main thread from the first line to the last.
  requestAnimationFrame(function () { requestAnimationFrame(function () {
    try {
      initScene();
      loadJob(INDEX[0].id);
    } catch (e) { bootFailed(e); throw e; }
  }); });
}
})();
