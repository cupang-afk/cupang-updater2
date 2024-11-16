import argparse
import time
from concurrent.futures import Future, ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

import strictyaml as sy
from cupang_downloader.downloader import DownloadJob

from ..config.config import Config
from ..downloader.downloader import get_downloader
from ..downloader.progress import get_callbacks, get_progress
from ..logger.logger import get_logger
from ..manager.plugin import get_plugin_updater
from ..manager.server import get_server_updaters
from ..meta import get_appdir, stop_event
from ..remote_storage.base import RemoteIO
from ..remote_storage.remote import get_remote_connection
from ..rich import get_rich_live, get_rich_status
from ..updater.base import Hashes, ResourceData
from ..updater.plugin.base import PluginUpdater, PluginUpdaterConfig
from ..updater.server.base import ServerUpdater, ServerUpdaterConfig
from ..utils.date import parse_date_datetime
from ..utils.hash import FileHash
from ..utils.jar import get_jar_info, jar_rename
from ..utils.rich import status_update


def _handle_server_update(
    updater_list: list[type[ServerUpdater]],
    server_folder: Path,
    server_data: dict,
    server_common: dict = None,
) -> tuple[str, ResourceData, ServerUpdaterConfig | None] | None:
    log = get_logger()
    server_file: Path = server_folder / server_data["file"]
    server_type: str = server_data["type"]
    server_version: str = server_data["version"]
    server_data["build_number"] = server_data["build_number"] or 0

    if server_file.exists():
        if server_data["hashes"]["md5"]:
            server_hash = FileHash.with_known_hashes(
                server_file,
                Hashes(**server_data["hashes"]),
            )
        else:
            server_hash = FileHash(server_file)
    else:
        server_hash = FileHash.with_known_hashes(
            server_file, Hashes("a", "b", "c", "d")
        )

    dl_callbacks = get_callbacks()
    resource_data = ResourceData(
        f"{server_type} ({server_file.name})",
        server_version,
        server_hash._hashes,
    )
    for updater in updater_list:
        if stop_event.is_set():
            break
        updater = updater(
            resource_data,
            # Perform a deepcopy to prevent changes to the original configuration
            # server_data is passed directly (refer to server: fields in config.yaml)
            ServerUpdaterConfig(
                common_config=deepcopy(server_common.get(server_type, {})),
                server_config=deepcopy(server_data),
            ),
        )
        try:
            update_data = updater.get_update()
        except Exception as e:
            updater.log.exception(f"Failed to get server update: {e}")
            log.error(f"Trying another server updater for {server_type}")
            continue

        if not update_data:
            continue

        is_dl_error = False

        def _on_error(j, err):
            dl_callbacks["on_error"](j, err)
            nonlocal is_dl_error
            is_dl_error = True

        get_downloader().dl(
            DownloadJob(
                update_data.url,
                server_file,
                update_data.headers,
                server_type,
            ),
            on_start=dl_callbacks["on_start"],
            on_finish=dl_callbacks["on_finish"],
            on_progress=dl_callbacks["on_progress"],
            on_cancel=dl_callbacks["on_cancel"],
            on_error=_on_error,
        )
        if is_dl_error:
            return

        server_hash = FileHash(server_file)

        server_hash.md5
        server_hash.sha1
        server_hash.sha256
        server_hash.sha512
        resource_data.hashes = server_hash._hashes

        return updater.get_config_path(), resource_data, updater.get_config_update()


def _handle_plugin_update(
    updater_list: list[type[PluginUpdater]],
    plugins_folder: Path,
    plugin_name: str,
    plugin_data: dict,
    plugin_common: dict = None,
) -> tuple[str, Path, ResourceData, PluginUpdaterConfig] | None:
    plugin_file: Path = plugins_folder / plugin_data["file"]
    plugin_version: str = plugin_data["version"]

    if plugin_file.exists():
        if plugin_data["hashes"]["md5"]:
            plugin_hash = FileHash.with_known_hashes(
                plugin_file,
                Hashes(**plugin_data["hashes"]),
            )
        else:
            plugin_hash = FileHash(plugin_file)
    else:
        plugin_hash = FileHash.with_known_hashes(plugin_file, Hashes())

    dl_callbacks = get_callbacks()
    resource_data = ResourceData(
        plugin_name,
        plugin_version,
        plugin_hash._hashes,
    )
    for updater in updater_list:
        if stop_event.is_set():
            break
        updater = updater(
            resource_data,
            PluginUpdaterConfig(
                common_config=deepcopy(
                    plugin_common.get(updater.get_config_path(), {})
                ),
                plugin_config=deepcopy(plugin_data.get(updater.get_config_path(), {})),
            ),
        )
        try:
            update_data = updater.get_update()
        except Exception as e:
            updater.log.exception(f"Failed to get plugin update: {e}")
            continue

        if not update_data:
            continue

        new_plugin_file = plugin_file.with_name(f"{plugin_name} [Latest].jar")

        is_dl_error = False

        def _on_error(j, err):
            dl_callbacks["on_error"](j, err)
            nonlocal is_dl_error
            is_dl_error = True

        get_downloader().dl(
            DownloadJob(
                update_data.url,
                new_plugin_file,
                update_data.headers,
                plugin_name,
            ),
            on_start=dl_callbacks["on_start"],
            on_finish=dl_callbacks["on_finish"],
            on_progress=dl_callbacks["on_progress"],
            on_cancel=dl_callbacks["on_cancel"],
            on_error=_on_error,
        )
        if is_dl_error:
            return

        jar_info = get_jar_info(new_plugin_file)
        new_plugin_file = jar_rename(new_plugin_file, jar_info)
        plugin_hash = FileHash(new_plugin_file)

        plugin_hash.md5
        plugin_hash.sha1
        plugin_hash.sha256
        plugin_hash.sha512

        resource_data.version = jar_info.version
        resource_data.hashes = plugin_hash

        return (
            updater.get_config_path(),
            new_plugin_file,
            resource_data,
            updater.get_config_update(),
        )


