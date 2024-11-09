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

    def __post_init__(self):
        self.config_path = (
            (self.base_dir / "config.yaml")
            if not self.config_path
            else self.config_path
        )
        self.ext_updater_path = self.base_dir / "ext_updater"
        self.logs_path = self.base_dir / "logs"
