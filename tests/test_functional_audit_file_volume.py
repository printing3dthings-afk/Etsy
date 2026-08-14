"""
Functional audit -- POST /api/files/upload (upload_to_volume, main.py ~18666)
and POST /api/reference-images/upload (upload_reference_image, main.py ~13444).

Scope (per audit brief): path traversal safety, file-size limit enforcement,
and whether upload_to_volume degrades cleanly (not an unhandled exception)
when server._FILE_ROOTS has no "volume" entry.

tests/test_reference_images.py already covers upload_reference_image's
happy path, non-image rejection, oversized rejection, category handling,
auth, and delete round-trip -- not duplicated here. This file adds one gap
check for that endpoint (traversal via a filename containing path separators)
and focuses the rest on upload_to_volume, which had zero existing coverage.

Run: python3 tests/test_functional_audit_file_volume.py
"""
import io
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def _auth_headers():
    # Bearer token path in _auth_session_or_bearer() -- simplest way to
    # authenticate a TestClient call without going through /login.
    return {"Authorization": f"Bearer {server.APP_TOKEN}"}


def _client(raise_server_exceptions=True):
    return TestClient(
        server.app, base_url="https://testserver",
        raise_server_exceptions=raise_server_exceptions,
    )


def _png_bytes(color=(200, 120, 180)) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (24, 24), color=color).save(buf, format="PNG")
    return buf.getvalue()


# ── upload_to_volume: missing volume root ───────────────────────────────────

def test_upload_to_volume_missing_root_returns_503_not_crash():
    with patch.dict(server._FILE_ROOTS, {}, clear=False):
        server._FILE_ROOTS.pop("volume", None)
        c = _client()
        r = c.post(
            "/api/files/upload",
            params={"path": "product_files/DP9999.pdf"},
            content=b"hello world",
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 503,
              f"missing volume root should 503 cleanly, got {r.status_code}: {r.text[:200]}")


# ── upload_to_volume: path traversal ────────────────────────────────────────

def test_upload_to_volume_rejects_dotdot_traversal():
    tmp = tempfile.mkdtemp(prefix="frank_volume_root_")
    vol_root = Path(tmp) / "files"
    with patch.dict(server._FILE_ROOTS, {"volume": vol_root}):
        c = _client()
        r = c.post(
            "/api/files/upload",
            params={"path": "../../../../etc/passwd_clobber"},
            content=b"malicious payload",
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 400,
              f"a ../ traversal path must be rejected, got {r.status_code}: {r.text[:200]}")
        # Nothing must have been written outside the intended root.
        escaped = Path(tmp) / "etc" / "passwd_clobber"
        check(not escaped.exists(), f"traversal must not create a file outside the volume root: {escaped}")


def test_upload_to_volume_leading_slash_is_contained_not_absolute():
    # path=/etc/x -- rel.lstrip("/") strips the leading slash, so this must land
    # INSIDE the volume root (vol_root/etc/x), never at the real filesystem /etc/x.
    tmp = tempfile.mkdtemp(prefix="frank_volume_root_")
    vol_root = Path(tmp) / "files"
    with patch.dict(server._FILE_ROOTS, {"volume": vol_root}):
        c = _client()
        r = c.post(
            "/api/files/upload",
            params={"path": "/etc/hosts_clobber"},
            content=b"contained payload",
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}")
        check((vol_root / "etc" / "hosts_clobber").is_file(),
              "a leading-slash path must be contained inside the volume root")
        check(not Path("/etc/hosts_clobber").exists(),
              "must never write to the real filesystem /etc regardless of sandboxing")


# ── upload_to_volume: size limit ────────────────────────────────────────────

def test_upload_to_volume_rejects_oversized():
    tmp = tempfile.mkdtemp(prefix="frank_volume_root_")
    vol_root = Path(tmp) / "files"
    with patch.dict(server._FILE_ROOTS, {"volume": vol_root}), \
         patch.object(server, "_MAX_UPLOAD_BYTES", 100):
        c = _client()
        r = c.post(
            "/api/files/upload",
            params={"path": "product_files/big.pdf"},
            content=b"x" * 1000,
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 413, f"an oversized upload must 413, got {r.status_code}: {r.text[:200]}")
        check(not (vol_root / "product_files" / "big.pdf").exists(),
              "a rejected oversized upload must not leave a file behind")


# ── upload_to_volume: valid round trip (sanity baseline) ────────────────────

def test_upload_to_volume_valid_round_trip():
    tmp = tempfile.mkdtemp(prefix="frank_volume_root_")
    vol_root = Path(tmp) / "files"
    with patch.dict(server._FILE_ROOTS, {"volume": vol_root}):
        c = _client()
        r = c.post(
            "/api/files/upload",
            params={"path": "product_files/DP1030.pdf"},
            content=b"%PDF-1.4 fake pdf body",
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}")
        stored = vol_root / "product_files" / "DP1030.pdf"
        check(stored.is_file(), "the uploaded file must actually exist on disk")
        check(stored.read_bytes() == b"%PDF-1.4 fake pdf body", "stored bytes must match the uploaded body")


