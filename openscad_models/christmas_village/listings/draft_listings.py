#!/usr/bin/env python3
"""Draft the Christmas village download listings into DRAFTS_downloads.md.

Drafts only: nothing here talks to Etsy. Every title, tag set and price is
checked against the shop's rules (title 100-140 chars, 13 tags of at most 20
chars, no tag repeating a title phrase, price ending .99/.97/.49) and the run
fails if any listing breaks one. Size, print time and filament come from the
same sources as the download READMEs (build_downloads.building_facts), so a
listing can never disagree with the file the buyer receives.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "downloads"))
from build_downloads import STYLES, building_facts  # noqa: E402

FILE_PRICE = "5.99"
BUNDLE_PRICE = "24.99"

# Per building: the title's lead phrase, a one-line hook, and what the model
# actually has, colours included (the 3MF carries them).
B = {
 ("victorian", "cottage"): dict(
    tag="cottage stl",
    lead="Victorian Christmas Village Cottage STL 3MF",
    hook="A round brick cottage under a snowy slate cone, with a little gable over its wreathed door: the first house of the Victorian village.",
    feat=["Round brick drum with a flat front rising into a gable, scalloped bargeboard and a pointed attic window",
          "Steep slate cone with snow on its crown and icicles under the eave",
          "Arched door with an evergreen wreath and garland, four sash windows with keystones and window boxes",
          "Tall chimney with two pots, on a soft snow base with drifts and a curved step"]),
 ("victorian", "shop_house"): dict(
    tag="victorian shop",
    lead="Victorian Christmas Village Shop House STL 3MF",
    hook="A rounded Victorian shop with a bow window downstairs and a jettied timber-framed storey above, under one swept slate roof.",
    feat=["Brick shop floor with a green bow window, four arched shop windows and a panelled door with a wreath",
          "Timber-framed plaster upper storey jutting out on brackets, with six diamond-leaded casements",
          "Round slate roof swept all the way round, snow on the crown, icicles under the curled eave",
          "Front dormer with a scalloped bargeboard, and a tall stepped chimney with two pots"]),
 ("victorian", "toy_shop"): dict(
    tag="toy shop model",
    lead="Victorian Christmas Village Toy Shop STL 3MF",
    hook="A two-storey brick toy shop with TOYS raised on its bay window, and a round tower on the corner with a flared slate cone.",
    feat=["Canted bay shop window with TOYS in raised letters on its fascia, under its own small roof",
          "Square brick shop with white quoins, sash windows, window boxes and a pointed window in each gable",
          "Round corner tower rising past the ridge to a flared cone and finial, the door at its foot",
          "One tealight lights both: the tower opens into the shop inside"]),
 ("victorian", "church"): dict(
    tag="church stl",
    lead="Victorian Christmas Village Church STL 3MF",
    hook="The tallest building in the village: a brick church with a rose window, a square bell tower and a tall octagonal spire.",
    feat=["Long brick nave with three tall lancet windows down each side and a round rose window over the door",
          "Square bell tower with louvred belfry lights and a tall broach spire topped by a ball and cross",
          "Half-round apse at the back with three lancets under a half cone of slate",
          "164 mm tall; the tower and apse open into the nave so one tealight fills all three"]),
 ("victorian", "coaching_inn"): dict(
    tag="inn model",
    lead="Victorian Christmas Village Coaching Inn STL 3MF",
    hook="A long two-storey coaching inn with a pointed carriage archway right through one end, and an INN sign with raised letters.",
    feat=["Brick ground floor with six segmental windows, a wreathed door and a wall lantern beside the archway",
          "Pointed carriage archway through the building, ringed with voussoirs and a keystone",
          "Plaster upper floor jettied out on a timber beam, with fifteen casements and dark timbers",
          "Steep slate roof with icicles and scalloped bargeboards, and two tall chimneys; the widest in the village"]),
 ("victorian", "townhouse"): dict(
    tag="townhouse stl",
    lead="Victorian Christmas Village Townhouse STL 3MF",
    hook="A tall, narrow three-storey townhouse with a round bow window running up its whole front and a mansard roof with dormers.",
    feat=["Round brick bow up all three storeys, three sash windows on each, under a bell-flared cone",
          "Door with a fanlight and a wreath, up two steps between low cheek walls",
          "Mansard roof with three dormers over a deep cornice, and a tall chimney",
          "The bow and every dormer open into the house, so one tealight lights them all"]),
 ("victorian", "santas_workshop"): dict(
    tag="santa workshop stl",
    lead="Victorian Santa's Workshop STL 3MF, Christmas Village",
    hook="A long brick workshop with one big arched window full of toys, lit from inside so they show against the glowing glass.",
    feat=["Big round-arched window with a rocking horse, teddy, sailboat, toy soldier and jack-in-the-box drawn on its glass",
          "Arched loading doors with a wreath on each leaf, under a SANTA'S WORKSHOP sign with raised letters",
          "Three skylights in the slate roof, scalloped bargeboards and finials, a tall chimney",
          "Snow on the roof, icicles under the eaves, a soft snow base with drifts"]),
 ("victorian", "clock_tower"): dict(
    tag="clock tower stl",
    lead="Victorian Christmas Village Clock Tower STL 3MF",
    hook="A square brick clock tower rising out of a round brick drum, with a big clock face on every side that glows when lit.",
    feat=["Four glazed clock faces set at ten past ten; lit, the hour marks and hands show dark against the glow",
          "Round one-storey drum with sash windows and a wreathed door under a slate cone",
          "Steep slate pyramid over a white cornice, snow on its point and a finial",
          "160 mm tall on a 67 mm base"]),
 ("gingerbread", "cottage"): dict(
    tag="cupcake house",
    lead="Gingerbread Christmas Village Cupcake House STL 3MF",
    hook="A gingerbread cottage shaped like a cupcake: a fluted drum under a chocolate dome dripping with white icing.",
    feat=["Fluted gingerbread drum with 40 ribs like a cupcake paper",
          "Chocolate dome with a wavy band of piped icing and 30 drips running down",
          "Gumdrops round the dome and one on top, four round peppermint windows",
          "Chocolate-bar door between two candy canes, on a snow base with peppermints"]),
 ("gingerbread", "turret_house"): dict(
    tag="turret house",
    lead="Gingerbread Christmas Village Turret House STL 3MF",
    hook="A swooping gingerbread house with a leaning turret and a candy-cane spire bent over at the top.",
    feat=["Round-ended chocolate roof swooping out into a curl of icing, with gumdrops along the ridge",
          "Leaning round turret with icing collars and a bell cone carrying a candy-cane spire",
          "Half-round porch on peppermint-stick columns over a chocolate-bar door",
          "Six arched windows framed in icing beads, three roofs at three heights"]),
 ("gingerbread", "candy_cane_chapel"): dict(
    tag="candy cane decor",
    lead="Gingerbread Christmas Village Candy Cane Chapel STL 3MF",
    hook="A gingerbread chapel with a round tower striped red in a spiral like a candy cane, its spire curling over into a crook.",
    feat=["Candy-cane tower striped in a spiral all the way up, with a spire that curls over at the tip",
          "Gingerbread nave under a chocolate scallop-tile gable with icing dripping off the eaves",
          "Arched windows framed in icing beads and a peppermint round window in the back gable",
          "Candy canes standing either side of the tower; one tealight lights tower and nave"]),
 ("gingerbread", "sweet_shop"): dict(
    tag="sweet shop decor",
    lead="Gingerbread Christmas Village Sweet Shop STL 3MF",
    hook="A three-tier layer cake with a cherry on top and a little gingerbread sweet shop standing out of its front.",
    feat=["Three tiers: gingerbread, chocolate and gingerbread, with frosting dripping off every ledge and berries round them",
          "SWEETS in raised letters across the bottom tier, a frosting dome and a cherry on top",
          "Gingerbread shop out front with an arched display window, a chocolate-bar door and a lollipop sign",
          "Snow base with drifts and peppermints"]),
 ("gingerbread", "cocoa_cafe"): dict(
    tag="hot cocoa decor",
    lead="Gingerbread Christmas Cocoa Cafe STL 3MF, Christmas Village",
    hook="A tower shaped like a hot-cocoa mug, piled with whipped cream and marshmallows, with a gingerbread cafe out of its front.",
    feat=["Mug with red stripes, a chunky handle and COCOA in raised letters; its windows are drawn in red on the white",
          "Cocoa, a tall swirl of whipped cream, toasted marshmallows and a candy-cane stirrer",
          "Gingerbread cafe with a striped awning over an arched window and a chocolate-bar door",
          "Snow base with peppermints; one tealight lights mug and cafe"]),
 ("gingerbread", "santas_workshop"): dict(
    tag="santa workshop stl",
    lead="Gingerbread Santa's Workshop STL 3MF, Christmas Village",
    hook="A round gingerbread workshop under a steep chocolate cone ringed with gumdrops, with a peppermint-stick chimney up its back.",
    feat=["Gingerbread drum with arched windows on two levels and icing dripping from its top ledge",
          "Steep chocolate shingle cone with red and white gumdrops round its foot and a big gumdrop on top",
          "Loading wing with chocolate-bar double doors and a peppermint round window",
          "Tall white chimney with red stripes winding up it like a peppermint stick"]),
 ("gingerbread", "cookie_clock_tower"): dict(
    tag="cookie decor",
    lead="Gingerbread Christmas Village Cookie Clock Tower STL 3MF",
    hook="A tower stacked from three thick gingerbread cookies, with a big frosted-cookie clock that glows when lit.",
    feat=["Three cookie discs with icing dripping between them",
          "Big scalloped cookie clock piped with icing dots, its face glazed so it glows, set at ten past ten",
          "Chocolate shingle cone with gumdrops round its foot and a candy cane out of the top",
          "Arched windows framed in icing; 141 mm tall"]),
}

STYLE_TAGS = {
    "victorian": ["dickens village", "victorian village"],
    "gingerbread": ["gingerbread village", "gingerbread house"],
}
COMMON_TAGS = ["village stl file", "tealight house", "christmas village", "3d print file",
               "bambu lab 3mf", "ams multicolor", "winter village", "holiday decor diy",
               "3d printing gift", "lighted village", "xmas village stl", "christmas stl",
               "led tealight house", "mantel decor"]


def tags_for(b: dict, style: str, title: str) -> list:
    t = title.lower()
    out = [x for x in [b["tag"]] + STYLE_TAGS[style] + COMMON_TAGS if x not in t]
    return out[:13]


def title_for(b: dict, style: str) -> str:
    tail = {"victorian": "Tealight House, Multicolor AMS File, Dickens Style, Instant Download",
            "gingerbread": "Tealight House, Multicolor AMS File, Candy Decor, Instant Download"}[style]
    return f"{b['lead']}, {tail}"


def description(b: dict, f: dict, label: str) -> str:
    w, d, h = f["size"]
    feats = "\n".join(f"• {x}" for x in b["feat"])
    return f"""{b['hook']} This is a digital download of 3D print files for the {f['title']}, part of the OnBrandCraftz {label} Christmas village.

