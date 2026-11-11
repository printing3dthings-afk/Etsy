# Claude's banner

`claude.png`, 3000 × 408. `claude_phone_crop.png` is the middle 1800 px, which is
what a phone is expected to keep.

- **Left:** "OnBrandCraftz" in Montserrat ExtraBold (navy "OnBrand", gold
  "Craftz"), a short gold bar, and one line: "Original 3D print designs:
  Christmas villages and more". All of it sits inside the middle 1800 px.
- **Right:** a street of seven buildings that alternates Gingerbread and
  Victorian, tallest in the middle, standing on a snow line. It starts inside the
  middle 1800 px and runs on to the right, so a phone shows the first four.
- **Small print:** "3D renders of the design files", under the street.
- **No logo, no "free",** no price, no other claim.

## Sources

- **Buildings:** `cutouts/*.png`, rendered by `cutouts.py` from the STL parts
  inside the two sale ZIPs (`business/store_kit/out/`), in the colours each
  building's README gives. They're the same files and colours as the store
  pictures, rendered on a transparent background so they can stand on the banner.
  - Gingerbread: Cottage, Candy Cane Chapel, Cocoa Café, Sweet Shop.
  - Victorian: Coaching Inn, Church, Toy Shop.
- **Fonts:** `assets/fonts/` (Montserrat ExtraBold, Poppins SemiBold and Regular).
- **Size:** 3000 × 408, from the brief. MakerWorld doesn't publish it; the
  brief cites the Bambu forum.

Rebuild: `python3 cutouts.py` (about 25 minutes), then `python3 claude_make.py`.
