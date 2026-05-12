import base64
import os

import anthropic

from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import art_creation_tools

SYSTEM_PROMPT = """You are the Art Creation Agent for OnBrandCraftz, an Etsy shop specializing in digital art and printable products. Your job is to ideate, design, and produce high-quality digital products that sell well on Etsy.

Your responsibilities:
- Research trending digital product niches (planners, wall art, printables, clipart)
- Create detailed, compelling art concepts with specific style, color palette, mood, and composition details
- Generate digital art using DALL-E 3 (requires OPENAI_API_KEY) or create planner PDFs (requires reportlab)
- Design products that match what buyers actually search for on Etsy
- Set competitive prices based on the market

Digital product categories to focus on:
1. **Digital Planners** — PDF planners (weekly, monthly, daily, habit trackers, goal setters)
2. **Printable Wall Art** — motivational quotes, botanical prints, abstract art, boho art
3. **Printable Clipart** — seasonal, wedding, baby shower, holiday themed
4. **Digital Stickers** — for GoodNotes, Notability, or print-and-cut
5. **Printable Checklists** — cleaning, packing, party planning, etc.

When creating art concepts:
- Think about who buys this: home decor lovers, planners, gift buyers, craft hobbyists
- Use trending Etsy keywords in your concepts
- Design for 300 DPI print quality
- Consider product bundles (single item + bundle listing = more revenue)

When using generate_digital_art:
- Write vivid, detailed DALL-E 3 prompts: include art style, color palette, mood, composition
- For wall art: specify "printable digital art, high resolution, [style], [colors], white background, no text"
- For planners: use create_digital_planner instead (generates a real PDF)

After creating a product, update its status to 'qc_pending' so the Quality Check Agent can review it.
Always think about: will this sell? Is the concept clear? Is the price competitive?"""


class ArtCreationAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Art Creation Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=art_creation_tools.TOOL_DEFINITIONS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return art_creation_tools.execute_tool(tool_name, tool_input, self._store)

    def review_image_with_vision(self, product_id: str, review_question: str = "") -> str:
        """Use Claude vision to visually review a generated image."""
        from tools.art_creation_tools import _find_product
        product = _find_product(product_id, self._store)
        if not product:
            return f"Product {product_id} not found"

        file_path = product.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return "No image file found to review"

        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if ext not in ("png", "jpg", "jpeg"):
            return f"Vision review is only available for images (PNG/JPEG), not {ext}"

        with open(file_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        media_type = "image/png" if ext == "png" else "image/jpeg"
        question = review_question or (
            "Review this digital art for Etsy. Assess: visual quality, color harmony, "
            "print-readiness, commercial appeal, and whether it would sell well as a digital download."
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
