class MarketplaceError(Exception):
    pass


class RepositoryError(MarketplaceError):
    def __init__(self, repo_url: str, reason: str) -> None:
        self.repo_url = repo_url
        self.reason = reason
        super().__init__(f"Repository '{repo_url}' error: {reason}")


class PluginNotFoundError(MarketplaceError):
    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        super().__init__(f"Plugin not found in marketplace: {plugin_id}")


class VersionNotFoundError(MarketplaceError):
    def __init__(self, plugin_id: str, version: str) -> None:
        self.plugin_id = plugin_id
        self.version = version
        super().__init__(f"Version {version} not found for plugin '{plugin_id}'")


class DependencyError(MarketplaceError):
    def __init__(self, plugin_id: str, missing: str) -> None:
        self.plugin_id = plugin_id
        self.missing = missing
        super().__init__(f"Plugin '{plugin_id}' missing dependency: {missing}")


class CircularDependencyError(MarketplaceError):
    def __init__(self, chain: list[str]) -> None:
        self.chain = chain
        super().__init__(f"Circular dependency detected: {' -> '.join(chain)}")


class VerificationError(MarketplaceError):
    def __init__(self, plugin_id: str, reason: str) -> None:
        self.plugin_id = plugin_id
        self.reason = reason
        super().__init__(f"Verification failed for '{plugin_id}': {reason}")


class PolicyError(MarketplaceError):
    def __init__(self, plugin_id: str, policy: str) -> None:
        self.plugin_id = plugin_id
        self.policy = policy
        super().__init__(f"Plugin '{plugin_id}' blocked by policy: {policy}")


class EnterprisePolicyError(MarketplaceError):
    def __init__(self, policy: str, detail: str) -> None:
        self.policy = policy
        self.detail = detail
        super().__init__(f"Enterprise policy '{policy}': {detail}")
