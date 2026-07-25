"""
Tests for the "Etsy Listing" Create-screen tile feature (2026-07-25): typing
a product ID and generating a full, grounded AI listing (title/description/
13 tags/price) staged for approval.

Covers:
  - qc_sweep.py's extracted pure counting functions (sticker_zip_counts,
    coloring_zip_page_count) and that the two checkers built on them still
    behave the same
  - main.py's _extract_grounding_facts() against real tiny fixture PDF/ZIPs
  - the grounding retry-with-feedback loop in
    _generate_product_listing_content_core() (mocking server._anthropic_
    create -- the narrowest real dependency, not the generator itself)
  - the generated-content sidecar's read/write + precedence over the
    git-tracked hand-authored data/{id}_listing.json
  - the exact _PRODUCT_DELIVERABLE_SUFFIXES bug found during planning
  - the taxonomy extension + stage_product_publish gating for wall_art/
    coloring_pages
  - the new endpoint's auth wiring and error gating

Self-contained TestClient-and-plain-function-call pattern, same harness
shape as tests/test_produce_qc.py and tests/test_products_file_integrity.py.
Run: python tests/test_listing_content_generator.py
"""
import asyncio
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_listinggen_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "listinggen-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import qc_sweep  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_anthropic_response(text: str):
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def _make_pdf_bytes(n_pages: int) -> bytes:
    from PyPDF2 import PdfWriter
    w = PdfWriter()
    for _ in range(n_pages):
        w.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def _make_png_bytes(rgba: bool = True) -> bytes:
    from PIL import Image as PILImage
    im = PILImage.new("RGBA" if rgba else "RGB", (4, 4), (255, 0, 0, 128) if rgba else (255, 0, 0))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _make_zip_bytes(members: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return buf.getvalue()


# ── qc_sweep.py pure counting functions ─────────────────────────────────

def test_sticker_zip_counts_prefixed_layout():
    names = ["png_sheets/1.png", "png_sheets/2.png", "png_sheets/3.png",
             "individual_stickers/s1.png", "individual_stickers/s2.png",
             "README.txt"]
    counts = qc_sweep.sticker_zip_counts(names)
    check(counts == {"sheet_count": 3, "individual_sticker_count": 2},
          f"expected 3 sheets / 2 individual, got {counts}")


def test_sticker_zip_counts_legacy_flat_fallback():
    # No png_sheets/ prefix at all -- legacy pack stored sheets flat at root.
    names = ["sheet1.png", "sheet2.png", "sheet3.png", "sheet4.png", "sheet5.png"]
    counts = qc_sweep.sticker_zip_counts(names)
    check(counts["sheet_count"] == 5, f"legacy flat-pack fallback should count 5 sheets, got {counts}")
    check(counts["individual_sticker_count"] == 0, "no individual_stickers/ prefix present -> 0")


def test_coloring_zip_page_count():
    names = [f"page_{i:02d}.png" for i in range(1, 21)] + ["subfolder/extra.png", "README.txt"]
    count = qc_sweep.coloring_zip_page_count(names)
    check(count == 20, f"expected 20 root-level PNGs (subfolder one excluded), got {count}")


def _ensure_qc_sweep_image_imported():
    # qc_sweep.py deliberately imports PIL lazily inside sweep() (`global
    # Image; from PIL import Image`) so the module imports fine without PIL
    # present. check_sticker_zip()/check_coloring_zip() reference that
    # module-global directly -- calling them without going through sweep()
    # first (as these regression tests do, on purpose, to isolate the
    # counting logic) needs the same lazy import done once up front.
    from PIL import Image
    qc_sweep.Image = Image


def test_check_sticker_zip_still_reports_correctly_after_refactor():
    _ensure_qc_sweep_image_imported()
    rows, add = qc_sweep._rows()
    members = {f"png_sheets/s{i}.png": _make_png_bytes(rgba=True) for i in range(1, 6)}
    members.update({f"individual_stickers/i{i}.png": b"x" for i in range(1, 251)})
    with tempfile.TemporaryDirectory() as d:
        zpath = Path(d) / "TEST_sticker_pack.zip"
        zpath.write_bytes(_make_zip_bytes(members))
        qc_sweep.check_sticker_zip(zpath, add)
    sheet_row = next((r for r in rows if r["check"] == "sheet_count"), None)
    sticker_row = next((r for r in rows if r["check"] == "sticker_count"), None)
    check(sheet_row is not None and sheet_row["severity"] == "PASS" and "5 sheets" in sheet_row["detail"],
          f"5 sheets should PASS with correct count, got {sheet_row}")
    check(sticker_row is not None and sticker_row["severity"] == "PASS" and "250 individual stickers" in sticker_row["detail"],
          f"250 individual stickers should PASS with correct count, got {sticker_row}")


def test_check_coloring_zip_still_reports_correctly_after_refactor():
    from tools.generate_coloring_pages import NEW_THEME_SET_SIZE
    rows, add = qc_sweep._rows()
    members = {f"page_{i:02d}.png": b"x" for i in range(1, NEW_THEME_SET_SIZE + 1)}
    with tempfile.TemporaryDirectory() as d:
        zpath = Path(d) / "coloring_test1234_set_01.zip"
        zpath.write_bytes(_make_zip_bytes(members))
        qc_sweep.check_coloring_zip(zpath, add)
    page_row = next((r for r in rows if r["check"] == "page_count"), None)
    check(page_row is not None and page_row["severity"] == "PASS",
          f"exact NEW_THEME_SET_SIZE page count should PASS, got {page_row}")


# ── _extract_grounding_facts() against real tiny fixtures ───────────────

def test_extract_grounding_facts_digital_planner():
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        (vol / "data" / "test_fixture_dp9999").mkdir(parents=True)
        (vol / "data" / "test_fixture_dp9999" / "DP9999.pdf").write_bytes(_make_pdf_bytes(12))
        had_volume = "volume" in server._FILE_ROOTS
        old_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = vol
        try:
            entry = {"category": "digital_planner", "name": "Test Planner",
                     "files": ["data/test_fixture_dp9999/DP9999.pdf"]}
            facts, problems = server._extract_grounding_facts("DP9999", entry)
            check(problems == [], f"a valid 12pp PDF should produce no problems, got {problems}")
            check(facts.get("pdf_pages") == 12, f"expected pdf_pages=12, got {facts.get('pdf_pages')}")
        finally:
            if had_volume:
                server._FILE_ROOTS["volume"] = old_volume
            else:
                server._FILE_ROOTS.pop("volume", None)


def test_extract_grounding_facts_missing_deliverable_reports_problem():
    entry = {"category": "digital_planner", "name": "Ghost Planner", "files": []}
    facts, problems = server._extract_grounding_facts("DP0000GHOST", entry)
    check(len(problems) == 1 and "pdf pages" in problems[0],
          f"a digital_planner entry with zero files should report a missing-pdf_pages problem, got {problems}")


def test_extract_grounding_facts_wall_art_and_sticker_counts():
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        (vol / "data" / "test_fixture_wa9999").mkdir(parents=True)
        members = {"a.jpg": b"x", "b.jpg": b"x", "c.jpg": b"x"}
        (vol / "data" / "test_fixture_wa9999" / "WA9999_print_sizes.zip").write_bytes(_make_zip_bytes(members))
        had_volume = "volume" in server._FILE_ROOTS
        old_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = vol
        try:
            entry = {"category": "wall_art", "name": "Test Wall Art",
                     "files": ["data/test_fixture_wa9999/WA9999_print_sizes.zip"]}
            facts, problems = server._extract_grounding_facts("WA9999", entry)
            check(problems == [], f"a valid print-sizes ZIP should produce no problems, got {problems}")
            check(facts.get("zip_members") == 3, f"expected zip_members=3, got {facts.get('zip_members')}")
        finally:
            if had_volume:
                server._FILE_ROOTS["volume"] = old_volume
            else:
                server._FILE_ROOTS.pop("volume", None)


def test_extract_grounding_facts_sticker_and_coloring_counts():
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        (vol / "data" / "test_fixture_dp8888").mkdir(parents=True)
        sticker_members = {f"png_sheets/s{i}.png": b"x" for i in range(1, 6)}
        sticker_members.update({f"individual_stickers/i{i}.png": b"x" for i in range(1, 251)})
        (vol / "data" / "test_fixture_dp8888" / "DP8888_sticker_pack.zip").write_bytes(_make_zip_bytes(sticker_members))
        (vol / "data" / "test_fixture_dp8888" / "DP8888.pdf").write_bytes(_make_pdf_bytes(15))
        coloring_members = {f"page_{i:02d}.png": b"x" for i in range(1, 21)}
        (vol / "data" / "test_fixture_dp8888" / "coloring_test8888_set_01.zip").write_bytes(_make_zip_bytes(coloring_members))
        had_volume = "volume" in server._FILE_ROOTS
        old_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = vol
        try:
            entry = {"category": "coloring_pages", "name": "Test Set",
                      "files": ["data/test_fixture_dp8888/DP8888_sticker_pack.zip",
                                "data/test_fixture_dp8888/coloring_test8888_set_01.zip"]}
            facts, problems = server._extract_grounding_facts("DP8888", entry)
            check(problems == [], f"expected no problems, got {problems}")
            check(facts.get("sticker_sheets") == 5, f"expected 5 sticker sheets, got {facts.get('sticker_sheets')}")
            check(facts.get("individual_stickers") == 250, f"expected 250 individual stickers, got {facts.get('individual_stickers')}")
            check(facts.get("coloring_page_count") == 20, f"expected coloring_page_count=20, got {facts.get('coloring_page_count')}")
        finally:
            if had_volume:
                server._FILE_ROOTS["volume"] = old_volume
            else:
                server._FILE_ROOTS.pop("volume", None)


# ── Grounding retry-with-feedback loop ───────────────────────────────────

_FAKE_ENTRY = {"category": "digital_planner", "name": "Test Planner", "files": []}
_FAKE_FACTS = {"product_id": "DP9999", "category": "digital_planner", "name": "Test Planner", "pdf_pages": 12}


def test_generator_retries_on_bad_count_then_succeeds():
    # Descriptions must be >=300 chars (EtsyAPIClient.pre_publish_gate()'s DESC
    # floor, folded into this loop's acceptance check 2026-07-25) so the ONLY
    # signal under test here is the page-count mismatch, not an incidental
    # gate failure from an unrealistically short fixture description.
    filler = " Filled with fillable fields, hyperlinked tabs, and a kawaii cover design so it's ready to use the moment you download it."
    bad_json = json.dumps({
        "title": "Digital Planner 2026, GoodNotes iPad, Instant Download",
        "description": "Pages: 99 total in this planner." + filler * 3,
        "tags": [f"tag{i}" for i in range(13)],
    })
    good_json = json.dumps({
        "title": "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download",
        "description": "Pages: 12 total in this planner. A full grounded description." + filler * 3,
        "tags": [f"tag{i}" for i in range(13)],
    })
    responses = [_fake_anthropic_response(bad_json), _fake_anthropic_response(good_json)]
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=dict(_FAKE_ENTRY)), \
         patch.object(server, "_extract_grounding_facts", return_value=(dict(_FAKE_FACTS), [])), \
         patch.object(server, "_anthropic_create", side_effect=responses), \
         patch.object(server, "_write_generated_listing_content") as mock_write:
        result = asyncio.run(server._generate_product_listing_content_core("DP9999", max_attempts=3))
    check("content" in result, f"should eventually succeed, got {result}")
    check(result.get("attempts") == 2, f"expected exactly 2 attempts (fail then succeed), got {result.get('attempts')}")
    check(mock_write.called, "successful generation must write to the sidecar")


