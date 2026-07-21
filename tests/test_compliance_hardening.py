"""
Tests for the SOC 2 / HIPAA / GDPR compliance hardening pass (2026-07-18).
HIPAA needed no engineering work (confirmed not applicable — see
data/knowledge_base/compliance_notes.md); this covers the GDPR/SOC-2-motivated
changes:

  1. Etsy OAuth tokens (db.py's etsy_tokens table) are encrypted at rest when
     TOKEN_ENCRYPTION_KEY is set, transparently decrypt back to plaintext for
     callers, and a pre-existing plaintext row (the migration case) still
     reads correctly without any manual migration step.
  2. Buyer-referencing local artifacts (data/message_drafts/*.json,
     data/notified_orders.json) are pruned on a retention window instead of
     growing forever (_prune_buyer_data_retention in main.py).
  3. data/notified_orders.json is gitignored (it was untracked but unprotected
     before this pass).
  4. The privacy policy no longer makes the false "no personal data...
     collected or retained" claim it used to.

Run: python tests/test_compliance_hardening.py
"""
import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_compliance_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "compliance-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import db as dbmod  # noqa: E402
import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fresh_key() -> str:
    import nacl.secret
    import nacl.utils
    return base64.b64encode(nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)).decode()


def _reset_tokens_table():
    conn = dbmod._connect()
    try:
        conn.execute("DELETE FROM etsy_tokens")
        conn.commit()
    finally:
        conn.close()
    dbmod._token_enc_warned = False


# ── 1. Token encryption ──────────────────────────────────────────────────────

def test_tokens_stored_plaintext_when_no_key_set():
    _reset_tokens_table()
    os.environ.pop("TOKEN_ENCRYPTION_KEY", None)
    dbmod.save_etsy_tokens("acc-plain-1", "ref-plain-1")
    conn = dbmod._connect()
    try:
        row = conn.execute("SELECT access_token FROM etsy_tokens WHERE id=1").fetchone()
    finally:
        conn.close()
    check(row["access_token"] == "acc-plain-1",
          "with no key set, tokens should be stored in plaintext, same as before this change")
    t = dbmod.get_etsy_tokens()
    check(t["access_token"] == "acc-plain-1", f"round-trip should still return plaintext, got: {t}")


def test_tokens_encrypted_at_rest_when_key_set():
    _reset_tokens_table()
    os.environ["TOKEN_ENCRYPTION_KEY"] = _fresh_key()
    dbmod._token_enc_warned = False
    dbmod.save_etsy_tokens("acc-secret-2", "ref-secret-2", parent_refresh_token="parent-2")
    conn = dbmod._connect()
    try:
        row = conn.execute(
            "SELECT access_token, refresh_token, parent_refresh_token FROM etsy_tokens WHERE id=1"
        ).fetchone()
    finally:
        conn.close()
    check(row["access_token"].startswith("enc:v1:"), f"raw row should be encrypted, got: {row['access_token'][:20]}")
    check("acc-secret-2" not in row["access_token"], "the plaintext token must not appear anywhere in the raw stored value")
    check("ref-secret-2" not in row["refresh_token"], "the plaintext refresh token must not appear in the raw stored value")
    check(row["parent_refresh_token"].startswith("enc:v1:"), "parent_refresh_token should also be encrypted")

    t = dbmod.get_etsy_tokens()
    check(t["access_token"] == "acc-secret-2", f"decrypted access_token should round-trip, got: {t}")
    check(t["refresh_token"] == "ref-secret-2", f"decrypted refresh_token should round-trip, got: {t}")
    # 2026-07-18: parent_refresh_token now stores a JSON-encoded lineage list
    # (see db.parse_token_lineage()'s docstring), not a single plain string --
    # a fresh row's lineage is just the one parent passed in.
    check(dbmod.parse_token_lineage(t["parent_refresh_token"]) == ["parent-2"],
          f"decrypted parent_refresh_token should round-trip as a 1-item lineage, got: {t}")
    os.environ.pop("TOKEN_ENCRYPTION_KEY", None)


def test_legacy_plaintext_row_still_readable_after_key_is_set():
    # Simulates the real migration case: a row saved before TOKEN_ENCRYPTION_KEY
    # existed, then the key gets set later -- must not break existing auth.
    _reset_tokens_table()
    os.environ.pop("TOKEN_ENCRYPTION_KEY", None)
    dbmod.save_etsy_tokens("acc-legacy-3", "ref-legacy-3")
    os.environ["TOKEN_ENCRYPTION_KEY"] = _fresh_key()
    dbmod._token_enc_warned = False
    t = dbmod.get_etsy_tokens()
    check(t["access_token"] == "acc-legacy-3",
          f"a pre-existing plaintext row must still decrypt (pass through) correctly once a key is set, got: {t}")
    os.environ.pop("TOKEN_ENCRYPTION_KEY", None)


