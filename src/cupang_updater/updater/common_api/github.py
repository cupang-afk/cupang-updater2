import json
import re
from typing import Any

from ...utils.date import parse_date_string
from ...utils.url import check_content_type, make_requests, make_url


class GithubAPI:
    def __init__(self, repo: str, prerelease: bool = False, token: str = None):
        """
        Initialize the GithubAPI object.

        Args:
            repo (str): The name of the Github repository, e.g. "EssentialsX/Essentials"
            prerelease (bool, optional): Whether to include prereleases in the query. Defaults to False.
            token (str, optional): The Github API token to use for authentication. Defaults to None.
        """

        self.repo = repo
        self.api = "https://api.github.com"
        self.prerelease = prerelease
        self.token = token

        self.headers = {"Accept": "application/json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        self.latest_data: dict[str, Any] = None
        self.tag_data: dict[str, Any] = None

    def _get_releases(self) -> list[dict[str, Any]] | None:
        """
        Get the list of releases for the given repository.

        Returns:
            list[dict[str, Any]] | None: The list of release data, or None if an error occurred.
        """
        res = make_requests(
            make_url(self.api, "repos", self.repo, "releases"), headers=self.headers
        )
        if not check_content_type(res, self.headers["Accept"]):
            return
        return json.loads(res.read())

    def _get_latest_release(self) -> dict[str, Any] | None:
        """
        Get the latest release for the given repository.

        Returns:
            dict[str, Any] | None: The latest release data, or None if an error occurred.
        """
        if self.latest_data:
            return self.latest_data

        latest_data = self._get_releases()
        if not latest_data:
            return

        _latest_data = filter(
            (lambda x: (bool(x["prerelease"]) == self.prerelease) and not x["draft"]),
            latest_data,
        )
        _latest_data = sorted(
            _latest_data,
            key=lambda x: parse_date_string(x["created_at"]),
            reverse=True,
        )
        self.latest_data = _latest_data[0]
        return self.latest_data

    def _get_tag_data(self, tag: str) -> dict[str, Any] | None:
        """
        Get the tag data for a specific tag in the given repository.

        Args:
            tag (str): The tag to query.

        Returns:
            dict[str, Any] | None: The tag data, or None if an error occurred.
        """
        if self.tag_data and self.tag_data["tag"] == tag:
            return self.tag_data

        res = make_requests(
            make_url(
                self.api,
                "repos",
                self.repo,
                "git",
                "ref",
                "tags",
                tag,
            ),
            headers=self.headers,
        )
        if not check_content_type(res, self.headers["Accept"]):
            return
        self.tag_data = json.loads(res.read())
        return self.tag_data

    def _get_asset(self, name_regex: re.Pattern) -> dict[str, Any] | None:
        """
        Get the first asset matching the given name regex in the latest release.

        Args:
            name_regex (re.Pattern): The regex to match the asset name.

        Returns:
            dict[str, Any] | None: The asset data, or None if an error occurred.
        """
        latest_data = self._get_latest_release()
        if not latest_data:
            return

        assets = list(
            filter(lambda x: name_regex.match(x["name"]), latest_data["assets"])
        )
        return assets[0] if assets else None

    def get_asset_url(self, name_regex: str):
        """
        Get the URL of the latest release asset matching the given name regex.

        Args:
        - name_regex (str): The name regex to match.

        Returns:
        - str | None: The URL of the asset, or None if an error occurred.
        """
        asset = self._get_asset(re.compile(name_regex))
        return asset["browser_download_url"] if asset else None

    def get_commit(self) -> str | None:
        """
        Get the commit SHA for the latest release tag.

        Returns:
            str | None: The commit SHA, or None if an error occurred.
        """
        tag = self.get_tag()
        if not tag:
            return
        tag_data = self._get_tag_data(tag)
        return tag_data["object"]["sha"][7:] if tag_data else None

    def get_file_name(self, name_regex: str):
        """
        Get the name of the latest release asset matching the given name regex.

        Args:
        - name_regex (str): The name regex to match.

        Returns:
        - str | None: The name of the asset, or None if an error occurred.
        """
        asset = self._get_asset(re.compile(name_regex))
        return asset["name"] if asset else None

    def get_release_name(self) -> str | None:
        """
        Get the name of the latest release.

        Returns:
            str | None: The release name, or None if an error occurred.
        """
        latest_release = self._get_latest_release()
        return latest_release["name"] if latest_release else None

    def get_tag(self) -> str | None:
        """
        Get the tag of the latest release.

        Returns:
            str | None: The tag name, or None if an error occurred.
        """
        latest_release = self._get_latest_release()
        return latest_release["tag_name"] if latest_release else None
