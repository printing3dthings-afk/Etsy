# Selling while Etsy is down: Payhip setup

2026-11-11. The Etsy shop is down for about a week (a payment issue). This
gets the two Christmas village file bundles on sale somewhere else, with the
money going straight to Scott's PayPal.

**Why Payhip:**
- Free to start, with a 5% fee on the free plan, plus PayPal's own fee. Check
  the current numbers on Payhip's pricing page when you sign up.
- Each sale is paid into your PayPal or Stripe as it happens; Payhip doesn't
  hold the money.
- It delivers the file automatically.
- A file can be up to 5 GB, so each village is one download, not the 3–4
  parts Etsy needed.

## Scott's part (about 15 minutes, on a phone or computer)

1. Sign up at payhip.com with your shop email, and name the store OnBrandCraftz.
2. Settings → Payments: connect your PayPal. This is the step that gets you paid.
3. Add the two products below. For each one, choose "Digital product", then
   upload the ZIP and the images I sent, and paste the name, price and description.
4. Send me the store link. I'll put it on your links page in place of Etsy, and
   write a short note for Muse to point posts at it.

## Product 1: Victorian Christmas Village

- **File:** `OnBrandCraftz_Victorian_Christmas_Village_8_buildings.zip` (36.7 MB)
- **Images:** `victorian_village_grid.png` first, then the single-building pictures
  `victorian_*.png`
- **Price:** $24.99 (the Etsy bundle price)
- **Name:** Victorian Christmas Village: 8 Tealight Houses, 3D Print Files (STL + 3MF)

**Description:**

```
The whole OnBrandCraftz Victorian Christmas village: all 8 buildings as 3D print files, one design language and one scale, so they stand together as one street.

DIGITAL DOWNLOAD: 3D print files only. No physical item is shipped and no tealight is included. You need a 3D printer.

THE 8 BUILDINGS
• Victorian Cottage: 67 × 67 × 95 mm, about 1 h 33 m in one colour
• Victorian Shop-House: 83 × 69 × 122 mm, about 2 h 19 m in one colour
• Victorian Toy Shop: 81 × 75 × 126 mm, about 2 h 59 m in one colour
• Victorian Church: 79 × 93 × 164 mm, about 3 h 17 m in one colour
• Victorian Coaching Inn: 97 × 69 × 111 mm, about 3 h 07 m in one colour
• Victorian Townhouse: 65 × 76 × 122 mm, about 2 h 53 m in one colour
• Victorian Santa's Workshop: 206 × 129 × 194 mm, about 15 h 34 m in one colour
• Victorian Clock Tower: 67 × 67 × 160 mm, about 2 h 12 m in one colour

WHAT YOU GET
• One ZIP, one folder per building
• Each building as a four-colour 3MF (opens in Bambu Studio and PrusaSlicer) and as STL parts for any slicer
• A README per building with its size, print settings, colours and lighting

PRINTING
• Supports OFF, printed standing up, 0.2 mm layers
• Print in one colour and paint it, or in four colours with an AMS
• Designed and sliced for a Bambu Lab P1S with a 0.4 mm nozzle; times are sliced estimates

LIGHTING
Every building is a hollow lantern with an open base, lit by battery LED tealights up to about 38 mm across and 45 mm tall (not included). Santa's Workshop takes three; the others take one. Battery LED lights only, never a flame.

The pictures are 3D renders of these files, not photos.

ABOUT THIS DESIGN
These models were designed with the help of AI tools, from original concepts by the seller, and every file is checked for printability before it is sold.

LICENCE
© OnBrandCraftz. Personal use and gifts only. Do not sell prints, or share or resell the files.
Questions: Printing3dthings@outlook.com
```

## Product 2: Gingerbread Christmas Village

- **File:** `OnBrandCraftz_Gingerbread_Christmas_Village_7_buildings.zip` (48.5 MB)
- **Images:** `gingerbread_village_grid.png` first, then `gingerbread_*.png`
- **Price:** $24.99
- **Name:** Gingerbread Christmas Village: 7 Tealight Houses, 3D Print Files (STL + 3MF)

**Description:**

```
The whole OnBrandCraftz Gingerbread Christmas village: all 7 buildings as 3D print files, one design language and one scale, so they stand together as one street.

DIGITAL DOWNLOAD: 3D print files only. No physical item is shipped and no tealight is included. You need a 3D printer.

THE 7 BUILDINGS
• Gingerbread Cottage: 69 × 69 × 86 mm, about 1 h 53 m in one colour
• Gingerbread Turret House: 81 × 73 × 113 mm, about 2 h 17 m in one colour
• Gingerbread Candy Cane Chapel: 68 × 84 × 132 mm, about 2 h 34 m in one colour
• Gingerbread Sweet Shop: 67 × 77 × 114 mm, about 2 h 06 m in one colour
• Gingerbread Cocoa Café: 69 × 77 × 97 mm, about 1 h 40 m in one colour
• Gingerbread Santa's Workshop: 206 × 129 × 192 mm, about 11 h 56 m in one colour
• Gingerbread Cookie Clock Tower: 67 × 67 × 141 mm, about 1 h 48 m in one colour

WHAT YOU GET
• One ZIP, one folder per building
• Each building as a four-colour 3MF (opens in Bambu Studio and PrusaSlicer) and as STL parts for any slicer
• A README per building with its size, print settings, colours and lighting

PRINTING
• Supports OFF, printed standing up, 0.2 mm layers
• Print in one colour and paint it, or in four colours with an AMS
• Designed and sliced for a Bambu Lab P1S with a 0.4 mm nozzle; times are sliced estimates

LIGHTING
Every building is a hollow lantern with an open base for a battery LED tealight up to about 38 mm across and 45 mm tall (not included). Battery LED lights only, never a flame.

The pictures are 3D renders of these files, not photos.

ABOUT THIS DESIGN
These models were designed with the help of AI tools, from original concepts by the seller, and every file is checked for printability before it is sold.

LICENCE
© OnBrandCraftz. Personal use and gifts only. Do not sell prints, or share or resell the files.
Questions: Printing3dthings@outlook.com
```

## Where every claim comes from

- **Sizes, times and tealights:** each building's own README inside the ZIP, which the
  buyer also gets. The older Etsy drafts in
  `openscad_models/christmas_village/listings/DRAFTS_downloads.md` give one-colour
  times about three times longer (cottage 4 h 31 m against the README's 1 h 33 m).
  The READMEs were built later, on 2026-10-30, so they're the ones used. The
  live Etsy listings may carry the old times; fix them when the shop is back.
- **The files:** the ZIPs are the Etsy bundle parts joined, byte for byte apart
  from one README line (`build_store_kit.py` checks it).
- **The pictures:** rendered from the STLs inside those ZIPs, in each README's
  colours (`render_covers.py`).
- **Not done yet:** a check that none of these designs is posted free on
  MakerWorld. Scott, tell me if any are, and I'll leave those out or say so.

Rebuild: `python3 build_store_kit.py`, then `python3 render_covers.py`.
