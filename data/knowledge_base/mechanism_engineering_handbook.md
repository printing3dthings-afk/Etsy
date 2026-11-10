# Mechanism engineering handbook: printed parts that work in the hand

2026-11-10. Written after the Fold Stand failed twice. v1 had "No click at
all. Very loose pin falls out." v2 "does not work". Scott: "You need to learn
more modeling engineering ... Your ability and design technique need to be at
a much higher level."

**This handbook is mandatory for anything that moves, clicks, locks, snaps,
holds an angle, or takes a load.** That covers hinges, catches, lids, threads,
stands and clips. Load it alongside the 3d-print-design skill. The calculator
is `tools/mechanism_budget.py`.

## 0. Why both stands failed, and what our checks can't see

Every stand passed every check we had:
- watertight;
- overhangs within limits;
- walls ≥ 1.2 mm;
- 0 slicer supports;
- a sectioned ratchet check of the CAD geometry.

**Those checks prove the model can be printed. They don't prove the mechanism
works once it is printed.** A printer misses every dimension by a little, and a
mechanism works only if it still works with those misses stacked against it.

The engineering that was missing is hand calculation, done before modelling:
1. how much each dimension can be off;
2. how deep a catch must be to survive that;
3. how hard a spring arm can bend before it cracks or creeps;
4. how much force or torque the joint must hold.

Run through `tools/mechanism_budget.py --demo`, v2's hinge fails four of five
basic checks (section 8). Nothing in the geometric gates could have caught it.

## 1. What the printer really does (P1S, 0.4 nozzle, 0.2 layers, PLA)

Values are ± per feature on a tuned machine. Sources and quality are noted:
most published "tolerance tables" are practitioner rules of thumb, not
controlled studies.

