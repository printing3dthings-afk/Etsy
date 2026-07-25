"""
Regression tests for the 2026-07-25 full-code-audit sweep (Scott: "Check all
of franks code"). Two thorough scans across the ~47k-line in-scope surface
found 9 real bugs in the recurring classes this session already hit three
times; each fix here gets a literal regression test.

  P0  video_generator/ai_video OUTPUT_DIR: write side must equal main.py's
      _FILE_ROOTS["videos"] READ side exactly (f6a78c7 made the read side
      volume-aware but not the write side -- generated videos vanished from
      the Studio list on the hosted deploy).
  P1  post_scheduled_art SCHEDULE_PATH: durable via db.resolve_persistent_path
      with seed_from (was a git-tracked file reset on every redeploy ->
      duplicate-subject risk).
  P2  build_coloring_product/build_wallart_product: zero QC rows must yield
      "NOT CHECKED", never "PASS".
  P3  trash.py vault: volume-aware on hosted runtime (runtime archives were
      the sole copy of deleted todos/folders and died on redeploy); local
      repo behavior unchanged.
  P4  shop_health_check hero-hash baseline: durable path + no silently
      swallowed write failure (source-level assertions, per the repo's
      inspect-the-source precedent for subprocess-only scripts).
  P5  studio_list_videos / stage_photo: behavior unchanged after moving the
      blocking filesystem work off the event loop (first-ever coverage for
      both routes).
  P6  _validate_staged_action at-approval re-check uses _catalog_file_exists
      (last stale caller of the old prefix-only resolver).

HUB_FILES_DIR is set BEFORE any import because every path constant under
test is computed at module import time (same technique as
tests/test_video_staging_durability.py; run_all.py runs each test file as
its own subprocess so the env can't leak).

Run: python tests/test_audit_sweep_fixes.py
"""
import asyncio
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import traceback
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_audit_sweep_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "audit-sweep-test-not-a-real-secret")

_HUB_DIR = tempfile.mkdtemp(prefix="frank_audit_sweep_hub_")
os.environ["HUB_FILES_DIR"] = _HUB_DIR

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import ai_video  # noqa: E402
import video_generator  # noqa: E402
import trash  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _run_py(code: str, *, drop_hub: bool) -> str:
    """Run a python one-liner in a subprocess (optionally without HUB_FILES_DIR)
    and return stdout -- the only way to exercise the no-volume fallback branch
    of an import-time constant from inside this volume-mode test process."""
    env = dict(os.environ)
    if drop_hub:
        env.pop("HUB_FILES_DIR", None)
    res = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True,
        cwd=str(ROOT), env=env, timeout=120,
    )
    if res.returncode != 0:
        raise RuntimeError(f"subprocess failed: {res.stderr[-500:]}")
    return res.stdout.strip()


# ── P0: video write side == main.py read side, exactly ──────────────────

def test_video_generator_output_dir_equals_file_roots_videos():
    check(video_generator.OUTPUT_DIR == server._FILE_ROOTS["videos"],
          f"video_generator writes to {video_generator.OUTPUT_DIR} but main.py reads "
          f"{server._FILE_ROOTS['videos']} -- the f6a78c7 regression was exactly this disagreement")


def test_ai_video_output_dir_equals_file_roots_videos():
    check(ai_video.OUTPUT_DIR == server._FILE_ROOTS["videos"],
          f"ai_video writes to {ai_video.OUTPUT_DIR} but main.py reads {server._FILE_ROOTS['videos']}")
    check(ai_video.OUTPUT_DIR.is_absolute(),
          f"ai_video.OUTPUT_DIR must be absolute (was cwd-relative), got {ai_video.OUTPUT_DIR}")


def test_video_output_dirs_fall_back_to_repo_path_without_volume():
    out = _run_py(
        "import sys; sys.path.insert(0, 'tools');"
        "import ai_video, video_generator;"
        "print(video_generator.OUTPUT_DIR); print(ai_video.OUTPUT_DIR)",
        drop_hub=True,
    )
    lines = out.splitlines()
    expected = str(ROOT / "data" / "social" / "videos")
    check(lines[0] == expected, f"video_generator fallback: expected {expected}, got {lines[0]}")
    check(lines[1] == expected, f"ai_video fallback: expected {expected}, got {lines[1]}")


# ── P1: art scheduler state goes through resolve_persistent_path ─────────

