from contextlib import suppress
from pathlib import Path
from urllib.parse import ParseResult

from rich.prompt import Prompt

from .cmd_opts import get_cmd_opts, parse_cmd
from .config.config import Config
from .downloader.downloader import setup_downloader
from .logger.logger import get_logger, setup_logger
from .manager.external import ext_register
from .manager.plugin import (
    get_plugin_updater_settings_default,
    get_plugin_updaters,
    plugin_updater_register,
)
from .manager.server import (
    get_server_types,
    get_server_updater_settings_default,
    server_updater_register,
)
from .meta import AppDir, get_appdir, setup_appdir, stop_event
from .remote_storage.ftp import FTPStorage
from .remote_storage.remote import get_remote_connection, setup_remote_connection
from .remote_storage.sftp import SFTPStorage
from .remote_storage.smb import SMBStorage
from .remote_storage.webdav import WebdavStorage
from .rich import console
from .task.scan import scan_plugins
from .task.update import update_all
from .updater.plugin.bukkit import BukkitUpdater
from .updater.plugin.custom import CustomUrlPluginUpdater
from .updater.plugin.github import GithubUpdater
from .updater.plugin.hangar import HangarUpdater
from .updater.plugin.jenkins import JenkinsUpdater
from .updater.plugin.modrinth import ModrinthUpdater
from .updater.plugin.spigot import SpigotUpdater
from .updater.server.bungee import BungeeUpdater
from .updater.server.custom import CustomUrlServerUpdater
from .updater.server.paper import PaperUpdater
from .updater.server.purpur import PurpurUpdater
from .utils.config import fix_config, update_server_type
from .utils.url import parse_url


def _initialize_environment(cmd_opts):
    setup_appdir(AppDir(cmd_opts.config_dir, cmd_opts.config_path))
    appdir = get_appdir()
    for x in [
        appdir.base_dir,
        appdir.ext_updater_path,
        appdir.logs_path,
        appdir.caches_path,
    ]:
        x.mkdir(parents=True, exist_ok=True)

    setup_logger(appdir.logs_path)


def _register_updaters():
    server_updater_register(PurpurUpdater)
    server_updater_register(PaperUpdater)
    server_updater_register(BungeeUpdater)
    server_updater_register(CustomUrlServerUpdater)

    plugin_updater_register(CustomUrlPluginUpdater)
    plugin_updater_register(BukkitUpdater)
    plugin_updater_register(SpigotUpdater)
    plugin_updater_register(HangarUpdater)
    plugin_updater_register(ModrinthUpdater)
    plugin_updater_register(GithubUpdater)
    plugin_updater_register(JenkinsUpdater)


def _get_server_folder(config: Config):
    log = get_logger()
    server_folder: str = config.get("settings.server_folder").data
    if not server_folder:
        while True:
            server_folder = Prompt.ask(
                "Enter server folder (i.e. /home/username/server)", console=console
            )
            if "://" in server_folder or Path(server_folder).exists():
                config.set("settings.server_folder", server_folder)
                break
            log.error("Invalid server folder, is folder exists?")
    return server_folder


def _setup_server_folder(config: Config):
    log = get_logger()
    server_folder = _get_server_folder(config)

    if "://" in server_folder:
        parsed_url = parse_url(server_folder)
        log.info(f"Setting up {parsed_url.scheme} storage connection")
        try:
            _connect_remote_storage(parsed_url, config)
        except (BaseException, Exception):
            log.exception("Failed to setup remote connection")
            exit()
    else:
        if not Path(server_folder).is_absolute():
            config.set(
                "settings.server_folder",
                str(Path(server_folder).expanduser().absolute()),
            )


def _configure_updater_settings(config: Config):
    if not config.get("settings.update_order").data:
        config.set("settings.update_order", list(get_plugin_updaters().keys()))
    else:
        update_order = config.get("settings.update_order").data
        update_order = [x for x in update_order if x in get_plugin_updaters()]
        update_order.extend([x for x in get_plugin_updaters() if x not in update_order])

    fix_config(
        config.strictyaml["updater_settings"]["server"],
        get_server_updater_settings_default(),
        "Updater Settings Server",
    )
    fix_config(
        config.strictyaml["updater_settings"]["plugin"],
        get_plugin_updater_settings_default(),
        "Updater Settings Plugin",
    )
    update_server_type(config, get_server_types())


def _connect_remote_storage(parsed_url: ParseResult, config: Config):
    match parsed_url.scheme:
        case "sftp":
            setup_remote_connection(
                SFTPStorage(
                    parsed_url.hostname,
                    parsed_url.port,
                    parsed_url.username,
                    parsed_url.password,
                    config.get("settings.sftp_key").data,
                ),
                parsed_url.path,
            )
        case "ftp":
            setup_remote_connection(
                FTPStorage(
                    parsed_url.hostname,
                    parsed_url.port,
                    parsed_url.username,
                    parsed_url.password,
                ),
                parsed_url.path,
            )
        case "smb":
            setup_remote_connection(
                SMBStorage(
                    parsed_url.hostname,
                    parsed_url.port,
                    parsed_url.username.replace("%40", "@"),
                    parsed_url.password,
                ),
                parsed_url.path,
            )
        case "webdav" | "webdavs":
            protocol = "http" if parsed_url.scheme == "webdav" else "https"
            setup_remote_connection(
                WebdavStorage(
                    parsed_url.hostname,
                    parsed_url.port,
                    parsed_url.username,
                    parsed_url.password,
                    protocol,
                ),
                parsed_url.path,
            )
        case _:
            raise RuntimeError(f"Unsupported protocol: {parsed_url.scheme}")


def main():
    try:
        parse_cmd()
        cmd_opts = get_cmd_opts()

        _initialize_environment(cmd_opts)
        appdir = get_appdir()

        # Registering updater
        _register_updaters()

        # Register external updater
        ext_register(appdir.ext_updater_path)

        setup_downloader()

        log = get_logger()
        log.info("Loading config")
        config = Config()
        config.load(appdir.config_path)
        _setup_server_folder(config)

        _configure_updater_settings(config)

        config.save()
        config.reload()

        if cmd_opts.scan_only:
            scan_plugins(config)
        else:
            scan_plugins(config)
            update_all(config)
        stop()
    except (Exception, KeyboardInterrupt):
        stop()
        console.print_exception()


def stop():
    stop_event.set()
    with suppress(Exception):
        get_remote_connection().close()


if __name__ == "__main__":
    main()
