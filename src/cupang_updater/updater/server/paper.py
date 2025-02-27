import json

from ..base import DownloadInfo, ResourceData
from .base import ServerUpdater, ServerUpdaterConfig, ServerUpdaterConfigSchema


class PaperUpdater(ServerUpdater):
    def __init__(self, server_data: ResourceData, updater_config: ServerUpdaterConfig):
        self.api = "https://api.papermc.io/v2/projects"
        self.new_updater_config = ServerUpdaterConfig()
        super().__init__(server_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "PaperMC"

    @staticmethod
    def get_config_path():
        return "papermc"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_server_types() -> list[str]:
        return ["paper", "waterfall", "velocity", "folia"]

    @staticmethod
    def get_config_schema():
        return ServerUpdaterConfigSchema()

    def get_config_update(self):
        return self.new_updater_config

    def _get_update_data(self, server_type: str, server_version: str):
        headers = {"Accept": "application/json"}
        res = self.make_requests(
            self.make_url(
                self.api,
                server_type,
                "versions",
                server_version,
            ),
            headers=headers,
        )
        if not self.check_content_type(res, "application/json"):
            return

        version_data: dict = json.loads(res.read())
        latest_build: int = max(version_data["builds"])

        res = self.make_requests(
            self.make_url(
                self.api,
                server_type,
                "versions",
                server_version,
                "builds",
                latest_build,
            ),
            headers=headers,
        )
        if not self.check_content_type(res, "application/json"):
            return

        builds_data: dict = json.loads(res.read())
        return builds_data

    def get_update(self) -> DownloadInfo | None:
        server_type = self.updater_config.server_config["type"]
        server_version = self.updater_config.server_config["version"]
        update_data = self._get_update_data(
            server_type,
            server_version,
        )
        if not update_data:
            return

        local_sha256 = self.server_data.hashes.sha256
        remote_sha256 = update_data["downloads"]["application"]["sha256"]
        if not self.has_new_version(local_sha256, remote_sha256, "!="):
            return

        remote_build_number = update_data["build"]

        url = self.make_url(
            self.api,
            server_type,
            "versions",
            server_version,
            "builds",
            remote_build_number,
            "downloads",
            f"{server_type}-{server_version}-{remote_build_number}.jar",
        )

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

        self.new_updater_config.server_config["build_number"] = update_data["build"]
        return DownloadInfo(url)
