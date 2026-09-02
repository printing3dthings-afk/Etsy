include <BOSL2/std.scad>
include <BOSL2/rounding.scad>

/*
  OnBrandCraftz snap-close box -- two-piece, perimeter bead snap, with the
  brand logo as a FLUSH multi-colour inlay in the lid's top face.

  The whole design is arranged around one printing decision: the lid prints
  UPSIDE DOWN, logo face flat on smooth PEI, so that face comes off the plate
  mirror-smooth. Two consequences drive the geometry:

    * The logo is not engraved and not embossed. It is a separate solid body
      occupying the top `inlay_h` of the lid, exactly filling a matching void
      in the lid body -- so the printed surface is dead flat and the logo is
      purely a filament change in the first few layers.
    * Printed inverted, the lid's top edge becomes a flare rising off the
      plate. A plain fillet there would start at 90 degrees of overhang, so
      the top edge uses os_teardrop(): a circular arc for the shallow part
      and a straight 45-degree run where a fillet would go unprintable.
      Verified by measuring real face normals on the flipped mesh, not by eye.

  The base prints the normal way up, open side up, and needs no supports
  either. Nothing in either part exceeds 45 degrees from vertical.

  Parts to slice (all share one origin -- load lid_body, then add the other
  two as parts of that same object and they land registered):
    part="base"       -- box body
    part="lid_body"   -- lid minus the logo void
    part="lid_script" -- charcoal brush wordmark
    part="lid_swash"  -- gold underline
    part="assembly"   -- preview only, never for slicing
*/

part = "assembly";      // base | lid_body | lid_script | lid_swash | assembly
open  = false;          // assembly preview: lift the lid clear of the base

// ── proportion ──────────────────────────────────────────────────────────
// 1.47:1 footprint. Sized up from a first 92x62 study specifically so the
// logo can be 86mm wide -- see the inlay note below, the script's thin
// strokes set a hard minimum size and the box has to be big enough for it.
box_l  = 106;
box_w  = 72;
base_h = 26;
lid_h  = 14;
sq     = 0.62;          // squircle squareness: 0 = ellipse, 1 = rectangle

lid_wall  = 2.0;        // skirt: thin enough to flex for the snap
lid_top   = 2.4;        // lid ceiling, and the first 2.4mm off the plate
plug_wall = 2.0;        // the locating rim the lid skirt slides over
floor_t   = 3.0;
clear     = 0.2;        // per-side sliding clearance, lid skirt over base plug

// The base wall is DERIVED, not chosen. The plug steps inward from the outer
// face by (lid_wall + clear) to clear the lid skirt, so its own inner face
// lands at box_half - (lid_wall + clear + plug_wall). Setting the base wall to
// exactly that sum puts the plug's inner face flush with the cavity wall: the
// plug becomes simply the top of the wall, rebated on the outside only, fully
// supported, with no internal ledge to overhang.
//
// Getting this wrong is silent. A first pass picked base_wall = 2.4 against a
// 2.65mm step, which left the plug hanging 0.25mm clear of the cavity wall on
// every side -- a completely detached floating ring. It rendered clean,
// reported Simple: yes, and only intersection(base_shell, base_plug) coming
// back EMPTY exposed it. A second pass at 3.2 reattached it but still left a
// 1.0mm unsupported ledge. Keep this derived.
base_wall = lid_wall + clear + plug_wall;

// ── snap ────────────────────────────────────────────────────────────────
// Bead centred on the plug's outer face: stands 0.55 proud, of which 0.25 is
// taken up by the sliding clearance, leaving 0.30mm per side of real
// interference -- mid-range for an annular snap on a 0.4mm nozzle. The groove
// is cut deeper than the bead stands so the bead never bottoms out; the click
// is the skirt springing back, not the bead hitting the groove floor.
// (0.55 proud minus 0.2 of clearance = 0.35mm of real interference per side.)
rim_h   = 9;            // how far the base's inner plug rises above the rim
bead_r  = 0.55;
bead_z  = 5;            // above the base rim, so 5mm up inside the lid skirt

// ── logo inlay ──────────────────────────────────────────────────────────
// Both SVGs are potrace traces of the real brand logo sharing one coordinate
// frame, so ONE scale and ONE offset keeps them registered. Extents measured
// from a real import+export, never read off the viewBox.
//
// They are also pre-flattened to straight segments (tools/flatten_svg_paths.py,
// tol=30 path units ~= 0.05mm here). That is not cosmetic: import() subdivides
// SVG beziers at its own fixed tolerance and ignores $fs/$fa entirely, which
// put 391,576 facets into the script and ran a single boolean against it past
// eight minutes without finishing. Flattened it is 19,596 facets, the same
// bounding box to within 0.001 units, and 15 seconds. If these SVGs are ever
// re-traced, flatten them again before use.
BRAND      = "../assets/brand_vector/";
LOGO_X     = 29.210;    // combined ink bounds across both files
LOGO_Y     = 29.483;
LOGO_W     = 1679.970;
LOGO_H     = 335.995;
logo_w     = 86;        // >= ~70mm or the script's thin strokes drop out
inlay_h    = 0.8;       // 4 layers at 0.2mm -- opaque, no show-through

// ── maker's mark ────────────────────────────────────────────────────────
mark_w     = 42;        // ~40% of box_l, per the sizing rule
mark_depth = 0.7;
MARK       = "../tools/api_server/static/vendor/wordmark/onbrandcraftz-geometric.svg";
MARK_X     = 148.6; MARK_Y = 550.0; MARK_W = 2477.2; MARK_H = 256.8;

