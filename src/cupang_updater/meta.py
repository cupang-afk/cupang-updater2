from dataclasses import dataclass, field
from pathlib import Path
from threading import Event

from ._version import __version__

app_name = "cupang-updater"
app_version = __version__
default_headers = {"User-Agent": f"{app_name}/{app_version}"}

stop_event = Event()


@dataclass
class AppDir:
    base_dir: Path
    config_path: Path = field(default=None)
    ext_updater_path: Path = field(init=False)
    logs_path: Path = field(init=False)
    caches_path: Path = field(init=False)

    def __post_init__(self):
        self.base_dir = self.base_dir.absolute()
        self.config_path = (
            (self.base_dir / "config.yaml")
            if not self.config_path
            else self.config_path
        )
        self.config_path = self.config_path.absolute()
        self.ext_updater_path = self.base_dir / "ext_updater"
        self.logs_path = self.base_dir / "logs"
        self.caches_path = self.base_dir / "caches"


_appdir: AppDir = None


def setup_appdir(appdir: AppDir):
    global _appdir
    _appdir = appdir


def get_appdir() -> AppDir:
    if not isinstance(_appdir, AppDir):
        raise RuntimeError("AppDir is not initialized")
    return _appdir
