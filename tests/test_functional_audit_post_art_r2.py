"""
Functional audit ROUND 2 — post_scheduled_art.py::post_art (tools/post_scheduled_art.py:402)

Round 1 shipped tests/test_functional_audit_post_art.py, which claimed PASS for
post_art()'s "always stages a draft, never activates live" behavior. An
independent mock-fidelity check found that round-1's fake Etsy client's
`_request` was defined as:

    def _request(method, path, json=None, **kwargs): ...

while the REAL `EtsyAPIClient._request` (tools/etsy_api.py) signature is:

    def _request(self, method, path, params: dict | None = None, body: dict | None = None) -> dict

There is no `json` parameter and no `**kwargs` catch-all on the real method.
Every real call site in post_scheduled_art.py (get_or_create_section's two
`_request` calls, and post_art()'s listing-create `_request` call) passed
`json={...}` — a keyword argument the real method does not accept at all.
Called against the real client, this raises `TypeError: _request() got an
unexpected keyword argument 'json'` at argument-binding time, before any of
`_request`'s body ever executes. Round 1's mock silently *accepted* `json=`
(because its fake signature had a matching `json` parameter and a `**kwargs`
sink), so its "success" test exercised a code path that can never actually
succeed in production.

This file:
  1. Independently reproduces the raw signature mismatch directly against the
     real `EtsyAPIClient._request` (test_real_request_rejects_json_kwarg) —
     documents the exact TypeError, independent of post_scheduled_art.py's
     current state.
  2. Runs post_art() end-to-end through a MOCK-FAITHFUL fake client whose
     `_request(method, path, params=None, body=None)` matches the real
     signature exactly (no `json` param, no `**kwargs`) and asserts the
     listing gets created + staged for approval successfully.
     Run against the ORIGINAL (unfixed) tools/post_scheduled_art.py, this test
     FAILS: post_art() silently returns None (its own `except Exception`
     swallows the TypeError and prints "FAILED to create listing"), and NO
     action is ever staged in the Action Center — meaning the entire
     "success" / approval-staging path this product's safety story depends on
     was unreachable in real production.
  3. A static source-scan guard (test_no_json_kwarg_call_sites) that fails if
     `_request(...)` is ever called with `json=` again anywhere in
     tools/post_scheduled_art.py — a permanent regression guard for this
     exact defect class, independent of the dynamic mock test above.

Per the task's HARD SAFETY RULE 5, this is a mechanical, unambiguous bug (a
wrong keyword-argument name with an obvious correct fix — `body=` instead of
`json=`, matching every other real call site in this codebase: etsy_api.py
itself, weekly_report.py, listing_integrity_check.py, approve_listing.py).
The fix was applied directly to tools/post_scheduled_art.py (both call
sites: get_or_create_section's section-create POST, and post_art()'s
listing-create POST) as part of this audit round. This test file, run
against the FIXED source, passes; run against the original source it fails
with the exact symptom described above (see the audit report for the
before/after transcript).
"""
import os
import re
import sys
import json
import inspect
import tempfile
import datetime
from pathlib import Path
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_post_art_r2_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-r2-not-a-real-secret")

