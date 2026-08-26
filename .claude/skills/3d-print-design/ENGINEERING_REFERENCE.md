# 3D Print Engineering Reference — OpenSCAD/BOSL2, Blender, and Real FDM Design Rules

Added 2026-08-25, per Scott's request for "senior level" 3D design knowledge, not
just what's worked so far. This is a **theory/technique reference**, distinct from
`.claude/skills/3d-print-design/SKILL.md`, which stays a log of real bugs found
while building actual models (per Scott's explicit direction to keep those
separate). Read this BEFORE starting a genuinely new class of model (first
mechanical part, first print-in-place joint, first time reaching for Blender) —
SKILL.md is where the specific gotchas of *this shop's* actual builds live.

Every claim below is sourced from real documentation, engineering guides, or
forum-reported field data gathered 2026-08-25 — not generic "AI 3D printing
tips" blogspam. Numbers are ranges because they're genuinely printer/material-
dependent, not because the research was sloppy; where a source gives a single
number, it's stated as such.

---

## 1. Tool choice: OpenSCAD stays primary, Blender is a narrow secondary tool

**Verdict, and why:** for anything with real dimensions — mechanical parts,
snap-fits, gears, threads, precise assemblies — stay in OpenSCAD. Blender's
Boolean modifier is documented as measurably less reliable than OpenSCAD/CGAL
for exactly this kind of work: a real Blender bug report (T66593) describes
"unpredictable results when executed in a loop via Python API," and separate
Blender Artists threads report a Boolean Union turning a manifold object
non-manifold. For an agent doing unattended, code-generated CSG on engineering
dimensions, that's a real regression risk, not a hypothetical one — OpenSCAD's
CGAL-backed booleans are the right tool for anything that needs to be *exactly*
right.

