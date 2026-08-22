"""
Pre-publish trademark screening via Goalie IP's USPTO trademark search API
(https://www.goalieip.com) -- added 2026-08-20 as part of "make Frank
smarter/more independent" work, directly addressing a real, already-
documented risk in CLAUDE.md's Suspension Triggers section: "Trademark
terms in titles/tags — even accidental use triggers shop quality score
penalty affecting ALL listings." That risk had no automated check anywhere
in this codebase before this module -- catching it depended entirely on a
human noticing before approving.

**Not yet authorized** -- `GOALIEIP_API_KEY` needs to be set in `.env` by
Scott. Sign up at https://www.goalieip.com/subscribe#api (free tier: 200
calls/month, no credit card required), then get the key from
https://www.goalieip.com/portal/api-keys. Until then, `is_configured()`
returns False and `screen_listing_content()` is a clean no-op -- same
pattern as Google Calendar OAuth elsewhere in this codebase: the code
ships ready, activation is a Scott-gated credential step, not a Claude one.

Deliberately conservative in what it flags: screens each Etsy TAG (already
an atomic 2-3 word phrase) and each comma-separated TITLE phrase (this
shop's titles are already comma-separated buyer-search phrases per
CLAUDE.md's Gate 3 title rules) with `markLiteralMode="exact"` against
live/registered trademarks only -- not a fuzzy or substring search, which
would flag nearly every listing and be useless noise. This is advisory,
not a hard block: a flagged phrase can be an exact trademark match in a
totally unrelated Nice class (a "MOON" mark for pharmaceuticals is not the
same collision risk as "moon phase art" for wall art) -- surfacing it for
a human to judge is the right level of automation here, not auto-rejecting
a staged action on a string match alone.
"""
from __future__ import annotations

import os
from typing import Any

import requests

_BASE_URL = "https://www.goalieip.com/api/v1"
_TIMEOUT = 10

# USPTO status codes in the 6xx/7xx/8xx families cover live marks --
# published for opposition, registered, renewed. Codes below that
# (abandoned, cancelled, expired application stages) aren't a live
# collision risk, so they're excluded before anything is ever surfaced --
# kept as a prefix check (not an exhaustive enum) since it's intentionally
# broad on the "live" side; a false positive here just means one more
# match for Scott to glance at and dismiss, which is the safe direction
# to err in for a compliance check.
_LIVE_STATUS_PREFIXES = ("6", "7", "8")


def is_configured() -> bool:
    return bool(os.getenv("GOALIEIP_API_KEY", "").strip())


def _headers() -> dict:
    key = os.getenv("GOALIEIP_API_KEY", "").strip()
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _search_exact(phrase: str) -> list[dict]:
    """One exact-match search against Goalie IP. Returns the raw `data`
    list (possibly empty). Raises requests.RequestException on a network/
    HTTP failure -- callers decide how to degrade, this never swallows an
    error silently."""
    resp = requests.post(
        f"{_BASE_URL}/trademarks/search",
        headers=_headers(),
        json={"markLiteral": phrase, "markLiteralMode": "exact", "pageSize": 10},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def _is_live(record: dict) -> bool:
    code = str(record.get("currentStatusCode") or "")
    return code.startswith(_LIVE_STATUS_PREFIXES)


def _phrases_from_title(title: str) -> list[str]:
    return [p.strip() for p in (title or "").split(",") if p.strip()]


def screen_listing_content(title: str = "", tags: list[str] | None = None) -> dict[str, Any]:
    """Screen a title + tag set for exact live-trademark collisions.

    Returns:
      {"configured": bool, "checked": [str], "flags": [dict], "error": str|None}

    - configured=False: no API key set yet -- nothing was checked, and
      callers must treat this as "unknown", never as "clean". The Action
      Center should show "not screened (trademark screening not
      configured)", not silence.
    - error: set if a call failed partway through (network issue, quota
      exhausted, bad key). Whatever was successfully checked before the
      failure is still returned in `checked`/`flags`, never discarded --
      a partial screen is still useful information, and silently dropping
      it would be exactly the "reported success without proof" failure
      mode this shop's ops_runbook already has one real incident about.
    - flags: phrases with at least one live/registered exact match, each
      with the matching owner + Nice class(es) + goods/services so a human
      can judge real collision risk vs. an unrelated-industry coincidence.
    """
    if not is_configured():
        return {"configured": False, "checked": [], "flags": [], "error": None}

    # Dedup case-insensitively (USPTO exact-match search is itself
    # case-insensitive, and a tag frequently repeats a title phrase in
    # different casing -- e.g. title "Kitchen Wall Decor" / tag "kitchen
    # wall decor") while keeping the first-seen casing for the actual call.
    seen_lower: set[str] = set()
    phrases: list[str] = []
    for phrase in _phrases_from_title(title) + [t.strip() for t in (tags or []) if t and t.strip()]:
        key = phrase.lower()
        if key not in seen_lower:
            seen_lower.add(key)
            phrases.append(phrase)
    checked: list[str] = []
    flags: list[dict] = []
    for phrase in phrases:
        try:
            records = _search_exact(phrase)
        except requests.RequestException as exc:
            return {"configured": True, "checked": checked, "flags": flags, "error": str(exc)[:300]}
        checked.append(phrase)
        live = [r for r in records if _is_live(r)]
        if live:
            flags.append({
                "phrase": phrase,
                "matches": [
                    {
                        "owner": r.get("ownerName"),
                        "classes": r.get("internationalClasses"),
                        "registration_number": r.get("registrationNumber"),
                        "goods_and_services": r.get("goodsAndServices"),
                    }
                    for r in live[:3]
                ],
            })
    return {"configured": True, "checked": checked, "flags": flags, "error": None}
