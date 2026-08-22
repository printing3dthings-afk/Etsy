"""
Functional audit: tools/order_notifier.py::_smtp_send_owner_notification

What this verifies:
  1. An SMTP send failure (connection refused, auth error, timeout) is caught,
     logged clearly (not silently swallowed), and the function returns False
     rather than raising or pretending success.
  2. SMTP_USER / SMTP_PASSWORD are read from the environment and used
     correctly (host/port/user/password wired into smtplib.SMTP + login()).
  3. The password never appears in anything printed to stdout, on any code
     path (missing-config, success, or failure) -- this is a real production
     smtplib footgun: smtplib.SMTPAuthenticationError's message frequently
     echoes back server response text, and a careless `print(f"...{exc}...")`
     combined with a password embedded in a wrapped/decorated exception
     object could leak it into logs.

No real network call is made anywhere in this file: smtplib.SMTP is mocked
at the class level and socket.getaddrinfo is mocked so even DNS resolution
never leaves the process.
"""
import io
import os
import smtplib
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_smtp_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import order_notifier as on  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


_SAMPLE_ORDERS = [
    {
        "receipt_id": "12345",
        "buyer_name": "Jane Doe",
        "product_title": "Ultimate Digital Life Planner 2026",
        "product_type": "digital_planner",
        "total": "14.99",
        "ordered_at": "Aug 13, 2026 at 09:00 AM UTC",
        "personal_message": "Hi Jane, thanks for your order!",
        "all_items": ["Ultimate Digital Life Planner 2026"],
    }
]

_SECRET_MARKER = "S3cr3t-P@ssw0rd-MARKER-xyz987"


def _clear_smtp_env():
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"):
        os.environ.pop(k, None)


def test_missing_config_returns_false_no_crash_no_network():
    """No SMTP_USER/SMTP_PASSWORD set -> must NOT attempt any network call,
    must return False (not raise), and must print a clear diagnostic."""
    _clear_smtp_env()
    with patch("order_notifier.smtplib.SMTP") as mock_smtp, \
         patch("order_notifier.socket.getaddrinfo") as mock_dns:
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = on._smtp_send_owner_notification(_SAMPLE_ORDERS, dry_run=False)
        out = buf.getvalue()

    check(result is False, f"expected False when SMTP not configured, got {result!r}")
    check(mock_smtp.call_count == 0, "SMTP() must never be constructed when config is missing")
    check(mock_dns.call_count == 0, "DNS lookup must never happen when config is missing")
    check("not configured" in out.lower() or "skipping" in out.lower(),
          f"expected a clear 'not configured' diagnostic in stdout, got: {out!r}")


def test_empty_orders_returns_true_without_touching_smtp():
    os.environ["SMTP_HOST"] = "smtp.office365.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "shopowner@example.com"
    os.environ["SMTP_PASSWORD"] = _SECRET_MARKER
    with patch("order_notifier.smtplib.SMTP") as mock_smtp:
        result = on._smtp_send_owner_notification([], dry_run=False)
    check(result is True, f"expected True for empty orders list, got {result!r}")
    check(mock_smtp.call_count == 0, "SMTP() must never be constructed for an empty orders list")


def test_dry_run_never_touches_network():
    os.environ["SMTP_HOST"] = "smtp.office365.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "shopowner@example.com"
    os.environ["SMTP_PASSWORD"] = _SECRET_MARKER
    with patch("order_notifier.smtplib.SMTP") as mock_smtp, \
         patch("order_notifier.socket.getaddrinfo") as mock_dns:
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = on._smtp_send_owner_notification(_SAMPLE_ORDERS, dry_run=True)
        out = buf.getvalue()
    check(result is True, f"expected True on dry_run, got {result!r}")
    check(mock_smtp.call_count == 0, "dry_run must never construct smtplib.SMTP")
    check(mock_dns.call_count == 0, "dry_run must never resolve DNS")
    check(_SECRET_MARKER not in out, "password leaked into dry-run stdout")


def test_connection_refused_is_caught_logged_and_returns_false():
    """Simulates a real connection-refused / network failure at the
    socket.getaddrinfo step (this runs BEFORE smtplib.SMTP is even
    constructed in the real function) -- must not propagate, must return
    False, must log something actionable, must never leak the password."""
    os.environ["SMTP_HOST"] = "smtp.office365.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "shopowner@example.com"
    os.environ["SMTP_PASSWORD"] = _SECRET_MARKER

    with patch("order_notifier.socket.getaddrinfo", side_effect=ConnectionRefusedError("[Errno 111] Connection refused")), \
         patch("order_notifier.smtplib.SMTP") as mock_smtp:
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = on._smtp_send_owner_notification(_SAMPLE_ORDERS, dry_run=False)
        out = buf.getvalue()

    check(result is False, f"expected False on connection-refused, got {result!r}")
    check(mock_smtp.call_count == 0, "SMTP object should never be constructed if DNS/connect fails first")
    check("failed" in out.lower(), f"expected a clear failure message in stdout, got: {out!r}")
    check(_SECRET_MARKER not in out, "password leaked into stdout on connection failure")


