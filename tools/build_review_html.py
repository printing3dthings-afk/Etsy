#!/usr/bin/env python3
"""
Build an HTML review page for all CDN-art listings that need manual ownership
confirmation. Each listing shows its hero photo + title + checkbox.
"""

import sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient

# 24 CDN listings needing manual review (rank-2 and rank-6+ art sources)
REVIEW_LISTINGS = [
    # rank-2 CDN
    (4513713984, "Hummingbird Nursery Print, Printable Wall Art"),
    (4513714013, "Paris Skyline Print, Black White Wall Art"),
    (4513714191, "Fox Nursery Wall Art, Printable Instant Download"),
    # rank-6+ CDN
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
        # rank 1 first, fallback to lowest rank
        imgs_sorted = sorted(imgs, key=lambda i: i.get("rank", 99))
        hero = next((i for i in imgs_sorted if i.get("rank") == 1), imgs_sorted[0])
        return hero.get("url_570xN") or hero.get("url_fullxfull") or None
    except Exception as e:
        print(f"  WARN {lid}: {e}")
        return None

def main():
    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Token refreshed. Fetching hero photos...")

    rows = []
    for lid, title in REVIEW_LISTINGS:
        url = get_hero_url(client, lid)
        print(f"  {lid}  {'OK' if url else 'MISSING'}  {title[:50]}")
        rows.append({"lid": lid, "title": title, "url": url})

    # Build HTML
    cards = ""
    for i, r in enumerate(rows):
        lid   = r["lid"]
        title = r["title"]
        url   = r["url"] or ""
        img_tag = (f'<img src="{url}" alt="{title}" loading="lazy">'
                   if url else '<div class="no-img">No photo found</div>')
        cards += f"""
        <div class="card" id="card-{lid}">
          <label class="cb-wrap">
            <input type="checkbox" id="cb-{lid}" onchange="mark('{lid}')">
            <span class="cb-label">Mark as INCORRECT / Not My Art</span>
          </label>
          {img_tag}
          <div class="meta">
            <span class="title">{title}</span>
            <span class="lid">Listing ID: {lid}</span>
            <a class="etsy-link" href="https://www.etsy.com/listing/{lid}" target="_blank">
              View on Etsy ↗
            </a>
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
    background: #f5f4f1;
    color: #222;
    padding: 24px;
  }}
  h1 {{ font-size: 22px; margin-bottom: 6px; }}
  .subtitle {{ font-size: 14px; color: #666; margin-bottom: 28px; }}
  .toolbar {{
    display: flex; gap: 12px; flex-wrap: wrap;
    margin-bottom: 24px; align-items: center;
  }}
  .toolbar button {{
    padding: 8px 16px; border: none; border-radius: 6px;
    cursor: pointer; font-size: 14px; font-weight: 600;
  }}
  #btn-export {{ background: #c0392b; color: #fff; }}
  #btn-clear  {{ background: #ddd; color: #333; }}
  #count-label {{ font-size: 14px; color: #555; }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 20px;
  }}
  .card {{
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    overflow: hidden;
    transition: box-shadow 0.2s, border 0.2s;
    border: 3px solid transparent;
  }}
  .card.flagged {{
    border-color: #e74c3c;
    box-shadow: 0 2px 16px rgba(231,76,60,0.25);
  }}
  .cb-wrap {{
    display: flex; align-items: center; gap: 10px;
    padding: 12px 14px 8px;
    cursor: pointer;
  }}
  .cb-wrap input {{ width: 18px; height: 18px; cursor: pointer; accent-color: #e74c3c; }}
  .cb-label {{ font-size: 13px; font-weight: 600; color: #c0392b; }}
  .card img {{
    width: 100%; display: block;
    max-height: 260px; object-fit: cover;
  }}
  .no-img {{
    height: 180px; display: flex; align-items: center; justify-content: center;
    background: #eee; color: #999; font-size: 13px;
  }}
  .meta {{
    padding: 10px 14px 14px;
    display: flex; flex-direction: column; gap: 4px;
  }}
  .title  {{ font-size: 13px; font-weight: 600; line-height: 1.35; }}
  .lid    {{ font-size: 11px; color: #999; }}
  .etsy-link {{
    font-size: 12px; color: #e06c1a; text-decoration: none; margin-top: 4px;
  }}
  .etsy-link:hover {{ text-decoration: underline; }}
  #export-box {{
    display: none; margin-top: 28px;
    background: #fff; border-radius: 10px;
    padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  #export-box h2 {{ font-size: 16px; margin-bottom: 12px; }}
  #export-box textarea {{
    width: 100%; height: 160px; font-family: monospace; font-size: 13px;
    padding: 10px; border: 1px solid #ccc; border-radius: 6px; resize: vertical;
  }}
</style>
</head>
<body>
<h1>🎨 OnBrandCraftz — Art Ownership Review</h1>
<p class="subtitle">
  Check any listing whose art is <strong>NOT yours</strong>. These {len(rows)} listings
  have no local art file on disk — their photos were sourced from their own Etsy CDN images.
  Confirm each one is art you created or licensed.
</p>

<div class="toolbar">
  <button id="btn-export" onclick="exportFlagged()">Export Flagged List</button>
  <button id="btn-clear"  onclick="clearAll()">Clear All</button>
  <span id="count-label">0 flagged</span>
</div>

<div class="grid">{cards}
</div>

<div id="export-box">
  <h2>Flagged listings (copy this list):</h2>
  <textarea id="export-text" readonly></textarea>
</div>

<script>
  const flagged = new Set();

  function mark(lid) {{
    const cb   = document.getElementById('cb-' + lid);
    const card = document.getElementById('card-' + lid);
    if (cb.checked) {{
      flagged.add(lid);
      card.classList.add('flagged');
    }} else {{
      flagged.delete(lid);
      card.classList.remove('flagged');
    }}
    document.getElementById('count-label').textContent =
      flagged.size + ' flagged';
  }}

  function exportFlagged() {{
    const box = document.getElementById('export-box');
    const txt = document.getElementById('export-text');
    if (flagged.size === 0) {{
      alert('No listings flagged yet.');
      return;
    }}
    const lines = Array.from(flagged).map(lid => {{
      const title = document.querySelector('#card-' + lid + ' .title').textContent;
      return lid + '  ' + title;
    }});
    txt.value = lines.join('\\n');
    box.style.display = 'block';
    txt.select();
  }}

  function clearAll() {{
    flagged.clear();
    document.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = false);
    document.querySelectorAll('.card').forEach(c => c.classList.remove('flagged'));
    document.getElementById('count-label').textContent = '0 flagged';
    document.getElementById('export-box').style.display = 'none';
  }}
</script>
</body>
</html>"""

    out = Path(__file__).parent.parent / "art_review.html"
    out.write_text(html)
    print(f"\nSaved: {out}")
    print(f"Open it in a browser: file://{out}")

if __name__ == "__main__":
    main()
