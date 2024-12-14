import json
from typing import Any

from ..base import DownloadInfo, ResourceData
from .base import ServerUpdater, ServerUpdaterConfig, ServerUpdaterConfigSchema


class PurpurUpdater(ServerUpdater):
    def __init__(self, server_data: ResourceData, updater_config: ServerUpdaterConfig):
        self.api = "https://api.purpurmc.org/v2/purpur"
        self.new_updater_config = ServerUpdaterConfig()
        super().__init__(server_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "PurpurMC"

    @staticmethod
    def get_config_path():
        return "purpur"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_server_types() -> list[str]:
        return ["purpur"]

    @staticmethod
    def get_config_schema():
        return ServerUpdaterConfigSchema()

    def get_config_update(self):
        return self.new_updater_config

    def _get_update_data(self, server_version: str) -> dict[str, Any] | None:
        headers = {"Accept": "application/json"}
        res = self.make_requests(
            self.make_url(self.api, server_version),
            headers=headers,
        )
        if not self.check_content_type(res, "application/json"):
            return

        return json.loads(res.read())

    def get_update(self) -> DownloadInfo | None:
        server_version = self.updater_config.server_config["version"]
        update_data = self._get_update_data(server_version)
        if not update_data:
            return

        local_build_number = self.updater_config.server_config["build_number"] or 0
        remote_build_number = int(update_data["builds"]["latest"])
        if not self.has_new_version(local_build_number, remote_build_number):
            return

        url = self.make_url(
            self.api,
            server_version,
            remote_build_number,
            "download",
        )
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

        self.new_updater_config.server_config["build_number"] = remote_build_number
        return DownloadInfo(url)
