#!/usr/bin/env python3
"""Build wrong_art_audit.html — visual comparison of listing photos vs attached files."""
import json, base64, os, sys
from pathlib import Path
from io import BytesIO

ROOT = Path("/home/user/Etsy")
UPSCALED = ROOT / "data" / "digital_products" / "product_files" / "upscaled"

def load_env(path):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env(ROOT / ".env")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

with open("/tmp/wrong_art_audit_full.json") as f:
    all_results = json.load(f)

with open(ROOT / "data" / "dp_listing_map.json") as f:
    dp_map = json.load(f)

def art_thumb_b64(dp_id):
    for ext in [".jpg", ".png"]:
        p = UPSCALED / f"{dp_id}{ext}"
        if p.exists() and HAS_PIL:
            try:
                img = Image.open(p).convert("RGB")
                img.thumbnail((120, 120))
                buf = BytesIO()
                img.save(buf, "JPEG", quality=75)
                return base64.b64encode(buf.getvalue()).decode()
            except:
                pass
    return None

mismatches = [r for r in all_results if r.get("art_mismatch")]
unmapped = [r for r in all_results if not r.get("expected_dp") and not r.get("art_mismatch")]
ok = [r for r in all_results if not r.get("art_mismatch") and r.get("expected_dp")]

print(f"Mismatches: {len(mismatches)}, Unmapped: {len(unmapped)}, OK: {len(ok)}")

art_thumbs = {}
all_dp_ids = set(dp_map.keys())
for r in all_results:
    for dp in [r.get("expected_dp"), r.get("best_photo_dp")] + r.get("attached_dps", []):
        if dp:
            all_dp_ids.add(dp)

for dp_id in sorted(all_dp_ids):
    b64 = art_thumb_b64(dp_id)
    if b64:
        art_thumbs[dp_id] = b64

print(f"Loaded {len(art_thumbs)} art thumbnails")


def dist_color(d):
    if d < 20:
        return "#27ae60"
    elif d < 60:
        return "#f39c12"
    else:
        return "#888888"


def top3_html(top3):
    parts = []
    for d, dp in (top3 or []):
        c = dist_color(d)
        parts.append(f'<div style="color:{c};font-size:11px">&nbsp;• {dp} (dist={d})</div>')
    return "".join(parts)


