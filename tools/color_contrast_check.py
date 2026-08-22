#!/usr/bin/env python3
"""
color_contrast_check.py — WCAG 2.x contrast-ratio audit for OnBrandCraftz's
documented theme palettes (2026-07-15 ADA/WCAG audit).

CLAUDE.md's Color Design Rules state "Minimum contrast ratio 4.5:1 — text on
background (WCAG AA accessibility standard)" but nothing has ever actually
computed it — data/knowledge_base/design_quality_research_2026-06.md already
flags a planned neon palette as a likely failure, based on a hunch, not a
number. This script is the missing check: pure WCAG relative-luminance math,
no dependencies, no live API calls, validated against every theme CLAUDE.md
documents a Text hex for.

Two theme groups exist in CLAUDE.md, with different levels of documentation:
  - The 12 new theme catalog entries (Cherry Blossom, Sage Garden, ...) each
    give an explicit Text hex, so those are checked directly here.
  - The 4 LIVE shipped product themes (DP1026-1029, "Current Product Color
    Schemes" table) do NOT give an explicit Text hex in that table -- only
    Primary/Accent/Neutral. That's a real documentation gap in its own
    right (flagged in the report below), not something this script should
    guess a value for.

Usage:
    python tools/color_contrast_check.py

Exit codes:
    0  every documented Text/Neutral pair passes WCAG AA (4.5:1)
    1  one or more pairs fail
"""
from __future__ import annotations

import sys

AA_NORMAL_TEXT = 4.5
AA_LARGE_TEXT = 3.0

# Text hex only documented for these 12 (CLAUDE.md's "New Theme Catalog").
# name: (text_hex, neutral_hex, primary_hex)
THEMES_WITH_TEXT_HEX = {
    "Cherry Blossom":     ("#3D1A24", "#FFF5F7", "#F4A7B9"),
    "Sage Garden":        ("#2C3828", "#F6F8F2", "#8BA888"),
    "Celestial Night":    ("#F9F6FF", "#1E1B4B", "#1E1B4B"),  # dark-bg theme: text-on-dark documented instead
    "Mocha Latte":        ("#2C1A0E", "#FDF8F0", "#8B5E3C"),
    "Mermaidcore":        ("#1A3A4A", "#F0FAFF", "#4ABFBF"),
    "Dark Academia":      ("#1C1208", "#F5EDD6", "#3B2A1A"),
    "Tropical Hibiscus":  ("#3D0029", "#FFFAF0", "#FF6B9D"),
    "Rose Gold Luxe":     ("#4A2030", "#FDF8F8", "#B76E79"),
    "Ocean Breeze":       ("#0D3535", "#F0FAFA", "#3B8E8A"),
    "Midnight Kawaii":    ("#F0E6FF", "#1A1A2E", "#1A1A2E"),  # dark-bg theme: text-on-dark documented instead
    "Sunflower Studio":   ("#2A1A00", "#FFFDF0", "#F4C430"),
    "Matcha Serenity":    ("#1E2D18", "#F7F9F3", "#6B8F5E"),
}

# The 4 LIVE shipped themes only document Primary/Accent/Neutral -- no Text
# hex anywhere in CLAUDE.md's "Current Product Color Schemes" table. Listed
# here so the report explicitly names the gap instead of silently skipping.
LIVE_THEMES_MISSING_TEXT_HEX = {
    "DP1026 Lavender Dreams": {"primary": "#8666AA", "accent": "#C4A8D4", "neutral": "#FAF7FF"},
    "DP1027 Cotton Candy":    {"primary": "#DE97C6", "accent": "#97C6DE", "neutral": "#FFF6FC"},
    "DP1028 Midnight Blue":   {"primary": "#1B2568", "accent": "#7BA7C2", "neutral": "#F0F5FF"},
    "DP1029 Coral Peach":     {"primary": "#FD6C49", "accent": "#F5B878", "neutral": "#FFF8F4"},
}


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    r, g, b = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """WCAG 2.x contrast ratio between two hex colors, always >= 1.0."""
    l1 = relative_luminance(hex_a)
    l2 = relative_luminance(hex_b)
    lighter, darker = max(l1, l2), min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def meets_wcag_aa(hex_a: str, hex_b: str, large_text: bool = False) -> bool:
    threshold = AA_LARGE_TEXT if large_text else AA_NORMAL_TEXT
    return contrast_ratio(hex_a, hex_b) >= threshold


def audit() -> tuple[list[dict], list[str]]:
    """Returns (results, gap_notes). Each result:
    {name, text_hex, bg_hex, ratio, passes}."""
    results = []
    for name, (text_hex, bg_hex, _primary_hex) in THEMES_WITH_TEXT_HEX.items():
        ratio = contrast_ratio(text_hex, bg_hex)
        results.append({
            "name": name, "text_hex": text_hex, "bg_hex": bg_hex,
            "ratio": ratio, "passes": ratio >= AA_NORMAL_TEXT,
        })
    gap_notes = [
        f"{name}: no Text hex documented in CLAUDE.md (only primary={c['primary']}, "
        f"accent={c['accent']}, neutral={c['neutral']}) -- cannot verify contrast until "
        f"a text color is documented"
        for name, c in LIVE_THEMES_MISSING_TEXT_HEX.items()
    ]
    return results, gap_notes


def main() -> int:
    results, gap_notes = audit()
    print("WCAG AA CONTRAST AUDIT — CLAUDE.md documented theme palettes")
    print("=" * 64)
    failures = [r for r in results if not r["passes"]]
    for r in results:
        status = "PASS" if r["passes"] else "FAIL"
        print(f"  [{status}] {r['name']:20s} text {r['text_hex']} on {r['bg_hex']}  "
              f"ratio={r['ratio']}:1 (need >= {AA_NORMAL_TEXT}:1)")
    print()
    if gap_notes:
        print(f"DOCUMENTATION GAP — {len(gap_notes)} live theme(s) have no Text hex to check:")
        for note in gap_notes:
            print(f"  - {note}")
        print()
    print(f"{len(results) - len(failures)}/{len(results)} documented themes pass WCAG AA "
          f"(4.5:1); {len(gap_notes)} live theme(s) undocumented and unchecked.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
