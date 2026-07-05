# GitHub Pull Request Review Agent

An AI agent that automatically reviews GitHub pull requests. It fetches a PR's
diff, sends each changed file to Claude for analysis, and posts the results
back to GitHub as inline review comments plus an overall summary.

## How it works

1. `github_client.py` talks to the GitHub REST API — fetches PR metadata and
   the diff ("patch") for every changed file.
2. `reviewer.py` sends each file's diff to Claude with a review-focused system
   prompt, and gets back structured JSON: a summary plus a list of
   `{line, severity, comment}` items.
3. `diff_utils.py` parses the raw diff to figure out which line numbers are
   actually valid targets for an inline GitHub comment (GitHub only allows
   commenting on lines that appear in the diff).
4. `main.py` orchestrates all of this, then either prints the review (dry run)
   or posts it to GitHub as a real PR review (`--post`).

## Project structure

```
github-pr-review-agent/
├── README.md
├── requirements.txt
├── .env.example
└── src/
    ├── config.py         # environment/config loading
    ├── github_client.py  # GitHub REST API wrapper
    ├── diff_utils.py      # unified diff parsing helpers
    ├── reviewer.py        # Claude-powered code review logic
    └── main.py            # CLI entry point
```

## Step-by-step setup

### 1. Prerequisites
- Python 3.9 or newer
- A GitHub account with access to the repo you want to review
- An Anthropic API key

### 2. Get a GitHub Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click **Generate new token** → **Fine-grained token** (recommended)
3. Under **Repository access**, select the repo(s) you want the agent to review
4. Under **Permissions**, grant:
   - **Pull requests**: Read and write
   - **Contents**: Read-only
5. Generate the token and copy it (you won't see it again)

*(A classic token with the `repo` scope also works if you prefer.)*

### 3. Get an Anthropic API key
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key and copy it

### 4. Install the project
```bash
# Unzip the project (if you haven't already) and enter it
cd github-pr-review-agent

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Configure your secrets
```bash
cp .env.example .env
```
Open `.env` and fill in:
```
GITHUB_TOKEN=ghp_your_real_token_here
ANTHROPIC_API_KEY=sk-ant-your_real_key_here
ANTHROPIC_MODEL=claude-sonnet-4-5
```

### 6. Run it

From inside the `src/` folder:

```bash
cd src

# Dry run — review a PR and print results, but don't post anything to GitHub
python main.py --repo octocat/hello-world --pr 42

# Review AND post the review as real comments on the PR
python main.py --repo octocat/hello-world --pr 42 --post

# Review every open PR in a repo
python main.py --repo octocat/hello-world --all-open --post

# Post a "request changes" review instead of a neutral comment
python main.py --repo octocat/hello-world --pr 42 --post --event REQUEST_CHANGES

# Print every generated comment as it's created (useful for debugging)
python main.py --repo octocat/hello-world --pr 42 --verbose
```

### 7. What you'll see on GitHub
When run with `--post`, the agent submits a single PR review containing:
- An overall summary comment at the top (🤖 Automated PR Review)
- Inline comments on the specific changed lines, each tagged by severity:
  - 🔴 Critical — likely bugs, security issues
  - 🟡 Warning — real but non-blocking issues
  - 🔵 Suggestion — style/readability improvements

## Extending the project
- **Run automatically on every PR**: wrap `main.py` in a GitHub Actions
  workflow that triggers on `pull_request` events and runs
  `python src/main.py --repo ${{ github.repository }} --pr ${{ github.event.pull_request.number }} --post`.
- **Change review strictness**: edit the `SYSTEM_PROMPT` in `reviewer.py`.
- **Skip more file types**: add patterns to `IGNORED_PATTERNS` in `config.py`.
- **Swap models**: change `ANTHROPIC_MODEL` in `.env`.

## Troubleshooting
- **401/403 from GitHub**: your token lacks permission on the repo, or has expired.
- **"Could not parse model output"**: the model didn't return valid JSON for
  that file; the raw text is included in the result for debugging — check
  `result["raw_output"]` if you're calling `Reviewer` programmatically.
- **No inline comments posted**: all suggested comments fell outside the
  diff's valid line ranges (rare edge case with certain diff formats) — a
  summary comment is posted instead as a fallback.
AI Review Agent Test