def test_smtp_auth_failure_is_caught_logged_and_returns_false():
    """Simulates smtplib.SMTPAuthenticationError raised from .login() --
    the realistic 'bad SMTP_PASSWORD in env' production failure mode."""
    os.environ["SMTP_HOST"] = "smtp.office365.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "shopowner@example.com"
    os.environ["SMTP_PASSWORD"] = _SECRET_MARKER

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False
    # Realistic Office365 auth failure text -- server-echoed, never includes
    # our password, but this proves the code doesn't independently append it.
    mock_conn.login.side_effect = smtplib.SMTPAuthenticationError(
        535, b"5.7.3 Authentication unsuccessful"
    )

    with patch("order_notifier.socket.getaddrinfo", return_value=[(None, None, None, None, ("1.2.3.4", 587))]), \
         patch("order_notifier.smtplib.SMTP", return_value=mock_conn) as mock_smtp_cls:
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = on._smtp_send_owner_notification(_SAMPLE_ORDERS, dry_run=False)
        out = buf.getvalue()

    check(result is False, f"expected False on SMTPAuthenticationError, got {result!r}")
    check(mock_smtp_cls.call_count == 1, "SMTP() should have been constructed once")
    check(mock_conn.login.called, "login() should have been attempted")
    check("failed" in out.lower(), f"expected a clear failure message in stdout, got: {out!r}")
    check("535" in out or "Authentication unsuccessful" in out,
          f"expected the underlying SMTP error surfaced for diagnosis, got: {out!r}")
    check(_SECRET_MARKER not in out, "password leaked into stdout on auth failure")


def test_timeout_is_caught_logged_and_returns_false():
    os.environ["SMTP_HOST"] = "smtp.office365.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "shopowner@example.com"
    os.environ["SMTP_PASSWORD"] = _SECRET_MARKER

    with patch("order_notifier.socket.getaddrinfo", return_value=[(None, None, None, None, ("1.2.3.4", 587))]), \
         patch("order_notifier.smtplib.SMTP", side_effect=TimeoutError("timed out")) as mock_smtp_cls:
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = on._smtp_send_owner_notification(_SAMPLE_ORDERS, dry_run=False)
        out = buf.getvalue()

    check(result is False, f"expected False on timeout, got {result!r}")
    check(mock_smtp_cls.call_count == 1, "SMTP() should have been attempted once")
    check("failed" in out.lower(), f"expected a clear failure message in stdout, got: {out!r}")
    check(_SECRET_MARKER not in out, "password leaked into stdout on timeout")


def test_successful_send_uses_env_credentials_correctly_and_returns_true():
    os.environ["SMTP_HOST"] = "smtp.office365.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "shopowner@example.com"
    os.environ["SMTP_PASSWORD"] = _SECRET_MARKER

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False

    with patch("order_notifier.socket.getaddrinfo", return_value=[(None, None, None, None, ("1.2.3.4", 587))]) as mock_dns, \
         patch("order_notifier.smtplib.SMTP", return_value=mock_conn) as mock_smtp_cls:
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = on._smtp_send_owner_notification(_SAMPLE_ORDERS, dry_run=False)
        out = buf.getvalue()

    check(result is True, f"expected True on successful send, got {result!r}")
    check(mock_dns.called, "should resolve host via getaddrinfo (IPv4-forced per module docstring)")
    mock_smtp_cls.assert_called_once()
    args, kwargs = mock_smtp_cls.call_args
    check(args[0] == "1.2.3.4", f"expected SMTP() called with resolved IPv4 addr, got {args!r}")
    check(args[1] == 587, f"expected SMTP() called with port 587, got {args!r}")

    check(mock_conn.starttls.called, "starttls() should have been called (env uses port 587)")
    mock_conn.login.assert_called_once_with("shopowner@example.com", _SECRET_MARKER)
    check(mock_conn.send_message.called, "send_message() should have been called")

    sent_msg = mock_conn.send_message.call_args[0][0]
    check(sent_msg["To"] == on.SHOP_OWNER_EMAIL,
          f"expected To header == SHOP_OWNER_EMAIL, got {sent_msg['To']!r}")
    check("shopowner@example.com" in sent_msg["From"],
          f"expected From header to contain SMTP_USER, got {sent_msg['From']!r}")

    check(_SECRET_MARKER not in out, "password leaked into stdout on success path")


def test_partial_config_missing_password_is_treated_as_not_configured():
    """SMTP_USER set but SMTP_PASSWORD empty -- must be treated the same as
    fully unconfigured (no network attempt), not crash trying to login with
    an empty password."""
    _clear_smtp_env()
    os.environ["SMTP_HOST"] = "smtp.office365.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "shopowner@example.com"
    # SMTP_PASSWORD intentionally left unset

    with patch("order_notifier.smtplib.SMTP") as mock_smtp:
        result = on._smtp_send_owner_notification(_SAMPLE_ORDERS, dry_run=False)

    check(result is False, f"expected False when password missing, got {result!r}")
    check(mock_smtp.call_count == 0, "must not attempt SMTP connection with missing password")


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
    print("FUNCTIONAL AUDIT TESTS OK -- _smtp_send_owner_notification correctly handles "
          "missing config, connection failures, auth failures, and timeouts by catching, "
          "logging, and returning False (never raising or silently succeeding), uses "
          "SMTP_USER/SMTP_PASSWORD from env correctly on the success path, and never "
          "leaks the password into any printed output on any code path.")


if __name__ == "__main__":
    run()
