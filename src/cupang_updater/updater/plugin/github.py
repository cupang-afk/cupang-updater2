import strictyaml as sy

from ..base import DownloadInfo, ResourceData
from ..common_api.github import GithubAPI
from .base import PluginUpdater, PluginUpdaterConfig, PluginUpdaterConfigSchema


class CompareToType(sy.Str):
    compare_to = ["commit", "tags", "release_name", "file_name"]

    def validate_scalar(self, chunk):
        val = chunk.contents
        if val.lower() not in self.compare_to:
            chunk.expecting_but_found(f"when expecting one of {self.compare_to}")
        return val


class GithubUpdater(PluginUpdater):
    def __init__(self, plugin_data: ResourceData, updater_config: PluginUpdaterConfig):
        self.token = updater_config.common_config.get("token")
        self.new_updater_config = PluginUpdaterConfig()
        super().__init__(plugin_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "Github"

    @staticmethod
    def get_config_path():
        return "github"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_config_schema():
        return PluginUpdaterConfigSchema(
            common_schema=sy.Map({"token": sy.EmptyNone() | sy.Str()}),
            common_default="""\
                token: # github token
            """,
            plugin_schema=sy.Map(
                {
                    "repo": sy.EmptyNone() | sy.Str(),
                    "name_regex": sy.EmptyNone() | sy.Str(),
                    "prerelease": sy.Bool(),
                    "commit": sy.EmptyNone() | sy.Str(),
                    "compare_to": CompareToType(),
                }
            ),
            plugin_default="""\
                # repo: format is "user/repository" for example "EssentialsX/Essentials"
                # name_regex: a regex search for the file name, example "Geyser-Spigot"
                # prerelease: true to get prerelease version
                # commit: auto generate
                # compare_to: commit, tags, release_name, or file_name
                repo: 
                name_regex: 
                prerelease: false
                commit: 
                compare_to: tags 
            """,
        )

    def get_config_update(self) -> PluginUpdaterConfig:
        return self.new_updater_config

    def get_update(self) -> DownloadInfo | None:
        repo = self.updater_config.plugin_config.get("repo")
        if not repo:
            return

        name_regex = self.updater_config.plugin_config.get("name_regex")
        if not name_regex:
            return

        compare_to = self.updater_config.plugin_config.get("compare_to")
        if not compare_to:
            return

        prerelease = self.updater_config.plugin_config.get("prerelease", False)

        api = GithubAPI(repo, prerelease, self.token)

        commit = ""
        if compare_to == "commit":
            local_commit = self.updater_config.plugin_config.get("commit")
            remote_commit = api.get_commit()
            if local_commit == remote_commit:
                return
            commit = remote_commit
        else:
            local_version = self.parse_version(self.plugin_data.version)
            match compare_to:
                case "tags":
                    remote_version = self.parse_version(api.get_tag())
                case "release_name":
                    remote_version = self.parse_version(api.get_release_name())
                case "file_name":
                    remote_version = self.parse_version(api.get_file_name(name_regex))
                case _:
                    remote_version = self.parse_version("1.0")
            if local_version >= remote_version:
                return

        url = api.get_asset_url(name_regex)
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

        self.new_updater_config.plugin_config["commit"] = commit
        return DownloadInfo(url, {"Authorization": f"Bearer {self.token}"})
