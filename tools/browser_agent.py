"""
Web scraping and browser automation for the Frank CEO agent.

Uses requests + BeautifulSoup for reliable HTML scraping — no Playwright
dependency needed for most tasks, and works correctly behind the HTTPS proxy
that this environment uses (REQUESTS_CA_BUNDLE / SSL_CERT_FILE env vars
auto-configure trust).

Called synchronously from _execute_agent_tool via asyncio.to_thread.
"""

import os
import re
import textwrap
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

_SESSION = None
_TIMEOUT = 20

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Trust the proxy CA if it exists, otherwise fall back to certifi default
_CA_BUNDLE = os.environ.get(
    "REQUESTS_CA_BUNDLE",
    os.environ.get("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else True),
)

_NOISE_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript", "iframe", "svg"}


def _session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        s = requests.Session()
        s.headers.update(_HEADERS)
        s.verify = _CA_BUNDLE
        _SESSION = s
    return _SESSION


def _clean_text(html: str, max_chars: int = 8000) -> str:
    """Strip tags and noise, return cleaned visible text."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse blank lines
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    return text[:max_chars]


def get_page_text(url: str, max_chars: int = 8000) -> str:
    """
    Fetch a URL and return its cleaned visible text.

    Returns an error string (not raises) so the agent can decide what to do.
    """
    try:
        r = _session().get(url, timeout=_TIMEOUT, allow_redirects=True)
        if r.status_code == 403:
            return f"[blocked] The site returned HTTP 403 — access denied. URL: {url}"
        if r.status_code == 404:
            return f"[not found] HTTP 404 — page does not exist. URL: {url}"
        if not r.ok:
            return f"[error] HTTP {r.status_code} from {url}"
        content_type = r.headers.get("content-type", "")
        if "html" not in content_type and "text" not in content_type:
            return f"[unsupported] Content-Type is {content_type!r} — not readable text. URL: {url}"
        return _clean_text(r.text, max_chars)
    except requests.exceptions.ConnectionError as exc:
        return f"[connection error] Could not reach {url}: {exc}"
    except requests.exceptions.Timeout:
        return f"[timeout] Request to {url} timed out after {_TIMEOUT}s"
    except Exception as exc:
        return f"[error] {exc}"


def search_etsy(query: str, limit: int = 10) -> list:
    """
    Search Etsy and return structured listing data.

    Each result dict has: title, price, shop, url, review_count (when available).
    Returns a list of dicts, or a list with one error dict if the request fails.
    """
    limit = max(1, min(limit, 20))
    search_url = f"https://www.etsy.com/search?q={quote_plus(query)}&ref=search_bar"
    try:
        r = _session().get(search_url, timeout=_TIMEOUT, allow_redirects=True)
        if r.status_code == 403:
            return [{"error": "Etsy returned 403 — access blocked in this environment. The tool will work on Railway (production)."}]
        if not r.ok:
            return [{"error": f"Etsy search returned HTTP {r.status_code}"}]
    except Exception as exc:
        return [{"error": f"Request failed: {exc}"}]

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # Etsy search result cards — try multiple selector strategies since their HTML changes
    cards = (
        soup.select("div[data-listing-id]") or
        soup.select("li[data-palette-listing-id]") or
        soup.select(".v2-listing-card") or
        soup.select("div.js-merch-stacking-col li") or
        []
    )

    for card in cards[:limit]:
        title = ""
        price = ""
        shop = ""
        href = ""
        reviews = ""

        # Title
        for sel in ["h3", "h2", ".v2-listing-card__title", "[data-tooltip]"]:
            el = card.select_one(sel)
            if el and el.get_text(strip=True):
                title = el.get_text(strip=True)[:120]
                break

        # Price — look for currency spans or data attributes
        for sel in ["span[data-currency-value]", ".currency-value", ".lc-price", "p.lc-price"]:
            el = card.select_one(sel)
            if el:
                price = el.get_text(strip=True)
                break
        if not price:
            # Fallback: look for $-prefixed text
            m = re.search(r"\$[\d,]+\.?\d*", card.get_text())
            if m:
                price = m.group()

        # Shop name
        for sel in [".v2-listing-card__shop .body-small", "p.body-small", ".shop-name"]:
            el = card.select_one(sel)
            if el and el.get_text(strip=True):
                shop = el.get_text(strip=True)[:60]
                break

        # Link
        a = card.select_one("a[href*='/listing/']")
        if a and a.get("href"):
            href = a["href"]
            if not href.startswith("http"):
                href = urljoin("https://www.etsy.com", href)
            # Clean tracking params
            href = href.split("?")[0]

        # Review count
        for sel in ["span.wt-text-caption", ".review-stars", ".stars-svg-small"]:
            el = card.select_one(sel)
            if el:
                m = re.search(r"([\d,]+)\s*(sale|review|sold)", el.get_text(), re.I)
                if m:
                    reviews = m.group(0)
                    break

        if title or href:
            results.append({
                "title": title,
                "price": price,
                "shop": shop,
                "url": href,
                "reviews": reviews,
            })

    if not results:
        # Fall back to raw text extraction as a last resort
        text = _clean_text(r.text, 3000)
        return [{"raw_text": text, "note": "Could not parse structured results — raw page text returned instead"}]

    return results


def compare_to_shop(query: str, shop_id: str = "onbrandcraftz", limit: int = 10) -> dict:
    """
    Search Etsy for a query and compare results to a specific shop.

    Returns top competitors plus whether the given shop appears in results.
    """
    results = search_etsy(query, limit)
    if results and "error" in results[0]:
        return {"error": results[0]["error"]}

    shop_found = False
    competitors = []
    for r in results:
        if shop_id.lower() in (r.get("shop") or "").lower() or shop_id.lower() in (r.get("url") or "").lower():
            shop_found = True
        else:
            competitors.append(r)

    prices = []
    for r in competitors:
        m = re.search(r"[\d.]+", (r.get("price") or "").replace(",", ""))
        if m:
            try:
                prices.append(float(m.group()))
            except ValueError:
                pass

    return {
        "query": query,
        "shop_in_results": shop_found,
        "competitors": competitors,
        "price_range": {
            "min": min(prices) if prices else None,
            "max": max(prices) if prices else None,
            "avg": round(sum(prices) / len(prices), 2) if prices else None,
        },
    }
