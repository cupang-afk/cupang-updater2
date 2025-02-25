import json
import re
from typing import Any, Literal

from ...utils.date import parse_date_string
from ...utils.url import check_content_type, make_requests, make_url


class GithubAPI:
    def __init__(self, repo: str, token: str = None):
        """
        Initialize the GithubAPI object.

        Args:
            repo (str): The name of the Github repository, e.g. "EssentialsX/Essentials"
            prerelease (bool, optional): Whether to include prereleases in the query.
                Defaults to False.
            token (str, optional): The Github API token to use for authentication.
                Defaults to None.
        """

        self.repo = repo
        self.api = "https://api.github.com"
        self.token = token

        self.headers = {"Accept": "application/json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _github_to_json(self, *url_parts, **url_query) -> dict[str, Any] | None:
        """
        Helper function to perform a GET request to a Github API endpoint.

        Args:
            *url_parts: The parts of the URL to make the request to.
            **url_query: The query parameters to add to the URL.

        Returns:
            dict[str, Any] | None: The JSON response from the API, or None if an
                error occurred.
        """
        url = make_url(*url_parts, **url_query)
        res = make_requests(url, headers=self.headers)
        if not check_content_type(res, self.headers["Accept"]):
            return
        try:
            return json.loads(res.read())
        except json.JSONDecodeError:
            return None

    def get_releases_data(
        self,
        _filter: Literal["prerelease", "release", "all"] = "all",
        per_page: int = 10,
        page: int = 1,
    ) -> list[dict[str, Any]] | None:
        """
        Get the list of releases for the given repository.

        Args:
            _filter (Literal["prerelease", "release", "all"], optional):
                Whether to include prereleases or releases in the query.
                Defaults to "all".
            per_page (int, optional): The number of items to return per page.
                Defaults to 10.
            page (int, optional): The page number to query. Defaults to 1.

        Returns:
            list[dict[str, Any]] | None: The list of release data, or None if an error
                occurred.
        """

        releases = self._github_to_json(
            self.api, "repos", self.repo, "releases", per_page=per_page, page=page
        )

        if not releases:
            return None

        releases = [x for x in releases if not x.get("draft", False)]

        if _filter == "prerelease":
            releases = [x for x in releases if x.get("prerelease", False)]
        elif _filter == "release":
            releases = [x for x in releases if not x.get("prerelease", False)]
        releases = list(
            sorted(
                releases,
                key=lambda x: parse_date_string(x["published_at"]),
                reverse=True,
            )
        )
        return releases

    def get_release_data(self, tag: str = "latest") -> dict[str, Any] | None:
        """
        Get the release data for a specific tag in the given repository.

        Args:
            tag (str, optional): The tag to query. Defaults to "latest".

        Returns:
            dict[str, Any] | None: The release data, or None if an error occurred.
        """
        if tag == "latest":
            return self._github_to_json(
                self.api, "repos", self.repo, "releases", "latest"
            )
        return self._github_to_json(
            self.api, "repos", self.repo, "releases", "tags", tag
        )

    def get_tag_data(self, tag: str) -> dict[str, Any] | None:
        """
        Get the tag data for a specific tag in the given repository.

        Args:
            tag (str): The tag to query.

        Returns:
            dict[str, Any] | None: The tag data, or None if an error occurred.
        """

        return self._github_to_json(
            self.api, "repos", self.repo, "git", "ref", "tags", tag
        )

    def get_asset_data(
        self, release_data: dict[str, Any], name_regex: str
    ) -> dict[str, Any] | None:
        """
        Get the URL of an asset from the release data that matches the given name regex.

        Args:
            release_data (dict[str, Any]): The release data containing the assets.
            name_regex (str): The regex pattern to match the asset name.

        Returns:
            str | None: The URL of the matching asset, or None if no match is found.
        """
        if not release_data:
            return

        _name_regex = re.compile(name_regex)
        assets = list(
            filter(lambda x: _name_regex.match(x["name"]), release_data["assets"])
        )
        return assets[0] if assets else None

    def get_asset_url(self, asset_data: dict[str, Any]) -> str | None:
        return asset_data["browser_download_url"] if asset_data else None

    def get_commit_sha(self, tag_data: dict[str, Any]) -> str | None:
        """
        Get the commit SHA for the given tag data.

        Args:
            tag_data (dict[str, Any]): The tag data.

        Returns:
            str | None: The commit SHA, or None if an error occurred.
        """
        return tag_data["object"]["sha"] if tag_data and "object" in tag_data else None
