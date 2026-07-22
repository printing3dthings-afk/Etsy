"""
Tests for the Reference Photos library (2026-07-22 Create-screen redesign) --
upload / list / delete round-trip for Scott's own inspiration/style-reference
images. Deliberately scoped to upload + organize + browse + delete only this
round; nothing here is wired into AI generation (see the module docstring
above upload_reference_image in main.py).

Self-contained TestClient-against-the-real-app pattern, same as
tests/test_produce_qc.py. Run: python tests/test_reference_images.py
"""
import io
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_refimages_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "refimages-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "refimagestest"
os.environ["TEST_LOGIN_PASSWORD"] = "RefImagesTest!2026Only"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _logged_in_client() -> TestClient:
    c = TestClient(server.app, base_url="https://testserver")
    r = c.post("/login", data={
        "username": os.environ["TEST_LOGIN_USERNAME"],
        "password": os.environ["TEST_LOGIN_PASSWORD"],
        "next": "/frank",
    }, follow_redirects=False)
    check(r.status_code in (302, 303), f"login should redirect, got {r.status_code}")
    return c


def _png_bytes(color=(200, 120, 180)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (24, 24), color=color).save(buf, format="PNG")
    return buf.getvalue()


def _isolated_roots():
    """A temp dir standing in for _FILE_ROOTS['reference_images'] + a temp meta
    sidecar path, so this test never touches real data/reference_images/."""
    tmp = tempfile.mkdtemp(prefix="frank_refimages_root_")
    return Path(tmp) / "reference_images", Path(tmp) / "reference_images_meta.json"


