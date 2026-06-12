import json
from datetime import date, timedelta
from tools.data_store import DataStore
from tools import pinterest_api

TOOL_DEFINITIONS = [
    {"name": "get_pinterest_profile", "description": "Get Pinterest profile stats and board overview.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_pin_schedule", "description": "Get recommended Pinterest pinning schedule.",
     "input_schema": {"type": "object", "properties": {"days_ahead": {"type": "integer"}}, "required": []}},
    {"name": "generate_pin_description", "description": "Generate SEO-optimized Pinterest pin description for a listing.",
     "input_schema": {"type": "object", "properties": {"listing_id": {"type": "string"}, "board": {"type": "string"}}, "required": ["listing_id"]}},
    {"name": "get_board_strategy", "description": "Get content strategy for each Pinterest board.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_content_calendar", "description": "Generate a 30-day Pinterest content calendar.",
     "input_schema": {"type": "object", "properties": {"start_date": {"type": "string"}}, "required": []}},
    {"name": "get_growth_recommendations", "description": "Get actionable recommendations to grow Pinterest and drive Etsy traffic.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "update_pinterest_stats", "description": "Update Pinterest metrics from manual check.",
     "input_schema": {"type": "object", "properties": {"followers": {"type": "integer"}, "monthly_views": {"type": "integer"}, "total_pins": {"type": "integer"}}, "required": []}},
    {"name": "get_pinterest_boards", "description": "Fetch all Pinterest boards from the live account.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "post_pin", "description": "Post a pin directly to Pinterest. Requires Pinterest OAuth and an image URL.",
     "input_schema": {"type": "object", "properties": {
         "listing_id": {"type": "string"}, "board_name": {"type": "string"},
         "image_url": {"type": "string"}, "custom_title": {"type": "string"},
         "custom_description": {"type": "string"}, "link": {"type": "string"}},
         "required": ["listing_id", "board_name", "image_url"]}},
]

