import argparse
import sys
from pathlib import Path

from .meta import AppDir, app_name, app_version

is_compiled = (
    hasattr(sys, "_MEIPASS")
    or getattr(sys, "frozen", False)
    or "__compiled__" in globals()
)

cwd = (Path(sys.executable).parent) if is_compiled else Path.cwd()
_temp_appdir = AppDir(cwd / app_name)
_opt_parsed = None


opt = argparse.ArgumentParser(
    app_name, description=f"{app_name} {app_version}\nA Minecraft Server/Plugin Updater"
)

opt_main = opt.add_argument_group("Main")
opt_config = opt.add_argument_group("Config")
opt_extra = opt.add_argument_group("Extra")
opt_downloader = opt.add_argument_group("Downloader")

opt_main.add_argument(
    "-v",
    "--version",
    action="version",
    version=f"{app_name} {app_version}",
    help="Show version information",
)
opt_main.add_argument(
    "-f",
    "--force",
    dest="force",
    action="store_true",
    default=False,
    help="Force to do update check despite the cooldown (default: %(default)s)",
)
opt_main.add_argument(
    "-fr",
    "--force-leftover-update",
    dest="force_leftover_update",
    action="store_true",
    default=False,
    help="Force to update leftover plugins (default: %(default)s)",
)
opt_main.add_argument(
    "-sv",
    "--skip-version-check",
    dest="skip_version_check",
    action="store_true",
    default=False,
    help="Skip version check, ultimately re-download server/plugins (default: %(default)s)",
)
opt_main.add_argument(
    "-sc",
    "--scan-only",
    dest="scan_only",
    action="store_true",
    default=False,
    help="Scan plugins without checking update (default: %(default)s)",
)
opt_main.add_argument(
    "-V" "--debug",
    dest="debug",
    action="store_true",
    default=False,
    help="Enable debug mode (default: %(default)s)",
)
opt_config.add_argument(
    "-cc",
    "--config-dir",
    dest="config_dir",
    action="store",
    metavar="PATH",
    type=Path,
    default=_temp_appdir.base_dir,
    help=f"Set config dir (default: {_temp_appdir.base_dir.relative_to(cwd)})",
)
opt_config.add_argument(
    "-c",
    "--config",
    dest="config_path",
    action="store",
    metavar="PATH",
    type=Path,
    default=None,  # automaticaly decided when AppDir is created unless set explicitly
    help=f"Set config file (default: {_temp_appdir.config_path.relative_to(cwd)})",
)
opt_config.add_argument(
    "-fcl",
    "--force-cleanup",
    dest="force_cleanup",
    action="store_true",
    default=False,
    help="Force clean leftover plugins (default: %(default)s)",
)
opt_downloader.add_argument(
    "-dl",
    "--downloader",
    dest="downloader",
    action="store",
    # metavar="DOWNLOADER",
    choices=["aria2c", "wget", "curl", "pycurl", "requests", "fallback"],
    type=str,
    default="pycurl",
    help="Set downloader (default: %(default)s)",
)
opt_downloader.add_argument(
    "-pdl",
    "--parallel-downloads",
    dest="parallel_downloads",
    action="store",
    metavar="INT",
    type=int,
    default=5,
    help="Set how many simultaneous downloads (default: %(default)s)",
)
opt_downloader.add_argument(
    "-mr",
    "--max-retries",
    dest="max_retries",
    action="store",
    metavar="INT",
    type=int,
    default=5,
    help="Set maximum number of retries for downloads (default: %(default)s)",
)
opt_downloader.add_argument(
    "--aria2c-bin",
    dest="aria2c_bin",
    action="store",
    metavar="PATH",
    type=Path,
    default=None,
    help="Set aria2c binary (default: None)",
)
opt_downloader.add_argument(
    "--wget-bin",
    dest="wget_bin",
    action="store",
    metavar="PATH",
    type=Path,
    default=None,
    help="Set wget binary (default: None)",
)
opt_downloader.add_argument(
    "--curl-bin",
    dest="curl_bin",
    action="store",
    metavar="PATH",
    type=Path,
    default=None,
    help="Set curl binary (default: None)",
)


def parse_cmd():
    global _opt_parsed
    if _opt_parsed is None:
        _opt_parsed = opt.parse_args()


def get_cmd_opts():
    return _opt_parsed
