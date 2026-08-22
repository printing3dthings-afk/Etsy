#!/usr/bin/env python3
"""
Tests for tools/trademark_screening.py (2026-08-20) -- advisory pre-publish
trademark screening via Goalie IP's USPTO search API, added as part of
"make Frank smarter/more independent" work. Directly addresses a real,
already-documented risk in CLAUDE.md's Suspension Triggers section:
"Trademark terms in titles/tags — even accidental use triggers shop
quality score penalty affecting ALL listings," which had no automated
check anywhere in this codebase before this module.

Covers:
  1. is_configured() reflects GOALIEIP_API_KEY presence.
  2. Not configured -> screen_listing_content() is a clean no-op
     ({"configured": False, ...}), never makes a network call.
  3. Configured + no live matches -> {"configured": True, "flags": []}.
  4. Configured + a live match -> flagged with owner/class/registration
     info; a dead/abandoned status code match is NOT flagged.
  5. Title phrases are split on commas (this shop's title convention) and
     deduped against tags before screening -- no duplicate API calls for
     the same phrase.
  6. A network failure partway through returns whatever was checked so
     far plus a non-None error, never raises and never silently discards
     the partial results.

Mocks requests.post -- no live Goalie IP calls, no network needed.

Run: python tests/test_trademark_screening.py
"""
import os
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools",):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import trademark_screening as ts  # noqa: E402
import requests  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_response(data):
    resp = mock.Mock()
    resp.raise_for_status = mock.Mock()
    resp.json = mock.Mock(return_value={"data": data})
    return resp


def test_is_configured_reflects_env_var():
    with mock.patch.dict(os.environ, {"GOALIEIP_API_KEY": ""}, clear=False):
        check(ts.is_configured() is False, "empty key must report not configured")
    with mock.patch.dict(os.environ, {"GOALIEIP_API_KEY": "gip_live_abc123"}, clear=False):
        check(ts.is_configured() is True, "a real-looking key must report configured")


def test_not_configured_is_a_clean_noop_no_network_call():
    with mock.patch.dict(os.environ, {"GOALIEIP_API_KEY": ""}, clear=False):
        with mock.patch("requests.post") as mock_post:
            result = ts.screen_listing_content(title="Nike Air Wall Art, Instant Download", tags=["nike shoe art"])
        check(mock_post.called is False, "must never call the network when not configured")
    check(result == {"configured": False, "checked": [], "flags": [], "error": None},
          f"unexpected result when not configured: {result}")


def test_configured_no_matches_returns_clean_result():
    with mock.patch.dict(os.environ, {"GOALIEIP_API_KEY": "gip_live_abc123"}, clear=False):
        with mock.patch("requests.post", return_value=_fake_response([])):
            result = ts.screen_listing_content(title="Lemon Window Art, Instant Download", tags=["kitchen wall art"])
    check(result["configured"] is True, f"must report configured=True: {result}")
    check(result["flags"] == [], f"no matches must mean no flags: {result}")
    check(result["error"] is None, f"a clean run must have no error: {result}")
    check(len(result["checked"]) > 0, "must record what was actually checked")


def test_live_match_is_flagged_dead_match_is_not():
    live_record = {
        "ownerName": "Nike, Inc.", "currentStatusCode": "700",
        "internationalClasses": ["025"], "registrationNumber": "6789012",
        "goodsAndServices": "Athletic footwear",
    }
    dead_record = {
        "ownerName": "Some Defunct Co.", "currentStatusCode": "200",  # abandoned
        "internationalClasses": ["025"], "registrationNumber": "1111111",
        "goodsAndServices": "N/A",
    }
    with mock.patch.dict(os.environ, {"GOALIEIP_API_KEY": "gip_live_abc123"}, clear=False):
        def fake_post(url, headers=None, json=None, timeout=None):
            if json["markLiteral"] == "NIKE":
                return _fake_response([live_record])
            return _fake_response([dead_record])
        with mock.patch("requests.post", side_effect=fake_post):
            result = ts.screen_listing_content(title="NIKE", tags=["dead brand tag"])
    check(len(result["flags"]) == 1, f"expected exactly 1 flag (the live match), got {result['flags']}")
    flag = result["flags"][0]
    check(flag["phrase"] == "NIKE", f"wrong phrase flagged: {flag}")
    check(flag["matches"][0]["owner"] == "Nike, Inc.", f"owner not carried through: {flag}")
    check(flag["matches"][0]["registration_number"] == "6789012", f"registration number not carried through: {flag}")


def test_title_phrases_split_on_commas_and_deduped_against_tags():
    seen_phrases = []
    with mock.patch.dict(os.environ, {"GOALIEIP_API_KEY": "gip_live_abc123"}, clear=False):
        def fake_post(url, headers=None, json=None, timeout=None):
            seen_phrases.append(json["markLiteral"])
            return _fake_response([])
        with mock.patch("requests.post", side_effect=fake_post):
            ts.screen_listing_content(
                title="Lemon Window Art, Kitchen Wall Decor, Instant Download",
                tags=["kitchen wall decor", "boho art"],  # "kitchen wall decor" duplicates a title phrase
            )
    check(seen_phrases.count("Kitchen Wall Decor") + seen_phrases.count("kitchen wall decor") == 1,
          f"a phrase appearing in both title and tags must be screened once, not twice: {seen_phrases}")
    check("Lemon Window Art" in seen_phrases, f"title phrases must be split on commas: {seen_phrases}")
    check("Instant Download" in seen_phrases, f"every comma segment must be checked: {seen_phrases}")
    check("boho art" in seen_phrases, f"tags must be checked too: {seen_phrases}")


def test_network_failure_returns_partial_results_not_a_crash():
    with mock.patch.dict(os.environ, {"GOALIEIP_API_KEY": "gip_live_abc123"}, clear=False):
        def fake_post(url, headers=None, json=None, timeout=None):
            if json["markLiteral"] == "First Phrase":
                return _fake_response([])
            raise requests.exceptions.ConnectionError("network down")
        with mock.patch("requests.post", side_effect=fake_post):
            result = ts.screen_listing_content(title="First Phrase, Second Phrase")
    check(result["configured"] is True, f"must still report configured=True: {result}")
    check(result["checked"] == ["First Phrase"], f"must keep whatever succeeded before the failure: {result}")
    check(result["error"] is not None, "a network failure must be surfaced, never silently swallowed")
    check("network down" in result["error"], f"error message must be informative: {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TRADEMARK SCREENING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TRADEMARK SCREENING TESTS OK — screen_listing_content() no-ops cleanly when unconfigured, "
          "correctly flags only live/registered exact matches (never dead/abandoned ones), dedupes "
          "title/tag phrase overlap, and preserves partial results on a mid-screen network failure "
          "instead of crashing or silently discarding what was already checked.")


if __name__ == "__main__":
    run()
