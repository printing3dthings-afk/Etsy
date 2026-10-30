#!/usr/bin/env python3
"""Shrink this repo's history without losing anything (2026-10-30).

Scott: "You have go ahead to rewrite the repo. Just make sure nothing we need
is lost."

WHAT IT DOES. Every branch's history still carries the old copies of big files
that have since changed or gone: text STLs before they were made compact,
renders before Git LFS, videos, replaced 3MFs. A full clone downloads all of
them. This strips old copies of files bigger than --min-mb from history, and
only those. Every file that exists on any branch today is kept, byte for byte,
and so is every commit and its message (empty ones included).

WHY YOU RUN IT, NOT CLAUDE. A cloud session can only push its own branch (the
session's git proxy answers 403 to anything else), and this has to push all
of them at once.

HOW NOTHING IS LOST, in order:
  1. A full backup bundle of the repo as it is now, every branch, tag and pull
     request, written next to the work folder and verified. Keep it: it can
     rebuild the old history exactly (`git clone full-history-*.bundle`).
  2. With --push, the old tip of every branch is also kept on GitHub under
     refs/backup/pre-rewrite-<date>/. Normal clones never download those refs,
     so they cost clones nothing, but the old history stays on GitHub.
  3. After the rewrite, every branch's files are compared with before by tree
     hash: one changed byte anywhere and it stops. Commit counts too.
  4. The push is atomic and leased: if anything was pushed to any branch since
     the copy was taken, nothing is changed at all.

    pip install git-filter-repo
    python tools/rewrite_history.py --workdir ~/etsy-rewrite            # dry run: everything but the push
    python tools/rewrite_history.py --workdir ~/etsy-rewrite --push     # the real thing

Before --push: make sure no Claude or Codex session is working on the repo.
After it: every existing clone must be re-cloned (or `git fetch origin` then
`git reset --hard origin/<branch>`, which discards local changes). Railway
redeploys production from the rewritten default branch: same files, so the
same build.
"""
import argparse, datetime, os, subprocess, sys
from pathlib import Path

URL = "https://github.com/printing3dthings-afk/Etsy.git"


def git(repo, *args, inp=None, check=True):
    r = subprocess.run(["git", "-C", str(repo), *args], input=inp, capture_output=True, text=True,
                       env=dict(os.environ, GIT_LFS_SKIP_SMUDGE="1"))
    if check and r.returncode:
        sys.exit(f"git {' '.join(args[:3])} failed:\n{r.stderr.strip()}")
    return r.stdout


def refs(repo, pattern):
    out = git(repo, "for-each-ref", pattern, "--format=%(objectname) %(refname)")
    return {name: sha for sha, name in (line.split() for line in out.splitlines())}


def tree_of(repo, ref):
    return git(repo, "rev-parse", f"{ref}^{{tree}}").strip()


def count(repo, ref):
    return int(git(repo, "rev-list", "--count", ref).strip())


