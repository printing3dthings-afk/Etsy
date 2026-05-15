import datetime
import json
import os
from typing import Any
from config import SHOP_DATA_FILE


class DataStore:
    """Shared in-memory data store backed by shop_data.json."""

    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(SHOP_DATA_FILE):
            raise FileNotFoundError(f"Shop data file not found: {SHOP_DATA_FILE}")
        with open(SHOP_DATA_FILE, "r") as f:
            self._data = json.load(f)

    def save(self) -> None:
        with open(SHOP_DATA_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, *keys: str, default: Any = None) -> Any:
        node = self._data
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def set(self, value: Any, *keys: str) -> None:
        node = self._data
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        node[keys[-1]] = value

    @property
    def shop(self) -> dict:
        return self._data.get("shop", {})

    @property
    def listings(self) -> list:
        return self._data.get("listings", [])

    @property
    def orders(self) -> list:
        return self._data.get("orders", [])

    @property
    def messages(self) -> list:
        return self._data.get("messages", [])

    @property
    def reviews(self) -> list:
        return self._data.get("reviews", [])

    @property
    def analytics(self) -> dict:
        return self._data.get("analytics", {})

    def find_listing(self, listing_id: str) -> dict | None:
        return next((l for l in self.listings if l["id"] == listing_id), None)

    def find_order(self, order_id: str) -> dict | None:
        return next((o for o in self.orders if o["id"] == order_id), None)

    def find_message(self, message_id: str) -> dict | None:
        return next((m for m in self.messages if m["id"] == message_id), None)

    def find_review(self, review_id: str) -> dict | None:
        return next((r for r in self.reviews if r["id"] == review_id), None)

    def log_action(self, agent: str, action: str, details: dict = None) -> None:
        """Append an audit entry and persist; keeps only the last 500 entries."""
        audit_log = self._data.setdefault("audit_log", [])
        audit_log.append({
            "ts":      datetime.datetime.now().isoformat(),
            "agent":   agent,
            "action":  action,
            "details": details or {},
        })
        if len(audit_log) > 500:
            self._data["audit_log"] = audit_log[-500:]
        self.save()

    def get_audit_log(self, limit: int = 50) -> list:
        """Return the last *limit* audit entries, newest first."""
        audit_log = self._data.get("audit_log", [])
        return list(reversed(audit_log[-limit:]))
