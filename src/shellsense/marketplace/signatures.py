from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_shellsense_dir

logger = get_logger(__name__)


class SignatureManager:
    def __init__(self, data_dir: str | None = None) -> None:
        self._data_dir = data_dir
        self._trusted_publishers: dict[str, dict[str, Any]] = {}
        self._revoked: set[str] = set()
        if data_dir is None:
            self._load()

    def _trust_path(self) -> str:
        if self._data_dir:
            return os.path.join(self._data_dir, "trust.json")
        return os.path.join(get_shellsense_dir(), "marketplace", "trust.json")

    def _load(self) -> None:
        path = self._trust_path()
        try:
            if os.path.isfile(path):
                with open(path) as f:
                    data: dict[str, Any] = json.load(f)
                self._trusted_publishers = data.get("publishers", {})
                self._revoked = set(data.get("revoked", []))
        except Exception as e:
            logger.warning("Failed to load trust data: %s", e)

    def _save(self) -> None:
        path = self._trust_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(
                    {
                        "publishers": self._trusted_publishers,
                        "revoked": list(self._revoked),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error("Failed to save trust data: %s", e)

    def compute_checksum(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def verify_checksum(self, file_path: str, expected: str) -> bool:
        actual = self.compute_checksum(file_path)
        return actual == expected

    def add_trusted_publisher(
        self, publisher_id: str, name: str, public_key: str = ""
    ) -> None:
        self._trusted_publishers[publisher_id] = {
            "name": name,
            "public_key": public_key,
            "added_at": __import__("datetime").datetime.now().isoformat(),
        }
        self._save()
        logger.info("Added trusted publisher '%s' (%s)", publisher_id, name)

    def remove_trusted_publisher(self, publisher_id: str) -> None:
        self._trusted_publishers.pop(publisher_id, None)
        self._save()

    def revoke_publisher(self, publisher_id: str) -> None:
        self._revoked.add(publisher_id)
        self._save()
        logger.warning("Revoked publisher '%s'", publisher_id)

    def is_publisher_trusted(self, publisher_id: str) -> bool:
        return publisher_id in self._trusted_publishers

    def is_publisher_revoked(self, publisher_id: str) -> bool:
        return publisher_id in self._revoked

    def verify_plugin(
        self, plugin_data: dict[str, Any], archive_path: str = ""
    ) -> list[str]:
        warnings: list[str] = []

        checksum = plugin_data.get("checksum", "")
        if checksum and archive_path and os.path.isfile(archive_path):
            if not self.verify_checksum(archive_path, checksum):
                warnings.append("Checksum verification failed")
        elif checksum and not archive_path:
            pass
        else:
            warnings.append("No checksum available for verification")

        publisher = plugin_data.get("publisher", "")
        if publisher:
            if self.is_publisher_revoked(publisher):
                warnings.append(f"Publisher '{publisher}' has been revoked")
            elif not self.is_publisher_trusted(publisher):
                warnings.append(f"Publisher '{publisher}' is not in trusted list")
        else:
            warnings.append("No publisher information")

        return warnings

    def get_trusted_publishers(self) -> dict[str, Any]:
        return dict(self._trusted_publishers)
