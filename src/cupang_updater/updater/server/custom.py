from ..base import CommonData
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

    def get_update(self) -> CommonData | None:
        url = self.updater_config.server_config["custom_url"]
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
                    f"When checking update for {self.get_updater_name()}, got {url} but its not a file"
                )
                return

        server_data = CommonData(
            name=self.get_updater_name(),
            version="",
        )
        server_data.set_url(url)
        return server_data
