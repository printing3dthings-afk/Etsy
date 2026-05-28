"""
Web search and URL fetching tools for the Company Intelligence Agent.
No API key required — uses DuckDuckGo HTML search + direct URL fetching.
"""

import re
import requests
import warnings
from html.parser import HTMLParser
from urllib.parse import quote_plus

from advertising.tools.package_store import PackageStore
from advertising.tools import ad_tools

# Suppress InsecureRequestWarning for SSL fallbacks
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
}
_TIMEOUT = 15


# ── HTML → text ──────────────────────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    _SKIP = frozenset(
        {"script", "style", "head", "meta", "link", "noscript", "svg", "path", "iframe"}
    )
    _BLOCK = frozenset(
        {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "section", "article"}
    )

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip: int = 0

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self._SKIP:
            self._skip += 1
        elif t in self._BLOCK and self._parts and self._parts[-1] != "\n":
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self._SKIP and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data):
        if self._skip == 0:
            text = data.strip()
            if text:
                self._parts.append(text)

    def get_text(self) -> str:
        raw = " ".join(p for p in self._parts if p.strip())
        return re.sub(r" {2,}", " ", raw).strip()


def _html_to_text(html: str, max_chars: int = 3500) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
        text = p.get_text()
    except Exception:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


# ── Search ────────────────────────────────────────────────────────────────────

def search_web(query: str, max_results: int = 7) -> str:
    """
    Search DuckDuckGo and return a formatted list of titles, URLs, and snippets.
    Falls back to the DDG Instant Answers JSON API if HTML parsing yields nothing.
    """
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "us-en"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        html = resp.text

        titles = re.findall(r'class="result__a"[^>]*>([^<]+)</a>', html)
        display_urls = re.findall(
            r'class="result__url"[^>]*>\s*(https?://[^\s<]+|[a-z0-9.-]+\.[a-z]{2,}[^\s<]*)\s*',
            html,
            re.IGNORECASE,
        )
        snippet_raw = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL
        )
        snippets = [re.sub(r"<[^>]+>", "", s).strip() for s in snippet_raw]

        results = []
        for i in range(min(max_results, len(titles))):
            title = titles[i].strip()
            url = display_urls[i].strip() if i < len(display_urls) else ""
            snippet = snippets[i][:220] if i < len(snippets) else ""
            url_display = url if url.startswith("http") else f"https://{url}"
            results.append(f"[{i+1}] {title}\n    {url_display}\n    {snippet}")

        if results:
            return f"Search: \"{query}\"\n\n" + "\n\n".join(results)

    except Exception:
        pass

    # Fallback: DuckDuckGo Instant Answers JSON API
    return _ddg_instant(query)


def _ddg_instant(query: str) -> str:
    try:
        url = (
            f"https://api.duckduckgo.com/?q={quote_plus(query)}"
            f"&format=json&no_html=1&skip_disambig=1"
        )
        data = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT).json()
        parts = []
        if data.get("AbstractText"):
            parts.append(f"Summary: {data['AbstractText']}")
        if data.get("AbstractURL"):
            parts.append(f"Source: {data['AbstractURL']}")
        if data.get("Answer"):
            parts.append(f"Answer: {data['Answer']}")
        for t in data.get("RelatedTopics", [])[:4]:
            if isinstance(t, dict) and t.get("Text"):
                parts.append(f"Related: {t['Text'][:200]}")
        return (
            f"Search: \"{query}\"\n\n" + "\n".join(parts)
            if parts
            else f"[No results found for: {query}]"
        )
    except Exception as e:
        return f"[Search unavailable: {e}]"


# ── Fetch URL ────────────────────────────────────────────────────────────────

def fetch_url(url: str, max_chars: int = 3500) -> str:
    """Fetch a URL and return its visible text content."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = requests.get(
            url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=True
        )
        ct = resp.headers.get("Content-Type", "")
        if resp.status_code == 200:
            if "html" in ct:
                text = _html_to_text(resp.text, max_chars)
                return f"[{url}]\n{text}" if text else f"[{url} — empty page]"
            elif "json" in ct:
                return f"[{url}]\n{resp.text[:max_chars]}"
            else:
                return f"[{url} — content type: {ct}]"
        else:
            return f"[HTTP {resp.status_code} for {url}]"

    except requests.exceptions.Timeout:
        return f"[Timeout fetching {url}]"
    except requests.exceptions.SSLError:
        try:
            resp = requests.get(
                url, headers=_HEADERS, timeout=_TIMEOUT, verify=False
            )
            return (
                f"[{url}]\n{_html_to_text(resp.text, max_chars)}"
                if resp.status_code == 200
                else f"[HTTP {resp.status_code} for {url}]"
            )
        except Exception:
            return f"[SSL error for {url}]"
    except Exception as e:
        return f"[Fetch error for {url}: {e}]"


# ── Tool definitions (passed to Claude API) ─────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "search_web",
        "description": (
            "Search the web using DuckDuckGo. Returns titles, URLs, and snippets. "
            "Use for: finding the company's website, reading reviews, news, competitors, "
            "social media profiles, and industry information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search query. Examples: 'Acme Corp official website', "
                        "'Acme Corp customer reviews', 'Acme Corp news 2026', "
                        "'best alternatives to Acme Corp'"
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default 7, max 10)",
                    "default": 7,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": (
            "Fetch and read the text content of any URL — company website pages, "
            "review sites (Trustpilot, G2, Yelp), news articles, LinkedIn pages, "
            "pricing pages, About pages, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch (include https://)",
                }
            },
            "required": ["url"],
        },
    },
    *ad_tools.COMMON_TOOL_DEFINITIONS,
]


def execute_tool(tool_name: str, tool_input: dict, store: PackageStore) -> str:
    if tool_name == "search_web":
        return search_web(tool_input["query"], tool_input.get("max_results", 7))
    if tool_name == "fetch_url":
        return fetch_url(tool_input["url"])
    return ad_tools.execute_common_tool(tool_name, tool_input, store)