def test_generator_retries_when_tag_duplicates_title_phrase_then_succeeds():
    # Literal regression for the COLOR1002 incident (2026-07-25): the model
    # generated a valid, grounded description but included "coloring pages"
    # as a tag while the title was "Halloween Printable Coloring Pages,
    # Instant Download" -- passed the (old) grounding-only check, got saved,
    # and only failed when Scott tapped Publish, via EtsyAPIClient.
    # pre_publish_gate()'s "no tag may duplicate a title phrase" rule. The
    # generator must now catch this itself and retry within its own budget.
    long_desc = (
        "Get spooky this season with our Halloween printable coloring page set, perfect for "
        "creative minds of all ages looking for festive fun at home. You'll receive 20 fun "
        "designs in a convenient zip file ready for instant download, perfect for kids and "
        "adults alike who love a relaxing, festive activity any time of year."
    )
    bad_tags = ["coloring pages", "halloween activity", "kids crafts", "spooky theme",
                "home printing", "adult coloring", "seasonal printable", "festive craft",
                "pdf coloring", "stress relief art", "halloween coloring", "printable instant",
                "digital download"]
    good_tags = [t if t != "coloring pages" else "spooky page set" for t in bad_tags]
    bad_json = json.dumps({
        "title": "Halloween Printable Coloring Pages, Instant Download",
        "description": long_desc,
        "tags": bad_tags,
    })
    good_json = json.dumps({
        "title": "Halloween Printable Coloring Pages, Instant Download",
        "description": long_desc,
        "tags": good_tags,
    })
    coloring_entry = {"category": "coloring_pages", "name": "Halloween Set", "files": []}
    coloring_facts = {"product_id": "COLOR1002", "category": "coloring_pages", "name": "Halloween Set"}
    responses = [_fake_anthropic_response(bad_json), _fake_anthropic_response(good_json)]
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=coloring_entry), \
         patch.object(server, "_extract_grounding_facts", return_value=(coloring_facts, [])), \
         patch.object(server, "_anthropic_create", side_effect=responses), \
         patch.object(server, "_write_generated_listing_content") as mock_write:
        result = asyncio.run(server._generate_product_listing_content_core("COLOR1002", max_attempts=3))
    check("content" in result, f"should eventually succeed once the duplicate tag is fixed, got {result}")
    check(result.get("attempts") == 2, f"expected exactly 2 attempts (duplicate-tag reject, then fixed), got {result.get('attempts')}")
    check("coloring pages" not in (result.get("content") or {}).get("tags", []),
          "the saved content must not contain the duplicate tag that triggered the retry")
    check(mock_write.called, "the eventually-accepted content must be written to the sidecar")


