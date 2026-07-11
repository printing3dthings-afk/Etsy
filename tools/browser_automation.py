"""
Browser Automation Tools — Playwright-driven rendering for JS-heavy pages.

Fills the gap left by a plain `requests`-based fetch: some keyword-research
SaaS dashboards (eRank, Sale Samurai, Marmalead) and modern search result
pages render content client-side and need a real browser to see the final
DOM.

HONEST LIMITATION (verified by direct testing, June 2026): this sandbox's
outbound IP is blocked by Etsy at the network/edge level — etsy.com returns
HTTP 403 on every page (including the bare homepage) regardless of browser
realism, while Google/Bing/generic sites render normally. This is the same
"anti_scrape" condition a plain requests-based Etsy fetch hits. A real
browser does not get around an IP
block, so `check_etsy_search_rank` below detects and reports this condition
honestly instead of pretending to return real ranking data.

eRank / Sale Samurai / Marmalead require login credentials Scott hasn't
provided — `render_page` and `screenshot_url` work generically against
those sites once SS_LOGIN_EMAIL/PASSWORD-style env vars are added for the
specific tool, but no login flow is hardcoded here without a confirmed
account.

Environment quirks this module works around (do not "fix" these without
re-verifying — they reflect this sandbox's actual setup):
  - The pip-installed Playwright package expects a browser revision that
    isn't present; the sandbox instead ships a working Chromium at
    /opt/pw-browsers/chromium (a symlink) — launched via executable_path.
  - This sandbox has an outbound TLS-intercepting proxy; pages must be
    loaded with ignore_https_errors=True or every navigation fails with
    net::ERR_CERT_AUTHORITY_INVALID.
"""
from __future__ import annotations

import json
import os
import time

CHROMIUM_PATH = os.getenv("CHROMIUM_PATH", "/opt/pw-browsers/chromium")
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "browser_screenshots")

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "check_browser_status",
        "description": (
            "Verify the Playwright browser automation tool is functional in this environment. "
            "Returns whether Chromium launches successfully and a quick reachability check "
            "against a known-good site."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "render_page",
        "description": (
            "Load a URL in a real Chromium browser (full JS execution) and return the page title, "
            "visible text content (truncated), and HTTP status. Use for JS-heavy pages that a plain "
            "requests-based fetch (research_etsy_market/fetch_url) can't render — e.g. keyword "
            "research dashboards. NOTE: etsy.com itself returns HTTP 403 from this sandbox's IP "
            "regardless of rendering — this is a network-level block, not something this tool can "
            "bypass. See check_etsy_search_rank for the documented handling of that case."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to load"},
                "wait_for_selector": {
                    "type": "string",
                    "description": "Optional CSS selector to wait for before reading content (for slow-rendering SPAs)",
                },
                "max_chars": {"type": "integer", "default": 4000, "description": "Max chars of visible text to return"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "screenshot_url",
        "description": (
            "Load a URL in a real Chromium browser and save a full-page screenshot to disk. "
            "Useful for visual QA of generated listing content or rendering a non-Etsy page that "
            "needs JS to display correctly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to load"},
                "output_name": {"type": "string", "description": "Filename (without path) to save as, e.g. 'erank_dashboard.png'"},
                "full_page": {"type": "boolean", "default": True},
                "width": {"type": "integer", "default": 1440},
                "height": {"type": "integer", "default": 900},
            },
            "required": ["url", "output_name"],
        },
    },
    {
        "name": "check_etsy_search_rank",
        "description": (
            "Attempt to check where a listing ranks for a search keyword by rendering Etsy's live "
            "search results page in a browser. HONEST LIMITATION: this sandbox's outbound IP is "
            "blocked by Etsy at the network/edge level (verified — even the bare homepage returns "
            "HTTP 403), so this will almost certainly return a 'blocked' status rather than real "
            "rank data. Use the `search_etsy` tool (official Etsy Open API) "
            "for reliable competitor/listing data instead — it cannot show personalized search rank "
            "but is not IP-blocked."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword to check"},
                "shop_name": {"type": "string", "default": "onbrandcraftz", "description": "Shop name to look for in results"},
            },
            "required": ["keyword"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "check_browser_status":
        return _check_browser_status()
    if tool_name == "render_page":
        return _render_page(tool_input)
    if tool_name == "screenshot_url":
        return _screenshot_url(tool_input)
    if tool_name == "check_etsy_search_rank":
        return _check_etsy_search_rank(tool_input)
    return f"Unknown browser_automation tool: {tool_name}"


def _launch_context(playwright, width: int = 1440, height: int = 900):
    # Sandbox ships a Chromium at CHROMIUM_PATH (a symlink) that we launch explicitly.
    # On Railway (and anywhere `playwright install chromium` has run) that path does not
    # exist — omit executable_path so Playwright uses its own bundled Chromium.
    launch_kwargs = {"headless": True}
    if CHROMIUM_PATH and os.path.exists(CHROMIUM_PATH):
        launch_kwargs["executable_path"] = CHROMIUM_PATH
    browser = playwright.chromium.launch(**launch_kwargs)
    context = browser.new_context(
        ignore_https_errors=True,
        user_agent=DEFAULT_UA,
        viewport={"width": width, "height": height},
    )
    return browser, context


def _check_browser_status() -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return json.dumps({
            "status": "error",
            "error": "playwright package not installed. Run: pip install playwright && playwright install chromium",
        })

    using_bundled = not (CHROMIUM_PATH and os.path.exists(CHROMIUM_PATH))

    start = time.monotonic()
    try:
        with sync_playwright() as p:
            browser, context = _launch_context(p)
            page = context.new_page()
            resp = page.goto("https://example.com", timeout=15000)
            title = page.title()
            browser.close()
        latency = round((time.monotonic() - start) * 1000, 1)
        return json.dumps({
            "status": "ok",
            "chromium_path": "bundled (playwright default)" if using_bundled else CHROMIUM_PATH,
            "test_page_title": title,
            "test_http_status": resp.status if resp else None,
            "latency_ms": latency,
            "known_limitation": "etsy.com returns HTTP 403 from this sandbox's IP regardless of browser/rendering (network-level block, verified June 2026).",
        }, indent=2)
    except Exception as exc:
        return json.dumps({"status": "error", "error": str(exc)})


def _render_page(data: dict) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return json.dumps({"error": "playwright package not installed."})

    url = data["url"]
    wait_for_selector = data.get("wait_for_selector", "")
    max_chars = data.get("max_chars", 4000)

    try:
        with sync_playwright() as p:
            browser, context = _launch_context(p)
            page = context.new_page()
            resp = page.goto(url, timeout=20000, wait_until="domcontentloaded")
            if wait_for_selector:
                try:
                    page.wait_for_selector(wait_for_selector, timeout=8000)
                except Exception:
                    pass
            else:
                page.wait_for_timeout(1500)  # let JS settle

            title = page.title()
            text = page.evaluate("() => document.body ? document.body.innerText : ''")
            status = resp.status if resp else None
            browser.close()

        blocked = status in (403, 429) or (status and status >= 500)
        return json.dumps({
            "url": url,
            "http_status": status,
            "blocked": blocked,
            "title": title,
            "text_preview": text[:max_chars],
            "text_truncated": len(text) > max_chars,
        }, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "url": url})


def _screenshot_url(data: dict) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return json.dumps({"error": "playwright package not installed."})

    url = data["url"]
    output_name = data["output_name"]
    full_page = data.get("full_page", True)
    width = data.get("width", 1440)
    height = data.get("height", 900)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    output_path = os.path.join(SCREENSHOT_DIR, output_name)

    try:
        with sync_playwright() as p:
            browser, context = _launch_context(p, width=width, height=height)
            page = context.new_page()
            resp = page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            page.screenshot(path=output_path, full_page=full_page)
            status = resp.status if resp else None
            browser.close()

        return json.dumps({
            "url": url,
            "http_status": status,
            "output_path": output_path,
            "blocked": status in (403, 429) if status else False,
        }, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "url": url})


