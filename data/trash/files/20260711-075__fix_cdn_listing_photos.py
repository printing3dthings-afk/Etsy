#!/usr/bin/env python3
"""
Fix CDN listing photos — bad rank 4-6 uploads used room scenes as art source.

For every wall-art listing whose art came from Etsy CDN (not a local DP file):
  1. Delete any photos at ranks 4-6 that were uploaded in the last 48 hours
  2. Download rank 1 (the actual product hero image) as the art source
  3. Re-add rank 4 = art_raw(hero),  rank 5 = frame_options(hero),
                rank 6 = closeup(hero)

Listings that use local DP art files are skipped — they already have
correct room composites.
"""

import sys, os, re, time, json, io, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient, EtsyAPIError

REPO  = Path(__file__).parent.parent
ART   = REPO / "data/digital_products/product_files"
UPSC  = ART / "upscaled"
TMP   = Path("/tmp/fix_cdn")
TMP.mkdir(exist_ok=True)

BG   = (253, 251, 247)
DARK = (44, 44, 44)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SKIP_TITLE_KEYWORDS = [
    "3d printed", "koozie", "can holder", "can koozie", "lamp",
    "planter", "candle holder", "tea light", "vase", "pen holder",
    "centerpiece", "arch", "sticker pack", "sticker bundle",
    "svg bundle", "commercial license", "sublimation", "tumbler wrap",
    "digital planner", "planner bundle", "kawaii planner bundle",
    "kawaii sticker",
]

# Cutoff: photos uploaded today are "ours to fix"
# fill_missing ran at ~14:40, fill_all at ~19:20 — use start-of-day cutoff
import time as _time, datetime as _dt
_today_start = _dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
CUTOFF_TSEC = int(_today_start.timestamp())


# ── Fonts ─────────────────────────────────────────────────────────────────────
def _fonts():
    def tf(p, s):
        try:    return ImageFont.truetype(p, s)
        except: return ImageFont.load_default()
    return {
        "h1":    tf(FONT_BOLD, 52),
        "h2":    tf(FONT_BOLD, 36),
        "body":  tf(FONT_REG,  28),
        "sm":    tf(FONT_REG,  22),
        "label": tf(FONT_BOLD, 26),
    }


# ── Photo generators ──────────────────────────────────────────────────────────
def make_art_raw(art_path: Path, out: Path) -> bool:
    try:
        art = Image.open(art_path).convert("RGB")
        aw, ah = art.size
        W = H = 2400
        scale = min((W - 100) / aw, (H - 100) / ah)
        nw, nh = int(aw * scale), int(ah * scale)
        resized = art.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), BG)
        canvas.paste(resized, ((W - nw) // 2, (H - nh) // 2))
        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] art_raw failed: {e}")
        return False


def make_frame_options(art_path: Path, out: Path) -> bool:
    try:
        F = _fonts()
        FRAMES = [
            ((139, 110, 80),  "Natural Wood"),
            ((30,  30,  30),  "Black"),
            ((240, 238, 233), "White"),
        ]
        W = H = 2400
        canvas = Image.new("RGB", (W, H), BG)
        draw   = ImageDraw.Draw(canvas)
        art    = Image.open(art_path).convert("RGB")

        col_w = W // 3
        for idx, (fc, label) in enumerate(FRAMES):
            bx = idx * col_w
            pad = 60
            inner_w = col_w - pad * 2
            inner_h = H - 260
            aw, ah = art.size
            scale   = min(inner_w / aw, inner_h / ah) * 0.82
            tw, th  = int(aw * scale), int(ah * scale)
            resized = art.resize((tw, th), Image.LANCZOS)

            frame_pad  = max(14, int(min(tw, th) * 0.06))
            mat_pad    = max(10, int(min(tw, th) * 0.04))
            outer_w    = tw + 2 * (frame_pad + mat_pad)
            outer_h    = th + 2 * (frame_pad + mat_pad)
            fx = bx + (col_w - outer_w) // 2
            fy = (H - 180 - outer_h) // 2

            shadow = Image.new("RGB", (outer_w + 8, outer_h + 8), (220, 215, 208))
            canvas.paste(shadow, (fx + 4, fy + 4))
            frame_img = Image.new("RGB", (outer_w, outer_h), fc)
            canvas.paste(frame_img, (fx, fy))
            mat = Image.new("RGB", (tw + 2 * mat_pad, th + 2 * mat_pad), (245, 243, 239))
            canvas.paste(mat, (fx + frame_pad, fy + frame_pad))
            canvas.paste(resized, (fx + frame_pad + mat_pad, fy + frame_pad + mat_pad))

            bbox = draw.textbbox((0, 0), label, font=F["label"])
            lw = bbox[2] - bbox[0]
            draw.text((bx + (col_w - lw) // 2, H - 160), label,
                      font=F["label"], fill=(100, 88, 75))

        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] frame_options failed: {e}")
        return False


def make_closeup(art_path: Path, out: Path) -> bool:
    try:
        F = _fonts()
        art  = Image.open(art_path).convert("RGB")
        aw, ah = art.size
        cx, cy = aw // 2, ah // 2
        cw, ch = int(aw * 0.70), int(ah * 0.70)
        crop   = art.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2))
        crop   = crop.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))

        W = H = 2400
        canvas = Image.new("RGB", (W, H), BG)
        tw, th = crop.size
        scale  = min((W - 120) / tw, (H - 200) / th)
        nw, nh = int(tw * scale), int(th * scale)
        resized = crop.resize((nw, nh), Image.LANCZOS)
        ox = (W - nw) // 2
        oy = (H - nh) // 2 - 30
        canvas.paste(resized, (ox, oy))

        badge  = "300 DPI · Fine Art Print"
        draw   = ImageDraw.Draw(canvas)
        bbox   = draw.textbbox((0, 0), badge, font=F["body"])
        bw, bh = bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 20
        bx     = (W - bw) // 2
        by_    = oy + nh + 24
        draw.rounded_rectangle([bx, by_, bx + bw, by_ + bh], radius=10, fill=(139, 110, 80))
        draw.text((bx + 20, by_ + 10), badge, font=F["body"], fill=(255, 255, 255))

        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] closeup failed: {e}")
        return False


