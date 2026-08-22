"""
Functional-correctness audit of the "publish a real Etsy listing" pipeline:
  - _publish_digital_listing   (tools/etsy_listing_tools.py)
  - _attach_digital_file       (tools/etsy_listing_tools.py)
  - set_listing_state          (tools/api_server/main.py, POST /api/listings/{id}/state)

EtsyAPIClient is mocked entirely at every call site -- no real network call is
ever made. This is a READ-testing audit: no application code is modified.
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_publish_path_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

# ROOT itself must be on sys.path so `import tools.etsy_listing_tools` (which
# does `from tools.data_store import DataStore` / `from tools.etsy_api import
# ...`) resolves `tools` as a real package -- the standard two-entry harness
# alone is not enough for a module that imports itself via the qualified
# `tools.*` name (main.py never needs this because it imports its Etsy/data
# helpers unqualified, via ROOT/tools being on sys.path directly).
for p in (ROOT, ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import tools.etsy_listing_tools as listing_tools  # noqa: E402
import tools.etsy_api as tools_etsy_api  # noqa: E402
import tools.data_store as tools_data_store  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fresh_store(tmpdir: str):
    """Build a brand-new DataStore instance backed by a throwaway JSON file
    under tmpdir. DataStore is a singleton (tools/data_store.py), so the
    class-level instance must be reset for every test that wants an isolated
    store -- otherwise tests would share state through the singleton, or
    worse, silently fall through to the real data/shop_data.json."""
    shop_data_path = os.path.join(tmpdir, "shop_data.json")
    tools_data_store.SHOP_DATA_FILE = shop_data_path
    tools_data_store.DataStore._instance = None
    store = tools_data_store.DataStore()
    return store


def _make_product(pid: str, file_path: str, **overrides) -> dict:
    product = {
        "id": pid,
        "title": f"{pid} Test Product",
        "product_type": "wall_art",
        "status": "approved",
        "qc_status": "approved",
        "spec_check_result": "PASS",
        "is_placeholder": False,
        "file_path": file_path,
        "listing_draft": {
            "title": "A" * 40 + " Printable Wall Art, Instant Download, Boho Decor" + "z" * 40,
            "description": "D" * 320,
            "tags": [f"tag{i} phrase" for i in range(13)],
            "price": 7.99,
            "quantity": 999,
            "taxonomy_id": 2097,
        },
    }
    product.update(overrides)
    return product


# ── _publish_digital_listing ─────────────────────────────────────────────────

def test_publish_requires_confirm_flag():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        result = json.loads(listing_tools._publish_digital_listing({"product_id": "DPX"}, store))
        check("error" in result, "publish without confirm=true should be rejected")


def test_publish_rejects_unknown_product():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        result = json.loads(
            listing_tools._publish_digital_listing({"product_id": "DOES_NOT_EXIST", "confirm": True}, store)
        )
        check("error" in result, "publishing a nonexistent product_id must error, not crash or fake success")


def test_publish_blocked_when_not_qc_approved():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        product = _make_product("DPX", f, status="draft", qc_status="not_run", spec_check_result=None)
        store.set([product], "digital_products")
        store.save()

        result = json.loads(listing_tools._publish_digital_listing({"product_id": "DPX", "confirm": True}, store))
        check("error" in result, "a product that hasn't passed QC must be blocked from publishing")
        check(
            store.get("digital_products", default=[])[0].get("status") != "listed",
            "a QC-blocked publish attempt must not mark the product as listed",
        )


def test_publish_success_records_consistent_state():
    """Happy path: Etsy returns a real listing_id -> product + main listings
    array must both reflect it accurately."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        product = _make_product("DPX", f)
        store.set([product], "digital_products")
        store.save()

        class FakeClientSuccess:
            def __init__(self, *a, **kw):
                self.access_token = "fake-token"

            def create_listing(self, listing_data):
                return {"listing_id": 999888777}

        with patch.object(listing_tools, "EtsyAPIClient", FakeClientSuccess), \
             patch.object(listing_tools, "is_configured", lambda: True):
            result = json.loads(listing_tools._publish_digital_listing({"product_id": "DPX", "confirm": True}, store))

        check(result.get("success") is True, f"expected success=True, got {result}")
        check(result.get("etsy_listing_id") == "999888777", f"expected etsy_listing_id 999888777, got {result.get('etsy_listing_id')!r}")

        saved = store.get("digital_products", default=[])[0]
        check(saved.get("status") == "listed", f"product status should become 'listed', got {saved.get('status')!r}")
        check(saved.get("etsy_listing_id") == "999888777", "product record must carry the real Etsy listing id")

        listings = store.get("listings", default=[])
        check(len(listings) == 1, f"expected exactly one main-listings record, got {len(listings)}")
        check(listings[0]["etsy_listing_id"] == "999888777", "main listings record must carry the real Etsy listing id")
        check(listings[0]["id"] == "DL999888777", f"expected id DL999888777, got {listings[0]['id']!r}")


