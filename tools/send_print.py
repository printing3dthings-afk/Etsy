#!/usr/bin/env python3
"""Send a sliced print to Scott's Action Center for one-tap approval.

    python3 tools/send_print.py model.gcode.3mf --label "LELAND plaque" \\
        [--ams 0,1,2,3] [--plate 1] [--bed textured_plate] [--notes "..."]

Uploads the .gcode.3mf (from tools/bambu_slice.py) to Frank's volume under
prints/, checks it arrived byte-identical, then stages a start_print action.
Nothing reaches the printer until Scott approves it; the home bridge then
starts it only if the P1S is idle (see tools/relay/bambu_p1s_bridge.py).

Env: FRANK_API_BASE (default the live Railway URL), APP_SECRET_TOKEN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = os.getenv("FRANK_API_BASE", "https://etsy-production-b2f1.up.railway.app").rstrip("/")
TOKEN = os.getenv("APP_SECRET_TOKEN", "").strip()


def _call(method: str, path: str, body: bytes | None = None, ctype: str = "application/json") -> bytes:
    req = urllib.request.Request(BASE + path, data=body, method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"{method} {path} -> {exc.code}: {exc.read().decode('utf-8', 'replace')[:500]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", type=Path)
    ap.add_argument("--label", required=True)
    ap.add_argument("--ams", help="AMS tray for each filament slot, comma-separated, 0-based (e.g. 0,1,2,3)")
    ap.add_argument("--plate", type=int, default=1)
    ap.add_argument("--bed", default="textured_plate")
    ap.add_argument("--notes", default="", help="shown on the approval card: spools to load, pauses, etc.")
    ap.add_argument("--summary", default="")
    a = ap.parse_args()
    if not TOKEN:
        raise SystemExit("APP_SECRET_TOKEN is not set")
    if not a.file.name.endswith(".gcode.3mf"):
        raise SystemExit("send a sliced .gcode.3mf from tools/bambu_slice.py, not a model file")
    data = a.file.read_bytes()
    rel = f"prints/{a.file.name}"
    _call("POST", "/api/files/upload?" + urllib.parse.urlencode({"path": rel}), data, "application/octet-stream")
    back = _call("GET", "/api/files/download?" + urllib.parse.urlencode({"root": "volume", "path": rel}))
    if hashlib.sha256(back).digest() != hashlib.sha256(data).digest():
        raise SystemExit(f"{rel} did not come back byte-identical from the volume; not staging it")
    body = {"file_path": rel, "label": a.label, "plate": a.plate, "bed_type": a.bed, "notes": a.notes}
    if a.summary:
        body["summary"] = a.summary
    if a.ams:
        body["ams_mapping"] = [int(x) for x in a.ams.split(",")]
    res = json.loads(_call("POST", "/api/print-jobs/stage", json.dumps(body).encode()))
    print(json.dumps({"uploaded": rel, "bytes": len(data), **res}, indent=1))


if __name__ == "__main__":
    main()
