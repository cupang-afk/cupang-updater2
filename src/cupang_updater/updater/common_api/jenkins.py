import json
import re
from typing import Any

from ...utils.url import check_content_type, make_requests, make_url


# TODO make it more like new GithubAPI approach
class JenkinsAPI:
    def __init__(self, url: str):
        """
        Initialize the JenkinsAPI object.

        Args:
            url (str): The base URL for the Jenkins server.
        """
        self.url = url
        self.headers = {"Accept": "application/json"}

    def _jenkins_to_json(self, *url_parts, **url_query) -> dict[str, Any] | None:
        """
        Helper function to perform a GET request to a Jenkins API endpoint.

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

    def get_build_data(
        self, build_number: int = -1
    ) -> tuple[dict[str, Any], int] | tuple[None, None]:
        """
        Get the build data for a specific build number.

        Args:
            build_number (int, optional): The build number to query. If not
                provided, the latest successful build will be queried.
                Defaults to -1.

        Returns:
            tuple[dict[str, Any], int] | tuple[None, None]: The build data, or
                None if an error occurred.
        """

        if build_number < 1:
            last_successful_build = self._jenkins_to_json(
                self.url, "api", "json", tree="lastSuccessfulBuild[id]"
            )
            if not last_successful_build:
                return None, None
            build_number = int(last_successful_build["lastSuccessfulBuild"]["id"])
        build = self._jenkins_to_json(
            self.url, str(build_number), "api", "json", tree="artifacts[*]"
        )
        if not build:
            return None, None
        return build, build_number

    def get_artifact_data(
        self, build_data: dict[str, Any], name_regex: str
    ) -> dict[str, Any] | None:
        """
        Get the data for an artifact from the build data
        that matches the given name regex.

        Args:
            build_data (dict[str, Any]): The build data containing the artifacts.
            name_regex (str): The regex pattern to match the artifact file name.

        Returns:
            dict[str, Any] | None: The data of the matching artifact,
                or None if no match is found.
        """
        if not build_data:
            return

        _name_regex = re.compile(name_regex)
        artifacts = [
            x for x in build_data["artifacts"] if _name_regex.match(x["fileName"])
        ]
        return artifacts[0] if artifacts else None

    def get_artifact_url(
        self, artifact_data: dict[str, Any], build_number: int
    ) -> str | None:
        """
        Get the URL of an artifact from the build data.

        Args:
            artifact_data (dict[str, Any]): The artifact data from the build data.
            build_number (int): The build number that the artifact belongs to.

        Returns:
            str | None: The URL of the matching artifact, or None if an error occurred.
        """
        if not artifact_data:
            return

        return make_url(
            self.url,
            str(build_number),
            "artifact",
            artifact_data["relativePath"],
        )
