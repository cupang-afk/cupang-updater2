from typing import Any

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

    def _get_git_data(
        self, api: GithubAPI, prerelease: bool, name_regex: str
    ) -> None | tuple[list[dict[str, Any]], dict[str, Any], str]:
        _null = [None, None, None]
        api_release_data = api.get_releases_data(
            _filter="prerelease" if prerelease else "release"
        )
        if not api_release_data:
            return _null
        api_release_data = api_release_data[0]
        api_tag_data = api.get_tag_data(api_release_data["tag_name"])
        if not api_tag_data:
            return _null
        api_asset_data = api.get_asset_data(api_release_data, name_regex)
        if not api_asset_data:
            return _null

        return api_release_data, api_tag_data, api_asset_data

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

        api = GithubAPI(repo, self.token)
        api_release_data, api_tag_data, api_asset_data = self._get_git_data(
            api, prerelease, name_regex
        )
        if any(not x for x in [api_release_data, api_tag_data, api_asset_data]):
            return

        commit = ""
        if compare_to == "commit":
            local_commit = self.updater_config.plugin_config.get("commit")
            remote_commit = api.get_commit_sha(api_tag_data)
            if not self.has_new_version(local_commit, remote_commit, "!="):
                return
            commit = remote_commit
        else:
            local_version = self.parse_version(self.plugin_data.version)
            match compare_to:
                case "tags":
                    remote_version = self.parse_version(api_release_data["tag_name"])
                case "release_name":
                    remote_version = self.parse_version(api_release_data["name"])
                case "file_name":
                    remote_version = self.parse_version(api_asset_data["name"])
                case _:
                    remote_version = self.parse_version("1.0")
            if not self.has_new_version(local_version, remote_version):
                return

        url = api.get_asset_url(api_asset_data)
        if not url:
            return

        if not self.check_valid_content_types(
            url,
            self.plugin_data.name,
            [
                "application/java-archive",
                "application/octet-stream",
                "application/zip",
            ],
        ):
            return

        self.new_updater_config.plugin_config["commit"] = (
            remote_commit if compare_to == "commit" else ""
        )
        return DownloadInfo(url, {"Authorization": f"Bearer {self.token}"})
