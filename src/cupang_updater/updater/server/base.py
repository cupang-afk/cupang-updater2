from abc import abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from strictyaml.validators import MapValidator

from ...utils.common import reindent
from ..base import CommonData, UpdaterBase


@dataclass
class ServerUpdaterConfigSchema:
    """
    The schema for the configuration of a server updater.

    Attributes:
        common_schema (MapValidator): The schema for the common configuration.
        common_default (str): The default common configuration.
    """

    common_schema: MapValidator = field(default=None)
    common_default: str = field(default=None)

    def __post_init__(self):
        if self.common_default is not None:
            self.common_default = reindent(self.common_default, 0)
            if not isinstance(self.common_schema, MapValidator):
                raise TypeError("common_schema should be a MapValidator instance")


@dataclass
class ServerUpdaterConfig:
    """
    The configuration for a server updater.

    Attributes:
        common_config (dict[str, Any]): The common configuration for the server updater.
        server_config (dict[str, Any]): The configuration specific to the server (corresponds to server fields in config.yaml).
    """

    common_config: dict[str, Any] = field(default=None)
    server_config: dict[str, Any] = field(default=None)

    def __post_init__(self):
        self.common_config = self.common_config or {}
        self.server_config = self.server_config or {}

    def copy(self) -> "ServerUpdaterConfig":
        """
        Returns a deep copy of the configuration.

        Returns:
            ServerUpdaterConfig: A deep copy of the configuration.
        """
        return ServerUpdaterConfig(
            deepcopy(self.common_config), deepcopy(self.server_config)
        )


class ServerUpdater(UpdaterBase):
    """
    Abstract base class for updating servers.

    Subclasses must implement the following abstract methods:
        - get_server_types: Get the list of server types supported by this updater.
        - get_config_schema: Get the configuration schema for the server updater.
        - get_config_update: Get the default configuration for the server updater.
        - get_update: Get the latest update information for the server.

    Optional methods to implement:
        - get_config_update: Get the updated configuration for the server updater.
    """

    def __init__(self, server_data: CommonData, updater_config: ServerUpdaterConfig):
        """
        Initialize the server updater.

        Args:
            server_data (CommonData): The data about the server to update.
            updater_config (ServerUpdaterConfig): The configuration for the server updater.
        """
        self.server_data = server_data
        self.updater_config = updater_config
        super().__init__()

    @staticmethod
    @abstractmethod
    def get_server_types() -> list[str]:
        """
        Get the list of server types supported by this updater.

        Returns:
            list[str]: The list of server types supported by this updater.
        """
        ...

    @staticmethod
    @abstractmethod
    def get_config_schema() -> ServerUpdaterConfigSchema:
        """
        Get the configuration schema for the server updater.

        Returns:
            ServerUpdaterConfigSchema: The schema for the server updater configuration.
        """
        ...

    def get_config_update(self) -> ServerUpdaterConfig:
        """
        Get the updated configuration for the server updater.

        Returns:
            ServerUpdaterConfig: The default configuration for the server updater.
        """
        return ServerUpdaterConfig()

    @abstractmethod
    def get_update(self) -> CommonData | None:
        """
        Get the latest update information for the server.

        Returns:
            - CommonData | None: The latest server data, or None if an error occurred.

        Note:
            ensure the returned CommonData has the URL set using .set_url()
        """
        ...
