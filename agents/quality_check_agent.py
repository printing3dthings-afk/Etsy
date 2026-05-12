import base64
import os

from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import quality_check_tools

SYSTEM_PROMPT = """You are the Quality Check Agent for OnBrandCraftz. You are the gatekeeper between digital product creation and listing on Etsy. Nothing goes live without your approval.

Your responsibilities:
- Review all digital products that reach 'qc_pending' status
- Run automated spec checks (resolution, DPI, file size, format)
- Visually assess image quality, color accuracy, and commercial appeal
- Ensure products meet Etsy's digital file requirements
- Approve products that are ready to sell, or reject with clear fix instructions

Quality standards to enforce:
- Images: minimum 3000px on shortest side, 300 DPI for print quality
- File size: under 20 MB (Etsy limit)
- Formats: PNG, JPEG, PDF, ZIP only
- Color: RGB or CMYK (no indexed/palette modes for art)
- Visual quality: no blurry edges, no obvious AI artifacts, no watermarks, clean composition
- PDF planners: all pages present, text legible, consistent formatting

When reviewing:
1. Always run check_file_specs first for automated checks
2. Then assess visual/content quality based on the concept and product type
3. Approve products that meet all standards, with encouraging notes
4. Reject products with specific, actionable feedback so the Art Creation Agent can fix them
5. Use flag_for_revision for minor issues that don't require full rejection

Common rejection reasons:
- "Resolution too low for print quality" → ask to regenerate at higher resolution
- "File size exceeds 20 MB Etsy limit" → ask to compress or split into ZIP
- "Image contains AI artifacts or watermarks" → ask to regenerate
- "Color mode is palette/indexed" → ask to convert to RGB
- "Planner missing sections" → specify which sections are missing

Be thorough but fair. The goal is to maintain high quality standards while keeping the pipeline moving."""


class QualityCheckAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Quality Check Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=quality_check_tools.TOOL_DEFINITIONS,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return quality_check_tools.execute_tool(tool_name, tool_input, self._store)

    def visual_review(self, product_id: str) -> str:
        """Use Claude vision to visually inspect a digital product image."""
        products = self._store.get("digital_products", default=[])
        product = next((p for p in products if p["id"] == product_id), None)
        if not product:
            return f"Product {product_id} not found"

        file_path = product.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return "No file found for visual review"

        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if ext not in ("png", "jpg", "jpeg"):
            return f"Visual review skipped (not an image file: .{ext})"

        with open(file_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        media_type = "image/png" if ext == "png" else "image/jpeg"

        response = self.client.messages.create(
            model=self._get_model(),
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": (
                        f"You are a quality control reviewer for an Etsy digital art shop. "
                        f"This is product '{product.get('title', product_id)}' (type: {product.get('product_type', 'unknown')}).\n\n"
                        "Evaluate this image on:\n"
                        "1. Overall visual quality (sharpness, composition, color balance)\n"
                        "2. Commercial appeal — would this sell well as an Etsy digital download?\n"
                        "3. Print readiness — any issues that would look bad when printed?\n"
                        "4. Any AI artifacts, watermarks, or distracting elements?\n"
                        "5. Does it match what the title/type implies?\n\n"
                        "Give a pass/fail recommendation with specific notes."
                    )},
                ],
            }],
        )
        return response.content[0].text if response.content else "No visual review returned"

    def _get_model(self) -> str:
        from config import MODEL
        return MODEL
