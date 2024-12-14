import fnmatch
import ftplib
import tempfile
from io import BytesIO
from pathlib import Path
from typing import IO

from ..meta import get_appdir
from ..utils.common import ensure_path
from .base import RemoteIO, RemotePathIsExistsError, RemotePathNotFoundError


class FTPStorage(RemoteIO):
    def __init__(
        self, host: str, port: int = 21, username: str = "anonymous", password: str = ""
    ):
        port = port or 21
        self._ftp = ftplib.FTP_TLS()
        self._ftp.connect(host, port)
        try:
            self._ftp.login(username, password)
        except ftplib.error_perm:
            self._ftp.login(username, password, secure=False)

    def _is_dir(self, path: str) -> bool:
        path = ensure_path(path).as_posix()
        pwd = self._ftp.pwd()
        try:
            self._ftp.cwd(path)
            self._ftp.cwd(pwd)
            return True
        except Exception:
            return False
        finally:
            self._ftp.cwd(pwd)

    def close(self):
        return self._ftp.close()

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
            with tempfile.NamedTemporaryFile("rb+", dir=get_appdir().caches_path) as f:
                self._ftp.retrbinary(f"RETR {from_path}", f.write)
                f.seek(0)
                self._ftp.storbinary(f"STOR {to_path}", f)

    def move(self, from_path: str, to_path: str):
        from_path = ensure_path(from_path).as_posix()
        to_path = ensure_path(to_path).as_posix()
        if self.exists(to_path):
            self.remove(to_path)
        self._ftp.rename(from_path, to_path)

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
            if self.is_dir(path):
                self._ftp.rmd(_)
            else:
                self._ftp.delete(_)

    def exists(self, path: str) -> bool:
        if self.is_dir(path):
            return True
        try:
            self._ftp.retrbinary(f"RETR {path}", lambda _: None)
            return True
        except Exception:
            return False

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
                self._ftp.mkd(parent.as_posix())

        self._ftp.mkd(path)

    def touch(self, path: str):
        path = ensure_path(path).as_posix()
        if self.exists(path):
            return
        with BytesIO() as f:
            self._ftp.storbinary(f"STOR {path}", f)

    def is_dir(self, path: str) -> bool:
        return self._is_dir(path)

    def is_file(self, path: str) -> bool:
        return not self._is_dir(path)

    def glob(self, path: str, pattern: str = "*", recursive: bool = False):
        path = ensure_path(path).as_posix()
        for item in self._ftp.nlst(path):
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
                with open(path, "rb") as f:
                    self._ftp.storbinary(
                        f"STOR {(to_remote_path / relative_path).as_posix()}", f
                    )

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
                with open((to_local_path / relative_path), "wb") as f:
                    self._ftp.retrbinary(f"RETR {path}", f.write)

    def uploadfo(self, stream: IO[bytes], to_remote_path: str):
        to_remote_path = ensure_path(to_remote_path).as_posix()
        stream.seek(0)
        self._ftp.storbinary(f"STOR {to_remote_path}", stream)

    def downloadfo(self, from_remote_path: str, stream: IO[bytes]):
        from_remote_path = ensure_path(from_remote_path).as_posix()
        stream.seek(0)
        self._ftp.retrbinary(f"RETR {from_remote_path}", stream.write)