$fn = 72;

function sqpath(l, w) = squircle([l, w], squareness = sq, $fn = 96);

plug_l = box_l - 2 * (lid_wall + clear);
plug_w = box_w - 2 * (lid_wall + clear);

// ── base ────────────────────────────────────────────────────────────────
module base_shell() {
    difference() {
        // Bottom edge gets a small chamfer, not a fillet: this face sits on
        // the plate and a rounded bed-contact edge costs first-layer grip.
        offset_sweep(sqpath(box_l, box_w), height = base_h,
                     bottom = os_chamfer(width = 0.6), top = os_smooth(cut = 2.0));
        translate([0, 0, floor_t])
            offset_sweep(sqpath(box_l - 2 * base_wall, box_w - 2 * base_wall),
                         height = base_h, bottom = os_circle(r = 1.5));
    }
}

module base_plug() {
    difference() {
        // Starts 1mm below the rim so it welds into the shell rather than
        // merely touching it -- a shared face does not reliably merge.
        translate([0, 0, base_h - 1])
            offset_sweep(sqpath(plug_l, plug_w), height = rim_h + 1,
                         top = os_circle(r = 1.0));
        translate([0, 0, base_h - 2])
            offset_sweep(sqpath(plug_l - 2 * plug_wall, plug_w - 2 * plug_wall),
                         height = rim_h + 4);
    }
}

module snap_bead() {
    translate([0, 0, base_h + bead_z])
        path_sweep(circle(r = bead_r, $fn = 20),
                   path3d(sqpath(plug_l, plug_w)), closed = true);
}

// mirror([0,1,0]) so the mark reads correctly once the box is picked up and
// turned over -- the axis is Technique 4's, confirmed on a real print.
// It has to be applied to the ALREADY-CENTRED shape: mirroring the raw import
// first (which sits at Y 550..807 in its own units) throws the centring offset
// the wrong way and lands the mark ~23mm off the part entirely. That version
// engraved nothing at all and still rendered and exported clean -- there was
// simply no recess-floor plane in the mesh to find.
module makers_mark() {
    s = mark_w / MARK_W;
    translate([0, 0, -0.5])
        mirror([0, 1, 0])
            translate([-(MARK_X + MARK_W / 2) * s, -(MARK_Y + MARK_H / 2) * s, 0])
                scale([s, s, 1])
                    linear_extrude(height = mark_depth + 0.5) import(MARK);
}

module base_part() {
    difference() {
        union() { base_shell(); base_plug(); snap_bead(); }
        makers_mark();
    }
}

// ── lid ─────────────────────────────────────────────────────────────────
// Modelled at its own origin, z=0 at the rim that lands on the base's
// shoulder. Placed at z=base_h when closed.
module lid_shell() {
    difference() {
        offset_sweep(sqpath(box_l, box_w), height = lid_h,
                     bottom = os_chamfer(width = 0.5), top = os_teardrop(r = 4.0));
        translate([0, 0, -0.01])
            offset_sweep(sqpath(box_l - 2 * lid_wall, box_w - 2 * lid_wall),
                         height = lid_h - lid_top + 0.01);
        // groove sits at the height the bead reaches once the lid's rim is
        // resting on the base shoulder
        translate([0, 0, bead_z])
            path_sweep(circle(r = bead_r + clear, $fn = 20),
                       path3d(sqpath(plug_l + 2 * clear, plug_w + 2 * clear)),
                       closed = true);
    }
}

// The logo prism runs from inlay_h below the top face to well above it;
// intersecting it with the shell gives the inlay, differencing gives the
// void. The two are exact complements by construction.
module logo_prism(which) {
    s = logo_w / LOGO_W;
    translate([-(LOGO_X + LOGO_W / 2) * s, -(LOGO_Y + LOGO_H / 2) * s,
               lid_h - inlay_h])
        scale([s, s, 1])
            linear_extrude(height = inlay_h + 4)
                import(str(BRAND, "onbrandcraftz-", which, ".svg"));
}
module logo_all() { logo_prism("script"); logo_prism("swash"); }

// The two SVGs are already disjoint with a real ~0.15mm gap between them --
// tools/vectorize_brand_logo.py opens that gap in the bitmap, before tracing,
// by cutting the gold mask back from a dilated dark mask. It has to happen
// there: the swash passes under the script's descenders, and subtracting one
// traced outline from the other in OpenSCAD leaves razor-thin slivers that
// make every downstream boolean non-manifold. Do not assume a freshly traced
// pair is safe to boolean directly.
module lid_body_part()   { difference()   { lid_shell(); logo_all(); } }
module lid_script_part() { intersection() { lid_shell(); logo_prism("script"); } }
module lid_swash_part()  { intersection() { lid_shell(); logo_prism("swash"); } }

// ── output ──────────────────────────────────────────────────────────────
lid_z = open ? base_h + 34 : base_h;

if (part == "base")            base_part();
else if (part == "lid_body")   lid_body_part();
else if (part == "lid_script") lid_script_part();
else if (part == "lid_swash")  lid_swash_part();
else {
    color("#7E6A93") base_part();
    translate([0, 0, lid_z]) {
        color("#B9A8CC") lid_body_part();
        color("#2E2E2E") lid_script_part();
        color("#B48B53") lid_swash_part();
    }
}