def test_post_scheduled_art_schedule_path_uses_persistent_resolver_with_seed():
    # Patch the resolver BEFORE the module's import-time call, record the args,
    # and confirm SCHEDULE_PATH is whatever the resolver returned -- a real
    # functional test of the wiring without needing a writable /data here.
    # NOTE: post_scheduled_art imports `tools.api_server.db` (package path),
    # which is a DIFFERENT module object from the bare `db` main.py uses --
    # patch the one it actually calls.
    import importlib
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    tadb = importlib.import_module("tools.api_server.db")
    recorded = {}
    fake_target = Path(_HUB_DIR) / "art_schedule.json"

    def fake_resolve(relative, fallback, seed_from=None):
        recorded.update(relative=relative, fallback=fallback, seed_from=seed_from)
        return fake_target

    check("post_scheduled_art" not in sys.modules, "test ordering: post_scheduled_art must not be pre-imported")
    with patch.object(tadb, "resolve_persistent_path", fake_resolve):
        import post_scheduled_art  # noqa: F401
    check(recorded.get("relative") == "art_schedule.json", f"got {recorded}")
    check(recorded.get("seed_from") == ROOT / "data" / "art_schedule.json",
          f"seed_from must migrate the committed file's state on first durable run, got {recorded}")
    check(sys.modules["post_scheduled_art"].SCHEDULE_PATH == str(fake_target),
          f"SCHEDULE_PATH must be the resolver's result, got {sys.modules['post_scheduled_art'].SCHEDULE_PATH}")


# ── P2: zero QC rows can never report PASS ───────────────────────────────

def _stub_module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


def test_build_wallart_zero_qc_rows_reports_not_checked():
    import build_wallart_product
    empty_dir = Path(tempfile.mkdtemp(prefix="audit_sweep_wa_"))
    stubs = {
        "generate_print_sizes": _stub_module(
            "generate_print_sizes",
            UPSCALED_DIR=empty_dir, PRODUCT_FILES_DIR=empty_dir, PRINT_ZIPS_DIR=empty_dir,
            process_file=lambda *a, **k: {"status": "error"},
        ),
        "qc_sweep": _stub_module("qc_sweep", sweep=lambda only=None: []),
        "backup_digital_products": _stub_module("backup_digital_products", run=lambda: None),
    }
    buf = io.StringIO()
    with patch.dict(sys.modules, stubs), \
         patch.object(sys, "argv", ["build_wallart_product.py", "WA9999"]), \
         contextlib.redirect_stdout(buf):
        build_wallart_product.main()
    out = buf.getvalue()
    check("NOT CHECKED" in out, f"zero QC rows must report NOT CHECKED, output was:\n{out[-600:]}")
    check("qc=PASS" not in out, f"the literal false-PASS build log line must be impossible now:\n{out[-600:]}")


def test_build_coloring_zero_qc_rows_reports_not_checked():
    import build_coloring_product

    def _raise(*a, **k):
        raise RuntimeError("simulated generation failure")

    stubs = {
        "generate_coloring_pages": _stub_module(
            "generate_coloring_pages",
            NEW_THEME_SET_SIZE=20, generate_dynamic_theme_set=_raise,
            build_sets=lambda *a, **k: [],
        ),
        "qc_sweep": _stub_module("qc_sweep", sweep=lambda only=None: []),
        "backup_digital_products": _stub_module("backup_digital_products", run=lambda: None),
    }
    buf = io.StringIO()
    with patch.dict(sys.modules, stubs), \
         patch.object(sys, "argv", ["build_coloring_product.py", "COLOR9999", "--description", "a spooky pumpkin"]), \
         contextlib.redirect_stdout(buf):
        build_coloring_product.main()
    out = buf.getvalue()
    check("NOT CHECKED" in out, f"zero QC rows must report NOT CHECKED, output was:\n{out[-600:]}")
    check("qc=PASS" not in out, f"generation failed + zero checks must never log qc=PASS:\n{out[-600:]}")


# ── P3: trash vault durable on hosted runtime, unchanged locally ─────────

def test_trash_dir_nests_under_volume_and_round_trips():
    check(trash.TRASH_DIR == Path(_HUB_DIR) / "trash",
          f"with HUB_FILES_DIR set, trash must live on the volume, got {trash.TRASH_DIR}")
    entry_id = trash.archive_snippet("fake/source.py", "the deleted text", "audit sweep round-trip test")
    check((trash.FILES_DIR / f"{entry_id}__snippet.txt").exists(),
          "archive_snippet must write the byte-exact payload under the volume vault")
    check("the deleted text" in trash.LEDGER.read_text(encoding="utf-8"),
          "the ledger on the volume must contain the archived content")


def test_trash_dir_falls_back_to_repo_path_without_volume():
    out = _run_py(
        "import sys; sys.path.insert(0, 'tools'); import trash; print(trash.TRASH_DIR)",
        drop_hub=True,
    )
    check(out == str(ROOT / "data" / "trash"),
          f"without a volume the committed repo vault must be unchanged, got {out}")


# ── P4: shop_health_check baseline durable + unswallowed (source-level) ──

