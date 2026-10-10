#!/usr/bin/env python3
"""Draft the printed (shipped) Christmas village listings into DRAFTS_printed.md.

Drafts only: nothing here talks to Etsy. What ships (Scott, 2026-10-08): each
building printed in white so the buyer can paint it, with a battery LED
tealight. Photos of copies painted by Jessee are labelled as painted. A
painted one is sold only when a buyer asks for it.

A white print shows only shape, so every feature line below names something
a white print really has (raised, carved or cut through), never a colour.
Checked against the white renders in white_check/. Size and print time come
from the same sources as the download READMEs, and the price from the print
time tier in RESEARCH_2026-10-08.md; the rules check is draft_listings.check.
"""
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "downloads"))
from build_downloads import STYLES, building_facts  # noqa: E402
from draft_listings import B, check  # noqa: E402

# Tiers by single-colour print time, the real cost (RESEARCH_2026-10-08.md).
TIERS = [(5.25, "29.99"), (7.5, "34.99"), (99, "39.99")]

# Per building: the tag that names it, and what a white print of it shows.
W = {
 ("victorian", "cottage"): dict(
    hook="A round cottage under a steep, snow-capped cone roof, with a little gable over its wreathed door: the first house of the Victorian village.",
    tag="village cottage",
    feat=["Round drum laid in raised brick courses, with a flat front rising into a gable, a scalloped bargeboard and a pointed attic window",
          "Steep cone roof with snow piled on its crown and icicles hanging from the eave",
          "Arched door with a wreath and a garland over it; four windows with keystones and window boxes",
          "Tall chimney with two pots, on a snow base with drifts and a curved step"]),
 ("victorian", "shop_house"): dict(
    hook="A rounded Victorian shop with a bow window downstairs and a timber-framed storey jutting out above, under one swept roof.",
    tag="village shop",
    feat=["Brick shop floor with a bow window, four arched shop windows and a panelled door with a wreath",
          "Timber-framed upper storey jutting out on brackets, its timbers standing proud of the plaster, with six diamond-leaded casements",
          "Round roof swept all the way round, snow on the crown, icicles under the curled eave",
          "Front dormer with a scalloped bargeboard, and a tall stepped chimney with two pots"]),
 ("victorian", "toy_shop"): dict(
    hook="A two-storey toy shop with TOYS in raised letters over its bay window, and a round corner tower with a flared cone.",
    tag="toy shop decor",
    feat=["Bay shop window with TOYS in raised letters on its fascia, under its own small roof",
          "Square brick shop with quoins, sash windows, window boxes and a pointed window in each gable",
          "Round corner tower rising past the ridge to a flared cone and finial, the door at its foot",
          "One tealight lights both: the tower opens into the shop inside"]),
 ("victorian", "church"): dict(
    hook="The tallest building in the village: a church with a round rose window, a square bell tower and a tall spire.",
    tag="village church",
    feat=["Long brick nave with three tall lancet windows down each side and a round rose window over the door",
          "Square bell tower with louvred belfry openings and a tall spire topped by a ball and cross",
          "Half-round apse at the back with three lancets",
          "164 mm tall; the tower and apse open into the nave so one tealight fills all three"]),
 ("victorian", "coaching_inn"): dict(
    hook="A long two-storey coaching inn with a pointed carriage archway right through one end, timbers framing its upper floor and an INN sign in raised letters.",
    tag="inn decor",
    feat=["Brick ground floor with six windows, a wreathed door and a wall lantern beside the archway",
          "Pointed carriage archway right through the building, ringed with voussoirs and a keystone",
          "Upper floor jettied out on a beam, with its timbers raised on the plaster and an INN sign in raised letters",
          "Steep roof with icicles, scalloped bargeboards and two tall chimneys; the widest building in the village"]),
 ("victorian", "townhouse"): dict(
    hook="A tall, narrow three-storey townhouse with a round bow running up its whole front and a mansard roof with dormers.",
    tag="village townhouse",
    feat=["Round brick bow up all three storeys, three sash windows on each, under a bell-flared cone",
          "Door with a fanlight and a wreath, up two steps between low cheek walls",
          "Mansard roof with three dormers over a deep cornice, and a tall chimney",
          "The bow and every dormer open into the house, so one tealight lights them all"]),
 ("victorian", "santas_workshop"): dict(
    hook="A long workshop with one big arched window full of toys, under a sign that reads SANTA'S WORKSHOP.",
    tag="santa workshop",
    feat=["Big round-arched window with a rocking horse, teddy, sailboat, toy soldier and jack-in-the-box raised on its glass",
          "Arched loading doors with a wreath on each leaf, under a SANTA'S WORKSHOP sign in raised letters",
          "Three skylights in the roof, scalloped bargeboards and finials, a tall chimney",
          "Snow on the roof, icicles under the eaves, a snow base with drifts"]),
 ("victorian", "clock_tower"): dict(
    hook="A square clock tower rising out of a round drum, with a clock face set at ten past ten on every side.",
    tag="clock tower decor",
    feat=["A clock face on every side, set at ten past ten, its hour marks and hands raised on the glass",
          "Round one-storey brick drum with sash windows and a wreathed door under a cone roof",
          "Steep pyramid roof over a cornice, snow on its point and a finial",
          "160 mm tall on a 67 mm base"]),
 ("gingerbread", "cottage"): dict(
    hook="A cottage shaped like a cupcake: a fluted drum under a dome dripping with piped icing and topped with gumdrops.",
    tag="cupcake house",
    feat=["Fluted drum with 40 ribs like a cupcake paper",
          "Dome roof with a wavy band of piped icing and drips running down",
          "Gumdrops round the dome and one on top, four round peppermint windows with raised swirls",
          "Chocolate-bar door between two raised candy canes, on a snow base with peppermints"]),
 ("gingerbread", "turret_house"): dict(
    hook="A swooping gingerbread-style house with a leaning turret and a candy-cane spire bent over at the top.",
    tag="turret house",
    feat=["Round-ended roof swooping out into a curl of icing, with gumdrops along the ridge",
          "Leaning round turret with icing collars and a bell cone under a candy-cane spire bent over at the top",
          "Half-round porch on striped peppermint-stick columns over a chocolate-bar door",
          "Six arched windows framed in icing beads, three roofs at three heights"]),
 ("gingerbread", "candy_cane_chapel"): dict(
    hook="A gingerbread-style chapel with a round tower that rises to a spire curling over like a candy cane's crook, and striped candy canes at its door.",
    tag="candy cane decor",
    feat=["Round tower and spire that curls over at the tip like a candy cane's crook; its spiral stripes are left for you to paint",
          "Gable roof of scallop tiles with icing dripping off the eaves",
          "Arched windows framed in icing beads and a peppermint round window in the back gable",
          "Striped candy canes standing either side of the tower; one tealight lights tower and nave"]),
 ("gingerbread", "sweet_shop"): dict(
    hook="A three-tier layer cake with a cherry on top, SWEETS across its bottom tier and a little shop standing out of its front.",
    tag="sweet shop decor",
    feat=["Three-tier layer cake with frosting dripping off every ledge and berries round the tiers",
          "SWEETS in raised letters across the bottom tier, a frosting dome and a cherry on top",
          "Little shop out front with an arched display window, a chocolate-bar door and a swirled lollipop sign",
          "Snow base with drifts and peppermints"]),
 ("gingerbread", "cocoa_cafe"): dict(
    hook="A tower shaped like a hot-cocoa mug, piled with whipped cream and marshmallows, with COCOA on the mug and a little cafe out front.",
    tag="hot cocoa decor",
    feat=["Mug-shaped tower with raised stripes, a chunky handle and COCOA in raised letters",
          "Whipped cream piled in a tall swirl, marshmallows and a striped candy-cane stirrer",
          "Little cafe out front with a striped awning over an arched window and a chocolate-bar door",
          "Snow base with peppermints; one tealight lights mug and cafe"]),
 ("gingerbread", "santas_workshop"): dict(
    hook="A round workshop under a steep shingled cone ringed with gumdrops, with a striped peppermint-stick chimney winding up its back.",
    tag="santa workshop",
    feat=["Round drum with arched windows on two levels and icing dripping from its top ledge",
          "Steep shingled cone with gumdrops round its foot and a big gumdrop on top",
          "Loading wing with chocolate-bar double doors and a peppermint round window",
          "Tall chimney with raised stripes winding up it like a peppermint stick"]),
 ("gingerbread", "cookie_clock_tower"): dict(
    hook="A tower stacked from three thick cookies, with a big frosted-cookie clock set at ten past ten.",
    tag="cookie decor",
    feat=["Three thick cookie discs stacked, with icing dripping between them",
          "Big scalloped cookie clock piped with icing dots, set at ten past ten, its hands raised",
          "Shingled cone with gumdrops round its foot and a striped candy cane out of the top",
          "Arched windows framed in icing; 141 mm tall"]),
}

