from abc import ABCMeta, abstractmethod
from typing import IO, final


class RemotePathIsExistsError(Exception):
    pass


class RemotePathNotFoundError(Exception):
    pass


class RemoteIO(metaclass=ABCMeta):
    @final
    @property
    def base_dir(self) -> str:
        """Get the base directory of the remote storage.

        The base directory is where all relative paths are resolved from.

        Returns:
            str: The base directory of the remote storage.
        """

        return self._base_dir

    @final
    @base_dir.setter
    def base_dir(self, path: str):
        self._base_dir = path

    @abstractmethod
    def close(self): ...

    @abstractmethod
    def copy(self, from_path: str, to_path: str): ...

    @abstractmethod
    def move(self, from_path: str, to_path: str): ...

    @abstractmethod
    def remove(self, path: str): ...

    @abstractmethod
    def exists(self, path: str) -> bool: ...

    @abstractmethod
    def mkdir(self, path: str, parents: bool = False, exists_ok: bool = False): ...

    @abstractmethod
    def touch(self, path: str): ...

    @abstractmethod
    def is_dir(self, path: str) -> bool: ...

    @abstractmethod
    def is_file(self, path: str) -> bool: ...

    @abstractmethod
    def glob(self, path: str, pattern: str = "*", recursive: bool = False): ...

    @abstractmethod
    def rglob(self, path: str, pattern: str = "**/**"): ...

    @abstractmethod
    def upload(self, from_local_path: str, to_remote_path: str): ...

    @abstractmethod
    def download(self, from_remote_path: str, to_local_path: str): ...

    @abstractmethod
    def uploadfo(self, stream: IO[bytes], to_remote_path: str): ...

    @abstractmethod
    def downloadfo(self, from_remote_path: str, stream: IO[bytes]): ...
