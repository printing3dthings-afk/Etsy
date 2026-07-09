#!/usr/bin/env python3
"""
Build a fully self-contained HTML review page with all images base64-embedded.
No internet connection needed to view — works from any local file on any device.
"""

import sys, json, time, base64, urllib.request, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient

REVIEW_LISTINGS = [
    (4513713984, "Hummingbird Nursery Print, Printable Wall Art"),
    (4513714013, "Paris Skyline Print, Black White Wall Art"),
    (4513714191, "Fox Nursery Wall Art, Printable Instant Download"),
    (4509193231, "Sage Lavender Botanical Print, Dusty Rose Wall Art"),
    (4509193237, "Pampas Grass Printable Wall Art, Boho"),
    (4509198434, "Boho Wildflower Printable Wall Art, Sage"),
    (4509198446, "Eucalyptus Branch Printable Wall Art, Botanical"),
    (4512768771, "Sunflower Watercolor Print, Botanical Wall Art"),
    (4512768858, "Cherry Blossom Watercolor Print, Spring Wall Art"),
    (4512770031, "Autumn Maple Printable Wall Art, Fall"),
    (4512772452, "Winter Birch Printable Wall Art"),
    (4512772539, "Sea Turtle Printable Wall Art, Ocean"),
    (4512774863, "Lighthouse Printable Wall Art, Coastal"),
    (4512776173, "Coral Reef Printable Wall Art, Ocean"),
    (4512780614, "Pelican Watercolor Print, Coastal Art"),
    (4513713514, "Japandi Tree Print, Black White Wall Art"),
    (4513713712, "Moon Phases Print, Black White Wall Art"),
    (4513713805, "Minimalist Botanical Print, Black White Wall Art"),
    (4513713922, "Bear Nursery Wall Art, Printable Instant Download"),
    (4513713936, "Owl Nursery Wall Art, Printable Instant Download"),
    (4513713945, "Vintage Botanical Print, Black White Wall Art"),
    (4513713962, "Watercolor Fox Nursery Print, Printable Instant Download"),
    (4515674042, "Minimalist Line Art Print | Modern Wall Decor"),
    (4515676301, "Floral Wreath Art Print | Botanical Wall Decor"),
]

def get_hero_url(client, lid):
    try:
        imgs = client.get_listing_images(lid)
        time.sleep(0.15)
        if not imgs:
            return None
        imgs_sorted = sorted(imgs, key=lambda i: i.get("rank", 99))
        hero = next((i for i in imgs_sorted if i.get("rank") == 1), imgs_sorted[0])
        return hero.get("url_570xN") or hero.get("url_fullxfull") or None
    except Exception as e:
        print(f"  WARN {lid}: {e}")
        return None

