"""
diff_utils.py
Parses unified diff "patch" text (as returned by GitHub's Files API) to
figure out which line numbers in the NEW version of a file were actually
added/changed. GitHub only allows inline review comments on lines that
appear in the diff, so we validate against this set before posting.
"""

import re

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def get_commentable_lines(patch: str) -> set:
    """
    Returns the set of new-file line numbers that can receive an inline
    review comment (i.e. lines that are context or additions within the diff).
    """
    if not patch:
        return set()

    commentable = set()
    new_line_num = None

    for line in patch.splitlines():
        match = HUNK_HEADER.match(line)
        if match:
            new_line_num = int(match.group(1))
            continue

        if new_line_num is None:
            continue

        if line.startswith("+"):
            commentable.add(new_line_num)
            new_line_num += 1
        elif line.startswith("-"):
            # Deleted line: doesn't exist in new file, don't advance new_line_num
            continue
        else:
            # Context line: exists in new file too
            commentable.add(new_line_num)
            new_line_num += 1

    return commentable


def truncate_patch(patch: str, max_lines: int) -> str:
    lines = patch.splitlines()
    if len(lines) <= max_lines:
        return patch
    truncated = lines[:max_lines]
    truncated.append(f"... (diff truncated, {len(lines) - max_lines} more lines omitted) ...")
    return "\n".join(truncated)
