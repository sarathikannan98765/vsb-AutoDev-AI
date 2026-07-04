"""
main.py
CLI entry point for the GitHub Pull Request Review Agent.

Usage:
    python main.py --repo owner/name --pr 42
    python main.py --repo owner/name --pr 42 --post
    python main.py --repo owner/name --all-open --post
    python main.py --repo owner/name --pr 42 --post --event REQUEST_CHANGES
"""

import argparse
import sys

from config import Config
from github_client import GitHubClient
from reviewer import Reviewer
from diff_utils import get_commentable_lines, truncate_patch


def should_skip_file(filename: str) -> bool:
    return any(filename.endswith(pattern) or pattern in filename
               for pattern in Config.IGNORED_PATTERNS)


def review_pull_request(gh: GitHubClient, reviewer: Reviewer,
                         owner: str, repo: str, pr_number: int,
                         post: bool, event: str, dry_run_verbose: bool):
    print(f"\n=== Reviewing {owner}/{repo}#{pr_number} ===")

    pr = gh.get_pull_request(owner, repo, pr_number)
    commit_id = pr["head"]["sha"]
    files = gh.get_pull_request_files(owner, repo, pr_number)

    if not files:
        print("No changed files found.")
        return

    all_inline_comments = []
    file_summaries = []

    for f in files:
        filename = f["filename"]
        patch = f.get("patch")

        if should_skip_file(filename):
            print(f"  - skipping {filename} (ignored file type)")
            continue

        if not patch:
            print(f"  - skipping {filename} (no textual diff, likely binary)")
            continue

        print(f"  - reviewing {filename} ...")
        patch_for_model = truncate_patch(patch, Config.MAX_DIFF_LINES_PER_FILE)
        result = reviewer.review_file_diff(filename, patch_for_model)
        file_summaries.append({"filename": filename, "summary": result.get("summary", "")})

        valid_lines = get_commentable_lines(patch)

        for c in result.get("comments", []):
            line = c.get("line")
            if line not in valid_lines:
                # Can't attach inline comment to a line not present in the diff;
                # note it in the summary instead of failing the whole review.
                print(f"    (skipped out-of-diff comment on {filename}:{line})")
                continue
            severity_tag = {"critical": "🔴", "warning": "🟡", "suggestion": "🔵"}.get(
                c.get("severity", "suggestion"), "🔵"
            )
            body = f"{severity_tag} **{c.get('severity', 'suggestion').title()}**: {c.get('comment', '')}"
            all_inline_comments.append({"path": filename, "line": line, "body": body})

            if dry_run_verbose:
                print(f"    [{filename}:{line}] {body}")

    summary = reviewer.summarize_pr(file_summaries, pr.get("title", ""), pr.get("body", ""))
    review_body = f"## 🤖 Automated PR Review\n\n{summary}"

    print(f"\n--- Summary ---\n{summary}\n")
    print(f"Total inline comments generated: {len(all_inline_comments)}")

    if post:
        if all_inline_comments:
            gh.post_review(owner, repo, pr_number, commit_id, review_body,
                            all_inline_comments, event=event)
            print(f"Posted review with {len(all_inline_comments)} inline comment(s) "
                  f"and event={event}.")
        else:
            gh.post_issue_comment(owner, repo, pr_number, review_body)
            print("Posted summary comment (no inline comments to attach).")
    else:
        print("Dry run: nothing was posted to GitHub. Use --post to submit the review.")


def main():
    parser = argparse.ArgumentParser(description="GitHub Pull Request Review Agent")
    parser.add_argument("--repo", required=True, help="owner/repo, e.g. octocat/hello-world")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", type=int, help="Pull request number to review")
    group.add_argument("--all-open", action="store_true", help="Review all open PRs in the repo")
    parser.add_argument("--post", action="store_true",
                         help="Actually post the review to GitHub (default: dry run)")
    parser.add_argument("--event", default="COMMENT",
                         choices=["COMMENT", "APPROVE", "REQUEST_CHANGES"],
                         help="Review event type when posting (default: COMMENT)")
    parser.add_argument("--verbose", action="store_true", help="Print each comment as it's generated")
    args = parser.parse_args()

    Config.validate()

    try:
        owner, repo = args.repo.split("/", 1)
    except ValueError:
        print("ERROR: --repo must be in the form owner/repo")
        sys.exit(1)

    gh = GitHubClient()
    reviewer = Reviewer()

    if args.all_open:
        prs = gh.list_open_pull_requests(owner, repo)
        if not prs:
            print("No open pull requests found.")
            return
        for pr in prs:
            review_pull_request(gh, reviewer, owner, repo, pr["number"],
                                 args.post, args.event, args.verbose)
    else:
        review_pull_request(gh, reviewer, owner, repo, args.pr,
                             args.post, args.event, args.verbose)


if __name__ == "__main__":
    main()