| feature | typical error | why |
|---|---|---|
| outer wall in XY | ±0.10 mm | extrusion width and flow; corners rounded to ~the nozzle radius |
| height of a feature | ±0.10 mm (½ a 0.2 mm layer) | heights quantise to layers; a slope becomes stairs |
| vertical hole (axis along Z) | prints **0.1–0.4 mm small** on Ø4–6 mm, 0.1–0.2 mm small over Ø30 | the bead's inner edge; polygon facets. Compensate in the model or with Bambu's X-Y hole compensation |
| horizontal hole (axis along X/Y) | ±0.25 mm, oval | the top is a bridge or a teardrop and sags; the sides stair-step at 0.2 mm |
| lip, ridge or tooth standing out of an upright wall | ±0.2 mm | it is a short overhang; the first layers of it droop |
| first layer (bed face) | +0.1–0.2 mm flare (elephant's foot) | the first layer is squashed; use the slicer's compensation or a 0.4 mm chamfer |
| smallest gap that stays open between parts | **≥ 0.3 mm** (0.2 on a perfectly tuned machine, in PLA) | smaller gaps weld or drag |
| sharp internal corner | radius ≈ 0.2 mm (½ nozzle) at best | the nozzle is round |
| tooth, rib or notch narrower than 2 beads (0.8 mm) | shape not reproduced | the slicer drops or merges it (print_fidelity sees this) |

Sources: Zbotic and 3dprintcalcs tolerance guides (rules of thumb), a euspen
2026 abstract (Bambu X1C, PLA, 0.4 nozzle: XY overshoot +0.02 mm on small
features, only ~30 % of 25 mm parts within IT7), Gebre et al. 2026 (accuracy
varies with direction, size and place on the bed), and Bambu forum "Precision
of FDM". Accuracy differs by direction and by machine, so **measure it**. The
shop's own Fit Test Plate exists for exactly this: its results should be the
design inputs. They were never recorded (section 7).

## 2. The engagement rule: a catch must outlast the error stack

List every dimension between the two surfaces that must engage, with its ±
from section 1. Then:
- **worst case** = the sum of the ± values: every error at its limit at once.
- **RSS** = √(sum of squares): the expected spread when the errors are
  independent.

**Rule:** an engagement depth (detent, ratchet tooth, snap undercut, latch
catch) must be **≥ 3 × RSS, and deeper than the worst case.** Then with every
error at its limit, something is still engaged.

A clearance must be the smallest open gap (≥ 0.3 mm), plus the worst case of
the errors that could close it.

**Worked: v2's ratchet.**
- The stack:
  - pin radius ±0.10;
  - horizontal bore radius ±0.25;
  - ridge out of an upright wall ±0.20;
  - ridge top face ±0.10;
  - blade position ±0.10.
- RSS 0.36 mm; worst case 0.75 mm.
- The notches were **0.45 mm**. They needed **≥ 1.1 mm**.
- With the bore 0.25 big and the ridge 0.2 short, the ridge never touched a
  notch: "no click".

**Consequence:** in FDM, functional engagements are **millimetres, not tenths
of a millimetre.** If a design needs sub-millimetre engagement to fit, the
mechanism is too small. Make it bigger, or move the precision into metal
hardware (section 6).

## 3. Material data for design

| | PLA (printed) | PETG (printed) | source quality |
|---|---|---|---|
| modulus E, XY | ~2.3–3.0 GPa (calculator: 2.6) | ~1.8–2.1 GPa | datasheets and papers |
| yield strain | ~2–3 %, brittle | ~4 % | datasheets |
| **permissible strain, one snap** | ~1.4 % (≈70 % of yield) | ~2.8 % | Bayer rule: amorphous plastics to ~70 % of yield strain |
| **permissible strain, repeated** | **~0.8 %** | ~1.7 % | Bayer: ~60 % of the one-time value for frequent separation |
| Z (across-layer) strength | ~40–75 % of XY, commonly ~55 %; brittle | similar | Formlabs-cited FDM test; Fayazbakhsh 2019 review |
| friction μ, dry, on itself | ~0.35–0.55 kinetic (calculator 0.45) | ~0.3–0.4 | Pawlak 2018/2020 pin-on-disc; Stoimenov 2024 |
| glass transition | ~55–60 °C | ~75–80 °C | datasheets |
| creep | significant under constant load, worse at 40 °C (a car); depends on build direction | less than PLA | sv-jme (10 and 20 MPa at RT, 40, 60 °C); SciELO (25–50 % of yield at 30 °C) |

**Design consequences:**
- **A PLA spring arm loses its preload.** Held bent, it relaxes, so a detent
  that clicks crisply on day one clicks weakly by day thirty. Keep held strain
  low (< 0.5 %).
  - Better: let an arm sit unbent at rest and bend only while clicking.
  - Or use a metal spring.
- **Never bend across layers.** A flexure's bend must be in the print plane,
  with layers running along its length.
- **PLA for snaps is marginal.** The Hubs and Covestro guidance is that PLA is
  too brittle for repeated snap use. For a repeatedly flexed part, prefer
  PETG; for a high-cycle hinge, TPU.
- **Hot places:** a PLA stand on a car dashboard will creep and soften. Say
  so in listings, or use PETG.

## 4. Spring arms, snaps and flexures: the equations (Covestro/Bayer guide)

**Cantilever of rectangular section.** Thickness h along the bend, length l,
width b, tip deflection y:
- constant section: **y = 0.67 ε l² / h**, so **ε = 1.5 h y / l²**;
- tapered to h/2 at the tip: **y = 1.09 ε l² / h**, which takes 60 % more
  deflection at the same strain;
- deflection force: **P = (b h² / 6) · E · ε / l**;
- mating (push-in) force over a ramp of angle α with friction μ:
  **W = P (μ + tan α) / (1 − μ tan α)**.

A retaining face self-locks (can't be pushed apart) when 1 − μ tan α ≤ 0, that
is when its angle is within atan(μ) of square. For PLA, atan(0.45) ≈ 24°: a
face within about 66–90° of the pull holds.

**Rules (Bayer, Hubs; the ones marked are rules of thumb):**
- **Root fillet:** R/h ≈ 0.5–0.6 cuts the stress concentration most. Never a
  sharp root: the crack starts there.
- **Taper** the arm to half thickness at the tip.
- **Width ≥ 5 mm** (rule of thumb).
- **Length:** l/h of 8–10 for PLA, 5–8 for PETG (rule of thumb). Check the
  strain with the formula; don't trust the ratio.
- **Undercut** = the engagement depth, sized by section 2, not the other way
  round. If the strain limit won't allow the deflection that the needed depth
  requires, lengthen the arm or change the mechanism.
- **Compliant mechanisms** (BYU, Howell): treat a short thin flexure as a
  pivot with a torsion spring (the pseudo-rigid-body model). The same strain
  limits apply at the thinnest section. Printed flexures fail at layer lines
  and creep. For anything high-cycle, a metal spring or TPU beats a PLA flexure.

## 5. Ways to hold an angle, ranked by how reliably they print

**1. Geometric lock with big features (best).** A leg, prop or tab sits in one
of several notches, each **≥ 3–5 mm deep**.
- Examples: a notched base with a prop leg (the easel), a slotted back.
- Nothing bends. The load sits on solid plastic, gravity keeps it in, and
  errors of 0.5 mm don't matter.
- This is what the most reliable printed phone and tablet stands use.

**2. Face-gear (Hirth / crown) lock with a screw and knob** (camera-tripod
style).
- Two discs of radial teeth, about 1.5–2 mm tall and 15–24 teeth on Ø20–30,
  are clamped together by an M3/M4 screw and a printed knob. Loosen, set,
  tighten.
- The teeth carry the load and the screw only clamps, so it's very strong.
- Takes an M3 screw, a nut or insert, and the knob. Printable designs:
  "Adjustable Simple Locking Hinge with Thumbscrew" on MakerWorld (serrated
  teeth stop it slipping).

**3. Friction hinge.** An M3 bolt and nylock nut clamp the barrels through an
elastic element (an O-ring or TPU washer) that keeps the clamp force as the
plastic creeps.
- Infinitely adjustable, but its holding torque depends on the clamp and on
  creep. Size it for **≥ 3 × the gravity torque**.
- PETG or better, pivot holes printed through the layers. The "Adjustable
  Geared Hinge with Screws" and the TPU-core friction hinge designs use this.

**4. Ratchet and pawl.**
- **Tooth profile:** a steep locking face at **85–92°** and a ramp at
  30–45°.
- **Self-locking:** the contact normal must pass on the engagement side of the
  pawl pivot by a few degrees, so load drives the pawl deeper.
- **Size for FDM:** teeth **≥ 1 mm tall** (section 2) at a pitch ≥ 2.5 mm, so
  each tooth is ≥ 3 beads wide.
- That needs a wheel of **Ø ≥ 25–30 mm** for 12° steps. A 4 mm pin can never
  carry a printable ratchet.
- **The pawl:** a metal spring, or a PETG arm checked by section 4. Printed
  examples work at sizes like these, not at pin size.

**5. Detent (a click with no lock).** A spring-loaded bump in a dimple.
- It only resists a torque of about F·r·tan(flank angle). It can't hold a
  lever-arm load (v1's mistake, as a reasoning error: a 0.35 mm click can't
  hold a 350 N·mm phone torque).
- Use detents for feel, never as the lock.

**For a phone stand:**
- A 200 g phone about 60 mm from the hinge needs **~350 N·mm with a ×3
  factor**.
- An A-frame stand also spreads at the feet. Either lock the hinge, or tie the
  feet, or use a single prop in notches.
- Printables/MakerWorld stands that work use notched backs, a prop leg in
  base slots, or a screw-clamped hinge. Fully printed micro-ratchets are rare.

## 6. Metal hardware: where the precision should live

- **M3 heat-set insert:** hole **Ø4.0 mm** (3.85–3.9 mm for soft PLA), 1 mm
  deeper than the insert, **wall ≥ 1.6–1.8 mm**. Set it with the soldering-iron
  tip.
- **M3 clearance hole:** Ø3.4 mm. A captive nut trap is a hexagon 5.7–5.8 mm
  across the flats.
- **Hinge pins:** steel dowel pins or an M3 bolt beat printed pins.
  - Print the hole slightly small, then ream it or test with a clearance
    series.
  - **Bolt holes run through the layers** (axis along Z) where possible.
    Across the layers, a screw can split the part.
- **Filament as a pin:** 1.75 mm filament in a Ø1.9–2.0 mm hole, melted over
  at the ends. A proven, cheap pin.
- **Springs and magnets** give consistent force that doesn't creep. Use them
  whenever a printed flexure would have to hold force for a long time.

## 7. The process: mandatory for every mechanism from now on

1. **Requirement, with numbers.** What it holds (N or N·mm) and how many
   cycles. How it is assembled, and with what hardware.
2. **Concept from section 5,** the most robust class that meets it. Say why
   the simpler class isn't enough.
3. **Hand calculations** in `tools/mechanism_budget.py`:
   - strain and force in every flexing part;
   - the engagement against the tolerance stack (≥ 3×RSS and > worst case);
   - clearances against the smallest open gap;
   - holding torque against the requirement.
   Any FAIL changes the design before modelling.
4. **A failure-mode table (DFMEA-lite)** for each moving part: how can it fail
   (won't assemble, too loose, won't engage, slips, cracks, creeps, user
   error)? How likely, and what in the design prevents it?
5. **A coupon first.** Print only the critical joint, at the real size, under
   30 minutes, with 2–3 clearance variants on one plate.
   - **Scott tests it before the full product is designed around it.**
   - The geometric gates still run, but they are not proof.
6. **Use measured clearances.** Ask Scott for the Fit Test Plate results and
   record them in `data/knowledge_base/printer_calibration.md` once he
   reports. Until then, use the conservative section 1 values.
7. **Only then the full product,** and its notes say plainly what was
   calculated, what was tested on a coupon, and what wasn't tested.

## 8. Retrospective: the Fold Stand, by the numbers (`mechanism_budget.py --demo`)

| check | v2 had | needed | |
|---|---|---|---|
| ratchet engagement | 0.45 mm | ≥ 1.1 mm (3 × RSS 0.36, > worst 0.75) | FAIL |
| blade strain, pin going in | 0.85 % | ≤ 0.8 % repeated in PLA | FAIL |
| release window | 0.58 mm (ratio 2.0) | ≥ 3 × RSS | FAIL |
| blade-to-bore gap | 0.15 mm | ≥ 0.3 mm open | FAIL |
| holding torque | unknown: never calculated | ≥ 350 N·mm | — |

**v1** used the same small pin, with a 0.35 mm V-detent and 0.05 mm press-fit
pins. That is below any process capability in section 1.

**Root cause, both times:** the mechanism was scaled to fit inside a 4 mm pin
in an 8 mm barrel. That is about ten times too small for printed engagement.
Nothing in the process asked for the numbers.

## Sources

- Covestro/Bayer, *Snap-Fit Joints for Plastics: A Design Guide*: cantilever
  equations, R/h, taper, permissible strains (one-time; ~60 % for repeated),
  mating force. Copies: [MIT](https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf),
  [SparkFun](https://cdn.sparkfun.com/assets/home_page_posts/1/4/1/0/Plastic_Snap_fit_design.pdf)
- [Fictiv: how to design snap-fit components](https://www.fictiv.com/articles/how-to-design-snap-fit-components);
  [BASF snap-fit (UL Prospector)](https://ulprospector.ul.com/1248/snapfit-3/)
- Creep of FDM polymers: [sv-jme](https://ojs30.sv-jme.eu/index.php/sv-jme/article/download/191/118/2454),
  [SciELO PLA tensile creep](https://www.scielo.br/j/rmat/a/k7YbRX5pcCNTvLYVJyPnMFt/abstract/?lang=en),
  [MDPI stress relaxation of PLA](https://mdpi.com/1996-1944/15/10/3509)
- Friction: [Stoimenov et al., Tribology in Industry 2024](https://tribology.rs/journals/2024/2024-1/2024-1-09.html),
  [Pawlak, Tribologia](https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-f7c60c77-2f7e-4c4f-8d4e-f962d0c503e7/c/pawlak.pdf)
- Accuracy: [euspen 2026 abstract](https://www.euspen.eu/knowledge-base/ICE26126.pdf),
  [Gebre et al. 2026](https://iris.unitn.it/retrieve/aaecc8a0-0420-472b-9a40-4d43d7df5e0b/Material%20Design%20%20%20Processing%20Communications%20-%202026%20-%20Gebre%20-%20Influence%20of%20Geometry%20and%20Size%20on%20Precision%20and%20Accuracy%20in.pdf),
  [Zbotic tolerances](https://zbotic.in/3d-printing-tolerances-designing-gaps-for-press-fits-threads-and-snap-fits/),
  [3dprintcalcs fit guide](https://3dprintcalcs.pages.dev/reference/common-tolerances),
  [Bambu forum: precision of FDM](https://forum.bambulab.com/t/precision-of-fdm/258975)
- Anisotropy: [Fayazbakhsh et al. 2019](https://www.torontomu.ca/content/dam/frames/publications/Fayazbakhsh_Movahedi_Kalman_2019.pdf),
  [Formlabs isotropy comparison](https://formlabs.com/blog/isotropy-in-3d-printing-comparing-fdm-sla-sls/)
- Ratchets: [Firgelli: pawl self-locking geometry](https://www.firgelliauto.com/en-fr/blogs/mechanisms/pawl),
  [Firgelli: ratchet tooth geometry](https://www.firgelliauto.com/blogs/mechanisms/ratchet-device).
  Blog sources: check against Shigley or Juvinall before relying on them.
- Hinges and stands:
  - [locking hinge with thumbscrew](https://makerworld.com/en/models/3173867-adjustable-simple-locking-hinge-with-thumbscrew);
  - [adjustable geared hinge with screws](https://www.printables.com/model/125084-adjustable-geared-hinge-with-screws);
  - [friction hinge design guide](https://mansfieldec.com/feeds/blog/friction-hinge-design);
  - stands: [versatile PIP stand](https://www.printables.com/model/1215014-versatile-phone-stand-print-in-place-foldable-hori),
    [adjustable tablet stand](https://printables.com/model/272896-adjustable-tablet-stand),
    [compact hinged phone stand](https://www.printables.com/model/302815-compact-hinged-phone-stand)
- Inserts: [Prusa M3 heat-set inserts](https://www.prusa3d.com/en/product/heat-set-inserts-m3-standard-100-pcs/),
  [Accu insert hole charts](https://accu.co.uk/p/488-threaded-insert-hole-size-charts-for-3d-printing-pla-petg-resin),
  [Digi-Key: heat-set inserts in FreeCAD](https://www.digikey.com/es/maker/tutorials/2025/intro-to-freecad-part-4-how-to-use-heat-set-inserts)
