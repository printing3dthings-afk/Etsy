#!/usr/bin/env python3
"""The full check set for a Christmas ornament set (2026-10-21):

    python3 check_ornament.py snowflakes [step ...]

Each design in a set is its own print (one object on the plate), checked one
by one; the renders lay them out side by side. Run the set's build.sh first.
Steps and results as tools/model_checks.py.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
from model_checks import run_checks  # noqa: E402

ICE, RED, WHITE, SLATE = "#D8E6F0", "#C62F3A", "#F4F1EA", "#2E3440"
SETS = {
    "snowflakes": dict(
        name="crystal_snowflake", designs=6, colour=ICE, spacing=(84, 92),
        label="Crystal Snowflake Ornaments",
        note="Six faceted snowflake ornaments: thick arms and branches cut like crystal, "
             "a six-sided gem at the hub and a hanging loop at the top."),
    # six prints, each in colour parts
    "mini_lanterns": dict(
        name="mini_lantern", designs=6, spacing=(48, 0),
        dparts=[("frame", SLATE), ("glass", WHITE), ("art", SLATE), ("snow", WHITE), ("bow", RED)],
        label="Village Mini-Lantern Ornaments",
        note="Six hex-lantern ornaments, each with a building from the Christmas village raised on its "
             "front and back glass (church, cottage, clock tower, town tree, toy shop, well), a snowflake "
             "and stars between, snow on the roof, a red bow and a ring to hang it by."),
    # one print in colour parts (the name is the buyer's: the file's default is a sample)
    "name_ornament": dict(
        name="name_ornament", parts=[("body", RED), ("inlay", WHITE)],
        label="Personalised Name Ornament",
        note="A domed ornament, flat behind, with a name and the year inlaid flush in a second colour "
             "under a star. The sample name is Olivia."),
}

if __name__ == "__main__":
    key = sys.argv[1]
    S = SETS[key]
    d = HERE / key
    if "parts" in S:
        run_checks(d, S["name"], dict(label=S["label"], note=S["note"], objects=[S["parts"]],
                                      unions=[f"{S['name']}_union.stl"],
                                      source=f"christmas_ornaments/{key}/{S['name']}.3mf"), sys.argv[2:] or None)
        sys.exit()
    n = S["designs"]
    objects, unions, tags, shown = [], [], [], {}
    sx, sy = S["spacing"]
    for i in range(1, n + 1):
        if "dparts" in S:
            objects.append([(f"{i}_{p}", c) for p, c in S["dparts"]])
            unions.append(f"{S['name']}_{i}_union.stl")
            shown[i - 1] = [(i - 3.5) * sx, 0, 0]
        else:
            objects.append([(f"{i}", S["colour"])])
            unions.append(f"{S['name']}_{i}.stl")
            shown[i - 1] = [((i - 1) % 3 - 1) * sx, -((i - 1) // 3 - 0.5) * sy, 0]
        tags.append(f"_{i}")
    run_checks(d, S["name"], dict(label=S["label"], note=S["note"], objects=objects, unions=unions,
                                  tags=tags, shown=shown, source=f"christmas_ornaments/{key}/{S['name']}.3mf"),
               sys.argv[2:] or None)
