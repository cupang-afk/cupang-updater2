import fnmatch
from pathlib import Path
from typing import IO

import smbclient
from smbprotocol.exceptions import SMBException

from ..utils.common import ensure_path
from .base import RemoteIO


class SMBPathNotFoundError(Exception):
    pass


class SMBPathIsExists(Exception):
    pass


class SMBStorage(RemoteIO):
    def __init__(
        self, host: str, port: int = 445, username: str = None, password: str = None
    ):
        self.host = host
        self.port = port or 445
        self._smb_host = f"\\\\{host}"
        self._connection_cache = {}
        smbclient.register_session(
            host,
            username,
            password,
            port or 445,
            encrypt=True,
            connection_cache=self._connection_cache,
        )

    def _is_dir(self, path: str):
        try:
            path_path = ensure_path(path)
            path = self._ensure_unc_path(path)
            is_dir = False
            for i in smbclient.scandir(
                self._ensure_unc_path(path_path.parent),
                path_path.name,
                connection_cache=self._connection_cache,
            ):
                if i.name == path_path.name:
                    is_dir = i.is_dir()
                    break

            if is_dir is None:
                raise SMBException
            return is_dir
        except SMBException:
            return False

    def _ensure_unc_path(self, path: str | Path) -> str:
        path = ensure_path(path)
        if path.as_posix().replace("/", "\\").startswith(self._smb_host):
            return path.as_posix().replace("/", "\\")

        return self._smb_host + ensure_path(path).as_posix().replace("/", "\\")

    def close(self):
        smbclient.delete_session(
            self.host, port=self.port, connection_cache=self._connection_cache
        )

    def copy(self, from_path: str, to_path: str):
        from_path = self._ensure_unc_path(from_path)
        to_path = self._ensure_unc_path(to_path)
        if self.is_dir(from_path):
            self.mkdir(to_path)
            for item in self.rglob(from_path):
                item = ensure_path(item)
                item_from_path = Path(from_path, item.name).as_posix()
                item_to_path = Path(to_path, item.name).as_posix()
                self.copy(item_from_path, item_to_path)
        else:
            smbclient.copyfile(
                from_path, to_path, connection_cache=self._connection_cache
            )

    def move(self, from_path: str, to_path: str):
        from_path = self._ensure_unc_path(from_path)
        to_path = self._ensure_unc_path(to_path)
        if self.exists(to_path):
            self.remove(to_path)
        smbclient.rename(from_path, to_path, connection_cache=self._connection_cache)

    def remove(self, path: str):
        path = self._ensure_unc_path(path)
        if not self.exists(path):
            raise SMBPathNotFoundError
        _need_to_delete = []
        _need_to_delete.append(path)
        if self.is_dir(path):
            for _ in self.rglob(path):
                _need_to_delete.append(self._ensure_unc_path(_))
        for _ in sorted(_need_to_delete, key=lambda x: len(x), reverse=True):
            if self.is_dir(path):
                smbclient.rmdir(_, connection_cache=self._connection_cache)
            else:
                smbclient.remove(_, connection_cache=self._connection_cache)

    def exists(self, path: str) -> bool:
        try:
            path_path = Path(path)
            path = self._ensure_unc_path(path)
            if len(Path(path).parts) == 1:
                # smbclient needs \\server\share
                # Path supports smb path and it will return 1 part if path is \\server\share
                # and \\server\share must exists
                return True
            for i in smbclient.scandir(
                self._ensure_unc_path(path_path.parent),
                path_path.name,
                connection_cache=self._connection_cache,
            ):
                if i.name == path_path.name:
                    is_dir = i.is_dir()
                    break

            if is_dir is None:
                raise SMBException
            return True
        except (SMBException, ValueError):
            return False

    def mkdir(self, path: str, parents: bool = False, exists_ok: bool = False):
        path = self._ensure_unc_path(path)
        if self.exists(path):
            if exists_ok:
                return
            else:
                raise SMBPathIsExists(path)
        if parents:
            parent_dir = ensure_path(path)
            for parent in parent_dir.parents[::-1]:
                parent = self._ensure_unc_path(parent)
                if self.exists(parent):
                    continue
                smbclient.mkdir(parent, connection_cache=self._connection_cache)

        smbclient.mkdir(path, connection_cache=self._connection_cache)

    def touch(self, path: str):
        path = self._ensure_unc_path(path)
        if self.exists(path):
            return
        with smbclient.open_file(
            path, "w", connection_cache=self._connection_cache
        ) as f:
            f.write("")

    def is_dir(self, path: str) -> bool:
        path = self._ensure_unc_path(path)
        return self._is_dir(path)

    def is_file(self, path: str) -> bool:
        path = self._ensure_unc_path(path)
        return not self._is_dir(path)

    def glob(self, path: str, pattern: str = "*", recursive: bool = False):
        base_path = Path(path)
        path = self._ensure_unc_path(path)
        for item in smbclient.listdir(path, connection_cache=self._connection_cache):
            item_path = (base_path / item).as_posix()
            if fnmatch.fnmatch(item_path, pattern):
                yield item_path

            if recursive and self.is_dir(item_path):
                yield from self.glob(item_path, pattern, recursive)

    def rglob(self, path: str, pattern: str = "**/**"):
        return self.glob(path, pattern, recursive=True)

    def upload(self, from_local_path: str, to_remote_path: str):
        from_local_path = ensure_path(from_local_path)
        to_remote_path = self._ensure_unc_path(to_remote_path)
        paths_to_upload = [from_local_path]
        base_path = Path(from_local_path)
        if from_local_path.is_dir():
            paths_to_upload.extend(from_local_path.rglob("*"))
        for path in sorted(paths_to_upload, key=lambda x: len(x.as_posix())):
            relative_path = Path(path).relative_to(base_path)
            if path.is_dir():
                self.mkdir(
                    str(to_remote_path / relative_path), parents=True, exists_ok=True
                )
            else:
                with open(path, "rb") as fs:
                    self.uploadfo(fs, (to_remote_path / relative_path).as_posix())

    def download(self, from_remote_path: str, to_local_path: str):
        base_path = Path(from_remote_path)
        from_remote_path = self._ensure_unc_path(from_remote_path)
        to_local_path = ensure_path(to_local_path)
        paths_to_download = [from_remote_path]
        if self.is_dir(from_remote_path):
            paths_to_download.extend(self.rglob(from_remote_path))
        for path in sorted(paths_to_download, key=lambda x: len(x)):
            relative_path = Path(path).relative_to(base_path)
            if self.is_dir(path):
                (to_local_path / relative_path).mkdir(parents=True, exist_ok=True)
            else:
                with open((to_local_path / relative_path), "wb") as fd:
                    self.downloadfo(path, fd)

    def uploadfo(self, stream: IO[bytes], to_remote_path: str):
        to_remote_path = self._ensure_unc_path(to_remote_path)
        stream.seek(0)
        with smbclient.open_file(
            to_remote_path, "wb", connection_cache=self._connection_cache
        ) as fd:
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    break
                fd.write(chunk)

    def downloadfo(self, from_remote_path: str, stream: IO[bytes]):
        from_remote_path = self._ensure_unc_path(from_remote_path)
        stream.seek(0)
        with smbclient.open_file(
            from_remote_path, "rb", connection_cache=self._connection_cache
        ) as fs:
            while True:
                chunk = fs.read(8192)
                if not chunk:
                    break
                stream.write(chunk)
