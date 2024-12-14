from copy import deepcopy

import strictyaml as sy

from ..config.schema import get_server_schema, get_server_updater_settings_schema
from ..logger.logger import get_logger
from ..updater.base import ResourceData
from ..updater.server.base import ServerUpdater, ServerUpdaterConfig
from ..utils.common import reindent
from ..utils.hash import FileHash

_dummy = (ResourceData("", "", FileHash.dummy()), ServerUpdaterConfig())
_server_updater_settings_schema = get_server_updater_settings_schema()
_server_schema = get_server_schema()
_default = {
    "server_updater_settings": sy.as_document(
        {},
        sy.EmptyDict()
        | sy.MapCombined(
            _server_updater_settings_schema,
            sy.Str(),
            sy.EmptyNone() | sy.Any(),
        ),
    )
}
# key as the updater because one updater can contain many server type
_updaters: dict[type[ServerUpdater], str] = {}


##
def _update_server_updater_settings_schema(path: str, schema: sy.Validator):
    """
    Update the server updater settings schema.

    Args:
        path (str): The path in the settings that this schema is for.
        schema (sy.Validator): The schema for this path.

    """

    _server_updater_settings_schema[sy.Optional(path)] = schema
    _default["server_updater_settings"]._validator = sy.EmptyDict() | sy.MapCombined(
        _server_updater_settings_schema,
        sy.Str(),
        sy.EmptyNone() | sy.Any(),
    )


def _update_server_updater_settings_value(path: str, value: sy.Validator):
    """
    Update the server updater settings value in the default configuration.

    Args:
        path (str): The path in the settings that this value is for.
        value (sy.Validator): The value to set.

    """

    _default["server_updater_settings"][path] = value


def _update_server_type(server_type: str):
    """
    Update the server type in the server schema.

    Args:
        server_type (str): The server type to add to the schema.
    """
    _server_schema["type"].update_server_type(server_type)


def _update_updater(server_types: list[str], updater: type[ServerUpdater]):
    """
    Update the mapping of server updaters.

    Args:
        server_types (list[str]): The server types that this server updater supports.
        updater (type[ServerUpdater]): The server updater class to register.

    """
    _updaters[updater] = server_types


##
def get_server_updater_settings_default() -> sy.YAML:
    """
    Retrieve the default server updater settings.

    Returns:
        sy.YAML: A deepcopy of the default server updater settings.
    """
    return deepcopy([_default["server_updater_settings"]])[0]


def get_server_types() -> list[str]:
    """
    Retrieve a list of all server types supported by the registered server updaters.

    Returns:
        list[str]: A sorted list of all server types supported by
            the registered server updaters.
    """
    result = list(set(x for y in _updaters.values() for x in y))
    result.sort()
    return result


def get_server_updaters(server_type: str) -> list[type[ServerUpdater]]:
    """
    Retrieve a list of all server updaters that support the given server type.

    Args:
        server_type (str): The server type to retrieve the updaters for.

    Returns:
        list[type[ServerUpdater]]: A list of all server updaters that support
            the given server type.
    """
    result = list(
        filter(
            lambda x: x is not None,
            map(
                lambda y: y[0] if server_type in y[1] else None,
                _updaters.items(),
            ),
        )
    )
    return result


def server_updater_register(server_updater: type[ServerUpdater]):
    """
    Register a server updater and updating schemas and default values.

    Args:
        server_updater (type[ServerUpdater]): The server updater class to register.

    """

    log = get_logger()
    try:
        updater_name = server_updater.get_updater_name()
        config_path = server_updater.get_config_path()
        version = server_updater.get_updater_version()
        config_schema = server_updater.get_config_schema()
        server_types = server_updater.get_server_types()
    except NotImplementedError as error:
        log.exception(f"Failed to register {server_updater}: {error}")
        return

    log.info(f"Registering server updater: {updater_name} ({version})")

    if config_path in _updaters:
        log.warning(f"Server updater already registered: {updater_name} ({version})")
        return

    try:
        server_updater(*_dummy)
    except Exception:
        log.exception(f"Failed to register server updater: {updater_name} ({version})")
        return

    for server_type in server_updater.get_server_types():
        _update_server_type(server_type)

    schema_types = (sy.Map, sy.MapCombined, sy.MapPattern)
    if config_schema.common_schema:
        _update_server_updater_settings_schema(config_path, config_schema.common_schema)
        if isinstance(config_schema.common_default, str) or isinstance(
            config_schema.common_schema, schema_types
        ):
            default_value = reindent(config_schema.common_default, 2)
            yaml_data = sy.load(default_value, config_schema.common_schema)
            _update_server_updater_settings_value(config_path, yaml_data)
        else:
            _update_server_updater_settings_value(
                config_path, config_schema.common_default
            )

    _update_updater(server_types, server_updater)
