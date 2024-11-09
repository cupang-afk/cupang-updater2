from copy import deepcopy

import strictyaml as sy

from ..config.default import default_plugin
from ..config.schema import get_plugin_schema, get_plugin_updater_settings_schema
from ..logger.logger import get_logger
from ..updater.base import CommonData
from ..updater.plugin.base import PluginUpdater, PluginUpdaterConfig
from ..utils.common import reindent

_dummy = (CommonData("", ""), PluginUpdaterConfig())
_plugin_updater_settings_schema = get_plugin_updater_settings_schema()
_plugin_schema = get_plugin_schema()
_default = {
    "plugin": sy.load(
        default_plugin,
        sy.MapCombined(
            _plugin_schema,
            sy.Str(),
            sy.EmptyNone() | sy.Any(),
        ),
    ),
    "plugin_updater_settings": sy.as_document(
        {},
        sy.EmptyDict()
        | sy.MapCombined(
            _plugin_updater_settings_schema,
            sy.Str(),
            sy.EmptyNone() | sy.Any(),
        ),
    ),
}
_updaters: dict[str, type[PluginUpdater]] = {}


##
def _update_plugin_updater_settings_schema(path: str, schema: sy.Validator):
    """Update the plugin updater settings schema.

    Args:
        path (str): The path in the settings that this schema is for.
        schema (sy.Validator): The schema for this path.
    """
    _plugin_updater_settings_schema[sy.Optional(path)] = schema
    _default["plugin_updater_settings"]._validator = sy.EmptyDict() | sy.MapCombined(
        _plugin_updater_settings_schema,
        sy.Str(),
        sy.EmptyNone() | sy.Any(),
    )


def _update_plugin_schema(path: str, schema: sy.Validator):
    """Update the plugin schema.

    Args:
        path (str): The path in the settings that this schema is for.
        schema (sy.Validator): The schema for this path.

    """
    _plugin_schema[sy.Optional(path)] = schema
    _default["plugin"]._validator = sy.MapCombined(
        _plugin_schema,
        sy.Str(),
        sy.EmptyNone() | sy.Any(),
    )


def _update_plugin_updater_settings_value(path: str, value: str):
    """Update the plugin updater settings value in the default configuration.

    Args:
        path (str): The path in the settings that this value is for.
        value (str): The value to set.

    """
    _default["plugin_updater_settings"][path] = value


def _update_plugin_value(path: str, value: str):
    """Update the plugin value in the default configuration.

    Args:
        path (str): The path in the settings that this value is for.
        value (str): The value to set.

    """
    _default["plugin"][path] = value


def _update_updater(path: str, updater: type[PluginUpdater]):
    """Update the mapping of plugin updaters.

    Args:
        path (str): The path in the settings for this plugin.
        updater (type[PluginUpdater]): The plugin updater class.

    """

    _updaters[path] = updater


##


def get_plugin_updater_settings_default() -> sy.YAML:
    """Retrieve the default plugin updater settings.

    Returns:
        sy.YAML: A deepcopy of the default plugin updater settings.
    """
    return deepcopy([_default["plugin_updater_settings"]])[0]


def get_plugin_default() -> sy.YAML:
    """Retrieve the default plugin configuration.

    Returns:
        sy.YAML: A deepcopy of the default plugin configuration.
    """
    return deepcopy([_default["plugin"]])[0]


def get_plugin_updater(config_path: str) -> type[PluginUpdater] | None:
    """
    Retrieve the plugin updater class for a given configuration path.

    Args:
        config_path (str): The configuration path to look up.

    Returns:
        type[PluginUpdater] | None: The plugin updater class if found,
                                    otherwise None.
    """
    return _updaters.get(config_path)


def get_plugin_updaters() -> dict[str, type[PluginUpdater]]:
    """Retrieve a dictionary of all plugin updaters.

    Returns:
        dict[str, type[PluginUpdater]]: A dictionary of all plugin updaters.
    """
    return _updaters


def plugin_updater_register(plugin_updater: type[PluginUpdater]):
    """
    Register a plugin updater and updating schemas and default values.

    Args:
        plugin_updater (type[PluginUpdater]): The plugin updater class to register.

    """
    log = get_logger()
    try:
        updater_name = plugin_updater.get_updater_name()
        config_path = plugin_updater.get_config_path()
        version = plugin_updater.get_updater_version()
        config_schema = plugin_updater.get_config_schema()
    except NotImplementedError as error:
        log.exception(f"Failed to register {plugin_updater}: {error}")
        return

    log.info(f"Registering plugin updater: {updater_name} ({version})")

    if config_path in _updaters:
        log.warning(f"Plugin updater already registered: {updater_name} ({version})")
        return

    try:
        plugin_updater(*_dummy)
    except Exception:
        log.exception(f"Failed to register plugin updater: {updater_name} ({version})")
        return

    schema_types = (sy.Map, sy.MapCombined, sy.MapPattern)

    if config_schema.plugin_schema:
        _update_plugin_schema(config_path, config_schema.plugin_schema)
        if isinstance(config_schema.plugin_default, str) or isinstance(
            config_schema.plugin_schema, schema_types
        ):
            default_value = reindent(config_schema.plugin_default, 6)
            yaml_data = sy.load(default_value, config_schema.plugin_schema)
            _update_plugin_value(config_path, yaml_data)
        else:
            _update_plugin_value(config_path, config_schema.plugin_default)

    if config_schema.common_schema:
        _update_plugin_updater_settings_schema(config_path, config_schema.common_schema)
        if isinstance(config_schema.common_default, str) or isinstance(
            config_schema.common_schema, schema_types
        ):
            default_value = reindent(config_schema.common_default, 6)
            yaml_data = sy.load(default_value, config_schema.common_schema)
            _update_plugin_updater_settings_value(config_path, yaml_data)
        else:
            _update_plugin_updater_settings_value(
                config_path, config_schema.common_default
            )

    _update_updater(config_path, plugin_updater)
