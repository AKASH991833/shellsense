from shellsense.plugins import PluginBase


class SystemMonitorPlugin(PluginBase):
    def on_load(self) -> None:
        self._api.log.info("System Monitor loaded")

    def on_enable(self) -> None:
        self._api.log.info("System Monitor enabled")

    def on_disable(self) -> None:
        self._api.log.info("System Monitor disabled")
