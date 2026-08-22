#!/usr/bin/env python3
"""
Google / Apple Sign-In tests (2026-08-13).

Covers oauth_providers.py's pure/offline-testable pieces (authorize URL
construction, Apple's ES256 client-secret JWT shape) plus main.py's OAuth
plumbing: the CSRF state-token store (_new_oauth_state/_consume_oauth_state,
same single-use pattern as the existing WS tickets), _find_or_create_oauth_user()
(the account-linking logic — including the security-critical rule that an
UNVERIFIED provider email must never auto-link into an existing password
account), and the /auth/google and /auth/apple routes end to end with the real
network calls mocked out.

Never touches accounts.google.com or appleid.apple.com — google_exchange_code/
apple_exchange_code are monkeypatched for every route-level test.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_oauth_login_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "oauth-login-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import jwt  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main as server  # noqa: E402
import oauth_providers  # noqa: E402
import db  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _reset_state():
    with server._oauth_states_lock:
        server._oauth_states.clear()


# ── oauth_providers: authorize URL construction ─────────────────────────────

def test_google_authorize_url_includes_required_params():
    url = oauth_providers.google_authorize_url("abc123", "https://example.com/auth/google/callback")
    check(url.startswith("https://accounts.google.com/o/oauth2/v2/auth?"), f"wrong base URL: {url}")
    check("state=abc123" in url, f"state missing from URL: {url}")
    check("redirect_uri=https%3A%2F%2Fexample.com%2Fauth%2Fgoogle%2Fcallback" in url, f"redirect_uri wrong/missing: {url}")
    check("scope=openid+email+profile" in url, f"scope missing/wrong: {url}")
    check("response_type=code" in url, f"response_type missing: {url}")


def test_apple_authorize_url_uses_form_post_and_name_email_scope():
    url = oauth_providers.apple_authorize_url("xyz789", "https://example.com/auth/apple/callback")
    check(url.startswith("https://appleid.apple.com/auth/authorize?"), f"wrong base URL: {url}")
    check("response_mode=form_post" in url,
          "Apple requires response_mode=form_post whenever name/email scopes are requested "
          "-- a plain GET callback silently never fires")
    check("scope=name+email" in url, f"scope missing/wrong: {url}")
    check("state=xyz789" in url, f"state missing from URL: {url}")


# ── oauth_providers: Apple ES256 client-secret JWT ──────────────────────────

_EC_KEY = ec.generate_private_key(ec.SECP256R1())
_EC_PEM = _EC_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()


def test_apple_client_secret_is_well_formed_es256_jwt():
    with patch.object(oauth_providers, "APPLE_TEAM_ID", "TEAM123456"), \
         patch.object(oauth_providers, "APPLE_CLIENT_ID", "com.example.frank.web"), \
         patch.object(oauth_providers, "APPLE_KEY_ID", "KEY1234567"), \
         patch.object(oauth_providers, "APPLE_PRIVATE_KEY", _EC_PEM):
        secret = oauth_providers._apple_client_secret()
        header = jwt.get_unverified_header(secret)
        check(header.get("alg") == "ES256", f"expected alg=ES256, got {header}")
        check(header.get("kid") == "KEY1234567", f"expected kid=KEY1234567, got {header}")
        claims = jwt.decode(secret, _EC_KEY.public_key(), algorithms=["ES256"], audience="https://appleid.apple.com")
        check(claims["iss"] == "TEAM123456", f"expected iss=team id, got {claims}")
        check(claims["sub"] == "com.example.frank.web", f"expected sub=client id, got {claims}")
        check(claims["exp"] - claims["iat"] == 300, f"expected a 5-minute TTL, got {claims}")


# ── main.py: OAuth CSRF state tokens (mirrors the existing WS-ticket tests) ──

def test_oauth_state_round_trips_next_path():
    _reset_state()
    state = server._new_oauth_state("/frank")
    check(server._consume_oauth_state(state) == "/frank", "state did not round-trip its next_path")


def test_oauth_state_is_single_use():
    _reset_state()
    state = server._new_oauth_state("/frank")
    server._consume_oauth_state(state)
    check(server._consume_oauth_state(state) is None, "a second consume of the same state must fail")


def test_oauth_state_unknown_token_returns_none():
    _reset_state()
    check(server._consume_oauth_state("never-issued") is None, "an unknown state must not validate")


def test_oauth_state_expired_returns_none():
    _reset_state()
    state = server._new_oauth_state("/frank")
    with server._oauth_states_lock:
        expiry, next_path = server._oauth_states[state]
        server._oauth_states[state] = (0.0, next_path)  # force into the past
    check(server._consume_oauth_state(state) is None, "an expired state must not validate")


# ── main.py: _username_from_email ───────────────────────────────────────────

def test_username_from_email_strips_and_lowercases():
    check(server._username_from_email("Scott.Jackson+test@Example.com") == "scott-jackson-test",
          f"got {server._username_from_email('Scott.Jackson+test@Example.com')!r}")


def test_username_from_email_falls_back_when_local_part_has_no_ascii_alnum():
    check(server._username_from_email("😀@example.com") == "user",
          f"got {server._username_from_email('😀@example.com')!r}")


# ── main.py: _find_or_create_oauth_user ─────────────────────────────────────

def _fresh_profile(sub: str, email: str, verified: bool = True, name: str | None = None) -> dict:
    return {"sub": sub, "email": email, "email_verified": verified, "name": name}


def test_find_or_create_oauth_user_creates_new_account():
    username = server._find_or_create_oauth_user("google", _fresh_profile("g-sub-1", "newperson@example.com"))
    check(username == "newperson", f"expected derived username 'newperson', got {username!r}")
    row = db.get_hub_user(username)
    check(row is not None, "hub_users row was not created")
    check(row["role"] == "admin", f"OAuth-created accounts must be role=admin, got {row['role']!r}")
    check(row["email"] == "newperson@example.com", f"email not stored, got {row['email']!r}")
    identity = db.get_oauth_identity("google", "g-sub-1")
    check(identity is not None and identity["username"] == username, "oauth_identities row missing/wrong")


def test_find_or_create_oauth_user_reuses_existing_identity_no_duplicate():
    profile = _fresh_profile("g-sub-2", "repeat@example.com")
    first = server._find_or_create_oauth_user("google", profile)
    second = server._find_or_create_oauth_user("google", profile)
    check(first == second, f"same provider+sub must resolve to the same username, got {first!r} vs {second!r}")


def test_find_or_create_oauth_user_links_verified_email_to_existing_password_account():
    db.create_hub_user("existinguser", server._hash_password("Whatever12345!"), role="admin",
                        email="linkme@example.com")
    username = server._find_or_create_oauth_user(
        "apple", _fresh_profile("a-sub-1", "linkme@example.com", verified=True)
    )
    check(username == "existinguser",
          f"a verified email matching an existing account must link to it, got {username!r}")
    all_users_named_linkme = [u for u in db.list_hub_users() if u["email"] == "linkme@example.com"]
    check(len(all_users_named_linkme) == 1,
          f"linking must not create a second account with the same email, found {len(all_users_named_linkme)}")


def test_find_or_create_oauth_user_does_not_link_unverified_email():
    """Security-critical: an OAuth provider claiming an UNVERIFIED email must
    never be trusted to walk into somebody else's existing account."""
    db.create_hub_user("victimaccount", server._hash_password("Whatever12345!"), role="admin",
                        email="victim@example.com")
    username = server._find_or_create_oauth_user(
        "google", _fresh_profile("g-sub-unverified", "victim@example.com", verified=False)
    )
    check(username != "victimaccount",
          f"an UNVERIFIED email must never auto-link to an existing account, but got {username!r}")
    row = db.get_hub_user(username)
    check(row is not None and row["email"] == "victim@example.com",
          "the new (separate) account should still record the claimed email")


