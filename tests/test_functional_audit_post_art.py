"""
Functional audit — post_scheduled_art.py::post_art (tools/post_scheduled_art.py:402)

CLAUDE.md's Autonomy Boundaries lists "Post to social media accounts" / publishing
any listing without Scott's review as a Hard Stop. This function's actual job is
to generate a scheduled wall-art listing and STAGE it (draft + Action Center entry)
rather than ever activating it live. This test verifies:

  1. On success, the created listing is submitted with state="draft" and the ONLY
     approval mechanism used is db.enqueue_action("publish_listing", ...) — never
     a direct state=active call, never any other Etsy mutation that would make the
     listing visible to buyers.
  2. When art generation fails, post_art aborts (returns None) WITHOUT ever
     constructing an EtsyAPIClient or staging anything — it must fail loudly,
     not silently report success while skipping the real work.
  3. --preview mode never touches Etsy or the action queue at all.
  4. A missing or corrupt schedule file raises loudly (FileNotFoundError /
     JSONDecodeError) rather than being swallowed into a false "nothing to do".
  5. main()'s CLI entrypoint actually respects next_post_date — it does not call
     post_art() when the schedule says today is not due.

All network I/O (OpenAI image generation, Etsy REST calls, raw `requests.post`
image/file uploads) is mocked at the narrowest point. The local sqlite action
queue is exercised for real against a throwaway tempfile DB (already isolated
via DB_PATH before import, per this repo's testing convention) so the staging
assertions are checking real enqueue_action() behavior, not a mock's promises.
"""
import os
import sys
import json
import tempfile
import datetime
from pathlib import Path
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_post_art_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT, ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import tools.post_scheduled_art as psa  # noqa: E402
from tools.api_server import db as _db  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


# ── Shared fixtures ──────────────────────────────────────────────────────────

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
    """Returns a gen_image replacement that writes a real tiny valid JPEG
    (so downstream PIL compositing code — which is NOT mocked, to exercise
    real logic — doesn't choke on a bogus file) and reports success."""
    from PIL import Image as PILImage

    def _fake(prompt, out_path, size="1024x1536", quality="high"):
        img = PILImage.new("RGB", (64, 64), (180, 140, 100))
        img.save(out_path, "JPEG", quality=80)
        return True
    return _fake


def _make_fake_etsy_client(listing_id=999999, section_results=None):
    """A Mock standing in for EtsyAPIClient(), logging every ._request call
    so tests can assert on exactly what was sent (in particular: never a
    direct activation)."""
    calls = []
    client = Mock()
    client.shop_id = "SHOP123"
    client.access_token = "tok"
    client.client_id = "cid"
    client.client_secret = "csecret"

    def _request(method, path, params=None, body=None):
        # Matches the REAL EtsyAPIClient._request(self, method, path, params=None,
        # body=None) signature exactly (tools/etsy_api.py:518) -- 2026-08-14 fix:
        # this used to accept a json= kwarg that doesn't exist on the real class,
        # masking a real bug in tools/post_scheduled_art.py (see ops_runbook.md).
        calls.append({"method": method, "path": path, "body": body})
        if method == "GET" and path.endswith("/sections"):
            return {"results": section_results or []}
        if method == "POST" and path.endswith("/sections"):
            return {"shop_section_id": 555}
        if method == "POST" and path.endswith("/listings"):
            return {"listing_id": listing_id}
        return {}

    client._request = Mock(side_effect=_request)
    client.get_listing = Mock(return_value={"state": "draft"})
    client._calls = calls
    return client


# ── Test 1: missing / corrupt schedule file fails loudly ────────────────────

def test_load_schedule_missing_file_raises():
    with tempfile.TemporaryDirectory() as td:
        missing = os.path.join(td, "does_not_exist.json")
        with patch.object(psa, "SCHEDULE_PATH", missing):
            raised = False
            try:
                psa.load_schedule()
            except FileNotFoundError:
                raised = True
            check(raised, "load_schedule() on a missing file must raise FileNotFoundError, "
                           "not silently return an empty/default schedule")


def test_load_schedule_corrupt_json_raises():
    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(td, "corrupt.json")
        with open(bad, "w") as f:
            f.write("{ this is not : valid json ]")
        with patch.object(psa, "SCHEDULE_PATH", bad):
            raised = False
            try:
                psa.load_schedule()
            except json.JSONDecodeError:
                raised = True
            check(raised, "load_schedule() on corrupt JSON must raise loudly "
                           "(json.JSONDecodeError), not silently skip while reporting success")


# ── Test 2: pick_subject cycling correctness ─────────────────────────────────

def test_pick_subject_cycles_and_resets():
    cat = _make_category(subjects=["A", "B"])
    s1 = psa.pick_subject(cat)
    check(s1 == "A", f"expected first pick 'A', got {s1!r}")
    check(cat["subjects_used"] == ["A"], f"subjects_used should track picks, got {cat['subjects_used']!r}")
    s2 = psa.pick_subject(cat)
    check(s2 == "B", f"expected second pick 'B', got {s2!r}")
    s3 = psa.pick_subject(cat)
    check(s3 == "A", f"expected reset-and-restart to 'A' after exhausting subjects, got {s3!r}")
    check(cat["subjects_used"] == ["A"], f"reset should clear prior used list before re-adding, got {cat['subjects_used']!r}")


