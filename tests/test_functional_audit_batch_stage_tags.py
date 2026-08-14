"""Functional audit: batch_stage_tags (tools/api_server/main.py, POST /api/batch/stage-tags).

CLAUDE.md's autonomy boundaries say: "any bulk edit touching more than 10
listings" requires Scott confirming scope first. This test checks whether
batch_stage_tags actually enforces any such cap, or whether it will
silently stage tag-fix actions for an unbounded number of listings in one
call with no confirmation step at all.

Read-only audit: mocks every external boundary (Etsy client / listings
fetch, Claude tag generation) and runs against a disposable temp sqlite DB.
No application code is modified.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_batch_stage_tags_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def _fake_listing(lid: int) -> dict:
    # Fewer than 13 tags so every listing qualifies for a tag fix.
    return {
        "listing_id": lid,
        "title": f"Fake Listing {lid}",
        "price": 9.99,
        "state": "active",
        "tags": ["digital planner", "goodnotes planner"],
    }


def _fake_tag_results(listings: list[dict]) -> list[dict]:
    # A valid, gate-passing 13-tag set for every listing handed to us —
    # mirrors what _generate_tags_for_listings would return on success.
    valid_tags = [f"tag{i}" for i in range(13)]
    return [{"listing_id": l["listing_id"], "tags": list(valid_tags)} for l in listings]


def test_batch_stage_tags_has_no_batch_size_cap_or_confirmation():
    """Feed it 50 under-tagged active listings (well above CLAUDE.md's 10-listing
    bulk-edit confirmation threshold) and confirm whether it refuses / requires
    confirmation, or silently stages all 50."""
    n = 50
    fake_listings = [_fake_listing(1000 + i) for i in range(n)]

    with patch.object(server, "ANTHROPIC_KEY", "fake-key-for-audit"), \
         patch.object(server, "_listings_sync", return_value={"listings": fake_listings}), \
         patch.object(server, "_generate_tags_for_listings", side_effect=lambda to_fix: _fake_tag_results(to_fix)):

        result = asyncio.run(server.batch_stage_tags(_token="test"))

    check(isinstance(result, dict), f"expected dict result, got {type(result)}")
    staged = result.get("staged")
    total_checked = result.get("total_checked")

    print(f"[audit] batch_stage_tags result for n={n} under-tagged listings: {result}")

    # The actual spec under test (CLAUDE.md's autonomy boundary): "any bulk
    # edit touching more than 10 listings" requires Scott confirming scope
    # BEFORE it runs -- the sibling stage_batch_price_update enforces this
    # concretely with a hard 5-listing cap and a refusal message. So a
    # correct batch_stage_tags should NOT silently stage tag-fix actions for
    # all 50 under-tagged listings from a single no-argument, no-confirmation
    # call. If it does, that's the bug.
    check(
        staged <= 10,
        f"BUG: batch_stage_tags staged {staged} of {n} under-tagged listings in a single call "
        "with no confirmation parameter and no batch-size cap of any kind. CLAUDE.md requires "
        "Scott confirm scope before any bulk edit touching more than 10 listings, and the "
        "sibling stage_batch_price_update enforces exactly this with a hard 5-listing cap "
        "('Refused: N listing_ids exceeds the 5-listing cap ...'). batch_stage_tags has no "
        "equivalent gate -- it takes zero request parameters and stages every fetched "
        "under-tagged active listing unconditionally.",
    )

    # Confirm the actions were actually persisted to the (temp) action queue,
    # i.e. this isn't merely a dry-run count -- real pending approvals were
    # created in one shot, one real DB write per listing, with no confirmation step.
    pending = server.db.list_actions(status="pending") if hasattr(server.db, "list_actions") else None
    if pending is not None:
        tag_fix_pending = [a for a in pending if a.get("type") == "update_tags"]
        check(
            len(tag_fix_pending) <= 10,
            f"BUG: {len(tag_fix_pending)} real pending update_tags actions were enqueued to the "
            f"Action Center DB from a single unconfirmed call touching {n} listings.",
        )


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
    print(
        "FUNCTIONAL AUDIT TESTS OK -- batch_stage_tags enforces a batch-size cap/confirmation "
        "step consistent with CLAUDE.md's >10-listing bulk-edit boundary."
    )


if __name__ == "__main__":
    run()
