from __future__ import annotations

import os
from pathlib import Path

import pytest

from shellsense.marketplace.collaboration import CollaborationManager
from shellsense.marketplace.dependency import DependencyResolver
from shellsense.marketplace.enterprise import EnterprisePolicies
from shellsense.marketplace.exceptions import (
    RepositoryError,
)
from shellsense.marketplace.marketplace import MarketplaceManager
from shellsense.marketplace.models import (
    AuditEntry,
    DependencyGraph,
    InstallResult,
    MarketplacePlugin,
    PluginVersion,
    PolicyRule,
    RepositoryInfo,
    SearchResult,
    SyncResult,
    UpdateResult,
)
from shellsense.marketplace.repository import RepositoryManager
from shellsense.marketplace.signatures import SignatureManager


class TestMarketplaceModels:
    def test_marketplace_plugin_defaults(self) -> None:
        p = MarketplacePlugin(
            id="test", name="Test", version="1.0", author="A", description="D"
        )
        assert p.license == "MIT"
        assert p.categories == []
        assert p.downloads == 0

    def test_marketplace_plugin_to_from_dict(self) -> None:
        original = MarketplacePlugin(
            id="p1",
            name="Plugin 1",
            version="2.0",
            author="Author",
            description="Desc",
            tags=["tag1"],
            categories=["cat1"],
            downloads=100,
            rating=4.5,
        )
        data = original.to_dict()
        restored = MarketplacePlugin.from_dict(data)
        assert restored.id == original.id
        assert restored.tags == ["tag1"]
        assert restored.downloads == 100
        assert restored.rating == 4.5

    def test_plugin_version(self) -> None:
        v = PluginVersion(version="1.0.0", checksum="abc123")
        assert v.version == "1.0.0"
        assert v.min_shellsense_version == "0.1.0"

    def test_repository_info_defaults(self) -> None:
        r = RepositoryInfo(name="test", url="https://example.com")
        assert r.enabled is True
        assert r.priority == 10
        assert r.type == "community"

    def test_sync_result(self) -> None:
        r = SyncResult(repository="official", plugins_found=5, plugins_added=3)
        assert r.success is True
        assert r.plugins_found == 5

    def test_install_result(self) -> None:
        r = InstallResult(plugin_id="test", version="1.0", success=True)
        assert r.success
        assert r.dependencies == []

    def test_update_result(self) -> None:
        r = UpdateResult(plugin_id="test", old_version="1.0", new_version="2.0")
        assert r.rollback_possible is True

    def test_dependency_graph(self) -> None:
        g = DependencyGraph(nodes=["a", "b"], edges={"a": ["b"]})
        assert g.resolution_order == []
        assert g.conflicts == []

    def test_policy_rule(self) -> None:
        r = PolicyRule(plugin_id="test", action="allow")
        assert r.enforced_by == "admin"

    def test_audit_entry(self) -> None:
        e = AuditEntry(action="install", plugin_id="test", version="1.0", user="admin")
        assert e.success is True

    def test_search_result(self) -> None:
        r = SearchResult(query="test", total=1)
        assert r.total == 1
        assert r.results == []


class TestRepositoryManager:
    def test_default_repositories(self) -> None:
        rm = RepositoryManager()
        repos = rm.list_all()
        assert len(repos) >= 2
        assert any(r.name == "official" for r in repos)
        assert any(r.name == "community" for r in repos)

    def test_add_repository(self) -> None:
        rm = RepositoryManager()
        rm.add("test-repo", "https://test.example.com", priority=5)
        repo = rm.get("test-repo")
        assert repo.url == "https://test.example.com"
        assert repo.priority == 5
        rm.remove("test-repo")

    def test_add_duplicate_raises(self) -> None:
        rm = RepositoryManager()
        with pytest.raises(RepositoryError):
            rm.add("official", "https://duplicate.com")

    def test_remove_nonexistent_raises(self) -> None:
        rm = RepositoryManager()
        with pytest.raises(RepositoryError):
            rm.remove("nonexistent")

    def test_enable_disable(self) -> None:
        rm = RepositoryManager()
        rm.add("test-ede", "https://test.com")
        rm.disable("test-ede")
        assert not rm.get("test-ede").enabled
        rm.enable("test-ede")
        assert rm.get("test-ede").enabled
        rm.remove("test-ede")

    def test_set_priority(self) -> None:
        rm = RepositoryManager()
        rm.add("test-pri", "https://test.com")
        rm.set_priority("test-pri", 99)
        assert rm.get("test-pri").priority == 99
        rm.remove("test-pri")

    def test_list_enabled(self) -> None:
        rm = RepositoryManager()
        enabled = rm.list_enabled()
        assert all(r.enabled for r in enabled)

    def test_get_nonexistent_raises(self) -> None:
        rm = RepositoryManager()
        with pytest.raises(RepositoryError):
            rm.get("nonexistent")

    def test_search_cached_no_cache(self) -> None:
        rm = RepositoryManager()
        results = rm.search_cached("test")
        assert results == []