⚠️ DIGITAL DOWNLOAD: 3D print files only. No physical item is shipped and no tealight is included. You need a 3D printer.

━━━━━━━━━━━━━━━━━━━━━━━━
🏠 THE BUILDING
━━━━━━━━━━━━━━━━━━━━━━━━
{feats}
• Hollow lantern with an open base: set it over a battery LED tealight and it glows through every window

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
• A 3MF with all four colour parts already in place: opens in Bambu Studio and PrusaSlicer
• The same four parts as STL files for any other slicer
• A README with size, settings, colours and lighting

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINTING
━━━━━━━━━━━━━━━━━━━━━━━━
• Size: {w:.0f} × {d:.0f} × {h:.0f} mm
• Supports OFF: every overhang is shaped to print without them
• Print standing up as it sits in the file, 0.2 mm layers
• One colour: about {f['time']}, about {f['grams']} g of PLA (sliced estimate)
• Four colours with an AMS: the parts are set up already; slice it for your own time and purge
• Designed and sliced for a Bambu Lab P1S with a 0.4 mm nozzle

━━━━━━━━━━━━━━━━━━━━━━━━
💡 LIGHTING
━━━━━━━━━━━━━━━━━━━━━━━━
Fits a battery LED tealight up to about 38 mm across and 45 mm tall (not included). Battery LED lights only, never a flame.

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this a physical item?
A: No. You get files to print yourself.