def test_publish_etsy_api_error_leaves_product_unpublished():
    """If Etsy genuinely errors, the product must NOT be marked listed and
    no phantom main-listings record should appear."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        product = _make_product("DPX", f)
        store.set([product], "digital_products")
        store.save()

        class FakeClientError:
            def __init__(self, *a, **kw):
                self.access_token = "fake-token"

            def create_listing(self, listing_data):
                raise tools_etsy_api.EtsyAPIError(500, "Etsy is down")

        with patch.object(listing_tools, "EtsyAPIClient", FakeClientError), \
             patch.object(listing_tools, "is_configured", lambda: True):
            result = json.loads(listing_tools._publish_digital_listing({"product_id": "DPX", "confirm": True}, store))

        check("success" not in result or result.get("success") is not True,
              f"an Etsy API error must never be reported as success, got {result}")
        check("error" in result, "an Etsy API error must surface as an error field")

        saved = store.get("digital_products", default=[])[0]
        check(saved.get("status") == "approved", f"status must be left unchanged on failure, got {saved.get('status')!r}")
        check(not saved.get("etsy_listing_id"), "no listing id should be recorded on a failed publish")
        check(store.get("listings", default=[]) == [], "no main-listings record should be created on a failed publish")


def test_publish_rejects_malformed_response_missing_listing_id():
    """CONFIRMED BUG: if create_listing() returns a 2xx response body that is
    missing "listing_id" (no exception raised -- e.g. a malformed/unexpected
    Etsy response shape), _publish_digital_listing has no validation that the
    id it got back is real. It reports success=True with an EMPTY
    etsy_listing_id, marks the product "listed", builds a broken etsy_url
    (".../listing/"), and even creates a main-listings record with id "DL"
    (etsy_listing_id="" is falsy, so _add_to_main_listings's own fallback to
    f"DL{product['id']}" doesn't even trigger consistently -- it silently
    accepts the empty string). This is exactly the "silently reported as
    success" failure mode CLAUDE.md's zero-tolerance truthfulness rule exists
    to prevent, and it is live: run_wall_art_workflow.py calls
    _publish_digital_listing({'confirm': True}) directly and trusts
    pub['etsy_listing_id'] whenever pub.get('success') is True (see
    run_wall_art_workflow.py:456-461) -- it would print
    "published -> Etsy ID " (blank) and carry that blank id into every
    downstream step (photo upload, file attach) without any human ever
    telling it something is wrong.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        product = _make_product("DPX", f)
        store.set([product], "digital_products")
        store.save()

        class FakeClientMalformed:
            def __init__(self, *a, **kw):
                self.access_token = "fake-token"

            def create_listing(self, listing_data):
                # No exception, no EtsyAPIError -- just an unexpected/malformed
                # response shape (missing listing_id).
                return {"status": "ok"}

        with patch.object(listing_tools, "EtsyAPIClient", FakeClientMalformed), \
             patch.object(listing_tools, "is_configured", lambda: True):
            result = json.loads(listing_tools._publish_digital_listing({"product_id": "DPX", "confirm": True}, store))

        saved = store.get("digital_products", default=[])[0]

        # This is the bug: success=True + status="listed" with NO real listing id.
        bug_present = (
            result.get("success") is True
            and result.get("etsy_listing_id") == ""
            and saved.get("status") == "listed"
        )
        check(
            not bug_present,
            "CONFIRMED BUG: _publish_digital_listing reported success=True and "
            f"marked the product 'listed' with an EMPTY etsy_listing_id when "
            f"create_listing() returned a response missing 'listing_id'. "
            f"Full result: {result}. Saved product etsy_listing_id="
            f"{saved.get('etsy_listing_id')!r}, status={saved.get('status')!r}.",
        )


