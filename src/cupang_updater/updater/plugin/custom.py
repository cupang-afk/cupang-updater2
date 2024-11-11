import strictyaml as sy

from ..base import DownloadInfo
from .base import PluginUpdater, PluginUpdaterConfigSchema


class CustomUrlPluginUpdater(PluginUpdater):
    @staticmethod
    def get_updater_name():
        return "Custom URL"

    @staticmethod
    def get_config_path():
        return "custom_url"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_config_schema():
        return PluginUpdaterConfigSchema(
            plugin_schema=sy.Map({"url": sy.EmptyNone() | sy.Str()}),
            plugin_default="""\
                # Set download url (must point to a file url)
                url:
            """,
        )

    def get_update(self) -> DownloadInfo | None:
        url = self.updater_config.plugin_config["url"]
        if not url:
            return

        with self.make_requests(url, method="HEAD") as res:
            if not any(
                self.check_content_type(res, x)
                for x in [
                    "application/java-archive",
                    "application/octet-stream",
                    "application/zip",
                ]
            ):
                self.log.error(
                    f"When checking update for {self.plugin_data.name}, got {url} but its not a file"
                )
                return

        return DownloadInfo(url)
