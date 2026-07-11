#!/usr/bin/env python3
"""
shop_audit.py — Comprehensive Shop Listing Photo Audit
Builds /home/user/Etsy/review_batches/shop_audit.html

For every active listing:
  - Fetches photo #1 from Etsy
  - If mapped in dp_listing_map.json, compares to saved art file via dhash (16x16)
  - Also runs nearest-neighbour search against ALL 62 upscaled art files
  - Flags where the nearest-neighbour match is NOT the expected DP (= possible wrong art)
  - Checks for missing digital files, composite overflow
  - Renders a full HTML report with embedded base64 images
"""

from __future__ import annotations

import os
import sys
import json
import time
import base64
import urllib.request
import urllib.error
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path("/home/user/Etsy")
sys.path.insert(0, str(ROOT))

def load_env(path: Path):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env(ROOT / ".env")

from tools.etsy_api import EtsyAPIClient  # noqa: E402

UPSCALED_DIR  = ROOT / "data" / "digital_products" / "product_files" / "upscaled"
PRODUCT_FILES = ROOT / "data" / "digital_products" / "product_files"
DP_MAP_PATH   = ROOT / "data" / "dp_listing_map.json"
OUTPUT_PATH   = ROOT / "review_batches" / "shop_audit.html"

# Hamming distance thresholds for dhash comparison (16×16 = 256 bits max)
# For lifestyle-composited photos vs raw art, distances cluster around 90-145.
# "Expected" art still tends to rank as the closest or near-closest match.
# We flag when the expected DP is NOT in the top-3 closest art files.
MISMATCH_THRESHOLD = 20       # direct comparison: >20 = mismatch label
WRONG_ART_RANK_THRESHOLD = 3  # nearest-neighbour: flag if expected art ranks > this

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("WARNING: PIL not available")


# ── dhash ─────────────────────────────────────────────────────────────────────

def dhash(img: "Image.Image", hash_size: int = 16) -> int:
    gray = img.convert("L").resize((hash_size + 1, hash_size), Image.LANCZOS)
    pixels = list(gray.getdata())
    bits = 0
    for row in range(hash_size):
        for col in range(hash_size):
            left  = pixels[row * (hash_size + 1) + col]
            right = pixels[row * (hash_size + 1) + col + 1]
            bits  = (bits << 1) | (1 if left > right else 0)
    return bits


def hamming(a: int, b: int) -> int:
    x = a ^ b
    c = 0
    while x:
        c += x & 1
        x >>= 1
    return c


# ── Image utilities ───────────────────────────────────────────────────────────

def download_image(url: str, max_retries: int = 3) -> Optional[bytes]:
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ShopAuditBot/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                print(f"    [WARN] Download failed: {url} — {e}")
    return None