for p in (ROOT, ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import tools.post_scheduled_art as psa  # noqa: E402
from tools.etsy_api import EtsyAPIClient  # noqa: E402
from tools.api_server import db as _db  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


# ── Fixtures (same shape as round 1) ─────────────────────────────────────────

def _make_category(cat_id="test_category", subjects=None):
    return {
        "id": cat_id,
        "label": "Test Category",
        "subjects": subjects or ["Subject One", "Subject Two"],
        "subjects_used": [],
        "price": 6.99,
        "title_template": "{subject} Test Print, Instant Download",
        "tags": ["test tag"] * 13,
        "art_prompt_template": "A painting of {subject_lower}.",
        "scene_a_prompt": "An empty room, scene A.",
        "scene_b_prompt": "An empty room, scene B.",
        "description_niche": "test",
        "room_context": "Test room context",
        "frame_color": [139, 110, 80],
    }


def _write_schedule(tmp_path, categories, queue_position=0, next_post_date=None,
                     interval_days=2, post_history=None):
    schedule = {
        "version": 1,
        "interval_days": interval_days,
        "last_posted_date": "2000-01-01",
        "next_post_date": next_post_date or "2000-01-01",
        "queue_position": queue_position,
        "post_history": post_history or [],
        "categories": categories,
    }
    with open(tmp_path, "w") as f:
        json.dump(schedule, f)
    return schedule


def _fake_gen_image_writer():
    from PIL import Image as PILImage

    def _fake(prompt, out_path, size="1024x1536", quality="high"):
        img = PILImage.new("RGB", (64, 64), (180, 140, 100))
        img.save(out_path, "JPEG", quality=80)
        return True
    return _fake


def _make_mock_faithful_fake_etsy_client(listing_id=424242):
    """A fake EtsyAPIClient whose `_request` matches the REAL
    `EtsyAPIClient._request(self, method, path, params=None, body=None)`
    signature exactly -- no `json` parameter, no `**kwargs` sink. Any call
    site that (wrongly) passes `json=...` will raise TypeError at the Mock's
    side_effect invocation, exactly as it would against the real client.
    This is the fix for round 1's mock-fidelity bug."""
    calls = []
    client = Mock()
    client.shop_id = "SHOP123"
    client.access_token = "tok"
    client.client_id = "cid"
    client.client_secret = "csecret"

    def _request(method, path, params=None, body=None):
        calls.append({"method": method, "path": path, "params": params, "body": body})
        if method == "GET" and path.endswith("/sections"):
            return {"results": []}  # forces the POST-create-section branch too
        if method == "POST" and path.endswith("/sections"):
            return {"shop_section_id": 555}
        if method == "POST" and path.endswith("/listings"):
            return {"listing_id": listing_id}
        return {}

    client._request = Mock(side_effect=_request)
    client.get_listing = Mock(return_value={"state": "draft"})
    client._calls = calls
    return client


# ── Test 1: the real signature mismatch, independent of post_scheduled_art.py ──

def test_real_request_rejects_json_kwarg():
    sig = inspect.signature(EtsyAPIClient._request)
    param_names = list(sig.parameters.keys())
    check("json" not in param_names,
          f"real EtsyAPIClient._request should NOT have a 'json' parameter, got params={param_names!r}")
    check(not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()),
          "real EtsyAPIClient._request should not have a **kwargs catch-all that would "
          "silently swallow a wrong keyword argument")

    raised = None
    try:
        EtsyAPIClient._request(object(), "POST", "shops/123/listings", json={"a": 1})
    except TypeError as e:
        raised = e
    check(raised is not None,
          "calling the real EtsyAPIClient._request with json=... must raise TypeError "
          "(it did not -- the signature may have changed, re-check this test)")
    if raised is not None:
        check("json" in str(raised) and "unexpected keyword argument" in str(raised),
              f"expected a clear 'unexpected keyword argument json' TypeError, got: {raised}")


# ── Test 2: static regression guard — no _request(...) call may pass json= ────

def test_no_json_kwarg_call_sites():
    src = (ROOT / "tools" / "post_scheduled_art.py").read_text()
    # Find every `_request(...)` call (balancing isn't needed -- these calls
    # never nest another call inside the json=/body= argument in this file)
    # and check none of them use a `json=` keyword argument.
    offending = []
    for m in re.finditer(r"_request\(([^)]*(?:\([^)]*\)[^)]*)*)\)", src, re.DOTALL):
        call_src = m.group(1)
        if re.search(r"(?<![A-Za-z0-9_])json\s*=", call_src):
            line_no = src[:m.start()].count("\n") + 1
            offending.append((line_no, call_src.strip().replace("\n", " ")[:80]))
    check(not offending,
          f"found _request(...) call site(s) still using json= instead of body=: {offending}")


# ── Test 3: post_art() end-to-end through a mock-faithful fake client ────────

