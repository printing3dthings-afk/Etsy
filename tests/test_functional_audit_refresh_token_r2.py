"""Functional audit ROUND 2: POST /api/core/refresh-etsy-token
(core_refresh_etsy_token, tools/api_server/main.py).

Round 1 confirmed+fixed: a successful refresh now calls db.save_etsy_tokens()
immediately instead of relying solely on the background _token_sync_loop.

This round targets what that fix left unguarded. The persistence call the
round-1 fix added:

    if new_access and new_refresh:
        await asyncio.to_thread(db.save_etsy_tokens, new_access, new_refresh, parent_refresh_token)
    tokens = await asyncio.to_thread(db.get_etsy_tokens)
    return {"ok": True, "updated_at": (tokens or {}).get("updated_at")}

is NOT wrapped in try/except anywhere in core_refresh_etsy_token. Per this
repo's own api-conventions.md ("Wrap every external call ... in try/except
and raise HTTPException(status_code=..., detail=<specific, actionable
text>) -- never a bare exception that becomes a generic 500") and
code-style.md ("Errors: never a bare 500, never a silent swallow"), any
failure of the DB write itself (disk full, `sqlite3.OperationalError:
database is locked`, permissions error on the /data volume, etc.) is a real,
foreseeable failure mode for exactly the kind of external call these rules
exist for. Today it is NOT handled at all: it propagates as a raw unhandled
exception out of the route.

The practical consequence is worse than a generic 500: the real Etsy OAuth
refresh_access_token() call already SUCCEEDED by this point (a fresh access
token is live in os.environ and immediately usable by this process for
Etsy API calls) -- but the caller of this endpoint receives an opaque crash
and has no way to know the refresh actually worked. This is the inverse of
a silent-failure bug: instead of silently reporting success while
persistence quietly fails (what the audit prompt hypothesized), the current
code hard-crashes on a persistence hiccup even though the operation the
caller asked for ("refresh my access token") genuinely succeeded.

No real network call is made anywhere in this file -- EtsyAPIClient is
mocked entirely, and db.save_etsy_tokens/db.get_etsy_tokens are patched to
simulate a disk-full / DB-locked condition without touching any real
database file.
"""
import os
import sys
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_r2_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-r2-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from starlette.requests import Request  # noqa: E402
from fastapi import HTTPException  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_request() -> Request:
    scope = {"type": "http", "method": "POST", "path": "/api/core/refresh-etsy-token",
              "headers": [], "query_string": b""}
    return Request(scope)


class _FakeClientSucceeds:
    """Mirrors the real EtsyAPIClient.refresh_access_token() success path:
    the Etsy OAuth call already succeeded and rotated the live credential
    in os.environ before this class returns."""

    def __init__(self, *a, **kw):
        pass

    def refresh_access_token(self):
        os.environ["ETSY_ACCESS_TOKEN"] = "live-and-already-usable-access-token"
        os.environ["ETSY_REFRESH_TOKEN"] = "live-and-already-usable-refresh-token"
        return True


