import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ETSY_API_KEY = os.getenv("ETSY_API_KEY", "")
ETSY_SHOP_ID = os.getenv("ETSY_SHOP_ID", "")

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500
MAX_ITERATIONS = 12

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SHOP_DATA_FILE = os.path.join(DATA_DIR, "shop_data.json")
DIGITAL_PRODUCTS_DIR = os.path.join(DATA_DIR, "digital_products")
BRAND_DIR = os.path.join(DATA_DIR, "brand")
