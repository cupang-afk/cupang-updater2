import json
import re

import strictyaml as sy

from ...utils.date import parse_date_timestamp
from ..base import DownloadInfo, ResourceData
from .base import PluginUpdater, PluginUpdaterConfig, PluginUpdaterConfigSchema


class BukkitUpdater(PluginUpdater):
    def __init__(self, plugin_data: ResourceData, updater_config: PluginUpdaterConfig):
        self.api = "https://api.curseforge.com/servermods"
        self.date_regex = re.compile(r"/Date\((\d+)\)/")
        super().__init__(plugin_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "Bukkit"

    @staticmethod
    def get_config_path():
        return "bukkit"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_config_schema():
        return PluginUpdaterConfigSchema(
            plugin_schema=sy.Map({"project_id": sy.EmptyNone() | sy.Int()}),
            plugin_default="""\
                # In "About This Project" section in the plugin's page, for example
                # for example 71561 for mythicmobs https://dev.bukkit.org/projects/mythicmobs
                project_id:
            """,
        )

    def _get_update(self, project_id: int) -> dict[str, str] | None:
        # Get the list of versions from the API
        headers = {"Accept": "application/json"}
        res = self.make_requests(
            self.make_url(self.api, "files", projectIds=project_id),
            headers=headers,
        )

        # Check if the response is valid
        if not self.check_content_type(res, "application/json"):
            return

        # Parse the response into a list of versions
        list_project_data: list[dict] = json.loads(res.read())

        if not list_project_data:
            return

        # Sort the list of versions by the date they were released
        sorted_list_project_data = sorted(
            list_project_data,
            key=(
                lambda x: parse_date_timestamp(
                    int(self.date_regex.search(x["dateReleased"]).group(1)) / 1000,
                )
            ),
            reverse=True,
        )

        # Return the latest version
        return sorted_list_project_data[0]

    def get_update(self) -> DownloadInfo | None:
        project_id = self.updater_config.plugin_config["project_id"]
        if not project_id:
            return

        latest_data = self._get_update(project_id)

        local_md5 = self.plugin_data.hashes.md5
        remote_md5 = latest_data.get("md5")
        if not self.has_new_version(local_md5, remote_md5, "!="):
            return

        url = latest_data.get("downloadUrl")
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

        return DownloadInfo(url)