def test_generator_never_saves_content_that_would_fail_publish_gate():
    # Same bug, but confirm it truly never accepts on any attempt if every
    # draft keeps the violation -- must give up with an error, not silently
    # save something that would only fail later at Scott's Publish tap.
    bad_json = json.dumps({
        "title": "Halloween Printable Coloring Pages, Instant Download",
        "description": "Too short to pass the description gate anyway.",
        "tags": ["coloring pages"] + [f"tag{i}" for i in range(12)],
    })
    coloring_entry = {"category": "coloring_pages", "name": "Halloween Set", "files": []}
    coloring_facts = {"product_id": "COLOR1002", "category": "coloring_pages", "name": "Halloween Set"}
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=coloring_entry), \
         patch.object(server, "_extract_grounding_facts", return_value=(coloring_facts, [])), \
         patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response(bad_json)), \
         patch.object(server, "_write_generated_listing_content") as mock_write:
        result = asyncio.run(server._generate_product_listing_content_core("COLOR1002", max_attempts=2))
    check("error" in result, f"should give up with an error, got {result}")
    check("duplicates a title phrase" in result["error"], f"error should name the specific gate failure, got {result['error']}")
    check(not mock_write.called, "content that would fail the publish gate must never reach the sidecar")


def test_generator_gives_up_after_max_attempts_never_writes():
    bad_json = json.dumps({
        "title": "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download",
        "description": "Pages: 999 total -- a made-up wrong count every time.",
        "tags": [f"tag{i}" for i in range(13)],
    })
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=dict(_FAKE_ENTRY)), \
         patch.object(server, "_extract_grounding_facts", return_value=(dict(_FAKE_FACTS), [])), \
         patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response(bad_json)), \
         patch.object(server, "_write_generated_listing_content") as mock_write:
        result = asyncio.run(server._generate_product_listing_content_core("DP9999", max_attempts=2))
    check("error" in result, f"should give up with an error, got {result}")
    check("999" in result["error"], f"error should name the specific mismatch, got {result['error']}")
    check(not mock_write.called, "a give-up must never write unverified content to the sidecar")