def test_shop_health_check_manifest_wiring():
    src = (ROOT / "tools" / "shop_health_check.py").read_text(encoding="utf-8")
    check("resolve_persistent_path" in src and "listing_image_manifest.json" in src,
          "hero-hash baseline must resolve through db.resolve_persistent_path")
    check("seed_from" in src, "the committed baseline must seed the volume copy on first run")
    check("could not save hero-hash baseline" in src,
          "a failed baseline write must produce a visible warning, not a bare pass")
    # The exact swallowed-error shape that caused the false-drift reports:
    check("MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))\n    except Exception:\n        pass" not in src,
          "the bare except:pass around the baseline write must be gone")


# ── P5: routes behave identically with the work moved off the event loop ─

def test_studio_list_videos_still_lists_and_sorts():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "older.mp4").write_bytes(b"a" * 10)
        (root / "newer.mp4").write_bytes(b"b" * 20)
        os.utime(root / "older.mp4", (1_000_000_000, 1_000_000_000))
        old_root = server._FILE_ROOTS["videos"]
        server._FILE_ROOTS["videos"] = root
        try:
            result = asyncio.run(server.studio_list_videos(_token="test"))
        finally:
            server._FILE_ROOTS["videos"] = old_root
    names = [v["path"] for v in result["videos"]]
    check(names == ["newer.mp4", "older.mp4"], f"newest-first listing must be unchanged, got {names}")
    check(result["videos"][0]["size"] == 20, f"stat sizes must be unchanged, got {result['videos'][0]}")


def test_stage_photo_route_still_stages_via_testclient():
    from fastapi.testclient import TestClient
    from PIL import Image as PILImage
    client = TestClient(server.app, base_url="https://testserver")
    auth = {"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"}
    img_buf = io.BytesIO()
    PILImage.new("RGB", (100, 100), (30, 30, 30)).save(img_buf, format="JPEG")  # dark: passes the pale gate
    with tempfile.TemporaryDirectory() as tmp:
        old_root = server._FILE_ROOTS["staged_photos"]
        server._FILE_ROOTS["staged_photos"] = Path(tmp)
        try:
            resp = client.post(
                "/api/queue/stage-photo",
                params={"listing_id": 4242, "rank": 1, "sku": "AUDIT_TEST",
                         "summary": "audit sweep route test", "design_paths": "[]"},
                content=img_buf.getvalue(), headers=auth,
            )
            check(resp.status_code == 200, f"got {resp.status_code}: {resp.text[:300]}")
            body = resp.json()
            check(body.get("action_id"), f"a staged action id must come back, got {body}")
            check((Path(tmp) / body["path"]).is_file(),
                  f"the photo must actually be written under staged_photos, got {body}")
        finally:
            server._FILE_ROOTS["staged_photos"] = old_root


# ── P6: at-approval re-check uses the catalog-aware resolver ─────────────

def test_validate_at_approval_recheck_handles_prefixed_catalog_files():
    payload = {
        "product_id": "AUDITX",
        "listing_data": {
            "title": "Kawaii Digital Planner 2026, GoodNotes iPad, Instant Download",
            "description": "x" * 350, "tags": [f"tag{i}" for i in range(13)], "price": 12.99,
        },
        "photo_paths": [],
        "file_paths": ["data/digital_products/product_files/AUDITX.pdf"],
    }
    fake_entry = {"product_id": "AUDITX", "name": "x", "category": "digital_planner",
                   "status": "ready_for_review", "etsy_listing_id": "",
                   "files": ["data/digital_products/product_files/AUDITX.pdf"]}
    seen_by_catalog_resolver = []

    def fake_catalog_exists(f):
        seen_by_catalog_resolver.append(f)
        return True

    with patch.object(server, "_product_file_abs_path", lambda rel: Path("/tmp/fake")), \
         patch.object(server, "_find_catalog_product", lambda pid: fake_entry), \
         patch.object(server, "_product_catalog_overrides", lambda: {}), \
         patch.object(server, "_catalog_file_exists", fake_catalog_exists):
        ok, msg = server._validate_staged_action(
            {"type": "create_listing", "payload": payload}, at_approval=True)
    check(ok, f"expected pass, got: {msg}")
    check(seen_by_catalog_resolver,
          "the at-approval re-check must route file existence through _catalog_file_exists "
          "(it was the last caller still passing the old prefix-only resolver)")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("AUDIT SWEEP FIXES TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("AUDIT SWEEP FIXES TESTS OK — video write/read roots agree exactly (volume and "
          "fallback), the art scheduler state is durably resolved with seeding, zero QC rows "
          "can never report PASS in either build script, the trash vault survives the hosted "
          "runtime while local behavior is untouched, the hero-hash baseline is durable with "
          "no swallowed write failure, both touched routes behave identically off the event "
          "loop, and the at-approval re-check uses the catalog-aware resolver.")


if __name__ == "__main__":
    run()
