"""
Google Calendar API v3 client — read/write access to a connected user's
primary calendar, mirroring tools/etsy_api.py's shape (auto-.env-load,
requests.Session module-level, auto token refresh) but much simpler: unlike
Etsy, Google's refresh token doesn't rotate on every use, so there's no
lineage-tracking needed across restarts.

OAuth-protected (requires the full OAuth flow):
  1. Set GOOGLE_CALENDAR_CLIENT_ID / GOOGLE_CALENDAR_CLIENT_SECRET in .env.
  2. Run tools/google_calendar_oauth.py to authorize (see its module
     docstring for the Google Cloud Console setup steps).

Every method raises GoogleCalendarNotConnectedError when no refresh token is
present -- callers should catch this specifically to degrade gracefully
(same contract EtsyAPIClient._require_oauth() gives main.py elsewhere in
this codebase), rather than a bare Exception.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import requests

# Auto-load .env on import, same idiom as tools/etsy_api.py -- every consumer
# (scripts, ad-hoc python -c, agents) gets credentials without copy-pasting a
# parser. setdefault never overrides values already in the environment.
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

BASE_URL = "https://www.googleapis.com/calendar/v3"
TOKEN_URL = "https://oauth2.googleapis.com/token"

_session = requests.Session()


class GoogleCalendarError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Google Calendar API {status}: {message}")


class GoogleCalendarNotConnectedError(GoogleCalendarError):
    """No refresh token on file -- Scott hasn't run google_calendar_oauth.py
    yet (or access was revoked). Distinct from GoogleCalendarError so callers
    can tell "not set up" apart from "a real API call failed"."""
    def __init__(self):
        super().__init__(401, "Google Calendar is not connected. Run "
                               "python tools/google_calendar_oauth.py to authorize.")


def _update_env(key: str, value: str) -> None:
    """Persist a rotated token to .env, same inline-rewrite pattern
    EtsyAPIClient.refresh_access_token() already uses."""
    try:
        if os.path.exists(_ENV_PATH):
            with open(_ENV_PATH) as f:
                lines = f.readlines()
        else:
            lines = []
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}\n")
        with open(_ENV_PATH, "w") as f:
            f.writelines(lines)
    except OSError:
        pass  # best-effort -- os.environ is already updated, which is what matters at runtime


class GoogleCalendarClient:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "").strip()
        self.access_token = os.getenv("GOOGLE_CALENDAR_ACCESS_TOKEN", "").strip()
        self.refresh_token = os.getenv("GOOGLE_CALENDAR_REFRESH_TOKEN", "").strip()

    def _require_oauth(self) -> None:
        if not self.refresh_token:
            raise GoogleCalendarNotConnectedError()

    def refresh_access_token(self) -> str:
        """Exchange the refresh token for a new access token, persisting it
        to .env and (best-effort) the encrypted-at-rest DB row so a server
        restart doesn't need a fresh OAuth run."""
        self._require_oauth()
        resp = _session.post(TOKEN_URL, data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }, timeout=15)
        try:
            data = resp.json()
        except ValueError:
            raise GoogleCalendarError(resp.status_code, resp.text[:300])
        new_access = data.get("access_token", "")
        if not new_access:
            raise GoogleCalendarError(resp.status_code, str(data)[:300])

        self.access_token = new_access
        os.environ["GOOGLE_CALENDAR_ACCESS_TOKEN"] = new_access
        _update_env("GOOGLE_CALENDAR_ACCESS_TOKEN", new_access)
        try:
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api_server"))
            import db as _db
            _db.save_google_calendar_tokens(new_access, self.refresh_token)
        except Exception:
            pass  # DB persistence is best-effort here; .env is the source of truth for this process
        return new_access

    def _request(self, method: str, path: str, **kwargs) -> dict:
        self._require_oauth()
        if not self.access_token:
            self.refresh_access_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        resp = _session.request(method, f"{BASE_URL}{path}", headers=headers, timeout=15, **kwargs)
        if resp.status_code == 401:
            self.refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            resp = _session.request(method, f"{BASE_URL}{path}", headers=headers, timeout=15, **kwargs)
        if resp.status_code >= 400:
            raise GoogleCalendarError(resp.status_code, resp.text[:300])
        return resp.json() if resp.content else {}

    def list_upcoming_events(self, days_ahead: int = 14) -> list[dict]:
        """Events on the primary calendar starting now through `days_ahead`
        days out, expanded (singleEvents) so recurring events show as
        individual occurrences rather than one recurrence-rule blob."""
        now = datetime.now(timezone.utc)
        data = self._request("GET", "/calendars/primary/events", params={
            "timeMin": now.isoformat(),
            "timeMax": (now + timedelta(days=days_ahead)).isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 50,
        })
        return data.get("items", [])

    def create_event(self, summary: str, when: str, description: str = "") -> dict:
        """Creates an event on the primary calendar. `when` is an ISO date
        ('2026-07-25') for an all-day event, or an ISO datetime
        ('2026-07-25T14:00:00-04:00') for a timed event."""
        is_all_day = "T" not in when
        body = {"summary": summary, "description": description}
        if is_all_day:
            body["start"] = {"date": when}
            body["end"] = {"date": when}
        else:
            body["start"] = {"dateTime": when}
            body["end"] = {"dateTime": when}
        return self._request("POST", "/calendars/primary/events", json=body)
