from rich.status import Status

from ..logger.logger import get_logger


def status_update(status: Status, msg: str, level: str = "info", no_log: bool = False):
    """
    Update the status message and log it.

    Args:
        status (Status): The rich status object to update.
        msg (str): The message to set in the status update.
        level (str, optional): The logging level to use. Defaults to "info".
        no_log (bool, optional): If True, the message will not be logged.
            Defaults to False.
    """
    status.update(msg)
    if no_log:
        return
    log = get_logger()
    getattr(log, level, log.info)(msg)
