#!/usr/bin/env python3
"""
Fill ALL remaining listing photos to 10-photo standard.

Handles:
- ART✓ wall art at 6–9/10 (local DP files in dp_listing_map)
- Kawaii Art Print No.XXXX listings (art = DP{N}.jpg from upscaled/)
- Unmapped digital download singles at 8/10 (download rank-8 art from Etsy CDN)
- Non-numbered physical print listings at 3/10 (download rank-1 from Etsy CDN)
- B&W / nursery reprint listings at 2/10 (download rank-1 from Etsy CDN)

Photo slot logic (fills slots from current count up to 10):
  slot 4 → room living_room template
  slot 5 → room kitchen_dining template
  slot 6 → room entryway template
  slot 7 → "What's Included" info graphic
  slot 8 → art file raw (plain, no framing)
  slot 9 → frame options (black / white / natural wood) side-by-side
  slot 10 → close-up center crop with quality badge

Skips: 3D-printed products, koozies, sticker packs, SVG bundles, planners,
       planner bundles, sublimation.
"""

import sys, os, re, time, json, io, urllib.request, urllib.error
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient, EtsyAPIError

# ── Config ────────────────────────────────────────────────────────────────────
REPO   = Path(__file__).parent.parent
ART    = REPO / "data/digital_products/product_files"
UPSC   = ART / "upscaled"
TMP    = Path("/tmp/fill_photos")
TMP.mkdir(exist_ok=True)

BG   = (253, 251, 247)
DARK = (44, 44, 44)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

ROOM_TEMPLATES = {
    "living_room":    str(ART / "DP1007_room_living_room_natural_wood.jpg"),
    "kitchen_dining": str(ART / "DP1007_room_kitchen_dining_natural_wood.jpg"),
    "entryway":       str(ART / "DP1007_room_entryway_natural_wood.jpg"),
}
ROOM_BOUNDS = {
    "living_room":    (409, 164, 614, 464),
    "kitchen_dining": (400, 166, 624, 494),
    "entryway":       (430, 147, 593, 365),
}

# Listing IDs to skip entirely (non-wall-art or already handled)
SKIP_TITLE_KEYWORDS = [
    "3d printed", "koozie", "can holder", "can koozie", "lamp",
    "planter", "candle holder", "tea light", "vase", "pen holder",
    "centerpiece", "arch", "sticker pack", "sticker bundle", "sticker sheet",
    "svg bundle", "commercial license", "sublimation", "tumbler wrap",
    "digital planner", "planner bundle", "kawaii planner bundle",
    "kawaii sticker",
]


# ── Fonts ─────────────────────────────────────────────────────────────────────
def _fonts():
    def tf(path, size):
        try:  return ImageFont.truetype(path, size)
        except: return ImageFont.load_default()
    return {
        "h1": tf(FONT_BOLD, 52), "h2": tf(FONT_BOLD, 36),
        "body": tf(FONT_REG, 28), "sm": tf(FONT_REG, 22),
        "label": tf(FONT_BOLD, 26),
    }


# ── Art-file resolver ─────────────────────────────────────────────────────────
def resolve_art(lid: int, title: str, imgs: list, lmap: dict) -> Path | None:
    """
    Returns a local Path to the best available art file for this listing,
    or None if we can't find one.
    """
    lid_to_pid = {v["listing_id"]: k for k, v in lmap.items()}
    pid = lid_to_pid.get(lid)
    if pid:
        for fname in lmap[pid].get("files", []):
            candidates = [ART / fname, UPSC / fname]
            for c in candidates:
                if c.exists() and c.suffix in (".jpg", ".png", ".jpeg"):
                    return c

    # Kawaii Art Print No.XXXX
    m = re.search(r"[Nn]o\.(\d+)", title)
    if m:
        n = int(m.group(1))
        for cand in [UPSC / f"DP{n}.jpg", ART / f"DP{n}.jpg"]:
            if cand.exists():
                return cand

    # Download from Etsy CDN — prefer rank 8 (raw art) then rank 1
    sorted_imgs = sorted(imgs, key=lambda i: abs(i.get("rank", 99) - 8))
    for img in sorted_imgs:
        url = img.get("url_fullxfull") or img.get("url_570xN") or ""
        if not url:
            continue
        try:
            dest = TMP / f"etsy_{lid}_r{img.get('rank')}.jpg"
            if not dest.exists():
                urllib.request.urlretrieve(url, str(dest))
            if dest.exists() and dest.stat().st_size > 5000:
                return dest
        except Exception:
            continue

    return None


