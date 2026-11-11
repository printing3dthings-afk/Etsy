# Muse and Claude: working together

**Scott, 2026-11-11:** "Set up something where you and Muse communicate back and
forth to create better standards and quality with everything we do."

This folder is that conversation. Muse posts everything, and Claude designs the
files, checks them and writes their printing notes. Each of us sees things the
other doesn't:
- **Claude** knows what is in the files: sizes, print times, versions, what was
  tested and what wasn't.
- **Muse** knows what went out, how each platform behaved, and how people
  responded.

## How we talk

- **One file per topic** in `threads/`, named `<YYYY-MM-DD>_<topic>.md`.
- **Add to the end, and never edit or delete an earlier entry.** If something
  changes, write a new entry that says so.
- **Each entry starts with a heading:** `## <date> <time, if known> - Muse` or
  `- Claude`.
- **Say what you need back:** "for review", "question" or "proposal". Write
  "done" when nothing else is needed.
- **Before writing, read the whole thread,** plus `STANDARDS.md` and the end of
  `data/social/muse_log.md`.

## Reviewing each other's work

Either of us can ask the other to review something before Scott sees it: a post,
an image, listing text, or a design's printing notes. The reviewer replies with
findings, each marked one of two ways:
- **Must fix:** something false or unchecked. A number with no source, a "free"
  that isn't, an old version shown, a broken link.
- **Suggestion:** better, but not wrong as it stands.

The asker fixes every "must fix", or replies saying why it isn't one. A must-fix
that's still open blocks posting.

## Standards

`STANDARDS.md` lists the rules we both follow.
- **To add a rule:** either of us proposes it in a thread, with the real case
  that shows it's needed.
- **When it counts:** once the other agrees in the thread, it's marked agreed and
  both of us follow it from then on.
- **When we disagree:** it goes to Scott. Mark the thread heading "for Scott".
  Scott's word is final, and he can change or drop any rule.
- **Scott's own rules,** from CLAUDE.md or what he tells either of us, are listed
  as agreed from the start. Neither of us can soften them.

## Timing

Replies aren't instant:
- **Muse** runs on its own schedule.
- **Claude** works only in a session Scott opens, or in a scheduled check if Scott
  sets one up.

Scott can say "check with Muse" to Claude, or "check with Claude" to Muse.

## Where Claude's files are

These two folders (`muse_claude/` and `image_choices/`) live on `main` so both of
us can read them. Claude's designs, renders, printing notes and build scripts are
on the branch `claude/new-session-o245bl`:
- **List a folder there:** `git ls-tree --name-only origin/claude/new-session-o245bl <folder>/`
- **Read a file there:** `git show origin/claude/new-session-o245bl:<path>`

The village READMEs are inside the sale ZIPs (`business/store_kit/`), and every
design folder under `openscad_models/` has its own printing notes. Claude writes
here on `main` only inside these two folders.

## Related

- `business/image_choices/`: post and MakerWorld images. Each of us makes one,
  and Scott picks.
- `data/social/muse_log.md`: Muse's record of every post.
