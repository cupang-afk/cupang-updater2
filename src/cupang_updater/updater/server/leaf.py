import strictyaml as sy

from ..base import DownloadInfo, ResourceData
from ..common_api.github import GithubAPI
from .base import (
    ServerUpdater,
    ServerUpdaterConfig,
    ServerUpdaterConfigSchema,
)


class LeafUpdater(ServerUpdater):
    def __init__(self, server_data: ResourceData, updater_config: ServerUpdaterConfig):
        self.token = updater_config.common_config.get("token")
        self.new_updater_config = ServerUpdaterConfig()
        super().__init__(server_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "LeafMC"

    @staticmethod
    def get_config_path():
        return "leaf"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_server_types() -> list[str]:
        return ["leaf"]

    @staticmethod
    def get_config_schema():
        return ServerUpdaterConfigSchema(
            common_schema=sy.Map(
                {
                    "token": sy.EmptyNone() | sy.Str(),
                    "commit": sy.EmptyNone() | sy.Str(),
                }
            ),
            common_default="""\
                token: # github token
                commit: # auto generate
            """,
        )

    def get_config_update(self):
        return self.new_updater_config

    def get_update(self) -> DownloadInfo | None:
        server_type = self.updater_config.server_config["type"]
        server_version = self.updater_config.server_config["version"]
        repo = "Winds-Studio/Leaf"
        name_regex = r"leaf\-[0-9.]+\.jar"

        api = GithubAPI(repo, self.token)
        api_release_data = api.get_release_data(f"ver-{server_version}")
        if not api_release_data:
            return
        api_tag_data = api.get_tag_data(api_release_data["tag_name"])
        if not api_tag_data:
            return
        api_asset_data = api.get_asset_data(api_release_data, name_regex)
        if not api_asset_data:
            return

        local_commit = self.updater_config.common_config.get("commit")
        remote_commit = api.get_commit_sha(api_tag_data)
        if self.has_new_version(local_commit, remote_commit, "=="):
            return None

        url = api.get_asset_url(api_asset_data)
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

        self.new_updater_config.common_config["commit"] = remote_commit
        return DownloadInfo(url, {"Authorization": f"Bearer {self.token}"})