# ── Photo generators (PIL only) ───────────────────────────────────────────────
def make_room_composite(art_path: Path, room_key: str, out: Path) -> bool:
    try:
        bg = Image.open(ROOM_TEMPLATES[room_key]).convert("RGB")
        l, t, r, b = ROOM_BOUNDS[room_key]
        art = Image.open(art_path).convert("RGB")
        fw, fh = r - l, b - t
        aw, ah = art.size
        if (aw / ah) < (fw / fh):
            sw, sh = fw, int(fw * ah / aw)
            resized = art.resize((sw, sh), Image.LANCZOS)
            cy = (sh - fh) // 2
            crop = resized.crop((0, cy, sw, cy + fh))
        else:
            sh, sw = fh, int(fh * aw / ah)
            resized = art.resize((sw, sh), Image.LANCZOS)
            cx = (sw - fw) // 2
            crop = resized.crop((cx, 0, cx + fw, sh))
        crop = ImageEnhance.Brightness(crop).enhance(0.90)
        bg.paste(crop, (l, t))
        bg.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] room composite failed: {e}")
        return False


def make_whats_included(art_path: Path, out: Path, price: float = 0) -> bool:
    try:
        F = _fonts()
        W = H = 2400
        canvas = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(canvas)

        art = Image.open(art_path).convert("RGB")
        aw, ah = art.size
        ph = 1400
        pw = int(ph * aw / ah)
        if pw > 1000:
            pw = 1000; ph = int(pw * ah / aw)
        art_small = art.resize((pw, ph), Image.LANCZOS)
        ax = 120
        ay = (H - ph) // 2
        canvas.paste(art_small, (ax, ay))
        # Simple thin border
        draw.rectangle([ax - 3, ay - 3, ax + pw + 3, ay + ph + 3], outline=(180, 170, 158), width=3)

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


def make_art_raw(art_path: Path, out: Path) -> bool:
    try:
        art = Image.open(art_path).convert("RGB")
        aw, ah = art.size
        W = H = 2400
        scale = min((W - 100) / aw, (H - 100) / ah)
        nw, nh = int(aw * scale), int(ah * scale)
        resized = art.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), BG)
        ox = (W - nw) // 2
        oy = (H - nh) // 2
        canvas.paste(resized, (ox, oy))
        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] art_raw failed: {e}")
        return False


