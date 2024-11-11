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
        self.log.info(
            f'Using {self.get_updater_name()} updater will ignore "version" (if set)'
        )

        api = JenkinsAPI(self.api)
        local_build_number = self.updater_config.server_config["build_number"] or 0
        remote_build_number = api.get_build_number()
        if local_build_number >= remote_build_number:
            return

        url = api.get_artifact_url("BungeeCord")
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

        self.new_updater_config.server_config["build_number"] = remote_build_number
        return DownloadInfo(url)
