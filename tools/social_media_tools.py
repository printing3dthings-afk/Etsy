"""Tool definitions and implementations for the Social Media Agent (Pinterest-focused)."""

import json
from datetime import date, timedelta
from tools.data_store import DataStore
from tools import pinterest_api

TOOL_DEFINITIONS = [
    {
        "name": "get_pinterest_profile",
        "description": "Get the current Pinterest profile stats and board overview for OnBrandCraftz.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_pin_schedule",
        "description": "Get the recommended Pinterest pinning schedule for the week.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days to plan ahead (default 7)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "generate_pin_description",
        "description": "Generate an SEO-optimized Pinterest pin description for a specific product listing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {
                    "type": "string",
                    "description": "The listing ID to generate a pin description for (e.g. L001)",
                },
                "board": {
                    "type": "string",
                    "description": "The target Pinterest board name",
                },
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "get_board_strategy",
        "description": "Get a content strategy for each Pinterest board — what to pin and how often.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_content_calendar",
        "description": "Generate a 30-day Pinterest content calendar with specific pins, boards, and posting times.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format (defaults to today)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_growth_recommendations",
        "description": "Get actionable recommendations to grow Pinterest followers and drive traffic to the Etsy shop.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "update_pinterest_stats",
        "description": "Update Pinterest metrics (followers, monthly views, pin count) from the seller's manual check.",
        "input_schema": {
            "type": "object",
            "properties": {
                "followers": {"type": "integer"},
                "monthly_views": {"type": "integer"},
                "total_pins": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "get_pinterest_boards",
        "description": "Fetch all Pinterest boards and their IDs from the live Pinterest account. Requires Pinterest OAuth.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "post_pin",
        "description": "Post a pin directly to Pinterest. Requires Pinterest OAuth and an image URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {
                    "type": "string",
                    "description": "The shop listing ID (e.g. L001). Used to get the pre-written title and description.",
                },
                "board_name": {
                    "type": "string",
                    "description": "The exact Pinterest board name to post to.",
                },
                "image_url": {
                    "type": "string",
                    "description": "Direct URL to the product image (must be publicly accessible).",
                },
                "custom_title": {
                    "type": "string",
                    "description": "Optional: override the default pin title.",
                },
                "custom_description": {
                    "type": "string",
                    "description": "Optional: override the default pin description.",
                },
                "link": {
                    "type": "string",
                    "description": "Destination URL (defaults to Etsy shop). Use specific listing URL for best results.",
                },
            },
            "required": ["listing_id", "board_name", "image_url"],
        },
    },
]

BOARDS = [
    {"name": "OnBrandCraftz Etsy Shop", "focus": "All products — main shop showcase board", "pins": 0},
    {"name": "3D Printed Home Décor", "focus": "All 3D printed decor items", "pins": 1},
    {"name": "Cozy Home Lighting & Lamps", "focus": "Crystal lamp, mesh lamp, geometric lamp", "pins": 1},
    {"name": "Coffee Bar Decor & Kitchen Gifts", "focus": "Coffee bar sign, koozies", "pins": 1},
    {"name": "Candle Holders & Ambient Living", "focus": "Tea light candle holder set", "pins": 1},
    {"name": "Boho Home Decor & Vases", "focus": "Ribbed vase, table centerpiece, macrame-style", "pins": 1},
    {"name": "Housewarming Gift Ideas", "focus": "All giftable products — lamps, decor, jewelry boxes", "pins": 0},
    {"name": "Unique Gift Ideas for Home", "focus": "All products framed as gifts", "pins": 0},
    {"name": "Modern Minimalist Living Room", "focus": "Lamps, vases, centerpieces", "pins": 0},
    {"name": "3D Printing & Maker Projects", "focus": "Behind-the-scenes, process, inspiration", "pins": 0},
]