def test_find_or_create_oauth_user_dedupes_username_collision():
    server._find_or_create_oauth_user("google", _fresh_profile("g-sub-collide-1", "collide@example.com"))
    second = server._find_or_create_oauth_user("apple", _fresh_profile("a-sub-collide-1", "collide@other.com"))
    # both emails have local-part "collide" -- the second must not silently
    # reuse/overwrite the first account.
    check(second != "collide", f"expected a deduped username distinct from 'collide', got {second!r}")
    check(db.get_hub_user(second) is not None, "deduped account was not actually created")


# ── Route-level tests (TestClient, real network calls mocked) ───────────────

def _client_with_owner() -> TestClient:
    if db.hub_users_empty():
        db.create_hub_user("owner", server._hash_password("Whatever12345!"), role="owner")
    return TestClient(server.app, base_url="https://testserver")


def test_google_start_404s_when_not_configured():
    with patch.object(oauth_providers, "GOOGLE_ENABLED", False):
        c = _client_with_owner()
        r = c.get("/auth/google", follow_redirects=False)
        check(r.status_code == 404, f"expected 404 when Google isn't configured, got {r.status_code}")


def test_apple_start_404s_when_not_configured():
    with patch.object(oauth_providers, "APPLE_ENABLED", False):
        c = _client_with_owner()
        r = c.get("/auth/apple", follow_redirects=False)
        check(r.status_code == 404, f"expected 404 when Apple isn't configured, got {r.status_code}")


def test_google_start_redirects_to_google_with_state():
    with patch.object(oauth_providers, "GOOGLE_ENABLED", True), \
         patch.object(oauth_providers, "GOOGLE_CLIENT_ID", "test-client-id"):
        c = _client_with_owner()
        r = c.get("/auth/google?next=/frank", follow_redirects=False)
        check(r.status_code == 303, f"expected a redirect, got {r.status_code}")
        loc = r.headers.get("location", "")
        check(loc.startswith("https://accounts.google.com/o/oauth2/v2/auth?"), f"wrong redirect target: {loc}")
        check("state=" in loc, f"no state param on the redirect: {loc}")


