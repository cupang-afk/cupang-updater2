import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from rich.logging import RichHandler
from rich.markup import escape

from ..cmd_opts import get_cmd_opts
from ..meta import app_name
from ..rich import console
from ..utils.date import parse_date_string


class LogFormatting(logging.Formatter):
    """
    A formatter that adds a color prefix to the log message depending on the log level.

    If the `no_color` attribute is set to True, the color prefix will be removed from the message.

    Attributes:
        colors (dict): A dictionary of log levels to color prefixes.
        no_color (bool): Whether to add a color prefix to the message. Defaults to False.

    Methods:
        format(record: logging.LogRecord) -> str: Format the message of the log record.
    """

    colors = {
        logging.CRITICAL: "[bold black on red]",
        logging.ERROR: "[bold red on default]",
        logging.WARNING: "[yellow on default]",
        logging.INFO: "[default on default]",
        logging.DEBUG: "[green on default]",
    }

    def _remove_prefix(self, text: str):
        """Remove the color prefix from the log message.

        Args:
            text (str): The log message.

        Returns:
            str: The log message without the color prefix.
        """
        for color in self.colors.values():
            if text.startswith(color):
                text = text[len(color) :]
        return text

    def _add_prefix(self, text: str, prefix: str):
        """Add the color prefix to the log message.

        Args:
            text (str): The log message.
            prefix (str): The color prefix to add to the log message.

        Returns:
            str: The log message with the color prefix added.
        """
        text = prefix + self._remove_prefix(text)
        return text

    def _set_nocolor(self, _default=True):
        """
        Set the no_color attribute to True.

        This is used to disable the color prefix from the log messages.
        """

        self.no_color = _default

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the message of the log record.

        The formatter will add a color prefix to the message depending on the log level.
        If the logger name is not the root logger, it will be added to the message in the format
        of "[logger.name] message" with a bright blue color.

        If the `no_color` attribute is set to True, the color prefix will be removed from the message.
        """
        no_color = getattr(self, "no_color", False)
        color_prefix = self.colors.get(record.levelno, "[default on default]")
        msg_orig = self._remove_prefix(str(record.msg))
        record.msg = self._add_prefix(str(record.msg), color_prefix)

        # Add the logger name to the message if it is not the root logger
        names = record.name.split(".")[1:]
        if names:
            record.msg = self._add_prefix(
                escape("[" + "/".join(names) + "] ") + record.msg,
                "[bright_blue on default]" if not no_color else "",
            )

        # Remove color prefix from the message if no_color is True
        if no_color:
            record.msg = msg_orig

        return super().format(record)


_logger = None
_name_format = "console_*_*.log"
_date_format = "%Y-%m-%d"


def _get_next_exec_n(logs_folder: Path) -> int:
    """
    Get the next execution number for log files in the given folder.

    Args:
        logs_folder (Path): The path to the folder containing log files.

    Returns:
        int: The next execution number for naming a new log file.
    """
    date_files: dict[datetime, list[Path]] = {}

    for log_file in logs_folder.glob(_name_format):
        # Gets YYYY-MM-DD part
        date = parse_date_string(log_file.stem.split("_")[1]).date()
        if not isinstance(date_files.get(date, None), list):
            date_files[date] = [log_file]
        else:
            date_files[date].append(log_file)

    if not date_files:
        return 1

    latest_date = max(date_files.keys())

    execution_numbers = [
        int(log_file.stem.split("_")[-1]) for log_file in date_files[latest_date]
    ]

    return max(execution_numbers, default=0) + 1


def _rename_latest_log(logs_folder: Path) -> None:
    """
    Rename the latest log file with the current date and the next execution number.
    """
    latest_log = logs_folder / "latest.log"
    if not latest_log.is_file():
        return
    current_date = datetime.now()
    execution_number = _get_next_exec_n(logs_folder)
    new_name = f"console_{current_date.strftime(_date_format)}_{execution_number}.log"
    shutil.move(latest_log, logs_folder / new_name)


def _compress_old_logs(logs_folder: Path) -> None:
    """
    Compress logs that are at least one day old into a .zip file with the current date.
    """
    current_date = datetime.now().date()

    for log_file in logs_folder.glob(_name_format):
        log_date = parse_date_string(log_file.stem.split("_")[1]).date()
        if current_date == log_date:
            continue

        zip_file_path = logs_folder / f"{log_date.strftime(_date_format)}.zip"
        with zipfile.ZipFile(
            zip_file_path, mode="a", compression=zipfile.ZIP_BZIP2, compresslevel=9
        ) as zip_file:
            zip_file.write(log_file, log_file.name)

        log_file.unlink()


def setup_logger(logs_path: Path) -> None:
    """
    Set up and configure the logger for the application.

    Args:
        logs_path (Path): The directory path where log files are stored.
    """
    current_date = datetime.now().date()
    cmd_opts = get_cmd_opts()

    _rename_latest_log(logs_path)
    _compress_old_logs(logs_path)

    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)

    stream_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
        show_path=False,
    )
    file_handler = RichHandler(
        console=type(console)(
            file=(logs_path / "latest.log").open("a", encoding="utf-8"),
            tab_size=console.tab_size,
            width=88,
            no_color=True,
        ),
        rich_tracebacks=True,
        markup=True,
    )

    log_formatter = LogFormatting("%(message)s", datefmt="%X")
    file_formatter = LogFormatting("%(message)s", datefmt="%X")
    file_formatter._set_nocolor()

    stream_handler.setLevel(logging.INFO if not cmd_opts.debug else logging.DEBUG)
    stream_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    logger.info(f"Logger created at {current_date.strftime(_date_format)}")

    global _logger
    _logger = logger


def get_logger() -> logging.Logger:
    """Return the logger instance.

    The logger is created by calling `setup_logger`. If the logger is not
    initialized, a RuntimeError is raised.

    Returns:
    - logging.Logger: The logger instance.
    """
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return _logger