def test_missing_key_for_an_encrypted_row_raises_clearly():
    _reset_tokens_table()
    os.environ["TOKEN_ENCRYPTION_KEY"] = _fresh_key()
    dbmod._token_enc_warned = False
    dbmod.save_etsy_tokens("acc-orphaned-4", "ref-orphaned-4")
    os.environ.pop("TOKEN_ENCRYPTION_KEY", None)
    dbmod._token_enc_warned = False
    try:
        dbmod.get_etsy_tokens()
        check(False, "reading an encrypted row with no key available should raise, not silently return garbage")
    except RuntimeError as exc:
        check("TOKEN_ENCRYPTION_KEY" in str(exc), f"error should name the missing env var, got: {exc}")


# ── 2. Buyer-data retention pruning ──────────────────────────────────────────

def test_prune_deletes_old_draft_files_keeps_recent():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        drafts_dir = tmp_root / "data" / "message_drafts"
        drafts_dir.mkdir(parents=True)
        old_file = drafts_dir / "2026-01-01_drafts.json"
        recent_file = drafts_dir / "2026-07-17_drafts.json"
        old_file.write_text("[]")
        recent_file.write_text("[]")
        old_ts = time.time() - (100 * 86400)
        os.utime(old_file, (old_ts, old_ts))

        with patch.object(server, "ROOT", tmp_root):
            result = server._prune_buyer_data_retention()

        check(not old_file.exists(), "a draft file older than the retention window should be deleted")
        check(recent_file.exists(), "a recent draft file should NOT be deleted")
        check(result["drafts_deleted"] == 1, f"expected 1 deletion reported, got: {result}")


def test_prune_caps_id_only_state_files_by_count():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        data_dir = tmp_root / "data"
        drafts_dir = data_dir / "message_drafts"
        drafts_dir.mkdir(parents=True)
        many_ids = list(range(1, 3001))  # over the _ID_STATE_FILE_MAX_KEPT (2000) cap
        (data_dir / "notified_orders.json").write_text(json.dumps({"notified": many_ids}))
        (drafts_dir / "sent_log.json").write_text(json.dumps({"sent_ids": many_ids}))

        with patch.object(server, "ROOT", tmp_root):
            result = server._prune_buyer_data_retention()

        notified = json.loads((data_dir / "notified_orders.json").read_text())
        sent = json.loads((drafts_dir / "sent_log.json").read_text())
        check(len(notified["notified"]) == server._ID_STATE_FILE_MAX_KEPT,
              f"notified_orders.json should be capped to {server._ID_STATE_FILE_MAX_KEPT}, got {len(notified['notified'])}")
        check(max(notified["notified"]) == 3000, "capping should keep the MOST RECENT (highest) ids, not the oldest")
        check(len(sent["sent_ids"]) == server._ID_STATE_FILE_MAX_KEPT, f"sent_log.json should also be capped, got: {result}")
        check(result["notified_orders_trimmed"] == 1000, f"expected 1000 trimmed, got: {result}")


def test_prune_is_a_safe_noop_on_missing_files():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)  # no data/ dir at all
        with patch.object(server, "ROOT", tmp_root):
            result = server._prune_buyer_data_retention()
        check(result == {"drafts_deleted": 0, "notified_orders_trimmed": 0, "sent_log_trimmed": 0},
              f"missing files/dirs should degrade to a clean no-op, got: {result}")


def test_prune_wired_into_daily_quality_audit_iteration():
    source = (ROOT / "tools" / "api_server" / "main.py").read_text(encoding="utf-8")
    idx_def = source.index("def _prune_buyer_data_retention")
    idx_iteration = source.index("async def _quality_audit_iteration")
    check(0 < idx_def < idx_iteration, "the retention function should be defined before the loop that calls it")
    call_site = source[idx_iteration:idx_iteration + 1600]
    check("await asyncio.to_thread(_prune_buyer_data_retention)" in call_site,
          "the daily quality-audit loop should call the retention pass via asyncio.to_thread "
          "(it does blocking file I/O), near the top of the iteration")


# ── 3. .gitignore coverage ───────────────────────────────────────────────────

def test_notified_orders_json_is_gitignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    check("data/notified_orders.json" in gitignore,
          "data/notified_orders.json should be gitignored so an accidental `git add -A` can't commit it")


# ── 4. Privacy policy accuracy ───────────────────────────────────────────────

def test_privacy_html_no_longer_makes_the_false_claim():
    for rel in ("privacy.html", "tools/api_server/static/privacy.html"):
        html = (ROOT / rel).read_text(encoding="utf-8")
        check("No personal data belonging to customers or third parties is collected or retained" not in html,
              f"{rel} should no longer make this false claim (get_orders/message drafts do touch buyer data)")
        check("buyer name" in html.lower(), f"{rel} should accurately disclose that buyer names are accessed")


def test_privacy_html_copies_stay_identical():
    a = (ROOT / "privacy.html").read_text(encoding="utf-8")
    b = (ROOT / "tools" / "api_server" / "static" / "privacy.html").read_text(encoding="utf-8")
    check(a == b, "the two privacy.html copies must stay byte-identical (main.py serves the static/ copy directly)")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COMPLIANCE HARDENING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COMPLIANCE HARDENING TESTS OK — Etsy tokens encrypt at rest with a clean plaintext "
          "migration path, buyer-referencing local artifacts are pruned on a retention window, "
          "notified_orders.json is gitignored, and the privacy policy no longer makes a false claim.")


if __name__ == "__main__":
    run()
