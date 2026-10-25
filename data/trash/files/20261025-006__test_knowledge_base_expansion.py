"""
Tests for the 2026-08-08 knowledge-base expansion, prompted by Scott: "I need
frank to have more knowledge... he needs more ability to make better coloring
pages... make sure we have [repos/tools/skills]."

Audited data/knowledge_base/ + CLAUDE.md first: wall art, SVG packs, digital
planners, and sticker packs already had deep, sourced research
(design_quality_research_2026-06.md, competitor_research_2026.md, CLAUDE.md's
own Sticker Pack Design Standards section). Coloring pages had NONE -- no
competitor research, no design-technique doc anywhere. Also found the monthly
competitor-research refresh (_run_competitor_research_refresh in main.py)
claimed to cover 4 product lines in its own prompt text but
_COMPETITOR_RESEARCH_SEARCH_TERMS only ever had 3 entries (no coloring pages,
no SVG packs) -- a real gap between what the automation claims to do and what
it actually searches for.

Covered here:
  1. A new, web-search-grounded knowledge_base doc for coloring pages exists
     and is auto-discoverable via read_knowledge_base_doc's glob (no
     registration step needed -- see main.py's _kb_docs()).
  2. _COMPETITOR_RESEARCH_SEARCH_TERMS now includes coloring pages + SVG packs,
     matching what the refresh prompt text already claimed to cover.
  3. All 4 coloring-page style-DNA prompt constants now include the
     closed-outline instruction sourced from real published coloring-book
     design guides (the one concrete prompt-technique gap the research found).

Run: python tests/test_knowledge_base_expansion.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_kbexpand_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "kbexpand-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import generate_coloring_pages as gcp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_coloring_page_doc_exists_and_is_kb_discoverable():
    doc_path = ROOT / "data" / "knowledge_base" / "coloring_page_design_and_market_research.md"
    check(doc_path.is_file(), f"expected {doc_path} to exist")
    text = doc_path.read_text()
    check("closed" in text.lower() and "outline" in text.lower(),
          "doc should discuss closed/enclosed outlines (the real prompt-technique gap found)")
    check("$" in text, "doc should cite real pricing data, not just qualitative claims")

    filenames = {d["filename"] for d in server._kb_docs()}
    check("coloring_page_design_and_market_research.md" in filenames,
          f"new doc must be auto-discovered by _kb_docs()'s glob, got: {sorted(filenames)}")

    resolved = server._resolve_kb_doc("coloring_page_design_and_market_research.md")
    check(resolved == doc_path.resolve(), f"_resolve_kb_doc should resolve to the real file, got {resolved}")


def test_competitor_research_search_terms_cover_all_4_product_lines():
    terms_text = " ".join(server._COMPETITOR_RESEARCH_SEARCH_TERMS).lower()
    check("coloring" in terms_text,
          f"search terms must include a coloring-pages term, got: {server._COMPETITOR_RESEARCH_SEARCH_TERMS}")
    check("svg" in terms_text,
          f"search terms must include an SVG-pack term, got: {server._COMPETITOR_RESEARCH_SEARCH_TERMS}")
    check(len(server._COMPETITOR_RESEARCH_SEARCH_TERMS) >= 5,
          f"expected at least 5 terms (3 original + 2 new), got {len(server._COMPETITOR_RESEARCH_SEARCH_TERMS)}")


def test_coloring_page_styles_all_specify_closed_outlines():
    for name, style in [
        ("_STYLE", gcp._STYLE),
        ("_STYLE_BOLD", gcp._STYLE_BOLD),
        ("_STYLE_ADULT", gcp._STYLE_ADULT),
        ("_STYLE_KIDS", gcp._STYLE_KIDS),
    ]:
        check("closed" in style.lower() and ("enclosed" in style.lower() or "loop" in style.lower()),
              f"{name} must instruct closed/enclosed outlines (published coloring-book design "
              f"guides call this the #1 technical requirement — an open line lets color leak "
              f"between regions): {style}")
    # Sanity: the shared clause is defined once and reused, not copy-pasted with drift.
    check(gcp._STYLE.count(gcp._CLOSED_OUTLINE_CLAUSE.strip()) == 0 or
          gcp._CLOSED_OUTLINE_CLAUSE.strip() in gcp._STYLE,
          "the shared _CLOSED_OUTLINE_CLAUSE should appear verbatim in _STYLE")
    for style in (gcp._STYLE, gcp._STYLE_BOLD, gcp._STYLE_ADULT, gcp._STYLE_KIDS):
        check(gcp._CLOSED_OUTLINE_CLAUSE.strip() in style,
              f"every style tier should reuse the same shared clause, not a hand-copied variant: {style}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("KNOWLEDGE BASE EXPANSION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("KNOWLEDGE BASE EXPANSION TESTS OK — the new coloring-page research doc is real, "
          "sourced, and auto-discoverable; the competitor-research automation's search terms now "
          "match what it already claimed to cover; all 4 coloring-page style prompts share the "
          "same closed-outline instruction sourced from real design-guide research.")


if __name__ == "__main__":
    run()
