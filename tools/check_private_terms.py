#!/usr/bin/env python
"""Block a commit that would publish a private name.

    uv run python tools/check_private_terms.py <file>...              # pre-commit: staged files
    uv run python tools/check_private_terms.py --commit-msg <file>    # commit-msg: the message

Checks for what tools/export_claude_sessions.py scrubs from transcripts: this machine's
hostname and username, the names in the gitignored private_terms.txt, and links to Claude
Code web sessions. The exporter cleans what it writes; this check covers everything else
that gets committed, such as reflections, score files, the README and commit messages.

A hit is reported by file, line and the placeholder the name stands for, never by the
name itself, so the check's own output cannot leak it.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_claude_sessions import CLAUDE_SESSION_LINK, PRIVATE_TERMS  # noqa: E402

CHECKS = PRIVATE_TERMS + [(CLAUDE_SESSION_LINK, "<claude-session-link>")]
SCISSORS = "# ------------------------ >8 ------------------------"


def hits_in(lines):
    for number, line in enumerate(lines, start=1):
        # dict.fromkeys keeps order and reports each placeholder once per line.
        placeholders = dict.fromkeys(p for pattern, p in CHECKS if pattern.search(line))
        for placeholder in placeholders:
            yield number, placeholder


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument(
        "--commit-msg",
        action="store_true",
        help="the file is a commit message: skip git's comment lines",
    )
    args = parser.parse_args()

    found = 0
    for path in args.files:
        data = path.read_bytes()
        if b"\0" in data[:8000]:
            continue
        lines = data.decode("utf-8", errors="replace").splitlines()
        if args.commit_msg:
            if SCISSORS in lines:
                lines = lines[: lines.index(SCISSORS)]
            lines = ["" if line.startswith("#") else line for line in lines]
        for number, placeholder in hits_in(lines):
            print(
                f"{path}:{number}: contains the private name scrubbed as {placeholder}"
            )
            found += 1
    if found:
        print(
            f"{found} private name(s) found. Replace each with its placeholder, or "
            "re-export the transcript, before committing."
        )
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