def _handle_plugin_meta_update(
    config: Config, plugin_name: str, plugin_file: Path, resource_data: ResourceData
):
    config_path = f"plugins.{plugin_name}."
    config.set(config_path + "file", plugin_file.name)
    config.set(config_path + "version", resource_data.version)
    config.set(config_path + "hashes.md5", resource_data.hashes.md5)
    config.set(config_path + "hashes.sha1", resource_data.hashes.sha1)
    config.set(config_path + "hashes.sha256", resource_data.hashes.sha256)
    config.set(config_path + "hashes.sha512", resource_data.hashes.sha512)


def _handle_plugin_updater_update(
    config: Config,
    config_path: str,
    plugin_name: str,
    plugin_config_update: PluginUpdaterConfig,
):
    if not isinstance(plugin_config_update, PluginUpdaterConfig):
        return
    for key, value in plugin_config_update.plugin_config.items():
        config.set(
            f"plugins.{plugin_name}.{config_path.strip('.')}.{key.strip('.')}",
            value,
        )


def _handle_settings_common_update(
    config: Config,
    config_path: str,
    config_update: ServerUpdaterConfig | PluginUpdaterConfig,
):
    if not isinstance(config_update, ServerUpdaterConfig) or isinstance(
        config_update, PluginUpdaterConfig
    ):
        return
    _type = "server" if isinstance(config_update, ServerUpdaterConfig) else "plugin"
    for key, value in config_update.common_config.items():
        config.set(
            f"updater_settings.{_type}.{config_path.strip('.')}.{key.strip('.')}",
            value,
        )


def _handle_remote_upload(
    remote_connection: RemoteIO, from_local_path: str, to_remote_path: str
) -> None:
    remote_connection.upload(from_local_path, to_remote_path)


def update_server(config: Config) -> None:
    """
    Update the server based on the given configuration.
    """
    status = get_rich_status()
    log = get_logger()
    with get_rich_live(get_progress(), status):
        try:
            remote_connection = get_remote_connection()
            remote_server_folder = remote_connection.base_dir
            server_folder = get_appdir().caches_path / "server"
            server_folder.mkdir(exist_ok=True)
            is_remote = True
        except RuntimeError:
            server_folder = Path(config.get("settings.server_folder").data)
            is_remote = False

        if config.get("server.enable", True):
            status_update(status, "Updating Server")

            result = _handle_server_update(
                get_server_updaters(config.get("server.type").data),
                server_folder,
                config.get("server").data,
                config.get("updater_settings.server").data,
            )
            if result:
                config_path, resource_data, server_config_update = result
                server_hash = resource_data.hashes

                # Updating the server config is somewhat unique, as we only perform updates for build_number and hashes
                config.set(
                    "server.build_number",
                    server_config_update.server_config.get("build_number", 0) or 0,
                )
                config.set(
                    "server.hashes",
                    dict(
                        md5=server_hash.md5,
                        sha1=server_hash.sha1,
                        sha256=server_hash.sha256,
                        sha512=server_hash.sha512,
                    ),
                )
                if is_remote:
                    server_file = Path(server_folder / config.get("server.file").data)
                    log.info(f"[green]Uploading {server_file.name}")
                    _handle_remote_upload(
                        remote_connection,
                        server_file.as_posix(),
                        Path(remote_server_folder, server_file.name).as_posix(),
                    )
                    server_file.unlink(missing_ok=True)

                _handle_settings_common_update(
                    config, config_path, server_config_update
                )

            status_update(status, "Finished Updating Server")