LISTING_BOARD_MAP = {
    "L001": ["Cozy Home Lighting & Lamps", "3D Printed Home Décor", "OnBrandCraftz Etsy Shop", "Unique Gift Ideas for Home"],
    "L002": ["Boho Home Decor & Vases", "3D Printed Home Décor", "Modern Minimalist Living Room"],
    "L003": ["Coffee Bar Decor & Kitchen Gifts", "Unique Gift Ideas for Home", "OnBrandCraftz Etsy Shop"],
    "L004": ["Candle Holders & Ambient Living", "Boho Home Decor & Vases", "Housewarming Gift Ideas"],
    "L005": ["Cozy Home Lighting & Lamps", "3D Printed Home Décor", "Housewarming Gift Ideas", "OnBrandCraftz Etsy Shop"],
    "L006": ["Boho Home Decor & Vases", "Modern Minimalist Living Room", "Housewarming Gift Ideas"],
    "L007": ["Cozy Home Lighting & Lamps", "Modern Minimalist Living Room", "3D Printed Home Décor"],
    "L008": ["Coffee Bar Decor & Kitchen Gifts", "Unique Gift Ideas for Home", "OnBrandCraftz Etsy Shop"],
    "L009": ["Housewarming Gift Ideas", "Unique Gift Ideas for Home", "OnBrandCraftz Etsy Shop"],
    "L010": ["Housewarming Gift Ideas", "Unique Gift Ideas for Home", "OnBrandCraftz Etsy Shop"],
}

