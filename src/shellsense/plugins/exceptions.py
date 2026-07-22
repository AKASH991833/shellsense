class PluginError(Exception):
    pass


class PluginNotFoundError(PluginError):
    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        super().__init__(f"Plugin not found: {plugin_id}")


class PluginLoadError(PluginError):
    def __init__(self, plugin_id: str, reason: str) -> None:
        self.plugin_id = plugin_id
        self.reason = reason
        super().__init__(f"Failed to load plugin '{plugin_id}': {reason}")


class PluginCompatibilityError(PluginError):
    def __init__(self, plugin_id: str, version: str, required: str) -> None:
        self.plugin_id = plugin_id
        self.plugin_version = version
        self.required = required
        super().__init__(
            f"Plugin '{plugin_id}' v{version} requires ShellSense >= {required}"
        )


class PluginPermissionError(PluginError):
    def __init__(self, plugin_id: str, permission: str) -> None:
        self.plugin_id = plugin_id
        self.permission = permission
        super().__init__(
            f"Plugin '{plugin_id}' lacks required permission: {permission}"
        )


class PluginHookError(PluginError):
    def __init__(self, plugin_id: str, hook: str, reason: str) -> None:
        self.plugin_id = plugin_id
        self.hook = hook
        self.reason = reason
        super().__init__(f"Plugin '{plugin_id}' hook '{hook}' failed: {reason}")


class PluginDependencyError(PluginError):
    def __init__(self, plugin_id: str, missing_dep: str) -> None:
        self.plugin_id = plugin_id
        self.missing_dep = missing_dep
        super().__init__(f"Plugin '{plugin_id}' missing dependency: {missing_dep}")
