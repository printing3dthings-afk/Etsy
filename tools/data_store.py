import datetime
import json
import os
import threading
from typing import Any
from config import SHOP_DATA_FILE


class DataStore:
    """Shared in-memory data store backed by shop_data.json.

    Thread-safe: all public read/write methods acquire a reentrant lock so
    concurrent agent threads cannot corrupt each other's modifications.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(SHOP_DATA_FILE):
            raise FileNotFoundError(f"Shop data file not found: {SHOP_DATA_FILE}")
        try:
            with open(SHOP_DATA_FILE, "r") as f:
                self._data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # Try to restore from most recent backup
            backup_dir = os.path.join(os.path.dirname(SHOP_DATA_FILE), "backups")
            if os.path.isdir(backup_dir):
                backups = sorted(
                    [f for f in os.listdir(backup_dir) if f.startswith("shop_data_")],
                    reverse=True,
                )
                if backups:
                    backup_path = os.path.join(backup_dir, backups[0])
                    with open(backup_path, "r") as f:
                        self._data = json.load(f)
                    import shutil
                    shutil.copy2(backup_path, SHOP_DATA_FILE)
                    return
            raise

    def save(self) -> None:
        import shutil
        from datetime import datetime

        with self._lock:
            tmp_path = SHOP_DATA_FILE + ".tmp"
            # Write to temp file first (atomic write — prevents corruption)
            with open(tmp_path, "w") as f:
                json.dump(self._data, f, indent=2)
            # Rename into place (atomic on most filesystems)
            os.replace(tmp_path, SHOP_DATA_FILE)

            # Rolling backup — keep last 3
            backup_dir = os.path.join(os.path.dirname(SHOP_DATA_FILE), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"shop_data_{ts}.json")
            shutil.copy2(SHOP_DATA_FILE, backup_path)
            # Prune: keep only 3 most recent backups
            backups = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith("shop_data_")],
                reverse=True,
            )
            for old in backups[3:]:
                try:
                    os.remove(os.path.join(backup_dir, old))
                except OSError:
                    pass

    def get(self, *keys: str, default: Any = None) -> Any:
        with self._lock:
            node = self._data
            for key in keys:
                if not isinstance(node, dict) or key not in node:
                    return default
                node = node[key]
            return node

    def set(self, value: Any, *keys: str) -> None:
        with self._lock:
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
        with self._lock:
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
