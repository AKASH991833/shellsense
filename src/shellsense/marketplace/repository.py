from __future__ import annotations

import json
import os
from typing import Any

from shellsense.marketplace.exceptions import RepositoryError
from shellsense.marketplace.models import RepositoryInfo, SyncResult
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_shellsense_dir

logger = get_logger(__name__)

DEFAULT_REPOSITORIES = [
    RepositoryInfo(
        name="official",
        url="https://marketplace.shellsense.ai/api/v1",
        enabled=True,
        priority=0,
        type="official",
        description="Official ShellSense plugin repository",
        is_official=True,
    ),
    RepositoryInfo(
        name="community",
        url="https://community.shellsense.ai/api/v1",
        enabled=True,
        priority=10,
        type="community",
        description="Community-contributed plugins",
    ),
]


class RepositoryManager:
    def __init__(self) -> None:
        self._repos: dict[str, RepositoryInfo] = {}
        self._local_cache_dir = os.path.join(
            get_shellsense_dir(), "marketplace", "cache"
        )
        self._load()

    def _repos_path(self) -> str:
        return os.path.join(get_shellsense_dir(), "marketplace", "repositories.json")

    def _load(self) -> None:
        path = self._repos_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.isfile(path):
                with open(path) as f:
                    data: list[dict[str, Any]] = json.load(f)
                for item in data:
                    info = RepositoryInfo(**item)
                    self._repos[info.name] = info
                logger.info("Loaded %d repositories", len(self._repos))
            else:
                self._reset_defaults()
        except Exception as e:
            logger.warning("Failed to load repositories: %s", e)
            self._reset_defaults()

    def _save(self) -> None:
        path = self._repos_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = [r.__dict__ for r in self._repos.values()]
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save repositories: %s", e)

    def _reset_defaults(self) -> None:
        self._repos = {r.name: r for r in DEFAULT_REPOSITORIES}
        self._save()

    def add(
        self,
        name: str,
        url: str,
        repo_type: str = "community",
        priority: int = 50,
        description: str = "",
    ) -> RepositoryInfo:
        if name in self._repos:
            raise RepositoryError(url, f"Repository '{name}' already exists")
        info = RepositoryInfo(
            name=name,
            url=url,
            type=repo_type,
            priority=priority,
            description=description or f"{name} repository",
        )
        self._repos[name] = info
        self._save()
        logger.info("Added repository '%s' -> %s", name, url)
        return info

    def remove(self, name: str) -> None:
        if name not in self._repos:
            raise RepositoryError(name, "Repository not found")
        del self._repos[name]
        self._save()
        logger.info("Removed repository '%s'", name)

    def enable(self, name: str) -> None:
        if name not in self._repos:
            raise RepositoryError(name, "Repository not found")
        self._repos[name].enabled = True
        self._save()

    def disable(self, name: str) -> None:
        if name not in self._repos:
            raise RepositoryError(name, "Repository not found")
        self._repos[name].enabled = False
        self._save()

    def set_priority(self, name: str, priority: int) -> None:
        if name not in self._repos:
            raise RepositoryError(name, "Repository not found")
        self._repos[name].priority = priority
        self._save()

    def get(self, name: str) -> RepositoryInfo:
        if name not in self._repos:
            raise RepositoryError(name, "Repository not found")
        return self._repos[name]

    def list_all(self) -> list[RepositoryInfo]:
        return sorted(
            self._repos.values(),
            key=lambda r: (r.priority, r.name),
        )

    def list_enabled(self) -> list[RepositoryInfo]:
        return [r for r in self.list_all() if r.enabled]

    def sync(self, name: str) -> SyncResult:
        if name not in self._repos:
            raise RepositoryError(name, "Repository not found")
        repo = self._repos[name]
        return self._sync_repo(repo)

    def sync_all(self) -> list[SyncResult]:
        results: list[SyncResult] = []
        for repo in self.list_enabled():
            try:
                result = self._sync_repo(repo)
                results.append(result)
            except Exception as e:
                results.append(
                    SyncResult(
                        repository=repo.name,
                        success=False,
                        errors=[str(e)],
                    )
                )
        return results

    def _sync_repo(self, repo: RepositoryInfo) -> SyncResult:
        cache_dir = os.path.join(self._local_cache_dir, repo.name)
        os.makedirs(cache_dir, exist_ok=True)

        result = SyncResult(repository=repo.name)
        try:
            import json as _json
            import urllib.request

            index_url = f"{repo.url}/plugins/index.json"
            req = urllib.request.Request(
                index_url,
                headers={"User-Agent": "ShellSenseAI/0.1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data: dict[str, Any] = _json.loads(resp.read().decode())

            plugins = data.get("plugins", [])
            result.plugins_found = len(plugins)

            cache_path = os.path.join(cache_dir, "index.json")
            with open(cache_path, "w") as f:
                _json.dump(data, f, indent=2)

            result.success = True
            repo.last_sync = __import__("datetime").datetime.now().isoformat()
            self._save()
            logger.info(
                "Synced repository '%s': %d plugins", repo.name, result.plugins_found
            )
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.warning("Failed to sync repository '%s': %s", repo.name, e)

        return result

    def get_cache(self, name: str) -> dict[str, Any] | None:
        cache_path = os.path.join(self._local_cache_dir, name, "index.json")
        try:
            if os.path.isfile(cache_path):
                with open(cache_path) as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def get_cached_plugin(
        self, repo_name: str, plugin_id: str
    ) -> dict[str, Any] | None:
        cache = self.get_cache(repo_name)
        if cache:
            for p in cache.get("plugins", []):
                if p.get("id") == plugin_id:
                    return p
        return None

    def search_cached(self, query: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        q = query.lower()
        for repo in self.list_enabled():
            cache = self.get_cache(repo.name)
            if not cache:
                continue
            for p in cache.get("plugins", []):
                if (
                    q in p.get("name", "").lower()
                    or q in p.get("id", "").lower()
                    or q in p.get("description", "").lower()
                    or q in ",".join(p.get("tags", [])).lower()
                ):
                    p["_repo"] = repo.name
                    results.append(p)
        return results
