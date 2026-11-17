"""Handy-safe slices (2026-11-17).

Benson, 2026-11-15: Bambu Handy's cloud slicer failed on the Printed 6 mm Balls (0500-4014).
Our .gcode.3mf had no <model_instance> on its plate, so the plate listed no objects.
tools/handy_finish.py's check must call such a file not ready, and the thumbnail must be
drawn from the meshes and filament colours inside the file itself, placed by the 3MF's
component and build transforms, with no Bambu Studio and no source parts.
"""
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import bambu_slice as bs  # noqa: E402
import handy_finish as hf  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"


def _box(oid: int, lo, hi) -> str:
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4),
         (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)]
    vs = "".join(f'<vertex x="{a}" y="{b}" z="{c}"/>' for a, b, c in v)
    ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
    return f'<object id="{oid}" type="model"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>'


def _bambu_file(path: Path, with_instance: bool) -> None:
    """A Bambu-shaped project: a white 20 mm cube (part 1) under a red slab (part 2), the
    parts' meshes centred and placed by component transforms, the object by a build item."""
    objects = (f'<model xmlns="{CORE}" xmlns:p="{PROD}"><resources>'
               + _box(1, (-10, -10, -5), (10, 10, 5)) + _box(2, (-10, -10, -1), (10, 10, 1))
               + "</resources></model>")
    model = (f'<model xmlns="{CORE}" xmlns:p="{PROD}"><resources><object id="3" type="model"><components>'
             '<component p:path="/3D/Objects/object_1.model" objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 5"/>'
             '<component p:path="/3D/Objects/object_1.model" objectid="2" transform="1 0 0 0 1 0 0 0 1 0 0 11"/>'
             '</components></object></resources><build>'
             '<item objectid="3" transform="1 0 0 0 1 0 0 0 1 128 128 0" printable="1"/></build></model>')
    inst = ('<model_instance><metadata key="object_id" value="3"/><metadata key="instance_id" value="0"/>'
            '<metadata key="identify_id" value="8"/></model_instance>') if with_instance else ""
    settings = ('<config><object id="3"><metadata key="extruder" value="1"/>'
                '<part id="1"><metadata key="extruder" value="1"/></part>'
                '<part id="2"><metadata key="extruder" value="2"/></part></object>'
                f'<plate><metadata key="plater_id" value="1"/>{inst}</plate></config>')
    info = '<config><plate>' + ('<object identify_id="8" name="cube" skipped="false" />' if with_instance else "") + "</plate></config>"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("3D/3dmodel.model", model)
        z.writestr("3D/Objects/object_1.model", objects)
        z.writestr("Metadata/model_settings.config", settings)
        z.writestr("Metadata/slice_info.config", info)
        z.writestr("Metadata/project_settings.config", json.dumps({"filament_colour": ["#F4F1EA", "#C8312B"]}))


def test_check_flags_a_plate_with_no_objects():
    with tempfile.TemporaryDirectory() as td:
        bad, good = Path(td) / "bad.gcode.3mf", Path(td) / "good.gcode.3mf"
        _bambu_file(bad, with_instance=False)
        _bambu_file(good, with_instance=True)
        r = hf.handy_ready(bad)
        check(not r["model_instance"] and not r["identify_id"], f"a plate with no objects read as ready: {r}")
        r = hf.handy_ready(good)
        check(r["model_instance"] and r["identify_id"], f"a plate with its object read as not ready: {r}")
        check(not r["thumbnail"], "no plate_1.png in the file, but the check found one")


def test_plate_parts_places_and_colours_from_the_file():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.gcode.3mf"
        _bambu_file(f, with_instance=True)
        parts = bs.plate_parts(f)
        check(len(parts) == 2, f"expected the two parts, got {len(parts)}")
        (cube, c1), (slab, c2) = parts
        check(np.allclose(cube.bounds, [[118, 118, 0], [138, 138, 10]]), f"cube placed at {cube.bounds.tolist()}")
        check(np.allclose(slab.bounds, [[118, 118, 10], [138, 138, 12]]), f"slab placed at {slab.bounds.tolist()}")
        check((c1, c2) == ("#F4F1EA", "#C8312B"), f"colours by extruder came out {c1}, {c2}")


def test_thumbnail_shows_the_top_part_in_its_own_colour():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.gcode.3mf"
        _bambu_file(f, with_instance=True)
        img = np.asarray(Image.open(io.BytesIO(bs.thumbnail(bs.plate_parts(f), 128))))
        check(img.shape == (128, 128, 4), f"thumbnail shape {img.shape}")
        seen = img[img[..., 3] == 255][:, :3].astype(int)
        red = ((seen[:, 0] > seen[:, 1] + 60)).sum()
        white = ((abs(seen[:, 0] - seen[:, 1]) < 25) & (seen[:, 1] > 100)).sum()
        # the red slab is on top: from above it covers the cube's top; the cube's sides show white
        check(red > 0.25 * len(seen), f"the red top covers too little of the picture ({red} of {len(seen)} px)")
        check(white > 0.15 * len(seen), f"the white sides barely show ({white} of {len(seen)} px)")
        check((img[..., 3] == 0).sum() > 0.2 * 128 * 128, "no transparent background around the model")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("HANDY FINISH TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HANDY FINISH TESTS OK — a plate with no objects is flagged, and the thumbnail is drawn "
          "from the file's own placed meshes in their filament colours.")


if __name__ == "__main__":
    run()
