"""
One-time fix: regenerate the 3 broken hero/lifestyle photos (ranks 1-3) on the
live Tropical Leaves listing (4509600086 / DP1064).

Root cause: photos at ranks 1-3 show a recursive "room within a frame" render
artifact instead of the real Tropical Leaves design — a CARDINAL RULE violation
(listing photo does not show the real product). Photos at ranks 4-10 are
correct and untouched. The real design was recovered by cropping the clean
square reference image out of the existing (correct) "What's Included" photo
(rank 6) since no local source file exists for DP1064.

Generates 3 new lifestyle photos in rooms not already used by the correct
photos (living room = rank 4, kitchen/dining = rank 5), using the mandated
generate_verified_photo() pipeline with framed_print physics, then replaces
ranks 1-3 on the live listing.
"""
import sys
from pathlib import Path

from tools.listing_photo_pipeline import generate_verified_photo
from tools.etsy_api import EtsyAPIClient

DESIGN = Path("data/digital_products/wall_art/DP1064_listing_photos/DP1064_source_design.png")
OUT_DIR = Path("data/digital_products/wall_art/DP1064_listing_photos/photos")
LISTING_ID = 4509600086

SCENES = {
    "photo_01_bedroom.jpg": (
        "Photorealistic bedroom interior. The framed print hangs on an off-white "
        "linen-textured wall above a low platform bed with natural light oak frame "
        "and cream linen bedding. A small ceramic lamp on the nightstand, a trailing "
        "pothos plant nearby. Soft diffused morning window light from the left, warm "
        "white balance. Japandi aesthetic, calm and warm. The frame is centered in "
        "the upper-middle of the wall, no overlap with furniture below."
    ),
    "photo_02_office.jpg": (
        "Photorealistic home office interior. The framed print hangs on a warm "
        "white wall with subtle linen texture above a light oak floating desk. A "
        "matte black desk lamp, a small potted plant, a stack of books on the desk. "
        "Bright clean natural daylight from a window on the left, even illumination. "
        "The frame is centered above the desk with no overlap with the desk surface "
        "or lamp."
    ),
    "photo_03_entryway.jpg": (
        "Photorealistic entryway interior. The framed print hangs on a warm cream "
        "plaster wall above a slim console table with a woven rattan basket and a "
        "small ceramic vase with dried pampas grass. Soft natural light from a "
        "nearby doorway, warm inviting atmosphere. The frame is centered above the "
        "console with no overlap with the table or vase."
    ),
}


def main():
    if not DESIGN.exists():
        raise FileNotFoundError(DESIGN)

    api = EtsyAPIClient()
    results = {}
    for filename, scene in SCENES.items():
        out_path = OUT_DIR / filename
        result = generate_verified_photo(
            design_paths=[DESIGN],
            scene_prompt=scene,
            out_path=out_path,
            physics="framed_print",
        )
        results[filename] = result
        if not result.passed:
            print(f"!! {filename} failed verification — NOT uploading. Issues: {result.issues}")

    if "--apply" not in sys.argv:
        print("\nDry run only (images generated, not uploaded). Re-run with --apply to replace ranks 1-3 on the live listing.")
        return

    # Existing rank-1..3 image IDs to delete after the new ones are uploaded.
    imgs = api._request("GET", f"listings/{LISTING_ID}/images")
    old_ids = [r["listing_image_id"] for r in imgs["results"] if r["rank"] in (1, 2, 3)]

    new_filenames = ["photo_01_bedroom.jpg", "photo_02_office.jpg", "photo_03_entryway.jpg"]
    if any(not results[f].passed for f in new_filenames):
        print("Aborting upload — not all 3 replacement photos passed verification.")
        return

    for i, filename in enumerate(new_filenames, start=1):
        path = OUT_DIR / filename
        api.upload_listing_image(LISTING_ID, str(path), rank=i)
        print(f"  uploaded {filename} at rank {i}")

    # Etsy re-ranks on upload; delete the old broken images by ID now that they're superseded.
    for img_id in old_ids:
        api._request("DELETE", f"shops/{api.shop_id}/listings/{LISTING_ID}/images/{img_id}")
        print(f"  deleted old broken image {img_id}")


if __name__ == "__main__":
    main()
