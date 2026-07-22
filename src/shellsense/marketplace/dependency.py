from __future__ import annotations

from typing import Any

from shellsense.marketplace.models import DependencyGraph
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class DependencyResolver:
    def resolve(
        self,
        plugin_id: str,
        dependencies: dict[str, str],
        all_plugins: dict[str, dict[str, Any]],
        visited: set[str] | None = None,
    ) -> DependencyGraph:
        graph = DependencyGraph()
        visited = visited or set()
        visited.add(plugin_id)
        graph.nodes.append(plugin_id)

        for dep_id, dep_version in dependencies.items():
            if dep_id in visited:
                graph.circular.append([plugin_id, dep_id])
                if dep_id not in graph.edges:
                    graph.edges[dep_id] = []
                if dep_id not in graph.nodes:
                    graph.nodes.append(dep_id)
                graph.edges[plugin_id] = graph.edges.get(plugin_id, []) + [dep_id]
                continue
            if dep_id not in graph.nodes:
                graph.nodes.append(dep_id)
            if dep_id not in graph.edges:
                graph.edges[dep_id] = []
            graph.edges[plugin_id] = graph.edges.get(plugin_id, []) + [dep_id]

            if dep_id not in all_plugins:
                graph.missing.append(dep_id)
                continue

            dep_data = all_plugins[dep_id]
            sub_deps = dep_data.get("dependencies", {})
            if isinstance(sub_deps, dict) and sub_deps:
                sub_visited = visited.copy()
                sub_graph = self.resolve(dep_id, sub_deps, all_plugins, sub_visited)
                graph.missing.extend(sub_graph.missing)
                graph.circular.extend(sub_graph.circular)
                for n in sub_graph.nodes:
                    if n not in graph.nodes:
                        graph.nodes.append(n)
                for src, tgts in sub_graph.edges.items():
                    if src not in graph.edges:
                        graph.edges[src] = []
                    graph.edges[src].extend(
                        t for t in tgts if t not in graph.edges.get(src, [])
                    )

        graph.circular = self._detect_circular(graph.nodes, graph.edges)
        if graph.circular:
            logger.warning("Circular dependencies detected: %s", graph.circular)

        graph.resolution_order = self._topological_sort(graph.nodes, graph.edges)
        return graph

    def check_conflicts(
        self, plugin_id: str, dependencies: dict[str, str], installed: dict[str, str]
    ) -> list[str]:
        conflicts: list[str] = []
        for dep_id, required_version in dependencies.items():
            if dep_id in installed:
                installed_version = installed[dep_id]
                if required_version and installed_version != required_version:
                    conflicts.append(
                        f"{dep_id}: required {required_version}, installed {installed_version}"
                    )
        return conflicts

    def _detect_circular(
        self, nodes: list[str], edges: dict[str, list[str]]
    ) -> list[list[str]]:
        visited: set[str] = set()
        path: list[str] = []
        cycles: list[list[str]] = []

        def dfs(node: str) -> None:
            if node in path:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for neighbor in edges.get(node, []):
                if neighbor in nodes:
                    dfs(neighbor)
            path.pop()

        for node in nodes:
            dfs(node)
        return cycles

    def _topological_sort(
        self, nodes: list[str], edges: dict[str, list[str]]
    ) -> list[str]:
        in_degree: dict[str, int] = {n: 0 for n in nodes}
        for src in edges:
            for tgt in edges[src]:
                if tgt in in_degree:
                    in_degree[tgt] += 1

        queue = [n for n in nodes if in_degree.get(n, 0) == 0]
        result: list[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in edges.get(node, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        remaining = [n for n in nodes if n not in result]
        result.extend(remaining)
        return result