def download_as_base64(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.etsy.com/"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        return "data:image/jpeg;base64," + base64.b64encode(data).decode()
    except Exception as e:
        print(f"    download failed: {e}")
        return None

def main():
    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Token refreshed. Fetching and embedding photos...")

    rows = []
    for lid, title in REVIEW_LISTINGS:
        url = get_hero_url(client, lid)
        if url:
            print(f"  {lid}  downloading…  {title[:45]}")
            b64 = download_as_base64(url)
            if b64:
                print(f"         embedded ({len(b64)//1024}KB)")
            else:
                print(f"         embed FAILED — using URL fallback")
        else:
            b64 = None
            print(f"  {lid}  NO URL  {title[:45]}")
        rows.append({"lid": lid, "title": title, "url": url, "b64": b64})

    # Build HTML cards
    cards = ""
    for r in rows:
        lid   = r["lid"]
        title = r["title"]
        src   = r["b64"] or r["url"] or ""
        img_tag = (f'<img src="{src}" alt="{title}">'
                   if src else '<div class="no-img">Photo unavailable</div>')
        cards += f"""
        <div class="card" id="card-{lid}">
          <label class="cb-wrap">
            <input type="checkbox" id="cb-{lid}" onchange="mark('{lid}')">
            <span class="cb-label">NOT My Art — Flag for Removal</span>
          </label>
          {img_tag}
          <div class="meta">
            <span class="title">{title}</span>
            <span class="lid">ID: {lid}</span>
            <a class="etsy-link" href="https://www.etsy.com/listing/{lid}" target="_blank">View on Etsy ↗</a>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OnBrandCraftz — Art Ownership Review</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f5f4f1; color: #222; padding: 20px;
  }}
  h1 {{ font-size: 22px; margin-bottom: 6px; }}
  .subtitle {{ font-size: 14px; color: #555; margin-bottom: 24px; line-height: 1.5; }}
  .toolbar {{
    display: flex; gap: 12px; flex-wrap: wrap;
    margin-bottom: 24px; align-items: center;
  }}
  .toolbar button {{
    padding: 10px 18px; border: none; border-radius: 8px;
    cursor: pointer; font-size: 14px; font-weight: 700;
  }}
  #btn-export {{ background: #c0392b; color: #fff; }}
  #btn-clear  {{ background: #ddd; color: #333; }}
  #count-label {{ font-size: 14px; color: #555; font-weight: 600; }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
  }}
  .card {{
    background: #fff; border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    overflow: hidden;
    border: 3px solid transparent;
    transition: border-color 0.2s, box-shadow 0.2s;
  }}
  .card.flagged {{
    border-color: #e74c3c;
    box-shadow: 0 0 0 4px rgba(231,76,60,0.15);
  }}
  .cb-wrap {{
    display: flex; align-items: center; gap: 10px;
    padding: 12px 14px 8px; cursor: pointer;
  }}
  .cb-wrap input {{ width: 20px; height: 20px; cursor: pointer; accent-color: #e74c3c; flex-shrink: 0; }}
  .cb-label {{ font-size: 13px; font-weight: 700; color: #c0392b; line-height: 1.2; }}
  .card img {{ width: 100%; display: block; max-height: 280px; object-fit: cover; }}
  .no-img {{
    height: 180px; display: flex; align-items: center; justify-content: center;
    background: #eee; color: #999; font-size: 13px;
  }}
  .meta {{ padding: 10px 14px 14px; display: flex; flex-direction: column; gap: 4px; }}
  .title  {{ font-size: 13px; font-weight: 600; line-height: 1.4; }}
  .lid    {{ font-size: 11px; color: #aaa; }}
  .etsy-link {{ font-size: 12px; color: #e06c1a; text-decoration: none; margin-top: 4px; display: inline-block; }}
  .etsy-link:hover {{ text-decoration: underline; }}
  #export-box {{
    display: none; margin-top: 28px;
    background: #fff; border-radius: 12px;
    padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  #export-box h2 {{ font-size: 16px; margin-bottom: 12px; color: #c0392b; }}
  #export-box textarea {{
    width: 100%; height: 180px; font-family: monospace; font-size: 13px;
    padding: 10px; border: 1px solid #ddd; border-radius: 8px; resize: vertical;
  }}
  .copy-btn {{
    margin-top: 10px; padding: 8px 16px;
    background: #2c3e50; color: #fff; border: none;
    border-radius: 6px; cursor: pointer; font-size: 13px;
  }}
</style>
</head>
<body>
<h1>🎨 Art Ownership Review</h1>
<p class="subtitle">
  Check the box on any listing whose art is <strong>NOT yours</strong>.
  These {len(rows)} listings have no local art file — confirm each is art you created or own rights to.
</p>

<div class="toolbar">
  <button id="btn-export" onclick="exportFlagged()">Export Flagged List</button>
  <button id="btn-clear"  onclick="clearAll()">Clear All</button>
  <span id="count-label">0 of {len(rows)} flagged</span>
</div>

<div class="grid">{cards}
</div>

<div id="export-box">
  <h2>⚠ Flagged for Removal</h2>
  <textarea id="export-text" readonly></textarea>
  <button class="copy-btn" onclick="copyText()">Copy to Clipboard</button>
</div>

<script>
  const flagged = new Set();
  function mark(lid) {{
    const cb   = document.getElementById('cb-' + lid);
    const card = document.getElementById('card-' + lid);
    if (cb.checked) {{ flagged.add(lid); card.classList.add('flagged'); }}
    else            {{ flagged.delete(lid); card.classList.remove('flagged'); }}
    document.getElementById('count-label').textContent =
      flagged.size + ' of {len(rows)} flagged';
  }}
  function exportFlagged() {{
    if (!flagged.size) {{ alert('No listings flagged yet.'); return; }}
    const lines = Array.from(flagged).map(lid => {{
      const t = document.querySelector('#card-' + lid + ' .title').textContent;
      return lid + '  ' + t;
    }});
    document.getElementById('export-text').value = lines.join('\\n');
    const box = document.getElementById('export-box');
    box.style.display = 'block';
    box.scrollIntoView({{behavior:'smooth'}});
  }}
  function clearAll() {{
    flagged.clear();
    document.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = false);
    document.querySelectorAll('.card').forEach(c => c.classList.remove('flagged'));
    document.getElementById('count-label').textContent = '0 of {len(rows)} flagged';
    document.getElementById('export-box').style.display = 'none';
  }}
  function copyText() {{
    const t = document.getElementById('export-text');
    t.select(); document.execCommand('copy');
    alert('Copied!');
  }}
</script>
</body>
</html>"""

    out = Path(__file__).parent.parent / "art_review.html"
    out.write_text(html)
    size_kb = out.stat().st_size // 1024
    print(f"\nSaved: {out}  ({size_kb} KB)")

if __name__ == "__main__":
    main()
