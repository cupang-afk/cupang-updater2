import logging
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, final

from ..logger.logger import get_logger
from ..meta import default_headers
from ..utils.common import parse_version
from ..utils.url import check_content_type, make_requests, make_url


@dataclass
class Hashes:
    """
    Attributes:
        md5 (str): The MD5 hash of the file.
        sha1 (str): The SHA-1 hash of the file.
        sha256 (str): The SHA-256 hash of the file.
        sha512 (str): The SHA-512 hash of the file.
    """

    md5: str = field(default=None)
    sha1: str = field(default=None)
    sha256: str = field(default=None)
    sha512: str = field(default=None)


@dataclass
class CommonData:
    """
    Attributes:
        name (str): The name of the file.
        version (str): The version of the file.
        hashes (Hashes): The hashes of the file.
        download_headers (dict[str, str]): The headers to use when downloading the file.
        extra (dict[str, Any]): Additional information about the file.
        url (str): The URL of the file.
    """

    name: str
    version: str
    hashes: Hashes = field(default_factory=Hashes)
    download_headers: dict[str, str] = field(default=None)
    extra: dict[str, Any] = field(default=None)
    url: str = field(init=False)

    def __post_init__(self):
        if self.download_headers:
            self.download_headers = {**self.download_headers, **default_headers}
        self.extra = self.extra or {}

    def set_url(self, url: str) -> "CommonData":
        self.url = url


class UpdaterBase(metaclass=ABCMeta):
    """
    Abstract base class for all updaters.

    This class provides common methods and properties for all updaters.
    """

    @staticmethod
    @abstractmethod
    def get_updater_name() -> str:
        """
        Get the name of the updater.

        Returns:
            str: The name of the updater.
        """
        ...

    @staticmethod
    @abstractmethod
    def get_updater_version() -> str:
        """
        Get the version of the updater.

        Returns:
            str: The version of the updater.
        """
        ...

    @staticmethod
    @abstractmethod
    def get_config_path() -> str:
        """
        Get the path to the configuration file for this updater.

        Returns:
            str: The path to the configuration file.
        """
        ...

    @final
    @property
    def log(self) -> logging.Logger:
        """
        Returns:
            logging.Logger: The logger for this Updater instance.
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
