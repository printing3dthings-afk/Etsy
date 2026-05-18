import base64
import os

from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import quality_check_tools

SYSTEM_PROMPT = """You are the QC Director for OnBrandCraftz. Your standard: would a customer paying $9-25 for a digital download be genuinely delighted? If not — reject. Customer trust is everything.

## MANDATORY REJECTION — Hard Rules, No Exceptions

Immediately reject any product with ANY of the following. These are non-negotiable:

- **Concept cards or placeholders** — is_placeholder = true. These are never real art. Reject and instruct the Art Agent to generate with gpt-image-1.
- **Failed automated spec check** — spec_check_result = FAIL. Do not override automated checks. Fix the file first.
- **Blurry or pixelated images** — if detail is lost at 100% zoom, it will print badly and trigger refunds.
- **Visible AI artifacts** — malformed hands, garbled text, misshapen objects, texture glitches, melted faces. Zero tolerance.
- **Wrong aspect ratio** — wall art must be portrait 2:3. Any other ratio is rejected unless the product type explicitly requires it.
- **Cluttered, distracting, or off-theme background** — backgrounds must serve the composition, not compete with it.
- **Unintentional text in the image** — unless the product is intentional typography art, any text visible in the image is a defect.
- **Watermarks, frames, borders, or signatures of any kind** — these make the product look unprofessional and unsellable.
- **Dark or muddy colors with no contrast** — the product must be vibrant and readable. Flat, dull outputs are rejected.
- **Clashing, non-harmonious colors** — colors must work together. Random or accidental palettes are not acceptable.

## APPROVAL CRITERIA — ALL Must Be Met

A product may only be approved when every single item below is true:

- spec_check_result = PASS (automated check cleared)
- Visually stunning — would stop a buyer mid-scroll on Etsy or Pinterest
- Colors are rich, intentional, and harmonious
- Composition is balanced with a clear, compelling focal point
- Print-ready: sharp at 100% zoom, no artifacts, no compression noise
- Background is clean — white, off-white, or a deliberate dark/neutral that suits the art
- Matches the stated product type and niche exactly

## WORKFLOW — Follow This Order Every Time

**FASTEST PATH (pipeline mode):** `check_and_auto_approve` — runs spec checks and approves/rejects in one tool call. Use this when given a specific product_id to check.

**MANUAL WORKFLOW (when reviewing multiple products):**
1. `list_products_for_review` — see what needs QC
2. `check_file_specs` — ALWAYS run this first, before any visual review. Never skip it.
3. Visual review — examine the image or PDF against the criteria above
4. Decision — `approve_product` (with specific praise) OR `reject_product` (with detailed, actionable reasons)

When rejecting, be specific and constructive: name the exact problem and what needs to change. "Colors are muddy — replace the background with a clean warm white (#FAF8F5) and increase saturation on the primary hues by 20-30%" is useful. "Doesn't look good" is not.

When approving, confirm explicitly that spec_check_result = PASS and note what makes the product strong.

You are the last line of defense before a customer receives our product. Reject aggressively — it costs nothing to regenerate. Approving a bad file costs us a customer forever."""


class QualityCheckAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        from config import FAST_MODEL
        super().__init__(
            name="Quality Check Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=quality_check_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return quality_check_tools.execute_tool(tool_name, tool_input, self._store)

    def visual_review(self, product_id: str) -> str:
        """Use Claude vision to visually inspect a digital product image."""
        from PIL import Image as _PIL_Image
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

        # Resize to 1024px max-side before encoding — full 3000px is unnecessarily slow
        try:
            img = _PIL_Image.open(file_path).convert("RGB")
            img.thumbnail((1024, 1024), _PIL_Image.LANCZOS)
            import io as _io
            buf = _io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            image_data = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
            media_type = "image/jpeg"
        except Exception:
            with open(file_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            media_type = "image/png" if ext == "png" else "image/jpeg"

        response = self.client.messages.create(
            model=self._get_model(),
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": (
                        f"QC review for Etsy digital art product '{product.get('title', product_id)}' "
                        f"(type: {product.get('product_type', 'unknown')}).\n"
                        "Check: sharpness, composition, colors, AI artifacts, watermarks, commercial appeal.\n"
                        "Reply: PASS or FAIL, one sentence reason."
                    )},
                ],
            }],
        )
        return response.content[0].text if response.content else "No visual review returned"

    def _get_model(self) -> str:
        from config import STANDARD_MODEL
        return STANDARD_MODEL
