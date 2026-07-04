"""
github_client.py
Thin wrapper around the GitHub REST API for the endpoints the agent needs:
fetching PR metadata, fetching the diff, and posting review comments.
"""

import requests
from config import Config


class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or Config.GITHUB_TOKEN
        self.base_url = Config.GITHUB_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> dict:
        resp = self.session.get(self._url(f"/repos/{owner}/{repo}/pulls/{pr_number}"))
        resp.raise_for_status()
        return resp.json()

    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> list:
        """Returns list of changed files with their patch (diff) text."""
        files = []
        page = 1
        while True:
            resp = self.session.get(
                self._url(f"/repos/{owner}/{repo}/pulls/{pr_number}/files"),
                params={"per_page": 100, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            files.extend(batch)
            page += 1
        return files

    def list_open_pull_requests(self, owner: str, repo: str) -> list:
        resp = self.session.get(
            self._url(f"/repos/{owner}/{repo}/pulls"),
            params={"state": "open", "per_page": 100},
        )
        resp.raise_for_status()
        return resp.json()

    def post_issue_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict:
        """Posts a general (non-line-specific) comment on the PR conversation tab."""
        resp = self.session.post(
            self._url(f"/repos/{owner}/{repo}/issues/{pr_number}/comments"),
            json={"body": body},
        )
        resp.raise_for_status()
        return resp.json()

    def post_review(self, owner: str, repo: str, pr_number: int,
                     commit_id: str, body: str, comments: list,
                     event: str = "COMMENT") -> dict:
        """
        Posts a full PR review with optional inline comments.
        comments: list of {"path": str, "line": int, "body": str}
        event: "COMMENT" | "APPROVE" | "REQUEST_CHANGES"
        """
        payload = {
            "commit_id": commit_id,
            "body": body,
            "event": event,
            "comments": comments,
        }
        resp = self.session.post(
            self._url(f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()
