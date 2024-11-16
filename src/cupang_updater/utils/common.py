import re
import shutil
import stat
import textwrap
from pathlib import Path

from packaging.version import InvalidVersion, Version

_reindent_pattern = re.compile(r"(?<=\S) +")


def ensure_path(path: str | Path) -> Path:
    """
    Ensure that the given path is a Path object.

    Args:
        path (str | Path): Path to ensure.

    Returns:
        Path: Ensured Path object.
    """
    return path if isinstance(path, Path) else Path(path)


def reindent(text: str, size: int, ch: str = " ") -> str:
    """
    Removes existing indentation from the text and applies a new indentation.

    Args:
        text (str): Input text with existing indentation.
        size (int): Number of spaces for the new indentation.
        ch (str): Character used for indentation (default is space).

    Returns:
        str: Text with the new indentation applied.
    """

    text = _reindent_pattern.sub(" ", text)

    return textwrap.indent(textwrap.dedent(text), ch * size)


def parse_version(version: str) -> Version:
    """
    Parse a given version string into a valid version number.

    Args:
        version (str): Input version string.

    Returns:
        Version: Parsed version number.

    Notes:
        If the version string is invalid, it will be matched against a regex to
        extract the version number. If the regex does not match, it will be
        replaced with "1.0".
    """
    try:
        _version = Version(version).base_version
    except InvalidVersion:
        _match_version = re.search(r"([\d.]+)", version)
        if not _match_version:
            _version = "1.0"
        else:
            _version = "".join(_match_version.group(1))
    except Exception:
        _version = "1.0"
    return Version(_version)


def remove_suffix(path: Path) -> Path:
    """
    Remove the suffix of a Path object.

    Args:
        path (Path): Input Path object.

    Returns:
        Path: Path object with the suffix removed.
    """
    path = ensure_path(path)
    if path.suffix == "":
        return path
    return remove_suffix(path.with_suffix(""))


def rmdir(dir: Path):
    """
    Recursively removes the directory and its contents.

    Parameters:
        dir: Path to the directory to be removed.
    """
    for _ in dir.rglob("*"):
        _.chmod(stat.S_IWRITE)
    shutil.rmtree(dir.absolute())