STYLE_TAGS = {"victorian": ["dickens village", "victorian village"],
              "gingerbread": ["gingerbread village", "gingerbread house"]}
COMMON_TAGS = ["christmas village", "tealight house", "lighted village", "paint your own",
               "diy christmas craft", "3d printed decor", "christmas mantel", "winter village",
               "led tealight house", "holiday decor", "gift for crafters", "christmas gift",
               "unpainted decor", "village houses"]
TAIL = {"victorian": "3D Printed Tealight House, Unpainted White to Paint, LED Tealight Included",
        "gingerbread": "3D Printed Tealight House, White to Paint, LED Tealight Included"}

# Each opening hook names shapes, not colours: a white print has no "red" or
# "chocolate" (2026-10-08). Checked against the as-printed renders.

# Not decided yet: each line is a question for Scott, printed at the top of the
# drafts so none ships as a guess.
TO_CONFIRM = [
    "Filament: the drafts say white PLA. Change it if the white is PETG or anything else.",
    "Tealight: are batteries included, and is it a flicker LED? The drafts say 'battery LED tealight' and nothing more.",
    "Processing time: the drafts leave it as [PROCESSING]. Print time is 4.5-10 h a building plus packing.",
    "Shipping: box sizes and weights are estimates from the model plus 20 mm of padding; weigh one packed box.",
    "Photos: the painted photos must be of these buildings, labelled 'shown painted'. The first photo should be the white print, lit.",
]


