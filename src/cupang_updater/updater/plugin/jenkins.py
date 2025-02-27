import strictyaml as sy

from ..base import DownloadInfo, ResourceData
from ..common_api.jenkins import JenkinsAPI
from .base import PluginUpdater, PluginUpdaterConfig, PluginUpdaterConfigSchema


class JenkinsUpdater(PluginUpdater):
    def __init__(self, plugin_data: ResourceData, updater_config: PluginUpdaterConfig):
        self.new_updater_config = PluginUpdaterConfig()
        super().__init__(plugin_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "Jenkins"

    @staticmethod
    def get_config_path():
        return "jenkins"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_config_schema():
        return PluginUpdaterConfigSchema(
            plugin_schema=sy.Map(
                {
                    "url": sy.EmptyNone() | sy.Url(),
                    "name_regex": sy.EmptyNone() | sy.Str(),
                    "build_number": sy.EmptyNone() | sy.Int(),
                }
            ),
            plugin_default="""\
                # url: jenkins url
                # name_regex: a regex search for the file name, example "Geyser-Spigot"
                # build_number: auto generate
                url:
                name_regex:
                build_number:
            """,
        )

    def get_config_update(self) -> PluginUpdaterConfig:
        return self.new_updater_config

    def get_update(self) -> DownloadInfo | None:
        jenkins_url = self.updater_config.plugin_config.get("url")
        name_regex = self.updater_config.plugin_config.get("name_regex")
        if not (jenkins_url and name_regex):
            return

        api = JenkinsAPI(jenkins_url)
        api_build_data, api_build_number = api.get_build_data()
        api_artifact_data = api.get_artifact_data(api_build_data, name_regex)
        if not (api_build_data and api_artifact_data):
            return

        local_build_number = (
            self.updater_config.plugin_config.get("build_number", 0) or 0
        )
        remote_build_number = api_build_number
        if not self.has_new_version(local_build_number, remote_build_number):
            return

        url = api.get_artifact_url(api_artifact_data, api_build_number)
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

        self.new_updater_config.plugin_config["build_number"] = remote_build_number
        return DownloadInfo(url)
