from abc import abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from strictyaml.validators import MapValidator

from ...utils.common import reindent
from ..base import ResourceData, UpdaterBase


@dataclass
class ServerUpdaterConfigSchema:
    """
    Defines the schema for the configuration of a server updater.

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
    Configuration for a server updater.

    Attributes:
        common_config (dict[str, Any]): Common configuration for the server updater.
        server_config (dict[str, Any]): Configuration specific to the server
            (corresponds to server fields in config.yaml).
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
        - get_server_types: Retrieve the list of server types this updater supports.
        - get_config_schema: Retrieve the configuration schema for the server updater.
        - get_update: Retrieve the latest update information for the server.

    Optional methods to implement:
        - get_config_update: Retrieve the updated configuration for the server updater.

    Note:
        See UpdaterBase class for inherited functionality.
    """

    def __init__(self, server_data: ResourceData, updater_config: ServerUpdaterConfig):
        """
        Initialize the server updater.

        Args:
            server_data (ResourceData): Information about the server to be updated.
            updater_config (ServerUpdaterConfig): Configuration specifics
                for the server updater.
        """
        self.server_data = server_data
        self.updater_config = updater_config
        super().__init__()

    @staticmethod
    @abstractmethod
    def get_server_types() -> list[str]:
        """
        Retrieve the list of server types this updater supports.

        Returns:
            list[str]: Supported server types.
        """
        ...

    @staticmethod
    @abstractmethod
    def get_config_schema() -> ServerUpdaterConfigSchema:
        """
        Retrieve the configuration schema for the server updater.

        Returns:
            ServerUpdaterConfigSchema: Schema defining server updater configuration.
        """
        ...

    def get_config_update(self) -> ServerUpdaterConfig:
        """
        Retrieve the updated configuration for the server updater.

        Returns:
            ServerUpdaterConfig: Default configuration for the server updater.
        """
        return ServerUpdaterConfig()