BOARDS = [
    {"name": "OnBrandCraftz Etsy Shop",         "focus": "All products — main shop showcase board",              "pins": 0},
    {"name": "3D Printed Home Décor",       "focus": "All 3D printed decor items",                          "pins": 1},
    {"name": "Cozy Home Lighting & Lamps",       "focus": "Crystal lamp, mesh lamp, geometric lamp",             "pins": 1},
    {"name": "Coffee Bar Decor & Kitchen Gifts", "focus": "Coffee bar sign, koozies",                            "pins": 1},
    {"name": "Candle Holders & Ambient Living",  "focus": "Tea light candle holder set",                         "pins": 1},
    {"name": "Boho Home Decor & Vases",          "focus": "Ribbed vase, table centerpiece, macrame-style",        "pins": 1},
    {"name": "Housewarming Gift Ideas",          "focus": "All giftable products — lamps, decor, jewelry boxes",  "pins": 0},
    {"name": "Unique Gift Ideas for Home",        "focus": "All products framed as gifts",                        "pins": 0},
    {"name": "Modern Minimalist Living Room",     "focus": "Lamps, vases, centerpieces",                          "pins": 0},
    {"name": "3D Printing & Maker Projects",     "focus": "Behind-the-scenes, process, inspiration",             "pins": 0},
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
    "L001": {"title": "3D Printed Crystal Glow Lamp | Faceted Geometric Night Light",
             "description": "✨ This 3D printed crystal glow lamp is giving total fairy-tale vibes! Faceted geometric design casts the most beautiful light patterns. Made to order in Indiana. \U0001f6cd️ Shop link in bio!\n\n#3DPrintedLamp #CrystalLamp #GlowLamp #GeometricDecor #HomeDecorInspo #ModernHomeDecor #NightLight #3DPrinting #EtsyFinds #UniqueHomeDecor"},
    "L002": {"title": "3D Printed Matte Black Ribbed Vase | Modern Minimalist Home Decor",
             "description": "\U0001f5a4 Obsessed with this matte black ribbed vase! Perfect for dried pampas grass or eucalyptus. Modern minimalist vibes, 3D printed to order. \U0001f33f Shop link in bio!\n\n#RibbedVase #MatteBlack #MinimalistDecor #DryFlowers #PampasGrass #3DPrinted #BohoHome #HomeDecor #EtsyShop #ModernVase"},
    "L003": {"title": "3D Printed Funny Cat Coffee Bar Sign | Ready to Brew Kitchen Decor",
             "description": "☕ This grumpy cat 'Ready to Brew' sign is SO my Monday morning mood \U0001f602 3D printed coffee bar sign that'll make everyone smile. Perfect kitchen gift! ☕ Shop link in bio!\n\n#CoffeeBarDecor #FunnyCatSign #CatLovers #CoffeeBar #KitchenDecor #CatMom #3DPrinted #FunnyGift #EtsyFinds #CoffeeLover"},
    "L004": {"title": "3D Printed Boho Tea Light Candle Holder Set | Cozy Ambient Lighting",
             "description": "\U0001f56f️ Ambient lighting just got an upgrade! These boho 3D printed tea light candle holders create the coziest glow. Perfect for a relaxing evening at home. \U0001f3e1 Shop link in bio!\n\n#CandleHolders #TeaLight #BohoDecor #CandleHolder #AmbientLighting #CozyHome #3DPrinted #HomeDecorIdeas #EtsyShop #BohoHome"},
    "L005": {"title": "3D Printed Mesh Table Lamp with Shade | Geometric Bedside Light",
             "description": "\U0001f31f The most gorgeous lamp on my nightstand! This 3D printed mesh table lamp with shade casts incredible geometric shadow patterns. Total conversation piece. \U0001f4a1 Shop link in bio!\n\n#TableLamp #MeshLamp #GeometricLamp #BedsideLamp #3DPrintedLamp #HomeDecorInspo #ModernLighting #EtsyFinds #NightLight #UniqueHome"},
    "L006": {"title": "3D Printed Boho Table Centerpiece Set | Dining Table Decor",
             "description": "\U0001f33f Boho dining table centrepiece goals! This 3D printed set brings instant warmth and texture to any table. \U0001f3e1 Shop link in bio!\n\n#TableCenterpiece #BohoCenterpiece #DiningDecor #BohoHome #TableDecor #HomeDecorInspo #3DPrinted #EtsyFinds #ModernBoho #CenterpieceIdeas"},
    "L007": {"title": "3D Printed Geometric Table Lamp | Modern Home Decor Lighting",
             "description": "✨ Loving the soft geometric glow this lamp gives my living room! 3D printed with an intricate lattice design. \U0001f4a1 Made to order from Indiana. Shop link in bio!\n\n#GeometricLamp #TableLamp #3DPrintedLamp #ModernDecor #HomeDecorInspo #BedsideLamp #UniqueGifts #EtsyShop #GeometricDecor #NightLight"},
    "L008": {"title": "3D Printed Race Day Can Koozie | Funny Beer Slim Can Cooler",
             "description": "\U0001f3c1 Race day just got cooler! This 3D printed slim can koozie with checkered flag design is the perfect party accessory. \U0001f37a Shop link in bio!\n\n#CanKoozie #RaceDay #BeerKoozie #PartyGifts #3DPrinted #FunnyGifts #SlimCan #RaceFan #EtsyFinds #GiftForHim"},
    "L009": {"title": "Hand Painted Wood Jewelry Box | Decorative Wooden Storage with Drawers",
             "description": "\U0001f49d The most beautiful jewelry box I've ever seen! Hand painted wooden jewelry box with drawers — each one is unique and made with so much love. \U0001f381 Shop link in bio!\n\n#JewelryBox #HandPainted #WoodenJewelryBox #GiftForHer #JewelryStorage #HandmadeGifts #EtsyFinds #UniqueGifts #JewelryOrganizer #BirthdayGift"},
    "L010": {"title": "Hand Painted Boho Wood Jewelry Organizer | Decorative Storage with Drawers",
             "description": "\U0001f48e Organize your jewelry in style! This hand painted boho wooden jewelry organizer has the prettiest floral details. \U0001f338 Shop link in bio!\n\n#JewelryOrganizer #HandPainted #BohoDecor #JewelryStorage #GiftForHer #WoodJewelryBox #HandmadeGifts #EtsyShop #UniqueGifts #JewelryBox"},
}

BEST_TIMES = ["8:00 PM", "9:00 PM", "2:00 PM", "8:00 AM"]
BEST_DAYS  = ["Saturday", "Sunday", "Friday", "Tuesday"]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_pinterest_profile":      return _get_pinterest_profile(store)
    if tool_name == "get_pin_schedule":           return _get_pin_schedule(tool_input.get("days_ahead", 7), store)
    if tool_name == "generate_pin_description":   return _generate_pin_description(tool_input["listing_id"], tool_input.get("board", ""), store)
    if tool_name == "get_board_strategy":         return _get_board_strategy(store)
    if tool_name == "get_content_calendar":       return _get_content_calendar(tool_input.get("start_date", str(date.today())), store)
    if tool_name == "get_growth_recommendations": return _get_growth_recommendations(store)
    if tool_name == "update_pinterest_stats":     return _update_pinterest_stats(tool_input, store)
    if tool_name == "get_pinterest_boards":       return _get_pinterest_boards()
    if tool_name == "post_pin":                   return _post_pin(tool_input, store)
    return f"Unknown social media tool: {tool_name}"


