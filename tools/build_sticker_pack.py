#!/usr/bin/env python3
"""
build_sticker_pack.py <PID> — one-shot sticker-pack build for Frank's one-tap
"Build sticker pack" capability. This is the sticker sibling of build_planner.py.

Each planner has a bespoke sticker spec module (theme palette + the 9 sheet
prompts). They are structurally identical — module-level PID, _STYLE, SHEETS —
so this wrapper reads any one of them and runs the SAME engine-agnostic pipeline:

  1. Generate the 9 raw sheets on a SOLID flat background (NOT transparent), so it
     works on any approved engine — Gemini in the sandbox, gpt-image-1 on the
     server. (Only gpt-image-1 supports background="transparent"; the bespoke
     modules hardcode that, which is why we can't just call their main().)
  2. Strip the background + segment into individual stickers + package the ZIP via
     the shared, proven tools/process_sticker_sheets.py (corner-sampled flood-fill
     removes whatever uniform background the engine rendered).

The sticker COUNT reported is a real measured number (segmented individuals),
never a guess — the top rule is NEVER LIE TO THE CUSTOMER, and sticker counts are
a described-on-the-listing claim.

Paths are volume-aware through process_sticker_sheets' resolve_dp_base(), so on
Railway this reads/writes the durable /data volume.

Usage:  python tools/build_sticker_pack.py DP1030
        python tools/build_sticker_pack.py DP1032 --sheets 5
"""
import argparse
import importlib
import re
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# The registry of buildable sticker packs: a planner code -> its spec module.
# A PID absent here has no sticker spec yet (a new product needs a spec module,
# same as build_planner requires a PLANNER_CONFIGS entry). Keeping this explicit
# means an unknown code fails loudly instead of silently doing nothing.
SPEC_MODULES = {
    "DP1030": "tools.generate_adhd_assets",
    "DP1031": "tools.generate_sage_garden_assets",
    "DP1032": "tools.generate_midnight_kawaii_assets",
    "DP1033": "tools.generate_sunflower_studio_assets",
    "DP1034": "tools.generate_celestial_assets",
}

# A single uniform mid-gray reads as clearly-background against BOTH the dark
# outlines of every sticker AND any light interior highlights, so the flood-fill
# eats neither (the dark-mode technique proven on DP1032/DP1034). Forcing it here
# — and overriding each module's "TRANSPARENT background" clause — gives one code
# path that produces a strippable sheet on every engine.
_SOLID_BG = (
    "SOLID FLAT MEDIUM-GRAY #808080 background that completely fills the canvas "
    "edge to edge behind the stickers (NOT transparent, no paper texture, no "
    "shadow) — a single uniform gray tone touching all four corners"
)


def _solidify(style: str) -> str:
    """Swap a spec module's transparent-background instruction for a solid one so
    the sheet can be background-stripped after generation on any engine."""
    # Replace the main "TRANSPARENT background (...)." sentence.
    style = re.sub(r"TRANSPARENT background[^.]*\.", _SOLID_BG + ".", style,
                   flags=re.IGNORECASE)
    # Neutralize stray "on a transparent grid" phrasing in sheet contents.
    style = re.sub(r"transparent grid", "grid", style, flags=re.IGNORECASE)
    return style


def build(pid: str, max_sheets: int | None = None) -> int:
    pid = pid.strip().upper()
    mod_name = SPEC_MODULES.get(pid)
    if not mod_name:
        print(f"[build_sticker_pack] no sticker spec for {pid}. "
              f"Supported: {', '.join(sorted(SPEC_MODULES))}")
        return 2

    spec = importlib.import_module(mod_name)
    style = _solidify(spec._STYLE)
    sheets = spec.SHEETS  # {n: (name, contents)}
    nums = sorted(sheets)
    if max_sheets:
        nums = [n for n in nums if n <= max_sheets]

    # Import the shared pipeline AFTER we know the PID is valid. ART_DIR here is the
    # volume-aware product_files dir process_pid() will read the raw sheets from.
    from tools import process_sticker_sheets as psp
    from tools.image_gen import generate_image, SQUARE

    psp.ART_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[build_sticker_pack] {pid}: generating {len(nums)} raw sheets "
          f"(solid background, {mod_name.split('.')[-1]} spec)…", flush=True)
    for n in nums:
        name, contents = sheets[n]
        contents = re.sub(r"transparent grid", "grid", contents, flags=re.IGNORECASE)
        prompt = f"{style}\n\nSheet theme: {name}. {contents}"
        out = psp.ART_DIR / f"{pid}_sticker_sheet_{n}.png"
        print(f"  sheet {n} ({name}) -> {out.name}", flush=True)
        try:
            generate_image(prompt, out, size=SQUARE, quality="high", output_format="png")
        except Exception as e:  # noqa: BLE001
            print(f"[build_sticker_pack] FAILED generating sheet {n} for {pid}: {e}")
            return 1

    print(f"[build_sticker_pack] {pid}: stripping backgrounds + segmenting + packaging…",
          flush=True)
    result = psp.process_pid(pid, max_sheets=max_sheets, make_individual=True)
    if not result or not result.get("sheets"):
        print(f"[build_sticker_pack] FAILED: no processed sheets for {pid}")
        return 1
    zip_path = psp.build_zip(result)

    count = result.get("sticker_count", 0)
    print(f"[build_sticker_pack] DONE {pid}: {len(result['sheets'])} sheets, "
          f"{count} individual stickers -> {zip_path.name} (in {psp.ART_DIR})", flush=True)
    if count < 50:
        # qc_sweep hard-FAILs under 50; surface it now rather than at QC time.
        print(f"[build_sticker_pack] WARNING: only {count} stickers segmented (<50) — "
              f"a sheet may have generated as one connected blob; re-run or inspect.")

    # Automatic durability backup (2026-07-17) — closes the exact failure mode that
    # lost DP1030-1034's source files the first time (approval-gated, so nobody
    # remembered to run it). A backup hiccup must never fail an otherwise-good build.
    try:
        from tools import backup_digital_products
        backup_digital_products.run()
    except Exception as exc:  # noqa: BLE001
        print(f"[build_sticker_pack] ⚠ backup step failed (build itself is still good): {exc}", flush=True)

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a planner's sticker pack end to end.")
    ap.add_argument("pid", help="Planner code, e.g. DP1030")
    ap.add_argument("--sheets", type=int, default=None,
                    help="Only build the first N sheets (default: all in the spec).")
    args = ap.parse_args()
    return build(args.pid, args.sheets)


if __name__ == "__main__":
    sys.exit(main())