def render_card(r):
    lid = r["listing_id"]
    title = r.get("title", "")
    expected = r.get("expected_dp", "")
    best_photo = r.get("best_photo_dp", "")
    best_dist = r.get("best_photo_dist", 999)
    attached = r.get("attached_dps", [])
    attached_files = r.get("attached_files", [])
    mismatch_reason = r.get("mismatch_reason", "")
    photo_b64 = r.get("photo1_b64", "")
    top3 = r.get("top3_matches", [])

    if r.get("art_mismatch"):
        status = "MISMATCH"
        badge_color = "#e74c3c"
    elif not expected:
        status = "UNMAPPED"
        badge_color = "#f39c12"
    else:
        status = "OK"
        badge_color = "#27ae60"

    if photo_b64:
        photo_html = f'<img src="data:image/jpeg;base64,{photo_b64}" style="width:100%;max-width:200px;border-radius:4px;">'
    else:
        photo_html = '<div style="width:160px;height:160px;background:#333;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#888">No photo</div>'

    exp_thumb = art_thumbs.get(expected, "") if expected else ""
    if exp_thumb:
        exp_html = (f'<img src="data:image/jpeg;base64,{exp_thumb}" style="width:100%;max-width:200px;border-radius:4px;">'
                    f'<br><small style="color:#888">{expected}</small>')
    elif expected:
        exp_html = f'<div style="width:160px;height:120px;background:#333;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#aaa">{expected}<br>No art file</div>'
    else:
        exp_html = '<div style="width:160px;height:80px;background:#222;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#555;font-size:12px">Not mapped</div>'

    best_thumb = art_thumbs.get(best_photo, "") if best_photo else ""
    dc = dist_color(best_dist)
    if best_thumb:
        best_html = (f'<img src="data:image/jpeg;base64,{best_thumb}" style="width:100%;max-width:200px;border-radius:4px;">'
                     f'<br><small style="color:{dc}">{best_photo} dist={best_dist}</small>')
    elif best_photo:
        best_html = f'<div style="color:{dc};font-size:12px">{best_photo} (dist={best_dist})</div>'
    else:
        best_html = '<div style="color:#555;font-size:12px">no match</div>'

    att_parts = []
    for dp in attached:
        th = art_thumbs.get(dp, "")
        if th:
            att_parts.append(f'<img src="data:image/jpeg;base64,{th}" style="width:100%;max-width:180px;border-radius:4px;">'
                             f'<br><small style="color:#27ae60">{dp}</small>')
        else:
            att_parts.append(f'<div style="color:#888;font-size:12px">{dp}</div>')
    if not att_parts:
        att_parts.append('<div style="color:#e74c3c;font-size:12px;padding:8px">No files attached</div>')
    att_html = "<br>".join(att_parts)

    short_files = ", ".join(attached_files) or "none"
    if len(short_files) > 80:
        short_files = short_files[:80] + "..."

    return f"""
<div class="card" data-status="{status.lower()}" data-lid="{lid}">
  <div style="background:{badge_color}20;border-left:4px solid {badge_color};padding:8px 12px;display:flex;justify-content:space-between;align-items:center">
    <div>
      <span style="background:{badge_color};color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:bold">{status}</span>
      &nbsp;<strong style="color:#eee">{lid}</strong>
      &nbsp;<span style="color:#ccc;font-size:13px">{title[:70]}</span>
    </div>
    <a href="https://www.etsy.com/listing/{lid}" target="_blank" style="color:#5dade2;font-size:12px;white-space:nowrap">Etsy &#8599;</a>
  </div>
  <div style="display:flex;gap:16px;padding:12px;background:#1a1a2e;flex-wrap:wrap">
    <div style="text-align:center;flex:0 0 auto">
      <div style="color:#888;font-size:10px;margin-bottom:4px;text-transform:uppercase">Listing Photo #1</div>
      {photo_html}
    </div>
    <div style="text-align:center;flex:0 0 auto">
      <div style="color:#888;font-size:10px;margin-bottom:4px;text-transform:uppercase">Attached Download</div>
      {att_html}
    </div>
    <div style="text-align:center;flex:0 0 auto">
      <div style="color:#888;font-size:10px;margin-bottom:4px;text-transform:uppercase">dp_map Expected</div>
      {exp_html}
    </div>
    <div style="text-align:center;flex:0 0 auto">
      <div style="color:#888;font-size:10px;margin-bottom:4px;text-transform:uppercase">Photo Nearest Match</div>
      {best_html}
    </div>
    <div style="flex:1;min-width:180px;font-size:12px;color:#ccc">
      <div style="color:#888;font-size:10px;text-transform:uppercase;margin-bottom:4px">Details</div>
      <div>Files: {short_files}</div>
      <div style="color:{badge_color};margin-top:4px">{mismatch_reason or 'OK'}</div>
      <div style="margin-top:6px;color:#666;font-size:10px">Top photo matches:</div>
      {top3_html(top3)}
    </div>
  </div>
</div>"""