def test_db_write_failure_after_successful_etsy_refresh_should_not_be_a_bare_crash():
    """Regression test for a confirmed 2026-08-14 (round 2) bug: the Etsy-side
    refresh genuinely succeeded (mirrors a disk-full or `database is locked`
    condition hitting db.save_etsy_tokens() -- a real, foreseeable failure for
    a SQLite file on a Railway volume), but it used to propagate as a bare/
    opaque exception (no try/except anywhere in the route), violating this
    repo's api-conventions.md. Fixed to log-and-swallow, returning
    {"ok": True, "updated_at": None} since the Etsy refresh itself already
    succeeded and the background _token_sync_loop retries persistence.
    """
    class _FakeDBOperationalError(Exception):
        pass

    with patch.object(server, "EtsyAPIClient", _FakeClientSucceeds), \
         patch.object(server.db, "save_etsy_tokens",
                      side_effect=_FakeDBOperationalError("database is locked")):
        try:
            result = asyncio.run(server.core_refresh_etsy_token(_fake_request(), _token="test"))
            # 2026-08-14: fixed to tolerate a persistence failure -- the Etsy
            # refresh itself already succeeded (a live token is in os.environ),
            # so this now logs-and-swallows rather than crashing, matching
            # test 2's already-correct expectation for the same failure class.
            check(result.get("ok") is True,
                  f"if no exception is raised, expect ok=True since the refresh itself "
                  f"genuinely succeeded, got {result!r}")
            check(result.get("updated_at") is None,
                  f"a swallowed persistence failure must not claim a fresh updated_at "
                  f"timestamp that was never actually written, got {result!r}")
        except HTTPException as exc:
            # This would be the well-behaved outcome per api-conventions.md.
            check(exc.status_code in (500, 502),
                  f"expected a 5xx actionable HTTPException, got status {exc.status_code}")
            check(len(str(exc.detail)) > 10,
                  f"expected an actionable detail message, got: {exc.detail!r}")
        except _FakeDBOperationalError as exc:
            # This is the CONFIRMED bug: the route lets the raw DB exception
            # escape uncaught instead of wrapping it, contradicting
            # api-conventions.md's "never a bare exception that becomes a
            # generic 500" rule -- and it masks that the Etsy-side refresh
            # (the thing the caller actually asked for) already succeeded:
            # os.environ now holds a live, usable access token that the
            # caller has no way to learn about from this crash.
            check(False,
                  "CONFIRMED BUG: core_refresh_etsy_token lets db.save_etsy_tokens()'s raw "
                  f"exception ({exc!r}) escape uncaught instead of wrapping it in an actionable "
                  "HTTPException per api-conventions.md's error-handling rule. Worse: the real "
                  "Etsy refresh already succeeded by this point (os.environ['ETSY_ACCESS_TOKEN'] "
                  f"== {os.environ.get('ETSY_ACCESS_TOKEN')!r}, a live usable token) -- the "
                  "caller receives an opaque crash with no indication the operation it asked "
                  "for actually worked.")
        except Exception as exc:  # noqa: BLE001
            check(False, f"expected HTTPException, got an unexpected unwrapped exception type "
                          f"{type(exc).__name__}: {exc!r}")


def test_db_readback_failure_after_successful_save_should_not_be_a_bare_crash():
    """Even if db.save_etsy_tokens() itself succeeds, the immediately
    following db.get_etsy_tokens() read-back (used only to report
    `updated_at` back to the caller) is equally unguarded. A transient read
    failure there (SQLite `database is locked` from a concurrent writer,
    for instance) should not be able to turn an otherwise fully successful
    forced refresh (Etsy call ok, DB write ok) into a hard crash just to
    report a timestamp."""

    class _FakeReadError(Exception):
        pass

    with patch.object(server, "EtsyAPIClient", _FakeClientSucceeds), \
         patch.object(server.db, "save_etsy_tokens", return_value=None), \
         patch.object(server.db, "get_etsy_tokens",
                      side_effect=_FakeReadError("database is locked")):
        try:
            result = asyncio.run(server.core_refresh_etsy_token(_fake_request(), _token="test"))
            check(result.get("ok") is True,
                  f"if no exception is raised, expect ok=True since the refresh itself "
                  f"genuinely succeeded, got {result!r}")
        except HTTPException:
            pass  # well-behaved outcome
        except _FakeReadError as exc:
            check(False,
                  "CONFIRMED BUG: core_refresh_etsy_token lets db.get_etsy_tokens()'s raw "
                  f"exception ({exc!r}) escape uncaught. The Etsy refresh AND the durable "
                  "save both genuinely succeeded by this point -- the only unguarded step left "
                  "is reading back a timestamp to include in the response, yet that alone is "
                  "enough to crash the whole request instead of e.g. returning "
                  "{ok: True, updated_at: None}.")
        except Exception as exc:  # noqa: BLE001
            check(False, f"expected HTTPException or a clean ok=True return, got an unexpected "
                          f"unwrapped exception type {type(exc).__name__}: {exc!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT ROUND 2 TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT ROUND 2 TESTS OK -- core_refresh_etsy_token's persistence step is "
          "properly guarded against its own failure modes.")


if __name__ == "__main__":
    run()
