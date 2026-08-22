"""
Functional audit of tools/shop_health_check.py::check_shop -- ROUND 2.

Round 1 (tests/test_functional_audit_check_shop.py) verified the
review-average check, the photo-count check, and the *same-run
cross-listing* half of the hero-art audit (two listings sharing an
identical hero thumbnail right now).

This round targets two checks Round 1 did NOT touch:

  1. Manifest drift detection -- the *other* half of the hero-art audit.
     Unlike the cross-listing check (comparing two listings' hashes to
     each other in the same run), this compares a single listing's
     CURRENT hero hash against a hash recorded in a persisted manifest
     from a PREVIOUS run, and flags it if drift > 8 bits. Verifies it
     fires when the stored baseline and the current hero diverge, and
     stays silent when they match -- including that a *fresh* listing
     with no prior baseline entry is silent on its first run (nothing to
     drift from yet) but still gets a baseline recorded for future runs.

  2. Unanswered-review check -- fires only when at least one of the
     fetched reviews has no `seller_feedback`, stays silent when every
     review already has a response.

No real Etsy/network/AI calls are made anywhere in this file: a hand-built
fake client stands in for EtsyAPIClient, and `urllib.request.urlopen` is
patched to return small in-memory PIL-generated images. The durable
manifest path and weekly-snapshot file are both redirected to a tempdir so
this file never reads or writes the real `data/` tree.
"""

import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_r2_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import shop_health_check as shc  # noqa: E402
import tools.api_server.db as db_mod  # noqa: E402

from PIL import Image  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


# ─────────────────────────────────────────────────────────────────────────
# Fakes / helpers (same shape as round 1's file)
# ─────────────────────────────────────────────────────────────────────────

class FakeEtsyClient:
    def __init__(self, shop_id, shop, listings=None, reviews=None,
                 conversations=None, images_by_lid=None):
        self.shop_id = shop_id
        self.shop = shop
        self.listings = listings or []
        self.reviews = reviews or []
        self.conversations = conversations or []
        self.images_by_lid = images_by_lid or {}

    def _request(self, method, path):
        if path == f"shops/{self.shop_id}":
            return self.shop
        if path.startswith(f"shops/{self.shop_id}/listings/active"):
            return {"results": self.listings}
        if path.startswith(f"shops/{self.shop_id}/reviews"):
            return {"results": self.reviews}
        if path.startswith(f"shops/{self.shop_id}/conversations"):
            return {"results": self.conversations}
        m = re.match(r"listings/(\d+)/images", path)
        if m:
            return {"results": self.images_by_lid.get(m.group(1), [])}
        return {"error": f"unmocked path in fake client: {path}"}


def _gradient_image_bytes(direction="up"):
    """16x16 monotonic brightness ramp -- "up" and "down" are bitwise
    inverses under dhash's neighbor-comparison, giving the maximum
    possible Hamming distance (64/64)."""
    im = Image.new("L", (16, 16))
    px = im.load()
    for x in range(16):
        val = int(255 * x / 15)
        if direction == "down":
            val = 255 - val
        for y in range(16):
            px[x, y] = val
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="JPEG")
    return buf.getvalue()


def _compute_dhash_for_bytes(data: bytes) -> int:
    """Mirrors exactly what check_shop() does internally to a downloaded
    hero image (Image.open(io.BytesIO(raw)) -> _dhash), so a test can
    pre-seed a manifest baseline that is guaranteed to match (or not
    match) what the code under test will independently compute."""
    return shc._dhash(Image.open(io.BytesIO(data)))


def _make_images(n, hero_url, first_rank=1):
    out = [{"rank": first_rank, "url_570xN": hero_url}]
    for i in range(n - 1):
        out.append({"rank": first_rank + i + 1, "url_570xN": hero_url})
    return out


def _fake_urlopen_factory(url_to_bytes):
    def _urlopen(url, timeout=10):
        data = url_to_bytes.get(url) or _gradient_image_bytes("up")

        class _Resp:
            def read(self_inner):
                return data
        return _Resp()
    return _urlopen