PIN_DESCRIPTIONS = {
    "L001": {
        "description": "✨ This 3D printed crystal glow lamp is giving total fairy-tale vibes! Faceted geometric design casts the most beautiful light patterns. Made to order in Indiana. 🛍️ Shop link in bio!\n\n#3DPrintedLamp #CrystalLamp #GlowLamp #GeometricDecor #HomeDecorInspo #ModernHomeDecor #NightLight #3DPrinting #EtsyFinds #UniqueHomeDecor",
        "title": "3D Printed Crystal Glow Lamp | Faceted Geometric Night Light",
    },
    "L002": {
        "description": "🖤 Obsessed with this matte black ribbed vase! Perfect for dried pampas grass or eucalyptus. Modern minimalist vibes, 3D printed to order. 🌿 Shop link in bio!\n\n#RibbedVase #MatteBlack #MinimalistDecor #DryFlowers #PampasGrass #3DPrinted #BohoHome #HomeDecor #EtsyShop #ModernVase",
        "title": "3D Printed Matte Black Ribbed Vase | Modern Minimalist Home Decor",
    },
    "L003": {
        "description": "☕ This grumpy cat 'Ready to Brew' sign is SO my Monday morning mood 😂 3D printed coffee bar sign that'll make everyone smile. Perfect kitchen gift! ☕ Shop link in bio!\n\n#CoffeeBarDecor #FunnyCatSign #CatLovers #CoffeeBar #KitchenDecor #CatMom #3DPrinted #FunnyGift #EtsyFinds #CoffeeLover",
        "title": "3D Printed Funny Cat Coffee Bar Sign | Ready to Brew Kitchen Decor",
    },
    "L004": {
        "description": "🕯️ Ambient lighting just got an upgrade! These boho 3D printed tea light candle holders create the coziest glow. Perfect for a relaxing evening at home. 🏡 Shop link in bio!\n\n#CandleHolders #TeaLight #BohoDecor #CandleHolder #AmbientLighting #CozyHome #3DPrinted #HomeDecorIdeas #EtsyShop #BohoHome",
        "title": "3D Printed Boho Tea Light Candle Holder Set | Cozy Ambient Lighting",
    },
    "L005": {
        "description": "🌟 The most gorgeous lamp on my nightstand right now! This 3D printed mesh table lamp with shade casts the most incredible geometric shadow patterns. Total conversation piece. 💡 Shop link in bio!\n\n#TableLamp #MeshLamp #GeometricLamp #BedsideLamp #3DPrintedLamp #HomeDecorInspo #ModernLighting #EtsyFinds #NightLight #UniqueHome",
        "title": "3D Printed Mesh Table Lamp with Shade | Geometric Bedside Light",
    },
    "L006": {
        "description": "🌿 Boho dining table centrepiece goals! This 3D printed set brings instant warmth and texture to any table. Vase + candle holder + tray — all in one. 🏡 Shop link in bio!\n\n#TableCenterpiece #BohoCenterpiece #DiningDecor #BohoHome #TableDecor #HomeDecorInspo #3DPrinted #EtsyFinds #ModernBoho #CenterpieceIdeas",
        "title": "3D Printed Boho Table Centerpiece Set | Dining Table Decor",
    },
    "L007": {
        "description": "✨ Loving the soft geometric glow this lamp gives my living room! 3D printed with an intricate lattice design — no two shadows are the same. 💡 Made to order from Indiana. Shop link in bio!\n\n#GeometricLamp #TableLamp #3DPrintedLamp #ModernDecor #HomeDecorInspo #BedsideLamp #UniqueGifts #EtsyShop #GeometricDecor #NightLight",
        "title": "3D Printed Geometric Table Lamp | Modern Home Decor Lighting",
    },
    "L008": {
        "description": "🏁 Race day just got cooler! This 3D printed slim can koozie with checkered flag design is the perfect party accessory. Fits slim cans, keeps drinks cold in style! 🍺 Shop link in bio!\n\n#CanKoozie #RaceDay #BeerKoozie #PartyGifts #3DPrinted #FunnyGifts #SlimCan #RaceFan #EtsyFinds #GiftForHim",
        "title": "3D Printed Race Day Can Koozie | Funny Beer Slim Can Cooler",
    },
    "L009": {
        "description": "💝 The most beautiful jewelry box I've ever seen! Hand painted wooden jewelry box with drawers — each one is unique and made with so much love. Perfect gift for her! 🎁 Shop link in bio!\n\n#JewelryBox #HandPainted #WoodenJewelryBox #GiftForHer #JewelryStorage #HandmadeGifts #EtsyFinds #UniqueGifts #JewelryOrganizer #BirthdayGift",
        "title": "Hand Painted Wood Jewelry Box | Decorative Wooden Storage with Drawers",
    },
    "L010": {
        "description": "💎 Organize your jewelry in style! This hand painted boho wooden jewelry organizer has the prettiest floral details. Makes the most thoughtful gift for any occasion! 🌸 Shop link in bio!\n\n#JewelryOrganizer #HandPainted #BohoDecor #JewelryStorage #GiftForHer #WoodJewelryBox #HandmadeGifts #EtsyShop #UniqueGifts #JewelryBox",
        "title": "Hand Painted Boho Wood Jewelry Organizer | Decorative Storage with Drawers",
    },
}

BEST_TIMES = ["8:00 PM", "9:00 PM", "2:00 PM", "8:00 AM"]
BEST_DAYS = ["Saturday", "Sunday", "Friday", "Tuesday"]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_pinterest_profile":
        return _get_pinterest_profile(store)
    if tool_name == "get_pin_schedule":
        return _get_pin_schedule(tool_input.get("days_ahead", 7), store)
    if tool_name == "generate_pin_description":
        return _generate_pin_description(tool_input["listing_id"], tool_input.get("board", ""), store)
    if tool_name == "get_board_strategy":
        return _get_board_strategy(store)
    if tool_name == "get_content_calendar":
        return _get_content_calendar(tool_input.get("start_date", str(date.today())), store)
    if tool_name == "get_growth_recommendations":
        return _get_growth_recommendations(store)
    if tool_name == "update_pinterest_stats":
        return _update_pinterest_stats(tool_input, store)
    if tool_name == "get_pinterest_boards":
        return _get_pinterest_boards()
    if tool_name == "post_pin":
        return _post_pin(tool_input, store)
    return f"Unknown social media tool: {tool_name}"


