"""
Tests for the Recurring Complaint / Review Theme Tracker (2026-08-06, idea
6/6 of the "significantly improve Frank" roadmap, second batch).

The rule every test here is really checking: a "theme" is only ever a real
word that appears verbatim in 2+ distinct real negative (<=3 star) reviews
on the same listing -- no LLM summarization, so nothing can be invented.
Every excerpt attached to a finding is the real, unmodified review text it
was found in. And critically: the Growth Brief (a non-PII-flagged endpoint)
must never leak the raw quoted excerpts -- only the generic shared_term and
counts, matching this codebase's PII-gating discipline used everywhere else
(get_orders, draft_review_replies, and now get_review_themes are the only
tools allowed to return real buyer-authored text).

Checks:
  1. _significant_review_terms() -- filters stopwords and short words, only
     keeps real significant terms.
  2. _compute_review_theme_findings(): requires 2+ distinct reviews sharing
     a term on the same listing; picks the most-shared term; excerpts are
     verbatim/unmodified; findings sorted by review_count desc and capped
     at 5; a listing with only 1 negative review, or no shared terms,
     produces no finding; 4-star+ reviews are excluded even if text
     matches.
  3. _compute_review_themes() survives a get_reviews() fetch failure
     (degrades to an honest empty result, never crashes).
  4. GET /api/review-themes serves the durable sidecar once populated, and
     falls through to a live compute on first-ever (empty) sidecar so the
     panel isn't blank for a full week.
  5. get_review_themes is registered in AGENT_TOOLS, dispatches correctly,
     and is a PII-flagged tool.
  6. The Growth Brief's review_theme scoring item never includes the raw
     excerpts field -- only shared_term/counts (the PII-leak-avoidance
     invariant).

Run: python tests/test_review_themes.py
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_reviewthemes_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "reviewthemes-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _patched_themes_path():
    """Swap _REVIEW_THEMES_PATH to a throwaway temp file, like
    test_competitor_watch.py does for _COMPETITOR_SNAPSHOTS_PATH -- never
    touch the real data/ sidecar from a test."""
    tmp = tempfile.NamedTemporaryFile(prefix="frank_reviewthemes_sidecar_", suffix=".json", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.unlink()  # start absent, like a fresh install
    return path


def test_significant_review_terms_filters_stopwords_and_short_words():
    terms = server._significant_review_terms("The pages are blurry and the download link doesn't work at all")
    check("blurry" in terms, f"a real significant word should survive, got: {terms}")
    check("download" not in terms, f"'download' is an explicit stopword (generic to this shop), got: {terms}")
    check("link" not in terms, f"'link' is under 5 letters, should be filtered, got: {terms}")
    check("work" not in terms, f"'work' is under 5 letters, should be filtered, got: {terms}")
    check("the" not in terms and "and" not in terms, f"common short filler words must not survive, got: {terms}")


_ID_TO_TITLE = {111: "Lavender Life Planner", 222: "Budget Planner", 333: "Fitness Planner"}


def test_compute_review_theme_findings_requires_two_distinct_reviews():
    reviews = {"results": [
        {"listing_id": 111, "rating": 2, "review": "The pages are blurry and hard to read on my iPad."},
    ]}
    findings = server._compute_review_theme_findings(reviews, _ID_TO_TITLE)
    check(findings == [], f"a single negative review can never be a 'recurring' theme, got: {findings}")


def test_compute_review_theme_findings_picks_shared_term_and_verbatim_excerpts():
    reviews = {"results": [
        {"listing_id": 111, "rating": 2, "review": "The pages are blurry when I zoom in on GoodNotes."},
        {"listing_id": 111, "rating": 1, "review": "Very blurry text, disappointed with the quality."},
        {"listing_id": 111, "rating": 5, "review": "This is blurry too but I loved it anyway!"},  # 5-star, excluded
        {"listing_id": 222, "rating": 3, "review": "Totally unrelated complaint about shipping speed."},
    ]}
    findings = server._compute_review_theme_findings(reviews, _ID_TO_TITLE)
    check(len(findings) == 1, f"only listing 111 has 2+ distinct negative reviews sharing a term, got: {findings}")
    f = findings[0]
    check(f["listing_id"] == 111, f"got: {f}")
    check(f["shared_term"] == "blurry", f"got: {f}")
    check(f["review_count"] == 2, f"exactly 2 negative reviews mention 'blurry' (the 5-star one is excluded), got: {f}")
    check(f["total_negative_reviews"] == 2, f"got: {f}")
    texts = {e["text"] for e in f["excerpts"]}
    check("The pages are blurry when I zoom in on GoodNotes." in texts,
          f"excerpt text must be the real unmodified review text, got: {texts}")
    check("Very blurry text, disappointed with the quality." in texts, f"got: {texts}")
    check(all(e["rating"] in (1, 2) for e in f["excerpts"]), f"excerpt ratings must be the real ratings, got: {f['excerpts']}")


def test_compute_review_theme_findings_sorted_and_capped_at_five():
    reviews_results = []
    # 7 listings, each with a distinct shared term appearing in a different
    # number of reviews (2..8) so ranking + the cap-at-5 are both exercised.
    for i, count in enumerate([2, 3, 4, 5, 6, 7, 8], start=1):
        lid = 1000 + i
        term = f"crumpled{i}xyz"  # unique >=5-letter non-stopword term per listing
        for _ in range(count):
            reviews_results.append({"listing_id": lid, "rating": 2, "review": f"The print arrived {term} and damaged."})
    id_to_title = {1000 + i: f"Listing {1000+i}" for i in range(1, 8)}
    findings = server._compute_review_theme_findings({"results": reviews_results}, id_to_title)
    check(len(findings) == 5, f"must cap at 5 findings, got {len(findings)}")
    counts = [f["review_count"] for f in findings]
    check(counts == sorted(counts, reverse=True), f"findings must be sorted by review_count desc, got: {counts}")
    check(counts[0] == 8, f"the listing with the most shared-term reviews (8) should rank first, got: {counts}")


def test_compute_review_theme_findings_no_shared_terms_produces_no_finding():
    reviews = {"results": [
        {"listing_id": 111, "rating": 2, "review": "Wrong color scheme entirely, expected lavender."},
        {"listing_id": 111, "rating": 1, "review": "Missing several important sections I paid for."},
    ]}
    findings = server._compute_review_theme_findings(reviews, _ID_TO_TITLE)
    check(findings == [], f"two negative reviews with no overlapping significant term must produce no finding, got: {findings}")


def test_compute_review_themes_survives_reviews_fetch_failure():
    with patch.object(server, "EtsyAPIClient") as mock_client_cls:
        mock_client_cls.return_value.get_reviews.side_effect = RuntimeError("Etsy is down")
        result = asyncio.run(server._compute_review_themes())
    check(result["findings"] == [], f"a reviews-fetch failure must degrade to an empty result, never crash: {result}")
    check("generated_at" in result, f"the degraded response should still be well-formed: {result}")


def test_get_review_themes_endpoint_serves_sidecar_or_falls_back():
    path = _patched_themes_path()
    orig = server._REVIEW_THEMES_PATH
    server._REVIEW_THEMES_PATH = path
    try:
        # First call: sidecar is empty/absent -> must fall through to a live compute.
        fake_live = {"findings": [{"listing_id": 111, "title": "X", "shared_term": "blurry",
                                    "review_count": 2, "total_negative_reviews": 2, "excerpts": []}],
                     "generated_at": "2026-08-06T00:00:00+00:00"}

        async def _fake_compute():
            return fake_live
        with patch.object(server, "_compute_review_themes", _fake_compute):
            r1 = asyncio.run(server.get_review_themes(_token="test"))
        check(r1 == fake_live, f"first-ever load with empty sidecar must fall through to a live compute, got: {r1}")

        # Sidecar now populated on disk (written by _review_theme_iteration inside the fallback path).
        check(path.exists(), "the fallback path must persist its result to the sidecar")

        # Second call: sidecar has a generated_at -> must serve straight from disk, not recompute.
        async def _fake_compute_should_not_be_called():
            raise AssertionError("must not recompute once the sidecar is populated")
        with patch.object(server, "_compute_review_themes", _fake_compute_should_not_be_called):
            r2 = asyncio.run(server.get_review_themes(_token="test"))
        check(r2["findings"][0]["shared_term"] == "blurry", f"must serve the persisted sidecar content, got: {r2}")
    finally:
        server._REVIEW_THEMES_PATH = orig
        if path.exists():
            path.unlink()


def test_tool_registered_and_dispatches():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("get_review_themes" in names, "get_review_themes must be registered in AGENT_TOOLS")
    fake_result = {"findings": [], "generated_at": None}

    async def _fake_compute():
        return fake_result
    with patch.object(server, "_compute_review_themes", _fake_compute):
        result = server._execute_agent_tool("get_review_themes", {})
    check(result == fake_result, f"got: {result}")


def test_pii_tools_membership():
    check("get_review_themes" in server._PII_TOOLS,
          "get_review_themes returns real buyer-authored review excerpts and must be PII-flagged")


def test_growth_brief_review_theme_item_never_leaks_raw_excerpts():
    findings = [{
        "listing_id": 111, "title": "Lavender Life Planner", "shared_term": "blurry",
        "review_count": 3, "total_negative_reviews": 4,
        "excerpts": [{"rating": 1, "text": "This buyer's real name and address are in here: Jane Doe, 123 Main St"}],
    }]
    items = server._score_growth_brief_items(
        ads={"used": False}, cogs={"used": False}, star_seller={"status": "on_track"},
        actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
        competitor_drift_items=None, review_theme_findings=findings,
    )
    review_items = [it for it in items if it["category"] == "review_theme"]
    check(len(review_items) == 1, f"expected exactly one review_theme item, got: {items}")
    it = review_items[0]
    check("excerpts" not in it, f"raw excerpts must never leak into the non-PII-flagged Growth Brief, got: {it}")
    check("Jane Doe" not in json.dumps(it), f"real buyer-identifying text must never appear in the Growth Brief item, got: {it}")
    check("blurry" in it.get("title", "") + it.get("detail", ""),
          f"the generic shared_term itself is fine to surface, got: {it}")
    check(it["est_dollar_impact"] is None, f"a review-theme finding must never carry a fabricated dollar estimate, got: {it}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("REVIEW THEMES TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("REVIEW THEMES TESTS OK — every recurring-theme finding traces to 2+ real distinct negative reviews "
          "sharing a real verbatim term, excerpts are never modified, and raw buyer text never leaks into the "
          "non-PII-flagged Growth Brief.")


if __name__ == "__main__":
    run()
