"""
github_client.py

Thin wrapper around the GitHub REST API.
"""

import requests
from config import Config


class GitHubClient:

    def __init__(self, token=None):
        self.token = token or Config.GITHUB_TOKEN
        self.base_url = Config.GITHUB_API_URL

        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _url(self, path):
        return f"{self.base_url}{path}"

    def get_pull_request(self, owner, repo, pr_number):
        resp = self.session.get(
            self._url(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        )

        if not resp.ok:
            print(resp.status_code)
            print(resp.text)

        resp.raise_for_status()
        return resp.json()

    def get_pull_request_files(self, owner, repo, pr_number):

        files = []
        page = 1

        while True:

            resp = self.session.get(
                self._url(f"/repos/{owner}/{repo}/pulls/{pr_number}/files"),
                params={
                    "per_page": 100,
                    "page": page
                }
            )

            if not resp.ok:
                print(resp.status_code)
                print(resp.text)

            resp.raise_for_status()

            batch = resp.json()

            if not batch:
                break

            files.extend(batch)
            page += 1

        return files

    def list_open_pull_requests(self, owner, repo):

        resp = self.session.get(
            self._url(f"/repos/{owner}/{repo}/pulls"),
            params={
                "state": "open",
                "per_page": 100
            }
        )

        if not resp.ok:
            print(resp.status_code)
            print(resp.text)

        resp.raise_for_status()

        return resp.json()

    def post_issue_comment(self, owner, repo, pr_number, body):

        resp = self.session.post(
            self._url(f"/repos/{owner}/{repo}/issues/{pr_number}/comments"),
            json={
                "body": body
            }
        )

        if not resp.ok:
            print("GitHub Error")
            print(resp.status_code)
            print(resp.text)

        resp.raise_for_status()

        return resp.json()

    def post_review(
        self,
        owner,
        repo,
        pr_number,
        commit_id,
        body,
        comments,
        event="COMMENT"
    ):

        payload = {
            "commit_id": commit_id,
            "body": body,
            "event": event,
            "comments": comments
        }

        resp = self.session.post(
            self._url(f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"),
            json=payload
        )

        if not resp.ok:
            print("========== GitHub Error ==========")
            print(resp.status_code)
            print(resp.text)
            print("==================================")

        resp.raise_for_status()

        return resp.json()