from __future__ import annotations

import json
import os
from typing import Any

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_shellsense_dir

logger = get_logger(__name__)


class CollaborationManager:
    def __init__(self) -> None:
        self._collections_dir = os.path.join(
            get_shellsense_dir(), "marketplace", "collections"
        )
        os.makedirs(self._collections_dir, exist_ok=True)

    def export_collection(
        self, name: str, plugin_ids: list[str], output_path: str | None = None
    ) -> str:
        collection = {
            "name": name,
            "version": "1.0",
            "exported_at": __import__("datetime").datetime.now().isoformat(),
            "plugins": plugin_ids,
        }
        if output_path is None:
            output_path = os.path.join(self._collections_dir, f"{name}.json")
        with open(output_path, "w") as f:
            json.dump(collection, f, indent=2)
        logger.info("Exported collection '%s' with %d plugins", name, len(plugin_ids))
        return output_path

    def import_collection(self, path: str) -> list[str]:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Collection file not found: {path}")
        with open(path) as f:
            collection = json.load(f)
        plugin_ids = collection.get("plugins", [])
        logger.info(
            "Imported collection '%s' with %d plugins",
            collection.get("name", "unknown"),
            len(plugin_ids),
        )
        return plugin_ids

    def list_collections(self) -> list[dict[str, Any]]:
        collections: list[dict[str, Any]] = []
        if not os.path.isdir(self._collections_dir):
            return collections
        for filename in os.listdir(self._collections_dir):
            if filename.endswith(".json"):
                path = os.path.join(self._collections_dir, filename)
                try:
                    with open(path) as f:
                        data = json.load(f)
                    collections.append(
                        {
                            "name": data.get("name", filename[:-5]),
                            "path": path,
                            "plugin_count": len(data.get("plugins", [])),
                            "exported_at": data.get("exported_at", ""),
                        }
                    )
                except Exception:
                    pass
        return collections
