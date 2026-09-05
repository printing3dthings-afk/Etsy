"""Frank must be able to read this shop's own skill docs.

Scott asked, 2026-09-05: "Is this knowledge being saved in frank so he knows
all this about 3d design and printing?" It was not. 300KB of measured
3D-printing findings lived in .claude/skills/3d-print-design/SKILL.md, which
Claude Code loads and Frank had no route to at all -- `_resolve_kb_doc` hard
-restricted reads to data/knowledge_base/ plus CLAUDE.md.

These tests pin the three things that had to be true for that to be fixed, and
one that was found while fixing it.
"""
import os, re as _re, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_kb_skill_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "kb-skill-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_skill_docs_are_listed():
    names = {d["filename"] for d in server._kb_docs()}
    check("skill_3d_print_design.md" in names,
          f"3d-print-design skill missing from the KB listing: {sorted(names)}")
    check("skill_verify_etsy_mutations.md" in names,
          "verify-etsy-mutations skill missing from the KB listing")


def test_skill_doc_resolves_and_has_real_content():
    target = server._resolve_kb_doc("skill_3d_print_design.md")
    check(target.is_file(), "skill_3d_print_design.md did not resolve to a real file")
    text = target.read_text()
    # The whole point of exposing this is the numbered techniques.
    check("## Technique 1 " in text or "## Technique 1 —" in text,
          "resolved doc does not look like the 3d-print-design skill")
    check(text.count("## Technique") >= 50,
          f"expected 50+ techniques, found {text.count('## Technique')}")


def test_skill_docs_are_searchable():
    hits = server._kb_search("contour rugosity")
    names = {r["filename"] for r in hits}
    check("skill_3d_print_design.md" in names,
          f"KB search missed the skill doc for a phrase only it contains: {sorted(names)}")


def test_traversal_still_rejected():
    from fastapi import HTTPException
    for bad in ("../CLAUDE.md", "../../etc/passwd", "skill_3d_print_design.txt",
                "../.claude/skills/3d-print-design/SKILL.md"):
        try:
            server._resolve_kb_doc(bad)
        except HTTPException:
            continue
        except Exception as e:
            _failures.append(f"{bad!r} raised {type(e).__name__}, expected HTTPException")
            continue
        _failures.append(f"{bad!r} resolved but should have been rejected")


def test_dockerignore_ships_what_the_server_reads():
    """A doc the server special-cases must actually exist in the image.

    This is the third time this repo's .dockerignore has silently excluded a
    file a runtime read path depends on -- see the two 2026-07-09 incidents in
    its own comments. `*.md` matches root-level markdown only, so CLAUDE.md was
    excluded from every image built here even though _resolve_kb_doc has a
    branch for it and the system prompt tells Frank to read it.
    """
    rules = (ROOT / ".dockerignore").read_text().splitlines()
    check("!CLAUDE.md" in rules,
          "CLAUDE.md is excluded from the image by `*.md` but _resolve_kb_doc "
          "special-cases it -- .dockerignore needs `!CLAUDE.md`")
    check(any(r.startswith("!.claude/skills") for r in rules),
          ".dockerignore has no negation re-including the skill docs Frank now reads")


def test_suite_never_writes_to_the_real_runbook():
    """No test may append to the git-tracked ops_runbook.md.

    Found 2026-09-05: test_health_check_reap and test_health_check_broadened
    exercise the escalation paths on purpose, and _append_ops_runbook_entry()
    writes to _OPS_RUNBOOK_PATH -- which is _volume_or_local(...), so with no
    volume mounted it falls back to the real data/knowledge_base copy. A suite
    run put eight fabricated incidents (TESTCRASH, TESTHUNG, a /tmp/... volume)
    into the document Frank reads as ground truth when Scott asks why something
    broke. Any test that can reach that writer must repoint _OPS_RUNBOOK_PATH
    at a tempfile first.
    """
    # Reaching the writer means calling something that appends, directly or via
    # the health loop. A bare "_escalate" substring was too loose on the first
    # pass -- it matched a test NAMED test_escalates_..., which writes nothing.
    reaches = ("_append_ops_runbook_entry(", "server._escalate", "_health_check_iteration(")
    # Two valid isolations: repoint the path, or mock the writer outright.
    # Matched against CODE only. The first version of this check searched the
    # raw file text, so the explanatory comment naming _OPS_RUNBOOK_PATH was
    # enough to satisfy it -- deleting the actual assignment left the guard
    # silently green. Verified by deleting it and watching this fail.
    isolates = (_re.compile(r"^\s*server\._OPS_RUNBOOK_PATH\s*=", _re.M),
                _re.compile(r'patch\.object\(\s*server\s*,\s*"_append_ops_runbook_entry"'))
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue  # this file names the patterns it searches for
        src = path.read_text()
        if not any(r in src for r in reaches):
            continue
        code = "\n".join(ln for ln in src.splitlines()
                         if not ln.lstrip().startswith("#"))
        check(any(pat.search(code) for pat in isolates),
              f"{path.name} can reach the ops_runbook writer but neither repoints "
              "server._OPS_RUNBOOK_PATH at a tempfile nor mocks "
              "_append_ops_runbook_entry — it will append test fixtures to the "
              "real git-tracked doc Frank reads as ground truth")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("KB SKILL DOC TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("KB SKILL DOC TESTS OK — Frank can list, read and search this shop's own "
          "skill docs, traversal is still rejected, and the image actually ships them.")


if __name__ == "__main__":
    run()
