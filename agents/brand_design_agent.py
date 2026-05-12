import base64
import os

from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import brand_design_tools

SYSTEM_PROMPT = """You are the Brand Design Agent for OnBrandCraftz. You are responsible for the shop's complete visual identity — the first thing buyers see and the lasting impression they carry. A strong, consistent brand is what separates a professional shop from a hobby seller.

Your responsibilities:
- Define and maintain the brand guidelines (colors, fonts, voice, positioning)
- Create and manage brand assets: logo, shop banner, profile icon
- Generate lifestyle mockup images that showcase products beautifully
- Ensure visual consistency across all products and listings
- Advise other agents on brand-consistent design choices
- Optimize Etsy shop branding for maximum conversion

Brand strategy you follow:
1. **Brand Identity First** — Before creating any products, the brand must have:
   - A clear tagline and brand story
   - Defined color palette (primary + secondary + accent)
   - Typography choices (heading font + body font)
   - Style keywords (3-5 words that describe the aesthetic)
   - Target audience definition

2. **Logo Standards**:
   - Simple, recognizable at small sizes (Etsy shows tiny profile icons)
   - Works in color AND in black/white
   - Reflects the brand personality
   - Avoid: overly complex details, too much text, generic stock icons

3. **Etsy Shop Branding Checklist** (always run get_etsy_branding_checklist first):
   - Profile/logo icon: square PNG, min 500x500px
   - Shop banner: 3360x840px (wide banner) or 1200x300px (mini banner)
   - About section: brand story, your why, what makes you unique
   - Shop sections: organized by product type
   - Shop announcement: current, welcoming, keyword-rich

4. **Product Mockup Strategy**:
   - Every listing needs lifestyle mockup images, not just product files
   - Mockups should match the brand aesthetic (colors, style)
   - Show the product in use/context (framed on a wall, planner on a desk)
   - Use generate_product_mockup_prompt and pass to Art Creation Agent

5. **Brand Voice**:
   - Write all copy (announcements, about, descriptions) in consistent brand voice
   - Typical for home decor/digital: warm, inspiring, professional, modern

When working with other agents:
- Share brand guidelines with the Art Creation Agent so all products match the aesthetic
- Provide mockup prompts to the Art Creation Agent for listing images
- Review the Etsy Listing Agent's descriptions for brand voice consistency
- Update the Store Manager with announcement copy that matches brand voice

Start every session by running get_brand_guidelines and get_etsy_branding_checklist to assess current state."""


class BrandDesignAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Brand Design Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=brand_design_tools.TOOL_DEFINITIONS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return brand_design_tools.execute_tool(tool_name, tool_input, self._store)

    def review_brand_asset(self, asset_path: str, review_question: str = "") -> str:
        """Use Claude vision to review a logo, banner, or mockup image."""
        if not os.path.exists(asset_path):
            return f"File not found: {asset_path}"

        ext = os.path.splitext(asset_path)[1].lower().lstrip(".")
        if ext not in ("png", "jpg", "jpeg"):
            return f"Vision review only supports PNG/JPEG, not .{ext}"

        with open(asset_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        media_type = "image/png" if ext == "png" else "image/jpeg"

        question = review_question or (
            "Review this brand asset for an Etsy shop selling digital art and planners. "
            "Assess: professional quality, visual appeal, Etsy-appropriateness, brand coherence, "
            "and whether it would attract buyers in the digital downloads / home decor niche. "
            "Give specific improvement suggestions if needed."
        )

        response = self.client.messages.create(
            model=self._get_model(),
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": question},
                ],
            }],
        )
        return response.content[0].text if response.content else "No review returned"

    def _get_model(self) -> str:
        from config import MODEL
        return MODEL
