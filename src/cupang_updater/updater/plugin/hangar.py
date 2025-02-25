import json

import strictyaml as sy

from ..base import DownloadInfo, ResourceData
from .base import PluginUpdater, PluginUpdaterConfig, PluginUpdaterConfigSchema


class PlatformType(sy.Str):
    platform = ["paper", "waterfall", "velocity"]

    def validate_scalar(self, chunk):
        val: str = chunk.contents
        val = val.lower()
        if val not in self.platform:
            chunk.expecting_but_found(f"when expecting one of these: {self.platform}")
        return super().validate_scalar(chunk)


class Channel(sy.Str):
    channel = ["release", "snapshot", "alpha"]

    def validate_scalar(self, chunk):
        val: str = chunk.contents
        if val not in self.channel:
            chunk.expecting_but_found(f"when expecting one of these: {self.channel}")

        return super().validate_scalar(chunk)


class HangarUpdater(PluginUpdater):
    def __init__(self, plugin_data: ResourceData, updater_config: PluginUpdaterConfig):
        self.api = "https://hangar.papermc.io/api/v1/projects"
        super().__init__(plugin_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "Hangar"

    @staticmethod
    def get_config_path():
        return "hangar"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_config_schema():
        return PluginUpdaterConfigSchema(
            plugin_schema=sy.Map(
                {
                    "id": sy.EmptyNone() | sy.Str(),
                    "platform": sy.EmptyNone() | PlatformType() | sy.Str(),
                    "channel": Channel(),
                }
            ),
            plugin_default="""\
                # id: example https://hangar.papermc.io/[author]/[your project id here]
                # platform: paper, waterfall, or velocity
                # channel: e.g. release, snapshot, or alpha
                id:
                platform: paper
                channel: release
            """,
        )

    def _get_update_data(self, project_id: str, channel: str):
        headers = {"Accept": "text/plain"}
        res = self.make_requests(
            self.make_url(
                self.api, project_id, "latest", channel=channel.lower().capitalize()
            ),
            headers=headers,
        )
        if not self.check_content_type(res, "text/plain"):
            return

        latest_version = res.read().decode().strip()
        headers = {"Accept": "application/json"}
        res = self.make_requests(
            self.make_url(self.api, project_id, "versions", latest_version),
            headers=headers,
        )
        if not self.check_content_type(res, "application/json"):
            return

        return json.loads(res.read())

    def get_update(self) -> DownloadInfo | None:
        project_id: str = self.updater_config.plugin_config["id"]
        platform: str = self.updater_config.plugin_config["platform"]
        channel: str = self.updater_config.plugin_config["channel"]
        if not (project_id and platform and channel):
            return

        update_data = self._get_update_data(project_id, channel)
        if not update_data:
            return

        # Compare local and remote versions
        local_version = self.parse_version(self.plugin_data.version)
        remote_version = self.parse_version(str(update_data["name"]))
        if not self.has_new_version(local_version, remote_version):
            return

        url = self.make_url(
            self.api,
            project_id,
            "versions",
            update_data["name"],
            platform.upper(),
            "download",
        )

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
