from ..base import DownloadInfo
from .base import ServerUpdater, ServerUpdaterConfigSchema


class CustomUrlServerUpdater(ServerUpdater):
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
    def get_server_types() -> list[str]:
        return ["custom"]

    @staticmethod
    def get_config_schema():
        return ServerUpdaterConfigSchema()

    def get_update(self) -> DownloadInfo | None:
        server_type = self.updater_config.server_config["type"]
        url = self.updater_config.server_config["custom_url"]
        if not url:
            return

        if not self.check_valid_content_types(
            url,
            f"[{self.get_updater_name()}] {server_type}",
            [
                "application/java-archive",
                "application/octet-stream",
                "application/zip",
            ],
        ):
            return

        return DownloadInfo(url)
