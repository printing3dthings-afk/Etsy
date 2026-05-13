from dataclasses import dataclass
from typing import Optional


@dataclass
class CompanyBrief:
    name: str
    industry: str
    products_services: str
    target_audience: str
    tone: str
    primary_goals: str
    competitors: str = ""
    budget_range: str = "medium ($1k–$10k/mo)"
    website: Optional[str] = None
    existing_tagline: Optional[str] = None
    additional_notes: Optional[str] = None

    def to_prompt_string(self) -> str:
        lines = [
            f"COMPANY NAME: {self.name}",
            f"INDUSTRY: {self.industry}",
            f"PRODUCTS/SERVICES: {self.products_services}",
            f"TARGET AUDIENCE: {self.target_audience}",
            f"BRAND TONE: {self.tone}",
            f"PRIMARY ADVERTISING GOALS: {self.primary_goals}",
            f"ADVERTISING BUDGET: {self.budget_range}",
        ]
        if self.competitors:
            lines.append(f"KNOWN COMPETITORS: {self.competitors}")
        if self.website:
            lines.append(f"WEBSITE: {self.website}")
        if self.existing_tagline:
            lines.append(f"EXISTING TAGLINE: {self.existing_tagline}")
        if self.additional_notes:
            lines.append(f"ADDITIONAL NOTES: {self.additional_notes}")
        return "\n".join(lines)