def _get_pinterest_profile(store: DataStore) -> str:
    pinterest = store.get("social_media", "pinterest") or {}
    return json.dumps({
        "platform": "Pinterest",
        "username": "printing3dthings",
        "display_name": "OnBrandCraftz",
        "url": "https://www.pinterest.com/printing3dthings",
        "bio": "Handcrafted 3D printed lamps, vases & home decor shipped from Indiana, USA. Unique pieces made to order for modern homes. Shop OnBrandCraftz on Etsy!",
        "followers": pinterest.get("followers", 2),
        "following": pinterest.get("following", 0),
        "monthly_views": pinterest.get("monthly_views", 0),
        "total_pins": pinterest.get("total_pins", 4),
        "boards": len(BOARDS),
        "board_list": [{"name": b["name"], "pins": b["pins"], "focus": b["focus"]} for b in BOARDS],
        "etsy_link_in_bio": True,
        "assessment": "Account is freshly set up with great board structure. 10 boards created but only 4 pins total. Huge growth opportunity — needs consistent daily pinning.",
    }, indent=2)


def _get_pin_schedule(days_ahead: int, store: DataStore) -> str:
    listings = store.listings
    schedule = []
    start = date.today()

    for i in range(days_ahead):
        day = start + timedelta(days=i)
        listing = listings[i % len(listings)]
        lid = listing["id"]
        boards = LISTING_BOARD_MAP.get(lid, ["OnBrandCraftz Etsy Shop"])
        board = boards[i % len(boards)]
        pin_data = PIN_DESCRIPTIONS.get(lid, {})
        schedule.append({
            "date": str(day),
            "day_of_week": day.strftime("%A"),
            "time": BEST_TIMES[i % len(BEST_TIMES)],
            "listing_id": lid,
            "product": listing["title"][:60],
            "board": board,
            "pin_title": pin_data.get("title", listing["title"][:60]),
            "etsy_url": f"https://www.etsy.com/shop/onbrandcraftz",
        })

    return json.dumps({
        "pin_schedule": schedule,
        "tip": "Best times to post on Pinterest: 8-9 PM and 2 PM. Best days: Saturday, Sunday, Friday.",
        "goal": f"Pin {days_ahead} times over the next {days_ahead} days — one per day minimum.",
    }, indent=2)


def _generate_pin_description(listing_id: str, board: str, store: DataStore) -> str:
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})

    pin_data = PIN_DESCRIPTIONS.get(listing_id, {})
    suggested_boards = LISTING_BOARD_MAP.get(listing_id, ["OnBrandCraftz Etsy Shop"])

    return json.dumps({
        "listing_id": listing_id,
        "product": listing["title"],
        "price": listing["price"],
        "pin_title": pin_data.get("title", listing["title"]),
        "pin_description": pin_data.get("description", f"Shop this beautiful handmade item at OnBrandCraftz on Etsy! Made to order in Indiana. #EtsyShop #HandmadeDecor #3DPrinted"),
        "destination_url": "https://www.etsy.com/shop/onbrandcraftz",
        "target_board": board or suggested_boards[0],
        "all_suitable_boards": suggested_boards,
        "tip": "Add the destination URL directly to the pin so it clicks through to your Etsy listing.",
    }, indent=2)


def _get_board_strategy(store: DataStore) -> str:
    strategies = []
    for board in BOARDS:
        relevant_listings = [lid for lid, boards in LISTING_BOARD_MAP.items() if board["name"] in boards]
        strategies.append({
            "board": board["name"],
            "current_pins": board["pins"],
            "focus": board["focus"],
            "your_listings_to_pin": relevant_listings,
            "target_pins_per_week": 3,
            "tip": f"Pin your products + 2-3 inspirational/lifestyle repins per week to keep the board active.",
        })
    return json.dumps({"board_strategies": strategies, "total_boards": len(BOARDS)}, indent=2)