# ── Test 3: art generation failure aborts without any Etsy/staging side effect ──

def test_post_art_art_generation_failure_aborts_without_etsy_or_staging():
    with tempfile.TemporaryDirectory() as td:
        sched_path = os.path.join(td, "art_schedule.json")
        art_dir = os.path.join(td, "art_dir")
        os.makedirs(art_dir, exist_ok=True)
        cat = _make_category(subjects=["OnlySubject"])
        _write_schedule(sched_path, [cat], queue_position=0, next_post_date="2000-01-01")

        before_actions = _db.list_actions(status=None, limit=1000)

        etsy_client_ctor = Mock()

        with patch.object(psa, "SCHEDULE_PATH", sched_path), \
             patch.object(psa, "ART_DIR", art_dir), \
             patch.object(psa, "gen_image", return_value=False) as mock_gen, \
             patch.object(psa, "EtsyAPIClient", etsy_client_ctor), \
             patch("time.sleep", return_value=None):
            result = psa.post_art(preview_only=False)

        check(result is None, f"post_art() must return None when art generation fails, got {result!r}")
        check(mock_gen.called, "gen_image should have been attempted at least once")
        check(not etsy_client_ctor.called,
              "post_art() must NEVER construct an EtsyAPIClient when the source art file "
              "was never successfully generated — that would mean posting/staging content "
              "that doesn't actually exist")

        after_actions = _db.list_actions(status=None, limit=1000)
        check(len(after_actions) == len(before_actions),
              "no action should be staged in the Action Center when art generation failed "
              "(this would be a 'reports success while silently skipping the real work' bug)")

        # Schedule file must be left untouched (save_schedule() is only reached
        # after a successful Etsy stage) -- an aborted run must be safely retryable.
        with open(sched_path) as f:
            on_disk = json.load(f)
        check(on_disk["queue_position"] == 0,
              f"aborted run must not silently advance the queue, got queue_position={on_disk['queue_position']!r}")


# ── Test 4: --preview never touches Etsy or the action queue ────────────────

def test_post_art_preview_only_never_touches_etsy_or_db():
    with tempfile.TemporaryDirectory() as td:
        sched_path = os.path.join(td, "art_schedule.json")
        art_dir = os.path.join(td, "art_dir")
        os.makedirs(art_dir, exist_ok=True)
        cat = _make_category(subjects=["PreviewSubject"])
        _write_schedule(sched_path, [cat], queue_position=0, next_post_date="2000-01-01")

        before_actions = _db.list_actions(status=None, limit=1000)
        etsy_client_ctor = Mock()

        with patch.object(psa, "SCHEDULE_PATH", sched_path), \
             patch.object(psa, "ART_DIR", art_dir), \
             patch.object(psa, "gen_image", side_effect=_fake_gen_image_writer()), \
             patch.object(psa, "EtsyAPIClient", etsy_client_ctor), \
             patch("time.sleep", return_value=None):
            result = psa.post_art(preview_only=True)

        check(isinstance(result, dict) and "out_dir" in result,
              f"preview mode should return a dict describing generated files, got {result!r}")
        check(not etsy_client_ctor.called,
              "preview mode (--preview) must never construct an EtsyAPIClient")

        after_actions = _db.list_actions(status=None, limit=1000)
        check(len(after_actions) == len(before_actions),
              "preview mode must never stage anything in the Action Center")

        with open(sched_path) as f:
            on_disk = json.load(f)
        check(on_disk["queue_position"] == 0,
              "preview mode must not advance the schedule queue")


# ── Test 5: success path stages a draft, never activates directly ───────────

