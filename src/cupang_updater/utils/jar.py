import json
import shutil
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import IO, Any

import strictyaml as sy
import toml

from ..remote_storage.base import RemoteIO
from .common import ensure_path

_jar_yaml_schema = sy.MapCombined(
    {
        sy.Optional("name"): sy.Str(),
        sy.Optional("version"): sy.Str() | sy.Seq(sy.Str()),
        sy.Optional("authors"): sy.Seq(sy.Str()),
        sy.Optional("author"): sy.Str(),
    },
    sy.Str(),
    sy.Any(),
)


@dataclass
class JarInfo:
    name: str
    version: str
    authors: list[str]

    def __post_init__(self):
        if not self.name or not self.version:
            raise ValueError("name and version are required")


def get_jar_info(jar_file: str | Path | IO[bytes]) -> JarInfo:
    """Extract metadata from a given jar file.

    Supports Bukkit, Velocity, Fabric, and Forge mods.

    Args:
        jar_path (str | Path | IO[bytes]): The jar file.

    Returns:
        JarInfo: A JarInfo instance containing the metadata.
    """
    with zipfile.ZipFile(jar_file) as jar:
        config: dict[str, Any]
        plugin_name: str | None = None
        plugin_version: str | None = None
        plugin_authors: list[str] | None = None

        # Bukkit (including Paper)
        bukkit_files = [
            file_name
            for file_name in ["paper-plugin.yml", "plugin.yml", "bungee.yml"]
            if file_name in jar.namelist()
        ]
        if bukkit_files:
            for bukkit_file in bukkit_files:
                with jar.open(bukkit_file, "r") as file:
                    config = sy.dirty_load(
                        file.read().decode(),
                        schema=_jar_yaml_schema,
                        allow_flow_style=True,
                    ).data

                    plugin_name = config.get("name")
                    plugin_version = config.get("version")
                    plugin_authors = config.get("authors", config.get("author"))
                break

        # Velocity
        elif "velocity-plugin.json" in jar.namelist():
            with jar.open("velocity-plugin.json", "r") as file:
                config = json.load(file)

                plugin_name = config.get("name", config.get("id"))
                plugin_version = config.get("version")
                plugin_authors = config.get("authors")

        # Fabric
        elif "fabric.mod.json" in jar.namelist():
            with jar.open("fabric.mod.json", "r") as file:
                config = json.load(file)

                plugin_name = config.get("name", config.get("id"))
                plugin_version = config.get("version")
                plugin_authors = config.get("authors")

        # Forge
        elif "META-INF/mods.toml" in jar.namelist():
            with jar.open("META-INF/mods.toml", "r") as file:
                config = toml.loads(file.read().decode())

                if config.get("mods"):
                    mod_info = config["mods"][0]
                    plugin_name = mod_info.get("modId")
                    plugin_version = mod_info.get("version")
                    plugin_authors = mod_info.get("authors")

        # Ensure authors are represented as a list
        if isinstance(plugin_authors, str):
            plugin_authors = [plugin_authors]

        # Ensure version is a string
        plugin_version = plugin_version or "0"
        if isinstance(plugin_version, list):
            plugin_version = plugin_version[0]
        plugin_version = str(plugin_version)

        return JarInfo(plugin_name, plugin_version, plugin_authors)


def jar_rename(
    jar_path: str | Path,
    jar_info: JarInfo = None,
    remote_connection: RemoteIO = None,
) -> Path:
    """
    Rename a given jar file based on its extracted metadata.

    Args:
        jar_path (str | Path): The jar path.
        jar_info (JarInfo): Metadata of the jar file.

    Returns:
        Path: The new path of the renamed jar file.

    Notes:
        If remote_connection is provided, the jar file will be renamed on the remote storage.
        so jar_path must be provided as a remote path.
        Return value is a remote path but wrapped as Path object.
    """
    jar_path = ensure_path(jar_path)
    if not jar_info:
        if remote_connection:
            with BytesIO() as f:
                remote_connection.downloadfo(jar_path.as_posix(), f)
                jar_info = get_jar_info(f)
        else:
            jar_info = get_jar_info(jar_path)

    new_name = f"{jar_info.name} [{jar_info.version}].jar"

    new_file = jar_path.with_name(new_name)
    if remote_connection:
        remote_connection.move(
            jar_path.as_posix(), jar_path.with_name(new_name).as_posix()
        )
    else:
        shutil.move(jar_path, new_file)
    return new_file
