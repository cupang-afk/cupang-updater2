from cupang_downloader.downloader import Downloader

from ..cmd_opts import get_cmd_opts
from ..logger.logger import get_logger
from ..meta import stop_event

_downloader: Downloader = None


def _setup_fallback_downloader():
    """Setup the fallback downloader, which is a urllib based downloader."""
    global _downloader
    log = get_logger()
    log.info("Setup fallback downloader")
    from cupang_downloader.downloaders.urllib_downloader import UrllibDownloader

    _downloader = Downloader(UrllibDownloader(cancel_event=stop_event))


def setup_downloader():
    """
    Set up the downloader.

    Note:
        If the specified downloader is not supported, or if the
        downloader setup fails, a fallback downloader is used.
    """

    global _downloader
    log = get_logger()
    if _downloader:
        log.warning("Downloader already setup")
        return
    cmd_opts = get_cmd_opts()
    try:
        match cmd_opts.downloader:
            case "aria2c":
                log.info("Setup aria2c downloader")
                from cupang_downloader.downloaders.aria2_downloader import (
                    Aria2Downloader,
                )

                _downloader = Downloader(
                    Aria2Downloader(
                        aria2c_bin=cmd_opts.aria2c_bin, cancel_event=stop_event
                    )
                )
            case "wget":
                log.info("Setup wget downloader")
                from cupang_downloader.downloaders.wget_downloader import WgetDownloader

                _downloader = Downloader(
                    WgetDownloader(wget_bin=cmd_opts.wget_bin, cancel_event=stop_event)
                )
            case "curl":
                log.info("Setup curl downloader")
                from cupang_downloader.downloaders.curl_downloader import CurlDownloader

                _downloader = Downloader(
                    CurlDownloader(curl_bin=cmd_opts.curl_bin, cancel_event=stop_event)
                )
            case "pycurl":
                log.info("Setup pycurl downloader")
                from cupang_downloader.downloaders.pycurl_downloader import (
                    PycurlDownloader,
                )

                _downloader = Downloader(PycurlDownloader(cancel_event=stop_event))
            case "requests":
                log.info("Setup requests downloader")
                from cupang_downloader.downloaders.requests_downloader import (
                    RequestsDownloader,
                )

                _downloader = Downloader(RequestsDownloader(cancel_event=stop_event))
            case _:
                log.warning(f"Unsupported downloader: {cmd_opts.downloader}")
                _setup_fallback_downloader()
    except Exception as e:
        log.error(
            f"Failed to setup downloader {cmd_opts.downloader} because {type(e).__qualname__}: {e}"
        )
        _setup_fallback_downloader()


def get_downloader() -> Downloader:
    """
    Retrieve the Downloader instance.

    If the Downloader instance has not been set up yet, a RuntimeError is raised.

    Returns:
        Downloader: The Downloader instance.
    """
    if not isinstance(_downloader, Downloader):
        raise RuntimeError("Downloader is not initialized")
    return _downloader
