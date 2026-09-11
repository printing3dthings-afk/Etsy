---
name: defuddle
description: Extract clean markdown content from web pages using Defuddle CLI, removing clutter and navigation to save tokens. Use instead of WebFetch when the user provides a URL to read or analyze, for online documentation, articles, blog posts, or any standard web page. Do NOT use for URLs ending in .md — those are already markdown, use WebFetch directly.
---

# Defuddle

Use Defuddle CLI to extract clean readable content from web pages. Prefer over WebFetch for standard web pages — it removes navigation, ads, and clutter, reducing token usage.

If not installed: `npm install -g defuddle` (this container is ephemeral, so
expect to run it once per session — it takes seconds).

## The reason that actually matters here (tested 2026-09-11)

**`WebFetch` returns 403 on sites this project genuinely needs.** Confirmed on
`docs.blender.org` and `claude.com` in one session — both refused `WebFetch`
and both parsed fine with `defuddle`. `curl` also gets through, but then you
own the HTML-stripping, and a hand-rolled stripper drags the whole nav sidebar
in with the content.

Measured on the same two pages, comparing `defuddle --md` against a hand-rolled
curl + regex stripper:

| page | hand-rolled | defuddle |
|---|---|---|
| Blender manual (structured docs) | ~1,739 tok | ~2,200 tok, but real markdown headings/code blocks |
| claude.com plugin page (marketing/SPA) | ~572 tok, **16 nav fragments** | **~252 tok, 0 nav fragments** |

So: on a well-structured docs page the two are comparable and `defuddle` wins
on structure; on a marketing or SPA page `defuddle` is less than half the
tokens with none of the clutter. Both substance checks passed — every technical
term relied on from the Blender page survived the extraction.

**Order to try, for any web page:**
1. `defuddle parse <url> --md` — default.
2. `curl -sSL -A "Mozilla/5.0" <url>` — when defuddle itself fails; you strip
   the HTML yourself.
3. `WebFetch` — fine when it works, but do not spend time debugging its 403s.
   That is a signal to drop to defuddle, not to retry.

Do NOT reach for a paid scraping service for this. Firecrawl was evaluated
2026-09-11 and declined — see CLAUDE.md's "Tool suggestions evaluated and
declined". This covers the same ground for free.

## Usage

Always use `--md` for markdown output:

```bash
defuddle parse <url> --md
```

Save to file:

```bash
defuddle parse <url> --md -o content.md
```

Extract specific metadata:

```bash
defuddle parse <url> -p title
defuddle parse <url> -p description
defuddle parse <url> -p domain
```

## Output formats

| Flag | Format |
|------|--------|
| `--md` | Markdown (default choice) |
| `--json` | JSON with both HTML and markdown |
| (none) | HTML |
| `-p <name>` | Specific metadata property |