def pack_mb(repo):
    kib = [line.split(": ")[1] for line in git(repo, "count-objects", "-v").splitlines() if line.startswith("size-pack")]
    return int(kib[0]) / 1024


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workdir", required=True, type=Path)
    ap.add_argument("--min-mb", type=float, default=0.5, help="strip old copies of files at least this big (default 0.5)")
    ap.add_argument("--push", action="store_true", help="push the result (default: dry run)")
    ap.add_argument("--url", default=URL)
    # for testing the script where disk is short: rewrite a mirror clone taken
    # just before, and skip the bundle. Never allowed with --push.
    ap.add_argument("--test-mirror", type=Path, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.test_mirror and a.push:
        sys.exit("--test-mirror is for dry runs only")
    a.workdir = a.workdir.expanduser().resolve()
    if subprocess.run(["git", "filter-repo", "--version"], capture_output=True).returncode:
        sys.exit("git-filter-repo is not installed: pip install git-filter-repo")
    stamp = datetime.date.today().isoformat()
    a.workdir.mkdir(parents=True, exist_ok=True)
    repo = a.workdir / "etsy.git"

    print("1. A fresh full copy of the repo")
    if a.test_mirror:
        repo = a.test_mirror.expanduser().resolve()
    elif repo.exists():
        sys.exit(f"{repo} already exists: delete it (or pick another --workdir) so the copy is fresh")
    else:
        subprocess.run(["git", "clone", "--mirror", a.url, str(repo)], check=True,
                       env=dict(os.environ, GIT_LFS_SKIP_SMUDGE="1"))
    before_mb = pack_mb(repo)
    heads = refs(repo, "refs/heads")
    tags = refs(repo, "refs/tags")
    keep_refs = {**heads, **tags}
    trees = {r: tree_of(repo, r) for r in keep_refs}
    counts = {r: count(repo, r) for r in heads}
    print(f"   {len(heads)} branches, {len(tags)} tags, {before_mb:,.0f} MB packed")

    print("2. The backup bundle (everything, pull requests included)")
    bundle = a.workdir / f"full-history-{stamp}.bundle"
    if a.test_mirror:
        print("   skipped (test run)")
    else:
        git(repo, "bundle", "create", str(bundle), "--all")
        git(repo, "bundle", "verify", str(bundle))
        print(f"   {bundle} ({bundle.stat().st_size / 1e6:,.0f} MB), verified. Keep it somewhere safe.")

    print("3. Which old copies go")
    keep = set()
    for r in keep_refs:
        for line in git(repo, "ls-tree", "-r", r).splitlines():
            meta, _ = line.split("\t", 1)
            _, kind, sha = meta.split()
            if kind == "blob":
                keep.add(sha)
    listed = git(repo, "rev-list", "--objects", "--branches", "--tags")
    shas = "\n".join(line.split()[0] for line in listed.splitlines()) + "\n"
    sizes = git(repo, "cat-file", "--batch-check=%(objecttype) %(objectname) %(objectsize)", inp=shas)
    floor = a.min_mb * 1e6
    strip, strip_bytes = [], 0
    for line in sizes.splitlines():
        kind, sha, size = line.split()
        if kind == "blob" and int(size) >= floor and sha not in keep:
            strip.append(sha)
            strip_bytes += int(size)
    ids = a.workdir / "strip-blob-ids.txt"
    ids.write_text("\n".join(strip) + "\n")
    print(f"   {len(strip)} old copies, {strip_bytes / 1e6:,.0f} MB before compression; "
          f"{len(keep)} files on the branches today are kept")

    if a.push:
        print("4a. Keeping the old tips on GitHub under refs/backup/")
        spec = [f"{sha}:refs/backup/pre-rewrite-{stamp}/{r[len('refs/'):]}" for r, sha in keep_refs.items()]
        subprocess.run(["git", "-C", str(repo), "push", "--atomic", a.url, *spec], check=True)

    print("4. Rewriting (pull request refs are dropped from this local copy only)")
    for r in refs(repo, "refs/pull"):
        git(repo, "update-ref", "-d", r)
    subprocess.run(["git", "-C", str(repo), "filter-repo", "--force", "--strip-blobs-with-ids", str(ids),
                    "--prune-empty", "never", "--prune-degenerate", "never"], check=True)

    print("5. Checking nothing on any branch changed")
    bad = []
    for r, t in trees.items():
        if tree_of(repo, r) != t:
            bad.append(f"{r}: its files changed")
    for r, n in counts.items():
        if count(repo, r) != n:
            bad.append(f"{r}: {count(repo, r)} commits, was {n}")
    if bad:
        sys.exit("STOPPED, nothing pushed:\n  " + "\n  ".join(bad))
    after_mb = pack_mb(repo)
    print(f"   every branch's files identical, every commit kept. {before_mb:,.0f} MB -> {after_mb:,.0f} MB packed")

    if not a.push:
        print("Dry run: nothing was pushed. Run again with --push (in a fresh --workdir) to do it.")
        return
    print("6. Pushing every branch and tag at once, leased on the tips the copy started from")
    new = refs(repo, "refs/heads")
    new.update(refs(repo, "refs/tags"))
    lease = [f"--force-with-lease={r}:{sha}" for r, sha in keep_refs.items()]
    spec = [f"+{new[r]}:{r}" for r in keep_refs]
    subprocess.run(["git", "-C", str(repo), "push", "--atomic", *lease, a.url, *spec], check=True)
    print("Done. Re-clone every other copy of the repo; the backup bundle and refs/backup/ hold the old history.")


if __name__ == "__main__":
    main()