def test_upload_to_volume_requires_auth():
    tmp = tempfile.mkdtemp(prefix="frank_volume_root_")
    vol_root = Path(tmp) / "files"
    with patch.dict(server._FILE_ROOTS, {"volume": vol_root}):
        c = _client()
        r = c.post(
            "/api/files/upload",
            params={"path": "product_files/x.pdf"},
            content=b"data",
            headers={"Content-Type": "application/octet-stream"},
        )
        check(r.status_code in (401, 403), f"unauthenticated upload must be rejected, got {r.status_code}")


def test_upload_to_volume_requires_path():
    tmp = tempfile.mkdtemp(prefix="frank_volume_root_")
    vol_root = Path(tmp) / "files"
    with patch.dict(server._FILE_ROOTS, {"volume": vol_root}):
        c = _client()
        r = c.post(
            "/api/files/upload",
            params={"path": ""},
            content=b"data",
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 400, f"an empty path must be rejected, got {r.status_code}: {r.text[:200]}")


# ── upload_to_volume: CONFIRMED BUG -- target path resolving to an existing
# directory crashes with an unhandled exception instead of a clean HTTP error ──

def test_upload_to_volume_path_dot_targets_the_root_itself():
    # path="." lstrips to "." (no leading slash to strip), so
    # (vroot / ".").resolve() == vroot exactly. The traversal guard is
    # `if vroot not in target.parents and target != vroot: raise 400` --
    # target == vroot makes the second clause False, so the OR-guard never
    # fires and the request is let through. _write() then does
    # target.write_bytes(body) with target == vroot, an existing directory.
    tmp = tempfile.mkdtemp(prefix="frank_volume_root_")
    vol_root = Path(tmp) / "files"
    vol_root.mkdir(parents=True)
    with patch.dict(server._FILE_ROOTS, {"volume": vol_root}):
        c = _client(raise_server_exceptions=False)
        r = c.post(
            "/api/files/upload",
            params={"path": "."},
            content=b"payload",
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r.status_code != 500,
              f"path='.' must not crash with an unhandled 500 (IsADirectoryError), got {r.status_code}: {r.text[:300]}")


def test_upload_to_volume_existing_directory_collision_crashes():
    # Real-world path, not just path=".": upload A creates "sub/" as a parent
    # directory for "sub/file1.txt" via target.parent.mkdir(parents=True).
    # A second upload then targets path="sub" directly -- the traversal guard
    # passes (target is legitimately inside vroot), but target now IS an
    # existing directory, so target.write_bytes(body) raises IsADirectoryError,
    # which is never caught -- an unhandled exception surfaces as a bare 500,
    # violating this repo's own rule (.claude/rules/api-conventions.md,
    # "Error responses": "never a bare exception that becomes a generic 500").
    tmp = tempfile.mkdtemp(prefix="frank_volume_root_")
    vol_root = Path(tmp) / "files"
    with patch.dict(server._FILE_ROOTS, {"volume": vol_root}):
        c = _client(raise_server_exceptions=False)
        r1 = c.post(
            "/api/files/upload",
            params={"path": "sub/file1.txt"},
            content=b"first file",
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r1.status_code == 200, f"setup upload should succeed, got {r1.status_code}: {r1.text[:200]}")
        check((vol_root / "sub").is_dir(), "sub/ must now exist as a directory")

        r2 = c.post(
            "/api/files/upload",
            params={"path": "sub"},
            content=b"second upload collides with the directory",
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r2.status_code != 500,
              f"a path colliding with an existing directory must return a clean HTTP error, "
              f"not crash -- got {r2.status_code}: {r2.text[:300]}")


# ── upload_reference_image: gap check (traversal in filename) ──────────────

def test_reference_image_upload_filename_traversal_is_contained():
    # os.path.basename() strips any directory components from `filename`
    # before it's used -- confirm a crafted "../../evil.png" cannot escape
    # the reference_images root even though a random uuid prefix is also
    # applied on top.
    tmp = tempfile.mkdtemp(prefix="frank_refimages_root_")
    root = Path(tmp) / "reference_images"
    meta_path = Path(tmp) / "reference_images_meta.json"
    with patch.dict(server._FILE_ROOTS, {"reference_images": root}), \
         patch.object(server, "_REFERENCE_IMAGES_META_PATH", meta_path):
        c = _client()
        r = c.post(
            "/api/reference-images/upload",
            params={"filename": "../../../../tmp/evil_escape.png"},
            content=_png_bytes(),
            headers={**_auth_headers(), "Content-Type": "application/octet-stream"},
        )
        check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}")
        entry = r.json()
        check(".." not in entry.get("filename", ""),
              f"stored filename must not retain any traversal components, got {entry}")
        check((root / entry["filename"]).is_file(),
              "the file must be stored inside the reference_images root")
        check(not Path("/tmp/evil_escape.png").exists(),
              "traversal filename must never escape onto the real filesystem")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT TESTS OK -- upload_to_volume traversal/size/missing-root "
          "handling and upload_reference_image filename-traversal containment verified.")


if __name__ == "__main__":
    run()
