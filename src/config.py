import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    # -----------------------
    # GitHub
    # -----------------------
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
    GITHUB_API_URL = "https://api.github.com"

    # -----------------------
    # Ollama
    # -----------------------
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    OLLAMA_URL = os.getenv(
        "OLLAMA_URL",
        "http://localhost:11434/api/generate"
    )

    # -----------------------
    # Review Settings
    # -----------------------
    MAX_DIFF_LINES_PER_FILE = 300

    IGNORED_PATTERNS = [
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".pdf",
        ".zip",
        ".exe",
        ".dll",
        ".class",
        ".jar",
        ".lock",
        ".min.js",
        ".min.css",
    ]

    @staticmethod
    def validate():

        if not Config.GITHUB_TOKEN:
            raise ValueError("Missing GITHUB_TOKEN in .env")

        if not Config.GITHUB_USERNAME:
            raise ValueError("Missing GITHUB_USERNAME in .env")

        if not Config.OLLAMA_MODEL:
            raise ValueError("Missing OLLAMA_MODEL in .env")

        if not Config.OLLAMA_URL:
            raise ValueError("Missing OLLAMA_URL in .env")