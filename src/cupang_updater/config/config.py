from pathlib import Path
from typing import Any

import strictyaml as sy

from ..utils.common import ensure_path
from .default import default_config
from .schema import get_config_schema


class Config:
    def __init__(self):
        """Initialize the configuration.

        Attributes:
            _config_path (Path): The path to the configuration file.
            _config (sy.YAML): The raw configuration as a strictyaml object.
        """
        self._config_path: Path = None
        self._config: sy.YAML = None

    def load(self, file: str | Path = None, _default: str = default_config):
        """Load configuration from a file.

        Args:
            file: The path to the configuration file.
                If not provided, use the default configuration.
            _default: The default configuration as a string.
                If not provided, use the default configuration.

        Raises:
            FileNotFoundError: If the file does not exist
                and no default configuration is provided.
        """
        file = ensure_path(file) if file else None
        self._config_path = file
        if file.exists():
            yaml_string = file.read_text(encoding="utf-8")
        else:
            if _default:
                yaml_string = _default
            else:
                raise FileNotFoundError(
                    f"Config file not found at {file} and default value not set"
                )
        self._config = sy.load(yaml_string, get_config_schema())

    def reload(self):
        """
        Reload the configuration from the file where it was previously loaded from.
        """

        self.load(self._config_path)

    def save(self, file: str | Path = None):
        """
        Save the current configuration to a file.

        Args:
            file (str | Path, optional): The path to the file where the configuration
                should be saved.
                If not provided, saves to the previously loaded configuration path.
        """
        file = ensure_path(file) if file else self._config_path
        file.write_text(self._config.as_yaml(), encoding="utf-8")

    @property
    def data(self) -> dict[str, Any]:
        """
        Get the data as a dictionary
        """
        return self._config.data

    @property
    def strictyaml(self) -> sy.YAML:
        """
        Get the raw strictyaml object
        """
        return self._config

    def set(self, path: str, value: Any):
        """
        Set the value using path.to.key
        """
        if not path:
            return
        if isinstance(value, sy.YAML):
            if not value.data:
                return
        elif not value:
            return

        current = self._config
        *initial_keys, last_key = path.split(".")

        for key in initial_keys:
            if not current.is_mapping() or key not in current:
                break
            current = current[key]

        current[last_key] = value

    def get(self, path: str, default: Any = None) -> sy.YAML | Any:
        """
        Get the value using path.to.value

        It's recommended to put default as YAML object
        """
        if path == ".":
            return self.config

        # mask default to return sy.YAML object
        if default is None:
            default = sy.YAML(default, sy.EmptyNone())

        current = self._config
        keys = path.split(".")

        for key in keys:
            if not current.is_mapping() or key not in current:
                break
            current = current[key]

        if current is None or current.data is None:
            return default
        return current
