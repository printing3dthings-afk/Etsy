"""Business identity config — de-hardcodes the shop name/owner/agent name so this
codebase can be deployed as a fresh, independent instance for a different business.

Every default below matches OnBrandCraftz's current literal values, so an instance
with no new env vars set renders byte-identical output to before this module existed.
"""

import os

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "OnBrandCraftz")
OWNER_NAME = os.getenv("OWNER_NAME", "Scott")
AGENT_NAME = os.getenv("AGENT_NAME", "Fucking Frank")
# Shorter form used in user-facing error toasts where the full AGENT_NAME reads
# oddly (e.g. "Fucking Frank's AI provider..."). Defaults to AGENT_NAME with any
# "Fucking " prefix stripped, which reproduces today's literal "Frank" for
# OnBrandCraftz and falls back to the full AGENT_NAME for any other instance.
AGENT_NAME_SHORT = os.getenv("AGENT_NAME_SHORT", AGENT_NAME.replace("Fucking ", ""))
BUSINESS_DESCRIPTION = os.getenv(
    "BUSINESS_DESCRIPTION",
    "an Etsy shop selling kawaii\ndigital planners, sticker packs, and 3D-print SVG files",
)
