#!/usr/bin/env python3
"""
Final CDN cleanup — delete the 4 bad fill_all photos (whats_included/art_raw/
frame_options/closeup using empty-room art) that are still on 25 CDN listings,
then fill each listing up to 10 photos using the hero image.

Run ONCE. Idempotent — skips any ID that no longer exists on the listing.
"""

import sys, time, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient, EtsyAPIError

TMP   = Path("/tmp/final_cdn_cleanup")
TMP.mkdir(exist_ok=True)

BG    = (253, 251, 247)
DARK  = (44, 44, 44)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ── Bad image IDs from fill_all second run (ranks 7-10 using empty-room art) ──
# Ranks 4-6 were already deleted by fix_cdn. Only ranks 7-10 remain bad.
BAD_IDS = {
    4513713044: [8146393629, 8098489962, 8146393949, 8098490372],
    4513713106: [8146394831, 8146394971, 8098491400, 8146395317],
    4513713142: [8098492080, 8098492228, 8146396185, 8098492512],
    4515672588: [8146415409, 8098511232, 8098511448, 8098511616],
    4515672864: [8098512352, 8098512476, 8098512626, 8146416963],
    4515672972: [8098514600, 8098514710, 8146418999, 8098515014],
    4515673064: [8146419711, 8146419901, 8098516034, 8146420187],
    4515673288: [8098516746, 8146420901, 8098517048, 8146421283],
    4515673500: [8098517954, 8098518110, 8098518302, 8146422339],
    4515673828: [8098518976, 8146422947, 8098519222, 8146423199],
    4515673940: [8098520066, 8146423833, 8146423939, 8146424063],
    4515674144: [8146424763, 8146424887, 8146425051, 8098521464],
    4515674250: [8098522186, 8098522304, 8098522504, 8146426289],
    4515674340: [8146426809, 8146426977, 8146427127, 8098523624],
    4515674486: [8146427877, 8098524472, 8146428167, 8098524784],
    4515674594: [8098525440, 8098525530, 8146429145, 8146429279],
    4515674696: [8098526376, 8146430031, 8098526674, 8146430345],
    4515676185: [8146436975, 8146437077, 8098533830, 8098533998],
    4515676711: [8098534642, 8098534738, 8098534864, 8146438385],
    4515676915: [8146438995, 8098535818, 8098535996, 8146439485],
    4515677081: [8098536818, 8146440313, 8098537140, 8098537268],
    4515677207: [8146441215, 8146441311, 8098538114, 8146441597],
    4515678828: [8146444183, 8146444323, 8098541060, 8146444591],
    4515678904: [8146445121, 8098541866, 8098542000, 8098542142],
    4515682265: [8146447415, 8098544148, 8146447773, 8098544504],
}

import urllib.request


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


def download_hero(lid: int, imgs: list) -> Path | None:
    rank1 = next((i for i in sorted(imgs, key=lambda x: x.get("rank", 99))
                  if i.get("rank", 0) == 1), None)
    if rank1 is None and imgs:
        rank1 = sorted(imgs, key=lambda x: x.get("rank", 99))[0]
    if rank1 is None:
        return None
    url = rank1.get("url_fullxfull") or rank1.get("url_570xN") or ""
    if not url:
        return None
    dest = TMP / f"hero_{lid}.jpg"
    if dest.exists():
        dest.unlink()
    try:
        urllib.request.urlretrieve(url, str(dest))
        if dest.exists() and dest.stat().st_size > 5000:
            return dest
    except Exception:
        pass
    return None


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
        col_w  = W // 3
        for idx, (fc, label) in enumerate(FRAMES):
            bx     = idx * col_w
            pad    = 60
            inner_w = col_w - pad * 2
            inner_h = H - 260
            aw, ah  = art.size
            scale   = min(inner_w / aw, inner_h / ah) * 0.82
            tw, th  = int(aw * scale), int(ah * scale)
            resized = art.resize((tw, th), Image.LANCZOS)
            fp      = max(14, int(min(tw, th) * 0.06))
            mp      = max(10, int(min(tw, th) * 0.04))
            ow, oh  = tw + 2 * (fp + mp), th + 2 * (fp + mp)
            fx = bx + (col_w - ow) // 2
            fy = (H - 180 - oh) // 2
            shadow = Image.new("RGB", (ow + 8, oh + 8), (220, 215, 208))
            canvas.paste(shadow, (fx + 4, fy + 4))
            frame_img = Image.new("RGB", (ow, oh), fc)
            canvas.paste(frame_img, (fx, fy))
            mat = Image.new("RGB", (tw + 2 * mp, th + 2 * mp), (245, 243, 239))
            canvas.paste(mat, (fx + fp, fy + fp))
            canvas.paste(resized, (fx + fp + mp, fy + fp + mp))
            bbox = draw.textbbox((0, 0), label, font=F["label"])
            lw   = bbox[2] - bbox[0]
            draw.text((bx + (col_w - lw) // 2, H - 160), label,
                      font=F["label"], fill=(100, 88, 75))
        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] frame_options failed: {e}")
        return False


