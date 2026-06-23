#!/usr/bin/env python3
"""
OnBrandCraftz — Recycle Bin / Deletion Safety Net
=================================================
Mission: "Providing the best and most accurate transaction for our customers
so we can grow responsibly." — nothing we remove should be unrecoverable by
accident.

Scott's rule (2026-06-23): "I want a file that keeps anything you delete for 30
days so in case it was accidentally removed or caused an issue we can pull
whatever we need back."

This is that recycle bin. BEFORE deleting any code block or file, archive it
here first. Everything lands in a committed, human-readable ledger so it
survives this environment's ephemeral container (uncommitted files are lost
when the session ends — that's why the vault lives inside the repo, not /tmp).

Vault layout (all committed to git):
  data/trash/DELETED.md   — human-readable ledger: one entry per deletion, with
                            a machine-parseable header comment, the reason, and
                            the verbatim content inlined for easy eyeballing.
  data/trash/files/       — byte-exact payload copies (one per entry) so a
                            restore is exact and never depends on re-parsing
                            markdown. Snippet payloads are <id>__snippet.txt;
                            archived whole files keep their basename.

Retention: entries older than 30 days are pruned automatically after every
archive, and a daily cron also runs `--prune` so time-based expiry happens even
on days with no deletions.

Usage:
  # From Python (preferred when removing code in an automated edit):
  from tools.trash import archive_snippet, archive_file
  archive_snippet("path/to/file.py", "<the exact removed text>", "why")
  archive_file("path/to/whole_file.bin", "why")        # moves the file in

  # From the CLI:
  python tools/trash.py --list
  python tools/trash.py --add-file path/to/file --reason "obsolete script"
  python tools/trash.py --restore 20260623-001            # -> stdout (snippet) or original path (file)
  python tools/trash.py --restore 20260623-001 dest.txt   # -> explicit dest
  python tools/trash.py --prune
"""

import argparse
import pathlib
import re
import shutil
import sys
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRASH_DIR = ROOT / "data" / "trash"
FILES_DIR = TRASH_DIR / "files"
LEDGER = TRASH_DIR / "DELETED.md"
RETENTION_DAYS = 30

_LEDGER_HEADER = """# Deletion Recycle Bin

> Everything deleted by an automated edit (code blocks or whole files) is
> archived here first, kept for **{days} days**, then auto-pruned. To recover
> something, run `python tools/trash.py --restore <id>` (or just copy it back
> out of the fenced block below). Byte-exact copies also live in
> `data/trash/files/`.

""".format(days=RETENTION_DAYS)

# Each entry is delimited by these markers so prune()/restore() can find it
# without a markdown parser. The opening marker carries all metadata.
_OPEN_RE = re.compile(
    r'<!-- TRASH id=(?P<id>[0-9]{8}-[0-9]{3}) date=(?P<date>\d{4}-\d{2}-\d{2}) '
    r'kind=(?P<kind>\w+) source="(?P<source>[^"]*)" reason="(?P<reason>[^"]*)" -->'
)


def _now():
    return datetime.now()


def _today_str():
    return _now().strftime("%Y-%m-%d")


def _ensure_vault():
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    if not LEDGER.exists():
        LEDGER.write_text(_LEDGER_HEADER, encoding="utf-8")


def _read_ledger():
    _ensure_vault()
    return LEDGER.read_text(encoding="utf-8")


def _split_entries(text):
    """Return (header_text, [entry_blocks]). Each entry block is the full text
    from its opening <!-- TRASH ... --> marker up to (and including) its
    matching <!-- /TRASH id --> closer."""
    entries = []
    first = None
    for m in _OPEN_RE.finditer(text):
        eid = m.group("id")
        if first is None:
            first = m.start()
        closer = "<!-- /TRASH {} -->".format(eid)
        cidx = text.find(closer, m.end())
        if cidx == -1:
            continue  # malformed; skip rather than corrupt
        end = cidx + len(closer)
        entries.append({"id": eid, "date": m.group("date"), "kind": m.group("kind"),
                        "source": m.group("source"), "reason": m.group("reason"),
                        "block": text[m.start():end], "match": m})
    header = text[:first] if first is not None else text
    return header, entries


def _next_id(entries):
    today = _now().strftime("%Y%m%d")
    seq = 1 + sum(1 for e in entries if e["id"].startswith(today))
    return "{}-{:03d}".format(today, seq)


def _fence_for(content):
    """CommonMark-safe fence: longer than any backtick run in the content."""
    longest = 0
    for run in re.findall(r"`+", content):
        longest = max(longest, len(run))
    return "`" * max(3, longest + 1)


def _lang_for(source):
    ext = pathlib.Path(source).suffix.lower()
    return {".py": "python", ".js": "javascript", ".css": "css", ".html": "html",
            ".json": "json", ".md": "markdown", ".sh": "bash"}.get(ext, "")


def _write_entry(kind, source, reason, content_for_display, payload_name):
    """Append a new entry to the ledger and return its id. Caller is responsible
    for having written the byte-exact payload to FILES_DIR/payload_name."""
    text = _read_ledger()
    header, entries = _split_entries(text)
    eid = _next_id(entries)
    fence = _fence_for(content_for_display)
    lang = _lang_for(source) if kind == "snippet" else ""
    block = (
        '<!-- TRASH id={id} date={date} kind={kind} source="{source}" reason="{reason}" -->\n'
        '## {id} · {date} · {kind} · `{source}`\n'
        '**Reason:** {reason}  \n'
        '**Payload:** `data/trash/files/{payload}`\n\n'
        '{fence}{lang}\n{content}\n{fence}\n\n'
        '<!-- /TRASH {id} -->\n\n'
    ).format(id=eid, date=_today_str(), kind=kind, source=source,
             reason=reason.replace('"', "'"), payload=payload_name,
             fence=fence, lang=lang, content=content_for_display.rstrip("\n"))
    LEDGER.write_text(text.rstrip("\n") + "\n\n" + block, encoding="utf-8")
    return eid