def _run_check_shop(client, url_to_bytes=None, manifest_seed=None):
    """Runs check_shop() with every external boundary mocked, capturing
    and returning (result_dict, stdout_text, manifest_dict_after_run).

    manifest_seed, if given, is a dict written to the manifest file
    BEFORE check_shop runs -- simulating "a previous run already recorded
    a baseline hero hash for this listing". manifest_dict_after_run is
    read back and parsed WHILE the tempdir still exists (the tempdir is
    cleaned up before this function returns).
    """
    url_to_bytes = url_to_bytes or {}
    tmp_dir = tempfile.TemporaryDirectory()
    try:
        manifest_path = Path(tmp_dir.name) / "listing_image_manifest.json"
        snapshot_path = Path(tmp_dir.name) / "weekly_snapshots.json"
        if manifest_seed is not None:
            manifest_path.write_text(json.dumps(manifest_seed))

        buf = io.StringIO()
        with patch.object(db_mod, "resolve_persistent_path",
                           lambda *a, **k: manifest_path), \
             patch.object(shc, "SNAPSHOT_FILE", snapshot_path), \
             patch.object(shc.urllib.request, "urlopen",
                           _fake_urlopen_factory(url_to_bytes)), \
             patch.object(shc.time, "sleep", lambda *_: None):
            import contextlib
            with contextlib.redirect_stdout(buf):
                result = shc.check_shop(client)
        manifest_after = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        return result, buf.getvalue(), manifest_after
    finally:
        tmp_dir.cleanup()


def _base_shop(**overrides):
    shop = {
        "transaction_sold_count": 50,
        "num_favorers": 20,
        "review_count": 12,
        "review_average": 5.0,
        "listing_active_count": 5,
    }
    shop.update(overrides)
    return shop


# ─────────────────────────────────────────────────────────────────────────
# 1. Manifest drift detection (the "compare to a stored baseline" half of
#    the hero-art audit -- distinct from round 1's same-run cross-listing
#    duplicate check)
# ─────────────────────────────────────────────────────────────────────────

def test_manifest_drift_fires_when_current_hero_differs_from_stored_baseline():
    url = "https://img.example/hero-701.jpg"
    current_bytes = _gradient_image_bytes("up")
    # Baseline recorded on a *previous* run showed a maximally different
    # image (bitwise-inverse gradient -> Hamming distance 64, well over
    # the >8 drift threshold) at the same URL/listing.
    stored_hash = _compute_dhash_for_bytes(_gradient_image_bytes("down"))

    listings = [{"listing_id": 701, "title": "DP1034 Some Planner"}]
    images_by_lid = {"701": _make_images(7, url)}
    client = FakeEtsyClient(
        shop_id="66666",
        shop=_base_shop(),
        listings=listings,
        images_by_lid=images_by_lid,
    )
    manifest_seed = {"701": {"hero_hash": stored_hash, "hero_checked_at": "2026-01-01"}}

    result, out, manifest_after = _run_check_shop(
        client, url_to_bytes={url: current_bytes}, manifest_seed=manifest_seed
    )

    check(result is not None, "check_shop returned None unexpectedly")
    check("hero has changed since last upload" in out,
          f"expected the manifest-drift alert text for listing 701, got:\n{out}")
    check("[701]" in out.split("HERO-ART AUDIT", 1)[1],
          f"expected listing 701 named in the hero-art audit section, got:\n{out}")

    # The alert must actually be counted in the returned alert total, not
    # merely printed.
    check(result["alerts"] >= 1,
          f"expected alerts>=1 for a drifted hero baseline, got {result['alerts']}")

    # And the baseline on disk must be refreshed to the NEW hash so the
    # next run doesn't re-flag forever on a genuinely intentional change.
    new_hash = manifest_after["701"]["hero_hash"]
    check(new_hash == _compute_dhash_for_bytes(current_bytes),
          f"expected manifest baseline updated to the current hero hash after the run, "
          f"got {new_hash!r} vs expected {_compute_dhash_for_bytes(current_bytes)!r}")


def test_manifest_drift_stays_silent_when_current_hero_matches_stored_baseline():
    url = "https://img.example/hero-702.jpg"
    current_bytes = _gradient_image_bytes("up")
    # Baseline matches exactly what this run will independently compute
    # for the same bytes -- Hamming distance 0, well under the threshold.
    stored_hash = _compute_dhash_for_bytes(current_bytes)

    listings = [{"listing_id": 702, "title": "DP1034 Some Other Planner"}]
    images_by_lid = {"702": _make_images(7, url)}
    client = FakeEtsyClient(
        shop_id="77777",
        shop=_base_shop(),
        listings=listings,
        images_by_lid=images_by_lid,
    )
    manifest_seed = {"702": {"hero_hash": stored_hash, "hero_checked_at": "2026-01-01"}}

    result, out, _ = _run_check_shop(
        client, url_to_bytes={url: current_bytes}, manifest_seed=manifest_seed
    )

    check(result is not None, "check_shop returned None unexpectedly")
    check("hero has changed since last upload" not in out,
          f"unchanged hero (matches stored baseline) falsely flagged as drift:\n{out}")
    check(result["alerts"] == 0,
          f"expected 0 alerts for an unchanged hero, got {result['alerts']}")
    check("no duplicates or drift detected" in out,
          f"expected the clean hero-audit confirmation line, got:\n{out}")


