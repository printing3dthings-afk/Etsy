#!/usr/bin/env python3
"""
Build batch HTML review files for ALL active Etsy listings.
10 listings per batch, all current photos shown per listing.
Photos are base64-embedded so files work offline / on any device.
Also initialises data/fix_queue.json for tracking flagged listings.
"""

import sys, json, time, base64, io, math, urllib.request
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient

REPO       = Path(__file__).parent.parent
OUT_DIR    = REPO / "review_batches"
FIX_QUEUE  = REPO / "data" / "fix_queue.json"
BATCH_SIZE = 10
MAX_PX     = 420    # max photo dimension before re-encode
QUALITY    = 72     # JPEG quality for embedded photos

OUT_DIR.mkdir(exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def download_and_compress(url: str) -> str | None:
    """Download photo, resize to MAX_PX, return base64 data URI."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer":    "https://www.etsy.com/"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = img.size
        if max(w, h) > MAX_PX:
            scale = MAX_PX / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=QUALITY, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return "data:image/jpeg;base64," + b64
    except Exception as e:
        print(f"      download failed: {e}")
        return None


def get_listing_photos(client, lid: int) -> list:
    """Return list of {rank, data_uri} for all photos on a listing."""
    try:
        imgs = client.get_listing_images(lid)
        time.sleep(0.12)
        return sorted(imgs, key=lambda i: i.get("rank", 99))
    except Exception as e:
        print(f"  WARN {lid} get_images: {e}")
        return []


# ── HTML generator ────────────────────────────────────────────────────────────

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f2f1ee; color: #1a1a1a; padding: 16px;
}
h1 { font-size: 19px; margin-bottom: 4px; }
.subtitle { font-size: 13px; color: #666; margin-bottom: 20px; }
.toolbar {
  position: sticky; top: 0; z-index: 10;
  background: #f2f1ee; padding: 10px 0 12px;
  display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
  border-bottom: 1px solid #ddd; margin-bottom: 20px;
}
.toolbar button {
  padding: 9px 16px; border: none; border-radius: 8px;
  cursor: pointer; font-size: 14px; font-weight: 700;
}
#btn-export { background: #c0392b; color: #fff; }
#btn-clear  { background: #ddd;    color: #333; }
#count-lbl  { font-size: 13px; color: #555; font-weight: 600; }
.listing {
  background: #fff; border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.07);
  margin-bottom: 20px; overflow: hidden;
  border: 3px solid transparent;
  transition: border-color 0.2s;
}
.listing.flagged { border-color: #e74c3c; }
.listing-header {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px 14px 10px; border-bottom: 1px solid #eee;
  cursor: pointer;
}
.listing-header input[type=checkbox] {
  width: 22px; height: 22px; flex-shrink: 0;
  margin-top: 2px; cursor: pointer; accent-color: #e74c3c;
}
.listing-info { flex: 1; min-width: 0; }
.listing-title { font-size: 14px; font-weight: 700; line-height: 1.35; }
.listing-meta  { font-size: 11px; color: #999; margin-top: 3px; }
.etsy-link {
  display: inline-block; margin-top: 5px;
  font-size: 12px; color: #e06c1a; text-decoration: none;
}
.photos {
  display: flex; gap: 8px; padding: 10px 12px;
  overflow-x: auto; -webkit-overflow-scrolling: touch;
}
.photo-wrap { flex-shrink: 0; text-align: center; }
.photo-wrap img {
  display: block; border-radius: 6px;
  max-height: 200px; width: auto;
  border: 1px solid #eee;
}
.rank-label {
  font-size: 10px; color: #aaa; margin-top: 3px;
}
.no-photo {
  width: 140px; height: 140px; background: #f5f5f5;
  border-radius: 6px; display: flex; align-items: center;
  justify-content: center; color: #bbb; font-size: 12px;
}
#export-box {
  display: none; margin-top: 24px; background: #fff;
  border-radius: 12px; padding: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
#export-box h2 { font-size: 15px; margin-bottom: 10px; color: #c0392b; }
#export-box textarea {
  width: 100%; height: 160px; font-family: monospace;
  font-size: 12px; padding: 10px;
  border: 1px solid #ddd; border-radius: 8px; resize: vertical;
}
.copy-btn {
  margin-top: 8px; padding: 8px 16px;
  background: #2c3e50; color: #fff; border: none;
  border-radius: 6px; cursor: pointer; font-size: 13px;
}
"""

JS = """
const flagged = new Set();
function toggle(lid) {
  const cb   = document.getElementById('cb-' + lid);
  const card = document.getElementById('lst-' + lid);
  if (cb.checked) { flagged.add(String(lid)); card.classList.add('flagged'); }
  else            { flagged.delete(String(lid)); card.classList.remove('flagged'); }
  document.getElementById('count-lbl').textContent =
    flagged.size + ' flagged';
}
function exportFlagged() {
  if (!flagged.size) { alert('Nothing flagged yet.'); return; }
  const lines = Array.from(flagged).map(lid => {
    const t = document.querySelector('#lst-' + lid + ' .listing-title').textContent;
    return lid + '  ' + t;
  });
  document.getElementById('export-text').value = lines.join('\\n');
  const box = document.getElementById('export-box');
  box.style.display = 'block';
  box.scrollIntoView({behavior:'smooth'});
}
function clearAll() {
  flagged.clear();
  document.querySelectorAll('input[type=checkbox]').forEach(c => c.checked = false);
  document.querySelectorAll('.listing').forEach(c => c.classList.remove('flagged'));
  document.getElementById('count-lbl').textContent = '0 flagged';
  document.getElementById('export-box').style.display = 'none';
}
function copyText() {
  const t = document.getElementById('export-text');
  t.select(); document.execCommand('copy'); alert('Copied!');
}
"""

def build_batch_html(batch_listings, batch_num, total_batches, photo_map):
    n = len(batch_listings)
    cards = ""
    for l in batch_listings:
        lid   = l["listing_id"]
        title = l["title"]
        price = l.get("price", {}).get("amount", 0) / max(l.get("price", {}).get("divisor", 100), 1)
        state = l.get("state", "active")

        photos = photo_map.get(lid, [])
        photo_html = ""
        if photos:
            for p in photos:
                rank = p.get("rank", "?")
                uri  = p.get("data_uri", "")
                if uri:
                    photo_html += f"""
              <div class="photo-wrap">
                <img src="{uri}" alt="rank {rank}">
                <div class="rank-label">Photo {rank}</div>
              </div>"""
                else:
                    photo_html += f"""
              <div class="photo-wrap">
                <div class="no-photo">No image</div>
                <div class="rank-label">Photo {rank}</div>
              </div>"""
        else:
            photo_html = '<div class="no-photo" style="margin:8px 12px">No photos found</div>'

        cards += f"""
    <div class="listing" id="lst-{lid}">
      <div class="listing-header" onclick="document.getElementById('cb-{lid}').click();toggle({lid})">
        <input type="checkbox" id="cb-{lid}" onclick="event.stopPropagation()"
               onchange="toggle({lid})">
        <div class="listing-info">
          <div class="listing-title">{title[:80]}</div>
          <div class="listing-meta">ID: {lid} &nbsp;·&nbsp; ${price:.2f} &nbsp;·&nbsp; {len(photos)} photos</div>
          <a class="etsy-link" href="https://www.etsy.com/listing/{lid}"
             target="_blank" onclick="event.stopPropagation()">View on Etsy ↗</a>
        </div>
      </div>
      <div class="photos">{photo_html}
      </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Batch {batch_num}/{total_batches} — OnBrandCraftz Review</title>
<style>{CSS}</style>
</head>
<body>
<h1>📋 Batch {batch_num} of {total_batches}</h1>
<p class="subtitle">{n} listings — tap a card or its checkbox to flag for fixing.</p>

<div class="toolbar">
  <button id="btn-export" onclick="exportFlagged()">Export Flagged</button>
  <button id="btn-clear"  onclick="clearAll()">Clear All</button>
  <span id="count-lbl">0 flagged</span>
</div>

{cards}

<div id="export-box">
  <h2>⚠ Flagged listings — paste these back to Claude</h2>
  <textarea id="export-text" readonly></textarea>
  <button class="copy-btn" onclick="copyText()">Copy to Clipboard</button>
</div>

<script>{JS}</script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Token refreshed.\n")

    print("Fetching all active listings…")
    all_listings = client.get_shop_listings_all(state="active", limit=100)
    all_listings.sort(key=lambda l: l["listing_id"])
    total = len(all_listings)
    print(f"  {total} active listings found\n")

    # ── Download all photos ───────────────────────────────────────────────────
    photo_map = {}  # lid -> [{rank, data_uri}]
    for idx, l in enumerate(all_listings, 1):
        lid   = l["listing_id"]
        title = l["title"][:55]
        print(f"  [{idx:3}/{total}]  {lid}  {title}")

        imgs = get_listing_photos(client, lid)
        embedded = []
        for img in imgs:
            rank = img.get("rank", 0)
            url  = img.get("url_570xN") or img.get("url_fullxfull") or ""
            uri  = download_and_compress(url) if url else None
            embedded.append({"rank": rank, "data_uri": uri})
            if uri:
                print(f"      rank {rank}  {len(uri)//1024}KB")
        photo_map[lid] = embedded

    # ── Split into batches and write HTML ─────────────────────────────────────
    batches = [all_listings[i:i+BATCH_SIZE]
               for i in range(0, total, BATCH_SIZE)]
    total_batches = len(batches)

    print(f"\nWriting {total_batches} batch files…")
    batch_files = []
    for bn, batch in enumerate(batches, 1):
        html = build_batch_html(batch, bn, total_batches, photo_map)
        fname = OUT_DIR / f"batch_{bn:02d}_of_{total_batches:02d}.html"
        fname.write_text(html)
        size_kb = fname.stat().st_size // 1024
        titles  = [l["title"][:40] for l in batch]
        print(f"  Batch {bn:2}: {size_kb} KB  ({len(batch)} listings)")
        batch_files.append({
            "batch": bn,
            "file":  str(fname),
            "size_kb": size_kb,
            "listing_ids": [l["listing_id"] for l in batch],
        })

    # ── Initialise fix_queue.json ─────────────────────────────────────────────
    if FIX_QUEUE.exists():
        queue = json.loads(FIX_QUEUE.read_text())
    else:
        queue = {"flagged": [], "reviewed_batches": []}

    FIX_QUEUE.write_text(json.dumps(queue, indent=2))
    print(f"\nfix_queue.json ready at {FIX_QUEUE}")

    print("\n" + "=" * 60)
    print(f"Done.  {total_batches} batch files in {OUT_DIR}/")
    print("=" * 60)
    for b in batch_files:
        ids = b["listing_ids"]
        print(f"  batch_{b['batch']:02d}  {b['size_kb']} KB  IDs {ids[0]}…{ids[-1]}")


if __name__ == "__main__":
    main()
