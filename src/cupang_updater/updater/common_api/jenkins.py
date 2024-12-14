import json
import re
from typing import Any

from ...utils.url import check_content_type, make_requests, make_url


class JenkinsAPI:
    def __init__(self, url: str):
        """
        Initialize the JenkinsAPI object.

        Args:
            url (str): The base URL for the Jenkins server.
        """
        self.url = url
        self.headers = {"Accept": "application/json"}
        self.latest_data: dict[str, Any] = None
        self.latest_build_number: int = -1  # in case build number not found

    def _get_latest_data(self) -> dict[str, Any] | None:
        """
        Retrieve the latest build data from the Jenkins server.

        Returns:
            dict[str, Any] | None: The latest build data, or None if an error occurred.
        """
        if self.latest_data:
            return self.latest_data

        res = make_requests(
            make_url(self.url, "api", "json", tree="lastSuccessfulBuild[id]"),
            headers=self.headers,
        )
        if not check_content_type(res, self.headers["Accept"]):
            return
        self.latest_build_number = int(
            json.loads(res.read())["lastSuccessfulBuild"]["id"]
        )

        res = make_requests(
            make_url(
                self.url,
                str(self.latest_build_number),
                "api",
                "json",
                tree="artifacts[*]",
            ),
            headers=self.headers,
        )
        if not check_content_type(res, self.headers["Accept"]):
            return
        self.latest_data = json.loads(res.read())
        return self.latest_data

    def _get_artifact(self, name_regex: re.Pattern) -> str | None:
        """
        Retrieve the first artifact matching the provided name regex
            from the latest build data.

        Args:
            name_regex (re.Pattern): The regex pattern to match the artifact name.

        Returns:
            str | None: The matching artifact's information, or None if
                no match is found.
        """
        latest_data = self._get_latest_data()
        if not latest_data:
            return

        artifact = list(
            filter(lambda x: name_regex.match(x["fileName"]), latest_data["artifacts"])
        )

        return artifact[0] if artifact else None

    def get_build_number(self) -> int:
        """
        Get latest build number.

        Returns:
            int: The build number of the latest build.
        """
        if self.latest_build_number < 0:
            self._get_latest_data()
        return self.latest_build_number

    def get_artifact_url(self, name_regex: str) -> str | None:
        """
        Retrieve the URL of the first artifact matching the provided name regex
        from the latest build.

        Args:
            name_regex (str): The regex pattern to match the artifact name.

        Returns:
            str | None: The URL of the matching artifact, or None if no match is found.
        """
        artifact = self._get_artifact(re.compile(name_regex))
        if not artifact:
            return
        return make_url(
            self.url,
            str(self.latest_build_number),
            "artifact",
            artifact["relativePath"],
        )