def test_manifest_drift_silent_on_first_run_with_no_prior_baseline_but_records_one():
    """A listing with no manifest entry yet (first time check_shop has
    ever seen it) has nothing to compare against -- must not be flagged
    as drift -- but must come away from this run WITH a recorded
    baseline, so a genuinely different hero next week can be detected."""
    url = "https://img.example/hero-703.jpg"
    current_bytes = _gradient_image_bytes("up")

    listings = [{"listing_id": 703, "title": "DP1034 Brand New Planner"}]
    images_by_lid = {"703": _make_images(7, url)}
    client = FakeEtsyClient(
        shop_id="88888",
        shop=_base_shop(),
        listings=listings,
        images_by_lid=images_by_lid,
    )
    # No manifest_seed at all -- simulates a completely fresh manifest file.
    result, out, manifest_after = _run_check_shop(
        client, url_to_bytes={url: current_bytes}, manifest_seed=None
    )

    check(result is not None, "check_shop returned None unexpectedly")
    check("hero has changed since last upload" not in out,
          f"a listing with no prior baseline was falsely flagged as drifted:\n{out}")
    check(result["alerts"] == 0,
          f"expected 0 alerts on a first-ever run for a new listing, got {result['alerts']}")

    check("703" in manifest_after and "hero_hash" in manifest_after.get("703", {}),
          f"expected a baseline hero_hash recorded for listing 703 after its first run, got: {manifest_after}")


# ─────────────────────────────────────────────────────────────────────────
# 2. Unanswered-review check
# ─────────────────────────────────────────────────────────────────────────

def test_unanswered_review_alert_fires_when_a_review_has_no_seller_feedback():
    reviews = [
        {"rating": 5, "buyer_user_id": 1, "review": "Loved it!", "seller_feedback": "Thank you!"},
        {"rating": 4, "buyer_user_id": 2, "review": "Pretty good", "seller_feedback": None},
    ]
    client = FakeEtsyClient(
        shop_id="99991",
        shop=_base_shop(review_average=5.0),
        listings=[],
        reviews=reviews,
    )
    result, out, _ = _run_check_shop(client)

    check(result is not None, "check_shop returned None unexpectedly")
    check("review(s) have no seller response" in out,
          f"expected the unanswered-review alert text, got:\n{out}")
    check("1 review(s) have no seller response" in out,
          f"expected exactly 1 unanswered review counted, got:\n{out}")
    check(result["unanswered_reviews"] == 1,
          f"expected unanswered_reviews==1, got {result['unanswered_reviews']}")
    check(result["alerts"] >= 1,
          f"expected alerts>=1 for a shop with an unanswered review, got {result['alerts']}")


def test_unanswered_review_check_stays_silent_when_all_reviews_answered():
    reviews = [
        {"rating": 5, "buyer_user_id": 1, "review": "Loved it!", "seller_feedback": "Thank you!"},
        {"rating": 5, "buyer_user_id": 2, "review": "Great planner", "seller_feedback": "Glad you liked it!"},
    ]
    client = FakeEtsyClient(
        shop_id="99992",
        shop=_base_shop(review_average=5.0),
        listings=[],
        reviews=reviews,
    )
    result, out, _ = _run_check_shop(client)

    check(result is not None, "check_shop returned None unexpectedly")
    check("review(s) have no seller response" not in out,
          f"fully-answered reviews falsely triggered the unanswered-review alert:\n{out}")
    check(result["unanswered_reviews"] == 0,
          f"expected unanswered_reviews==0, got {result['unanswered_reviews']}")
    check("All reviews have seller responses" in out,
          f"expected the clean confirmation line, got:\n{out}")


# ─────────────────────────────────────────────────────────────────────────

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
    print("FUNCTIONAL AUDIT R2 TESTS OK -- check_shop's manifest drift detection and "
          "unanswered-review check each correctly fire on their real failure case and "
          "stay silent on the corresponding healthy case.")


if __name__ == "__main__":
    run()
