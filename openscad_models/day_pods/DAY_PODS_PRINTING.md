# Day Pods

2026-11-04. Your pick, form B of four: a weekly pill box of seven separate
pods, each with a sliding lid, standing in order on a stand. You lift one day
off to take with you.

The first of the three practice designs. It practises sliding fits, the one
kind of joint the fit test plate doesn't cover yet.

## What it is

- **Seven pods**, one per day, each holding a cavity 26 × 28 × 17 mm. The
  floor rounds up into the walls, so nothing lodges in a corner.
- **A sliding lid on each pod**, with the day engraved on top: MO TU WE TH
  FR SA SU. Two letters rather than one, so the two Ts and the two Ss can't be
  mixed up.
- **A stand** the pods slide down onto, in day order.

**Size:** each pod is 32 × 33 × 22 mm. On the stand the week is 236 × 38 mm
and 25 mm tall.

## Printing

PLA, 0.2 mm layers, **no supports**, everything as it lies in the file.
Times and weights are from PrusaSlicer with the P1S settings:

| print | file | colour | time | filament |
|---|---|---|---|---|
| 7 pods | `day_pods_pods.3mf` | white `#F4F1EA` | 1 h 36 min | 53 g |
| 7 lids | `day_pods_lids.3mf` | lilac `#B79CE0` | 32 min | 17 g |
| stand | `day_pods_stand.3mf` | white `#F4F1EA` | 50 min | 34 g |
| fit coupon (optional) | `day_pods_fit_coupon.3mf` | any | 20 min | 11 g |

The set is about 2 h 58 min and 103 g. Each lid is its own object, so they
can be given different colours, a rainbow week, at four colours per AMS.

- **The pods** print the right way up, open at the top.
- **The lids** print upside down, so the day is engraved into the smooth face
  on the plate. The small ridge underneath prints on top.
- **The stand** prints flat, its back wall and rails standing up. The OBC mark
  is engraved underneath.

## How it works

**The lid** slides forward out of grooves along the top of the pod's side
walls.

- **Bevelled edges:** the lid's edges are bevelled at 30°, so the wall over
  them holds it down. That wall overhangs at a printable 30°.
- **The click:** a low round ridge under the lid's front rides over the pod's
  front wall. Shut, the lid stays shut in a bag.
- **Opening:** push it open with a thumb on the three grooves at the front.

**The pod** has an upright dovetail groove down its back. It slides down onto
a matching rail on the stand's back wall.

- Pulled forward, it's held.
- Lifted, it comes straight off, to take one day with you.

**The clearance** is 0.2 mm each side (`CLR`), for both slides.

- **The coupon** is the lid's slide at 0.1, 0.2 and 0.3, marked one, two and
  three dots.
- **Tuning:** print it, find the one that slides smoothly without rattling,
  and tell me. Changing `CLR` and running `./ship.sh` rebuilds everything at
  that fit.

## Checked before it was pushed

The results are in `checks/`.

**Fit (`check_pods.py`, on the exported parts): all pass.**

- **The lid:** shut, it touches nothing. Lifted 0.5 mm, pushed 0.5 sideways or
  back, it hits the pod, so the grooves hold it.
  - Slid 1 mm forward, its ridge meets the front wall: the click.
  - Slid 6 mm forward, it's past the click and slides free.
- **The pods:** all seven on the stand touch nothing and rest on the base.
  - Pulled 0.5 mm forward or pushed 0.5 sideways, a pod hits its rail.
  - Lifted the rail's height, it's off.
  - Neighbours don't touch.

**Product gate: all passes.** The pod, the stand, all seven lids and the
coupon: 0 supports, 0 overhang perimeters, every wall at least 1.2 mm.

**Print fidelity: 0 flags** on the pod, the stand, two of the lids and the
coupon.

**Fragility:** nothing high and nothing on watch.

**What it took:**

- **The back wall:** the lid first tucked 1 mm into the back wall, which left
  0.2 mm between it and the stand's groove. The tuck is gone (the side grooves
  hold the lid) and the back wall is 3.8 mm.
- **The front wall:** a chamfer on its top edge cut slivers into the cavity's
  rounded corners. The edge is square now; the ridge is round and rides over
  it.
- **The lids:**
  - gaps under 1.2 mm between the letters' strokes are closed;
  - the finger grooves are spaced so 1.6 mm of lid stands between them;
  - the upright band at each edge is 1.4 mm.
- **The coupon:** its numbers, engraved on upright faces, needed support.
  They're dots on top now.

**Not tested on the printer yet.** What I'd check first:

- **the slide**, which is what the coupon is for;
- **the click:** that the ridge holds the lid shut without needing force to
  open.

The ridge is one number too (`RIDGE_H`, 0.4 mm).

**Before listing it:** it's a pill organiser for dry tablets and capsules,
not a medical device, and the listing shouldn't claim more.

## Renders

In `images/`:

- `day_pods_{front,three_quarter,top}.png`: the week on its stand.
- `day_pods_wednesday.png`: Wednesday lifted off, its lid slid half open.
- `day_pods_prints.png`: the pods and lids as they lie on the plate.

These are design-review renders from the real exported parts, not photos.

Rebuild everything with `./ship.sh`, then `python3 render_pods.py`.
