"""
Google / Apple Sign-In for the Frank login screen (2026-08-13).

Both providers use the standard OAuth 2.0 authorization-code flow. This module
only builds authorize URLs and exchanges a callback code for a verified
identity (sub/email/name) — it never touches sessions, hub_users, or cookies;
that's main.py's job (see _find_or_create_oauth_user()).

Each provider is "enabled" only when its full credential set is present in the
environment, so main.py can hide the corresponding button entirely rather than
show one that 404s. Neither provider's app can be registered by this code —
Google Cloud Console (OAuth client) and Apple Developer Program (Services ID +
Sign-in-with-Apple private key) both require a human with account access; see
CLAUDE.md's "Google / Apple Sign-In (Frank login)" section for the exact steps.

Google: verifies the account by calling Google's own userinfo endpoint with the
access token (over TLS) rather than decoding the id_token locally — simpler and
just as trustworthy, since the token itself came straight from Google's token
endpoint in this same request.

Apple: has no userinfo endpoint — identity only comes back as a signed id_token
JWT, so this DOES verify it locally against Apple's published JWKS (PyJWT).
Apple also requires the token-endpoint client_secret to be a short-lived ES256
JWT signed with the developer's own Sign-in-with-Apple private key (not a
static secret) — generated fresh per exchange here rather than cached/rotated,
since a 5-minute validity window is trivially within Apple's 6-month max and
sidesteps any secret-rotation bookkeeping entirely.
"""
from __future__ import annotations

import os
import time
from urllib.parse import urlencode

import jwt
import requests

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID", "").strip()          # the Services ID, e.g. com.onbrandcraftz.frank.web
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID", "").strip()
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID", "").strip()
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY", "").strip()      # contents of the .p8 file (PEM), \n-escaped is fine
APPLE_ENABLED = bool(APPLE_CLIENT_ID and APPLE_TEAM_ID and APPLE_KEY_ID and APPLE_PRIVATE_KEY)

_HTTP_TIMEOUT = 10  # seconds — every external call below is a synchronous request during a route handler


class OAuthError(Exception):
    """Raised on any provider/network/verification failure — main.py catches
    this and redirects to /login with a generic, non-leaky error message."""


# ── Google ────────────────────────────────────────────────────────────────────

_GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def google_authorize_url(state: str, redirect_uri: str) -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{_GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"


def google_exchange_code(code: str, redirect_uri: str) -> dict:
    """Returns {"sub", "email", "email_verified", "name"}. Raises OAuthError on
    any failure — token exchange rejected, network error, or a malformed
    userinfo response."""
    try:
        token_resp = requests.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=_HTTP_TIMEOUT,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
    except Exception as exc:  # noqa: BLE001
        raise OAuthError(f"Google token exchange failed: {exc}") from exc

    try:
        info_resp = requests.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=_HTTP_TIMEOUT,
        )
        info_resp.raise_for_status()
        info = info_resp.json()
    except Exception as exc:  # noqa: BLE001
        raise OAuthError(f"Google userinfo fetch failed: {exc}") from exc

    sub = info.get("sub")
    email = info.get("email")
    if not sub or not email:
        raise OAuthError("Google userinfo response missing sub/email")
    return {
        "sub": sub,
        "email": email,
        "email_verified": bool(info.get("email_verified")),
        "name": info.get("name") or None,
    }


# ── Apple ─────────────────────────────────────────────────────────────────────

_APPLE_AUTHORIZE_URL = "https://appleid.apple.com/auth/authorize"
_APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
_APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
_APPLE_ISSUER = "https://appleid.apple.com"
_APPLE_CLIENT_SECRET_TTL = 300  # seconds — generated fresh per exchange, see module docstring


def apple_authorize_url(state: str, redirect_uri: str) -> str:
    params = {
        "client_id": APPLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        # form_post is REQUIRED by Apple whenever "name"/"email" scopes are
        # requested — a plain GET-redirect callback silently never fires.
        "response_mode": "form_post",
        "scope": "name email",
        "state": state,
    }
    return f"{_APPLE_AUTHORIZE_URL}?{urlencode(params)}"


def _apple_client_secret() -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": APPLE_TEAM_ID,
            "iat": now,
            "exp": now + _APPLE_CLIENT_SECRET_TTL,
            "aud": _APPLE_ISSUER,
            "sub": APPLE_CLIENT_ID,
        },
        APPLE_PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": APPLE_KEY_ID},
    )


def apple_exchange_code(code: str, redirect_uri: str) -> dict:
    """Returns {"sub", "email", "email_verified", "name"}. "name" is only ever
    non-None on a user's very first authorization (Apple sends it once, in the
    separate form-encoded "user" field, never inside the id_token) — every
    subsequent sign-in returns name=None and callers must not treat that as
    the name having changed."""
    try:
        token_resp = requests.post(
            _APPLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": APPLE_CLIENT_ID,
                "client_secret": _apple_client_secret(),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=_HTTP_TIMEOUT,
        )
        token_resp.raise_for_status()
        id_token = token_resp.json()["id_token"]
    except Exception as exc:  # noqa: BLE001
        raise OAuthError(f"Apple token exchange failed: {exc}") from exc

    try:
        jwk_client = jwt.PyJWKClient(_APPLE_JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=APPLE_CLIENT_ID,
            issuer=_APPLE_ISSUER,
        )
    except Exception as exc:  # noqa: BLE001
        raise OAuthError(f"Apple id_token verification failed: {exc}") from exc

    sub = claims.get("sub")
    email = claims.get("email")
    if not sub or not email:
        raise OAuthError("Apple id_token missing sub/email")
    # Apple's email_verified claim is sometimes the string "true"/"false" rather
    # than a real bool, depending on client — normalize both shapes.
    verified = claims.get("email_verified")
    email_verified = verified is True or verified == "true"
    return {"sub": sub, "email": email, "email_verified": email_verified, "name": None}
