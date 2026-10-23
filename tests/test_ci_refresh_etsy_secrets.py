"""tools/ci_refresh_etsy_secrets.py never rotates unsynced, and tells the server first.

The Etsy connection died again in October 2026 despite the 2026-06-17 lineage
fix: APP_SECRET_TOKEN had never been set as an Actions secret, so the workflow's
runs rotated their own copy without syncing with the live server. And a failed
GitHub secret write exited before the new pair reached the server.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import ci_refresh_etsy_secrets as r  # noqa: E402

_failures: list[str] = []
BASE = {"ETSY_CLIENT_ID": "cid", "ETSY_REFRESH_TOKEN": "gh-copy", "GH_PAT_SECRETS": "pat",
        "GITHUB_REPOSITORY": "o/r"}


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_refuses_to_rotate_without_the_server():
    with patch.dict(os.environ, BASE, clear=True), \
         patch.object(r, "refresh_etsy_token") as refresh:
        rc = r.main()
    check(rc == 1, f"no APP_SECRET_TOKEN must fail, got {rc}")
    check(not refresh.called, "it must not touch Etsy without syncing with the server")


def test_refuses_when_the_server_cannot_be_read():
    env = dict(BASE, RAILWAY_APP_URL="https://x", APP_SECRET_TOKEN="t")
    with patch.dict(os.environ, env, clear=True), \
         patch.object(r, "fetch_railway_tokens", return_value=None), \
         patch.object(r, "refresh_etsy_token") as refresh:
        rc = r.main()
    check(rc == 1 and not refresh.called, "an unreadable server must stop the rotation")


def test_uses_the_servers_token_and_pushes_before_github():
    env = dict(BASE, RAILWAY_APP_URL="https://x", APP_SECRET_TOKEN="t")
    order = []
    with patch.dict(os.environ, env, clear=True), \
         patch.object(r, "fetch_railway_tokens", return_value={"refresh_token": "live"}), \
         patch.object(r, "refresh_etsy_token", side_effect=lambda c, t: order.append(("refresh", t)) or
                      {"access_token": "A2", "refresh_token": "R2"}), \
         patch.object(r, "push_railway_tokens", side_effect=lambda *a: order.append(("push", a[4]))), \
         patch.object(r, "update_repo_secret", side_effect=RuntimeError("bad PAT")), \
         patch.object(r, "mask_and_export"):
        rc = r.main()
    check(order[:1] == [("refresh", "live")], f"it must rotate the server's token, not its own copy: {order}")
    check(("push", "live") in order, f"the new pair must reach the server even when the GitHub write fails: {order}")
    check(rc == 1, "a failed GitHub write is still reported")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CI ETSY REFRESH TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CI ETSY REFRESH TESTS OK — never rotates unsynced; the server hears of a new token first.")


if __name__ == "__main__":
    run()
