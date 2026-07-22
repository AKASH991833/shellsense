from shellsense.plugins import PluginBase


class DockerHelperPlugin(PluginBase):
    def on_load(self) -> None:
        self._api.log.info("Docker Helper loaded")

    def on_enable(self) -> None:
        self._api.log.info("Docker Helper enabled")

    def on_disable(self) -> None:
        self._api.log.info("Docker Helper disabled")
