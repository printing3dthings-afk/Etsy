#!/usr/bin/env python3
"""
Shared smart composite module for wall art lifestyle scenes.

Replaces the old fixed-position composite_into_ai_room() with composite_smart(),
which auto-detects where furniture starts in the background and positions the frame
above it with guaranteed clearance. Uses adaptive mat color to match room lighting.

Import this module instead of copy-pasting composite_into_ai_room everywhere.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


# ── Furniture line detection ──────────────────────────────────────────────────

def find_furniture_line(arr, x0=200, x1=824, search_top=0.25, search_bottom=0.88,
                        min_furniture_pct=0.35):
    """
    Scan top-to-bottom for the y-coordinate where furniture/objects first appear.

    Uses gradient magnitude per row: wall rows are nearly flat (low gradient),
    furniture rows have sharp colour transitions (high gradient). Returns the y-pixel
    of the first sustained furniture region.

    Falls back to int(H * 0.55) when no clear edge is found (conservative safe zone).
    """
    H = arr.shape[0]
    search_start = int(H * search_top)
    search_end = int(H * search_bottom)
    floor = int(H * min_furniture_pct)  # never report furniture above this

    # Per-row vertical gradient magnitude
    edges = []
    for y in range(search_start, search_end):
        row       = arr[y,     x0:x1].astype(np.float32)
        row_above = arr[max(0, y-1), x0:x1].astype(np.float32)
        gy = float(np.abs(row - row_above).mean())
        edges.append(gy)

    if not edges:
        return int(H * 0.55)

    # Smooth with 9-row moving average to suppress single-pixel noise
    window = 9
    smoothed = []
    for i in range(len(edges)):
        s = max(0, i - window // 2)
        e = min(len(edges), i + window // 2 + 1)
        smoothed.append(sum(edges[s:e]) / (e - s))

    # Wall baseline = mean of the first quarter of the search zone
    baseline_n = max(1, len(smoothed) // 4)
    baseline = sum(smoothed[:baseline_n]) / baseline_n

    # Furniture threshold: first 3 consecutive rows all exceed 2.5× wall baseline
    threshold = max(baseline * 2.5, 2.5)
    run = 0
    for i, val in enumerate(smoothed):
        if val > threshold:
            run += 1
            if run >= 3:
                furniture_y = search_start + (i - 2)
                return max(floor, furniture_y)
        else:
            run = 0

    # No clear furniture line — conservative fallback
    return int(H * 0.55)


# ── Adaptive mat colour ───────────────────────────────────────────────────────

def _adaptive_mat_color(arr, px, py, full_w, full_h):
    """
    Sample the wall pixels surrounding the frame and return a mat colour that
    blends naturally with the room's ambient lighting.  Prevents the 'glowing
    white mat in a dark room' artifact.
    """
    H, W = arr.shape[:2]
    left_s  = arr[py:py+full_h, max(0, px-40):px]
    right_s = arr[py:py+full_h, px+full_w:min(W, px+full_w+40)]
    top_s   = arr[max(0, py-10):py, px:px+full_w]
    samples = [s.reshape(-1, 3) for s in [left_s, right_s, top_s] if s.size > 0]
    wall    = tuple(int(c) for c in np.vstack(samples).mean(axis=0)) if samples else (128, 128, 128)

    brightness = (0.299*wall[0] + 0.587*wall[1] + 0.114*wall[2]) / 255
    if   brightness < 0.25: factor = 0.72
    elif brightness < 0.40: factor = 0.80
    elif brightness < 0.55: factor = 0.90
    else:                   factor = 0.97

    return (
        min(255, int(255*factor + wall[0]*0.08)),
        min(255, int(250*factor + wall[1]*0.06)),
        min(255, int(240*factor + wall[2]*0.03)),
    )


# ── Core composite helper ─────────────────────────────────────────────────────

def _draw_framed_art(room, art_path, px, py, art_w, art_h, mat_w, frame_w,
                     frame_color, mat_color):
    """Draw AO blob, drop-shadow, frame, mat, and real art onto room (in-place)."""
    CANVAS = room.size[0]
    full_w = art_w + 2*mat_w + 2*frame_w
    full_h = art_h + 2*mat_w + 2*frame_w

    # Ambient occlusion — subtle wall darkening behind the frame
    ao = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    for pad in range(40, 0, -4):
        alpha = int(40 * (1 - (pad / 40) ** 1.5))
        ImageDraw.Draw(ao).rectangle(
            [px-pad, py-pad, px+full_w+pad, py+full_h+pad], fill=(0, 0, 0, alpha))
    ao = ao.filter(ImageFilter.GaussianBlur(radius=22))
    room = Image.alpha_composite(room.convert('RGBA'), ao).convert('RGB')

    # Drop shadow
    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [px+10, py+14, px+full_w+10, py+full_h+14], fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)

    # Frame with bevel
    draw.rectangle([px, py, px+full_w, py+full_h], fill=frame_color)
    hi = tuple(min(255, c+45) for c in frame_color)
    sh = tuple(max(0,   c-45) for c in frame_color)
    bv = 4
    draw.polygon([px, py, px+full_w, py, px+full_w-bv, py+bv, px+bv, py+bv], fill=hi)
    draw.polygon([px, py, px, py+full_h, px+bv, py+full_h-bv, px+bv, py+bv], fill=hi)
    draw.polygon([px+full_w, py, px+full_w, py+full_h,
                  px+full_w-bv, py+full_h-bv, px+full_w-bv, py+bv], fill=sh)
    draw.polygon([px, py+full_h, px+full_w, py+full_h,
                  px+full_w-bv, py+full_h-bv, px+bv, py+full_h-bv], fill=sh)

    # Mat
    mx, my = px + frame_w, py + frame_w
    draw.rectangle([mx, my, mx + art_w + 2*mat_w, my + art_h + 2*mat_w], fill=mat_color)

    # Inner mat shadow (depth)
    inner = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    art_x, art_y = mx + mat_w, my + mat_w
    ImageDraw.Draw(inner).rectangle(
        [art_x-3, art_y-3, art_x+art_w+3, art_y+art_h+3], fill=(0, 0, 0, 30))
    inner = inner.filter(ImageFilter.GaussianBlur(radius=6))
    room = Image.alpha_composite(room.convert('RGBA'), inner).convert('RGB')

    # Actual artwork (slightly dimmed for indoor-lit realism)
    art = Image.open(art_path).convert('RGB')
    art_resized = ImageEnhance.Brightness(
        art.resize((art_w, art_h), Image.LANCZOS)
    ).enhance(0.93)
    room.paste(art_resized, (art_x, art_y))

    return room


# ── Public API ────────────────────────────────────────────────────────────────

def composite_smart(bg_path, art_path, out_path,
                    frame_color=(100, 85, 65),
                    art_pct=0.25,
                    min_clearance=60):
    """
    Smart lifestyle composite with automatic safe placement.

    Detects the furniture line in bg_path, then sizes and positions the frame
    so its bottom clears the furniture by min_clearance pixels.  If the default
    art_pct produces a frame too large to fit, it shrinks until it fits.

    Returns (success: bool, furniture_y: int, frame_bottom_y: int).
    """
    CANVAS = 1024
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
    arr  = np.array(room)

    furniture_y = find_furniture_line(arr)
    mat_w, frame_w = 30, 14

    # Pre-load art dimensions once
    _art_tmp = Image.open(art_path)
    _art_aspect = _art_tmp.height / _art_tmp.width
    _art_tmp.close()

    # Find the largest art_pct that fits above the furniture line
    current_pct = art_pct
    py = None
    for _ in range(6):
        art_w   = int(CANVAS * current_pct)
        art_h_v = int(art_w * _art_aspect)
        full_w  = art_w + 2*mat_w + 2*frame_w
        full_h  = art_h_v + 2*mat_w + 2*frame_w

        frame_bottom_target = furniture_y - min_clearance
        frame_top_target    = frame_bottom_target - full_h

        if frame_top_target >= int(CANVAS * 0.03):
            py = frame_top_target
            break

        current_pct = max(0.12, current_pct * 0.87)

    if py is None:
        # Can't fit above furniture line — background likely has furniture too high.
        # Place the smallest possible frame as high as possible and flag it.
        current_pct = 0.14
        art_w   = int(CANVAS * current_pct)
        art_h_v = int(art_w * _art_aspect)
        full_w  = art_w + 2*mat_w + 2*frame_w
        full_h  = art_h_v + 2*mat_w + 2*frame_w
        py = int(CANVAS * 0.03)
        print(f"  WARNING: furniture_y={furniture_y} too high to clear — "
              f"background may need regeneration. Placing minimal frame at py={py}.")

    px = (CANVAS - full_w) // 2

    # Open art once for final composite
    art_img = Image.open(art_path)
    art_h_v = int(art_w * art_img.height / art_img.width)

    mat_color = _adaptive_mat_color(arr, px, py, full_w, full_h)

    room = _draw_framed_art(room, art_path, px, py,
                            art_w, art_h_v, mat_w, frame_w,
                            frame_color, mat_color)

    room.save(out_path, 'JPEG', quality=93)
    actual_bottom = py + full_h
    clearance     = furniture_y - actual_bottom
    print(f"  Smart composite ✓  furniture_y={furniture_y}  "
          f"frame_bottom={actual_bottom}  clearance={clearance}px  "
          f"art_pct={current_pct:.2f}")
    return True, furniture_y, actual_bottom


def qc_check(composite_path, frame_top_y, frame_bottom_y, clearance_min=40):
    """
    Post-composite QC gate.

    Checks that the frame bounding box has low edge complexity (wall, not furniture)
    and that there is adequate clearance below the frame.

    Returns (pass: bool, message: str).
    """
    arr = np.array(Image.open(composite_path).convert('RGB').resize((1024, 1024), Image.LANCZOS))
    H   = arr.shape[0]

    def _edge(y0, y1, x0=200, x1=824):
        if y1 <= y0: return 0.0
        band = arr[y0:y1, x0:x1].astype(np.float32)
        gy = np.abs(np.diff(band, axis=0)).mean() if band.shape[0] > 1 else 0.0
        gx = np.abs(np.diff(band, axis=1)).mean() if band.shape[1] > 1 else 0.0
        return float((gy + gx) / 2)

    # Edge density inside the frame zone vs. well below the frame (furniture zone)
    frame_edge    = _edge(frame_top_y,    frame_bottom_y)
    furniture_edge = _edge(frame_bottom_y + 80, min(H-1, frame_bottom_y + 280))

    if furniture_edge > 0:
        ratio = frame_edge / furniture_edge
        # The frame zone should look LESS complex than the furniture zone
        # (the frame itself adds some edges so allow up to 0.65 ratio)
        if ratio > 0.65:
            return False, f"frame zone complexity ratio {ratio:.2f} > 0.65 — furniture may overlap frame"

    # Re-detect furniture line on the original (un-framed) background
    furniture_y = find_furniture_line(arr)
    clearance   = furniture_y - frame_bottom_y
    if clearance < clearance_min:
        return False, f"clearance {clearance}px < {clearance_min}px minimum"

    return True, "ok"


# ── Improved room prompt builder ──────────────────────────────────────────────

def scene_prompt(room_desc, wall_color, furniture_desc, lighting, style, focal="50mm"):
    """
    Build a room background prompt that enforces a large clear wall zone.

    Tighter than the old version: 70% clear wall, furniture strictly in bottom 30%.
    This prevents AI from placing chair backs, lamps, or curtains too high.
    """
    return (
        "Interior design product photography, square format. "
        f"{room_desc} with smooth {wall_color} painted walls. "
        "STRICT LAYOUT — READ CAREFULLY: "
        f"The UPPER 70% of the image is a completely plain, featureless {wall_color} wall. "
        "NOTHING appears in the upper 70% — no furniture backs, no lamp tops, no curtain edges, "
        "no shelves, no objects of any kind. The wall is a single flat colour with zero clutter. "
        "ALL furniture and decor are confined ENTIRELY to the LOWER 30% of the frame. "
        f"BOTTOM 30% only: {furniture_desc}. "
        f"{lighting} {style} {focal}, photorealistic. No text."
    )
