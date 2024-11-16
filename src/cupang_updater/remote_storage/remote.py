from .base import RemoteIO

_connection: RemoteIO = None


def setup_remote_connection(connection: RemoteIO, base_dir: str):
    global _connection
    _connection = connection
    _connection.base_dir = base_dir


def get_remote_connection() -> RemoteIO:
    if not isinstance(_connection, RemoteIO):
        raise RuntimeError("Remote connection is not initialized")
    return _connection