def test_generator_rejects_unsupported_category():
    entry = {"category": "sublimation", "name": "X", "files": []}
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=entry):
        result = asyncio.run(server._generate_product_listing_content_core("SUB9999"))
    check("error" in result and "sublimation" in result["error"], f"expected an unsupported-category error, got {result}")


def test_generator_rejects_unknown_product():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=None):
        result = asyncio.run(server._generate_product_listing_content_core("DOES_NOT_EXIST"))
    check("error" in result and "unknown product_id" in result["error"], f"expected unknown-product error, got {result}")


# ── Sidecar read/write + precedence over hand-authored file ─────────────

def test_generated_content_sidecar_roundtrip_and_precedence():
    with tempfile.TemporaryDirectory() as d:
        sidecar_path = Path(d) / "generated_listing_content.json"
        old_path = server._GENERATED_LISTING_CONTENT_PATH
        server._GENERATED_LISTING_CONTENT_PATH = sidecar_path
        hand_authored_path = ROOT / "data" / "dp9999test_listing.json"
        try:
            server._write_generated_listing_content("DP9999TEST", {
                "product_id": "DP9999TEST", "title": "Generated Title",
                "description": "Generated description.", "tags": ["a"], "price": 12.99,
            })
            check(server._generated_listing_content().get("DP9999TEST", {}).get("title") == "Generated Title",
                  "generated content should round-trip through the sidecar")

            with patch.object(server, "_find_catalog_product",
                               return_value={"category": "digital_planner", "name": "X", "files": []}), \
                 patch.object(server, "_build_products_status",
                               return_value=[{"status": "draft", "listing_id": ""}]), \
                 patch.object(server, "_qc_check_product", return_value={"verdict": "pass"}):
                review = server._gather_product_review("DP9999TEST")
            check(review["has_content"] is True, "review should fall back to the generated sidecar when no hand-authored file exists")
            check(review["content"]["title"] == "Generated Title", f"expected generated title, got {review['content']}")

            hand_authored_path.write_text(json.dumps({
                "title": "Hand-Authored Title", "description": "Hand-authored.",
                "tags": ["b"], "price": 9.99,
            }))
            with patch.object(server, "_find_catalog_product",
                               return_value={"category": "digital_planner", "name": "X", "files": []}), \
                 patch.object(server, "_build_products_status",
                               return_value=[{"status": "draft", "listing_id": ""}]), \
                 patch.object(server, "_qc_check_product", return_value={"verdict": "pass"}):
                review2 = server._gather_product_review("DP9999TEST")
            check(review2["content"]["title"] == "Hand-Authored Title",
                  f"the hand-authored file must win over the generated sidecar, got {review2['content']}")
        finally:
            server._GENERATED_LISTING_CONTENT_PATH = old_path
            hand_authored_path.unlink(missing_ok=True)


