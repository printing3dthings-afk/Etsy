#!/usr/bin/env python3
"""
Competitor & keyword intelligence via Scrapling (adaptive, anti-bot-aware scraping).

WHY: OnBrandCraftz needs competitor/keyword/trend signal for listings and the seasonal
keyword cadence (see CLAUDE.md "Competitor Intelligence"). Our existing `search_etsy` /
`browse_web` use plain requests+BeautifulSoup, which get 403'd or served bot-challenge
pages by Etsy and most SERPs. Scrapling adds two things over that: (1) an *adaptive*
parser that relocates elements when a page's markup changes, and (2) a stealth fetch
transport (curl_cffi TLS impersonation + realistic headers) that gets past many anti-bot
walls without a full browser.

════════════════════════════════════════════════════════════════════════════════════
VERIFICATION STATUS (2026-07-03) — read before relying on this:
  • Scrapling PARSER  ✅ verified working (css/xpath/regex extraction on real HTML).
  • Stealth FETCH     ⚠️ NOT verified in the build sandbox: that environment routes all
    egress through a MITM HTTPS proxy that resets curl_cffi's custom-TLS handshake
    ("connection reset by peer"). On a normal network (Scott's PC via the relay, or the
    Railway host) there is no such proxy and the stealth path should work — but that is
    UNPROVEN until someone runs `python tools/competitor_intel.py --selfcheck` there.
  → Do not trust the Etsy path until --selfcheck passes on a real network.

ToS NOTE (Scott opted in, owns the risk): scraping Etsy is ToS-sensitive and the shop's
account health is precious (see CLAUDE.md cascade-penalty notes). The Etsy helpers here
are deliberately LOW-VOLUME and rate-limited, use only public data, and must never be run
at high frequency. Prefer the non-Etsy research helpers for routine work.

This module is import-guarded end-to-end: if Scrapling is not installed it degrades to a
plain requests fetch + a clear "install scrapling" message, and never crashes an importer.
It is intentionally NOT wired into Frank's live agent tools yet — wire it only after the
stealth path is validated on a real network.
════════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote_plus, urlparse

# ── optional deps, guarded ────────────────────────────────────────────────────
try:
    from scrapling import Selector as _Selector  # adaptive parser
    _HAVE_SCRAPLING = True
except Exception:
    _Selector = None
    _HAVE_SCRAPLING = False

try:
    from scrapling.fetchers import Fetcher as _Fetcher  # stealth transport
    _HAVE_FETCHER = True
except Exception:
    _Fetcher = None
    _HAVE_FETCHER = False

try:
    import requests as _requests
except Exception:  # requests is a core dep everywhere else, but stay defensive
    _requests = None

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# Politeness: minimum seconds between successive fetches to the same host family.
_MIN_INTERVAL = 2.0
_last_fetch_at = 0.0


def is_available() -> bool:
    """True when the adaptive parser is importable (the always-useful half)."""
    return _HAVE_SCRAPLING


def _throttle() -> None:
    global _last_fetch_at
    dt = time.monotonic() - _last_fetch_at
    if dt < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - dt)
    _last_fetch_at = time.monotonic()


def _parse(html: str):
    """Return a Scrapling Selector when available, else None (caller handles)."""
    if _HAVE_SCRAPLING and html:
        try:
            return _Selector(html)
        except Exception:
            return None
    return None


def _first(res):
    try:
        return res[0]
    except Exception:
        return None


def fetch(url: str, *, stealth: bool = True, impersonate: str = "chrome",
          timeout: int = 25) -> dict[str, Any]:
    """Fetch a URL, preferring Scrapling's stealth transport, falling back to requests.

    Returns {url, status, ok, html, via, note}. `via` is 'scrapling' or 'requests' so
    callers (and --selfcheck) can see which path actually worked — no silent pretending.
    """
    _throttle()
    note = None

    if stealth and _HAVE_FETCHER:
        try:
            page = _Fetcher.get(url, timeout=timeout, stealthy_headers=True,
                                impersonate=impersonate)
            html = getattr(page, "html_content", None) or getattr(page, "body", None) or str(page)
            status = int(getattr(page, "status", 0) or 0)
            return {"url": url, "status": status, "ok": 200 <= status < 300,
                    "html": html, "via": "scrapling", "note": None}
        except Exception as e:
            # Most commonly the MITM-proxy TLS reset in the build sandbox; on a real
            # network this rarely fires. Fall back so the tool still returns something.
            note = f"stealth fetch failed ({type(e).__name__}); used plain requests"

    if _requests is None:
        return {"url": url, "status": 0, "ok": False, "html": "",
                "via": "none", "note": "requests not installed"}
    try:
        r = _requests.get(url, headers={"User-Agent": _UA,
                                        "Accept-Language": "en-US,en;q=0.9"},
                          timeout=timeout)
        return {"url": url, "status": r.status_code, "ok": r.ok, "html": r.text,
                "via": "requests", "note": note}
    except Exception as e:
        return {"url": url, "status": 0, "ok": False, "html": "",
                "via": "requests", "note": f"{note or ''} requests error: {e}".strip()}


# ── research helpers (safe, non-Etsy — the routine path) ──────────────────────
def keyword_intel(query: str, *, limit: int = 10) -> dict[str, Any]:
    """Pull candidate keyword phrases from a public SERP for `query`.

    Non-Etsy and low-risk. Returns {query, source, phrases, count, fetch}. Useful for
    the seasonal-keyword cadence: harvest real phrases buyers/blogs use around a niche.
    """
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    res = fetch(url)
    sel = _parse(res["html"])
    phrases: list[str] = []
    if sel is not None:
        for sels in ("a.result__a::text", "h2 a::text", "a::text"):
            phrases = [t.strip() for t in sel.css(sels) if t and len(t.strip()) > 3]
            if phrases:
                break
    # de-dup, keep order
    seen, out = set(), []
    for p in phrases:
        k = p.lower()
        if k not in seen:
            seen.add(k); out.append(p)
        if len(out) >= limit:
            break
    return {"query": query, "source": "duckduckgo", "phrases": out,
            "count": len(out), "fetch": {k: res[k] for k in ("status", "via", "note")}}


def fetch_competitor_listing(url: str) -> dict[str, Any]:
    """Parse a public product/listing page for title, price, and description snippet.

    Works on Etsy or any shop page. On Etsy this is ToS-sensitive — use sparingly and
    only for public competitive reference, never in a loop over many listings.
    """
    res = fetch(url)
    sel = _parse(res["html"])
    data: dict[str, Any] = {"url": url, "fetch": {k: res[k] for k in ("status", "via", "note")}}
    if sel is None:
        data["error"] = "no parseable HTML (blocked, or scrapling missing)"
        return data
    # Adaptive, best-effort selectors — resilient to markup drift is Scrapling's point.
    data["title"] = (_first(sel.css("h1::text")) or _first(sel.css("title::text")) or "").strip()
    price = (_first(sel.css('[data-selector="price-only"]::text'))
             or _first(sel.css('p.wt-text-title-larger::text'))
             or _first(sel.re(r"\$\s?\d+[.,]?\d{0,2}")))
    data["price"] = (price or "").strip()
    meta = _first(sel.css('meta[name="description"]::attr(content)'))
    data["description_snippet"] = (meta or "")[:300]
    return data


# ── Etsy rank check (cautious, rate-limited — ToS-sensitive) ──────────────────
def etsy_rank_check(keyword: str, shop_name: str = "onbrandcraftz",
                    max_pages: int = 2) -> dict[str, Any]:
    """Find where `shop_name` appears in Etsy search for `keyword` (best-effort).

    ⚠️ ToS-sensitive + Etsy 403s datacenter IPs. This ONLY works where the stealth path
    is validated (run --selfcheck first). Hard-capped at `max_pages` (≤3) with a polite
    delay, public data only. Returns honest status when blocked — never fabricates a rank.
    """
    max_pages = max(1, min(3, max_pages))
    shop_l = shop_name.lower()
    for page in range(1, max_pages + 1):
        url = (f"https://www.etsy.com/search?q={quote_plus(keyword)}"
               f"&page={page}&ref=pagination")
        res = fetch(url)
        if not res["ok"]:
            return {"keyword": keyword, "shop": shop_name, "found": False,
                    "blocked": True, "page_checked": page,
                    "status": res["status"], "via": res["via"], "note": res["note"],
                    "hint": "Etsy blocked this fetch. Validate the stealth path with "
                            "`python tools/competitor_intel.py --selfcheck` on a real network."}
        sel = _parse(res["html"])
        if sel is not None:
            hrefs = [h for h in sel.css("a::attr(href)") if h]
            for idx, h in enumerate(hrefs):
                if f"/shop/{shop_l}" in h.lower() or f"{shop_l}.etsy" in h.lower():
                    return {"keyword": keyword, "shop": shop_name, "found": True,
                            "page": page, "approx_position_on_page": idx + 1,
                            "via": res["via"]}
        time.sleep(1.0)  # politeness between pages
    return {"keyword": keyword, "shop": shop_name, "found": False, "blocked": False,
            "pages_checked": max_pages, "note": "shop not seen in the checked pages"}


# ── self-check / validation harness ───────────────────────────────────────────
def selfcheck() -> int:
    """Prove what works in THIS environment. Run on the target network before relying
    on the Etsy path. Exit 0 if the stealth fetch works against a real anti-bot page."""
    print("competitor_intel self-check")
    print(f"  scrapling parser available : {_HAVE_SCRAPLING}")
    print(f"  scrapling fetcher available: {_HAVE_FETCHER}")
    if not _HAVE_SCRAPLING:
        print("  → install with:  pip install \"scrapling[fetchers]\"  (then: scrapling install)")
        return 1

    # 1) parser on known-good content
    r = fetch("https://example.com", stealth=False)
    sel = _parse(r["html"])
    title = _first(sel.css("title::text")) if sel else None
    print(f"  parser test         : title={title!r}  ({'OK' if title else 'FAIL'})")

    # 2) the real question: does the stealth path beat a bot wall?
    r2 = fetch("https://www.etsy.com/search?q=kawaii%20planner", stealth=True)
    stealth_ok = r2["ok"] and r2["via"] == "scrapling"
    print(f"  stealth fetch (Etsy): status={r2['status']} via={r2['via']} "
          f"note={r2['note']!r}")
    if stealth_ok:
        print("  ✅ stealth path WORKS here — Etsy rank checks are usable (stay low-volume).")
        return 0
    print("  ⚠️  stealth path did NOT get through here. If this is the build sandbox, that's "
          "the MITM-proxy TLS reset and is expected. Re-run on Scott's PC (relay) or Railway.")
    return 2


if __name__ == "__main__":
    import sys
    if "--selfcheck" in sys.argv:
        raise SystemExit(selfcheck())
    print(__doc__)
    print("Run `python tools/competitor_intel.py --selfcheck` to validate this environment.")
