import logging
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Literal, Protocol, TypeVar, final

from ..cmd_opts import get_cmd_opts
from ..logger.logger import get_logger
from ..meta import default_headers
from ..utils.common import parse_version
from ..utils.hash import FileHash, Hashes
from ..utils.url import check_content_type, make_requests, make_url

T = TypeVar("T", bound="_Comparable")

_compare = {
    "==": lambda x, y: x == y,
    "!=": lambda x, y: x != y,
    "<": lambda x, y: x < y,
    "<=": lambda x, y: x <= y,
    ">": lambda x, y: x > y,
    ">=": lambda x, y: x >= y,
}


class _Comparable(Protocol):
    def __eq__(self: T, other: T) -> bool: ...
    def __ne__(self: T, other: T) -> bool: ...
    def __lt__(self: T, other: T) -> bool: ...
    def __le__(self: T, other: T) -> bool: ...
    def __gt__(self: T, other: T) -> bool: ...
    def __ge__(self: T, other: T) -> bool: ...


@dataclass
class ResourceData:
    """
    Represents the data associated with a resource, such as a plugin or server.

    Attributes:
        name (str): The name of the plugin or server type.
        version (str): The version of the resource.
        hashes (FileHash | Hashes): The hash values associated with the resource.
    """

    name: str
    version: str
    hashes: FileHash | Hashes = field(default_factory=Hashes)


@dataclass
class DownloadInfo:
    """
    Represents the information required to download a file, including
    the URL of the file and any additional HTTP headers to send with the request.

    Attributes:
        url (str): The URL of the file.
        headers (dict[str, str], optional): Additional HTTP headers to send with the request.
    """

    url: str
    headers: dict[str, str] = field(default=None)

    def __post_init__(self):
        if self.headers:
            self.headers = {**self.headers, **default_headers}
        else:
            self.headers = default_headers.copy()


class UpdaterBase(metaclass=ABCMeta):
    """
    Abstract base class for all updaters.

    This class provides common methods and properties for all updaters.

    Subclasses must implement the following abstract methods:
        - get_updater_name: Get the name of the updater.
        - get_updater_version: Get the version of the updater.
        - get_config_path: Get the path to the configuration file for this updater.
        - get_update: Get the latest update information for the plugin/server.
    """

    @staticmethod
    @abstractmethod
    def get_updater_name() -> str:
        """
        Retrieve the name of the updater.

        Returns:
            str: The name of the updater.
        """
        ...

    @staticmethod
    @abstractmethod
    def get_updater_version() -> str:
        """
        Retrieve the version of the updater.

        Returns:
            str: The version of the updater.
        """
        ...

    @staticmethod
    @abstractmethod
    def get_config_path() -> str:
        """
        Retrieve the config key for the config section.

        Returns:
            str: The config key to the config section.
        """
        ...

    @abstractmethod
    def get_update(self) -> DownloadInfo | None:
        """
        Retrieve the latest update information for the plugin/server.

        Returns:
            DownloadInfo | None: The latest update information, or None if update is not available or an error occurred.
        """
        ...

    @final
    @property
    def log(self) -> logging.Logger:
        """
        Retrieve the logger instance for this updater.

        Returns:
            logging.Logger: The logger instance.
        """
        if not hasattr(self, "_logger"):
            self._logger = get_logger().getChild(self.get_updater_name())
        return self._logger

    @final
    @property
    def make_url(self):
        return make_url

    @final
    @property
    def make_requests(self):
        return make_requests

    @final
    @property
    def check_content_type(self):
        return check_content_type

    @final
    @property
    def parse_version(self):
        return parse_version

    @final
    def has_new_version(
        self,
        old: _Comparable,
        new: _Comparable,
        op: Literal["==", "!=", "<", "<=", ">", ">="] = "<",
    ) -> bool:
        """
        Check if a new version is available.

        Args:
            old (_Comparable): The old version.
            new (_Comparable): The new version.
            op (Literal["==", "!=", "<", "<=", ">", ">="], optional): The comparison operator.
                Defaults to "<" but can be set to any of "==", "!=", "<", "<=", ">", ">=".

        Note:
            If `--skip-version-check` is set, this method will always return True.
        """
        if get_cmd_opts().skip_version_check:
            return True
        return _compare[op](old, new)