# ── _attach_digital_file ─────────────────────────────────────────────────────

def test_attach_rejects_unlisted_product():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        product = _make_product("DPX", f, etsy_listing_id=None)
        store.set([product], "digital_products")
        store.save()

        result = json.loads(listing_tools._attach_digital_file({"product_id": "DPX"}, store))
        check("error" in result, "attaching a file to a product with no etsy_listing_id must error")


def test_attach_rejects_placeholder():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        product = _make_product("DPX", f, etsy_listing_id="12345", is_placeholder=True)
        store.set([product], "digital_products")
        store.save()

        called = {"n": 0}

        class FakeClientShouldNotBeCalled:
            def __init__(self, *a, **kw):
                self.access_token = "fake-token"

            def upload_listing_file(self, listing_id, file_path):
                called["n"] += 1
                return {}

        with patch.object(tools_etsy_api, "EtsyAPIClient", FakeClientShouldNotBeCalled):
            result = json.loads(listing_tools._attach_digital_file({"product_id": "DPX"}, store))

        check("error" in result, "placeholder products must never have a file attached")
        check(called["n"] == 0, "placeholder guard must block BEFORE any Etsy API call is made")


def test_attach_uses_the_exact_registered_file_no_path_mixup():
    """The file that gets uploaded must be the exact product.file_path -- the
    same value that would have been fed to validate_digital_file() inside
    EtsyAPIClient.upload_listing_file(). Verifies there is no id/path mixup:
    a second, decoy product's file must never be the one actually sent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        real_file = os.path.join(tmpdir, "DPX_real.pdf")
        with open(real_file, "wb") as fh:
            fh.write(b"%PDF-1.4 real product bytes")
        decoy_file = os.path.join(tmpdir, "DPY_decoy.pdf")
        with open(decoy_file, "wb") as fh:
            fh.write(b"%PDF-1.4 decoy product bytes")

        product_x = _make_product("DPX", real_file, etsy_listing_id="11111")
        product_y = _make_product("DPY", decoy_file, etsy_listing_id="22222")
        store.set([product_x, product_y], "digital_products")
        store.save()

        captured = {}

        class FakeClientCapture:
            def __init__(self, *a, **kw):
                self.access_token = "fake-token"

            def upload_listing_file(self, listing_id, file_path):
                captured["listing_id"] = listing_id
                captured["file_path"] = file_path
                return {"listing_file_id": 555}

        with patch.object(tools_etsy_api, "EtsyAPIClient", FakeClientCapture):
            result = json.loads(listing_tools._attach_digital_file({"product_id": "DPX"}, store))

        check(result.get("success") is True, f"expected success, got {result}")
        check(captured.get("listing_id") == "11111", f"expected listing_id 11111 (DPX's), got {captured.get('listing_id')!r}")
        check(captured.get("file_path") == real_file, f"expected DPX's real file path, got {captured.get('file_path')!r}")
        check(captured.get("file_path") != decoy_file, "must never attach the decoy product's file")

        saved = next(p for p in store.get("digital_products", default=[]) if p["id"] == "DPX")
        check(saved.get("etsy_file_attached") is True, "DPX should be marked file-attached")
        saved_y = next(p for p in store.get("digital_products", default=[]) if p["id"] == "DPY")
        check(not saved_y.get("etsy_file_attached"), "DPY must NOT be marked file-attached -- only DPX's file was sent")


def test_attach_etsy_api_error_leaves_consistent_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        product = _make_product("DPX", f, etsy_listing_id="11111")
        store.set([product], "digital_products")
        store.save()

        class FakeClientError:
            def __init__(self, *a, **kw):
                self.access_token = "fake-token"

            def upload_listing_file(self, listing_id, file_path):
                raise tools_etsy_api.EtsyAPIError(500, "Etsy upload failed")

        with patch.object(tools_etsy_api, "EtsyAPIClient", FakeClientError):
            result = json.loads(listing_tools._attach_digital_file({"product_id": "DPX"}, store))

        check("error" in result, "an EtsyAPIError during upload must surface as a clean error")
        saved = store.get("digital_products", default=[])[0]
        check(not saved.get("etsy_file_attached"), "must not be marked attached when the upload actually failed")


def test_attach_catches_file_content_error_from_validation_gate():
    """CONFIRMED BUG: EtsyAPIClient.upload_listing_file() runs validate_digital_file()
    and the DP-code-vs-listing cross-check internally and raises FileContentError
    on a real mismatch -- per its own docstring, this is literally "the exact
    failure that shipped a customer the wrong art" protection. But
    _attach_digital_file only has `except EtsyAPIError` -- FileContentError
    is a plain Exception, not an EtsyAPIError subclass, so it is NOT caught
    here (contrast with _publish_digital_listing, which has both a specific
    except EtsyAPIError AND a catch-all except Exception). The result: the one
    safety net specifically built to stop a wrong-file shipment crashes the
    caller with an unhandled traceback instead of returning the clean
    {"error": ...} response every other failure mode in this file returns.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        product = _make_product("DPX", f, etsy_listing_id="11111")
        store.set([product], "digital_products")
        store.save()

        class FakeClientMismatch:
            def __init__(self, *a, **kw):
                self.access_token = "fake-token"

            def upload_listing_file(self, listing_id, file_path):
                raise tools_etsy_api.FileContentError(
                    "DP code mismatch: file belongs to DP9999, not this listing's DPX"
                )

        with patch.object(tools_etsy_api, "EtsyAPIClient", FakeClientMismatch):
            raised_unhandled = False
            result = None
            try:
                result = listing_tools._attach_digital_file({"product_id": "DPX"}, store)
            except tools_etsy_api.FileContentError:
                raised_unhandled = True

        check(
            not raised_unhandled,
            "CONFIRMED BUG: _attach_digital_file does not catch FileContentError "
            "(only EtsyAPIError) -- a real DP-code-mismatch safety-check failure "
            "raised inside EtsyAPIClient.upload_listing_file() propagates as an "
            "unhandled exception out of _attach_digital_file instead of the clean "
            "{'error': ...} JSON response every other failure path in this file "
            "returns.",
        )
        if not raised_unhandled:
            parsed = json.loads(result)
            check("error" in parsed, f"expected a clean error response, got {parsed}")