Q: Do I need an AMS?
A: No. Print it in one colour and paint it, or assign the four parts to four filaments.

Q: Will it work in my slicer?
A: The 3MF opens in Bambu Studio and PrusaSlicer, and the STLs work in any slicer.

Q: Can I sell prints?
A: No, the licence is personal use only (see below).

━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ABOUT THIS DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━
This model was designed with the help of AI tools, from original concepts by the seller, and every file is checked for printability before listing.

━━━━━━━━━━━━━━━━━━━━━━━━
© LICENCE
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use and gifts only. Do not sell prints, or share or resell the files."""


def check(title: str, tags: list, price: str, who: str) -> list:
    errs = []
    if not 100 <= len(title) <= 140:
        errs.append(f"{who}: title is {len(title)} chars")
    if len(tags) != 13:
        errs.append(f"{who}: {len(tags)} tags")
    errs += [f"{who}: tag '{t}' is {len(t)} chars" for t in tags if len(t) > 20]
    if not price.endswith((".99", ".97", ".49")):
        errs.append(f"{who}: price {price}")
    return errs


def main() -> int:
    out, errs = ["# Christmas village — download listing drafts\n",
                 "Drafts only. Nothing is published; each goes to the Action Center for Scott's approval.\n"], []
    for style, (label, slugs) in STYLES.items():
        for slug in slugs:
            f = building_facts(style, slug)
            b = B[(style, slug)]
            title = title_for(b, style)
            tags = tags_for(b, style, title)
            errs += check(title, tags, FILE_PRICE, f["name"])
            out += [f"\n## {f['title']} — files\n", f"**Price:** ${FILE_PRICE}\n",
                    f"**Title** ({len(title)} chars): {title}\n", "**Tags:** " + ", ".join(tags) + "\n",
                    "**Description:**\n", "```", description(b, f, label), "```"]
    bundle_titles = {
        "victorian": "Victorian Christmas Village STL 3MF Bundle, 8 Tealight Houses, Dickens Style Church Inn Toy Shop, Multicolor AMS, Instant Download",
        "gingerbread": "Gingerbread Christmas Village STL 3MF Bundle, 7 Tealight Houses, Candy Cane Chapel, Cocoa Cafe, Multicolor AMS, Instant Download",
    }
    for style, (label, slugs) in STYLES.items():
        facts = [building_facts(style, s) for s in slugs]
        title = bundle_titles[style]
        tags = [x for x in STYLE_TAGS[style] + ["village stl bundle", "christmas stl"] + COMMON_TAGS
                if x not in title.lower()][:13]
        errs += check(title, tags, BUNDLE_PRICE, f"{style} bundle")
        n = len(facts)
        listing = "\n".join(f"• {f['title']}: {f['size'][0]:.0f} × {f['size'][1]:.0f} × {f['size'][2]:.0f} mm, about {f['time']} in one colour" for f in facts)
        parts = "two ZIP files (the meshes are too large for one)" if style == "gingerbread" else "one ZIP file"
        desc = f"""The whole OnBrandCraftz {label} Christmas village: all {n} buildings as 3D print files, one design language and one scale, so they stand together as one street. This is a digital download; no physical item or tealight is shipped.

