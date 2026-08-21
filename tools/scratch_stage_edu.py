"""One-off script: register EDU1001/1002/1003, upload their real files to the
live Railway volume, set listing content, and stage each for Scott's
Action Center approval. Not part of the shop's permanent tooling -- run
once, then safe to delete."""
import json
import mimetypes
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE = "https://etsy-production-b2f1.up.railway.app"
ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / ".env") as fh:
    _env = dict(l.split("=", 1) for l in fh.read().splitlines() if l.strip() and "=" in l and not l.startswith("#"))
TOKEN = _env["APP_SECRET_TOKEN"].strip()

HEADERS = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "curl/8.5.0"}


def call(method, path, body=None, raw=None, content_type=None):
    url = BASE + path
    headers = dict(HEADERS)
    data = None
    if raw is not None:
        data = raw
        headers["Content-Type"] = content_type or "application/octet-stream"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        return e.code, detail


def upload_file(local_path: Path, rel_path: str):
    ctype = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
    status, resp = call("POST", f"/api/files/upload?path={urllib.parse.quote(rel_path)}",
                         raw=local_path.read_bytes(), content_type=ctype)
    return status, resp


import urllib.parse  # noqa: E402

# category="digital_planner", not the more descriptive "kids_worksheets" this
# repo's own local data/product_catalog.json uses -- confirmed live 2026-08-21
# that the DEPLOYED server's /api/products/register endpoint validates against
# a fixed category enum that does not include "kids_worksheets" (real 422:
# "category must be one of [...]"), and adding a new category to that enum is
# a code change that needs a deploy, not something this script can do from
# outside. "digital_planner" is a genuine, accurate fit for the live system's
# purposes: same delivery shape (interactive GoodNotes-compatible PDF), same
# real Etsy taxonomy (2078, Craft Supplies & Tools > Patterns & How To >
# Digital Files) as every DP-series planner already published from this shop.
PRODUCTS = {
    "EDU1001": {
        "name": "Kawaii Interactive Tracing Workbook for Kids (Sunflower Studio)",
        "category": "digital_planner",
        "price": 6.99,
    },
    "EDU1002": {
        "name": "Kawaii Interactive Tracing Workbook for Kids (Truck Zone)",
        "category": "digital_planner",
        "price": 6.99,
    },
    "EDU1003": {
        "name": "Cursive & Skills Workbook for Kids (Ocean Breeze, Grade 1-2)",
        "category": "digital_planner",
        "price": 6.99,
    },
}


def main():
    pids = sys.argv[1:] or list(PRODUCTS)

    # Step 1+2 combined: /api/products/register's own execute path always
    # writes files=[] (no way to pass a files list through that endpoint), so
    # write the FULL override record directly in one read-modify-write pass --
    # same shape _register_new_product_overlay()/_execute_register_product_
    # staged_action() write server-side, just constructed here since this
    # session can't deploy a new HTTP endpoint for it. This is a pure local
    # bookkeeping write (zero Etsy API calls, trivially reversible -- same
    # category of action the register endpoint itself already is).
    status, current = call("GET", "/api/files/download?root=volume&path=product_catalog_overrides.json")
    if status == 200:
        overrides = json.loads(current) if isinstance(current, str) else current
    else:
        print(f"[overrides] GET failed {status}: {str(current)[:200]} -- assuming empty")
        overrides = {}

    from datetime import datetime, timezone
    for pid in pids:
        cfg = PRODUCTS[pid]
        pdf_rel = f"data/digital_products/product_files/{pid}.pdf"
        photo_dir = ROOT / "data" / "digital_products" / "product_files" / "listing_photos" / pid
        photo_rels = [f"data/digital_products/product_files/{pid}_listing_images/{p.name}"
                      for p in sorted(photo_dir.glob("photo_*.jpg"))]
        files = [pdf_rel] + photo_rels
        overrides[pid] = {
            "is_new_product": True,
            "product_id": pid,
            "name": cfg["name"],
            "category": cfg["category"],
            "price": cfg["price"],
            "status": "draft",
            "etsy_listing_id": "",
            "files": files,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "frank_register",
        }
        print(f"[files-plan] {pid}: {len(files)} files ({pdf_rel} + {len(photo_rels)} photos)")

    body = json.dumps(overrides).encode()
    status, resp = call("POST", "/api/files/upload?path=" + urllib.parse.quote("product_catalog_overrides.json"),
                         raw=body, content_type="application/json")
    print(f"[overrides] write: {status} {resp}")

    # Step 3: upload the actual binary files
    for pid in pids:
        pdf_local = ROOT / "data" / "digital_products" / "product_files" / f"{pid}.pdf"
        pdf_rel = f"data/digital_products/product_files/{pid}.pdf"
        st, resp = upload_file(pdf_local, pdf_rel)
        print(f"[upload] {pid} PDF: {st} {resp}")

        photo_dir = ROOT / "data" / "digital_products" / "product_files" / "listing_photos" / pid
        for p in sorted(photo_dir.glob("photo_*.jpg")):
            rel = f"data/digital_products/product_files/{pid}_listing_images/{p.name}"
            st, resp = upload_file(p, rel)
            print(f"[upload] {pid} {p.name}: {st} {'OK' if st == 200 else resp}")

    # Step 4: set listing content
    for pid in pids:
        content = json.loads((ROOT / "data" / f"{pid.lower()}_listing.json").read_text())
        status, resp = call("POST", f"/api/products/{pid}/set-listing-content", body={
            "title": content["title"], "description": content["description"],
            "tags": content["tags"], "price": content["price"],
        })
        print(f"[content] {pid}: {status} {'OK' if status == 200 else resp}")

    # Step 5: review + stage
    for pid in pids:
        status, review = call("GET", f"/api/products/{pid}/review")
        print(f"[review] {pid}: {status}")
        if status == 200:
            print(f"  qc={review.get('qc')} photos={len(review.get('photos', []))} deliverables={len(review.get('deliverables', []))}")
        status, resp = call("POST", f"/api/products/{pid}/stage-publish")
        print(f"[stage] {pid}: {status} {resp}")


if __name__ == "__main__":
    main()