def make_frame_options(art_path: Path, out: Path) -> bool:
    """3 frames side by side: natural wood / black / white on 2400×2400."""
    try:
        F = _fonts()
        FRAMES = [
            ((139, 110, 80),  "Natural Wood"),
            ((28,  28,  28),  "Black"),
            ((240, 240, 240), "White"),
        ]
        W = H = 2400
        canvas = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(canvas)

        # Title banner at top
        draw.text((W // 2, 70), "— Frame Options —", font=F["h2"], fill=(100, 85, 65), anchor="mm")

        art = Image.open(art_path).convert("RGB")
        panel_w = 700
        mat = 20
        frame_thick = 14
        frame_y_top = 160

        # Art aspect ratio — fit inside panel
        aw, ah = art.size
        inner_h = int(panel_w * ah / aw)
        if inner_h > 1600:
            inner_h = 1600
            panel_w = int(inner_h * aw / ah)

        total_w = 3 * panel_w + 3 * (2 * mat + 2 * frame_thick) + 2 * 60
        start_x = (W - total_w) // 2

        for i, (fc, label) in enumerate(FRAMES):
            fw = panel_w + 2 * mat + 2 * frame_thick
            fh = inner_h + 2 * mat + 2 * frame_thick
            px = start_x + i * (fw + 60)
            py = frame_y_top

            # Shadow
            shadow_l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(shadow_l).rectangle(
                [px + 8, py + 10, px + fw + 8, py + fh + 10], fill=(0, 0, 0, 55)
            )
            shadow_l = shadow_l.filter(ImageFilter.GaussianBlur(12))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow_l).convert("RGB")
            draw = ImageDraw.Draw(canvas)

            # Frame
            draw.rectangle([px, py, px + fw, py + fh], fill=fc)
            # Highlight/shadow bevel
            hi = tuple(min(255, c + 35) for c in fc)
            sh_c = tuple(max(0, c - 35) for c in fc)
            bv = 4
            draw.polygon([px, py, px+fw, py, px+fw-bv, py+bv, px+bv, py+bv], fill=hi)
            draw.polygon([px, py, px, py+fh, px+bv, py+fh-bv, px+bv, py+bv], fill=hi)
            draw.polygon([px+fw, py, px+fw, py+fh, px+fw-bv, py+fh-bv, px+fw-bv, py+bv], fill=sh_c)
            draw.polygon([px, py+fh, px+fw, py+fh, px+fw-bv, py+fh-bv, px+bv, py+fh-bv], fill=sh_c)
            # Mat
            mx, my = px + frame_thick, py + frame_thick
            draw.rectangle([mx, my, mx + panel_w + 2*mat, my + inner_h + 2*mat], fill=(252, 250, 247))
            # Art
            art_r = art.resize((panel_w, inner_h), Image.LANCZOS)
            art_r = ImageEnhance.Brightness(art_r).enhance(0.93)
            canvas.paste(art_r, (mx + mat, my + mat))

            # Label below frame
            lx = px + fw // 2
            ly = py + fh + 26
            draw.text((lx, ly), label, font=F["label"], fill=(80, 68, 55), anchor="mt")

        # Bottom caption strip
        strip_y = H - 100
        draw.rectangle([0, strip_y, W, H], fill=DARK)
        draw.text((W // 2, strip_y + 50), "All frames sold separately — art print digital download",
                  font=F["body"], fill=(200, 190, 178), anchor="mm")

        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] frame_options failed: {e}")
        return False


def make_closeup(art_path: Path, out: Path) -> bool:
    """Center-70% crop, sharpened, with quality badge."""
    try:
        F = _fonts()
        art = Image.open(art_path).convert("RGB")
        aw, ah = art.size
        # Crop center 70%
        cx, cy = aw // 2, ah // 2
        crop_w, crop_h = int(aw * 0.70), int(ah * 0.70)
        crop = art.crop((cx - crop_w // 2, cy - crop_h // 2,
                         cx + crop_w // 2, cy + crop_h // 2))
        crop = crop.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))

        W = H = 2400
        canvas = Image.new("RGB", (W, H), BG)
        cw, ch = crop.size
        scale = min((W - 120) / cw, (H - 200) / ch)
        nw, nh = int(cw * scale), int(ch * scale)
        resized = crop.resize((nw, nh), Image.LANCZOS)
        ox = (W - nw) // 2
        oy = (H - nh) // 2 - 30
        canvas.paste(resized, (ox, oy))

        # Badge
        badge_text = "300 DPI · Fine Art Print"
        draw = ImageDraw.Draw(canvas)
        bbox = draw.textbbox((0, 0), badge_text, font=F["body"])
        bw = bbox[2] - bbox[0] + 40
        bh = bbox[3] - bbox[1] + 20
        bx = (W - bw) // 2
        by = oy + nh + 24
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=(139, 110, 80))
        draw.text((bx + 20, by + 10), badge_text, font=F["body"], fill=(255, 255, 255))

        canvas.save(str(out), "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"    [WARN] closeup failed: {e}")
        return False


# ── Upload helper ─────────────────────────────────────────────────────────────
def upload(client, lid: int, path: Path, rank: int, label: str) -> bool:
    for attempt in range(3):
        try:
            result = client.upload_listing_image(lid, str(path), rank=rank)
            img_id = result.get("listing_image_id", "?")
            print(f"      ✓ rank={rank}  {label}  id={img_id}")
            return True
        except EtsyAPIError as e:
            if getattr(e, "status_code", 0) == 429:
                wait = 12 * (attempt + 1)
                print(f"      429 — wait {wait}s …")
                time.sleep(wait)
            else:
                print(f"      ✗ rank={rank} EtsyAPIError: {e}")
                return False
        except Exception as e:
            print(f"      ✗ rank={rank} error: {e}")
            return False
    return False


# ── Slot plan for a listing ───────────────────────────────────────────────────
SLOT_PLAN = {
    4: ("room_living",   "living_room"),
    5: ("room_kitchen",  "kitchen_dining"),
    6: ("room_entryway", "entryway"),
    7: ("whats_included", None),
    8: ("art_raw",       None),
    9: ("frame_options", None),
    10: ("closeup",      None),
}


def process_listing(client, lid: int, title: str, n_photos: int,
                    lmap: dict, price: float) -> dict:
    """Fill all empty SLOT_PLAN ranks (4–10) for this listing."""

    title_lower = title.lower()
    for kw in SKIP_TITLE_KEYWORDS:
        if kw in title_lower:
            return {"lid": lid, "skipped": True, "reason": f"keyword '{kw}'"}

    # Refresh live photo state (may differ from n_photos after prior runs)
    imgs = client.get_listing_images(lid)
    existing_ranks = {i.get("rank", 0) for i in imgs}
    live_n = len(imgs)

    if live_n >= 10:
        return {"lid": lid, "skipped": True, "reason": "already at 10"}

    art = resolve_art(lid, title, imgs, lmap)
    if art is None:
        return {"lid": lid, "skipped": True, "reason": "no art file found"}

    # Don't do room composites for CDN-downloaded art — may be lifestyle photos already
    is_cdn_art = art.parent == TMP

    print(f"\n  {lid}  [{live_n}/10]  '{title[:55]}'")
    print(f"    art: {art.name}")

    uploads = 0
    # Iterate ALL SLOT_PLAN ranks so we fill gaps left by prior failed runs
    for rank in sorted(SLOT_PLAN.keys()):
        if rank in existing_ranks:
            continue  # already has a photo here

        slot_type, room_key = SLOT_PLAN[rank]

        out = TMP / f"{lid}_rank{rank}.jpg"
        if out.exists():
            out.unlink()  # force fresh generation

        ok = False
        if slot_type and "room_" in slot_type:
            if is_cdn_art:
                # CDN art might already be styled; use art_raw instead
                ok = make_art_raw(art, out)
            elif room_key and ROOM_TEMPLATES.get(room_key):
                ok = make_room_composite(art, room_key, out)  # fixed arg order
            else:
                ok = make_art_raw(art, out)
        elif slot_type == "whats_included":
            ok = make_whats_included(art, out, price)
        elif slot_type == "art_raw":
            ok = make_art_raw(art, out)
        elif slot_type == "frame_options":
            ok = make_frame_options(art, out)
        elif slot_type == "closeup":
            ok = make_closeup(art, out)

        if ok and out.exists():
            if upload(client, lid, out, rank, slot_type):
                uploads += 1
            time.sleep(1.2)
        else:
            print(f"    [SKIP] could not generate rank={rank}")

    return {"lid": lid, "skipped": False, "uploads": uploads,
            "target": 10 - live_n, "art": art.name}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("Fill All Listing Photos — bring everything to 10-photo standard")
    print("=" * 65)

    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Etsy token refreshed OK")

    lmap = json.loads((REPO / "data/dp_listing_map.json").read_text())

    all_listings = client.get_shop_listings_all(state="active", limit=100)

    # Get photo counts for all
    print(f"\nChecking photo counts for {len(all_listings)} listings …")
    to_process = []
    for l in all_listings:
        try:
            imgs = client.get_listing_images(l["listing_id"])
            n = len(imgs)
            time.sleep(0.07)
        except:
            n = 0
        if n < 10:
            to_process.append({
                "lid":    l["listing_id"],
                "title":  l["title"],
                "n":      n,
                "price":  l.get("price", {}).get("amount", 0) / 100.0
            })

    to_process.sort(key=lambda x: (x["n"], x["lid"]))
    print(f"Found {len(to_process)} listings under 10 photos")

    results = []
    for item in to_process:
        r = process_listing(client, item["lid"], item["title"], item["n"], lmap, item["price"])
        results.append(r)

    # Summary
    print(f"\n{'=' * 65}")
    print("SUMMARY")
    print("=" * 65)
    filled = [r for r in results if not r.get("skipped")]
    skipped = [r for r in results if r.get("skipped")]
    total_uploads = sum(r.get("uploads", 0) for r in filled)

    print(f"  Listings processed: {len(filled)}")
    print(f"  Total photos uploaded: {total_uploads}")
    print(f"  Skipped: {len(skipped)}")

    if filled:
        print("\n  Filled listings:")
        for r in filled:
            u, t = r.get("uploads", 0), r.get("target", 0)
            status = "✓" if u >= t else f"partial ({u}/{t})"
            print(f"    {status}  {r['lid']}  art={r.get('art','?')}")

    if skipped:
        print("\n  Skipped:")
        for r in skipped[:15]:
            print(f"    {r['lid']}  reason={r.get('reason')}")
        if len(skipped) > 15:
            print(f"    … and {len(skipped) - 15} more")


if __name__ == "__main__":
    main()