# ── _PRODUCT_DELIVERABLE_SUFFIXES regression (the bug found during planning) ──

def test_wall_art_print_sizes_zip_now_counted_as_deliverable():
    with patch.object(server, "_find_catalog_product",
                       return_value={"category": "wall_art", "name": "X",
                                      "files": ["data/wall_art_test/WA9999_print_sizes.zip"]}), \
         patch.object(server, "_build_products_status",
                       return_value=[{"status": "draft", "listing_id": ""}]), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server, "_catalog_file_url", return_value="/files/WA9999_print_sizes.zip"), \
         patch.object(server, "_qc_check_product", return_value={"verdict": "pass"}):
        review = server._gather_product_review("WA9999")
    names = [d["name"] for d in review["deliverables"]]
    check("WA9999_print_sizes.zip" in names,
          f"a Wall Art print-sizes ZIP must now appear in deliverables (was silently dropped before the fix), got {names}")


def test_coloring_pages_set_zip_now_counted_as_deliverable():
    with patch.object(server, "_find_catalog_product",
                       return_value={"category": "coloring_pages", "name": "X",
                                      "files": ["data/coloring_test/coloring_test1234_set_01.zip"]}), \
         patch.object(server, "_build_products_status",
                       return_value=[{"status": "draft", "listing_id": ""}]), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server, "_catalog_file_url", return_value="/files/coloring_test1234_set_01.zip"), \
         patch.object(server, "_qc_check_product", return_value={"verdict": "pass"}):
        review = server._gather_product_review("COLOR1234")
    names = [d["name"] for d in review["deliverables"]]
    check("coloring_test1234_set_01.zip" in names,
          f"a Coloring Pages set ZIP must now appear in deliverables, got {names}")


