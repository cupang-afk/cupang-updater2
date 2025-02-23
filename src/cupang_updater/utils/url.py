import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.client import HTTPResponse

from ..logger.logger import get_logger
from ..meta import default_headers


def make_url(base: str, *paths: str, **queries: str) -> str:
    """
    Make a URL by joining the given base URL with the given paths and queries.

    Args:
        base (str): The base URL to join with.
        paths (str): Paths to join with the base URL.
        queries (str): Query parameters to add to the URL.

    Returns:
        str: The joined URL.

    Example:
    >>> make_url("https://example.com", "path", "to", "resource", key="value")
    "https://example.com/path/to/resource?key=value"
    """
    base = base.rstrip("/")
    parsed = urllib.parse.urlparse(base)
    paths = [str(x) for x in paths]
    joined_path = "/".join((*parsed.path.split("/"), *paths))
    query_string = urllib.parse.urlencode({k: str(v) for k, v in queries.items()})
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, joined_path, "", query_string, "")
    )


def make_requests(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> HTTPResponse | None:
    """
    Make an HTTP request to the given URL using the given method and headers.

    Args:
        url (str): The URL to request.
        method (str): The HTTP method to use (default: "GET").
        headers (dict[str, str]): Additional HTTP headers to include in the request.

    Returns:
        HTTPResponse | None: The response from the server, or None if an error occurred.

    Example:
    >>> make_requests("https://example.com", "GET", {"Accept": "text/html"})
    <http.client.HTTPResponse object at 0x...>
    >>> make_requests(
    ...     "https://example.com", "POST", {"Content-Type": "application/json"}
    ... )
    <http.client.HTTPResponse object at 0x...>
    """
    headers = {**default_headers, **(headers or {})}
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        res = urllib.request.urlopen(req, timeout=timeout)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        msg = f'Error while requesting data from "{url}" {type(e).__qualname__}: {e}'
        try:
            get_logger().error(msg)
        except RuntimeError:
            print(msg)
        return
    return res


def check_content_type(res: HTTPResponse, content_type: str) -> bool:
    """
    Check if the given HTTPResponse has the given content type.

    Args:
        res (HTTPResponse): The HTTP response to check.
        content_type (str): The content type to check for.

    Returns:
        bool: True if the content type matches, False otherwise.
    """
    if res is None:
        return False
    if res.status != HTTPStatus.OK:
        return False

    if (
        res.getheader("content-type", "").split(";", maxsplit=1)[0].lower()
        != content_type.lower()
    ):
        return False
    return True


def parse_url(url: str) -> urllib.parse.ParseResult:
    """
    Parse a URL into a urllib.parse.ParseResult object.

    Args:
        url (str): The URL to parse.

    Returns:
        urllib.parse.ParseResult: The parsed URL.

    Example:
    >>> parse_url("https://example.com/path/to/resource?key=value")
    ParseResult(scheme='https', netloc='example.com', path='/path/to/resource',
                params='', query='key=value', fragment='')
    """
    # I should use this directly tbh, but whatever
    return urllib.parse.urlparse(url)