# ── Helpers ───────────────────────────────────────────────────────────────────
def is_local_art(lid: int, title: str, lmap: dict) -> bool:
    """Return True if this listing has a local DP art file (not CDN-only)."""
    lid_to_pid = {v["listing_id"]: k for k, v in lmap.items()}
    if lid_to_pid.get(lid):
        return True
    if re.search(r"[Nn]o\.(\d+)", title):
        return True
    return False


def download_rank1(lid: int, imgs: list) -> Path | None:
    """Download rank 1 (hero) image from Etsy CDN."""
    rank1 = next((i for i in sorted(imgs, key=lambda x: x.get("rank", 99))
                  if i.get("rank", 0) == 1), None)
    if rank1 is None:
        rank1 = sorted(imgs, key=lambda x: x.get("rank", 99))[0] if imgs else None
    if rank1 is None:
        return None
    url = rank1.get("url_fullxfull") or rank1.get("url_570xN") or ""
    if not url:
        return None
    dest = TMP / f"hero_{lid}_r1.jpg"
    if dest.exists():
        dest.unlink()
    try:
        urllib.request.urlretrieve(url, str(dest))
        if dest.exists() and dest.stat().st_size > 5000:
            return dest
    except Exception:
        pass
    return None


def delete_image(client, lid: int, img_id: int, rank: int) -> bool:
    try:
        client.delete_listing_image(lid, img_id)
        print(f"      🗑  deleted rank={rank} id={img_id}")
        time.sleep(0.5)
        return True
    except EtsyAPIError as e:
        print(f"      ✗  delete rank={rank} id={img_id} failed: {e}")
        return False


def upload_img(client, lid: int, path: Path, rank: int, label: str) -> bool:
    for attempt in range(3):
        try:
            result  = client.upload_listing_image(lid, str(path), rank=rank)
            img_id  = result.get("listing_image_id", "?")
            print(f"      ✓ rank={rank}  {label}  id={img_id}")
            return True
        except EtsyAPIError as e:
            if getattr(e, "status_code", 0) == 429:
                wait = 12 * (attempt + 1)
                print(f"      429 — wait {wait}s")
                time.sleep(wait)
            else:
                print(f"      ✗ rank={rank} {e}")
                return False
        except Exception as e:
            print(f"      ✗ rank={rank} {e}")
            return False
    return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("Fix CDN Listing Photos — replace bad rank 4-6 with hero-based")
    print("=" * 65)

    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Etsy token refreshed OK")

    lmap = json.loads((REPO / "data/dp_listing_map.json").read_text())

    all_listings = client.get_shop_listings_all(state="active", limit=100)
    print(f"\nScanning {len(all_listings)} listings …\n")

    fixed = skipped = 0

    for l in sorted(all_listings, key=lambda x: x["listing_id"]):
        lid   = l["listing_id"]
        title = l["title"]
        tlow  = title.lower()

        # Skip non-wall-art categories
        if any(kw in tlow for kw in SKIP_TITLE_KEYWORDS):
            continue

        # Skip listings with known local art (they're already correct)
        if is_local_art(lid, title, lmap):
            continue

        imgs = client.get_listing_images(lid)
        time.sleep(0.07)

        # Find rank 3-6 photos uploaded today (from fill_missing or fill_all runs)
        bad_imgs = [
            i for i in imgs
            if i.get("rank", 0) in (3, 4, 5, 6)
            and i.get("created_timestamp", 0) >= CUTOFF_TSEC
        ]

        if not bad_imgs:
            continue

        print(f"  {lid}  '{title[:55]}'")
        print(f"    bad rank 3-6 photos: {[i.get('rank') for i in bad_imgs]}")

        # Download the rank 1 hero image as art source
        hero = download_rank1(lid, imgs)
        if hero is None:
            print(f"    [SKIP] could not download hero image")
            skipped += 1
            continue
        print(f"    hero: {hero.name}")

        # Delete the bad photos
        for img in sorted(bad_imgs, key=lambda i: i.get("rank", 0), reverse=True):
            delete_image(client, lid, img["listing_image_id"], img.get("rank"))

        # Wait for Etsy to settle after deletes
        time.sleep(2)

        # Re-generate using hero image — only fill rank 4-6 (rank 3 stays empty)
        replacements = [
            (4, "art_raw",       make_art_raw),
            (5, "frame_options", make_frame_options),
            (6, "closeup",       make_closeup),
        ]
        for rank, label, gen_fn in replacements:
            out = TMP / f"{lid}_rank{rank}.jpg"
            if gen_fn(hero, out):
                if upload_img(client, lid, out, rank, label):
                    time.sleep(1.2)
            else:
                print(f"    [SKIP] could not generate rank={rank}")

        fixed += 1
        print()

    print("=" * 65)
    print(f"Fixed: {fixed}  |  Skipped: {skipped}")


if __name__ == "__main__":
    main()