# ── Taxonomy extension + stage_product_publish gating ────────────────────

def test_taxonomy_extended_to_wall_art_and_coloring_pages():
    check(server._PRODUCT_TAXONOMY_BY_CATEGORY.get("wall_art") is not None,
          "wall_art must have a taxonomy_id set")
    check(server._PRODUCT_TAXONOMY_BY_CATEGORY.get("coloring_pages") is not None,
          "coloring_pages must have a taxonomy_id set")


def test_resolve_category_taxonomy_id_unknown_category_returns_none():
    check(server._resolve_category_taxonomy_id("totally_bogus_category") is None,
          "a category with no hardcoded default at all must return None (never guess)")


def test_resolve_category_taxonomy_id_short_circuits_once_resolved():
    # Once a category has been through one live-check attempt this process
    # lifetime, _resolve_category_taxonomy_id() must return the cached
    # RESOLVED value directly without touching the catalog file or Etsy
    # again -- verified by patching EtsyAPIClient and confirming it's never
    # called. Uses a resolved value that DIFFERS from the hardcoded default
    # to also prove the cache stores the corrected value, not just "checked".
    server._CATEGORY_TAXONOMY_RESOLVED["wall_art"] = 9999999
    try:
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            result = server._resolve_category_taxonomy_id("wall_art")
        check(not mock_client_cls.called, "an already-resolved category must never call EtsyAPIClient again")
        check(result == 9999999,
              f"should return the cached RESOLVED value (not the stale hardcoded default), got {result}")
    finally:
        server._CATEGORY_TAXONOMY_RESOLVED.pop("wall_art", None)


def test_resolve_category_taxonomy_id_caches_a_live_correction_for_later_calls():
    # Regression test for the 2026-07-26 bug: a corrected/discovered value
    # from a live check must apply to every subsequent call in this process,
    # not just the one call that happened to trigger the live check.
    server._CATEGORY_TAXONOMY_RESOLVED.pop("wall_art", None)
    try:
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            mock_client_cls.return_value.get_listing.return_value = {"taxonomy_id": 2097}
            first = server._resolve_category_taxonomy_id("wall_art")
            check(mock_client_cls.called, "first call for an unresolved category must attempt the live check")
        check(first == 2097, f"first call should return the live-discovered value, got {first}")
        with patch.object(server, "EtsyAPIClient") as mock_client_cls2:
            second = server._resolve_category_taxonomy_id("wall_art")
        check(not mock_client_cls2.called, "second call must use the cached resolved value, not re-check")
        check(second == 2097, f"second call must also return the corrected value, got {second}")
    finally:
        server._CATEGORY_TAXONOMY_RESOLVED.pop("wall_art", None)


def test_resolve_category_taxonomy_id_falls_back_when_live_check_fails():
    # First-ever check for this category (not yet cached) -- if a live
    # listing exists in the real catalog for this category but the Etsy
    # call itself fails (e.g. no credentials in this environment), the
    # resolver must fall back to the hardcoded default rather than raise
    # or return None.
    server._CATEGORY_TAXONOMY_RESOLVED.pop("wall_art", None)
    try:
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            mock_client_cls.return_value.get_listing.side_effect = Exception("no credentials in this environment")
            result = server._resolve_category_taxonomy_id("wall_art")
        check(result == server._PRODUCT_TAXONOMY_BY_CATEGORY["wall_art"],
              f"a failed live check must fall back to the hardcoded default, got {result}")
    finally:
        server._CATEGORY_TAXONOMY_RESOLVED.pop("wall_art", None)