def test_google_callback_rejects_invalid_state():
    with patch.object(oauth_providers, "GOOGLE_ENABLED", True):
        c = _client_with_owner()
        r = c.get("/auth/google/callback?code=fake&state=never-issued", follow_redirects=False)
        check(r.status_code == 303 and r.headers.get("location", "").startswith("/login"),
              f"expected redirect to /login on invalid state, got {r.status_code} {r.headers.get('location')}")
        check(server.SESSION_COOKIE not in r.cookies, "no session cookie should be set on a failed callback")


def test_google_callback_success_creates_session_and_redirects_to_next():
    _reset_state()
    c = _client_with_owner()
    state = server._new_oauth_state("/frank")
    fake_profile = _fresh_profile("g-sub-route-1", "routetest@example.com")
    with patch.object(oauth_providers, "google_exchange_code", return_value=fake_profile):
        r = c.get(f"/auth/google/callback?code=fakecode&state={state}", follow_redirects=False)
    check(r.status_code == 303, f"expected a redirect, got {r.status_code}")
    check(r.headers.get("location") == "/frank", f"expected redirect to /frank, got {r.headers.get('location')}")
    check(server.SESSION_COOKIE in r.cookies, "a session cookie must be set on a successful OAuth login")
    check(db.get_oauth_identity("google", "g-sub-route-1") is not None, "oauth identity was not persisted")


def test_google_callback_exchange_failure_redirects_to_login_no_session():
    _reset_state()
    c = _client_with_owner()
    state = server._new_oauth_state("/frank")
    with patch.object(oauth_providers, "google_exchange_code",
                       side_effect=oauth_providers.OAuthError("token exchange failed")):
        r = c.get(f"/auth/google/callback?code=fakecode&state={state}", follow_redirects=False)
    check(r.status_code == 303 and r.headers.get("location", "").startswith("/login"),
          f"expected redirect to /login on exchange failure, got {r.status_code} {r.headers.get('location')}")
    check(server.SESSION_COOKIE not in r.cookies, "no session cookie should be set when the exchange fails")


def test_apple_callback_success_via_form_post():
    _reset_state()
    c = _client_with_owner()
    state = server._new_oauth_state("/frank")
    fake_profile = _fresh_profile("a-sub-route-1", "appleroute@example.com")
    with patch.object(oauth_providers, "apple_exchange_code", return_value=fake_profile):
        r = c.post("/auth/apple/callback", data={"code": "fakecode", "state": state}, follow_redirects=False)
    check(r.status_code == 303, f"expected a redirect, got {r.status_code}")
    check(r.headers.get("location") == "/frank", f"expected redirect to /frank, got {r.headers.get('location')}")
    check(server.SESSION_COOKIE in r.cookies, "a session cookie must be set on a successful Apple login")


def test_apple_callback_rejects_invalid_state():
    c = _client_with_owner()
    r = c.post("/auth/apple/callback", data={"code": "fake", "state": "never-issued"}, follow_redirects=False)
    check(r.status_code == 303 and r.headers.get("location", "").startswith("/login"),
          f"expected redirect to /login on invalid state, got {r.status_code} {r.headers.get('location')}")


# ── Login/signup page: buttons render only when configured ──────────────────

def test_login_page_hides_oauth_buttons_when_unconfigured():
    with patch.object(oauth_providers, "GOOGLE_ENABLED", False), patch.object(oauth_providers, "APPLE_ENABLED", False):
        c = _client_with_owner()
        html = c.get("/login").text
        check("Continue with Google" not in html, "Google button shown despite GOOGLE_ENABLED=False")
        check("Continue with Apple" not in html, "Apple button shown despite APPLE_ENABLED=False")


def test_login_page_shows_only_configured_provider_buttons():
    with patch.object(oauth_providers, "GOOGLE_ENABLED", True), patch.object(oauth_providers, "APPLE_ENABLED", False):
        c = _client_with_owner()
        html = c.get("/login").text
        check("Continue with Google" in html, "Google button missing despite GOOGLE_ENABLED=True")
        check("Continue with Apple" not in html, "Apple button shown despite APPLE_ENABLED=False")


def test_login_page_matches_frank_design_tokens():
    c = _client_with_owner()
    html = c.get("/login").text
    check("#241c2e" in html, "login page background does not match Frank's Studio Warm --bg token")
    check("#e4b155" in html, "login page primary button does not match Frank's --gold token")
    check("Manrope" in html and "Outfit" in html, "login page font stack does not match Frank's --font-body/--font-display")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("OAUTH LOGIN TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("OAUTH LOGIN TESTS OK — authorize URL construction, Apple client-secret JWT shape, OAuth CSRF state "
          "tokens, account-linking (incl. the unverified-email-must-not-auto-link security rule), and the "
          "/auth/google + /auth/apple routes all behave correctly with real network calls mocked out.")


if __name__ == "__main__":
    run()
