"""
config.py
Loads and validates environment configuration for the PR Review Agent.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    GITHUB_API_URL = "https://api.github.com"

    # Files larger than this (in changed lines) get truncated before
    # being sent to the model, to control cost/context size.
    MAX_DIFF_LINES_PER_FILE = 400

    # File extensions the agent will skip (binaries, locks, generated code)
    IGNORED_PATTERNS = (
        ".lock", ".min.js", ".map", ".png", ".jpg", ".jpeg", ".gif",
        ".svg", ".ico", ".woff", ".woff2", ".ttf", ".pdf", ".zip",
        "package-lock.json", "yarn.lock", "poetry.lock",
    )

    @classmethod
    def validate(cls):
        missing = []
        if not cls.GITHUB_TOKEN:
            missing.append("GITHUB_TOKEN")
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if missing:
            print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
            print("Copy .env.example to .env and fill in your values.")
            sys.exit(1)
