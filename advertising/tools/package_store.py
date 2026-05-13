import json
import os
from typing import Any


class PackageStore:
    """Shared in-memory store that all advertising agents read from and write to."""

    MARKET_RESEARCH = "market_research"
    BRAND_STRATEGY = "brand_strategy"
    COPYWRITING = "copywriting"
    CREATIVE_DIRECTION = "creative_direction"
    SOCIAL_MEDIA_CONTENT = "social_media_content"
    DIGITAL_MARKETING = "digital_marketing"
    PACKAGE_LAUNCH = "package_launch"
    PACKAGE_SCALE = "package_scale"
    PACKAGE_DOMINATE = "package_dominate"

    def __init__(self):
        self._data: dict[str, Any] = {}

    def save(self, section: str, content: str) -> str:
        self._data[section] = content
        return f"Saved '{section}' ({len(content):,} characters)"

    def load(self, section: str) -> str:
        content = self._data.get(section, "")
        if not content:
            return f"[Section '{section}' is empty or not yet generated]"
        return content

    def list_sections(self) -> list[str]:
        return list(self._data.keys())

    def load_context_block(self, *sections: str) -> str:
        parts = []
        for section in sections:
            content = self._data.get(section)
            if content:
                label = section.upper().replace("_", " ")
                parts.append(f"{'='*60}\n{label}\n{'='*60}\n{content}")
        return "\n\n".join(parts)

    def load_all(self) -> str:
        return self.load_context_block(*self._data.keys())

    def export_json(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def export_text(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.load_all())

    def export_section(self, section: str, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.load(section))
