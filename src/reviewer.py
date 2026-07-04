"""
reviewer.py
Sends file diffs to Claude and parses back structured review feedback.
"""

import json
import re
from anthropic import Anthropic
from config import Config

SYSTEM_PROMPT = """You are an expert senior software engineer performing a pull request code review.

You will be given the unified diff (patch) for ONE file changed in a pull request.
Review ONLY the added/changed lines (lines starting with '+' in the patch, ignoring the '+' itself).
Focus on:
- Bugs, logic errors, and edge cases
- Security vulnerabilities (injection, secrets, unsafe deserialization, etc.)
- Performance issues
- Readability, naming, and maintainability
- Missing error handling
- Style/convention issues (only if notable)

Do NOT comment on lines that were not changed. Do NOT invent line numbers that
don't appear in the diff. Be concise and specific. Skip trivial nitpicks unless
nothing else is wrong. If the file looks good, return an empty comments list.

Respond with ONLY valid JSON (no markdown fences, no prose outside the JSON),
matching exactly this schema:

{
  "summary": "one or two sentence overall assessment of this file's changes",
  "comments": [
    {
      "line": <integer, the NEW-file line number from the diff>,
      "severity": "critical" | "warning" | "suggestion",
      "comment": "specific, actionable feedback"
    }
  ]
}
"""


class Reviewer:
    def __init__(self, api_key: str = None, model: str = None):
        self.client = Anthropic(api_key=api_key or Config.ANTHROPIC_API_KEY)
        self.model = model or Config.ANTHROPIC_MODEL

    def review_file_diff(self, filename: str, patch: str) -> dict:
        """
        Sends a single file's diff to Claude and returns parsed JSON:
        {"summary": str, "comments": [{"line": int, "severity": str, "comment": str}]}
        """
        user_prompt = f"File: {filename}\n\nDiff:\n```diff\n{patch}\n```"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()

        return self._parse_json_response(raw_text)

    @staticmethod
    def _parse_json_response(raw_text: str) -> dict:
        # Strip markdown code fences if the model added them despite instructions
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
        try:
            data = json.loads(cleaned)
            data.setdefault("summary", "")
            data.setdefault("comments", [])
            return data
        except json.JSONDecodeError:
            return {
                "summary": "Could not parse model output for this file.",
                "comments": [],
                "raw_output": raw_text,
            }

    def summarize_pr(self, file_summaries: list, pr_title: str, pr_body: str) -> str:
        """Produces a top-level PR review summary from all per-file summaries."""
        joined = "\n".join(f"- {f['filename']}: {f['summary']}" for f in file_summaries)
        prompt = (
            f"PR Title: {pr_title}\n"
            f"PR Description: {pr_body or '(none provided)'}\n\n"
            f"Per-file review summaries:\n{joined}\n\n"
            "Write a concise overall PR review summary (3-5 sentences) for the "
            "top of the review, covering the general quality of the change and "
            "any cross-cutting concerns. Plain text only, no markdown headers."
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()
