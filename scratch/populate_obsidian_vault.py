import os
import shutil

VAULT_DIR = "/home/sjack7/Desktop/Onbrandcraftz"
REPO_DIR = "/home/sjack7/Desktop/frank-source/Etsy-claude-etsy-automation-agents-WFAPU"

MAPPINGS = [
    # 01 - Products
    (os.path.join(REPO_DIR, "data/svg_pack/etsy_listing.md"), os.path.join(VAULT_DIR, "01 - Products/SVG Pack Listing Draft.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/price_tests.md"), os.path.join(VAULT_DIR, "01 - Products/Listing Pricing & A-B Tests.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/design_quality_research_2026-06.md"), os.path.join(VAULT_DIR, "01 - Products/Design Quality Research.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/sublimation_standards.md"), os.path.join(VAULT_DIR, "01 - Products/Sublimation & Printing Standards.md")),

    # 02 - Operations
    (os.path.join(REPO_DIR, "data/financial/profit_loss.md"), os.path.join(VAULT_DIR, "02 - Operations/Profit & Loss Financial Tracker.md")),
    (os.path.join(REPO_DIR, "data/printify/printify_setup_guide.md"), os.path.join(VAULT_DIR, "02 - Operations/Printify Setup Guide.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/ops_runbook.md"), os.path.join(VAULT_DIR, "02 - Operations/Ops Runbook.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/action_plan_2026.md"), os.path.join(VAULT_DIR, "02 - Operations/Action Plan 2026.md")),
    (os.path.join(REPO_DIR, "data/todo.md"), os.path.join(VAULT_DIR, "02 - Operations/Shop Master Todo List.md")),

    # 03 - Knowledge
    (os.path.join(REPO_DIR, "data/knowledge_base/ceo_operating_playbook.md"), os.path.join(VAULT_DIR, "03 - Knowledge/CEO Operating Playbook.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/business_standards.md"), os.path.join(VAULT_DIR, "03 - Knowledge/Business Standards.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/competitor_research_2026.md"), os.path.join(VAULT_DIR, "03 - Knowledge/Competitor Research 2026.md")),
    (os.path.join(REPO_DIR, "data/marketing_copy.md"), os.path.join(VAULT_DIR, "03 - Knowledge/Marketing Copy Vault.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/lifestyle_photo_mastery.md"), os.path.join(VAULT_DIR, "03 - Knowledge/Lifestyle Photo Mastery.md")),
    (os.path.join(REPO_DIR, "data/knowledge_base/compliance_notes.md"), os.path.join(VAULT_DIR, "03 - Knowledge/Etsy Compliance Notes.md")),
    (os.path.join(REPO_DIR, "BEST_PRACTICES.md"), os.path.join(VAULT_DIR, "03 - Knowledge/Etsy Automation Best Practices.md")),
]

copied_count = 0
for src, dst in MAPPINGS:
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"✓ Copied: {os.path.basename(dst)}")
        copied_count += 1
    else:
        print(f"⚠️ Source missing: {src}")

print(f"\nSuccessfully populated {copied_count} knowledge, operational, product, and financial notes into Obsidian!")