class TestSignatureManager:
    def test_checksum(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        checksum = sm.compute_checksum(str(test_file))
        assert len(checksum) == 64
        assert sm.verify_checksum(str(test_file), checksum)

    def test_checksum_mismatch(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        assert not sm.verify_checksum(
            str(test_file), "00000000000000000000000000000000" * 4
        )

    def test_trusted_publishers(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        sm.add_trusted_publisher("pub1", "Publisher One")
        assert sm.is_publisher_trusted("pub1")
        assert not sm.is_publisher_trusted("unknown")

    def test_revoke_publisher(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        sm.add_trusted_publisher("pub2", "Publisher Two")
        assert not sm.is_publisher_revoked("pub2")
        sm.revoke_publisher("pub2")
        assert sm.is_publisher_revoked("pub2")

    def test_remove_trusted_publisher(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        sm.add_trusted_publisher("pub3", "Publisher Three")
        sm.remove_trusted_publisher("pub3")
        assert not sm.is_publisher_trusted("pub3")

    def test_verify_plugin_no_checksum(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        warnings = sm.verify_plugin({"id": "test", "version": "1.0"})
        assert any("No checksum" in w for w in warnings)

    def test_verify_plugin_unknown_publisher(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        warnings = sm.verify_plugin({"id": "test", "publisher": "unknown"})
        assert any("not in trusted" in w for w in warnings)

    def test_verify_plugin_revoked_publisher(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        sm.add_trusted_publisher("revoked-pub", "Revoked")
        sm.revoke_publisher("revoked-pub")
        warnings = sm.verify_plugin({"id": "test", "publisher": "revoked-pub"})
        assert any("revoked" in w.lower() for w in warnings)

    def test_get_trusted_publishers(self, tmp_path: Path) -> None:
        sm = SignatureManager(data_dir=str(tmp_path))
        sm.add_trusted_publisher("pub-a", "Publisher A")
        pubs = sm.get_trusted_publishers()
        assert "pub-a" in pubs


class TestDependencyResolver:
    def test_resolve_no_deps(self) -> None:
        resolver = DependencyResolver()
        graph = resolver.resolve("my-plugin", {}, {})
        assert "my-plugin" in graph.nodes
        assert graph.missing == []

    def test_resolve_simple_dep(self) -> None:
        resolver = DependencyResolver()
        all_plugins = {
            "dep-a": {"dependencies": {}},
        }
        graph = resolver.resolve("my-plugin", {"dep-a": "1.0"}, all_plugins)
        assert "dep-a" in graph.nodes
        assert graph.missing == []

    def test_resolve_missing_dep(self) -> None:
        resolver = DependencyResolver()
        graph = resolver.resolve("my-plugin", {"missing-dep": "1.0"}, {})
        assert "missing-dep" in graph.missing

    def test_circular_dependency(self) -> None:
        resolver = DependencyResolver()
        all_plugins = {
            "dep-a": {"dependencies": {"dep-b": "1.0"}},
            "dep-b": {"dependencies": {"dep-a": "1.0"}},
        }
        graph = resolver.resolve("my-plugin", {"dep-a": "1.0"}, all_plugins)
        assert graph.circular

    def test_topological_order(self) -> None:
        resolver = DependencyResolver()
        graph = DependencyGraph(
            nodes=["a", "b", "c"],
            edges={"a": ["b"], "b": ["c"]},
        )
        order = resolver._topological_sort(graph.nodes, graph.edges)
        assert order.index("a") < order.index("b") < order.index("c")

    def test_check_conflicts(self) -> None:
        resolver = DependencyResolver()
        conflicts = resolver.check_conflicts(
            "my-plugin", {"dep-a": "2.0"}, {"dep-a": "1.0"}
        )
        assert len(conflicts) == 1
        assert "dep-a" in conflicts[0]

    def test_no_conflicts(self) -> None:
        resolver = DependencyResolver()
        conflicts = resolver.check_conflicts(
            "my-plugin", {"dep-a": "1.0"}, {"dep-a": "1.0"}
        )
        assert conflicts == []

    def test_detect_circular(self) -> None:
        resolver = DependencyResolver()
        cycles = resolver._detect_circular(["a", "b"], {"a": ["b"], "b": ["a"]})
        assert len(cycles) >= 1


class TestMarketplaceManager:
    def test_initialization(self) -> None:
        mm = MarketplaceManager()
        assert mm.repos is not None
        assert mm.signatures is not None
        assert mm.dep_resolver is not None

    def test_search_empty_cache(self) -> None:
        mm = MarketplaceManager()
        result = mm.search("test")
        assert result.total == 0
        assert result.results == []

    def test_list_installed_empty(self) -> None:
        mm = MarketplaceManager()
        assert mm.list_installed() == []

    def test_info_not_found(self) -> None:
        mm = MarketplaceManager()
        plugin = mm.info("nonexistent-plugin")
        assert plugin is None

    def test_verify_not_found(self) -> None:
        mm = MarketplaceManager()
        warnings = mm.verify("nonexistent-plugin")
        assert len(warnings) == 1
        assert "not found" in warnings[0]

    def test_export_import_collection(self, tmp_path: Path) -> None:
        mm = MarketplaceManager()
        output = str(tmp_path / "collection.json")
        mm.export_collection(output)
        assert os.path.isfile(output)
        count = mm.import_collection(output)
        assert count >= 0


class TestEnterprisePolicies:
    def make_ep(self) -> EnterprisePolicies:
        return EnterprisePolicies(data_dir="/tmp/_test_disabled")

    def test_default_policies(self) -> None:
        ep = self.make_ep()
        assert ep.get_approved() == []
        assert ep.get_blocked() == []
        assert ep.get_mandatory() == []

    def test_check_install_no_policies(self) -> None:
        ep = self.make_ep()
        result = ep.check_install_policy("any-plugin")
        assert result["allowed"] is True

    def test_block_plugin(self) -> None:
        ep = self.make_ep()
        ep.block_plugin("bad-plugin", "Security risk")
        result = ep.check_install_policy("bad-plugin")
        assert result["allowed"] is False
        assert "blocked" in result["reason"]

    def test_approve_plugin(self) -> None:
        ep = self.make_ep()
        ep.approve_plugin("good-plugin")
        assert ep.is_approved("good-plugin")
        assert not ep.is_blocked("good-plugin")

    def test_approved_list_only(self) -> None:
        ep = self.make_ep()
        ep._approved = ["only-this"]
        result = ep.check_install_policy("other-plugin")
        assert result["allowed"] is False

        result = ep.check_install_policy("only-this")
        assert result["allowed"] is True

    def test_mandatory_plugins(self) -> None:
        ep = self.make_ep()
        ep.set_mandatory("required-plugin")
        assert ep.is_mandatory("required-plugin")
        ep.remove_mandatory("required-plugin")
        assert not ep.is_mandatory("required-plugin")

    def test_audit_log(self) -> None:
        ep = self.make_ep()
        ep.approve_plugin("audited-plugin")
        log = ep.get_audit_log()
        assert len(log) >= 1
        assert log[-1].action == "approve"
        assert log[-1].plugin_id == "audited-plugin"

    def test_compliance_report(self) -> None:
        ep = self.make_ep()
        report = ep.get_compliance_report()
        assert "approved_count" in report
        assert "blocked_count" in report

    def test_block_removes_from_approved(self) -> None:
        ep = self.make_ep()
        ep.approve_plugin("test")
        ep.block_plugin("test", "Reason")
        assert not ep.is_approved("test")
        assert ep.is_blocked("test")


class TestCollaborationManager:
    def test_export_import_collection(self, tmp_path: Path) -> None:
        cm = CollaborationManager()
        output = str(tmp_path / "team-collection.json")
        path = cm.export_collection("team-plugins", ["p1", "p2"], output)
        assert os.path.isfile(path)
        plugin_ids = cm.import_collection(path)
        assert "p1" in plugin_ids
        assert "p2" in plugin_ids

    def test_list_collections(self) -> None:
        cm = CollaborationManager()
        collections = cm.list_collections()
        assert isinstance(collections, list)

    def test_import_nonexistent(self) -> None:
        cm = CollaborationManager()
        with pytest.raises(FileNotFoundError):
            cm.import_collection("/nonexistent/path.json")
