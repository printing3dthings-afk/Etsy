#!/usr/bin/env python3
"""
video_generator.py

Creates short TikTok / Instagram Reels / Pinterest video slideshows from Etsy
listing photos. Each photo gets a Ken Burns effect (slow zoom + pan) to make
still images feel dynamic. Exports a silent 9:16 MP4 — add trending audio
directly in TikTok or Reels after uploading.

Output format: 1080×1920 (9:16), 24fps, H.264 MP4, ~15-30 seconds, silent.
File saved to: data/social/videos/{listing_id}_{style}.mp4

Usage:
  python tools/video_generator.py --listing 12345
  python tools/video_generator.py --listing 12345 --style new-drop
  python tools/video_generator.py --images a.jpg b.jpg c.jpg --title "My Product"
  python tools/video_generator.py --batch-3d          # all 3D product listings
  python tools/video_generator.py --batch-planners    # all digital planner listings

Styles:
  showcase    Slow elegant Ken Burns, title at top, CTA at bottom (default)
  new-drop    Faster cuts, "NEW" badge, energetic feel
  feature     One photo per feature with label text
  minimal     No text overlay, pure visual (for Pinterest)
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import random
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from moviepy import VideoClip, concatenate_videoclips

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

OUTPUT_DIR  = BASE / "data" / "social" / "videos"
CACHE_DIR   = BASE / "data" / "social" / "image_cache"

# ── Video constants ───────────────────────────────────────────────────────────

W, H    = 1080, 1920          # 9:16 TikTok/Reels
FPS     = 24
SHOP    = "OnBrandCraftz"
ETSY_URL = "etsy.com/shop/OnBrandCraftz"

FONT_BOLD    = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# ── Image loading & prep ──────────────────────────────────────────────────────

def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default(size=size)


def download_image(url: str, cache_key: str) -> Image.Image:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{cache_key}.jpg"
    if cache_path.exists():
        return Image.open(cache_path).convert("RGB")
    req = urllib.request.Request(url, headers={"User-Agent": "OnBrandCraftz/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.save(cache_path, "JPEG", quality=92)
    return img


def make_vertical_frame(img: Image.Image) -> Image.Image:
    """
    Fit any image into a 1080×1920 frame:
    - Blurred + darkened version of the image fills the background
    - Sharp version of the image centered on top, scaled to fit
    """
    # Background: stretch to fill, heavy blur, darken
    bg = img.resize((W, H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
    overlay = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, overlay, 0.45)

    # Foreground: fit within safe zone (1080 wide, 1350 tall — leaves room for text)
    safe_w, safe_h = W, int(H * 0.70)
    aspect = img.width / img.height
    if aspect >= (safe_w / safe_h):
        fw = safe_w
        fh = int(fw / aspect)
    else:
        fh = safe_h
        fw = int(fh * aspect)

    fg = img.resize((fw, fh), Image.LANCZOS)
    fx = (W - fw) // 2
    fy = int(H * 0.12) + (safe_h - fh) // 2   # offset down from top text area
    bg.paste(fg, (fx, fy))
    return bg


# ── Text overlays ─────────────────────────────────────────────────────────────

def draw_text_with_shadow(draw: ImageDraw.ImageDraw, xy: tuple,
                           text: str, font: ImageFont.FreeTypeFont,
                           fill: tuple = (255, 255, 255),
                           shadow: tuple = (0, 0, 0, 180),
                           shadow_offset: int = 3) -> None:
    x, y = xy
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font,
              fill=shadow[:3] if len(shadow) == 3 else shadow)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def add_title_bar(frame: Image.Image, title: str, subtitle: str = "") -> Image.Image:
    """Add a semi-transparent bar at top with product title."""
    frame = frame.copy()
    draw  = ImageDraw.Draw(frame, "RGBA")

    font_title = _load_font(FONT_BOLD,    52)
    font_sub   = _load_font(FONT_REGULAR, 36)

    bar_h = 160 if subtitle else 110
    bar   = Image.new("RGBA", (W, bar_h), (0, 0, 0, 160))
    frame.paste(bar, (0, 0), bar)

    draw = ImageDraw.Draw(frame)
    # Wrap title if too long
    words, line, lines = title.split(), "", []
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font_title)
        if bbox[2] > W - 60:
            if line:
                lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    lines = lines[:2]  # max 2 lines

    y = 18
    for l in lines:
        draw_text_with_shadow(draw, (30, y), l, font_title)
        y += 58

    if subtitle:
        draw_text_with_shadow(draw, (30, y + 4), subtitle, font_sub,
                               fill=(220, 220, 220))
    return frame


def add_cta_bar(frame: Image.Image, line1: str, line2: str = "") -> Image.Image:
    """Add a semi-transparent CTA bar at the bottom."""
    frame = frame.copy()
    bar_h = 130
    bar   = Image.new("RGBA", (W, bar_h), (0, 0, 0, 170))
    frame.paste(bar, (0, H - bar_h), bar)

    draw       = ImageDraw.Draw(frame)
    font_l1    = _load_font(FONT_BOLD,    44)
    font_l2    = _load_font(FONT_REGULAR, 34)

    draw_text_with_shadow(draw, (30, H - bar_h + 16), line1, font_l1,
                           fill=(255, 220, 100))   # gold accent
    if line2:
        draw_text_with_shadow(draw, (30, H - bar_h + 68), line2, font_l2,
                               fill=(200, 200, 200))
    return frame


def add_badge(frame: Image.Image, text: str,
              color: tuple = (220, 50, 50)) -> Image.Image:
    """Add a colored badge in the top-right corner."""
    frame  = frame.copy()
    draw   = ImageDraw.Draw(frame, "RGBA")
    font   = _load_font(FONT_BOLD, 38)
    pad    = 16
    bbox   = draw.textbbox((0, 0), text, font=font)
    bw     = bbox[2] - bbox[0] + pad * 2
    bh     = bbox[3] - bbox[1] + pad * 2
    bx     = W - bw - 24
    by     = 24

    badge_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd          = ImageDraw.Draw(badge_layer)
    bd.rounded_rectangle([bx, by, bx + bw, by + bh], radius=12,
                          fill=(*color, 230))
    frame.paste(badge_layer, (0, 0), badge_layer)

    draw = ImageDraw.Draw(frame)
    draw.text((bx + pad, by + pad), text, font=font, fill=(255, 255, 255))
    return frame


# ── Ken Burns effect ──────────────────────────────────────────────────────────

def ken_burns_clip(frame_img: Image.Image, duration: float,
                   zoom_start: float = 1.0, zoom_end: float = 1.12,
                   pan_x: float = 0.0, pan_y: float = 0.0) -> VideoClip:
    """
    Animate a still frame with slow zoom + pan (Ken Burns).
    pan_x / pan_y: -1.0 to 1.0, direction of pan over the duration.
    """
    arr = np.array(frame_img)

    def make_frame(t: float) -> np.ndarray:
        progress = t / duration if duration > 0 else 1.0
        # Ease in/out
        ease = 0.5 - 0.5 * math.cos(math.pi * progress)
        zoom = zoom_start + (zoom_end - zoom_start) * ease

        ch, cw = arr.shape[:2]
        crop_w = int(cw / zoom)
        crop_h = int(ch / zoom)

        # Pan offset
        max_px = (cw - crop_w) // 2
        max_py = (ch - crop_h) // 2
        cx = cw // 2 + int(pan_x * max_px * ease)
        cy = ch // 2 + int(pan_y * max_py * ease)

        left  = max(0, cx - crop_w // 2)
        top   = max(0, cy - crop_h // 2)
        right = min(cw, left + crop_w)
        bottom = min(ch, top + crop_h)

        cropped = arr[top:bottom, left:right]
        out = Image.fromarray(cropped).resize((W, H), Image.LANCZOS)
        return np.array(out)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def fade_clip(clip: VideoClip, fade_in: float = 0.4,
              fade_out: float = 0.4) -> VideoClip:
    """Apply fade in/out to a clip."""
    dur = clip.duration

    def make_frame(t: float) -> np.ndarray:
        frame = clip.get_frame(t)
        alpha = 1.0
        if t < fade_in:
            alpha = t / fade_in
        elif t > dur - fade_out:
            alpha = (dur - t) / fade_out
        if alpha < 1.0:
            frame = (frame * alpha).astype(np.uint8)
        return frame

    return VideoClip(make_frame, duration=dur).with_fps(FPS)


# ── Video styles ──────────────────────────────────────────────────────────────

# Pan directions that feel natural, cycling through images
_PAN_PATTERNS = [
    (0.4, 0.0),   # pan right
    (-0.4, 0.0),  # pan left
    (0.0, 0.3),   # pan down
    (0.3, -0.3),  # diagonal
    (-0.3, 0.3),  # diagonal other
    (0.0, -0.3),  # pan up
]


def build_showcase(images: list[Image.Image], title: str,
                   price: str = "", is_digital: bool = True) -> VideoClip:
    """Slow, elegant. Title bar on first frame, CTA on last frame."""
    per_photo  = 4.0
    zoom_pairs = [(1.0, 1.12), (1.1, 1.0), (1.0, 1.15), (1.05, 1.0)]
    clips      = []

    for i, img in enumerate(images[:6]):
        frame = make_vertical_frame(img)
        zoom_s, zoom_e = zoom_pairs[i % len(zoom_pairs)]
        pan_x, pan_y   = _PAN_PATTERNS[i % len(_PAN_PATTERNS)]

        if i == 0:
            sub = f"{'Instant Download' if is_digital else 'Ships to your door'}"
            if price:
                sub += f"  •  ${price}"
            frame = add_title_bar(frame, title, sub)
        if i == len(images[:6]) - 1:
            frame = add_cta_bar(frame,
                                f"Shop {SHOP} on Etsy",
                                "Link in bio 🛍️")

        clip = ken_burns_clip(frame, per_photo, zoom_s, zoom_e, pan_x, pan_y)
        clips.append(fade_clip(clip, fade_in=0.35, fade_out=0.35))

    return concatenate_videoclips(clips, method="compose")


def build_new_drop(images: list[Image.Image], title: str,
                   price: str = "", is_digital: bool = True) -> VideoClip:
    """Faster cuts. NEW badge. More energetic."""
    per_photo = 2.8
    clips     = []

    for i, img in enumerate(images[:7]):
        frame = make_vertical_frame(img)
        pan_x, pan_y = _PAN_PATTERNS[i % len(_PAN_PATTERNS)]

        frame = add_title_bar(frame, title)
        if i == 0:
            frame = add_badge(frame, "NEW ✦")
        if i == len(images[:7]) - 1:
            cta1 = f"Shop now — {SHOP}"
            cta2 = f"{'Instant Download' if is_digital else ''} • {ETSY_URL}"
            frame = add_cta_bar(frame, cta1, cta2)

        clip = ken_burns_clip(frame, per_photo, 1.0, 1.1, pan_x, pan_y)
        clips.append(fade_clip(clip, fade_in=0.2, fade_out=0.2))

    return concatenate_videoclips(clips, method="compose")


def build_feature(images: list[Image.Image], title: str,
                  labels: list[str] | None = None,
                  is_digital: bool = True) -> VideoClip:
    """Each photo gets a feature label at the bottom."""
    per_photo    = 3.5
    default_lbls = [
        "✨ Beautiful Design",
        "🎨 Multiple Sizes Included",
        "📱 Works on iPad & iPhone",
        "⬇️ Instant Download",
        "🛍️ Shop OnBrandCraftz",
    ]
    lbls  = (labels or default_lbls) + default_lbls
    clips = []

    for i, img in enumerate(images[:5]):
        frame  = make_vertical_frame(img)
        pan_x, pan_y = _PAN_PATTERNS[i % len(_PAN_PATTERNS)]
        if i == 0:
            frame = add_title_bar(frame, title)
        frame = add_cta_bar(frame, lbls[i])

        clip = ken_burns_clip(frame, per_photo, 1.0, 1.1, pan_x, pan_y)
        clips.append(fade_clip(clip, fade_in=0.3, fade_out=0.3))

    return concatenate_videoclips(clips, method="compose")


def build_minimal(images: list[Image.Image], title: str,
                  **kwargs) -> VideoClip:
    """No text. Pure visual. Best for Pinterest."""
    per_photo = 4.5
    clips     = []
    zoom_pairs = [(1.0, 1.15), (1.12, 1.0), (1.0, 1.1)]

    for i, img in enumerate(images[:6]):
        frame        = make_vertical_frame(img)
        zoom_s, zoom_e = zoom_pairs[i % len(zoom_pairs)]
        pan_x, pan_y   = _PAN_PATTERNS[i % len(_PAN_PATTERNS)]
        clip = ken_burns_clip(frame, per_photo, zoom_s, zoom_e, pan_x, pan_y)
        clips.append(fade_clip(clip, fade_in=0.5, fade_out=0.5))

    return concatenate_videoclips(clips, method="compose")


STYLES = {
    "showcase": build_showcase,
    "new-drop":  build_new_drop,
    "feature":   build_feature,
    "minimal":   build_minimal,
}

# ── Etsy data fetching ────────────────────────────────────────────────────────

def fetch_listing_images(listing_id: int, client) -> tuple[list[Image.Image], dict]:
    listing = client.get_listing(listing_id)
    images  = client.get_listing_images(listing_id)
    imgs    = []
    for img_data in sorted(images, key=lambda x: x.get("rank", 99)):
        url = img_data.get("url_fullxfull", "")
        if not url:
            continue
        try:
            pil = download_image(url, f"{listing_id}_{img_data.get('listing_image_id','')}")
            imgs.append(pil)
            if len(imgs) >= 7:
                break
        except Exception as e:
            print(f"  Warning: could not download image: {e}")
    return imgs, listing


def get_price_str(listing: dict) -> str:
    price = listing.get("price") or {}
    if isinstance(price, dict):
        amt = price.get("amount", 0)
        div = price.get("divisor", 100) or 100
        return f"{amt / div:.2f}"
    return ""


def is_digital(listing: dict) -> bool:
    return bool(listing.get("is_digital")) or "Instant Download" in (listing.get("title") or "")


# ── Batch selectors ───────────────────────────────────────────────────────────

PRINTIFY_MARKERS = ["Art Print", "Physical Print", "Wall Art Print", "Kawaii Wall Art",
                    "Candle Holder", "Can Coozie", "Koozie", "Tealight", "3D Print",
                    "Arch Centerpiece"]
PLANNER_MARKERS  = ["Digital Planner", "Life Planner", "Student Planner",
                    "Budget Planner", "Fitness Planner"]


def get_batch_listings(client, batch_type: str) -> list[dict]:
    all_listings = client.get_shop_listings_all(state="active")
    if batch_type == "3d":
        return [l for l in all_listings
                if any(m in (l.get("title") or "") for m in PRINTIFY_MARKERS)]
    if batch_type == "planners":
        return [l for l in all_listings
                if any(m in (l.get("title") or "") for m in PLANNER_MARKERS)]
    return all_listings


# ── Main ──────────────────────────────────────────────────────────────────────

def generate_video(images: list[Image.Image], title: str, style: str,
                   listing_id: int | str, price: str = "",
                   digital: bool = True) -> Path:
    if len(images) < 2:
        raise ValueError(f"Need at least 2 images, got {len(images)}")

    builder = STYLES.get(style, build_showcase)
    print(f"  Building '{style}' video ({len(images)} photos, "
          f"{len(images) * (4.0 if style == 'showcase' else 3.0):.0f}s est.)...")

    clip     = builder(images, title, price=price, is_digital=digital)
    duration = clip.duration

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:30])
    out_path   = OUTPUT_DIR / f"{listing_id}_{style}_{safe_title}.mp4"

    print(f"  Rendering {duration:.1f}s video → {out_path.name}")
    clip.write_videofile(
        str(out_path),
        codec="libx264",
        audio=False,
        fps=FPS,
        logger=None,  # suppress MoviePy progress output
        preset="fast",
    )
    print(f"  ✓ Saved: {out_path} ({out_path.stat().st_size // 1024}KB)")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TikTok/Reels video from listing photos")
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--listing",       type=int, help="Etsy listing ID")
    src_group.add_argument("--images",        nargs="+", help="Local image file paths")
    src_group.add_argument("--batch-3d",      action="store_true", help="All 3D product listings")
    src_group.add_argument("--batch-planners",action="store_true", help="All digital planner listings")

    parser.add_argument("--style", default="showcase",
                        choices=list(STYLES.keys()),
                        help="Video style (default: showcase)")
    parser.add_argument("--title",  default="", help="Override product title")
    parser.add_argument("--price",  default="", help="Price string to show (e.g. 14.99)")
    parser.add_argument("--all-styles", action="store_true",
                        help="Generate all 4 styles for the listing")
    args = parser.parse_args()

    with open(BASE / ".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    client = None

    # ── From local images ────────────────────────────────────────────────────
    if args.images:
        images = []
        for path in args.images:
            try:
                images.append(Image.open(path).convert("RGB"))
            except Exception as e:
                print(f"Warning: could not load {path}: {e}")
        if not images:
            print("ERROR: No valid images loaded")
            sys.exit(1)
        title  = args.title or Path(args.images[0]).stem
        styles = list(STYLES.keys()) if args.all_styles else [args.style]
        for style in styles:
            generate_video(images, title, style, "local", price=args.price)
        return

    # ── From Etsy API ────────────────────────────────────────────────────────
    sys.path.insert(0, str(BASE))
    from tools.etsy_api import EtsyAPIClient
    client = EtsyAPIClient()
    if not client.refresh_access_token():
        print("ERROR: Could not refresh OAuth token")
        sys.exit(1)

    if args.listing:
        listing_ids = [args.listing]
        batch_mode  = False
    else:
        batch_type  = "3d" if args.batch_3d else "planners"
        listings    = get_batch_listings(client, batch_type)
        listing_ids = [l["listing_id"] for l in listings]
        batch_mode  = True
        print(f"Batch mode: {len(listing_ids)} {batch_type} listings\n")

    styles = list(STYLES.keys()) if args.all_styles else [args.style]

    for i, lid in enumerate(listing_ids):
        if batch_mode:
            print(f"[{i+1}/{len(listing_ids)}] Listing {lid}")
        else:
            print(f"Listing {lid}")

        try:
            images, listing = fetch_listing_images(lid, client)
        except Exception as e:
            print(f"  ERROR fetching listing {lid}: {e}")
            continue

        if len(images) < 2:
            print(f"  Skipping — only {len(images)} image(s) available")
            continue

        title   = args.title or (listing.get("title") or "")[:60]
        price   = args.price or get_price_str(listing)
        digital = is_digital(listing)

        print(f"  Title: {title}")
        print(f"  Photos: {len(images)}  Price: ${price}  Digital: {digital}")

        for style in styles:
            try:
                generate_video(images, title, style, lid, price=price, digital=digital)
            except Exception as e:
                print(f"  ERROR generating {style} video: {e}")

        if batch_mode and i < len(listing_ids) - 1:
            time.sleep(1)

    print("\nDone. Upload videos to TikTok/Instagram Reels/Pinterest.")
    print("Add trending audio in-app after uploading.")
    print(f"Videos saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