def hours(t: str) -> float:
    m = re.match(r"(\d+) h (\d+) m", t)
    return int(m.group(1)) + int(m.group(2)) / 60


def price_for(t: str) -> str:
    return next(p for h, p in TIERS if hours(t) < h)


def box(size) -> str:
    # the building plus 20 mm of padding each side, to the inch above
    return " × ".join(str(math.ceil((s + 40) / 25.4)) for s in size) + " in"


def title_for(style: str, slug: str) -> str:
    lead = B[(style, slug)]["lead"].replace(" STL 3MF", "")
    return f"{lead}, {TAIL[style]}"


def description(w: dict, f: dict, label: str) -> str:
    sx, sy, sz = f["size"]
    feats = "\n".join(f"• {x}" for x in w["feat"])
    return f"""{w['hook']} This is the finished building, 3D printed in white and shipped unpainted, ready for you to paint, with a battery LED tealight to light it. Part of the OnBrandCraftz {label} Christmas village.

⚠️ WHAT ARRIVES: one 3D printed building in plain white, unpainted, and one battery LED tealight. Photos marked "shown painted" show a copy painted by hand, to show what it can look like. Want one painted for you? Send a message before ordering.

━━━━━━━━━━━━━━━━━━━━━━━━
🏠 THE BUILDING
━━━━━━━━━━━━━━━━━━━━━━━━
{feats}
• Every window, door and line is raised or cut in, so it shows on plain white and your brush has an edge to follow

━━━━━━━━━━━━━━━━━━━━━━━━
📏 SIZE
━━━━━━━━━━━━━━━━━━━━━━━━
{sx:.0f} × {sy:.0f} × {sz:.0f} mm ({sx / 25.4:.1f} × {sy / 25.4:.1f} × {sz / 25.4:.1f} in), snow base included. One solid piece.

━━━━━━━━━━━━━━━━━━━━━━━━
💡 LIGHTING
━━━━━━━━━━━━━━━━━━━━━━━━
The building is hollow with an open base. Switch on the tealight, set the building over it, and it glows through every window. Any battery tealight up to 38 mm across and 45 mm tall fits. Battery lights only, never a candle with a flame.

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PAINTING
━━━━━━━━━━━━━━━━━━━━━━━━
• Acrylic craft paint works well on the printed plastic; a light coat of primer first helps it grip
• Thin coats keep the small details sharp
• Leave the window panes unpainted, or paint them thinly, so the light comes through

━━━━━━━━━━━━━━━━━━━━━━━━
📦 MADE TO ORDER
━━━━━━━━━━━━━━━━━━━━━━━━
• Printed for your order (about {f['time']} on the printer), checked, and packed in a padded box
• Ships within [PROCESSING]; free shipping in the US
• Fine layer lines are part of 3D printing and show on close inspection

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is it painted?
A: No. It ships plain white, ready to paint. Painted photos are marked "shown painted".

Q: Is the light included?
A: Yes, one battery LED tealight comes with every building.

Q: Can I order one painted, or in a colour?
A: Send a message before ordering and we'll see what we can do.

Q: Can I use a real candle?
A: No. The printed plastic softens with heat: battery lights only, and keep it away from heaters, hot cars and strong sun.

Q: Is it a toy?
A: No, it's a decoration for display, not for young children.

━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ABOUT THIS DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━
This building was designed with the help of AI tools, from original concepts by the seller, and printed by the seller on a Bambu Lab P1S.

━━━━━━━━━━━━━━━━━━━━━━━━
© DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━
Design © OnBrandCraftz."""


def main() -> int:
    out = ["# Christmas village — printed listing drafts\n",
           "Drafts only. Nothing is published; each goes to the Action Center for Scott's approval.\n",
           "## To confirm before any of these go live\n"] + [f"- {x}" for x in TO_CONFIRM] + [""]
    errs = []
    for style, (label, slugs) in STYLES.items():
        for slug in slugs:
            f = building_facts(style, slug)
            f.update(style=style, slug=slug)
            w = W[(style, slug)]
            title = title_for(style, slug)
            tags = [x for x in [w["tag"]] + STYLE_TAGS[style] + COMMON_TAGS if x not in title.lower()][:13]
            price = price_for(f["time"])
            errs += check(title, tags, price, f["name"])
            out += [f"\n## {f['title']} — printed\n",
                    f"**Price:** ${price} (print time {f['time']}) · **Box:** {box(f['size'])} (estimate)\n",
                    f"**Title** ({len(title)} chars): {title}\n", "**Tags:** " + ", ".join(tags) + "\n",
                    "**Description:**\n", "```", description(w, f, label), "```"]
    if errs:
        print("\n".join(errs))
        return 1
    (HERE / "DRAFTS_printed.md").write_text("\n".join(out) + "\n")
    print("ok: 15 printed drafts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
