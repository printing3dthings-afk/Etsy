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

**Minimum print size.** Measured off the source bitmap, the script's thin
connector strokes run about 8 px wide against a 1232 px-wide logo. To keep
those strokes at or above one 0.4mm extrusion they need roughly 0.45mm, so
the wordmark must be at least ~70mm wide to print as a separate filament.
Below that the slicer drops the thin strokes and the script breaks up.
