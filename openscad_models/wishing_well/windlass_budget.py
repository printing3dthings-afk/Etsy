#!/usr/bin/env python3
"""Stone Wishing Well: the windlass's hand calculations, before the coupon is modelled (2026-11-15).

Scott picked form 1: a round stone well, two posts, a peaked roof, and a crank that raises a
bucket. The crank has to hold the bucket where it is left (mechanism handbook section 7).

The windlass:
- Two posts printed FLAT. Each has a snap cradle: the axle's journal presses down into it
  between two in-plane fingers, which bend along the layers (the Gear Heart's posts bent
  across them and snapped).
- An axle printed UPRIGHT, so its journals are drawn in XY and come out round. A drum between
  the posts carries the twine.
- A crank wheel printed flat: ratchet teeth round its rim and a handle peg on its face. It snaps
  onto the axle's hex end with the Pocket Top's hub joint (three in-plane beams, reach 0.45).
  Scott has that joint on test.
- A gravity pawl on a T-headed pin on the crank-side post. It drops into the teeth, so the
  bucket stays where it's left. Lift the pawl to let it down.

Why not something simpler:
- Friction in plain bearings: about a third of the bucket's pull (below), so it would unwind.
- A preloaded snap as a friction brake: section 5 class 3, held strain 0.2 % that creeps.
- So the ratchet: section 5 class 4, a positive lock.

    python3 windlass_budget.py      (writes checks/windlass_budget.txt)
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from mechanism_budget import PLA, PROCESS, cantilever, engagement, mating_force  # noqa: E402

G = 9.81e-3                       # N per gram
R_J = 3.0                         # journal radius
C = 0.25                          # cradle hole radius over the journal (both drawn in XY: +/-0.1 each)
FRAME_T = 8.0                     # post thickness = the fingers' width (print Z)
T_F, L_F = 1.3, 10.1              # finger: thickness in the bend, root to the catch
VARIANTS = (0.40, 0.55, 0.70)    # how far the mouth narrows below the journal, each side (0.50 failed
                                  # the 3x RSS rule by 0.02, so the design value is 0.55)
R_DRUM = 5.0
BUCKET_G = 20.0                   # printed bucket ~3 g; allow 17 g in it (a few sweets, a coin)
R_HANDLE = 12.5                   # handle peg's radius on the wheel
HAND_N = 5.0                      # a firm push on the handle
WHEEL_R, TOOTH_H, TEETH = 17.0, 1.6, 24
ENGAGE = 1.25                     # the pawl tip stops 0.35 over the root
AXLE_G = 3.0

out = []
def line(s=""):
    out.append(s)

line("WISHING WELL WINDLASS: hand calculations (mechanism handbook section 7)")
line()
line("1. REQUIREMENT")
load_t = BUCKET_G * G * R_DRUM
line(f"  bucket up to {BUCKET_G:.0f} g on a drum of radius {R_DRUM}: {load_t:.2f} N mm; held with x3: "
     f"{3 * load_t:.2f} N mm")
line(f"  a firm crank push {HAND_N} N at the handle (radius {R_HANDLE}) must not lift the axle out "
     f"of its cradles")
line("  cycles: hundreds of turns; the snaps are pressed in once (and a few times on test)")
line()
line("2. WHY A RATCHET")
fric = PLA["mu"] * (BUCKET_G + AXLE_G) * G * R_J
line(f"  plain bearing friction: mu {PLA['mu']} x ({BUCKET_G:.0f} + {AXLE_G:.0f}) g x r {R_J} = {fric:.2f} N mm "
     f"vs the load's {load_t:.2f}: it unwinds")
line()
line("3. THE CRADLE SNAP (fingers bend in the print plane)")
for e in VARIANTS:
    r = cantilever(t=T_F, L=L_F, b=FRAME_T, y=e, repeated=False)
    rr = cantilever(t=T_F, L=L_F, b=FRAME_T, y=e, repeated=True)
    # the journal meets the catch where the cradle's circle meets the mouth: the contact
    # normal there is at atan(half-mouth / height) from vertical
    half = R_J - e
    h = math.sqrt(R_J ** 2 - half ** 2)
    ang = math.degrees(math.atan2(half, h))
    pull = mating_force(P=2 * r["tip_force_N"], angle_deg=ang)
    push = mating_force(P=2 * r["tip_force_N"], angle_deg=30)
    line(f"  narrowing {e:.2f}: strain {r['strain_pct']:.2f} % (once {r['limit_pct']:.1f} %, repeated "
         f"{rr['limit_pct']:.1f} %), {'ok' if r['ok'] else 'FAIL'} to press in; finger force "
         f"{r['tip_force_N']:.1f} N")
    pf = pull["W_N"]
    pf_txt = "self-locking (won't pull out)" if pull.get("self_locking") else f"{pf:.0f} N"
    line(f"      press in (30 deg lead-in): {push['W_N']:.0f} N; pull out (catch at "
         f"{ang:.0f} deg): {pf_txt}; crank lift {HAND_N} N")
eng = engagement(depth=0.55, stack_items=[("journal r", PROCESS["xy_wall"]), ("mouth edge", PROCESS["xy_wall"]),
                                          ("finger position", PROCESS["xy_wall"])])
line(f"  catch 0.55 (the design value) vs the XY stack: worst {eng['worst_case']:.2f}, 3x RSS {3 * eng['rss']:.2f}: "
     f"{'ok' if eng['ok'] else 'FAIL'}")
line(f"  running clearance {C} radial: journal and cradle are both drawn in XY (+/-0.10 each)")
line()
line("4. THE RATCHET AND PAWL")
pitch = 2 * math.pi * WHEEL_R / TEETH
line(f"  wheel radius {WHEEL_R}, {TEETH} teeth, {TOOTH_H} tall, pitch {pitch:.2f} (handbook: >= 1 tall, "
     f">= 2.5 pitch, wheel >= 25-30 across): {'ok' if TOOTH_H >= 1 and pitch >= 2.5 and 2 * WHEEL_R >= 25 else 'FAIL'}")
stack = [("pawl pin, XY", 0.10), ("pawl hole, XY", PROCESS["hole_vertical"]), ("tooth, XY", 0.10),
         ("cradle clearance", C), ("journal, XY", 0.10), ("cradle, XY", 0.10), ("hex play", 0.15)]
eng2 = engagement(depth=ENGAGE, stack_items=stack)
line(f"  pawl tip {ENGAGE} into a {TOOTH_H} tooth vs the stack between pawl and tooth: worst {eng2['worst_case']:.2f}, "
     f"3x RSS {3 * eng2['rss']:.2f}: {'ok' if eng2['ok'] else 'FAIL'}")
line(f"  holding: positive lock (the pawl stops the tooth); {3 * load_t:.2f} N mm is nothing to a tooth "
     f"{TOOTH_H} x 3 mm")
line()
line("5. TURNING IT")
wind = (load_t + fric) / R_HANDLE
line(f"  winding the full bucket up: ({load_t:.2f} + {fric:.2f}) / {R_HANDLE} = {wind:.2f} N at the handle")
line(f"  the hex (5 across flats) carries {HAND_N * R_HANDLE:.0f} N mm at most; the Pocket Top hex "
     f"bears after 6.6 deg of free play")
line()
line("VERDICT: build the coupon. Scott's test decides the cradle narrowing, and his Pocket Top")
line("result decides the crank's hub joint.")

text = "\n".join(out)
print(text)
(HERE / "checks").mkdir(exist_ok=True)
(HERE / "checks" / "windlass_budget.txt").write_text(text + "\n")