def _get_pinterest_profile(store: DataStore) -> str:
    p = store.get("social_media", "pinterest") or {}
    return json.dumps({
        "platform": "Pinterest", "username": "printing3dthings", "display_name": "OnBrandCraftz",
        "url": "https://www.pinterest.com/printing3dthings",
        "followers": p.get("followers", 2), "following": p.get("following", 0),
        "monthly_views": p.get("monthly_views", 0), "total_pins": p.get("total_pins", 4),
        "boards": len(BOARDS), "board_list": [{"name": b["name"], "pins": b["pins"], "focus": b["focus"]} for b in BOARDS],
        "etsy_link_in_bio": True,
        "assessment": "Account is freshly set up with great board structure. 10 boards created but only 4 pins total. Huge growth opportunity.",
    }, indent=2)


def _get_pin_schedule(days_ahead: int, store: DataStore) -> str:
    listings = store.listings
    start = date.today()
    schedule = []
    for i in range(days_ahead):
        day = start + timedelta(days=i)
        listing = listings[i % len(listings)]
        lid = listing["id"]
        boards = LISTING_BOARD_MAP.get(lid, ["OnBrandCraftz Etsy Shop"])
        board = boards[i % len(boards)]
        pin_data = PIN_DESCRIPTIONS.get(lid, {})
        schedule.append({"date": str(day), "day_of_week": day.strftime("%A"),
                          "time": BEST_TIMES[i % len(BEST_TIMES)], "listing_id": lid,
                          "product": listing["title"][:60], "board": board,
                          "pin_title": pin_data.get("title", listing["title"][:60]),
                          "etsy_url": "https://www.etsy.com/shop/onbrandcraftz"})
    return json.dumps({"pin_schedule": schedule,
                       "tip": "Best times: 8-9 PM and 2 PM. Best days: Saturday, Sunday, Friday.",
                       "goal": f"Pin {days_ahead} times over {days_ahead} days."}, indent=2)


def _generate_pin_description(listing_id: str, board: str, store: DataStore) -> str:
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})
    pin_data = PIN_DESCRIPTIONS.get(listing_id, {})
    suggested_boards = LISTING_BOARD_MAP.get(listing_id, ["OnBrandCraftz Etsy Shop"])
    return json.dumps({
        "listing_id": listing_id, "product": listing["title"], "price": listing["price"],
        "pin_title": pin_data.get("title", listing["title"]),
        "pin_description": pin_data.get("description", f"Shop this beautiful handmade item at OnBrandCraftz on Etsy! #EtsyShop #HandmadeDecor"),
        "destination_url": "https://www.etsy.com/shop/onbrandcraftz",
        "target_board": board or suggested_boards[0], "all_suitable_boards": suggested_boards,
    }, indent=2)


def _get_board_strategy(store: DataStore) -> str:
    strategies = []
    for board in BOARDS:
        relevant = [lid for lid, boards in LISTING_BOARD_MAP.items() if board["name"] in boards]
        strategies.append({"board": board["name"], "current_pins": board["pins"], "focus": board["focus"],
                            "your_listings_to_pin": relevant, "target_pins_per_week": 3,
                            "tip": "Pin your products + 2-3 lifestyle repins per week."})
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
        if i % 7 == 6:
            calendar.append({"date": str(day), "day": day.strftime("%A"), "type": "lifestyle_repin",
                              "action": "Repin 2-3 inspiring home decor or 3D printing posts from other creators",
                              "boards": ["3D Printing & Maker Projects", "Modern Minimalist Living Room"], "time": "8:00 PM"})
        else:
            calendar.append({"date": str(day), "day": day.strftime("%A"), "type": "product_pin",
                              "listing_id": lid, "product": listing["title"][:55], "board": board,
                              "pin_title": pin_data.get("title", "")[:60],
                              "time": BEST_TIMES[i % len(BEST_TIMES)],
                              "etsy_url": "https://www.etsy.com/shop/onbrandcraftz"})
    product_pins = len([c for c in calendar if c["type"] == "product_pin"])
    return json.dumps({"calendar": calendar, "period": f"{start} to {start + timedelta(days=29)}",
                       "total_pins": product_pins, "tip": "Use Pinterest's built-in scheduler. Do a week at a time on Sundays."}, indent=2)


