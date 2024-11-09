import strictyaml as sy
from strictyaml.validators import MapValidator


class ServerType(sy.Str):
    def __init__(self):
        self.server_types = []
        super().__init__()

    def validate_scalar(self, chunk):
        val = chunk.contents
        if val.lower() not in self.server_types:
            chunk.expecting_but_found(f"when expecting one of {self.server_types}")
        return super().validate_scalar(chunk)

    def update_server_type(self, server_type: str):
        self.server_types.append(server_type)
        # make it unique
        self.server_types = list(sorted(list(set(self.server_types))))


class NonEmptyStr(sy.Str):
    def validate_scalar(self, chunk):
        if chunk.contents == "":
            chunk.expecting_but_found("when expecting some string")
        return chunk.contents


_last_update_schema: sy.Validator = sy.EmptyNone() | sy.Datetime()
_hashes: dict[str, sy.Validator] = {
    "md5": sy.EmptyNone() | sy.Str(),
    "sha1": sy.EmptyNone() | sy.Str(),
    "sha256": sy.EmptyNone() | sy.Str(),
    "sha512": sy.EmptyNone() | sy.Str(),
}
_server_updater_settings_schema: dict[str, MapValidator] = {}
_plugin_updater_settings_schema: dict[str, MapValidator] = {}
_settings_schema: dict[str, sy.Validator] = {
    "server_folder": sy.Str(),
    "update_cooldown": sy.Int(),
    "keep_removed": sy.Bool(),
    "update_order": sy.EmptyList() | sy.Seq(sy.Str()),
}
_server_schema: dict[str, sy.Validator] = {
    "enable": sy.Bool(),
    "file": sy.Str(),
    "type": ServerType(),
    "version": NonEmptyStr(),
    "build_number": sy.EmptyNone() | sy.Int(),
    "custom_url": sy.EmptyNone() | sy.Str(),
    "hashes": sy.Map(_hashes),
}
_plugin_schema: dict[str, sy.Validator] = {
    "exclude": sy.Bool(),
    "file": sy.Str(),
    "version": sy.Str(),
    "authors": sy.EmptyNone() | sy.Seq(sy.Str()),
    "hashes": sy.Map(_hashes),
}


def get_server_updater_settings_schema() -> dict[str, MapValidator]:
    """
    Get the schema for the server updater settings.

    Returns:
        dict[str, MapValidator]: A dictionary where the key is the path in the settings and the value is the schema for that path.
    """
    return _server_updater_settings_schema


def get_plugin_updater_settings_schema() -> dict[str, MapValidator]:
    """
    Get the schema for the plugin updater settings.

    Returns:
        dict[str, MapValidator]: A dictionary where the key is the path in the settings and the value is the schema for that path.
    """
    return _plugin_updater_settings_schema


def get_server_schema() -> dict[str, sy.Validator]:
    """
    Get the schema for the server configuration.

    Returns:
        dict[str, sy.Validator]: A dictionary where the key is the server configuration field and the value is the corresponding validator.
    """
    return _server_schema


def get_plugin_schema() -> dict[str, sy.Validator]:
    """
    Get the schema for the plugin configuration.

    Returns:
        dict[str, sy.Validator]: A dictionary where the key is the plugin configuration field and the value is the corresponding validator.
    """

    return _plugin_schema


def get_config_schema() -> sy.Map:
    """
    Get the complete configuration schema.

    Returns:
        sy.Map: A strictyaml Map validator that contains the schema for
        the configuration fields, including 'last_update', 'settings',
        'updater_settings', 'server', and 'plugins'.
    """
    return sy.Map(
        {
            "last_update": _last_update_schema,
            "settings": sy.Map(_settings_schema),
            # updater_settings is dynamic
            "updater_settings": sy.Map(
                {
                    # using sy.MapCombined as a safe guard in case the updater is fail to register
                    "server": sy.EmptyDict()
                    | sy.MapCombined(
                        _server_updater_settings_schema,
                        sy.Str(),
                        sy.EmptyNone() | sy.Any(),
                    ),
                    "plugin": sy.EmptyDict()
                    | sy.MapCombined(
                        _plugin_updater_settings_schema,
                        sy.Str(),
                        sy.EmptyNone() | sy.Any(),
                    ),
                }
            ),
            "server": sy.Map(_server_schema),
            # plugin is dynamic
            "plugins": sy.EmptyDict()
            | sy.MapPattern(
                sy.Str(),
                # using sy.MapCombined as a safe guard in case the updater is fail to register
                sy.MapCombined(
                    _plugin_schema,
                    sy.Str(),
                    sy.EmptyNone() | sy.Any(),
                ),
            ),
        }
    )


# FOOT NOTE
# this schema is managed by cupang_updater.manager module (for dynamicaly updating schema)