def make_closeup(art_path: Path, out: Path) -> bool:
    try:
        F    = _fonts()
        art  = Image.open(art_path).convert("RGB")
        aw, ah = art.size
        cx, cy = aw // 2, ah // 2
        cw, ch = int(aw * 0.70), int(ah * 0.70)
        crop   = art.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2))
        crop   = crop.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
        W = H  = 2400
        canvas = Image.new("RGB", (W, H), BG)
        tw, th = crop.size
        scale  = min((W - 120) / tw, (H - 200) / th)
        nw, nh = int(tw * scale), int(th * scale)
        resized = crop.resize((nw, nh), Image.LANCZOS)
        ox = (W - nw) // 2
        oy = (H - nh) // 2 - 30
        canvas.paste(resized, (ox, oy))
        badge = "300 DPI · Fine Art Print"
        draw  = ImageDraw.Draw(canvas)
        bbox  = draw.textbbox((0, 0), badge, font=F["body"])
        bw, bh = bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 20
        bx    = (W - bw) // 2
        by_   = oy + nh + 24
        draw.rounded_rectangle([bx, by_, bx + bw, by_ + bh], radius=10, fill=(139, 110, 80))
        draw.text((bx + 20, by_ + 10), badge, font=F["body"], fill=(255, 255, 255))
        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] closeup failed: {e}")
        return False


def make_whats_included(art_path: Path, out: Path, price: float = 0) -> bool:
    try:
        F = _fonts()
        W = H = 2400
        canvas = Image.new("RGB", (W, H), BG)
        draw   = ImageDraw.Draw(canvas)
        art    = Image.open(art_path).convert("RGB")
        aw, ah = art.size
        ph     = 1400
        pw     = int(ph * aw / ah)
        if pw > 1000:
            pw = 1000; ph = int(pw * ah / aw)
        art_small = art.resize((pw, ph), Image.LANCZOS)
        ax = 120
        ay = (H - ph) // 2
        canvas.paste(art_small, (ax, ay))
        draw.rectangle([ax - 3, ay - 3, ax + pw + 3, ay + ph + 3],
                       outline=(180, 170, 158), width=3)
        rx = ax + pw + 100
        ry = 260
        draw.text((rx, ry), "INSTANT DOWNLOAD", font=F["h1"], fill=(139, 110, 80))
        ry += 78
        draw.rectangle([rx, ry, W - 120, ry + 3], fill=(139, 110, 80))
        ry += 28
        if price:
            draw.text((rx, ry), f"${price:.2f}", font=F["h1"], fill=DARK)
            ry += 80
        draw.text((rx, ry), "WHAT'S INCLUDED:", font=F["h2"], fill=DARK)
        ry += 58
        items = [
            "✓  High-resolution JPG (300 DPI)",
            "✓  Multiple print sizes included",
            "✓  4×6  ·  5×7  ·  8×10  ·  8×12",
            "✓  11×14  ·  16×20  ·  18×24  ·  24×36",
            "✓  Print at home or any print shop",
            "✓  Personal use license included",
        ]
        for item in items:
            draw.text((rx, ry), item, font=F["body"], fill=(80, 70, 60))
            ry += 46
        ry += 18
        draw.rectangle([rx, ry, W - 120, ry + 2], fill=(200, 190, 178))
        ry += 26
        draw.text((rx, ry), "FORMAT: JPG  ·  RESOLUTION: 300 DPI  ·  COLOR: sRGB",
                  font=F["sm"], fill=(130, 115, 100))
        ry += 40
        draw.text((rx, ry), "© OnBrandCraftz  |  Personal use license",
                  font=F["sm"], fill=(160, 148, 135))
        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] whats_included failed: {e}")
        return False