def test_resolve_category_taxonomy_id_discovers_value_for_category_with_no_default():
    # 2026-07-26 broadening: a category with NO entry in
    # _PRODUCT_TAXONOMY_BY_CATEGORY at all (e.g. 3d_print_physical --
    # deliberately left unset since 2078 would be actively wrong for a
    # physical good) must still attempt a live check if the catalog has a
    # live listing for it -- previously this short-circuited to None before
    # ever looking.
    server._CATEGORY_TAXONOMY_RESOLVED.pop("3d_print_physical", None)
    check("3d_print_physical" not in server._PRODUCT_TAXONOMY_BY_CATEGORY,
          "test assumes 3d_print_physical has no hardcoded default -- update this test if that changes")
    fake_catalog = json.dumps([
        {"category": "3d_print_physical", "etsy_listing_id": "5551234"},
    ])
    try:
        with patch.object(server, "EtsyAPIClient") as mock_client_cls, \
             patch.object(Path, "read_text", return_value=fake_catalog):
            mock_client_cls.return_value.get_listing.return_value = {"taxonomy_id": 1633}
            result = server._resolve_category_taxonomy_id("3d_print_physical")
        check(result == 1633,
              f"a category with no hardcoded default must still discover a real value from a live listing, got {result}")
    finally:
        server._CATEGORY_TAXONOMY_RESOLVED.pop("3d_print_physical", None)


def test_stage_product_publish_stages_wall_art_when_fully_fixtured():
    fake_review = {
        "product_id": "WA9999", "category": "wall_art", "status": "draft",
        "listing_id": "", "has_content": True,
        "content": {"title": "Sunset Botanical Printable Wall Art, Instant Download, Boho",
                    "description": "Instant download printable wall art — " + ("x" * 300),
                    "tags": [f"tag{i}" for i in range(13)], "price": 6.99, "shop_section_id": None},
        "photos": [], "deliverables": [{"name": "WA9999_print_sizes.zip", "rel": "data/x.zip", "exists": True}],
        "qc": {"verdict": "pass", "message": ""},
    }
    with patch.object(server, "_gather_product_review", return_value=fake_review), \
         patch.object(server, "_resolve_category_taxonomy_id", return_value=2078), \
         patch.object(server.db, "list_actions", return_value=[]), \
         patch.object(server, "_validate_staged_action", return_value=(True, "")), \
         patch.object(server.db, "enqueue_action", return_value=42):
        result = asyncio.run(server.stage_product_publish("WA9999", _token="test"))
    check(result.get("staged") is True, f"a fully-fixtured wall_art product should stage successfully, got {result}")
    check(result.get("action_id") == 42, f"expected the mocked action_id, got {result}")


# ── File-resolution regression (COLOR1003, 2026-07-25) ──────────────────
# _validate_staged_action's create_listing branch and _execute_create_listing_
# staged_action's upload loops used to call _product_file_abs_path(rel)
# directly on photo_paths/file_paths -- but those are raw product_catalog.json
# "files" strings (see _gather_product_review's `"rel": f`), which in every
# real catalog entry carry the full "data/digital_products/..." prefix.
# _product_file_abs_path() expects a path already relative to _FILE_ROOTS
# ["products"] (prefix stripped), so joining it with the still-prefixed rel
# double-nested the path and could never resolve -- even though the review
# endpoint (which correctly uses _catalog_file_abs_path()) had just confirmed
# the exact same file exists. This blocked EVERY real publish attempt, not
# just coloring_pages -- the prior test above never caught it because it
# mocks _validate_staged_action away entirely.

