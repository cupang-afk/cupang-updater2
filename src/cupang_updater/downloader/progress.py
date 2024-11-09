from threading import Lock

from cupang_downloader import DownloadJob
from rich.progress import Progress, TaskID, TransferSpeedColumn

from ..logger.logger import get_logger
from ..rich import console

_progresses: dict[str, TaskID] = {}
_lock = Lock()
_progress = Progress(
    *Progress.get_default_columns(),
    TransferSpeedColumn(),
    console=console,
    transient=True,
)


def _create_unique_id(o) -> str:
    """
    Create a unique identifier for the given object.

    The unique identifier is a hexadecimal representation of the object's ID.

    Args:
        o (object): The object for which to create a unique identifier.

    Returns:
        str: A unique identifier for the given object.
    """
    return hex(id(o))


def _remove_bar(k: str):
    """
    Remove a progress bar from the progress tracker.

    This function removes the progress bar for the given key from the progress tracker
    and removes the key from the dictionary.

    Args:
        k (str): The key for the progress bar to remove.
    """
    _progress.update(_progresses[k], visible=False)
    _progress.remove_task(_progresses[k])
    # using lock we can now remove the progress from dictionary
    # by using lock, we ensure that only one thread can edit the dictionary
    with _lock:
        del _progresses[k]


def _on_start(j: DownloadJob):
    """
    Callred when a download job starts downloading.

    This function creates a new progress bar in the progress tracker for the given download job.
    The progress bar is not visible until the download job starts.

    Args:
        j (DownloadJob): The download job for which to create a new progress bar.
    """
    k = _create_unique_id(j)
    # create new progress bar and save to progresses
    _progresses[k] = _progress.add_task(
        description=j.progress_name, total=None, visible=False
    )


def _on_finish(j: DownloadJob):
    """
    Called when a download job finishes downloading.

    This function removes the progress bar for the given download job from the progress tracker.

    Args:
        j (DownloadJob): The download job that finished downloading.
    """
    log = get_logger()
    log.info(f"Finished downloading {j.progress_name}")
    k = _create_unique_id(j)
    _remove_bar(k)


def _on_progress(j: DownloadJob, t: int, d: int, **extra):
    """
    Called when a download job sends a progress update.

    This function updates the progress bar for the given download job in the progress tracker.

    Args:
        j (DownloadJob): The download job that sent the progress update.
        t (int): The total number of bytes to download.
        d (int): The number of bytes downloaded so far.
        **extra (dict): Any additional extra arguments sent by the download job.
    """
    k = _create_unique_id(j)
    # we set to None because rich.progress has pulse animation when total is None
    t = None if t == 0 else t
    _progress.update(_progresses[k], total=t, completed=d, visible=True)


def _on_cancel(j: DownloadJob):
    """
    Called when a download job is canceled.

    This function removes the progress bar for the given download job from the progress tracker.

    Args:
        j (DownloadJob): The download job that was canceled.
    """

    log = get_logger()
    log.warning(f"Canceled {j.progress_name}")
    k = _create_unique_id(j)
    _remove_bar(k)


def _on_error(j: DownloadJob, err):
    """
    Called when a download job encounters an error.

    This function logs an error message and removes the progress bar for the given download job
    from the progress tracker.

    Args:
        j (DownloadJob): The download job that encountered an error.
        err (Exception): The exception that was raised during the download.
    """
    log = get_logger()
    log.exception(f"Error while downloading {j.progress_name}")

    k = _create_unique_id(j)
    _remove_bar(k)


def get_callbacks():
    """
    Retrieve a dictionary of callback functions for download events.

    Returns:
        dict: A dictionary containing callback functions for various
            download events, including start, finish, progress,
            cancel, and error.
    """
    return dict(
        on_start=_on_start,
        on_finish=_on_finish,
        on_progress=_on_progress,
        on_cancel=_on_cancel,
        on_error=_on_error,
    )


def get_progress() -> Progress:
    """
    Get the shared progress bar.

    Returns:
        Progress: The shared progress bar.
    """
    return _progress
