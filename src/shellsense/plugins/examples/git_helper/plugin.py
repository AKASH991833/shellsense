from shellsense.plugins import PluginBase


class GitHelperPlugin(PluginBase):
    def on_load(self) -> None:
        self._api.log.info("Git Helper loaded")

    def on_enable(self) -> None:
        self._api.log.info("Git Helper enabled")

    def on_disable(self) -> None:
        self._api.log.info("Git Helper disabled")

    def on_startup(self) -> None:
        self._api.log.info("Git Helper ready")