━━━━━━━━━━━━━━━━━━━━━━━━
🏘️ THE {n} BUILDINGS
━━━━━━━━━━━━━━━━━━━━━━━━
{listing}

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
• {parts}, one folder per building
• Each building as a four-colour 3MF (Bambu Studio, PrusaSlicer) and as STL parts for any slicer
• A README per building with size, settings, colours and lighting

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ PRINTING
━━━━━━━━━━━━━━━━━━━━━━━━
• Supports OFF, printed standing up, 0.2 mm layers
• One colour to paint, or four colours with an AMS
• Every building is a hollow lantern with an open base for a battery LED tealight up to about 38 mm across and 45 mm tall (not included). Battery lights only, never a flame.

━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ABOUT THIS DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━
These models were designed with the help of AI tools, from original concepts by the seller, and every file is checked for printability before listing.

━━━━━━━━━━━━━━━━━━━━━━━━
© LICENCE
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use and gifts only. Do not sell prints, or share or resell the files."""
        out += [f"\n## {label} village bundle — files\n", f"**Price:** ${BUNDLE_PRICE}\n",
                f"**Title** ({len(title)} chars): {title}\n", "**Tags:** " + ", ".join(tags) + "\n",
                "**Description:**\n", "```", desc, "```"]
    if errs:
        print("\n".join(errs))
        return 1
    (HERE / "DRAFTS_downloads.md").write_text("\n".join(out) + "\n")
    print("ok: 15 download drafts and 2 bundles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
