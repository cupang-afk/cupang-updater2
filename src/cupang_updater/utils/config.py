import strictyaml as sy

from ..config.config import Config
from ..config.schema import get_server_schema
from ..logger.logger import get_logger


def fix_config(data: sy.YAML, default_data: sy.YAML, name: str | None = None):
    """Make data keys consistent with default_data keys."""

    log = get_logger()
    # Remove keys from data that are not in default_data
    for key in data.data.keys() - default_data.data.keys():
        log.info(f"[red]Removing key {key}" + (f" from {name}" if name else ""))
        del data[key]

    # Add keys to data that are present in default_data but not in data
    for key in default_data.data.keys() - data.data.keys():
        log.info(f"[green]Adding key {key}" + (f" for {name}" if name else ""))
        data[key] = default_data[key]

    return data


def update_server_type(config: Config, server_types: list[str]):
    """
    Update comments in server.type
    """
    # sort
    server_types.sort()

    server_schema = get_server_schema()
    st_value: str = config.get("server.type").data
    server_as_yaml: str = config.get("server").as_yaml()
    _server_as_yaml = ""
    for line in server_as_yaml.splitlines():
        if "type:" in line:
            st_index = line.find(st_value)
            line = line[: st_index + len(st_value)].rstrip()
            line += f" # one of these: {', '.join(server_types)}"
        _server_as_yaml += line + "\n"

    new_server_config = sy.load(_server_as_yaml, sy.Map(server_schema))
    config.set("server", new_server_config)
