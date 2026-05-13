from advertising.tools.package_store import PackageStore

COMMON_TOOL_DEFINITIONS = [
    {
        "name": "save_content",
        "description": (
            "Save your generated content to the shared advertising package store. "
            "Always call this after completing your work so other agents can build on it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": (
                        "Section name, e.g. 'market_research', 'brand_strategy', "
                        "'copywriting', 'creative_direction', 'social_media_content', "
                        "'digital_marketing'. Use sub-sections for specifics: "
                        "'copywriting_headlines', 'social_instagram', etc."
                    ),
                },
                "content": {
                    "type": "string",
                    "description": "The complete, formatted content to store.",
                },
            },
            "required": ["section", "content"],
        },
    },
    {
        "name": "load_content",
        "description": "Load previously generated content from the package store by section name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Section name to load.",
                }
            },
            "required": ["section"],
        },
    },
    {
        "name": "list_store_contents",
        "description": "List all section names currently saved in the package store.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

QC_TOOL_DEFINITIONS = COMMON_TOOL_DEFINITIONS + [
    {
        "name": "save_qc_report",
        "description": "Save a structured quality control report for a reviewed content section.",
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "The section that was reviewed.",
                },
                "score": {
                    "type": "integer",
                    "description": "Quality score 1–10 (10 = flawless).",
                },
                "issues": {
                    "type": "string",
                    "description": "Specific issues found: grammar, clarity, brand consistency, missing elements, etc.",
                },
                "improvements": {
                    "type": "string",
                    "description": "Concrete, actionable improvement suggestions.",
                },
                "approved": {
                    "type": "boolean",
                    "description": "True if content meets standards (score >= 7). False requires revision.",
                },
            },
            "required": ["section", "score", "issues", "improvements", "approved"],
        },
    },
]

CEO_EXTRA_TOOLS = [
    {
        "name": "load_all_content",
        "description": "Load the entire package store as one formatted document for final assembly.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_package",
        "description": "Save a fully assembled advertising package tier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {
                    "type": "string",
                    "enum": ["launch", "scale", "dominate"],
                    "description": "Package tier: 'launch' (starter), 'scale' (professional), 'dominate' (enterprise).",
                },
                "content": {
                    "type": "string",
                    "description": "The complete formatted package document.",
                },
            },
            "required": ["tier", "content"],
        },
    },
]


def execute_common_tool(tool_name: str, tool_input: dict, store: PackageStore) -> str:
    if tool_name == "save_content":
        return store.save(tool_input["section"], tool_input["content"])
    if tool_name == "load_content":
        return store.load(tool_input["section"])
    if tool_name == "list_store_contents":
        sections = store.list_sections()
        if not sections:
            return "Store is currently empty."
        return "Available sections:\n" + "\n".join(f"  • {s}" for s in sections)
    return f"Unknown tool: {tool_name}"


def execute_qc_tool(tool_name: str, tool_input: dict, store: PackageStore) -> str:
    if tool_name == "save_qc_report":
        section = tool_input["section"]
        score = tool_input["score"]
        approved = tool_input["approved"]
        report = (
            f"QC REPORT — {section}\n"
            f"{'─'*40}\n"
            f"Score:    {score}/10\n"
            f"Status:   {'✓ APPROVED' if approved else '✗ NEEDS REVISION'}\n"
            f"Issues:   {tool_input['issues']}\n"
            f"Improve:  {tool_input['improvements']}\n"
        )
        return store.save(f"qc_{section}", report)
    return execute_common_tool(tool_name, tool_input, store)


def execute_ceo_tool(tool_name: str, tool_input: dict, store: PackageStore) -> str:
    if tool_name == "load_all_content":
        return store.load_all()
    if tool_name == "save_package":
        tier = tool_input["tier"]
        key = f"package_{tier}"
        return store.save(key, tool_input["content"])
    return execute_common_tool(tool_name, tool_input, store)
