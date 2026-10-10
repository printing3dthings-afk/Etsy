#!/usr/bin/env python3
"""
tools/p1s_motion.py -- how long each move of a G-code file really takes on a
Bambu P1S: acceleration, cornering and top speed, move by move.

Scott, 2026-10-10: "see how good of real physics in this thing ... as close to
reality as possible." The viewer used to spread each layer's time evenly over
its extruded length, so every line in a layer ran at one speed, travel took no
time and the nozzle teleported between islands. A real head accelerates out of
every corner, cruises if the line is long enough, brakes into the next corner,
and crosses the gaps at travel speed. That is what this computes, per move.

THE MODEL is Marlin's planner with classic jerk, the one PrusaSlicer's own time
estimator implements (GCodeProcessor), so its totals can be checked against the
slicer's footer -- an independent implementation of the same physics. It is:
  * per move, a target speed: the feedrate, capped per axis by the machine's
    max speeds;
  * an acceleration: M204 P (print), T (travel) or R (retract) as the G-code
    sets it, capped by the machine's extruding / travel / retracting limits
    and per axis;
  * a junction speed between consecutive moves from classic jerk (the largest
    instantaneous change in velocity each axis may take);
  * a backward and a forward pass so no move asks for more braking or
    acceleration than its length allows;
  * a trapezoid (or triangle) per move.

WHAT IT DOES NOT MODEL, said out loud: Bambu's own firmware and its input
shaping (it may corner faster than classic jerk allows), pressure advance,
heat-up and bed-levelling before the first layer, and the AMS's mechanical
filament swap beyond the load and unload times Bambu's own profile states.

Machine limits default to Bambu's "Bambu Lab P1S 0.4 nozzle" profile
(bambulab/BambuStudio resources/profiles/BBL, read 2026-10-10) and are read
from the G-code's own config footer when it has one.
"""
from __future__ import annotations

import math
import re
from array import array

# Bambu Lab P1S 0.4 nozzle, normal mode.
P1S_LIMITS = {
    "max_acceleration_x": 20000.0, "max_acceleration_y": 20000.0,
    "max_acceleration_z": 500.0, "max_acceleration_e": 5000.0,
    "max_acceleration_extruding": 20000.0, "max_acceleration_retracting": 5000.0,
    "max_acceleration_travel": 9000.0,
    "max_feedrate_x": 500.0, "max_feedrate_y": 500.0,
    "max_feedrate_z": 20.0, "max_feedrate_e": 30.0,
    "max_jerk_x": 9.0, "max_jerk_y": 9.0, "max_jerk_z": 3.0, "max_jerk_e": 2.5,
}
# AMS swap: machine_unload_filament_time 28 (P1S) + machine_load_filament_time
# 29 (fdm_machine_common). The flush itself is in the G-code as wipe-tower moves.
P1S_TOOLCHANGE_S = 28.0 + 29.0

_CFG = re.compile(r"^;\s*machine_(max_(?:acceleration|feedrate|jerk)_[a-z]+)\s*=\s*([-0-9.]+)")


def limits_from_gcode(path):
    """P1S limits, overridden by any machine_max_* the slicer wrote into the
    file's config block. Only the first (normal-mode) value is used."""
    lim = dict(P1S_LIMITS)
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            if line.startswith("; machine_max_"):
                m = _CFG.match(line)
                if m and m.group(1) in lim:
                    try:
                        lim[m.group(1)] = float(m.group(2))
                    except ValueError:
                        pass
    return lim


