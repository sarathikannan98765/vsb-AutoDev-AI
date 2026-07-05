"""
reviewer.py
Uses Ollama to review GitHub Pull Request file diffs.
"""

import json
import re
import requests
from config import Config

SYSTEM_PROMPT = """You are an expert senior software engineer performing a pull request code review.

You will be given the unified diff (patch) for ONE file changed in a pull request.

Review ONLY the added or changed lines.

Focus on:
- Bugs
- Logic errors
- Security
- Performance
- Readability
- Error handling
- Code quality

Return ONLY valid JSON.

Example:

{
  "summary": "Overall review",
  "comments": [
    {
      "line": 25,
      "severity": "warning",
      "comment": "Possible null pointer here."
    }
  ]
}
"""


class Reviewer:

    def __init__(self, api_key=None, model=None):
        self.model = model or Config.OLLAMA_MODEL
        self.url = Config.OLLAMA_URL

    def review_file_diff(self, filename: str, patch: str) -> dict:

        user_prompt = f"""
File:
{filename}

Diff:

{patch}
"""

        payload = {
            "model": self.model,
            "prompt": SYSTEM_PROMPT + "\n\n" + user_prompt,
            "stream": False
        }

        response = requests.post(
            self.url,
            json=payload
        )

        response.raise_for_status()

        raw_text = response.json()["response"].strip()

        return self._parse_json_response(raw_text)

    @staticmethod
    def _parse_json_response(raw_text: str):

        cleaned = re.sub(
            r"^```(?:json)?|```$",
            "",
            raw_text.strip(),
            flags=re.MULTILINE
        ).strip()

        try:

            data = json.loads(cleaned)

            data.setdefault("summary", "")

            data.setdefault("comments", [])

            return data

        except json.JSONDecodeError:

            return {
                "summary": "Could not parse Ollama output.",
                "comments": [],
                "raw_output": raw_text,
            }

    def summarize_pr(self, file_summaries, pr_title, pr_body):

        joined = "\n".join(
            f"- {f['filename']}: {f['summary']}"
            for f in file_summaries
        )

        prompt = f"""
PR Title:
{pr_title}

PR Description:
{pr_body}

Per File Summary:

{joined}

Write an overall Pull Request review in 3-5 sentences.
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(
            self.url,
            json=payload
        )

        response.raise_for_status()

        return response.json()["response"].strip()