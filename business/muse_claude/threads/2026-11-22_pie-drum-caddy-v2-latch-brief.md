Filed by Benson 2026-11-22 for Claude's return Tue Nov 24.
Scott picked the mechanism 2026-11-22.
Full brief follows, unabridged.

# BRIEF — Pie Drum Caddy v2: keeper-knob latch (Scott's pick, 2026-11-22)

**From:** Benson, for Claude (design work — Claude returns Tue Nov 24)
**Product:** Pie Drum Caddy (live private model 3621416; drum Ø150, base Ø120)
**Scott's ask, verbatim intent:** "Can it be designed to latch in somehow. So when
it's moved it stays in one piece." Four mechanisms were put to Scott
(keeper knob / bayonet track / snap detent / magnets). **Scott picked the
keeper knob on the centre post.**

## The problem
v1 (FACTS.md, 2026-11-15): the drum sits on a ring of 46 × 6 mm airsoft BBs in
the base's channel and spins on them. The centre post (POST_R 8, radial gap
0.4) only centres it — "nothing holds it on, so it lifts straight off."
Carrying the caddy by the drum leaves the base behind; tipping it in transit
separates the two. Scott wants it to travel as one piece while keeping the
free spin and the lift-apart cleaning.

## The v2 change (three parts: base, drum, + knob)
1. **Base — post grows up and gains a thread.** Today the post ends inside the
   drum's blind bore (engagement ~11 mm, chamfered top; BORE_D = FLOOR + 9,
   bore roof 37°). Extend the post so it passes through the bore roof and the
   centre well floor and protrudes into the centre well. Put a coarse printed
   external thread on the protruding section (2.5–3 mm pitch class, thread
   clearance ~0.3–0.4 mm/side per the shop's fit research,
   business/muse_claude/research/2026-11-22_3d-print-design-techniques.md).
   Nothing else on the base changes: BB channel (ball circle r50, 46 BBs,
   0.3/side), ironed channel floor, footprint all stay.
2. **Drum — the bore becomes a through-hole.** The centre well floor gets a
   hole continuing the bore (post Ø16 + the existing 0.4 radial gap + hole
   compensation, same fit as today's bore). The drum must still spin freely
   around the post exactly as v1 — the hole is a running fit, never a clamp.
   Bearing faces untouched: smooth underside bed face, float 2.0 mm above the
   base rim.
3. **Knob — new third part.** Internally threaded cap that screws onto the
   post inside the centre well. Its underside overhangs the well floor with
   **0.3–0.5 mm running clearance** — it traps the drum vertically WITHOUT
   clamping it, so the drum keeps spinning under the knob. Requirements:
   - ≥3 full thread turns of engagement.
   - Load case: lifting by the drum with 1 kg spread in the wells — knob +
     thread hold drum (206 g) + contents.
   - Low profile: ≤ ~12 mm above the well floor; OD inside the centre well
     with finger room (knurl or lobes — it is tightened by fingers only).
   - Top face is customer-facing and flat → ironing `top` applies
     (confirmed standard: 0.15 spacing / 10% flow / 30 mm/s).
   - Unscrews fully → drum lifts off exactly as v1 for cleaning; BBs stay in
     the base channel.

## Standing constraints (do not break)
- No supports anywhere visible; no hardware beyond the BBs (knob is printed).
- Matte white PLA; Standard (0.20, 3 walls, 15%) + Optimized (0.16, 3 walls,
  12% gyroid) profiles for all three parts; knob may share the base's plate
  or run as its own small profile.
- Printability gates and the fit-check discipline from ENGINEERING.md §9 —
  re-run the fit check for the new post/hole/thread stack and state the RSS.
- Copy updates owed with the design: FACTS.md ("nothing locks it on" line is
  superseded), the guide PDF's assembly section (add: drop BBs in, set drum
  on, screw the knob down until it seats — do not overtighten), and the
  MakerWorld description when the profiles swap.

## Sequence
- Scott is printing v1 (Base — Standard) today, Sun Nov 22 — the caddy's
  first full print; treat it as the bearing/fit test for v1 geometry.
- v2 design work waits for Claude's return Tue Nov 24. Benson builds the
  profiles, runs the finish step, and swaps them onto model 3621416 (which
  also still owes its 3-wall re-slice — fold that into the v2 build so the
  model is touched once).

## Claude, 2026-11-24 3:08 PM: design done, keeper coupon with Scott

**One change to the brief, Scott's call (Nov 24): a tall keeper cup, not a low knob.** The well
floor sits 97.5 mm down a 23 mm tube, where no finger reaches a 12 mm knob. So the post grows
up through the drum, and the keeper is a cup that fills the centre well: a nut at its foot, a
pen cup above, a knurled collar standing just above the hub to turn it by. Lifting by the collar
carries the whole caddy.

- **Thread:** the jar tower's tested profile, 4 mm pitch, 1.2 deep, 0.2 clearance. 16.5 mm long,
  12.4 mm of it at full depth: just over 3 full turns.
- **How it traps without clamping:** the cup screws down until a cone inside it lands on the
  post's cone tip. That stop, not how hard it's turned, puts the cup's foot 0.5 mm above the
  drum's ledge. Fit check: the drum lifts 0.45 clear and is caught at 0.5. Worst-case stack
  0.45, RSS 0.23, so the gap never closes.
- **Load:** 40 N design load (1.36 kg x 3 g). The thread strips at ~1.4 kN and the post core
  breaks at ~1.7 kN.
- **Gates:** base, drum, keeper and all coupon parts pass with 0 support moves, and fragility is
  0. Getting there meant five geometry fixes, all in ENGINEERING_v2.md section 5: a 40° stop
  cone, tapered thread ends, a chamfered knurl, a 40° lead-in and a flat-cut tip.
- **Standard slices on the branch:**
  - base: 1 h 47 m, 40.2 g;
  - drum: 8 h 41 m, 211 g, the same as v1;
  - keeper: 56 m, 23.2 g, with a 3 mm brim because it's 119 mm tall on a 30 mm foot.

  These are design checks, not Benson's shipping profiles.

**Keeper test sent to Scott:** plate 1 (post, ring, 0.2 cup) 29 m; plate 2 (0.3 cup) 14 m, only
if 0.2 binds. Files are `pie_caddy_v2_keeper_coupon*.gcode.3mf` and
`guide/Pie_Caddy_v2_Keeper_Test_Guide.pdf` on branch `claude/new-session-o245bl`, folder
`openscad_models/pie_caddy/`.

**Waits on Scott's result, then:** the guide PDF's assembly section, FACTS v2 (the "nothing
locks it on" line goes), renders, the viewer entry, and Benson's profiles. The collar's top is a
flat ring the customer sees, so `top` ironing applies. Nothing about v1 or model 3621416 has
been touched.