class Planner:
    """Collect moves in order, then solve() once for every move's duration."""

    def __init__(self, limits=None):
        self.lim = dict(P1S_LIMITS, **(limits or {}))
        L = self.lim
        self._vmax = (L["max_feedrate_x"], L["max_feedrate_y"], L["max_feedrate_z"], L["max_feedrate_e"])
        self._amax = (L["max_acceleration_x"], L["max_acceleration_y"],
                      L["max_acceleration_z"], L["max_acceleration_e"])
        self._jerk = (L["max_jerk_x"], L["max_jerk_y"], L["max_jerk_z"], L["max_jerk_e"])
        # Flat arrays, not objects: a big plate is over a million moves.
        self.dist = array("d")
        self.vnom = array("d")
        self.acc = array("d")
        self.vmax_entry = array("d")
        self.fixed = array("d")       # >0: a dwell / swap of fixed duration, no motion
        self._prev = None             # (unit, vnom, safe_speed) of the last motion block

    # -- adding ---------------------------------------------------------------
    def add_move(self, dx, dy, dz, de, feed_mm_s, accel, kind):
        """kind: 'print', 'travel' or 'retract'. Returns the block index, or
        None if the move has no length at all."""
        xyz = math.sqrt(dx * dx + dy * dy + dz * dz)
        if xyz > 1e-9:
            d = xyz
        elif abs(de) > 1e-9:
            d = abs(de)
            kind = "retract"
        else:
            return None
        inv = 1.0 / d
        unit = (dx * inv, dy * inv, dz * inv, de * inv)

        v = feed_mm_s
        for i in range(4):
            u = abs(unit[i])
            if u > 1e-12 and v * u > self._vmax[i]:
                v = self._vmax[i] / u
        L = self.lim
        cap = {"print": L["max_acceleration_extruding"], "travel": L["max_acceleration_travel"],
               "retract": L["max_acceleration_retracting"]}[kind]
        a = min(accel, cap) if accel > 0 else cap
        for i in range(4):
            u = abs(unit[i])
            if u > 1e-12 and a * u > self._amax[i]:
                a = self._amax[i] / u

        # Marlin classic jerk. Velocity per axis of this block at full speed.
        cur = [unit[i] * v for i in range(4)]
        safe = v
        limited = False
        for i in range(4):
            j = abs(cur[i])
            mj = self._jerk[i]
            if j > mj:
                if limited:
                    mjerk = v * mj
                    if j * safe > mjerk:
                        safe = mjerk / j
                else:
                    safe *= mj / j
                    limited = True
        if self._prev is not None and self._prev[1] > 1e-9:
            punit, pv, psafe = self._prev
            vj = min(v, pv)
            smaller = vj / pv
            vf = 1.0
            lim = False
            for i in range(4):
                v_exit = punit[i] * pv * smaller
                v_entry = cur[i]
                if lim:
                    v_exit *= vf
                    v_entry *= vf
                if v_exit > v_entry:
                    jk = (v_exit - v_entry) if (v_entry > 0 or v_exit < 0) else max(v_exit, -v_entry)
                else:
                    jk = (v_entry - v_exit) if (v_entry < 0 or v_exit > 0) else max(-v_exit, v_entry)
                if jk > self._jerk[i]:
                    vf *= self._jerk[i] / jk
                    lim = True
            if lim:
                vj *= vf
            thr = vj * 0.99
            if psafe > thr and safe > thr:
                vj = safe
        else:
            vj = safe
        self._prev = (unit, v, safe)

        self.dist.append(d)
        self.vnom.append(v)
        self.acc.append(a)
        self.vmax_entry.append(min(vj, v))
        self.fixed.append(0.0)
        return len(self.dist) - 1

    def add_fixed(self, seconds):
        """A pause the head spends standing still (dwell, filament swap). Breaks
        the junction chain: whatever follows starts from rest."""
        self.dist.append(0.0)
        self.vnom.append(0.0)
        self.acc.append(1.0)
        self.vmax_entry.append(0.0)
        self.fixed.append(max(0.0, seconds))
        self._prev = None
        return len(self.dist) - 1

    # -- solving --------------------------------------------------------------
    def solve(self):
        """Duration of every block, in seconds, as an array('d')."""
        n = len(self.dist)
        dist, vnom, acc, vme, fixed = self.dist, self.vnom, self.acc, self.vmax_entry, self.fixed
        entry = array("d", vme)
        # Backward: a block can only enter as fast as it can still brake to the
        # next block's entry speed within its own length. The last move ends
        # at rest.
        nxt = 0.0
        for k in range(n - 1, -1, -1):
            if fixed[k] > 0 or dist[k] == 0:
                entry[k] = 0.0
                nxt = 0.0
                continue
            e = math.sqrt(nxt * nxt + 2.0 * acc[k] * dist[k])
            if e < entry[k]:
                entry[k] = e
            nxt = entry[k]
        # Forward: and only exit as fast as it could accelerate to from its entry.
        for k in range(n - 1):
            if fixed[k] > 0 or dist[k] == 0:
                continue
            reach = math.sqrt(entry[k] * entry[k] + 2.0 * acc[k] * dist[k])
            if entry[k + 1] > reach:
                entry[k + 1] = reach
        t = array("d", bytes(8 * n))
        for k in range(n):
            if fixed[k] > 0 or dist[k] == 0:
                t[k] = fixed[k]
                continue
            v0 = entry[k]
            v1 = entry[k + 1] if k + 1 < n and not (fixed[k + 1] > 0 or dist[k + 1] == 0) else 0.0
            t[k] = trapezoid_time(dist[k], v0, vnom[k], v1, acc[k])
        return t


def trapezoid_time(d, v0, vc, v1, a):
    """Time to cover d starting at v0, cruising at most vc, ending at v1."""
    v0 = min(v0, vc)
    v1 = min(v1, vc)
    if a <= 0:
        return d / max(vc, 1e-9)
    da = (vc * vc - v0 * v0) / (2.0 * a)
    dd = (vc * vc - v1 * v1) / (2.0 * a)
    if da + dd <= d:
        return (vc - v0) / a + (vc - v1) / a + (d - da - dd) / vc
    # Never reaches cruise: accelerate to a peak, then brake.
    vp = math.sqrt(max(0.0, (2.0 * a * d + v0 * v0 + v1 * v1) / 2.0))
    return max(0.0, (vp - v0) / a) + max(0.0, (vp - v1) / a)