mismatch_cards = "\n".join(render_card(r) for r in mismatches)
unmapped_cards = "\n".join(render_card(r) for r in unmapped)

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shop Audit — Wrong Art</title>
<style>
body{{background:#0f0f1a;color:#ddd;font-family:system-ui,sans-serif;margin:0;padding:0}}
.header{{background:#1a1a2e;padding:20px;border-bottom:2px solid #333}}
h1{{margin:0 0 4px 0;color:#fff;font-size:22px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}}
.stat{{background:#0f0f1a;border:1px solid #333;border-radius:6px;padding:8px 14px;text-align:center}}
.stat .n{{font-size:26px;font-weight:bold}}
.stat .l{{font-size:10px;color:#888;text-transform:uppercase}}
.tabs{{display:flex;gap:0;background:#1a1a2e;border-bottom:1px solid #333;padding:0 16px}}
.tab{{padding:12px 18px;cursor:pointer;border-bottom:3px solid transparent;font-size:13px;color:#888}}
.tab.active{{color:#5dade2;border-bottom-color:#5dade2}}
.tab-content{{display:none;padding:12px}}
.tab-content.active{{display:block}}
.card{{background:#16213e;border:1px solid #333;border-radius:8px;margin-bottom:10px;overflow:hidden}}
.search{{padding:10px;background:#1a1a2e;position:sticky;top:0;z-index:10;border-bottom:1px solid #333}}
.search input{{width:300px;padding:7px 12px;background:#0f0f1a;border:1px solid #444;color:#ddd;border-radius:4px;font-size:13px}}
.sec-note{{padding:10px 14px;background:#1a1a2e;font-size:12px;color:#888;border-bottom:1px solid #333;margin-bottom:8px}}
</style>
</head>
<body>
<div class="header">
  <h1>Shop Audit — Art &amp; File Mismatches</h1>
  <div style="color:#888;font-size:13px">OnBrandCraftz &middot; {len(all_results)} digital listings</div>
  <div class="stats">
    <div class="stat"><div class="n" style="color:#e74c3c">{len(mismatches)}</div><div class="l">Mismatches</div></div>
    <div class="stat"><div class="n" style="color:#f39c12">{len(unmapped)}</div><div class="l">Unmapped</div></div>
    <div class="stat"><div class="n" style="color:#27ae60">{len(ok)}</div><div class="l">OK</div></div>
    <div class="stat"><div class="n" style="color:#5dade2">{len(all_results)}</div><div class="l">Total</div></div>
  </div>
</div>
<div class="tabs">
  <div class="tab active" onclick="showTab('mis',this)">Mismatches ({len(mismatches)})</div>
  <div class="tab" onclick="showTab('unm',this)">Unmapped ({len(unmapped)})</div>
  <div class="tab" onclick="showTab('ok2',this)">OK ({len(ok)})</div>
</div>
<div id="mis" class="tab-content active">
  <div class="search"><input type="text" placeholder="Search ID or title..." oninput="filterCards('mis',this.value)"></div>
  <div class="sec-note">
    ⚠️ {len(mismatches)} listings where the attached download file doesn't match the expected art (or photo looks like a different file).
    Customers downloading these may get the wrong art. Fix priority: HIGH.
  </div>
  {mismatch_cards}
</div>
<div id="unm" class="tab-content">
  <div class="search"><input type="text" placeholder="Search..." oninput="filterCards('unm',this.value)"></div>
  <div class="sec-note">
    &#128269; {len(unmapped)} listings not in dp_listing_map.json. Review attached files to verify correctness.
  </div>
  {unmapped_cards}
</div>
<div id="ok2" class="tab-content">
  <div class="sec-note">&#10003; {len(ok)} listings mapped and verified OK.</div>
  <div style="padding:12px;font-family:monospace;font-size:12px;color:#888;line-height:1.8">
    {"<br>".join([f"{r['listing_id']} ({r.get('expected_dp','')}) — {r['title'][:60]}" for r in ok])}
  </div>
</div>
<script>
function showTab(id,el){{
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  el.classList.add('active');
}}
function filterCards(tabId,query){{
  var q=query.toLowerCase();
  document.querySelectorAll('#'+tabId+' .card').forEach(function(card){{
    card.style.display=card.textContent.toLowerCase().includes(q)?'':'none';
  }});
}}
</script>
</body>
</html>"""

out_path = ROOT / "review_batches" / "wrong_art_audit.html"
out_path.write_text(html, encoding="utf-8")
size_mb = out_path.stat().st_size / 1024 / 1024
print(f"Saved {out_path} ({size_mb:.1f} MB)")
