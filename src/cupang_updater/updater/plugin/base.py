from abc import abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from strictyaml.validators import MapValidator

from ...utils.common import reindent
from ..base import CommonData, UpdaterBase


@dataclass
class PluginUpdaterConfigSchema:
    """
    Schema configuration for a plugin updater.

    Attributes:
        common_schema (MapValidator): Validator for common configuration.
        common_default (str): Default value for common configuration.
        plugin_schema (MapValidator): Validator for plugin-specific configuration.
        plugin_default (str): Default value for plugin-specific configuration.
    """

    common_schema: MapValidator = field(default=None)
    common_default: str = field(default=None)
    plugin_schema: MapValidator = field(default=None)
    plugin_default: str = field(default=None)

    def __post_init__(self):
        if self.common_default is not None:
            self.common_default = reindent(self.common_default, 0)
            if not isinstance(self.common_schema, MapValidator):
                raise TypeError("common_schema should be a MapValidator instance")
        if self.plugin_default is not None:
            self.plugin_default = reindent(self.plugin_default, 0)
            if not isinstance(self.plugin_schema, MapValidator):
                raise TypeError("plugin_schema should be a MapValidator instance")


@dataclass
class PluginUpdaterConfig:
    """
    Configuration for a plugin updater.

    Attributes:
        common_config (dict[str, Any]): Common configuration for the plugin updater.
        plugin_config (dict[str, Any]): Plugin-specific configuration for the plugin updater.
    """

    common_config: dict[str, Any] = field(default=None)
    plugin_config: dict[str, Any] = field(default=None)

    def __post_init__(self):
        self.common_config = self.common_config or {}
        self.plugin_config = self.plugin_config or {}

    def copy(self) -> "PluginUpdaterConfig":
        return PluginUpdaterConfig(
            deepcopy(self.common_config), deepcopy(self.plugin_config)
        )


class PluginUpdater(UpdaterBase):
    """
    Abstract base class for updating plugins.

    Subclasses must implement the following abstract methods:
        - get_config_schema: Get the configuration schema for the plugin updater.
        - get_update: Get the latest update information for the plugin.

    Optional methods to implement:
        - get_config_update: Get the updated configuration for the plugin updater.
    """

    def __init__(self, plugin_data: CommonData, updater_config: PluginUpdaterConfig):
        """
        Initialize the plugin updater.

        Args:
            plugin_data (CommonData): The information about the plugin to update.
            updater_config (PluginUpdaterConfig): The configuration for the plugin updater.
        """
        self.plugin_data = plugin_data
        self.updater_config = updater_config
        super().__init__()

    @staticmethod
    @abstractmethod
    def get_config_schema() -> PluginUpdaterConfigSchema:
        """
        Get the configuration schema for the plugin updater.

        Returns:
            PluginUpdaterConfigSchema: The schema for the plugin updater configuration.
        """
        ...

    def get_config_update(self) -> PluginUpdaterConfig:
        """
        Get the updated configuration for the plugin updater.

        Returns:
            PluginUpdaterConfig: The default configuration for the plugin updater.
        """
        return PluginUpdaterConfig()

    @abstractmethod
    def get_update(self) -> CommonData | None:
        """
        Get the latest update information for the plugin.

        Returns:
            - CommonData | None: The latest plugin data, or None if an error occurred.

        Note:
            ensure the returned CommonData has the URL set using .set_url()
        """
        ...
