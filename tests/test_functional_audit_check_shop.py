"""
Functional audit of tools/shop_health_check.py::check_shop.

check_shop() is Frank/Scott's core weekly health-check function -- the tool
meant to catch everything else's failures. This audit verifies three of its
real checks actually flag the failure case they claim to catch (not just
pass on the happy path):

  1. Review-average check  -- alerts when shop review_average < 4.9,
     stays silent at/above 4.9.
  2. Photo-count check     -- alerts only for the specific listing(s) below
     the 7-photo minimum, not for listings that meet it.
  3. Hero-art duplicate detection -- flags two listings that share an
     identical hero thumbnail ("WRONG ART", pHash dist=0) while leaving
     visually distinct listings alone.

No real Etsy/network/AI calls are made anywhere in this file: a hand-built
fake client stands in for EtsyAPIClient (check_shop only ever touches
`client.shop_id` and `client._request()`), and `urllib.request.urlopen`
(used internally to download hero thumbnails for perceptual hashing) is
patched to return small in-memory PIL-generated images. The durable
manifest path and weekly-snapshot file are both redirected to a tempdir so
this file never reads or writes the real `data/` tree.
"""

import io
import os
import re
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

import shop_health_check as shc  # noqa: E402
import tools.api_server.db as db_mod  # noqa: E402

from PIL import Image  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


# ─────────────────────────────────────────────────────────────────────────
# Fakes / helpers
# ─────────────────────────────────────────────────────────────────────────

class FakeEtsyClient:
    """Duck-types the only two things check_shop() touches on a real
    EtsyAPIClient: `.shop_id` and `._request(method, path)`. Never makes a
    real HTTP call."""

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


def _image_bytes(rgb):
    """Small real JPEG bytes of a solid color, for _dhash() to hash.

    NOTE: only usable for the *duplicate* case (same bytes reused for both
    listings). A perfectly flat/solid-color image is useless for the
    *distinct* case: _dhash() compares each pixel to its right-hand
    neighbor, and on a solid color every neighbor pair is equal, so EVERY
    solid-color image (regardless of which color) hashes to the same
    all-zero-bits value -- two different solid colors would come back
    pHash dist=0 and look like a false "duplicate art" positive. Use
    _gradient_image_bytes() below for any test needing two genuinely
    distinguishable images.
    """
    im = Image.new("RGB", (16, 16), rgb)
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    return buf.getvalue()


def _gradient_image_bytes(direction="up"):
    """A 16x16 monotonic brightness ramp, left (dark) to right (light) for
    direction="up", or reversed for "down". These two are bitwise-inverse
    under dhash's neighbor-comparison (every column-pair flips sign), which
    gives the maximum possible Hamming distance (64/64) -- an unambiguous
    'genuinely different image' fixture, unlike two solid colors."""
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


def _make_images(n, hero_url, first_rank=1):
    """n listing-image dicts; item 0 carries the hero url the code will
    fetch (rank==1, or images[0] if no image has rank==1)."""
    out = [{"rank": first_rank, "url_570xN": hero_url}]
    for i in range(n - 1):
        out.append({"rank": first_rank + i + 1, "url_570xN": hero_url})
    return out


def _fake_urlopen_factory(url_to_bytes):
    """Returns a stand-in for urllib.request.urlopen keyed by exact URL.
    `url_to_bytes` maps URL -> raw image bytes (see _image_bytes /
    _gradient_image_bytes above)."""
    def _urlopen(url, timeout=10):
        data = url_to_bytes.get(url) or _image_bytes((128, 128, 128))

        class _Resp:
            def read(self_inner):
                return data
        return _Resp()
    return _urlopen


def _run_check_shop(client, url_to_bytes=None):
    """Runs check_shop() with every external boundary mocked, capturing
    and returning (result_dict, stdout_text)."""
    url_to_bytes = url_to_bytes or {}
    tmp_dir = tempfile.TemporaryDirectory()
    try:
        manifest_path = Path(tmp_dir.name) / "listing_image_manifest.json"
        snapshot_path = Path(tmp_dir.name) / "weekly_snapshots.json"

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
        return result, buf.getvalue()
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
# 1. Review-average check
# ─────────────────────────────────────────────────────────────────────────

def test_review_average_alert_fires_when_below_4_9():
    client = FakeEtsyClient(
        shop_id="11111",
        shop=_base_shop(review_average=4.5, review_count=12),
        listings=[],  # keep photo/hero loops trivial for this check
    )
    result, out = _run_check_shop(client)

    check(result is not None, "check_shop returned None for a valid shop response")
    check("Review average 4.5 is below 4.9" in out,
          f"expected the low-review-average alert text in output, got:\n{out}")
    check(result["alerts"] >= 1,
          f"expected alerts>=1 for a 4.5-star shop, got {result['alerts']}")