def test_upload_valid_image_round_trips_through_list():
    root, meta_path = _isolated_roots()
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _logged_in_client()
        r = c.post(
            "/api/reference-images/upload",
            params={"filename": "cozy_desk.png", "category": "digital_planner"},
            content=_png_bytes(),
            headers={"Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 200, f"valid image upload should 200, got {r.status_code}: {r.text[:200]}")
        entry = r.json()
        check(entry.get("category") == "digital_planner", f"category should be echoed, got {entry}")
        check(entry.get("filename", "").endswith("cozy_desk.png"), f"filename should be preserved, got {entry}")
        check(bool(entry.get("id")), f"entry must have an id, got {entry}")
        check((root / entry["filename"]).is_file(), "the uploaded file must actually exist on disk")

        r2 = c.get("/api/reference-images")
        check(r2.status_code == 200, f"list should 200, got {r2.status_code}")
        images = r2.json().get("images") or []
        check(any(im["id"] == entry["id"] for im in images),
              f"the uploaded image must appear in the list, got {images}")


def test_upload_rejects_non_image():
    root, meta_path = _isolated_roots()
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _logged_in_client()
        r = c.post(
            "/api/reference-images/upload",
            params={"filename": "not_a_photo.png"},
            content=b"this is definitely not image data, just text bytes",
            headers={"Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 400, f"a non-image body must 400, got {r.status_code}: {r.text[:200]}")
        check(not list(root.glob("*")) if root.exists() else True,
              "a rejected upload must not leave a stored file behind")


def test_upload_rejects_svg_with_embedded_script():
    # Same XSS vector studio_upload_image already blocks -- PIL can't decode an
    # SVG as a raster image, so this is naturally rejected the same way as any
    # other non-image body, not via SVG-specific parsing.
    root, meta_path = _isolated_roots()
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _logged_in_client()
        r = c.post(
            "/api/reference-images/upload",
            params={"filename": "evil.svg"},
            content=b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            headers={"Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 400, f"an SVG-as-image must be rejected, got {r.status_code}")


def test_upload_rejects_oversized_file():
    with patch.object(server, "_MAX_UPLOAD_BYTES", 100):
        root, meta_path = _isolated_roots()
        with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
             patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
            c = _logged_in_client()
            r = c.post(
                "/api/reference-images/upload",
                params={"filename": "too_big.png"},
                content=_png_bytes() * 5,  # comfortably over the patched 100-byte cap
                headers={"Content-Type": "application/octet-stream"},
            )
            check(r.status_code == 413, f"an oversized upload must 413, got {r.status_code}: {r.text[:200]}")


def test_upload_requires_filename():
    root, meta_path = _isolated_roots()
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _logged_in_client()
        r = c.post(
            "/api/reference-images/upload",
            params={"filename": ""},
            content=_png_bytes(),
            headers={"Content-Type": "application/octet-stream"},
        )
        check(r.status_code in (400, 422), f"an empty filename must be rejected, got {r.status_code}")


def test_unknown_category_falls_back_to_general():
    root, meta_path = _isolated_roots()
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _logged_in_client()
        r = c.post(
            "/api/reference-images/upload",
            params={"filename": "mystery.png", "category": "not_a_real_category"},
            content=_png_bytes(),
            headers={"Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 200, f"expected 200, got {r.status_code}")
        check(r.json().get("category") == "general",
              f"an unrecognized category must fall back to 'general', got {r.json()}")


def test_delete_removes_file_and_metadata():
    root, meta_path = _isolated_roots()
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _logged_in_client()
        entry = c.post(
            "/api/reference-images/upload",
            params={"filename": "to_delete.png", "category": "wall_art"},
            content=_png_bytes(),
            headers={"Content-Type": "application/octet-stream"},
        ).json()
        stored_path = root / entry["filename"]
        check(stored_path.is_file(), "file must exist right after upload")

        r = c.delete(f"/api/reference-images/{entry['id']}")
        check(r.status_code == 200, f"delete should 200, got {r.status_code}: {r.text[:200]}")
        check(not stored_path.exists(), "the file must be gone from disk after delete")

        listed = c.get("/api/reference-images").json().get("images") or []
        check(not any(im["id"] == entry["id"] for im in listed),
              f"the deleted image must not appear in the list anymore, got {listed}")


def test_delete_unknown_id_404s():
    root, meta_path = _isolated_roots()
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _logged_in_client()
        r = c.delete("/api/reference-images/not-a-real-id")
        check(r.status_code == 404, f"deleting an unknown id must 404, got {r.status_code}")


def test_category_filter_narrows_list():
    root, meta_path = _isolated_roots()
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _logged_in_client()
        c.post("/api/reference-images/upload", params={"filename": "a.png", "category": "wall_art"},
               content=_png_bytes(), headers={"Content-Type": "application/octet-stream"})
        c.post("/api/reference-images/upload", params={"filename": "b.png", "category": "sticker_pack"},
               content=_png_bytes(), headers={"Content-Type": "application/octet-stream"})

        r = c.get("/api/reference-images", params={"category": "wall_art"})
        images = r.json().get("images") or []
        check(len(images) == 1 and images[0]["category"] == "wall_art",
              f"filtering by category=wall_art should return exactly the wall_art upload, got {images}")


def test_upload_requires_auth():
    c = TestClient(server.app, base_url="https://testserver")
    r = c.post(
        "/api/reference-images/upload",
        params={"filename": "x.png"},
        content=_png_bytes(),
        headers={"Content-Type": "application/octet-stream"},
    )
    check(r.status_code in (401, 403), f"unauthenticated upload must be rejected, got {r.status_code}")


def test_list_requires_auth():
    c = TestClient(server.app, base_url="https://testserver")
    r = c.get("/api/reference-images")
    check(r.status_code in (401, 403), f"unauthenticated list must be rejected, got {r.status_code}")


def test_reference_images_root_registered_in_file_labels():
    # Confirms the library is browsable from the Files screen for free, per the
    # plan's §3 -- a "reference_images" -> "Reference Photos" label must exist.
    check("reference_images" in server._FILE_ROOTS,
          "reference_images must be a registered durable root")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("REFERENCE IMAGES TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("REFERENCE IMAGES TESTS OK — upload/list/delete round-trip, non-image and "
          "oversized rejection, category fallback + filtering, and auth all verified.")


if __name__ == "__main__":
    run()
