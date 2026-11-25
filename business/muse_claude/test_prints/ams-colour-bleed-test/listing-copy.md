# TEST - AMS Colour-Bleed Test

**Title (MakerWorld, <= 50 chars):** TEST - AMS Colour-Bleed Test

**What it tests:** the only multicolour piece in this test series -
how much flushing a dark-to-light colour change really needs before
the dark stops bleeding into the light. The strip (120 x 26 x 5 mm)
is one object in two parts: a dark part (block + a 12 mm island) and
a light part that wraps the island, so EVERY layer forces two
dark-to-light transitions - the hardest case, fifty times per print.
Shallow tick grooves cross the light part's top every 5 mm for the
first 30 mm, so the fade can be read off in millimetres.

**The four profiles (the profiles ARE the test):** identical strip,
identical settings - only the flush volume for the dark-to-light
transition differs (the flush matrix entry, verified in each file's
config; light-to-dark is fixed at 160 mm3, flush multiplier 1.0, so
the matrix number is the purge you actually get):

- Flush 120: dark->light flush 120 mm3 - verified slice 50 min 43 sec - 15.98 g total (dark 7.83 g / light 8.15 g).
- Flush 240: dark->light flush 240 mm3 - verified slice 52 min 58 sec - 17.88 g total (dark 7.83 g / light 10.05 g).
- Flush 360: dark->light flush 360 mm3 - verified slice 55 min 15 sec - 19.78 g total (dark 7.83 g / light 11.95 g).
- Flush 480: dark->light flush 480 mm3 - verified slice 57 min 26 sec - 21.68 g total (dark 7.83 g / light 13.85 g).

The light filament's verified usage climbs with each step while the
dark stays constant - the extra purge is real, and it is the price of
each step. Load YOUR dark filament in AMS slot 1 and your light in
slot 2 (the files carry the stock matte white identity on both slots
with black / white assigned as the working colours - remap to your
actual spools in Bambu Studio / Handy before printing; the test is
about YOUR darkest and lightest pair).

**How to judge:** print the steps in order and hold each strip under
the same light. Read the light section after the dark block AND
around the island: at which flush step does the light first read
clean - no grey/pink cast at the boundary, and how many tick grooves
(5 mm each) does the fade take to disappear entirely?

**Record your results:**

| Flush (dark->light) | Boundary clean? | Fade length (ticks x 5 mm) | Verdict |
|---|---|---|---|
| 120 mm3 |  |  |  |
| 240 mm3 |  |  |  |
| 360 mm3 |  |  |  |
| 480 mm3 |  |  |  |

**Filament:** two AMS slots - dark in slot 1, light in slot 2 (stock
matte identities in the file; remap to your spools). **Ironing: OFF.**
Supports off. Prime tower on (multicolour default).

**Per-profile copy (paste into each profile's description box):**

Prints the AMS Colour-Bleed Test strip at a 120 mm3 dark-to-light flush: one 120 x 26 x 5 mm strip in two parts - dark (AMS slot 1) block + island, light (AMS slot 2) wrapping it, two dark-to-light transitions per layer, tick grooves every 5 mm across the first 30 mm of light. Stock matte identity on both slots; load your dark filament in slot 1 and your light in slot 2. Flush matrix verified in the file's config (dark->light 120 mm3, light->dark 160 mm3, multiplier 1.0). Verified slice: 50 min 43 sec - 15.98 g total (dark 7.83 g / light 8.15 g).

Prints the AMS Colour-Bleed Test strip at a 240 mm3 dark-to-light flush: one 120 x 26 x 5 mm strip in two parts - dark (AMS slot 1) block + island, light (AMS slot 2) wrapping it, two dark-to-light transitions per layer, tick grooves every 5 mm across the first 30 mm of light. Stock matte identity on both slots; load your dark filament in slot 1 and your light in slot 2. Flush matrix verified in the file's config (dark->light 240 mm3, light->dark 160 mm3, multiplier 1.0). Verified slice: 52 min 58 sec - 17.88 g total (dark 7.83 g / light 10.05 g).

Prints the AMS Colour-Bleed Test strip at a 360 mm3 dark-to-light flush: one 120 x 26 x 5 mm strip in two parts - dark (AMS slot 1) block + island, light (AMS slot 2) wrapping it, two dark-to-light transitions per layer, tick grooves every 5 mm across the first 30 mm of light. Stock matte identity on both slots; load your dark filament in slot 1 and your light in slot 2. Flush matrix verified in the file's config (dark->light 360 mm3, light->dark 160 mm3, multiplier 1.0). Verified slice: 55 min 15 sec - 19.78 g total (dark 7.83 g / light 11.95 g).

Prints the AMS Colour-Bleed Test strip at a 480 mm3 dark-to-light flush: one 120 x 26 x 5 mm strip in two parts - dark (AMS slot 1) block + island, light (AMS slot 2) wrapping it, two dark-to-light transitions per layer, tick grooves every 5 mm across the first 30 mm of light. Stock matte identity on both slots; load your dark filament in slot 1 and your light in slot 2. Flush matrix verified in the file's config (dark->light 480 mm3, light->dark 160 mm3, multiplier 1.0). Verified slice: 57 min 26 sec - 21.68 g total (dark 7.83 g / light 13.85 g).
