#!/usr/bin/env python3
"""
CI guardrail against the "works in sandbox, breaks in prod" bug class that has
hit this codebase at least 10 separate times (qc_sweep.py, gen_planner_listing_
photos.py, generate_print_sizes.py, process_sticker_sheets.py, generate_planner.py
/planner_hyperlinker.py, backup_digital_products.py, and — found while building
THIS guardrail, 2026-07-17 — add_ai_disclosure.py, fetch_market_examples.py,
gen_lifestyle_scene.py, gen_sticker_listing_photos.py, post_scheduled_art.py):
a script hardcodes the absolute path of one specific sandbox checkout
(/home/user/Etsy) instead of resolving it portably (Path(__file__).resolve().
parent.parent, or resolve_dp_base()-style volume-aware resolution for product
files). It works fine when Claude runs it directly in a sandbox session, then
silently fails — or in several confirmed cases, crashes at import time before
any of the script's logic runs — the moment it's invoked from a different
working directory or the live Railway server process.

This check is deliberately narrow and low-false-positive: it flags the exact
literal string "/home/user/Etsy" appearing in a LIVE STRING LITERAL (something
that's actually a runtime value: sys.path.insert(0, '...'), open('...'), a
constant assignment, etc.) — not inside a module/function/class docstring
(legitimate documentation, e.g. a past-fix explanation or an illustrative
crontab example, several of which already exist in this codebase) or a '#'
comment. Uses ast (not a text/regex heuristic) specifically because the first
version of this script, built during the same pass that fixed those 10 bugs,
false-positived on its own docstring and on two crontab-example docstrings —
a plain substring/heuristic search can't reliably tell "this is documentation"
from "this is a real hardcoded path" the way parsing the actual syntax tree can.

Usage:
    python tools/check_hardcoded_paths.py            # scan tools/**/*.py
    python tools/check_hardcoded_paths.py --paths a.py b.py   # scan specific files
Exit code 0 = clean, 1 = violations found (prints each one).
"""
import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNED_LITERAL = "/home/user/Etsy"
# This file's own docstring/BANNED_LITERAL assignment legitimately contain the
# string being searched for — self-referential, not a violation.
SELF_PATH = Path(__file__).resolve()


def _docstring_nodes(tree: ast.Module) -> set[int]:
    """Every ast node id whose Constant IS a module/function/class docstring
    (the first statement of that body, per Python's own docstring convention),
    so they can be excluded below regardless of what they contain."""
    exempt_ids: set[int] = set()
    candidates: list[ast.AST] = [tree]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            candidates.append(node)
    for node in candidates:
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            exempt_ids.add(id(first.value))
    return exempt_ids


def find_violations(paths: list[Path]) -> list[tuple[Path, int, str]]:
    violations = []
    for path in paths:
        if path.resolve() == SELF_PATH:
            continue
        try:
            source = path.read_text()
            tree = ast.parse(source, filename=str(path))
        except (UnicodeDecodeError, OSError, SyntaxError):
            continue
        exempt = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if id(node) in exempt:
                continue
            if BANNED_LITERAL not in node.value:
                continue
            line = source.splitlines()[node.lineno - 1].strip() if node.lineno else ""
            violations.append((path, node.lineno, line))
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paths", nargs="*", default=None,
                     help="Specific files to check (default: every tools/**/*.py)")
    args = ap.parse_args()

    if args.paths:
        targets = [Path(p) for p in args.paths]
    else:
        targets = sorted((ROOT / "tools").rglob("*.py"))

    violations = find_violations(targets)
    if violations:
        print(f"HARDCODED-PATH CHECK FAILED — {len(violations)} occurrence(s) of "
              f"'{BANNED_LITERAL}' found in live code (not a docstring):\n")
        for path, lineno, line in violations:
            try:
                rel = path.relative_to(ROOT) if path.is_absolute() else path
            except ValueError:
                rel = path  # outside ROOT (e.g. an ad hoc --paths target) -- show as-is
            print(f"  {rel}:{lineno}: {line}")
        print(
            f"\nFix: resolve paths portably instead — Path(__file__).resolve().parent.parent "
            f"for the repo root, or a resolve_dp_base()-style helper (see tools/build_sticker_pack.py "
            f"or tools/backup_digital_products.py for the established pattern) for product files that "
            f"need to find the durable Railway volume in production. See data/knowledge_base/"
            f"ops_runbook.md's 2026-07-17 entries for the full pattern + why it matters."
        )
        return 1

    print(f"HARDCODED-PATH CHECK OK — no '{BANNED_LITERAL}' literals found in "
          f"{len(targets)} file(s) scanned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