def _check_etsy_search_rank(data: dict) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return json.dumps({"error": "playwright package not installed."})

    keyword = data["keyword"]
    shop_name = data.get("shop_name", "onbrandcraftz").lower()
    search_url = f"https://www.etsy.com/search?q={keyword.replace(' ', '+')}"

    try:
        with sync_playwright() as p:
            browser, context = _launch_context(p)
            page = context.new_page()
            resp = page.goto(search_url, timeout=20000, wait_until="domcontentloaded")
            status = resp.status if resp else None
            html_len = len(page.content())
            browser.close()

        if status == 403 or html_len < 5000:
            return json.dumps({
                "status": "blocked",
                "keyword": keyword,
                "http_status": status,
                "explanation": (
                    "Etsy is blocking this sandbox's outbound IP at the network/edge level "
                    "(verified: even the bare homepage returns 403 here). This is not fixable "
                    "by better browser fingerprinting — it's an IP reputation block. Real rank "
                    "checking would need to run from a residential/non-datacenter IP (e.g. "
                    "Scott's own machine), or use a third-party rank-tracking service."
                ),
                "alternative": "Use the search_etsy tool (official Etsy Open API) for listing/price/competitor data — no rank position, but not IP-blocked.",
            }, indent=2)

        # If somehow not blocked, do a best-effort rank scan
        with sync_playwright() as p:
            browser, context = _launch_context(p)
            page = context.new_page()
            page.goto(search_url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            listing_links = page.eval_on_selector_all(
                "a[href*='/listing/']",
                "els => els.map(e => e.href)"
            )
            browser.close()

        rank = None
        for i, href in enumerate(listing_links, start=1):
            if shop_name in href.lower():
                rank = i
                break

        return json.dumps({
            "status": "ok",
            "keyword": keyword,
            "shop_name": shop_name,
            "rank": rank,
            "results_scanned": len(listing_links),
            "note": "Position reflects this unauthenticated/non-personalized session only — Etsy's 2026 algorithm personalizes results per shopper, so this is directional, not the rank every buyer sees.",
        }, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "keyword": keyword})


def is_available() -> bool:
    """True when Playwright is importable. A browser is then either at CHROMIUM_PATH
    (sandbox) or Playwright's bundled location (Railway, after `playwright install
    chromium`). Actual launch is confirmed by check_browser_status."""
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False