def upload_img(client, lid: int, path: Path, rank: int, label: str) -> bool:
    for attempt in range(3):
        try:
            result = client.upload_listing_image(lid, str(path), rank=rank)
            img_id = result.get("listing_image_id", "?")
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


def main():
    print("=" * 65)
    print("Final CDN Cleanup — delete bad fill_all photos, fill to 10")
    print("=" * 65)

    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Etsy token refreshed OK\n")

    fixed = 0

    for lid, bad_ids in sorted(BAD_IDS.items()):
        print(f"  {lid}")
        imgs = client.get_listing_images(lid)
        time.sleep(0.1)
        existing_ids = {i["listing_image_id"]: i.get("rank", 0) for i in imgs}
        n_existing   = len(imgs)

        # Delete bad images that still exist
        deleted = 0
        for img_id in bad_ids:
            if img_id in existing_ids:
                try:
                    client.delete_listing_image(lid, img_id)
                    print(f"    🗑  deleted id={img_id} (was rank={existing_ids[img_id]})")
                    deleted += 1
                    time.sleep(0.6)
                except EtsyAPIError as e:
                    print(f"    ✗  delete id={img_id} failed: {e}")
            else:
                print(f"    –  id={img_id} already gone, skip")

        if deleted == 0:
            # Re-fetch to get current count
            pass

        # Wait for Etsy to settle
        if deleted > 0:
            time.sleep(2)

        # Re-fetch current photo count
        imgs = client.get_listing_images(lid)
        time.sleep(0.1)
        n_now = len(imgs)
        existing_ranks = {i.get("rank", 0) for i in imgs}

        print(f"    photos now: {n_now}/10  (deleted {deleted})")

        if n_now >= 10:
            print(f"    already at 10, done")
            fixed += 1
            print()
            continue

        # Download hero image
        hero = download_hero(lid, imgs)
        if hero is None:
            print(f"    [SKIP] could not download hero image")
            print()
            continue

        # After deleting 4 bad photos, listing has 5 photos at ranks 1-5.
        # Fill ranks 6-10 with good hero-based photos.
        fill_plan = [
            (6,  "art_raw",        lambda a, o: make_art_raw(a, o)),
            (7,  "whats_included", lambda a, o: make_whats_included(a, o, 0)),
            (8,  "art_raw_2",      lambda a, o: make_art_raw(a, o)),
            (9,  "frame_options",  lambda a, o: make_frame_options(a, o)),
            (10, "closeup",        lambda a, o: make_closeup(a, o)),
        ]

        for rank, label, gen_fn in fill_plan:
            if rank in existing_ranks:
                continue
            if n_now >= 10:
                break
            out = TMP / f"{lid}_rank{rank}.jpg"
            if out.exists():
                out.unlink()
            if gen_fn(hero, out):
                if upload_img(client, lid, out, rank, label):
                    n_now += 1
                    time.sleep(1.2)
            else:
                print(f"    [SKIP] could not generate {label}")

        fixed += 1
        print()

    print("=" * 65)
    print(f"Done. Processed: {fixed}")


if __name__ == "__main__":
    main()
