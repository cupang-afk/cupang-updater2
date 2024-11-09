from pathlib import Path

from rich.prompt import Prompt

from .cmd_opts import opt
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
from .meta import AppDir
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


def main():
    cmd_args = opt.parse_args()
    appdir = AppDir(cmd_args.config_dir, cmd_args.config_path)

    for x in [
        appdir.base_dir,
        appdir.ext_updater_path,
        appdir.logs_path,
    ]:
        x.mkdir(parents=True, exist_ok=True)

    setup_logger(appdir.logs_path, cmd_args.debug)
    setup_downloader(cmd_args)

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

    ext_register(appdir.ext_updater_path)

    log = get_logger()
    config = Config()
    config.load(appdir.config_path)
    if not config.get("settings.server_folder").data:
        while True:
            server_folder = Prompt.ask(
                "Enter server folder (i.e. /home/username/server)", console=console
            )
            server_folder = Path(server_folder).expanduser().absolute()
            if server_folder.exists():
                config.set("settings.server_folder", server_folder.as_posix())
                break
            log.error("Invalid server folder, is folder exists?")
    if not config.get("settings.update_order").data:
        config.set("settings.update_order", list(get_plugin_updaters().keys()))
    else:
        update_order = config.get("settings.update_order").data
        update_order = [x for x in update_order if x in get_plugin_updaters().keys()]
        update_order.extend(
            [x for x in get_plugin_updaters().keys() if x not in update_order]
        )
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
    config.save()
    config.reload()

    if cmd_args.scan_only:
        scan_plugins(config)
    else:
        scan_plugins(config)
        update_all(config, cmd_args)


if __name__ == "__main__":
    main()
