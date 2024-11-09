import json

import strictyaml as sy

from ..base import CommonData, Hashes
from .base import PluginUpdater, PluginUpdaterConfig, PluginUpdaterConfigSchema


class SpigotUpdater(PluginUpdater):
    def __init__(self, plugin_data: CommonData, updater_config: PluginUpdaterConfig):
        self.api = "https://api.spiget.org/v2"
        super().__init__(plugin_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "Spigot"

    @staticmethod
    def get_config_path():
        return "spigot"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_config_schema():
        return PluginUpdaterConfigSchema(
            plugin_schema=sy.Map({"resource_id": sy.EmptyNone() | sy.Int()}),
            plugin_default="""\
                # In spigotmc url
                # for example: 18494 for discordsrv https://www.spigotmc.org/resources/discordsrv.18494/
                resource_id:
            """,
        )

    def _is_premium(self, resource_id: int):
        headers = {"Accept": "application/json"}
        res = self.make_requests(
            self.make_url(self.api, "resources", resource_id),
            headers=headers,
        )
        if not self.check_content_type(res, "application/json"):
            return

        return json.loads(res.read())["premium"]

    def _get_version(self, resource_id: int):
        headers = {"Accept": "application/json"}
        res = self.make_requests(
            self.make_url(self.api, "resources", resource_id, "versions", "latest"),
            headers=headers,
        )
        if not self.check_content_type(res, "application/json"):
            return

        return json.loads(res.read())["name"]

    def get_update(self):
        resource_id = self.updater_config.plugin_config["resource_id"]
        if not resource_id:
            return

        is_premium = self._is_premium(resource_id)
        if is_premium:
            self.log.info(
                f"Plugin {self.plugin_data.name} is premium\n"
                f"Download it yourself at https://www.spigotmc.org/resources/{resource_id}"
            )
            return

        local_version = self.parse_version(self.plugin_data.version)
        remote_version = str(self._get_version(resource_id))
        if local_version >= self.parse_version(remote_version):
            return

        url = self.make_url(self.api, "resources", resource_id, "download")
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

        self.plugin_data.version = remote_version
        plugin_data = CommonData(
            name=self.plugin_data.name,
            version=remote_version,
            hashes=Hashes(),
        )
        plugin_data.set_url(url)
        return plugin_data
