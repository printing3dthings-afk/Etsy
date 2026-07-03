# Creative-Production Tooling Assessment (2026-07-03)

Honest review of GitHub/open-source options to improve OnBrandCraftz's creative pipeline —
digital art, 3D physical products, sticker/vector production, and design QC — scored against
what we ALREADY do. Prompted by Scott asking whether we're "running the best possible options."

**Bottom line:** we're in good shape. The two genuine upgrades are GPU-heavy, and Scott's GPU
is weak, so their LOCAL versions are off — but the same capabilities exist as zero-GPU cloud
APIs (which is our standing "buy, don't self-host" doctrine anyway). Nothing here is a must-build;
nothing here beats clearing the live blocker (Frank out of Anthropic credits).

---

## Scorecard

| Area | Our current approach | Best 2026 option | Verdict |
|---|---|---|---|
| **Wall-art upscaling** | `tools/upscale_art.py` — Lanczos + UnsharpMask (classical resize, no AI) | Upscayl / Real-ESRGAN (AI, local) | **Real upgrade, but optional.** AI upscaling is sharper on AI-art enlargements. Local needs a Vulkan GPU (Scott's is weak → off). Cloud path: Replicate/fal Real-ESRGAN, no GPU. Only worth wiring if wall art becomes real volume — Lanczos already clears the ≥3,000px gate. |
| **New 3D products (image→mesh)** | Entirely hand-designed in Bambu Studio; no generation tooling | TRELLIS.2 (Microsoft, ~68% benchmark wins), Hunyuan3D 2.1, TripoSR/Stable Fast 3D | **Exploratory strategic bet, not a quick build.** Local needs a strong GPU (off). Cloud path: Tripo/Meshy APIs, no GPU. Caveats: generated meshes usually aren't watertight (need a repair pass); a single mesh ≠ our multi-color AMS layer model; and the "never lie" rule means we must print + photograph the REAL print, never show the AI mesh render. |
| **Sticker cutout / bg removal** | Color-flood `remove_white_background()` + scipy connected-components `segment_stickers()` (dependency-free). Fixed DP1027 Sheet 6 (1→21) on 2026-07-03. | SAM 2, BRIA RMBG-2.0 (GPU models) | **SKIP.** We solved this correctly last session. Our sheets have flat, known backgrounds where color-flood works and needs no GPU/dependency. Don't add a GPU model to re-solve a solved problem. |
| **Raster→SVG vectorization** | SS-series REQUIRES clean vectors; `validate_digital_file()` rejects traced rasters (≤20 fills, ≤200 paths, ≤150 KB per SVG) | vtracer, potrace, Inkscape trace | **SKIP — actively wrong for us.** vtracer/potrace OUTPUT traced-raster SVGs with hundreds of paths — exactly what our own gate rejects, because those files can't be color-separated for AMS multi-color printing (GitHub issue #8044). Confirms our standard is right. Clean vectors come from genuine vector design, not tracing. |
| **Design QC / visual oversight** | `listing_photo_pipeline.verify_render` (VLM compares render vs source), `_check_no_pale_background`, `goal_loop.py` (retry-until-pass), `EtsyAPIClient.pre_publish_gate`, `validate_digital_file` | — | **Already strong — ahead of most Etsy shops.** Only marginal idea: route the verifier to a cheaper/better vision model. Low priority. |

---

## The recurring fork
Every genuine upgrade in this space is GPU-heavy → the local version needs a capable GPU.
Scott's GPU is weak (confirmed 2026-07-03), so local/relay pipelines are out. This is the same
fork hit on GitHub tool batches 1–2. It doesn't leave us stuck: the same features are available
as **cloud APIs with zero GPU**, which matches our documented AI/API strategy (self-hosting is a
false economy at our volume — buy per-call, don't host).

## What would trigger a build later (all Scott-gated)
- **Cloud AI upscaler** — add a Replicate Real-ESRGAN engine to `tools/upscale_art.py` behind an
  engine flag (default OFF, OpenAI-style), IF wall art scales into a real volume line.
- **Image→3D** — a separate strategic decision to open a generated-3D product line via Tripo/Meshy
  API, with a mesh-repair + real-print-and-photograph step. Not a quick win.

## Skips (recorded so we don't re-litigate)
- Sticker SAM2/RMBG — color-flood already solves our flat-background sheets, dependency-free.
- vtracer/potrace — produce exactly the traced-raster SVGs our own SS-series gate rejects.
