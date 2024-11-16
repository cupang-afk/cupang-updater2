import re
from io import BytesIO, StringIO
from pathlib import Path

import strictyaml as sy

from ..config.config import Config
from ..logger.logger import get_logger
from ..manager.plugin import get_plugin_default
from ..meta import get_appdir, stop_event
from ..remote_storage.remote import get_remote_connection
from ..rich import get_rich_status
from ..utils.common import reindent
from ..utils.config import fix_config
from ..utils.hash import FileHash
from ..utils.jar import get_jar_info, jar_rename
from ..utils.rich import status_update


def scan_plugins(config: Config) -> None:
    """
    Scans the plugins directory.

    - Newly discovered plugins are added to the configuration with default values.
    - Clean up the configuration after the scan.

    Args:
        config (Config): The configuration object that holds plugin settings.

    Raises:
        FileNotFoundError: If the plugins folder does not exist.
    """
    log = get_logger()
    try:
        remote_connection = get_remote_connection()
        remote_plugins_folder = Path(remote_connection.base_dir, "plugins").as_posix()
        plugins_folder = get_appdir().caches_path / "plugins"
        plugins_folder.mkdir(exist_ok=True)
        is_remote = True
    except RuntimeError:
        plugins_folder = Path(config.get("settings.server_folder").data, "plugins")
        is_remote = False
    is_new_plugin = False
    keep_removed: bool = config.get(
        "settings.keep_removed", sy.YAML(False, sy.Bool())
    ).data

    # updating YAML object directly is too slow
    # instead we create a new dict object that hold {plugin_name: YAML}
    # and use it to add new plugins
    if config.data["plugins"]:
        plugins_config: sy.YAML = sy.load(
            config.strictyaml["plugins"].as_yaml(),
            config.strictyaml["plugins"].validator,
        )
    else:
        plugins_config: sy.YAML = sy.as_document(
            {}, config.strictyaml["plugins"].validator
        )
    if plugins_config.data:
        _ = {}
        for k in plugins_config.data.keys():
            _[k] = plugins_config[k]
        plugins_config = _
    else:
        plugins_config = plugins_config.data
    # ensure the typing
    plugins_config: dict[str, sy.YAML] = plugins_config

    status = get_rich_status()

    with status:
        status_update(status, "Scanning Plugins")

        if not plugins_folder.exists():
            log.error(
                "Could not check plugins because plugins folder is not exist :shrug:"
            )
            raise FileNotFoundError

        if is_remote:
            plugin_list = [
                str(p) for p in remote_connection.glob(remote_plugins_folder, "*.jar")
            ]
        else:
            plugin_list = [str(p) for p in plugins_folder.glob("*.jar")]

        plugin_list = sorted(plugin_list, key=lambda x: Path(x).name)

        for jar in plugin_list:
            if stop_event.set():
                break
            if is_remote:
                with BytesIO() as f:
                    remote_connection.downloadfo(jar, f)
                    f.seek(0)
                    file_hash = FileHash(f)
                    file_hash.md5
                    file_hash.sha1
                    file_hash.sha256
                    file_hash.sha512
                    f.seek(0)
                    jar_info = get_jar_info(f)
            else:
                file_hash = FileHash(jar)
                jar_info = get_jar_info(jar)

            status_update(status, f"Scanning plugins {jar_info.name}", no_log=True)

            jar = Path(jar)

            # rename the jar in PluginName [Version].jar
            if jar.name != f"{jar_info.name} [{jar_info.version}].jar":
                new_jar = jar_rename(
                    jar,
                    jar_info,
                    remote_connection if is_remote else None,
                )
                log.info(
                    f"[green]Renaming [cyan]{Path(jar).name} [green]-> [cyan]{new_jar.name}"
                )
                jar = new_jar

            default_plugin_data = get_plugin_default()

            if plugins_config.get(jar_info.name, sy.YAML(None, sy.EmptyNone())).data:
                if (
                    file_hash.md5 == plugins_config[jar_info.name]["hashes"]["md5"].data
                    and jar.name == plugins_config[jar_info.name]["file"].data
                ):
                    continue
            else:
                is_new_plugin = True

            # Why is this using a YAML object instead of a regular dict?
            #
            # This is because the `preserve_comments` feature of the strictyaml library
            # allows comments to be preserved in the YAML file, but regular dictionaries
            # don't have this ability.
            #
            # If the config for a plugin already exists, updating it will be slower
            # because the YAML library needs to re-validate the entire config.
            # Otherwise, it will be faster.
            log.info(f"[green]Update config for {jar_info.name} [cyan]{jar.name}")

            # use default_plugin_data if not exists
            if not plugins_config.get(
                jar_info.name, sy.YAML(None, sy.EmptyNone())
            ).data:
                plugin_data: sy.YAML = default_plugin_data
            else:
                plugin_data = plugins_config[jar_info.name]

            plugin_data["file"] = jar.name
            plugin_data["version"] = jar_info.version
            plugin_data["authors"] = jar_info.authors

            plugin_hashes = plugin_data["hashes"]
            plugin_hashes["md5"] = file_hash.md5
            plugin_hashes["sha1"] = file_hash.sha1
            plugin_hashes["sha256"] = file_hash.sha256
            plugin_hashes["sha512"] = file_hash.sha512

            plugins_config[jar_info.name] = plugin_data

        status_update(status, "Finished Scanning Plugins")

        if not keep_removed:
            status_update(status, "Remove deleted plugin")

            for name in list(plugins_config.keys()).copy():
                if Path(plugins_folder, plugins_config[name].data["file"]).exists():
                    continue
                log.info(f"[red]Removing {name} from config")
                del plugins_config[name]
            status_update(status, "Finished removing plugins")

        status_update(status, "Fixing Config")
        for name in plugins_config.keys():
            fix_config(
                plugins_config[name],
                get_plugin_default(),
                name,
            )
        status_update(status, "Finished Fixing Config")

        # this part also fix the yaml comment by editing it as yaml text
        status_update(status, "Updating Config")
        sorted_plugins = sorted(plugins_config.keys(), key=lambda k: k.lower())
        with StringIO() as temp:
            temp.write("plugins:\n")
            inline_comment_regex = re.compile(r"(\s+)#")
            for name in sorted_plugins:
                temp.write(reindent(f"{name}:\n", 2))
                for line in plugins_config[name].as_yaml().splitlines():
                    if not line.lstrip().startswith("#"):
                        # remove excessive whitespaces between inline comments
                        line = inline_comment_regex.sub(" #", line)
                        # .as_yaml() already dedent the yaml, we only need to add indent
                        line = " " * 4 + line
                    else:
                        # indent the mapping comment
                        line = reindent(line, 6)
                    temp.write(line + "\n")

            data = sy.load(
                temp.getvalue(), sy.Map({"plugins": config.get("plugins").validator})
            )
            config.set("plugins", data["plugins"])
            config.save()
            config.reload()
        status_update(status, "Config updated")

        if is_new_plugin:
            log.info("[green]You have new plugin, please fill the config")
            exit()
