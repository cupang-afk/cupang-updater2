import fnmatch
from io import BytesIO
from pathlib import Path
from typing import IO, Literal

from webdav3.client import Client

from ..utils.common import ensure_path
from .base import RemoteIO, RemotePathIsExistsError, RemotePathNotFoundError


class WebdavStorage(RemoteIO):
    def __init__(
        self,
        host: str,
        port: int = 80,
        username: str = None,
        password: str = None,
        protocol: Literal["http", "https"] = "http",
    ):
        port = port or (80 if protocol == "http" else 443)
        self._dav = Client(
            {
                "webdav_hostname": f"{protocol}://{host}:{port}",
                "webdav_login": username,
                "webdav_password": password,
                "webdav_timeout": 5,
                "chunk_size": 8192,
            }
        )
        self.touch("/.webdav")

    def close(self):
        self.remove("/.webdav")

    def copy(self, from_path: str, to_path: str):
        from_path = ensure_path(from_path).as_posix()
        to_path = ensure_path(to_path).as_posix()
        if self.is_dir(from_path):
            self.mkdir(to_path)
            for item in self.rglob(from_path):
                item = ensure_path(item)
                item_from_path = Path(from_path, item.name).as_posix()
                item_to_path = Path(to_path, item.name).as_posix()
                self.copy(item_from_path, item_to_path)
        else:
            self._dav.copy(from_path, to_path)

    def move(self, from_path: str, to_path: str):
        from_path = ensure_path(from_path).as_posix()
        to_path = ensure_path(to_path).as_posix()
        if self.exists(to_path):
            self.remove(to_path)
        self._dav.move(from_path, to_path)

    def remove(self, path: str):
        path = ensure_path(path).as_posix()
        if not self.exists(path):
            raise RemotePathNotFoundError(path)
        _need_to_delete = []
        _need_to_delete.append(path)
        if self.is_dir(path):
            for _ in self.rglob(path):
                _need_to_delete.append(_)
        for _ in sorted(_need_to_delete, key=lambda x: len(x), reverse=True):
            self._dav.clean(_)

    def exists(self, path: str) -> bool:
        path = ensure_path(path).as_posix()
        return self._dav.check(path)

    def mkdir(self, path: str, parents: bool = False, exists_ok: bool = False):
        path = ensure_path(path).as_posix()
        if self.exists(path):
            if exists_ok:
                return
            else:
                raise RemotePathIsExistsError(path)
        if parents:
            parent_dir = ensure_path(path)
            for parent in parent_dir.parents[::-1]:
                if self.exists(parent):
                    continue
                self._dav.mkdir(parent.as_posix())

        self._dav.mkdir(path)

    def touch(self, path: str):
        path = ensure_path(path).as_posix()
        if self.exists(path):
            return
        with BytesIO() as f:
            self._dav.upload_to(f, path)

    def is_dir(self, path: str) -> bool:
        if not self.exists(path):
            raise RemotePathNotFoundError(path)
        return self._dav.is_dir(path)

    def is_file(self, path: str) -> bool:
        return not self.is_dir(path)

    def glob(self, path: str, pattern: str = "*", recursive: bool = False):
        path = ensure_path(path).as_posix()
        for item in self._dav.list(path):
            item_path = Path(path, item).as_posix()
            if fnmatch.fnmatch(item_path, pattern):
                yield item_path

            if recursive and self.is_dir(item_path):
                yield from self.glob(item_path, pattern, recursive)

    def rglob(self, path: str, pattern: str = "**/**"):
        return self.glob(path, pattern, recursive=True)

    def upload(self, from_local_path: str, to_remote_path: str):
        from_local_path = ensure_path(from_local_path).absolute()
        to_remote_path = ensure_path(to_remote_path).as_posix()
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
                self._dav.upload((to_remote_path / relative_path).as_posix(), str(path))

    def download(self, from_remote_path: str, to_local_path: str):
        from_remote_path = ensure_path(from_remote_path).as_posix()
        to_local_path = ensure_path(to_local_path)
        paths_to_download = [from_remote_path]
        base_path = Path(from_remote_path)
        if self.is_dir(from_remote_path):
            paths_to_download.extend(self.rglob(from_remote_path))
        for path in sorted(paths_to_download, key=lambda x: len(x)):
            relative_path = Path(path).relative_to(base_path)
            if self.is_dir(path):
                (to_local_path / relative_path).mkdir(parents=True, exist_ok=True)
            else:
                self._dav.download(path, str(to_local_path / relative_path))

    def uploadfo(self, stream: IO[bytes], to_remote_path: str):
        to_remote_path = ensure_path(to_remote_path).as_posix()
        stream.seek(0)
        self._dav.upload_to(stream, to_remote_path)

    def downloadfo(self, from_remote_path: str, stream: IO[bytes]):
        from_remote_path = ensure_path(from_remote_path).as_posix()
        stream.seek(0)
        self._dav.download_from(stream, from_remote_path)