def test_post_art_success_with_mock_faithful_request_signature():
    with tempfile.TemporaryDirectory() as td:
        sched_path = os.path.join(td, "art_schedule.json")
        art_dir = os.path.join(td, "art_dir")
        os.makedirs(art_dir, exist_ok=True)
        cat = _make_category(subjects=["LiveSubject", "SecondSubject"])
        today_iso = datetime.date.today().isoformat()
        _write_schedule(sched_path, [cat], queue_position=0, next_post_date=today_iso)

        fake_client = _make_mock_faithful_fake_etsy_client(listing_id=424242)
        etsy_client_ctor = Mock(return_value=fake_client)

        uploaded_images = []
        uploaded_files = []

        def _fake_upload_image_raw(client, listing_id, img_path, rank):
            uploaded_images.append((listing_id, rank))
            return True

        def _fake_upload_file_raw(client, listing_id, file_path):
            uploaded_files.append((listing_id, file_path))
            return True

        before_actions = _db.list_actions(status=None, limit=1000)

        with patch.object(psa, "SCHEDULE_PATH", sched_path), \
             patch.object(psa, "ART_DIR", art_dir), \
             patch.object(psa, "gen_image", side_effect=_fake_gen_image_writer()), \
             patch.object(psa, "EtsyAPIClient", etsy_client_ctor), \
             patch.object(psa, "upload_image_raw", side_effect=_fake_upload_image_raw), \
             patch.object(psa, "upload_file_raw", side_effect=_fake_upload_file_raw), \
             patch("time.sleep", return_value=None):
            result = psa.post_art(preview_only=False)

        # ---- THE CENTRAL ASSERTION ----
        # Against the buggy (json=) source this is where the round-1-masked bug
        # actually surfaces: result comes back None because post_art()'s own
        # `except Exception` swallows the TypeError from the listing-create
        # call and prints "FAILED to create listing", never reaching the
        # staging step at all.
        check(result is not None,
              "post_art() returned None -- this is the round-2-confirmed bug: the real "
              "EtsyAPIClient._request() has no 'json' parameter, so the json=... call at "
              "the listing-create step raises TypeError, which post_art()'s own except-block "
              "swallows and reports as 'FAILED to create listing'. The success/staging path "
              "is unreachable in real production.")
        if result is not None:
            check(result.get("listing_id") == 424242,
                  f"expected returned listing_id 424242, got {result!r}")

        # ---- Section lookup/create actually completed (proves the OTHER json= site is fixed too) ----
        section_posts = [c for c in fake_client._calls
                          if c["method"] == "POST" and c["path"].endswith("/sections")]
        check(len(section_posts) == 1,
              f"expected exactly one section-create POST to have actually gone through "
              f"(not silently swallowed by get_or_create_section's own try/except), got "
              f"{len(section_posts)}: {fake_client._calls}")

        # ---- Listing was created as a draft ----
        listings_posts = [c for c in fake_client._calls
                           if c["method"] == "POST" and c["path"].endswith("/listings")]
        check(len(listings_posts) == 1,
              f"expected exactly one listing-create POST to have gone through, got "
              f"{len(listings_posts)}: {fake_client._calls}")
        if listings_posts:
            body = listings_posts[0]["body"] or {}
            check(body.get("state") == "draft",
                  f"listing must be created with state='draft', got state={body.get('state')!r}")
            check(body.get("shop_section_id") == 555,
                  f"listing should carry the newly-created shop_section_id=555, got "
                  f"{body.get('shop_section_id')!r} -- body={body!r}")

        # ---- The approval action was actually staged ----
        after_actions = _db.list_actions(status=None, limit=1000)
        new_actions = [a for a in after_actions if a not in before_actions]
        check(len(new_actions) == 1,
              f"expected exactly one new staged 'publish_listing' action once the listing "
              f"create call actually succeeds, got {len(new_actions)}: {new_actions}")
        if new_actions:
            check(new_actions[0]["type"] == "publish_listing",
                  f"expected staged action type 'publish_listing', got {new_actions[0]['type']!r}")
            check(new_actions[0]["payload"].get("listing_id") == 424242,
                  f"staged action payload must reference the created listing_id, got "
                  f"{new_actions[0]['payload']!r}")

        check(len(uploaded_images) >= 1, "expected at least one image upload once listing creation succeeds")
        check(len(uploaded_files) == 1 and uploaded_files[0][0] == 424242,
              f"expected exactly one digital file upload for listing 424242, got {uploaded_files!r}")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT R2 TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT R2 TESTS OK -- real EtsyAPIClient._request has no 'json' "
          "parameter, post_scheduled_art.py's _request(...) call sites all use body= "
          "(not json=), and post_art() genuinely creates the listing + stages the "
          "publish_listing approval action end-to-end against a mock-faithful fake client.")


if __name__ == "__main__":
    run()