def to_b64_thumb(img: "Image.Image", max_width: int = 400) -> Optional[str]:
    if not HAS_PIL or img is None:
        return None
    try:
        w, h = img.size
        if w > max_width:
            img = img.resize((int(w * max_width / w), int(h * max_width / w)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        print(f"    [WARN] Thumbnail failed: {e}")
        return None


def load_img(source) -> Optional["Image.Image"]:
    """Load a PIL Image from bytes or a Path."""
    if not HAS_PIL:
        return None
    try:
        if isinstance(source, (bytes, bytearray)):
            return Image.open(BytesIO(source)).convert("RGB")
        else:
            return Image.open(source).convert("RGB")
    except Exception:
        return None


def load_thumb_b64(source, max_width: int = 400) -> Optional[str]:
    img = load_img(source)
    if img is None:
        return None
    return to_b64_thumb(img, max_width)


# ── Composite overflow detector ───────────────────────────────────────────────

def detect_composite_overflow(img: "Image.Image") -> bool:
    """Heuristic: detect art bleeding beyond frame into room edge bands."""
    if not HAS_PIL or img is None:
        return False
    try:
        w, h = img.size
        sw = max(1, w // 20)

        def edge_var(region) -> float:
            small = region.resize((10, 10), Image.LANCZOS).convert("L")
            pixels = list(small.getdata())
            mean = sum(pixels) / len(pixels)
            return sum((p - mean) ** 2 for p in pixels) / len(pixels)

        variances = [
            edge_var(img.crop((0, 0, sw, h))),
            edge_var(img.crop((w - sw, 0, w, h))),
            edge_var(img.crop((0, 0, w, sw))),
            edge_var(img.crop((0, h - sw, w, h))),
        ]
        return all(v < 50 for v in variances)
    except Exception:
        return False


# ── Pre-load all art hashes ───────────────────────────────────────────────────

def load_all_art_hashes() -> dict[str, int]:
    """Load dhash for every .jpg in upscaled/ directory."""
    hashes: dict[str, int] = {}
    if not HAS_PIL:
        return hashes
    for f in sorted(UPSCALED_DIR.glob("*.jpg")):
        img = load_img(f)
        if img:
            hashes[f.stem] = dhash(img)
    print(f"[INFO] Pre-loaded {len(hashes)} art file hashes from upscaled/")
    return hashes


# ── Fetch all active listings ─────────────────────────────────────────────────

def fetch_all_listings(client: EtsyAPIClient) -> list[dict]:
    all_results = []
    offset = 0
    limit  = 100
    total  = None

    print(f"[INFO] Fetching active listings from shop {client.shop_id}...")
    while True:
        resp  = client._request(
            "GET",
            f"shops/{client.shop_id}/listings",
            params={"state": "active", "limit": limit, "offset": offset, "includes": "images"},
        )
        batch = resp.get("results", [])
        if total is None:
            total = resp.get("count", 0)
            print(f"[INFO] Total active listings: {total}")
        all_results.extend(batch)
        print(f"  Fetched {len(all_results)}/{total} listings...")
        if len(batch) < limit:
            break
        offset += len(batch)
        if offset >= total:
            break
    return all_results


# ── Fetch digital files ───────────────────────────────────────────────────────

def fetch_digital_files(client: EtsyAPIClient, listing_id: int) -> list[dict]:
    """Return list of {filename, filesize, rank} dicts."""
    try:
        resp = client._request("GET", f"shops/{client.shop_id}/listings/{listing_id}/files")
        return resp.get("results", [])
    except Exception as e:
        print(f"    [WARN] Could not fetch files for {listing_id}: {e}")
        return []


# ── Build reverse map ─────────────────────────────────────────────────────────

def build_rev_map(dp_map: dict) -> dict[int, list[str]]:
    rev: dict[int, list[str]] = {}
    for dp_num, info in dp_map.items():
        lid = info.get("listing_id")
        if lid:
            rev.setdefault(int(lid), []).append(dp_num)
    return rev


# ── Find art file for a DP ─────────────────────────────────────────────────────

def find_art_file(dp_num: str) -> Optional[Path]:
    candidates = [
        UPSCALED_DIR / f"{dp_num}.jpg",
        PRODUCT_FILES / f"{dp_num}.jpg",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


# ── HTML helpers ──────────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def badge(status: str) -> str:
    palette = {
        "MATCHED":       ("#16a34a", "#fff"),
        "MISMATCH":      ("#dc2626", "#fff"),
        "NO FILE":       ("#6b7280", "#fff"),
        "NO PHOTO":      ("#ea580c", "#fff"),
        "WRONG ART":     ("#7c3aed", "#fff"),
        "NEEDS REVIEW":  ("#b45309", "#fff"),
        "UNMAPPED":      ("#0e7490", "#fff"),
    }
    bg, fg = palette.get(status.upper(), ("#475569", "#fff"))
    return f'<span class="badge" style="background:{bg};color:{fg}">{_esc(status)}</span>'


def img_tag(b64: Optional[str], alt: str = "", mw: int = 400) -> str:
    if b64:
        return f'<img src="data:image/jpeg;base64,{b64}" alt="{_esc(alt)}" loading="lazy" style="max-width:{mw}px;border-radius:6px;display:block">'
    return '<div class="no-img">No image</div>'


# ── Main audit ────────────────────────────────────────────────────────────────

def run_audit():
    client = EtsyAPIClient()
    if not client.api_key and not client.access_token:
        print("[ERROR] No Etsy credentials.")
        sys.exit(1)

    dp_map = json.loads(DP_MAP_PATH.read_text()) if DP_MAP_PATH.exists() else {}
    print(f"[INFO] dp_listing_map: {len(dp_map)} entries")
    rev_map = build_rev_map(dp_map)

    art_hashes = load_all_art_hashes()

    listings = fetch_all_listings(client)
    print(f"\n[INFO] Processing {len(listings)} listings...\n")

    records = []
    for i, listing in enumerate(listings):
        lid   = int(listing["listing_id"])
        title = listing.get("title", "")
        print(f"[{i+1}/{len(listings)}] {lid}: {title[:55]}")

        # ── Cover photo ────────────────────────────────────────────────────
        images    = listing.get("images") or []
        cover_img = next((x for x in images if x.get("rank") == 1), images[0] if images else None)
        photo_url = (cover_img or {}).get("url_570xN")

        photo_bytes: Optional[bytes] = None
        photo_img_pil: Optional["Image.Image"] = None
        photo_b64: Optional[str] = None
        photo_hash: Optional[int] = None

        if photo_url:
            photo_bytes = download_image(photo_url)
            if photo_bytes:
                photo_img_pil = load_img(photo_bytes)
                photo_b64     = to_b64_thumb(photo_img_pil) if photo_img_pil else None
                if photo_img_pil and HAS_PIL:
                    photo_hash = dhash(photo_img_pil)
            time.sleep(0.1)

        # ── Digital files ──────────────────────────────────────────────────
        digital_file_records = fetch_digital_files(client, lid)
        digital_filenames    = [f["filename"] for f in digital_file_records]
        digital_filesizes    = {f["filename"]: f.get("filesize", "") for f in digital_file_records}
        time.sleep(0.25)

        # ── DP mapping ────────────────────────────────────────────────────
        dp_nums     = rev_map.get(lid, [])
        primary_dp  = next(
            (dp for dp in sorted(dp_nums) if dp_map.get(dp, {}).get("status") == "active"),
            sorted(dp_nums)[0] if dp_nums else None,
        )

        # ── Art file lookup ───────────────────────────────────────────────
        art_path: Optional[Path] = find_art_file(primary_dp) if primary_dp else None
        art_b64:  Optional[str]  = load_thumb_b64(art_path) if art_path else None
        art_hash: Optional[int]  = art_hashes.get(primary_dp) if primary_dp else None

        # ── Direct hash comparison (expected DP vs cover photo) ────────────
        direct_distance: Optional[int] = None
        if photo_hash is not None and art_hash is not None:
            direct_distance = hamming(photo_hash, art_hash)

        # Classify direct comparison result
        if direct_distance is None:
            if not art_path:
                direct_status = "NO FILE"
            else:
                direct_status = "NO PHOTO"
        elif direct_distance <= MISMATCH_THRESHOLD:
            direct_status = "MATCHED"
        else:
            direct_status = "MISMATCH"

        # ── Nearest-neighbour search ───────────────────────────────────────
        # For lifestyle composite photos, the expected art may still rank as
        # the closest match even at high absolute distance.
        nearest: list[tuple[int, str]] = []  # (distance, dp_name)
        wrong_art_flag = False
        nn_rank_of_expected: Optional[int] = None

        if photo_hash is not None and art_hashes:
            nearest = sorted((hamming(photo_hash, h), dp) for dp, h in art_hashes.items())[:5]
            if primary_dp:
                expected_rank = next(
                    (rank + 1 for rank, (_, dp) in enumerate(nearest) if dp == primary_dp),
                    None,
                )
                # Look beyond top-5 if not found
                if expected_rank is None:
                    all_ranked = sorted((hamming(photo_hash, h), dp) for dp, h in art_hashes.items())
                    expected_rank = next(
                        (rank + 1 for rank, (_, dp) in enumerate(all_ranked) if dp == primary_dp),
                        None,
                    )
                nn_rank_of_expected = expected_rank
                wrong_art_flag = (
                    expected_rank is not None
                    and expected_rank > WRONG_ART_RANK_THRESHOLD
                    and art_hash is not None  # only flag if we actually have the art
                )

        # ── Composite overflow ────────────────────────────────────────────
        composite_flag = detect_composite_overflow(photo_img_pil) if photo_img_pil else False

        # ── Build flags ────────────────────────────────────────────────────
        flags = []
        if not digital_filenames:
            flags.append("No digital files attached to this listing")
        if wrong_art_flag:
            flags.append(
                f"Nearest-neighbour: expected {primary_dp} ranks #{nn_rank_of_expected} "
                f"(top match is {nearest[0][1]}, Δ={nearest[0][0]}) — possible wrong art in listing photo"
            )
        if composite_flag:
            flags.append("Possible composite overflow: edges appear flat-colour (art may bleed past frame)")
        if not photo_url:
            flags.append("No cover photo on this listing")
        if not dp_nums:
            flags.append("Listing not mapped in dp_listing_map.json")
        if dp_nums and not art_path:
            flags.append(f"Art file not found locally for {primary_dp}")

        # Overall review status (for sorting / filtering)
        if wrong_art_flag:
            review_status = "WRONG ART"
        elif not digital_filenames:
            review_status = "NEEDS REVIEW"
        elif not dp_nums:
            review_status = "UNMAPPED"
        elif direct_status == "MATCHED":
            review_status = "MATCHED"
        elif art_path:
            review_status = "MISMATCH"  # high distance but has art — expected for composite photos
        else:
            review_status = "NO FILE"

        records.append({
            "listing_id":         lid,
            "title":              title,
            "dp_nums":            dp_nums,
            "primary_dp":         primary_dp,
            "photo_url":          photo_url,
            "photo_b64":          photo_b64,
            "art_path":           str(art_path) if art_path else None,
            "art_b64":            art_b64,
            "direct_distance":    direct_distance,
            "direct_status":      direct_status,
            "nearest":            nearest,
            "nn_rank_expected":   nn_rank_of_expected,
            "wrong_art_flag":     wrong_art_flag,
            "composite_flag":     composite_flag,
            "digital_filenames":  digital_filenames,
            "digital_filesizes":  digital_filesizes,
            "flags":              flags,
            "review_status":      review_status,
        })

    # ── Summary counts ─────────────────────────────────────────────────────
    total         = len(records)
    wrong_art     = sum(1 for r in records if r["wrong_art_flag"])
    no_digital    = sum(1 for r in records if not r["digital_filenames"])
    composite_cnt = sum(1 for r in records if r["composite_flag"])
    unmapped      = sum(1 for r in records if not r["dp_nums"])
    no_art_file   = sum(1 for r in records if r["dp_nums"] and not r["art_path"])
    matched_direct = sum(1 for r in records if r["direct_status"] == "MATCHED")
    needs_review  = sum(1 for r in records if r["flags"])

    print(f"\n[SUMMARY]")
    print(f"  Total listings:        {total}")
    print(f"  Wrong art (NN flag):   {wrong_art}")
    print(f"  No digital files:      {no_digital}")
    print(f"  Composite overflow:    {composite_cnt}")
    print(f"  Unmapped in dp_map:    {unmapped}")
    print(f"  No local art file:     {no_art_file}")
    print(f"  Direct hash matched:   {matched_direct}")
    print(f"  Needs review (any):    {needs_review}")

    # Sort: wrong art → no digital → composite → unmapped → rest
    def sort_key(r):
        if r["wrong_art_flag"]:              return 0
        if not r["digital_filenames"]:       return 1
        if r["composite_flag"]:              return 2
        if not r["dp_nums"]:                 return 3
        if r["dp_nums"] and not r["art_path"]: return 4
        return 5

    records.sort(key=sort_key)

    # ── Build HTML ─────────────────────────────────────────────────────────
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _nn_table(nearest: list) -> str:
        if not nearest:
            return ""
        rows = "".join(
            f'<tr><td>#{i+1}</td><td class="nn-dp">{_esc(dp)}</td><td>Δ{d}</td></tr>'
            for i, (d, dp) in enumerate(nearest)
        )
        return f'<table class="nn-table"><thead><tr><th>Rank</th><th>DP</th><th>Dist</th></tr></thead><tbody>{rows}</tbody></table>'

    cards = []
    for r in records:
        lid     = r["listing_id"]
        title   = r["title"]
        dp_lbl  = ", ".join(r["dp_nums"]) if r["dp_nums"] else "—"
        rstatus = r["review_status"]

        # Distance display
        d_txt = f"Δ{r['direct_distance']}/256" if r["direct_distance"] is not None else "N/A"
        nn_txt = ""
        if r["nn_rank_expected"] is not None:
            icon = "✓" if r["nn_rank_expected"] <= WRONG_ART_RANK_THRESHOLD else "⚠"
            nn_txt = f'<span class="nn-rank">NN rank #{r["nn_rank_expected"]} {icon}</span>'

        # Flags
        flags_html = ""
        if r["flags"]:
            items = "".join(f"<li>{_esc(f)}</li>" for f in r["flags"])
            flags_html = f'<ul class="flags">{items}</ul>'

        # Digital files
        if r["digital_filenames"]:
            file_items = "".join(
                f'<li>{_esc(fn)} <span class="fsize">{_esc(r["digital_filesizes"].get(fn,""))}</span></li>'
                for fn in r["digital_filenames"]
            )
            files_html = f'<ul class="file-list">{file_items}</ul>'
        else:
            files_html = '<p class="no-files">⚠ No digital files attached</p>'

        # Card border
        border = {
            "WRONG ART":    "#7c3aed",
            "NEEDS REVIEW": "#b45309",
            "UNMAPPED":     "#0e7490",
            "MISMATCH":     "#475569",
            "NO FILE":      "#374151",
            "MATCHED":      "#15803d",
            "NO PHOTO":     "#ea580c",
        }.get(rstatus, "#334155")

        comp_tag = '<span class="comp-flag">⚠ Overflow</span>' if r["composite_flag"] else ""

        card = f"""
<div class="card" data-status="{_esc(rstatus)}" data-flags="{1 if r['flags'] else 0}"
     style="border-left:5px solid {border}" id="lid-{lid}">
  <div class="card-header">
    <div class="card-meta">
      <span class="lid"><a href="https://www.etsy.com/listing/{lid}" target="_blank">#{lid}</a></span>
      <span class="dp-tag">DP: {_esc(dp_lbl)}</span>
      {badge(rstatus)}
      <span class="dist-tag">{_esc(d_txt)}</span>
      {nn_txt}
      {comp_tag}
    </div>
    <h3 class="card-title">{_esc(title)}</h3>
  </div>
  <div class="card-body">
    <div class="img-col">
      <div class="img-label">Live Photo #1</div>
      {img_tag(r["photo_b64"], "Listing photo")}
    </div>
    <div class="img-col">
      <div class="img-label">Our Art ({_esc(r["primary_dp"] or "—")})</div>
      {img_tag(r["art_b64"], "Art file")}
    </div>
    <div class="info-col">
      <div class="info-section">
        <strong>Top-5 nearest art matches (NN hash)</strong>
        {_nn_table(r["nearest"])}
      </div>
      <div class="info-section">
        <strong>Digital files attached</strong>
        {files_html}
      </div>
      {f'<div class="info-section"><strong>Flags</strong>{flags_html}</div>' if r["flags"] else ""}
    </div>
  </div>
</div>"""
        cards.append(card)

    all_cards = "\n".join(cards)

    # ── Summary bar ────────────────────────────────────────────────────────
    summary = f"""
<div class="summary-bar">
  <div class="pill p-total"><span class="n">{total}</span><span class="l">Total Listings</span></div>
  <div class="pill p-wrong"><span class="n">{wrong_art}</span><span class="l">Wrong Art (NN)</span></div>
  <div class="pill p-nodig"><span class="n">{no_digital}</span><span class="l">No Digital Files</span></div>
  <div class="pill p-comp"><span class="n">{composite_cnt}</span><span class="l">Composite Issues</span></div>
  <div class="pill p-unmap"><span class="n">{unmapped}</span><span class="l">Unmapped</span></div>
  <div class="pill p-noart"><span class="n">{no_art_file}</span><span class="l">Missing Art File</span></div>
  <div class="pill p-review"><span class="n">{needs_review}</span><span class="l">Needs Review</span></div>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OnBrandCraftz — Shop Audit — {generated_at}</title>
<style>
:root{{--bg:#0f172a;--card:#1e293b;--hdr:#1a2540;--text:#e2e8f0;--muted:#94a3b8;--bdr:#334155;font-size:14px}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,sans-serif;padding:24px;line-height:1.5}}
h1{{font-size:1.6rem;margin-bottom:4px}}
.sub{{color:var(--muted);font-size:.85rem;margin-bottom:20px}}
.note{{background:#1e3a5f;border:1px solid #1e40af;border-radius:8px;padding:12px 16px;margin-bottom:20px;font-size:.85rem;color:#93c5fd;line-height:1.6}}
.note strong{{color:#bfdbfe}}

/* Summary bar */
.summary-bar{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:24px}}
.pill{{border-radius:10px;padding:10px 20px;text-align:center;min-width:100px}}
.pill .n{{display:block;font-size:1.9rem;font-weight:700;line-height:1}}
.pill .l{{display:block;font-size:.72rem;color:rgba(255,255,255,.8);margin-top:3px}}
.p-total{{background:#1e293b;border:1px solid #334155}}
.p-wrong{{background:#581c87}}
.p-nodig{{background:#92400e}}
.p-comp{{background:#065f46}}
.p-unmap{{background:#164e63}}
.p-noart{{background:#374151}}
.p-review{{background:#78350f}}

/* Filters */
.filter-bar{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;align-items:center}}
.filter-bar label{{color:var(--muted);font-size:.83rem}}
#search{{background:var(--card);border:1px solid var(--bdr);color:var(--text);padding:6px 12px;border-radius:6px;font-size:.9rem;width:260px}}
.fb{{background:var(--card);border:1px solid var(--bdr);color:var(--text);padding:5px 14px;border-radius:6px;cursor:pointer;font-size:.83rem}}
.fb:hover{{background:#334155}}
.fb.on{{background:#1d4ed8;border-color:#1d4ed8;color:#fff}}

/* Cards */
.card{{background:var(--card);border-radius:10px;margin-bottom:14px;overflow:hidden;transition:box-shadow .15s}}
.card:hover{{box-shadow:0 4px 24px rgba(0,0,0,.5)}}
.card-header{{background:var(--hdr);padding:10px 14px;border-bottom:1px solid var(--bdr)}}
.card-meta{{display:flex;align-items:center;flex-wrap:wrap;gap:7px;margin-bottom:5px}}
.lid a{{color:#60a5fa;text-decoration:none;font-weight:700;font-size:.83rem}}
.lid a:hover{{text-decoration:underline}}
.dp-tag{{background:#1e3a5f;color:#93c5fd;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:600}}
.dist-tag{{background:#1f2937;color:var(--muted);padding:2px 7px;border-radius:4px;font-size:.75rem}}
.nn-rank{{background:#134e4a;color:#6ee7b7;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:600}}
.badge{{padding:2px 9px;border-radius:10px;font-size:.73rem;font-weight:700;letter-spacing:.04em}}
.comp-flag{{background:#78350f;color:#fcd34d;padding:2px 8px;border-radius:4px;font-size:.73rem}}
.card-title{{font-size:.92rem;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.card-body{{display:grid;grid-template-columns:1fr 1fr 1.2fr;gap:0}}
.img-col{{padding:12px;border-right:1px solid var(--bdr);display:flex;flex-direction:column;gap:7px}}
.info-col{{padding:12px;display:flex;flex-direction:column;gap:10px;overflow:hidden}}
.img-label{{font-size:.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
.no-img{{background:#1f2937;border:1px dashed #334155;border-radius:6px;padding:24px;text-align:center;color:var(--muted);font-size:.83rem}}
.info-section{{font-size:.83rem}}
.info-section strong{{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;display:block;margin-bottom:4px}}
/* NN table */
.nn-table{{width:100%;border-collapse:collapse;font-size:.78rem}}
.nn-table th,.nn-table td{{padding:2px 6px;border:1px solid var(--bdr);text-align:left}}
.nn-table th{{background:#0f172a;color:var(--muted)}}
.nn-dp{{font-family:monospace;color:#86efac}}
/* File list */
.file-list{{list-style:none;padding:0}}
.file-list li{{background:#0f172a;border-radius:4px;padding:3px 8px;margin-bottom:3px;font-family:monospace;font-size:.77rem;color:#86efac;word-break:break-all;display:flex;justify-content:space-between;gap:8px}}
.fsize{{color:#6b7280;font-size:.72rem;white-space:nowrap}}
.no-files{{color:#f87171;font-size:.83rem}}
.flags{{list-style:none;padding:0}}
.flags li{{background:#450a0a;border-radius:4px;padding:3px 8px;margin-bottom:3px;font-size:.8rem;color:#fca5a5;border-left:3px solid #ef4444;word-break:break-word}}
.hidden{{display:none!important}}
@media(max-width:900px){{.card-body{{grid-template-columns:1fr 1fr}}.info-col{{grid-column:1/-1;border-top:1px solid var(--bdr)}}}}
@media(max-width:580px){{.card-body{{grid-template-columns:1fr}}.img-col{{border-right:none;border-bottom:1px solid var(--bdr)}}}}
</style>
</head>
<body>
<h1>OnBrandCraftz — Shop Listing Audit</h1>
<p class="sub">Generated {generated_at} · {total} active listings · Shop {client.shop_id}</p>

<div class="note">
  <strong>How to read this report:</strong>
  Listing photos are lifestyle composites (room scenes), so direct hash distance will always be high (~80–145).
  The key metric is the <strong>NN (nearest-neighbour) rank</strong>: even as a composite, the correct art
  should rank in the top-3 closest matches against all {len(art_hashes)} art files.
  If it ranks <strong>#4 or higher</strong>, a different (possibly wrong) art was composited — flagged as
  <strong>WRONG ART</strong>.  Listings with <strong>no digital files attached</strong> mean the customer
  cannot download their purchase and need urgent attention.
</div>

{summary}

<div class="filter-bar">
  <label>Search:</label>
  <input id="search" placeholder="Filter by title, ID, DP…" oninput="applyFilters()">
  <button class="fb on"  onclick="setStatus('ALL')">All</button>
  <button class="fb"     onclick="setStatus('WRONG ART')">Wrong Art</button>
  <button class="fb"     onclick="setStatus('NEEDS REVIEW')">Needs Review</button>
  <button class="fb"     onclick="setStatus('UNMAPPED')">Unmapped</button>
  <button class="fb"     onclick="setStatus('MISMATCH')">Mismatch</button>
  <button class="fb"     onclick="setStatus('MATCHED')">Matched</button>
  <button class="fb"     onclick="setStatus('NO FILE')">No Art File</button>
  <button class="fb"     onclick="setStatus('FLAGS')">Has Flags</button>
</div>

<div id="cards">{all_cards}</div>

<p style="color:var(--muted);font-size:.78rem;text-align:center;margin-top:20px">
  OnBrandCraftz Shop Audit · {generated_at} · NN wrong-art threshold: rank &gt; {WRONG_ART_RANK_THRESHOLD}
</p>

<script>
let curStatus = 'ALL';
function applyFilters() {{
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.card').forEach(c => {{
    const txt = c.textContent.toLowerCase();
    const st  = c.dataset.status || '';
    const hasFlags = c.dataset.flags === '1';
    const okSearch = !q || txt.includes(q);
    const okStatus =
      curStatus === 'ALL' ||
      (curStatus === 'FLAGS' && hasFlags) ||
      st.toUpperCase() === curStatus;
    c.classList.toggle('hidden', !(okSearch && okStatus));
  }});
}}
function setStatus(s) {{
  curStatus = s;
  document.querySelectorAll('.fb').forEach(b => {{
    b.classList.toggle('on', b.textContent.trim() === s || (s==='ALL' && b.textContent.trim()==='All'));
  }});
  applyFilters();
}}
</script>
</body>
</html>"""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    size_mb = OUTPUT_PATH.stat().st_size / 1024 / 1024
    print(f"\n[DONE] {OUTPUT_PATH}  ({size_mb:.1f} MB)")

    return records


if __name__ == "__main__":
    run_audit()
