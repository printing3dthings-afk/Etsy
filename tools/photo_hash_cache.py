#!/usr/bin/env python3
"""
photo_hash_cache.py — persistent URL -> perceptual-hash cache for listing photos.

The integrity checks download and hash every listing photo on every run. Etsy's
url_fullxfull URLs embed a stable image id, so the same URL always yields the same
hash — re-downloading it is pure waste (bandwidth, time, and load that contributes
to rate-limit pressure). This cache stores {url: hash} on disk so repeat runs only
fetch photos they have never seen.

Usage:
    from tools.photo_hash_cache import PhotoHashCache

    cache = PhotoHashCache()
    h = cache.get_or_compute(url, fetch_fn, hash_fn)   # fetch+hash only on miss
    cache.save()
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

_BASE_DIR = Path(__file__).parent.parent
_DEFAULT_PATH = _BASE_DIR / "data" / "photo_hash_cache.json"


class PhotoHashCache:
    def __init__(self, path: Path | str = _DEFAULT_PATH):
        self.path = Path(path)
        self._data: dict[str, str] = {}
        self._dirty = False
        self.hits = 0
        self.misses = 0
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except Exception:
                self._data = {}

    def get(self, url: str) -> str | None:
        return self._data.get(url)

    def put(self, url: str, hash_value: str) -> None:
        if url and hash_value and self._data.get(url) != hash_value:
            self._data[url] = hash_value
            self._dirty = True

    def get_or_compute(
        self,
        url: str,
        fetch_fn: Callable[[str], bytes | None],
        hash_fn: Callable[[bytes], str | None],
    ) -> str | None:
        """Return the cached hash for url, or fetch+hash on a miss and cache it."""
        cached = self._data.get(url)
        if cached is not None:
            self.hits += 1
            return cached
        self.misses += 1
        data = fetch_fn(url)
        if data is None:
            return None
        h = hash_fn(data)
        if h:
            self.put(url, h)
        return h

    def save(self) -> None:
        if not self._dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2, sort_keys=True))
        self._dirty = False

    def __len__(self) -> int:
        return len(self._data)