def _get_content_calendar(start_date_str: str, store: DataStore) -> str:
    try:
        start = date.fromisoformat(start_date_str)
    except ValueError:
        start = date.today()

    listings = store.listings
    calendar = []

    for i in range(30):
        day = start + timedelta(days=i)
        listing = listings[i % len(listings)]
        lid = listing["id"]
        boards = LISTING_BOARD_MAP.get(lid, ["OnBrandCraftz Etsy Shop"])
        board = boards[(i // len(listings)) % len(boards)]
        pin_data = PIN_DESCRIPTIONS.get(lid, {})

        # Every 3rd day, add a lifestyle/repin suggestion instead
        if i % 7 == 6:
            calendar.append({
                "date": str(day),
                "day": day.strftime("%A"),
                "type": "lifestyle_repin",
                "action": "Repin 2-3 inspiring home decor or 3D printing posts from other creators",
                "boards": ["3D Printing & Maker Projects", "Modern Minimalist Living Room"],
                "time": "8:00 PM",
            })
        else:
            calendar.append({
                "date": str(day),
                "day": day.strftime("%A"),
                "type": "product_pin",
                "listing_id": lid,
                "product": listing["title"][:55],
                "board": board,
                "pin_title": pin_data.get("title", "")[:60],
                "time": BEST_TIMES[i % len(BEST_TIMES)],
                "etsy_url": "https://www.etsy.com/shop/onbrandcraftz",
            })

    return json.dumps({
        "calendar": calendar,
        "period": f"{start} to {start + timedelta(days=29)}",
        "total_pins": len([c for c in calendar if c["type"] == "product_pin"]),
        "total_repins": len([c for c in calendar if c["type"] == "lifestyle_repin"]),
        "tip": "Use Pinterest's built-in scheduler to queue these up in batches. Do a week at a time on Sundays.",
    }, indent=2)


def _get_growth_recommendations(store: DataStore) -> str:
    recommendations = [
        {
            "priority": 1,
            "action": "Pin ALL 10 listings immediately",
            "detail": "You have 10 products and only 4 pins. Pin every product to at least 2-3 relevant boards TODAY. This is the fastest way to get traction.",
            "time_required": "30 minutes",
        },
        {
            "priority": 2,
            "action": "Add your Etsy shop link to every pin",
            "detail": "Every pin should link directly to your Etsy shop. Pinterest is a massive traffic driver to Etsy — buyers discover on Pinterest, purchase on Etsy.",
            "time_required": "Ongoing",
        },
        {
            "priority": 3,
            "action": "Pin consistently — 1 pin per day minimum",
            "detail": "Pinterest rewards consistency. Daily pinning grows monthly views faster than sporadic big batches. Use the 30-day calendar the Social Media Agent provides.",
            "time_required": "5-10 min/day",
        },
        {
            "priority": 4,
            "action": "Add keywords to board titles and descriptions",
            "detail": "Boards like 'Cozy Home Lighting & Lamps' are good. Add descriptions to each board with keywords like '3D printed', 'handmade', 'modern home decor', 'Etsy'.",
            "time_required": "20 minutes",
        },
        {
            "priority": 5,
            "action": "Repin lifestyle content from big accounts",
            "detail": "Repinning from popular home decor accounts exposes your profile to their followers. Aim for 2-3 repins per week alongside your product pins.",
            "time_required": "10 min/week",
        },
        {
            "priority": 6,
            "action": "Use vertical images (2:3 ratio, 1000x1500px)",
            "detail": "Vertical pins take up more screen real estate and get more clicks. If your Etsy photos are square, create a Pinterest-optimized version with a lifestyle background or text overlay.",
            "time_required": "Per product",
        },
        {
            "priority": 7,
            "action": "Apply for Pinterest's Verified Merchant Program",
            "detail": "Once you have a few sales, apply for Verified Merchant status. It adds a blue checkmark and boosts your pins in search results.",
            "time_required": "15 min to apply",
        },
    ]
    return json.dumps({
        "current_status": {"followers": 2, "total_pins": 4, "boards": 10},
        "growth_recommendations": recommendations,
        "30_day_goal": "Reach 50+ monthly views and 25+ pins",
        "90_day_goal": "Reach 500+ monthly views, 100+ followers, consistent Etsy traffic from Pinterest",
    }, indent=2)


def _update_pinterest_stats(data: dict, store: DataStore) -> str:
    pinterest = store.get("social_media", "pinterest") or {}
    if "followers" in data:
        pinterest["followers"] = data["followers"]
    if "monthly_views" in data:
        pinterest["monthly_views"] = data["monthly_views"]
    if "total_pins" in data:
        pinterest["total_pins"] = data["total_pins"]
    pinterest["last_updated"] = str(date.today())

    social = store.get("social_media") or {}
    social["pinterest"] = pinterest
    store.set(social, "social_media")
    store.save()
    return json.dumps({"success": True, "pinterest": pinterest}, indent=2)


def _get_pinterest_boards() -> str:
    if not pinterest_api.is_configured():
        return json.dumps({
            "status": "oauth_required",
            "message": "Pinterest not connected yet. To enable direct posting: "
                       "1) Go to https://developers.pinterest.com/ "
                       "2) Create an app, copy App ID and App Secret "
                       "3) Add PINTEREST_APP_ID and PINTEREST_APP_SECRET to .env "
                       "4) Run: python tools/pinterest_oauth.py",
            "your_boards": [b["name"] for b in BOARDS],
        }, indent=2)

    try:
        client = pinterest_api.get_client()
        boards = client.get_boards()
        return json.dumps({
            "boards": [{"id": b["id"], "name": b["name"], "pin_count": b.get("pin_count", 0)} for b in boards],
            "total": len(boards),
        }, indent=2)
    except pinterest_api.PinterestAPIError as e:
        return json.dumps({"error": str(e)}, indent=2)


def _post_pin(tool_input: dict, store: DataStore) -> str:
    if not pinterest_api.is_configured():
        return json.dumps({
            "status": "oauth_required",
            "message": "Pinterest not connected. Run 'python tools/pinterest_oauth.py' first.",
            "setup_steps": [
                "1. Go to https://developers.pinterest.com/",
                "2. Create an app → copy App ID and App Secret",
                "3. Add PINTEREST_APP_ID and PINTEREST_APP_SECRET to .env",
                "4. Run: python tools/pinterest_oauth.py",
                "5. Re-run this post command",
            ],
        }, indent=2)

    listing_id = tool_input["listing_id"]
    board_name = tool_input["board_name"]
    image_url = tool_input["image_url"]
    link = tool_input.get("link", "https://www.etsy.com/shop/onbrandcraftz")

    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})

    pin_data = PIN_DESCRIPTIONS.get(listing_id, {})
    title = tool_input.get("custom_title") or pin_data.get("title", listing["title"])
    description = tool_input.get("custom_description") or pin_data.get("description", listing["title"])

    try:
        client = pinterest_api.get_client()
        board_id = client.get_board_id(board_name)
        if not board_id:
            boards = client.get_boards()
            available = [b["name"] for b in boards]
            return json.dumps({
                "error": f"Board '{board_name}' not found.",
                "available_boards": available,
            }, indent=2)

        result = client.create_pin(
            board_id=board_id,
            title=title,
            description=description,
            image_url=image_url,
            link=link,
        )
        return json.dumps({
            "success": True,
            "pin_id": result.get("id"),
            "title": title,
            "board": board_name,
            "link": link,
            "pinterest_url": f"https://www.pinterest.com/pin/{result.get('id', '')}",
        }, indent=2)

    except pinterest_api.PinterestAPIError as e:
        return json.dumps({"error": str(e), "listing_id": listing_id}, indent=2)
