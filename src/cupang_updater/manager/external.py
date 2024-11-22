import inspect
import sys
from importlib.util import module_from_spec, spec_from_file_location
from itertools import chain
from pathlib import Path

from ..logger.logger import get_logger
from ..utils.common import ensure_path, remove_suffix

_is_registered = False


def _load_ext(name: str, path: str | Path):
    """
    Load a python module from file by name and path.

    Args:
        name: The name to use for the module in sys.modules
        path: The path to the python file
    """
    caller_file = Path(inspect.stack()[1].filename)
    if Path(__file__) != caller_file:
        raise RuntimeError("This function is not meant to be called directly.")

    path = ensure_path(path)
    spec = spec_from_file_location(name, path.absolute())
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)


def ext_register(*ext_paths: str | Path):
    """
    Register external updaters.

    Args:
        *ext_paths: str or Path, the paths to the python files containing the external updaters
    """
    global _is_registered
    log = get_logger()
    if _is_registered:
        log.warning("Ext already registered")
        return

    for path in chain.from_iterable(x.glob("*") for x in ext_paths):
        try:
            if len(path.suffixes) == 1 and path.suffix == ".py":
                sys.path.append(str(path.parent.absolute()))
                _load_ext(f"ext_updater.{remove_suffix(path).name}", path)
        except Exception:
            log.exception(f'Exception occur when trying to register "{path}"')

    sys.path[:] = list(set(sys.path))
    _is_registered = True