def test_post_art_success_stages_draft_listing_never_activates_directly():
    with tempfile.TemporaryDirectory() as td:
        sched_path = os.path.join(td, "art_schedule.json")
        art_dir = os.path.join(td, "art_dir")
        os.makedirs(art_dir, exist_ok=True)
        cat = _make_category(subjects=["LiveSubject", "SecondSubject"])
        today_iso = datetime.date.today().isoformat()
        _write_schedule(sched_path, [cat], queue_position=0, next_post_date=today_iso)

        fake_client = _make_fake_etsy_client(listing_id=424242)
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

        check(etsy_client_ctor.called, "post_art() must construct an EtsyAPIClient on the live-post path")
        check(isinstance(result, dict) and result.get("listing_id") == 424242,
              f"expected returned listing_id 424242, got {result!r}")

        # ---- Verify the listing was created as a DRAFT, never active ----
        listings_posts = [c for c in fake_client._calls
                           if c["method"] == "POST" and c["path"].endswith("/listings")]
        check(len(listings_posts) == 1, f"expected exactly one listing-create POST, got {len(listings_posts)}")
        if listings_posts:
            body = listings_posts[0]["body"] or {}
            check(body.get("state") == "draft",
                  f"CRITICAL: new listing must be created with state='draft' so it is never "
                  f"visible to buyers without Scott's approval — got state={body.get('state')!r}")

        # ---- Verify NO call anywhere set state to 'active' (direct activation) ----
        any_active = any(
            (c.get("body") or {}).get("state") == "active"
            for c in fake_client._calls
        )
        check(not any_active,
              "post_art() must never issue any Etsy request with state='active' — "
              "publishing live without Scott's approval is a Hard Stop per CLAUDE.md")

        # get_listing() may be called for the at-approval re-check; it must never
        # be used to flip state to active either -- it's a plain Mock so this is
        # implicitly satisfied, but assert it was only ever used read-only.
        for call in fake_client.get_listing.call_args_list:
            check(call.args and call.args[0] == 424242,
                  f"get_listing should only be queried for the newly created listing, got {call}")

        # ---- Verify the ONLY approval mechanism is enqueue_action('publish_listing', ...) ----
        after_actions = _db.list_actions(status=None, limit=1000)
        new_actions = [a for a in after_actions if a not in before_actions]
        check(len(new_actions) == 1,
              f"expected exactly one new staged action, got {len(new_actions)}: {new_actions}")
        if new_actions:
            action = new_actions[0]
            check(action["type"] == "publish_listing",
                  f"expected staged action type 'publish_listing', got {action['type']!r}")
            check(action["status"] == "pending",
                  f"staged action must start 'pending' (awaiting Scott's approval), got {action['status']!r}")
            check(action["payload"].get("listing_id") == 424242,
                  f"staged action payload must reference the created listing_id, got {action['payload']!r}")

        # ---- Schedule must advance exactly once, subject recorded as used ----
        with open(sched_path) as f:
            on_disk = json.load(f)
        check(on_disk["queue_position"] == 0,
              f"single-category schedule should wrap back to 0, got {on_disk['queue_position']!r}")
        check(on_disk["categories"][0]["subjects_used"] == ["LiveSubject"],
              f"expected subjects_used=['LiveSubject'], got {on_disk['categories'][0]['subjects_used']!r}")
        check(len(on_disk.get("post_history", [])) == 1,
              f"expected exactly one post_history entry, got {len(on_disk.get('post_history', []))}")
        if on_disk.get("post_history"):
            hist = on_disk["post_history"][0]
            check(hist.get("listing_id") == 424242, f"post_history listing_id mismatch: {hist!r}")

        # Uploads happened, scoped to the created listing
        check(len(uploaded_images) >= 1, "expected at least one image upload attempt on the success path")
        check(all(lid == 424242 for lid, _rank in uploaded_images),
              "all image uploads must target the newly created listing_id")
        check(len(uploaded_files) == 1 and uploaded_files[0][0] == 424242,
              f"expected exactly one digital file upload for listing 424242, got {uploaded_files!r}")


# ── Test 6: main()'s CLI entrypoint actually respects the due-date gate ─────

def test_main_respects_next_post_date_gate():
    with tempfile.TemporaryDirectory() as td:
        sched_path = os.path.join(td, "art_schedule.json")
        cat = _make_category(subjects=["X"])

        # Case A: next_post_date is far in the future -> must NOT post.
        future = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        _write_schedule(sched_path, [cat], queue_position=0, next_post_date=future)
        with patch.object(psa, "SCHEDULE_PATH", sched_path), \
             patch.object(psa, "post_art") as mock_post_art, \
             patch("sys.argv", ["post_scheduled_art.py"]):
            psa.main()
        check(not mock_post_art.called,
              "main() must NOT call post_art() when next_post_date is in the future "
              "(this is the actual autonomous-posting gate CLAUDE.md relies on)")

        # Case B: next_post_date is today -> must post (undated flag).
        today_iso = datetime.date.today().isoformat()
        _write_schedule(sched_path, [cat], queue_position=0, next_post_date=today_iso)
        with patch.object(psa, "SCHEDULE_PATH", sched_path), \
             patch.object(psa, "post_art") as mock_post_art, \
             patch("sys.argv", ["post_scheduled_art.py"]):
            psa.main()
        check(mock_post_art.called,
              "main() should call post_art() once next_post_date has arrived")
        if mock_post_art.called:
            _, kwargs = mock_post_art.call_args
            check(kwargs.get("preview_only") is False,
                  f"scheduled (non-forced) run must not be preview-only, got kwargs={kwargs!r}")


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
    print("FUNCTIONAL AUDIT TESTS OK -- post_art() only ever creates draft listings and "
          "stages a publish_listing approval action (never activates live directly), aborts "
          "loudly without any Etsy/staging side effects when art generation fails or the "
          "schedule file is missing/corrupt, --preview never touches Etsy/the action queue, "
          "and main()'s CLI entrypoint truly gates on next_post_date before calling post_art().")


if __name__ == "__main__":
    run()