# ── set_listing_state (POST /api/listings/{listing_id}/state) ───────────────

def test_set_listing_state_rejects_invalid_state_value():
    async def _run():
        try:
            await server.set_listing_state(listing_id=123456, new_state="deleted", _token="test")
            return None
        except Exception as exc:
            return exc

    exc = asyncio.run(_run())
    check(exc is not None, "an invalid new_state value must be rejected")
    check(getattr(exc, "status_code", None) == 400, f"expected HTTP 400 for invalid state, got {getattr(exc, 'status_code', None)}")


def test_set_listing_state_success_updates_and_invalidates_cache():
    class FakeClientSuccess:
        def __init__(self, *a, **kw):
            pass

        def update_listing(self, listing_id, updates):
            check(updates == {"state": "inactive"}, f"expected state update payload, got {updates}")
            return {"listing_id": listing_id, "state": "inactive"}

    with server._cache_lock:
        server._cache["listings_active"] = ("stale", 0)
        server._cache["listings_inactive"] = ("stale", 0)

    with patch.object(server, "EtsyAPIClient", FakeClientSuccess):
        result = asyncio.run(server.set_listing_state(listing_id=987654, new_state="inactive", _token="test"))

    check(result == {"listing_id": 987654, "state": "inactive"}, f"unexpected result: {result}")
    with server._cache_lock:
        check("listings_active" not in server._cache, "successful state change must invalidate the listings_active cache")
        check("listings_inactive" not in server._cache, "successful state change must invalidate the listings_inactive cache")


