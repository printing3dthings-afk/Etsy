# Coloring Page Design & Market Research — August 2026
*Web-search-grounded research (real citations below each section). This is the first
dedicated research doc for this product line — wall art, SVG bundles, and digital planners
already had deep coverage in `design_quality_research_2026-06.md`; coloring pages had none.
Confidence flagged where a single source drove a claim.*

---

## VERDICT SUMMARY

| Area | Current state | Gap |
|---|---|---|
| Generation pipeline (`tools/generate_coloring_pages.py`) | Already mature: tiered style prompts, hard black/white threshold post-process, vision-QA retry loop | Missing one specific, well-documented technique: explicit "closed/fully-enclosed outline" instruction |
| Pricing | 20-page packs at $3.99 flat | Under-priced against real market data by roughly 2–3x |
| Theme/niche targeting | 2 fixed packs (kawaii, fun/basic) + a dynamic Scott-typed-theme generator | Fixed packs don't target any of the specific niches trending in 2026 research below — the dynamic generator already CAN, just hasn't been pointed at them |
| Competitor research | None existed before this doc | This doc |

---

## 1. Pricing — Real Market Data

- Single printable coloring pages: **$2.99–$3.99** each.
- **Themed bundles: $4–$8 for 10–15 pages.**
- **Comprehensive themed coloring books: $8–$15 for 25+ pages.**
- Worked example from the research: a 50-page mandala book at $6 outperforms selling the same pages individually at $0.50–$1 each — bundling beats unbundling on this product type.
- Monthly Etsy search volume for coloring-related terms: 500,000+. Specific themed sub-niches ("farm animal coloring pages," "ocean coloring book printable") individually pull 5,000–15,000 monthly searches.

**Gap against our own catalog:** our packs are 20 pages at a flat $3.99. Per the bundle-tier data above, a 20-page pack sits between the $4–8/10–15-page tier and the $8–15/25+-page tier — priced at the bottom of a tier it has already outgrown in page count. **This is a pricing recommendation for Scott's review, not something changed here** — matches the existing autonomy boundary (price changes on ranked listings require his approval). Rough reference point: a 20-page pack priced in the $6–9 range would still undercut the $8–15/25+ tier while sitting well above the current $3.99.

