"""
Tests for _reconcile_etsy_tokens() (Frank upgrade Wave 1, reliability item 7,
2026-07-17) — the mechanism CLAUDE.md flags as needing Scott's manual re-run
every 90 days, and the one that caused the 2026-06-17 "landmine": Etsy rotates
the refresh token on every use and invalidates the old one, so if the server
refreshed a token before a Railway restart, the re-injected env var is a dead
token and the next refresh 401s with invalid_grant. This function restores the
rotated token from the durable DB at boot instead — but ONLY when it's
provably a forward rotation of the *current* env token (matched via
parent_refresh_token lineage), so a genuine manual re-authorization
(tools/etsy_oauth.py) always wins over a stale DB row. That "only when
provably forward" branch had zero test coverage before this.

Self-contained, same pattern as tests/test_produce_qc.py. Run:
    python tests/test_etsy_token_reconcile.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_oauth_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "oauth-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402 — this import itself already calls
                        # _reconcile_etsy_tokens() once; each test below calls
                        # it again after seeding its own DB/env state, so that
                        # first uncontrolled call is irrelevant to what's checked.
import db  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _reset_db_tokens_table() -> None:
    conn = db._connect()
    try:
        conn.execute("DELETE FROM etsy_tokens")
        conn.commit()
    finally:
        conn.close()


def _set_env(access: str | None, refresh: str | None) -> None:
    if access is None:
        os.environ.pop("ETSY_ACCESS_TOKEN", None)
    else:
        os.environ["ETSY_ACCESS_TOKEN"] = access
    if refresh is None:
        os.environ.pop("ETSY_REFRESH_TOKEN", None)
    else:
        os.environ["ETSY_REFRESH_TOKEN"] = refresh


def test_no_stored_row_is_a_noop():
    _reset_db_tokens_table()
    _set_env("env-access-1", "env-refresh-1")
    server._reconcile_etsy_tokens()
    check(os.environ.get("ETSY_ACCESS_TOKEN") == "env-access-1",
          "with no DB row at all, env access token must be left untouched")
    check(os.environ.get("ETSY_REFRESH_TOKEN") == "env-refresh-1",
          "with no DB row at all, env refresh token must be left untouched")


def test_env_matches_stored_refresh_directly_restores_from_db():
    # The simple case: env still holds exactly the token the DB has too (no
    # rotation happened since it was last persisted) -- restoring is a no-op
    # in effect, but exercises the "matches stored.refresh_token" branch.
    _reset_db_tokens_table()
    db.save_etsy_tokens(access_token="db-access-current", refresh_token="shared-refresh-token")
    _set_env("stale-env-access", "shared-refresh-token")
    server._reconcile_etsy_tokens()
    check(os.environ.get("ETSY_ACCESS_TOKEN") == "db-access-current",
          "env refresh matching stored.refresh_token should restore the DB's access token")
    check(os.environ.get("ETSY_REFRESH_TOKEN") == "shared-refresh-token",
          "env refresh matching stored.refresh_token should restore the DB's refresh token")


def test_env_matches_parent_lineage_restores_the_rotated_token():
    # THE actual bug this function exists to fix: the env var still has the OLD
    # (now-invalid) refresh token from before a rotation; the DB has the NEWER
    # rotated token with parent_refresh_token pointing back to the old one.
    # This must be recognized as a forward rotation and restore the new token.
    _reset_db_tokens_table()
    db.save_etsy_tokens(
        access_token="db-access-rotated", refresh_token="db-refresh-rotated",
        parent_refresh_token="old-env-refresh-token",
    )
    _set_env("dead-env-access", "old-env-refresh-token")
    server._reconcile_etsy_tokens()
    check(os.environ.get("ETSY_ACCESS_TOKEN") == "db-access-rotated",
          "env refresh matching stored.parent_refresh_token (a rotation) should restore the new access token")
    check(os.environ.get("ETSY_REFRESH_TOKEN") == "db-refresh-rotated",
          "env refresh matching stored.parent_refresh_token (a rotation) should restore the new refresh token")


def test_env_refresh_unrelated_to_stored_lineage_is_left_alone():
    # A genuine manual re-authorization (tools/etsy_oauth.py + a fresh dashboard
    # update) must always win over a stale DB row from before that re-auth --
    # the env token here matches NEITHER stored.refresh_token NOR
    # stored.parent_refresh_token, so it must be treated as fresh and untouched.
    _reset_db_tokens_table()
    db.save_etsy_tokens(
        access_token="db-access-old", refresh_token="db-refresh-old",
        parent_refresh_token="some-older-refresh-token",
    )
    _set_env("brand-new-manual-reauth-access", "brand-new-manual-reauth-refresh")
    server._reconcile_etsy_tokens()
    check(os.environ.get("ETSY_ACCESS_TOKEN") == "brand-new-manual-reauth-access",
          "a fresh manual re-authorization's access token must never be overwritten by a stale DB row")
    check(os.environ.get("ETSY_REFRESH_TOKEN") == "brand-new-manual-reauth-refresh",
          "a fresh manual re-authorization's refresh token must never be overwritten by a stale DB row")


def test_env_matches_a_two_generations_back_parent_still_restores():
    # Bug fixed 2026-07-18: parent_refresh_token used to store only the
    # IMMEDIATE parent, overwritten on every rotation -- so if the server
    # reactively rotated A->B->C without a restart in between, the DB row's
    # "parent" would end up as B only, silently losing A from history. If
    # Railway then re-injected the ORIGINAL stale env var A (from before any
    # rotation happened), the old code would misidentify it as a genuine
    # fresh manual re-authorization and leave the already-invalidated dead
    # token A in place -- the exact 401 invalid_grant landmine this whole
    # mechanism exists to prevent. save_etsy_tokens() now accumulates a full
    # lineage list instead of overwriting a single parent, so this must
    # correctly recognize A even 2 rotations back and restore C.
    _reset_db_tokens_table()
    db.save_etsy_tokens(access_token="access-A", refresh_token="A")          # initial state
    db.save_etsy_tokens(access_token="access-B", refresh_token="B", parent_refresh_token="A")  # rotation 1: A->B
    db.save_etsy_tokens(access_token="access-C", refresh_token="C", parent_refresh_token="B")  # rotation 2: B->C
    _set_env("dead-access-A", "A")  # Railway re-injects the original, now-twice-stale token
    server._reconcile_etsy_tokens()
    check(os.environ.get("ETSY_ACCESS_TOKEN") == "access-C",
          "env matching a 2-generations-back parent should still restore the current access token")
    check(os.environ.get("ETSY_REFRESH_TOKEN") == "C",
          "env matching a 2-generations-back parent should still restore the current refresh token")


def test_a_broken_db_read_never_crashes_the_caller():
    # _reconcile_etsy_tokens() runs unconditionally at module import time (see
    # main.py) -- if db.get_etsy_tokens() ever raised, that would crash the
    # whole server on boot. Confirm it's caught and swallowed instead.
    saved_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = "/nonexistent/directory/that/cannot/exist/hub.db"
    try:
        server._reconcile_etsy_tokens()  # must not raise
        check(True, "unreachable if it raised")
    except Exception as exc:  # noqa: BLE001
        check(False, f"_reconcile_etsy_tokens() must never raise, even on a broken DB path, got: {exc}")
    finally:
        if saved_path is not None:
            os.environ["DB_PATH"] = saved_path
        else:
            os.environ.pop("DB_PATH", None)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ETSY TOKEN RECONCILE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ETSY TOKEN RECONCILE TESTS OK — no-op/direct-match/rotation-lineage/"
          "fresh-reauth-wins/never-crashes-on-broken-db all verified.")


if __name__ == "__main__":
    run()