def test_review_average_does_not_false_positive_at_or_above_4_9():
    # Exactly at the threshold: the check is `< 4.9`, so 4.9 must NOT alert.
    client_at = FakeEtsyClient(
        shop_id="22221",
        shop=_base_shop(review_average=4.9, review_count=12),
        listings=[],
    )
    result_at, out_at = _run_check_shop(client_at)
    check("is below 4.9" not in out_at,
          f"4.9-star shop falsely triggered the below-4.9 alert:\n{out_at}")
    check(result_at["alerts"] == 0,
          f"expected 0 alerts for exactly-4.9 shop, got {result_at['alerts']}")

    # Perfect score: should print the explicit "perfect" confirmation line.
    client_perfect = FakeEtsyClient(
        shop_id="22222",
        shop=_base_shop(review_average=5.0, review_count=12),
        listings=[],
    )
    result_perfect, out_perfect = _run_check_shop(client_perfect)
    check("Perfect 5.0 review average" in out_perfect,
          f"expected perfect-score confirmation line, got:\n{out_perfect}")
    check(result_perfect["alerts"] == 0,
          f"expected 0 alerts for a 5.0-star shop, got {result_perfect['alerts']}")


# ─────────────────────────────────────────────────────────────────────────
# 2. Photo-count check
# ─────────────────────────────────────────────────────────────────────────

def test_photo_count_check_flags_only_the_underfilled_listing():
    url_low = "https://img.example/low.jpg"
    url_ok = "https://img.example/ok.jpg"
    listings = [
        {"listing_id": 111, "title": "Kawaii Planner Low Photos"},
        {"listing_id": 222, "title": "Kawaii Planner Full Photos"},
    ]
    images_by_lid = {
        "111": _make_images(3, url_low),   # below the 7-photo minimum
        "222": _make_images(10, url_ok),   # above the minimum
    }
    client = FakeEtsyClient(
        shop_id="33333",
        shop=_base_shop(),
        listings=listings,
        images_by_lid=images_by_lid,
    )
    # Genuinely distinguishable (opposite-gradient) images so the hero-art
    # duplicate-detector doesn't also fire and pollute the assertions below
    # (that's check #3's job).
    result, out = _run_check_shop(
        client, url_to_bytes={
            url_low: _gradient_image_bytes("up"),
            url_ok: _gradient_image_bytes("down"),
        }
    )

    check(result is not None, "check_shop returned None unexpectedly")
    check("only 3 photos" in out and "[111]" in out,
          f"expected listing 111 (3 photos) to be flagged, got:\n{out}")
    check(result["photo_warnings"] == 1,
          f"expected exactly 1 photo_warning, got {result['photo_warnings']}")

    # Negative half of the same check: the 10-photo listing must NOT appear
    # in the photo-count warning section.
    scan_section = out.split("ACTIVE LISTING SCAN", 1)[1].split("HERO-ART AUDIT", 1)[0]
    check("[222]" not in scan_section,
          f"listing 222 (10 photos, above minimum) was wrongly flagged:\n{scan_section}")


# ─────────────────────────────────────────────────────────────────────────
# 3. Hero-art cross-listing duplicate detection
# ─────────────────────────────────────────────────────────────────────────

def test_hero_art_duplicate_detection_flags_identical_thumbnails():
    same_url = "https://img.example/shared-hero.jpg"
    listings = [
        {"listing_id": 501, "title": "DP1030 ADHD Planner"},
        {"listing_id": 502, "title": "DP1031 Evergreen Planner"},
    ]
    # Both listings' hero image points at the literal same URL/pixels --
    # i.e. the exact same file was uploaded to two different listings,
    # which is exactly the "wrong art" scenario this check exists to catch.
    images_by_lid = {
        "501": _make_images(7, same_url),
        "502": _make_images(7, same_url),
    }
    client = FakeEtsyClient(
        shop_id="44444",
        shop=_base_shop(),
        listings=listings,
        images_by_lid=images_by_lid,
    )
    result, out = _run_check_shop(
        client, url_to_bytes={same_url: _gradient_image_bytes("up")}
    )

    check(result is not None, "check_shop returned None unexpectedly")
    check("WRONG ART" in out,
          f"expected a WRONG ART duplicate-hero alert, got:\n{out}")
    check("[501]" in out and "[502]" in out,
          f"expected both duplicate listing ids named in the warning, got:\n{out}")


def test_hero_art_duplicate_detection_does_not_false_positive_on_distinct_art():
    url_a = "https://img.example/design-a.jpg"
    url_b = "https://img.example/design-b.jpg"
    listings = [
        {"listing_id": 601, "title": "DP1032 Dark Mode Planner"},
        {"listing_id": 602, "title": "DP1033 Teacher Planner"},
    ]
    images_by_lid = {
        "601": _make_images(7, url_a),
        "602": _make_images(7, url_b),
    }
    client = FakeEtsyClient(
        shop_id="55555",
        shop=_base_shop(),
        listings=listings,
        images_by_lid=images_by_lid,
    )
    # Bitwise-inverse gradients -> maximally different (64/64) dhash.
    result, out = _run_check_shop(
        client, url_to_bytes={
            url_a: _gradient_image_bytes("up"),
            url_b: _gradient_image_bytes("down"),
        }
    )

    check(result is not None, "check_shop returned None unexpectedly")
    check("WRONG ART" not in out,
          f"distinct hero art was falsely flagged as a duplicate:\n{out}")


# ─────────────────────────────────────────────────────────────────────────

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
    print("FUNCTIONAL AUDIT TESTS OK -- check_shop's review-average, photo-count, "
          "and hero-art-duplicate checks each correctly flag their real failure "
          "case and stay silent on the corresponding healthy case.")


if __name__ == "__main__":
    run()