def test_validate_staged_action_resolves_real_prefixed_catalog_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        products_root = Path(tmpdir)
        nested = products_root / "coloring_pages" / "sets"
        nested.mkdir(parents=True)
        (nested / "coloring_color1003_set_01.zip").write_bytes(b"fake zip")
        old_products_root = server._FILE_ROOTS["products"]
        server._FILE_ROOTS["products"] = products_root
        try:
            candidate = {
                "type": "create_listing",
                "payload": {
                    "product_id": "COLOR1003",
                    "listing_data": {
                        "title": "Halloween Printable Coloring Pages, Instant Download",
                        "description": "x" * 320,
                        "tags": [f"tag{i}" for i in range(13)],
                        "price": 6.99,
                    },
                    "photo_paths": [],
                    "file_paths": ["data/digital_products/coloring_pages/sets/coloring_color1003_set_01.zip"],
                },
            }
            ok, msg = server._validate_staged_action(candidate)
        finally:
            server._FILE_ROOTS["products"] = old_products_root
    check(ok, f"a real catalog-style prefixed path must resolve and pass, got: {msg}")


def test_execute_create_listing_uploads_resolve_real_prefixed_catalog_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        products_root = Path(tmpdir)
        nested = products_root / "coloring_pages" / "sets"
        nested.mkdir(parents=True)
        real_file = nested / "coloring_color1003_set_01.zip"
        real_file.write_bytes(b"fake zip")
        old_products_root = server._FILE_ROOTS["products"]
        server._FILE_ROOTS["products"] = products_root
        try:
            with patch.object(server, "EtsyAPIClient") as MockClient, \
                 patch.object(server, "_write_product_catalog_override") as mock_override:
                instance = MockClient.return_value
                instance.create_listing.return_value = {"listing_id": 999}
                instance.upload_listing_file.return_value = {"listing_file_id": 55}
                action = {"payload": {
                    "product_id": "COLOR1003",
                    "listing_data": {"title": "x"},
                    "photo_paths": [],
                    "file_paths": ["data/digital_products/coloring_pages/sets/coloring_color1003_set_01.zip"],
                }}
                result = server._execute_create_listing_staged_action(action)
        finally:
            server._FILE_ROOTS["products"] = old_products_root
    check("upload_errors" not in result, f"the real file must resolve and upload cleanly, got {result.get('upload_errors')}")
    check(instance.upload_listing_file.called, "upload_listing_file must actually be invoked once the file resolves")
    called_path = instance.upload_listing_file.call_args[0][1]
    check(called_path == str(real_file), f"expected the real resolved path {real_file}, got {called_path}")
    check(mock_override.called, "a successful create must still write the catalog override")


# ── Endpoint gating ────────────────────────────────────────────────────

def test_generate_content_endpoint_rejects_unknown_product():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=None):
        try:
            asyncio.run(server.generate_product_listing_content("DOES_NOT_EXIST", _token="test"))
            check(False, "should have raised HTTPException for an unknown product")
        except server.HTTPException as exc:
            check(exc.status_code == 400, f"expected 400, got {exc.status_code}")


def test_generate_content_endpoint_rejects_unsupported_category():
    entry = {"category": "sublimation", "name": "X", "files": []}
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=entry):
        try:
            asyncio.run(server.generate_product_listing_content("SUB9999", _token="test"))
            check(False, "should have raised HTTPException for an unsupported category")
        except server.HTTPException as exc:
            check(exc.status_code == 400, f"expected 400, got {exc.status_code}")


def test_generate_content_endpoint_uses_rate_limited_auth():
    route = next((r for r in server.app.routes
                  if getattr(r, "path", "") == "/api/products/{product_id}/generate-listing-content"), None)
    check(route is not None, "the new route must be registered")
    if route is not None:
        deps = [d.call for d in route.dependant.dependencies]
        check(server._rate_limited_auth in deps,
              f"the endpoint must use _rate_limited_auth (costs LLM $ + writes state), got deps calling {deps}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("LISTING CONTENT GENERATOR TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("LISTING CONTENT GENERATOR TESTS OK — fact extraction, grounding retry/give-up, "
          "the COLOR1002 duplicate-tag pre-publish-gate regression, sidecar precedence, "
          "the deliverable-suffix regression, taxonomy extension, and endpoint gating all verified.")


if __name__ == "__main__":
    run()