def test_set_listing_state_foreign_listing_id_is_rejected_not_silently_applied():
    """A listing_id that does not belong to this shop: Etsy's own API scopes
    PATCH shops/{shop_id}/listings/{listing_id} to the authenticated shop, so
    a foreign id comes back as a real Etsy error (403/404) -- simulate that
    here and confirm the route surfaces it honestly rather than reporting a
    fake state change."""
    class FakeClientForeign:
        def __init__(self, *a, **kw):
            pass

        def update_listing(self, listing_id, updates):
            # main.py imports EtsyAPIClient/EtsyAPIError *unqualified* (`from
            # etsy_api import ...`, ROOT/tools on sys.path) while this test file
            # imports `tools.etsy_api` *qualified* to reach etsy_listing_tools.py
            # -- Python treats these as two different module cache entries
            # (sys.modules["etsy_api"] vs sys.modules["tools.etsy_api"]), so
            # they define two distinct EtsyAPIError classes despite being the
            # same source file. set_listing_state's `except EtsyAPIError` only
            # catches server.EtsyAPIError, so the fake client here must raise
            # that exact class for the test to exercise the real except clause.
            raise server.EtsyAPIError(404, "listing not found for this shop")

    with patch.object(server, "EtsyAPIClient", FakeClientForeign):
        async def _run():
            try:
                await server.set_listing_state(listing_id=42, new_state="active", _token="test")
                return None
            except Exception as exc:
                return exc

        exc = asyncio.run(_run())

    check(exc is not None, "a foreign/non-owned listing_id must not silently succeed")
    check(getattr(exc, "status_code", None) == 502, f"expected HTTP 502, got {getattr(exc, 'status_code', None)}")


def test_set_listing_state_retries_only_on_403_not_on_404():
    """update_listing's known-quirk retry (non-deterministic 403 'listing is
    not editable') should retry on 403, but must NOT retry on a 404 (foreign
    listing_id / genuinely wrong id) -- retrying a real ownership error just
    wastes time and could mask the honest failure behind extra latency."""
    call_count = {"n": 0}

    class FakeClient404:
        def __init__(self, *a, **kw):
            pass

        def update_listing(self, listing_id, updates):
            call_count["n"] += 1
            raise server.EtsyAPIError(404, "not found")  # see comment above on module identity

    with patch.object(server, "EtsyAPIClient", FakeClient404):
        async def _run():
            try:
                await server.set_listing_state(listing_id=42, new_state="active", _token="test")
            except Exception as exc:
                return exc
            return None

        exc = asyncio.run(_run())

    check(exc is not None, "expected an exception for a 404")
    check(call_count["n"] == 1, f"a 404 must not be retried (retryable only matches 403); got {call_count['n']} calls")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print(
        "FUNCTIONAL AUDIT TESTS OK -- publish/attach/state-change all behave "
        "correctly and honestly report failure."
    )


if __name__ == "__main__":
    run()