def update_plugin(config: Config) -> None:
    """
    Update the plugins based on the given configuration.

    Args:
        config (Config): The configuration object containing update settings.
    """
    log = get_logger()
    status = get_rich_status()
    with get_rich_live(get_progress(), status):
        try:
            remote_connection = get_remote_connection()
            remote_plugins_folder = Path(
                remote_connection.base_dir, "plugins"
            ).as_posix()
            plugins_folder = get_appdir().caches_path / "plugins"
            plugins_folder.mkdir(exist_ok=True)
            is_remote = True
        except RuntimeError:
            plugins_folder = Path(config.get("settings.server_folder").data, "plugins")
            is_remote = False

        if not plugins_folder.exists():
            log.error(
                f"I don't know how you do it, but your {plugins_folder} is missing for some reason"
            )
            return 1

        update_order: list[str] = config.get("settings.update_order").data
        updater_list: list[type[PluginUpdater]] = [
            get_plugin_updater(name) for name in update_order
        ]

        plugins: dict[str, dict] = config.get("plugins").data

        with ThreadPoolExecutor(5) as worker:
            jobs: list[Future] = []
            status_update(status, "Updating plugins")
            for plugin_name, plugin_data in plugins.items():
                status_update(status, f"Adding job for {plugin_name}", no_log=True)

                # skip plugins that are marked as excluded or don't exist
                old_plugin = plugins_folder / plugin_data.get("file", ".unknown")
                if plugin_data["exclude"]:
                    log.warning(f"Plugin {plugin_name} is excluded, skipping")
                    continue

                if not (
                    remote_connection.exists(
                        Path(remote_plugins_folder, old_plugin.name).as_posix()
                    )
                    if is_remote
                    else old_plugin.exists()
                ):
                    log.warning(f"Plugin {plugin_name} is a leftover, skipping")
                    continue

                jobs.append(
                    worker.submit(
                        _handle_plugin_update,
                        updater_list,
                        plugins_folder,
                        plugin_name,
                        plugin_data,
                        config.get("updater_settings.plugin").data,
                    )
                )

            status_update(status, "All job added, waiting for completion")
            try:
                while not all([x.done() for x in jobs]) and not stop_event.is_set():
                    time.sleep(1)
            except (KeyboardInterrupt, Exception):
                stop_event.set()
            finally:
                worker.shutdown(wait=False, cancel_futures=True)

            for job in jobs:
                try:
                    if job.cancelled() or not job.result():
                        continue
                except Exception:
                    log.exception("Failed to update plugin")
                    continue
                config_path, new_plugin_file, resource_data, plugin_config_update = (
                    job.result()
                )
                plugin_name = resource_data.name
                old_plugin = Path(plugins_folder / plugins[plugin_name]["file"])
                if is_remote:
                    old_plugin_remote = Path(remote_plugins_folder, old_plugin.name)
                    try:
                        if remote_connection.exists(old_plugin_remote.as_posix()):
                            remote_connection.remove(old_plugin_remote.as_posix())
                    except Exception:
                        log.warning(
                            "Failed to remove old plugin from remote storage, "
                            + f"make sure to delete them manually: [bold]{plugin_name} [cyan]{old_plugin.name}"
                        )

                    log.info(f"[green]Uploading {new_plugin_file.name}")
                    _handle_remote_upload(
                        remote_connection,
                        new_plugin_file.as_posix(),
                        f"{remote_plugins_folder}/{new_plugin_file.name}",
                    )
                    new_plugin_file.unlink(missing_ok=True)
                else:
                    if old_plugin.absolute() != new_plugin_file.absolute():
                        old_plugin.unlink(missing_ok=True)

                log.info(
                    f"[green]Update config for {plugin_name} [cyan]{new_plugin_file.name}"
                )

                _handle_plugin_meta_update(
                    config, plugin_name, new_plugin_file, resource_data
                )
                _handle_plugin_updater_update(
                    config, config_path, plugin_name, plugin_config_update
                )
                _handle_settings_common_update(
                    config, config_path, plugin_config_update
                )
            status_update(status, "Finished updating plugins")


def update_all(config: Config, opt: argparse.Namespace) -> None:
    """
    Update the server and plugins.

    Args:
        config (Config): The configuration object containing update settings.
        opt (argparse.Namespace): Parsed command line options.
    """
    log = get_logger()
    last_update = config.get("last_update").data
    if last_update and not opt.force:
        today = parse_date_datetime(datetime.now())
        last_update = parse_date_datetime(last_update)
        cooldown = timedelta(
            hours=config.get("settings.update_cooldown", sy.YAML(12, sy.Int())).data
        )

        # Check time elapsed since the last update
        if (today - last_update) <= cooldown:
            # Calculate the remaining time
            remaining = (last_update + cooldown) - today
            log.info(
                f"Updater still in cooldown, {round(remaining.total_seconds() / 3600)} hours remaining"
            )
            return

    update_server(config)
    update_plugin(config)
    config.set("last_update", str(parse_date_datetime(datetime.now())))
    config.save()
    config.reload()