def _get_growth_recommendations(store: DataStore) -> str:
    recommendations = [
        {"priority": 1, "action": "Pin ALL 10 listings immediately",
         "detail": "You have 10 products and only 4 pins. Pin every product to at least 2-3 relevant boards TODAY.", "time_required": "30 minutes"},
        {"priority": 2, "action": "Add your Etsy shop link to every pin",
         "detail": "Every pin should link directly to your Etsy shop. Pinterest is a massive traffic driver to Etsy.", "time_required": "Ongoing"},
        {"priority": 3, "action": "Pin consistently — 1 pin per day minimum",
         "detail": "Pinterest rewards consistency. Daily pinning grows monthly views faster than sporadic batches.", "time_required": "5-10 min/day"},
        {"priority": 4, "action": "Add keywords to board descriptions",
         "detail": "Add descriptions to each board with keywords: '3D printed', 'handmade', 'modern home decor', 'Etsy'.", "time_required": "20 minutes"},
        {"priority": 5, "action": "Use vertical images (2:3 ratio, 1000x1500px)",
         "detail": "Vertical pins get more clicks. Create Pinterest-optimized versions with lifestyle backgrounds.", "time_required": "Per product"},
    ]
    return json.dumps({"current_status": {"followers": 2, "total_pins": 4, "boards": 10},
                       "growth_recommendations": recommendations,
                       "30_day_goal": "Reach 50+ monthly views and 25+ pins",
                       "90_day_goal": "Reach 500+ monthly views, 100+ followers, consistent Etsy traffic"}, indent=2)


def _update_pinterest_stats(data: dict, store: DataStore) -> str:
    pinterest = store.get("social_media", "pinterest") or {}
    if "followers"     in data: pinterest["followers"]     = data["followers"]
    if "monthly_views" in data: pinterest["monthly_views"] = data["monthly_views"]
    if "total_pins"    in data: pinterest["total_pins"]    = data["total_pins"]
    pinterest["last_updated"] = str(date.today())
    social = store.get("social_media") or {}
    social["pinterest"] = pinterest
    store.set(social, "social_media")
    store.save()
    return json.dumps({"success": True, "pinterest": pinterest}, indent=2)


def _get_pinterest_boards() -> str:
    if not pinterest_api.is_configured():
        return json.dumps({"status": "oauth_required",
                           "message": "Pinterest not connected. Run 'python tools/pinterest_oauth.py' to enable direct posting.",
                           "your_boards": [b["name"] for b in BOARDS]}, indent=2)
    try:
        client = pinterest_api.get_client()
        boards = client.get_boards()
        return json.dumps({"boards": [{"id": b["id"], "name": b["name"], "pin_count": b.get("pin_count", 0)} for b in boards], "total": len(boards)}, indent=2)
    except pinterest_api.PinterestAPIError as e:
        return json.dumps({"error": str(e)}, indent=2)


def _post_pin(tool_input: dict, store: DataStore) -> str:
    if not pinterest_api.is_configured():
        return json.dumps({"status": "oauth_required",
                           "message": "Pinterest not connected. Run 'python tools/pinterest_oauth.py' first.",
                           "setup_steps": ["1. Go to https://developers.pinterest.com/", "2. Create app, copy App ID + App Secret",
                                           "3. Add to .env: PINTEREST_APP_ID and PINTEREST_APP_SECRET",
                                           "4. Run: python tools/pinterest_oauth.py"]}, indent=2)
    listing_id = tool_input["listing_id"]
    board_name = tool_input["board_name"]
    image_url  = tool_input["image_url"]
    link = tool_input.get("link", "https://www.etsy.com/shop/onbrandcraftz")
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})
    pin_data    = PIN_DESCRIPTIONS.get(listing_id, {})
    title       = tool_input.get("custom_title")       or pin_data.get("title", listing["title"])
    description = tool_input.get("custom_description") or pin_data.get("description", listing["title"])
    try:
        client   = pinterest_api.get_client()
        board_id = client.get_board_id(board_name)
        if not board_id:
            boards = client.get_boards()
            return json.dumps({"error": f"Board '{board_name}' not found.", "available_boards": [b["name"] for b in boards]}, indent=2)
        result = client.create_pin(board_id=board_id, title=title, description=description, image_url=image_url, link=link)
        return json.dumps({"success": True, "pin_id": result.get("id"), "title": title, "board": board_name, "link": link,
                           "pinterest_url": f"https://www.pinterest.com/pin/{result.get('id', '')}"}, indent=2)
    except pinterest_api.PinterestAPIError as e:
        return json.dumps({"error": str(e), "listing_id": listing_id}, indent=2)