Sources: [Sell Coloring Books on Etsy: 2026 Guide — Insight Agent](https://www.insightagent.app/guides/sell-coloring-books-on-etsy), [How to Make Coloring Pages to Sell on Etsy Using AI (2026) — Digital Biz PLR](https://digitalbizplr.com/blogs/learn/how-to-make-coloring-pages-sell-etsy-ai)

---

## 2. Trending Niches (2026) — What to Target Next

- **Educational integration is the standout 2026 differentiator**: coloring pages that add vocabulary labels, counting elements, or letter-practice alongside the artwork command premium prices and attract education-focused (parent/teacher) buyers — a reliable repeat-buyer segment, not one-off impulse buyers.
- **Cottagecore aesthetic** — trending as of March 2026.
- **Stained-glass style line art** — trending, visually distinct from standard flat line art (thicker segmented sections, mosaic-style panel breaks).
- **Affirmation / mental-health / mindfulness themes** — trending, and a natural fit for our kawaii-adjacent brand aesthetic already established across the planner/sticker lines.
- Popular established themes (steady demand, not necessarily under-served): mandala, botanical, seasonal, inspirational-quote coloring.

**Actionable fit with our own pipeline:** `generate_dynamic_theme_set()` (the Scott-typed-theme path, `tools/generate_coloring_pages.py`) already supports arbitrary themes — it does not need new code to target cottagecore, stained-glass, affirmations, or educational-hybrid pages. The two FIXED packs (`kawaii`, `fun_basic`) don't currently point at any of these; a new fixed pack or a dynamic set built around one of these niches is a content decision, not an engineering one.

Sources: [Best Niches for Etsy Digital Products in 2026 — Promptless Press](https://www.promptlesspress.com/blog-best-niches-etsy-digital-products-2026), [Top-selling niches on Etsy in 2026 — Printify](https://printify.com/blog/top-selling-niches-on-etsy/), [Best Printable Niches for Etsy in 2026 — LessonCraftStudio](https://www.lessoncraftstudio.com/en/ideas/best-printable-niches-etsy-2026)

---

## 3. Line-Art Design Principles (published coloring-book design standards)

- **Closed shapes are the #1 technical requirement.** Outlines must fully enclose each region — "all objects must be complete and paths must be closed to prevent colors from leaking out during coloring." This applies to both physical coloring (crayon/marker bleeding past a broken line) and digital coloring apps (a bucket-fill tool leaks through any gap in the outline).
- **Line weight**: bold and even; thick, closed outlines that won't visually disappear under crayon. A more advanced technique — **variable line weight for depth** — uses thicker lines for foreground/outer objects and thinner lines for background or inner surface detail. Line weight is also the main tool for taming an otherwise-too-busy intricate pattern.
- **Color/contrast**: crisp 1-bit-style pure black outlines on pure white, zero shading or gray fills — this exactly matches what `_enforce_bw()`'s hard 185-threshold post-process already guarantees mechanically; the finding here confirms that step is correctly designed, not a gap.
- **Composition**: enough open space to actually color — cramped, over-detailed pages read as harder to use, not more premium.
- **Format**: US Letter (8.5×11") is the most common size in the market — already what we ship.

Sources: [7 Terrific Tips to Creating Perfect Coloring Book Art Vectors — Vectips](http://vectips.com/tips-and-tricks/tips-for-coloring-book-art-vectors/), [Coloring Book Design: How to Make One — Made Good Designs](https://madegooddesigns.com/coloring-book-design/), [How to Design a Coloring Book — Printing Center USA](https://www.printingcenterusa.com/blog/color-book-design/), [How to Create A Coloring Page — Kaitlin Trisciani](https://www.katetrish.com/blog/how-to-create-a-coloring-page)

---

## 4. AI-Generation Prompt Technique — What Transfers to Our Pipeline

Most published AI-coloring-page prompting guides are written for Midjourney and lean on its
`--no <thing>` negative-prompt syntax ("--no colors," "--no shadows/shades," "--no complex
patterns, shading, color, sketch"). **This does not transfer to our engine.** gpt-image-1 has
no negative-prompt field — CLAUDE.md's own "Negative Prompting — gpt-image-1 Has No Negative
Field" section already establishes that every constraint must be phrased as a positive
instruction instead, and `_STYLE`/`_STYLE_BOLD`/`_STYLE_ADULT`/`_STYLE_KIDS` in
`generate_coloring_pages.py` already do this correctly (e.g. "ZERO fills, ZERO shading" rather
than a `--no` flag). **No change needed there — the research confirms the existing approach is
right for the engine actually in use, not a gap.**

What IS a real, transferable, currently-missing instruction: **none of the four `_STYLE*`
constants explicitly tell the model to keep every outline closed/fully enclosed.** They specify
line weight, purity of black/white, and absence of fill — but never the one property that
published coloring-book design guides call the single most important technical requirement
(section 3 above). Recommended addition to each `_STYLE*` constant: a clause such as *"Every
outline must form a closed, fully enclosed loop — no open or broken line segments, so colored
areas cannot leak between regions."* This is a text-only prompt change, no pipeline logic
change, and composes cleanly with the existing vision-QA verify/retry loop (`run_until_goal` +
`verify_original_art`) already checking each generated page.

Sources: [40+ Best Coloring Book Pages Prompts for Midjourney — Weam.ai](https://weam.ai/blog/prompts/coloring-book-ai-prompts-midjourney/), [How to Write Midjourney Prompts for Coloring Books — AiArty](https://www.aiarty.com/midjourney-prompts/midjourney-coloring-book-prompt.htm), [Midjourney Coloring Book: Tips, Tricks, and Example Prompts](https://www.instantaiprompt.com/prompts/midjourney/coloring-book/)

---

## 5. Tooling — Confirmed No Better Option Exists

Checked whether a dedicated line-art/coloring-page generation tool beats the current
gpt-image-1 → hard-threshold → vision-QA pipeline. Logged in `tool_evaluations.md` rather than
repeated here — short version: nothing found beats "generate with the already-approved image
engine, then deterministically force pure black/white, then vision-QA verify" for our specific
requirement (a *specific themed subject*, not a *photo-to-lineart trace*). Dedicated "photo to
line art" converters (e.g. lineart.ai) solve a different problem — turning an existing photo
into an outline — not generating original themed artwork, which is what every one of our
packs needs.

---

## PRIORITIZED ACTION ITEMS

1. **Add the closed-outline instruction to all 4 `_STYLE*` constants** — text-only prompt fix,
   directly sourced from section 3/4 above, composes with the existing QA loop. (Shipped
   alongside this doc — see ops_runbook.md entry.)
2. **Pricing review** — present to Scott: current $3.99/20-page flat price sits below the
   $8–15/25+-page market tier our page count already qualifies for. His call, not auto-changed.
3. **New niche targeting** — no code needed; the dynamic per-theme generator already supports
   any subject. Candidates from real 2026 trend data: cottagecore, stained-glass style,
   affirmation/mindfulness, and educational-hybrid (vocabulary/counting elements baked into the
   art) — the last one is flagged by research as the single biggest 2026 differentiator for this
   category.

*Sources listed inline per section above (all from live web search, August 2026).*
