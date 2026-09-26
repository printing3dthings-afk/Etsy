# OnBrandCraftz logo — vector, for 3D print inlays

`onbrandcraftz-script.svg` (the charcoal brush wordmark) and
`onbrandcraftz-swash.svg` (the gold underline) are potrace vectorizations of
the shop's real logo. They share one coordinate frame, so importing both and
applying the *same* scale + offset keeps them registered to each other.

**Why these exist:** the canonical brand file,
`tools/api_server/static/brand/onbrandcraftz-wordmark.svg`, is an SVG wrapper
around a base64 PNG — there is no vector geometry in it, so OpenSCAD's
`import()` cannot use it. The wordmarks under `static/vendor/wordmark/` ARE
real outlines but they are HUD font pairings, not the brand logo.

Source: `static/brand/onbrandcraftz-wordmark.svg`'s embedded PNG (1232x281,
transparent), split by hue into a dark mask and a gold mask, upsampled 4x
(LANCZOS) and traced with `potrace -b svg -a 1.0 -O 0.2 -t 12`.

Measured extents after a real OpenSCAD import+export (never read off the
viewBox — potrace's viewBox carries padding the ink never reaches):

| file | X | Y |
|---|---|---|
| script | 29.210 .. 1709.180 (w 1679.970) | 29.483 .. 365.478 (h 335.995) |
| swash  | 480.492 .. 1366.830 (w 886.338) | 41.418 .. 70.555 (h 29.137) |

**Minimum print size — CORRECTED 2026-09-09, and the answer is "it cannot".**
This section used to claim ~70mm, from an eyeballed "about 8 px" connector
width and a 1-extrusion target. Both were wrong. Measured properly (distance
transform over the dark mask, `scipy.ndimage`), the hairlines are **2 px on an
1188 px-wide mark — 0.168% of the width**, and the shop's standing rule is
**2 extrusions (0.84mm)**, not one.

| stroke | % of width | width needed for 0.84mm |
|---|---|---|
| hairline (1st pct) | 0.168% | **499 mm** |
| 5th pct | 0.238% | 353 mm |
| median | 0.607% | 138 mm |

The P1S plate is 256mm. **This logo cannot print as an inlay at any size that
fits the machine.** Keep these files for listings and the dashboard; for
anything printed use `assets/brand/OBC.svg` (min 9.4mm) or
`assets/brand/OnBrandCraftz.svg` in Caveat Bold (min 50.5mm), both true font
vectors rather than traces.
