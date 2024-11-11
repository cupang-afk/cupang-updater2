import ast
import json
import re

import strictyaml as sy

from ...utils.date import parse_date_string
from ..base import DownloadInfo, ResourceData
from .base import PluginUpdater, PluginUpdaterConfig, PluginUpdaterConfigSchema


class ModrinthList(sy.Str):
    def is_valid_list(self, s):
        if not s.startswith("[") and not s.endswith("]"):
            return True
        try:
            ast.literal_eval(s)
            return True
        except (SyntaxError, ValueError):
            return False

    def validate_scalar(self, chunk):
        val = chunk.contents
        if not self.is_valid_list(val):
            chunk.expecting_but_found(
                "when expecting string, or a valid list for example \"['paper', 'folia']\","
                " also remember to encapsulate it in quotes"
            )
        return val


class ModrinthVersionType(sy.Str):
    def validate_scalar(self, chunk):
        val = chunk.contents
        if val.lower() not in ["release", "beta", "alpha"]:
            chunk.expecting_but_found(
                "when expecting one of ['release', 'beta', 'alpha']"
            )
        return val


class ModrinthUpdater(PluginUpdater):
    def __init__(self, plugin_data: ResourceData, updater_config: PluginUpdaterConfig):
        self.api = "https://api.modrinth.com/v2"
        super().__init__(plugin_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "Modrinth"

    @staticmethod
    def get_config_path():
        return "modrinth"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_config_schema():
        return PluginUpdaterConfigSchema(
            plugin_schema=sy.Map(
                {
                    "id": sy.EmptyNone() | sy.Str(),
                    "name_regex": sy.EmptyNone() | sy.Str(),
                    "loaders": sy.EmptyNone() | ModrinthList(),
                    "game_versions": sy.EmptyNone() | ModrinthList(),
                    "version_type": ModrinthVersionType(),
                }
            ),
            plugin_default="""\
                # id: https://modrinth.com/plugin/[your project id here]
                # name_regex: a regex search for the file name, example "Geyser-Spigot"
                # loaders: (optional) example paper, or for many loaders ["paper", "folia"]
                # game_versions: (optional) example 1.20.4, or for many game_versions ["1.20.4", "1.18.2"]
                # version_type: release, beta, or alpha
                id:
                name_regex:
                loaders:
                game_versions:
                version_type: release
            """,
        )

    def _is_valid_syntax(self, input: str):
        try:
            # Validate syntax using literal_eval
            output = ast.literal_eval(input)
        except (SyntaxError, ValueError):
            return False
        return output

    def _modrinth_params(self, text: str):
        if text.startswith("[") and text.endswith("]"):
            text = self._is_valid_syntax(text)
            if text:
                return "[" + ",".join([f'"{x}"' for x in text]) + "]"
        else:
            return f'["{text}"]'

    def _get_update_data(
        self,
        project_id: str,
        loaders: str = None,
        game_versions: str = None,
        version_type: str = None,
    ):
        # Prepare parameters for the Modrinth API request
        params = {}
        if loaders is not None:
            params["loaders"] = self._modrinth_params(loaders)
        if game_versions:
            params["game_versions"] = self._modrinth_params(game_versions)

        # Perform GET request to Modrinth API
        headers = {"Accept": "application/json"}
        res = self.make_requests(
            self.make_url(self.api, "project", project_id, "version", **params),
            headers=headers,
        )
        if not self.check_content_type(res, "application/json"):
            return

        # Convert the response to a list of release data
        list_release_data: list[dict] = json.loads(res.read())

        # Sort the release data by date_published for release versions
        date_sorted_project_data = {
            parse_date_string(x["date_published"]): x
            for x in list_release_data
            if str(x["version_type"]).lower() == version_type.lower()
        }
        # Set update_data to the latest release version
        return date_sorted_project_data[max(date_sorted_project_data.keys())]

    def get_update(self) -> DownloadInfo | None:
        project_id = self.updater_config.plugin_config["id"]
        if not project_id:
            return

        name_regex = self.updater_config.plugin_config.get("name_regex")
        if not name_regex:
            return

        loaders = self.updater_config.plugin_config.get("loaders")
        game_versions = self.updater_config.plugin_config.get("game_versions")
        version_type = self.updater_config.plugin_config.get("version_type")

        update_data = self._get_update_data(
            project_id, loaders, game_versions, version_type
        )
        if not update_data:
            return

        # Compare local and remote versions
        local_version = self.parse_version(self.plugin_data.version)
        remote_version = str(update_data["version_number"])
        if local_version >= self.parse_version(remote_version):
            return

        _name_regex = re.compile(name_regex)
        file = list(
            filter(lambda x: _name_regex.match(x["filename"]), update_data["files"])
        )
        if not file:
            return

        url = file[0].get("url")
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
