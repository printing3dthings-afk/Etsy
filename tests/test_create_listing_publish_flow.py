#!/usr/bin/env python3
"""
Tests for the Products-tappable-cards feature (2026-07-18), P2+P3: the new
`create_listing` staged-action type and POST /api/products/{id}/stage-publish
-- the "Publish to Etsy" button in the review modal.

This is the first capability in the whole app that can create a brand-new
Etsy listing (the only prior code that did this, tools/etsy_listing_tools.py,
is an orphaned module never imported by main.py and uses an incompatible
data model). It's built to the same stage -> validate -> approve -> execute
discipline every other Etsy mutation here follows: stage-publish only
enqueues a create_listing action after re-deriving and gate-checking the
content fresh; the actual Etsy write happens only in
_execute_create_listing_staged_action, dispatched from approve_action after
Scott approves it in the Action Center. The new listing is always created as
an Etsy-side DRAFT (client.create_listing() omits `state`) -- activation is a
separate, already-existing toggle_listing_state action, never automatic here.

Run: python tests/test_create_listing_publish_flow.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_create_listing_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "create-listing-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(server.app, base_url="https://testserver")
_AUTH = {"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"}

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


_GOOD_LISTING_DATA = {
    "title": "Kawaii Digital Planner 2026, GoodNotes iPad, Instant Download",
    "description": "x" * 350,
    "tags": [f"tag{i}" for i in range(13)],
    "price": 12.99,
    "taxonomy_id": 2078,
    "quantity": 999,
    "type": "download",
}


# ── _validate_staged_action("create_listing") ───────────────────────────────

def test_registered_in_staged_action_types():
    check("create_listing" in server._STAGED_ACTION_TYPES, "create_listing must be a recognized staged-action type")
    check("create_listing" in server._LISTING_CREATE_STAGED_ACTION_TYPES, "must be in its own dedicated bucket")
    check("create_listing" not in server._ETSY_STAGED_ACTION_TYPES,
          "must NOT share _ETSY_STAGED_ACTION_TYPES -- that bucket assumes an existing listing_id")


def test_validate_missing_product_id():
    ok, msg = server._validate_staged_action({"type": "create_listing", "payload": {}})
    check(not ok and "product_id" in msg, f"got: {ok}, {msg}")


def test_validate_pre_publish_gate_failure_blocks_staging():
    bad_data = dict(_GOOD_LISTING_DATA)
    bad_data["title"] = "x"  # too short, no "instant download"
    payload = {"product_id": "DPX", "listing_data": bad_data,
               "photo_paths": [], "file_paths": ["product_files/DPX.pdf"]}
    with patch.object(server, "_product_file_abs_path", lambda rel: Path("/tmp/fake")):
        ok, msg = server._validate_staged_action({"type": "create_listing", "payload": payload})
    check(not ok and "pre-publish gate failed" in msg, f"got: {ok}, {msg}")


def test_validate_missing_files_on_disk_blocks_staging():
    payload = {"product_id": "DPX", "listing_data": _GOOD_LISTING_DATA,
               "photo_paths": [], "file_paths": ["product_files/DPX.pdf"]}
    with patch.object(server, "_product_file_abs_path", lambda rel: None):
        ok, msg = server._validate_staged_action({"type": "create_listing", "payload": payload})
    check(not ok and "not found on disk" in msg, f"got: {ok}, {msg}")


def test_validate_no_deliverable_files_blocks_staging():
    payload = {"product_id": "DPX", "listing_data": _GOOD_LISTING_DATA, "photo_paths": [], "file_paths": []}
    ok, msg = server._validate_staged_action({"type": "create_listing", "payload": payload})
    check(not ok and "deliverable" in msg, f"got: {ok}, {msg}")


def test_validate_happy_path_passes():
    payload = {"product_id": "DPX", "listing_data": _GOOD_LISTING_DATA,
               "photo_paths": ["a.jpg"], "file_paths": ["product_files/DPX.pdf"]}
    with patch.object(server, "_product_file_abs_path", lambda rel: Path("/tmp/fake")):
        ok, msg = server._validate_staged_action({"type": "create_listing", "payload": payload})
    check(ok, f"expected pass, got: {msg}")


def test_validate_at_approval_refuses_if_already_published():
    payload = {"product_id": "DPX", "listing_data": _GOOD_LISTING_DATA,
               "photo_paths": [], "file_paths": ["product_files/DPX.pdf"]}
    fake_entry = {"product_id": "DPX", "name": "x", "category": "digital_planner",
                  "status": "listed_draft", "etsy_listing_id": "", "files": []}
    with patch.object(server, "_product_file_abs_path", lambda rel: Path("/tmp/fake")), \
         patch.object(server, "_find_catalog_product", lambda pid: fake_entry), \
         patch.object(server, "_product_catalog_overrides", lambda: {"DPX": {"etsy_listing_id": "555"}}):
        ok, msg = server._validate_staged_action({"type": "create_listing", "payload": payload}, at_approval=True)
    check(not ok and "already has an Etsy listing" in msg, f"got: {ok}, {msg}")


def test_validate_at_approval_passes_when_not_yet_published():
    payload = {"product_id": "DPX", "listing_data": _GOOD_LISTING_DATA,
               "photo_paths": [], "file_paths": ["product_files/DPX.pdf"]}
    fake_entry = {"product_id": "DPX", "name": "x", "category": "digital_planner",
                  "status": "ready_for_review", "etsy_listing_id": "", "files": []}
    with patch.object(server, "_product_file_abs_path", lambda rel: Path("/tmp/fake")), \
         patch.object(server, "_find_catalog_product", lambda pid: fake_entry), \
         patch.object(server, "_product_catalog_overrides", lambda: {}):
        ok, msg = server._validate_staged_action({"type": "create_listing", "payload": payload}, at_approval=True)
    check(ok, f"expected pass, got: {msg}")


# ── _execute_create_listing_staged_action ───────────────────────────────────

def _fake_client(create_result=None, image_result=None, file_result=None,
                  create_raises=None, image_raises=None):
    inst = MagicMock()
    if create_raises:
        inst.create_listing.side_effect = create_raises
    else:
        inst.create_listing.return_value = create_result or {"listing_id": 999111222}
    if image_raises:
        inst.upload_listing_image.side_effect = image_raises
    else:
        inst.upload_listing_image.return_value = image_result or {"listing_image_id": 1}
    inst.upload_listing_file.return_value = file_result or {"listing_file_id": 2}
    return inst


def test_execute_happy_path_creates_draft_and_writes_override():
    action = {"payload": {
        "product_id": "DPX", "listing_data": _GOOD_LISTING_DATA,
        "photo_paths": ["photo1.jpg"], "file_paths": ["file1.pdf", "file2.zip"],
    }}
    fake_client = _fake_client()
    captured_override = {}

    def fake_write_override(pid, updates):
        captured_override["product_id"] = pid
        captured_override.update(updates)

    with patch.object(server, "EtsyAPIClient", return_value=fake_client), \
         patch.object(server, "_product_file_abs_path", lambda rel: Path("/tmp/" + rel)), \
         patch.object(server, "_write_product_catalog_override", fake_write_override):
        result = server._execute_create_listing_staged_action(action)

    check(result["etsy_listing_id"] == 999111222, f"got: {result}")
    check(result["state"] == "draft", f"got: {result}")
    check("upload_errors" not in result, f"expected no errors, got: {result}")
    check(len(result["photos_uploaded"]) == 1 and len(result["files_uploaded"]) == 2, f"got: {result}")
    check(captured_override.get("etsy_listing_id") == "999111222", f"got: {captured_override}")
    check(captured_override.get("status") == "listed_draft", f"got: {captured_override}")
    # Must NOT auto-activate -- create_listing() call must never receive state=active.
    call_kwargs = fake_client.create_listing.call_args
    listing_data_sent = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("listing_data")
    check("state" not in listing_data_sent, f"must not set state explicitly, got: {listing_data_sent}")


def test_execute_creation_failure_raises_and_writes_nothing():
    action = {"payload": {
        "product_id": "DPX", "listing_data": _GOOD_LISTING_DATA,
        "photo_paths": [], "file_paths": ["file1.pdf"],
    }}
    fake_client = _fake_client(create_raises=RuntimeError("simulated Etsy outage"))
    write_called = []
    with patch.object(server, "EtsyAPIClient", return_value=fake_client), \
         patch.object(server, "_write_product_catalog_override", lambda pid, u: write_called.append((pid, u))):
        try:
            server._execute_create_listing_staged_action(action)
            raised = False
        except RuntimeError:
            raised = True
    check(raised, "expected a listing-creation failure to raise")
    check(write_called == [], "no override should be written if creation itself failed")


def test_execute_partial_upload_failure_still_writes_override_and_reports_errors():
    action = {"payload": {
        "product_id": "DPX", "listing_data": _GOOD_LISTING_DATA,
        "photo_paths": ["photo1.jpg"], "file_paths": ["file1.pdf"],
    }}
    fake_client = _fake_client(image_raises=RuntimeError("simulated image upload failure"))
    captured_override = {}
    with patch.object(server, "EtsyAPIClient", return_value=fake_client), \
         patch.object(server, "_product_file_abs_path", lambda rel: Path("/tmp/" + rel)), \
         patch.object(server, "_write_product_catalog_override", lambda pid, u: captured_override.update(u)):
        result = server._execute_create_listing_staged_action(action)

    check("upload_errors" in result and len(result["upload_errors"]) == 1, f"got: {result}")
    check(captured_override.get("etsy_listing_id") == "999111222",
          "a real draft now exists on Etsy -- the override must still be written even on partial failure")


# ── approve_action dispatch ──────────────────────────────────────────────────

def test_approve_action_dispatches_create_listing_to_its_own_executor():
    fake_action = {"id": 1, "status": "pending", "type": "create_listing",
                   "payload": {"product_id": "DPX", "listing_data": _GOOD_LISTING_DATA,
                               "photo_paths": [], "file_paths": ["f.pdf"]}}
    calls = []

    def fake_get_action(aid):
        return fake_action

    def fake_set_status(aid, status, result=None):
        calls.append((status, result))

    def fake_execute(a):
        return {"etsy_listing_id": 42, "state": "draft"}

    with patch.object(server.db, "get_action", fake_get_action), \
         patch.object(server.db, "set_action_status", fake_set_status), \
         patch.object(server, "_validate_staged_action", lambda a, at_approval=False: (True, "ok")), \
         patch.object(server, "_execute_create_listing_staged_action", fake_execute):
        resp = client.post("/api/queue/1/approve", headers=_AUTH)

    check(resp.status_code == 200, f"got {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    check(body["result"]["etsy_listing_id"] == 42, f"got: {body}")
    check(any(c[0] == "executing" for c in calls), f"got: {calls}")


# ── POST /api/products/{id}/stage-publish ───────────────────────────────────

def _fake_review(**overrides):
    base = {
        "product_id": "DPX", "category": "digital_planner", "status": "ready_for_review",
        "listing_id": None,
        "catalog": {"id": "DPX", "listing_id": None},
        "has_content": True,
        "content": {"title": _GOOD_LISTING_DATA["title"], "description": _GOOD_LISTING_DATA["description"],
                     "tags": _GOOD_LISTING_DATA["tags"], "price": 12.99, "shop_section_id": 58657105},
        "photos": [{"name": "01.jpg", "rel": "product_files/DPX_listing_images/01.jpg", "exists": True, "url": "/x"}],
        "deliverables": [
            {"name": "DPX.pdf", "rel": "product_files/DPX.pdf", "exists": True},
            {"name": "DPX_sticker_pack.zip", "rel": "product_files/DPX_sticker_pack.zip", "exists": True},
        ],
        "qc": {"pid": "DPX", "verdict": "pass", "summary": {}, "rows": [], "message": "ok"},
    }
    base.update(overrides)
    return base


def test_stage_publish_happy_path():
    with patch.object(server, "_gather_product_review", lambda pid: _fake_review()), \
         patch.object(server, "_validate_staged_action", lambda a, at_approval=False: (True, "ok")), \
         patch.object(server.db, "list_actions", lambda status="pending", limit=100: []), \
         patch.object(server.db, "enqueue_action", lambda t, s, p: 77):
        resp = client.post("/api/products/DPX/stage-publish", headers=_AUTH)
    check(resp.status_code == 200, f"got {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    check(body["staged"] is True and body["action_id"] == 77, f"got: {body}")


def test_stage_publish_404_unknown_product():
    with patch.object(server, "_gather_product_review", lambda pid: None):
        resp = client.post("/api/products/NOPE/stage-publish", headers=_AUTH)
    check(resp.status_code == 404, f"got {resp.status_code}")


def test_stage_publish_refuses_if_already_has_listing():
    with patch.object(server, "_gather_product_review", lambda pid: _fake_review(listing_id="12345")):
        resp = client.post("/api/products/DPX/stage-publish", headers=_AUTH)
    check(resp.status_code == 409, f"got {resp.status_code}: {resp.text[:200]}")


def test_stage_publish_refuses_unsupported_category():
    # (2026-07-25) Was category="wall_art" -- the "Etsy Listing" tile feature
    # extended _PRODUCT_TAXONOMY_BY_CATEGORY to cover wall_art and
    # coloring_pages, so wall_art is no longer an unsupported-category case.
    # "sublimation" is a real category name in _CREATE_CATEGORIES that has
    # no build pipeline and, correctly, still has no taxonomy entry either.
    with patch.object(server, "_gather_product_review", lambda pid: _fake_review(category="sublimation")):
        resp = client.post("/api/products/DPX/stage-publish", headers=_AUTH)
    check(resp.status_code == 400 and "category" in resp.text, f"got {resp.status_code}: {resp.text[:200]}")


def test_stage_publish_refuses_no_content():
    with patch.object(server, "_gather_product_review", lambda pid: _fake_review(has_content=False, content=None)):
        resp = client.post("/api/products/DPX/stage-publish", headers=_AUTH)
    check(resp.status_code == 400 and "content" in resp.text, f"got {resp.status_code}: {resp.text[:200]}")


def test_stage_publish_refuses_qc_fail():
    with patch.object(server, "_gather_product_review",
                       lambda pid: _fake_review(qc={"pid": "DPX", "verdict": "fail", "message": "bad zip", "summary": {}, "rows": []})):
        resp = client.post("/api/products/DPX/stage-publish", headers=_AUTH)
    check(resp.status_code == 400 and "QC gate failed" in resp.text, f"got {resp.status_code}: {resp.text[:200]}")


def test_stage_publish_refuses_missing_deliverable():
    review = _fake_review()
    review["deliverables"][1]["exists"] = False
    with patch.object(server, "_gather_product_review", lambda pid: review):
        resp = client.post("/api/products/DPX/stage-publish", headers=_AUTH)
    check(resp.status_code == 400 and "missing deliverable" in resp.text, f"got {resp.status_code}: {resp.text[:200]}")


def test_stage_publish_refuses_duplicate_pending():
    pending = [{"type": "create_listing", "payload": {"product_id": "DPX"}}]
    with patch.object(server, "_gather_product_review", lambda pid: _fake_review()), \
         patch.object(server.db, "list_actions", lambda status="pending", limit=100: pending):
        resp = client.post("/api/products/DPX/stage-publish", headers=_AUTH)
    check(resp.status_code == 409 and "already pending" in resp.text, f"got {resp.status_code}: {resp.text[:200]}")


def test_stage_publish_builds_correct_listing_data():
    captured = {}

    def fake_enqueue(t, s, payload):
        captured["type"] = t
        captured["payload"] = payload
        return 1

    with patch.object(server, "_gather_product_review", lambda pid: _fake_review()), \
         patch.object(server, "_validate_staged_action", lambda a, at_approval=False: (True, "ok")), \
         patch.object(server.db, "list_actions", lambda status="pending", limit=100: []), \
         patch.object(server.db, "enqueue_action", fake_enqueue):
        resp = client.post("/api/products/DPX/stage-publish", headers=_AUTH)

    check(resp.status_code == 200, f"got {resp.status_code}")
    ld = captured["payload"]["listing_data"]
    check(ld["taxonomy_id"] == 2078, f"got: {ld}")
    check(ld["shop_section_id"] == 58657105, f"got: {ld}")
    check(ld["type"] == "download" and ld["quantity"] == 999, f"got: {ld}")
    check(captured["payload"]["file_paths"] == ["product_files/DPX.pdf", "product_files/DPX_sticker_pack.zip"],
          f"got: {captured['payload']}")


def test_stage_publish_requires_auth():
    resp = client.post("/api/products/DPX/stage-publish")
    check(resp.status_code == 401, f"got {resp.status_code}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CREATE-LISTING PUBLISH FLOW TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CREATE-LISTING PUBLISH FLOW TESTS OK — create_listing is its own staged-action "
          "bucket (never assumes an existing listing_id), validation blocks bad gate/missing "
          "files/duplicate publish, execution creates an Etsy DRAFT (never auto-activates), "
          "writes the durable override even on partial upload failure, raises with nothing "
          "written on outright creation failure, approve_action dispatches it to its own "
          "executor, and stage-publish gate-checks category/content/QC/files/duplicates "
          "before ever enqueueing.")


if __name__ == "__main__":
    run()
