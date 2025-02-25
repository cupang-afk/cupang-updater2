from ..base import DownloadInfo, ResourceData
from ..common_api.jenkins import JenkinsAPI
from .base import ServerUpdater, ServerUpdaterConfig, ServerUpdaterConfigSchema


class BungeeUpdater(ServerUpdater):
    def __init__(self, server_data: ResourceData, updater_config: ServerUpdaterConfig):
        self.api = "https://ci.md-5.net/job/Bungeecord"
        self.new_updater_config = ServerUpdaterConfig()
        super().__init__(server_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "BungeeCord"

    @staticmethod
    def get_config_path():
        return "bungee"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_server_types() -> list[str]:
        return ["bungee"]

    @staticmethod
    def get_config_schema():
        return ServerUpdaterConfigSchema()

    def get_config_update(self):
        return self.new_updater_config

    def get_update(self) -> DownloadInfo | None:
        server_type = self.updater_config.server_config["type"]
        server_version = self.updater_config.server_config["version"]
        match self.parse_version(server_version):
            case v if v <= self.parse_version("1.7.10"):
                get_build_number = 1119
            case v if v <= self.parse_version("1.6.4"):
                get_build_number = 701
            case v if v <= self.parse_version("1.6.2"):
                get_build_number = 666
            case v if v <= self.parse_version("1.5.2"):
                get_build_number = 548
            case v if v <= self.parse_version("1.5.0"):
                get_build_number = 386
            case v if v <= self.parse_version("1.4.7"):
                get_build_number = 251
            case _:
                get_build_number = -1

        api = JenkinsAPI(self.api)
        api_build_data, api_build_number = api.get_build_data(get_build_number)
        api_artifact_data = api.get_artifact_data(api_build_data, "BungeeCord")
        if not (api_build_data and api_artifact_data):
            return

        local_build_number = self.updater_config.server_config["build_number"] or 0
        remote_build_number = api_build_number
        if not self.has_new_version(local_build_number, remote_build_number):
            return

        url = api.get_artifact_url(api_artifact_data, api_build_number)
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

        self.new_updater_config.server_config["build_number"] = remote_build_number
        return DownloadInfo(url)