def archive_snippet(source, content, reason):
    """Archive a removed block of text/code. `source` is the file it came from,
    `content` the exact text removed, `reason` why. Returns the entry id."""
    _ensure_vault()
    text = _read_ledger()
    _, entries = _split_entries(text)
    eid = _next_id(entries)
    payload_name = "{}__snippet.txt".format(eid)
    (FILES_DIR / payload_name).write_text(content, encoding="utf-8")
    # _write_entry recomputes the id; keep them in lockstep by writing payload
    # under the id it will assign. Since no archive happened between, ids match.
    written = _write_entry("snippet", source, reason, content, payload_name)
    if written != eid:  # extremely unlikely race; rename payload to match
        (FILES_DIR / payload_name).rename(FILES_DIR / "{}__snippet.txt".format(written))
    prune()
    return written


def archive_file(path, reason):
    """Move a whole file into the vault (byte-exact) and log it. Returns the id."""
    _ensure_vault()
    src = pathlib.Path(path)
    if not src.is_absolute():
        src = ROOT / src
    if not src.exists():
        raise FileNotFoundError(str(src))
    rel = str(src.relative_to(ROOT)) if str(src).startswith(str(ROOT)) else src.name
    text = _read_ledger()
    _, entries = _split_entries(text)
    eid = _next_id(entries)
    payload_name = "{}__{}".format(eid, src.name)
    shutil.move(str(src), str(FILES_DIR / payload_name))
    try:
        preview = (FILES_DIR / payload_name).read_text(encoding="utf-8")
        if len(preview) > 4000:
            preview = preview[:4000] + "\n… (truncated in ledger; full copy in payload)"
    except (UnicodeDecodeError, OSError):
        preview = "(binary file — see payload copy)"
    written = _write_entry("file", rel, reason, preview, payload_name)
    if written != eid:
        (FILES_DIR / payload_name).rename(FILES_DIR / "{}__{}".format(written, src.name))
    prune()
    return written


def prune(days=RETENTION_DAYS):
    """Drop entries (and their payload copies) older than `days`. Returns the
    number of entries removed."""
    if not LEDGER.exists():
        return 0
    text = _read_ledger()
    header, entries = _split_entries(text)
    cutoff = _now().date() - timedelta(days=days)
    kept, dropped = [], []
    for e in entries:
        try:
            d = datetime.strptime(e["date"], "%Y-%m-%d").date()
        except ValueError:
            kept.append(e)  # unparseable date: keep, never silently lose data
            continue
        (dropped if d < cutoff else kept).append(e)
    if not dropped:
        return 0
    for e in dropped:
        for p in FILES_DIR.glob(e["id"] + "__*"):
            p.unlink(missing_ok=True)
    rebuilt = header.rstrip("\n") + "\n\n" + "\n".join(e["block"] for e in kept)
    LEDGER.write_text(rebuilt.rstrip("\n") + "\n", encoding="utf-8")
    return len(dropped)


def restore(entry_id, dest=None):
    """Recover an archived entry. Snippets: write to `dest` if given else print
    to stdout. Files: copy back to original source path if `dest` is None, else
    to `dest`. Returns the path written (or None for stdout)."""
    _, entries = _split_entries(_read_ledger())
    match = next((e for e in entries if e["id"] == entry_id), None)
    if not match:
        raise KeyError("no trash entry with id {}".format(entry_id))
    payloads = sorted(FILES_DIR.glob(entry_id + "__*"))
    if not payloads:
        raise FileNotFoundError("payload for {} is gone".format(entry_id))
    payload = payloads[0]
    if match["kind"] == "snippet":
        content = payload.read_text(encoding="utf-8")
        if dest:
            pathlib.Path(dest).write_text(content, encoding="utf-8")
            return dest
        sys.stdout.write(content)
        return None
    # whole file
    target = pathlib.Path(dest) if dest else (ROOT / match["source"])
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(payload), str(target))
    return str(target)


def list_entries():
    _, entries = _split_entries(_read_ledger())
    return entries


def _cli():
    ap = argparse.ArgumentParser(description="OnBrandCraftz deletion recycle bin")
    ap.add_argument("--list", action="store_true", help="list archived entries")
    ap.add_argument("--prune", action="store_true", help="drop entries older than 30 days")
    ap.add_argument("--restore", metavar="ID", help="restore an entry by id")
    ap.add_argument("dest", nargs="?", help="optional restore destination path")
    ap.add_argument("--add-file", metavar="PATH", help="move a whole file into the bin")
    ap.add_argument("--reason", default="", help="reason (used with --add-file)")
    args = ap.parse_args()

    if args.add_file:
        eid = archive_file(args.add_file, args.reason or "archived via CLI")
        print("archived {} as {}".format(args.add_file, eid))
        return
    if args.restore:
        out = restore(args.restore, args.dest)
        if out:
            print("restored {} -> {}".format(args.restore, out))
        return
    if args.prune:
        n = prune()
        print("pruned {} expired entr{}".format(n, "y" if n == 1 else "ies"))
        return
    # default / --list
    entries = list_entries()
    if not entries:
        print("recycle bin is empty ({})".format(LEDGER))
        return
    print("{} entr{} in {}:".format(len(entries), "y" if len(entries) == 1 else "ies", LEDGER))
    for e in entries:
        print("  {}  {:7}  {:50}  {}".format(e["date"], e["kind"], e["source"][:50], e["reason"][:60]))


if __name__ == "__main__":
    _cli()
