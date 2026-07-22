from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MarketplacePlugin:
    id: str
    name: str
    version: str
    author: str
    description: str
    license: str = "MIT"
    repository: str = ""
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    min_shellsense_version: str = "0.1.0"
    max_shellsense_version: str = ""
    dependencies: dict[str, str] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    downloads: int = 0
    rating: float = 0.0
    homepage: str = ""
    source_url: str = ""
    documentation_url: str = ""
    checksum: str = ""
    signature: str = ""
    publisher: str = ""
    release_notes: str = ""
    updated_at: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "license": self.license,
            "repository": self.repository,
            "categories": self.categories,
            "tags": self.tags,
            "min_shellsense_version": self.min_shellsense_version,
            "max_shellsense_version": self.max_shellsense_version,
            "dependencies": self.dependencies,
            "permissions": self.permissions,
            "downloads": self.downloads,
            "rating": self.rating,
            "homepage": self.homepage,
            "source_url": self.source_url,
            "documentation_url": self.documentation_url,
            "checksum": self.checksum,
            "signature": self.signature,
            "publisher": self.publisher,
            "release_notes": self.release_notes,
            "updated_at": self.updated_at,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketplacePlugin:
        return cls(
            **{k: data.get(k, getattr(cls, k, "")) for k in cls.__dataclass_fields__}
        )


@dataclass
class PluginVersion:
    version: str
    checksum: str
    signature: str = ""
    release_notes: str = ""
    min_shellsense_version: str = "0.1.0"
    published_at: str = ""
    download_url: str = ""


@dataclass
class RepositoryInfo:
    name: str
    url: str
    enabled: bool = True
    priority: int = 10
    type: str = "community"
    description: str = ""
    last_sync: str = ""
    plugin_count: int = 0
    is_official: bool = False
    is_enterprise: bool = False


@dataclass
class SyncResult:
    repository: str = ""
    plugins_found: int = 0
    plugins_added: int = 0
    plugins_updated: int = 0
    errors: list[str] = field(default_factory=list)
    success: bool = True


@dataclass
class InstallResult:
    plugin_id: str = ""
    version: str = ""
    success: bool = False
    path: str = ""
    dependencies: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class UpdateResult:
    plugin_id: str = ""
    old_version: str = ""
    new_version: str = ""
    success: bool = False
    rollback_possible: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    nodes: list[str] = field(default_factory=list)
    edges: dict[str, list[str]] = field(default_factory=dict)
    resolution_order: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    circular: list[list[str]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


@dataclass
class PolicyRule:
    plugin_id: str = ""
    action: str = "allow"
    reason: str = ""
    enforced_by: str = "admin"


@dataclass
class AuditEntry:
    action: str = ""
    plugin_id: str = ""
    version: str = ""
    user: str = ""
    timestamp: str = ""
    details: str = ""
    success: bool = True


@dataclass
class SearchResult:
    query: str = ""
    total: int = 0
    results: list[MarketplacePlugin] = field(default_factory=list)
    facets: dict[str, list[str]] = field(default_factory=dict)