**What Blender genuinely adds, and how to use it correctly:** true organic
double-curvature — a form with no describable swept/lofted/revolved profile —
is fundamentally out of reach of OpenSCAD's CSG. Blender's Subdivision Surface
modifier (Catmull-Clark) and Geometry Nodes are both **genuinely scriptable
end-to-end with zero human clicking**, via `blender --background --python
script.py` calling `bpy` — this is a mature, real pattern (see NYT's
`rd-blender-docker`, Cornell's own "STL Scripting in Blender" guide). Sculpt-mode
brushes are NOT scriptable this way — that's an honest limit, not a gap to
paper over; the scriptable substitute for organic surface *variation* (not
deliberate sculpted shape) is a Displace modifier or Geometry Nodes driven by a
procedural noise texture.

**The correct integration pattern, if/when this gets built:** OpenSCAD builds
the precise, dimensioned structure and exports STL → Blender (headless,
`--background`) imports that STL, applies Subdivision Surface for pure organic
smoothing (never Boolean operations on the OpenSCAD-built structure) → re-export
STL. This is a documented real workflow (OpenSCAD forum, BrainVoyage's guide),
not an invented one. **Not built yet as an actual tool** — no
`render_blender_model` wrapper exists in this codebase. Build one (matching
`tools/openscad_render.py`'s shape: subprocess wrapper, `xvfb-run` for the same
"no display" problem OpenSCAD already solved, clear error on missing binary) the
first time a real design genuinely needs Subdivision Surface refinement that
OpenSCAD's `rounded_prism()`/`offset_sweep()` (below) can't achieve — not
speculatively ahead of that need.

Sources: [T66593 Blender bug tracker](https://developer.blender.org/T66593),
[Boolean Union → non-manifold, Blender Artists](https://blenderartists.org/t/boolean-union-modifier-on-manifold-object-produces-non-manifold-object/700896),
[Cornell CNF — STL Scripting in Blender](https://confluence.cornell.edu/display/CNFUserWiki/STL+Scripting+in+Blender+for+3D+Printing),
[nytimes/rd-blender-docker](https://github.com/nytimes/rd-blender-docker),
[SubsurfModifier API](https://docs.blender.org/api/current/bpy.types.SubsurfModifier.html),
[OpenSCAD forum — import STL from Blender](https://forum.openscad.org/import-stl-from-blender-export-td9599.html)

---

## 2. Organic/smooth surface tools in OpenSCAD/BOSL2 — beyond what this shop has used

- **`rounded_prism()`** — genuinely new to this shop. Connects two same-vertex-
  count polygons (a loft's top/bottom profile) with continuous-curvature bezier
  roundovers (`joint_top`/`joint_bot`/`joint_sides`, `k`≈0.8 for a circular-
  looking curve). This is the correct tool for rounding a vase rim or an
  organizer's top edge — it produces genuine curvature, not a chamfer mask.
  Should replace ad-hoc skin()-based rounding wherever an end needs to look
  truly rounded rather than beveled.
- **`offset_sweep()`** — builds a solid from a 2D polygon whose offset varies
  along the extrusion height. The right tool for a profile that needs to flare,
  taper, or round non-uniformly along its length without hand-building a
  `skin()` profile list for it.
- **`minkowski()` for fillets — avoid, don't reach for by default.** It's
  correct but "so slow it's only recommended if desperate"
  ([Scorch Works](https://www.scorchworks.com/Blog/openscad-modules-for-automatic-fillets-and-radii/)),
  and concave-operand minkowski specifically regresses badly even on the newer
  Manifold render backend because it falls back to slow CGAL Nef conversion.
  `rounded_prism()`/BOSL2's cuboid `rounding=` parameter (already used in this
  shop's organizer work) cover the common cases without this cost.
- **Bezier path tools (`bezpath_curve()`, `path_to_bezpath()`, `bez_tang()`)** —
  a real upgrade over plain `smooth_path()` when a curve must pass *exactly*
  through given control points (an approximating spline like `smooth_path()`
  doesn't guarantee that) or when two curve segments need a matched tangent at
  their join for a genuinely seamless-looking profile.
- **`surface(file="x.png")`** — reads pixel luminance as a Z-heightfield,
  genuinely usable for engraved/embossed texture from a real image. Real
  limitation: it only produces a flat displaced grid — there's no native way to
  wrap a heightfield texture around a curved surface (e.g. bark texture around
  a cylindrical trunk); that would need a custom per-point angular remap, not
  a built-in.
- **The honest ceiling:** anything expressible as a swept/lofted profile, a
  revolve, or a bezier-defined cross-section is achievable and can look
  genuinely smooth in OpenSCAD. Freeform sculpted asymmetry (a face, a flowing
  form with no describable profile) is fundamentally a mesh-sculpting problem —
  see §1's Blender guidance rather than fighting CSG for it.

Sources: [BOSL2 rounding.scad](https://github.com/BelfrySCAD/BOSL2/wiki/rounding.scad),
[BOSL2 Beziers tutorial](https://github.com/BelfrySCAD/BOSL2/wiki/Tutorial-Beziers_for_Beginners),
[Wikibooks Surface Module](https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Importing_Geometry/Surface_Module),
[Scorch Works fillets](https://www.scorchworks.com/Blog/openscad-modules-for-automatic-fillets-and-radii/)

---

## 3. Mechanical components in BOSL2 — real modules, not hand-rolled geometry

- **`gears.scad`** — real involute-tooth gear generation (`spur_gear2d()` and
  full 3D modules), standard params (circular pitch, pressure angle, helical
  angle). **Not FDM-print-safe at zero backlash as generated** — offset each
  tooth flank inward 0.1–0.2mm (0.2–0.4mm total meshing clearance) or teeth
  bind from perimeter over-extrusion; oversize bores ~0.1–0.2mm.
- **`hinges.scad`** — `knuckle_hinge()` (real pin-and-barrel geometry),
  `living_hinge_mask()`. Ships in BOSL2 directly — use these instead of hand-
  rolling hinge geometry from primitives.
- **`hingesnaps.scad`** (community fork) — `snap_lock()`/`snap_socket()`, a
  parametric snap-lock hinge with a `hingegap` fold-clearance parameter.
- **`threading.scad`/`screws.scad`** — real ISO/UTS/ACME/buttress threads with
  proper tolerance-class tables. FDM-specific advice from the library's own
  community: blunt-start threads, raise `$slop` for internal threads. **But the
  professional standard for anything assembled more than once is a heat-set
  insert, not a printed thread** — printed threads round out after ~5–10 cycles
  on small sizes. Insert-boss design: hole 1–2mm deeper than insert length (burr
  relief), 4–6 perimeter walls around the boss.
- **`attach()`/`attachable()`** — genuinely useful for mechanical precision, not
  just cosmetic positioning. Named-anchor referencing (`position()`, `attach()`,
  `spin=`) lets a multi-part assembly's mating features track each other as
  parametric dimensions change, instead of hand-tracked absolute coordinates
  that silently drift out of alignment when one dimension changes.

Sources: [BOSL2 gears.scad](https://github.com/BelfrySCAD/BOSL2/wiki/gears.scad),
[EngineerDog FDM gear guide](https://engineerdog.com/2017/01/07/a-practical-guide-to-fdm-3d-printing-gears/),
[BOSL2 hinges.scad](https://github.com/BelfrySCAD/BOSL2/blob/master/hinges.scad),
[BOSL2 threading.scad](https://github.com/BelfrySCAD/BOSL2/blob/master/threading.scad),
[FacFox heat-set inserts](https://facfox.com/docs/kb/mastering-heat-set-inserts-a-professionals-guide-to-durable-3d-printed-threads),
[BOSL2 Attachments tutorial](https://github.com/BelfrySCAD/BOSL2/wiki/Tutorial-Attachments)

---

## 4. Real FDM tolerance numbers (Bambu P1S, 0.4mm nozzle) — ranges, not guesses

| Fit type | Clearance |
|---|---|
| Loose sliding fit | 0.3–0.6mm total diametral |
| Snug press/location fit | 0.1–0.2mm total (0.0–0.1mm for true interference) |
| Rotating joint, assembled post-print | 0.2–0.3mm per surface |
| Print-in-place joint (pin/ball, printed already assembled) | 0.2–0.3mm sweet spot; 0.15–0.2mm achievable on a well-calibrated machine; below ~0.15mm, real fusion risk from ordinary over-extrusion/elephant's-foot |
| Ball-and-socket specifically | 0.4–0.5mm — needs MORE than a pin hinge because the enclosed geometry traps heat and fuses more easily |
| Internal threads | Oversize +0.2–0.4mm diameter |
| External threads | Undersize −0.1–0.2mm |

**Print-in-place is a per-material, per-printer calibration, not a universal
number.** 0.3mm that works fine in PLA can fuse solid in PETG (PETG needs
~0.4mm). Real practice: print a dedicated pin/hinge tolerance test coupon in
0.1mm increments (0.1–0.5mm) per material before committing a real product
design — don't assume the numbers above transfer without a physical check.
Reduce Bambu Studio's "slice gap closing radius" (e.g. to 0.03mm) for
print-in-place models — its default behavior can bridge and weld small
intentional gaps shut.

**Anisotropic strength — the design-shaping fact.** Z-axis (interlayer)
strength is **~40–75% of XY-plane strength** (multiple sources converge near
~55%), and Z-axis *ductility* is worse still (10–30% of XY elongation) — Z-
loaded parts fail more brittle, not just weaker, because layer bonding is
diffusion-based, not a true weld. **Concrete design consequences:**
- Snap-fit cantilevers: flex direction must be in-plane (perpendicular to the Z
  stack), never printed vertically — one source measured 20–30% tensile
  strength loss and 50% elongation loss for a Z-oriented cantilever.
- Gear teeth: print with the gear axis along Z so tooth-root bending is
  resisted by in-plane strength, not interlayer adhesion.
- Living hinges: the flex axis must run parallel to layers (hinge printed
  flat, bending in-plane) — never flexing across a layer boundary.
- Screw bosses: pull-out load is often axial (Z), a known weak axis — oversize
  wall thickness around the boss rather than assuming default thickness holds.

Sources: [Hubs — design parts for FDM](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/),
[Hubs — threaded fasteners](https://www.hubs.com/knowledge-base/how-assemble-3d-printed-parts-threaded-fasteners/),
[AON3D Engineering Fits](https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/),
[FacFox — print direction vs strength](https://facfox.com/docs/kb/how-3d-printing-direction-orientation-affects-strength),
[Bambu Lab forum — PIP hinge tolerances](https://forum.bambulab.com/t/print-in-place-hinge-tolerances/111715),
[Sovol — PIP hinges/joints](https://www.sovol3d.com/blogs/news/print-in-place-3d-printing-how-to-design-hinges-joints-and-mechanisms)

---

## 5. Snap-fits and living hinges — real numbers, and an honest material warning

**Cantilever snap-fit:**
- Undercut/catch clearance: 0.5mm · minimum cantilever width: 5mm
- Root fillet radius: **≥0.5× base thickness** — mandatory, this is where FDM
  parts crack first
- Taper beam thickness from 100% at root to ~50% at tip, to spread strain along
  the length instead of concentrating it at the root
- L/t ratio: 8:1–10:1 for stiffer/more brittle materials (PLA), 5:1–8:1 for
  tougher materials (PETG) — this specific ratio is a secondary-source rule of
  thumb, not a validated formula; treat it as a starting point to physically
  test, not an engineering constant
- **PLA is explicitly discouraged for snap-fits** — too brittle at the root
  under repeated flex. ABS/nylon/PETG/TPU preferred.

**Living hinges — real thickness number, and a material honesty check the
shop's cardinal "never lie to the customer" rule directly requires:**
0.4–0.6mm hinge thickness, minimum 2 layers, below ~0.3mm too fragile to print
reliably. **PLA and PETG are genuinely NOT good living-hinge materials** — PLA
fails quickly under repeated flex, PETG is workable but not durable for high-
cycle use. Polypropylene is the real best-practice living-hinge material
(matches injection-molded convention) but is notoriously hard to bed-adhere on
FDM without a PP-specific setup this shop doesn't currently have. **Realistic
option within this shop's existing materials: TPU, or a dual-material design
(rigid PETG/PLA shell + TPU flex hinge via AMS).** Any listing describing a
"flexible living hinge" printed in plain PLA/PETG must be scoped honestly to
low-cycle/decorative use — claiming it survives repeated real use in those
materials would be exactly the kind of unverified compatibility/durability
claim the shop's top-priority truthfulness rule forbids.

Sources: [Hubs — snap-fit joints](https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/),
[Hubs — living hinges](https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/),
[Mandarin3D — living hinges](https://mandarin3d.com/blog/designing-living-hinges-for-flexible-3d-prints)

---

## 6. Infill and walls — decorative vs. load-bearing parts

Prusa's own knowledge base is explicit: **part strength is mostly defined by
perimeter count, not infill** — infill's main job is supporting top layers for
bridging, not overall strength.

| | Decorative (this shop's current default) | Load-bearing/mechanical |
|---|---|---|
| Perimeters | 2 | 3–5 (5 for large/stressed gears) |
| Infill % | 15–20% | 30–50% |
| Pattern | not critical | gyroid or cubic (isotropic, strongest general-purpose); honeycomb for best strength-to-weight when minimizing mass matters more than absolute strength |

Gear-specific real number: 5 walls + minimum 35% infill, given tooth-root
stress concentration.

Sources: [Prusa KB — Layers and Perimeters](https://help.prusa3d.com/article/layers-and-perimeters_1748),
[Prusa Forum — settings for functional strength](https://forum.prusa3d.com/forum/original-prusa-i3-mk3s-mk3-how-do-i-print-this-printing-help/settings-for-functional-strength/),
[Zbotic — infill patterns compared](https://zbotic.in/slicer-infill-patterns-compared-which-is-strongest-and-fastest/)

---

## 7. What's genuinely trending (2026) — grounding for what to design next

**MakerWorld:** print-in-place articulated animals are a whole active genre
(a dedicated 178-model "Flexi" collection), not a niche — Flexi Spider (17.6k
likes/7.3k downloads), Flexi Penguin (14.6k/7.3k), Articulated Baby Capybara
(14k/5.9k). Pure-mechanism kinetic gear pieces also perform well but don't
combine organic form with mechanism the way the animal genre does.

**Etsy:** two independent 2026 seller-guide sources name flexi/articulated
animal figurines (sold in multipacks) as a dominant top-selling 3D-printed
category specifically — dragons, cats, frogs, pangolins, axolotls named by
name. A 25-piece animal figurine set was estimated at ~4,275 units/month at
$13.56.

**How the joints actually work:** print-in-place articulation is a deliberate
air-gap the slicer can't bridge with plastic — the parts are modeled already
assembled. Real numbers: 0.2–0.3mm for a pin-in-barrel hinge; 0.4–0.5mm for a
ball-and-socket (needs more because trapped heat fuses it more easily); joint
axis oriented so each printed layer bridges cleanly across the gap as an
expanding/contracting ring, rather than printing an overhang directly onto the
mating part.

**What this points to as a genuinely well-grounded next build:** a smooth-
bodied organic animal (axolotl, otter, or similar rounded creature — the
dragon category is already saturated) using print-in-place ball-and-socket
joints for spine/limb articulation. This is the one object type that
demonstrates organic surface quality, real non-trivial mechanical joint design,
and sits directly in the best-evidenced trending category on both platforms at
once.

Sources: [MakerWorld Flexi Animal collection](https://makerworld.com/en/collections/2059692-flexi-animal),
[3DSEARCH — best-selling 3D printed Etsy items 2026](https://3dsearch.net/blog/best-selling-3d-printed-items-etsy-2026),
[Insight Agent — best-selling 3D printed items](https://www.insightagent.app/guides/best-selling-3d-printed-items-etsy),
[Sovol — PIP hinges/joints design guide](https://www.sovol3d.com/blogs/news/print-in-place-3d-printing-how-to-design-hinges-joints-and-moving-parts-that-actually-work)
