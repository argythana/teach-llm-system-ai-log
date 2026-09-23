#!/usr/bin/env python
"""Export Claude Code session transcripts into ai_collaboration_log/sessions/.

    uv run python tools/export_claude_sessions.py              # export every session of this project
    uv run python tools/export_claude_sessions.py --copy-raw   # also copy the raw JSONL into ai_collaboration_log/raw/

For each session it writes:
  sessions/<date>_<session-id8>.md          the curated, human-readable transcript
  sessions/<date>_<session-id8>.turns.json  the same turns as data (used by tools/log_session_to_mlflow.py)
  sessions/README.md                        an index

Kept: every instructor message verbatim (typed prompts, messages sent while Claude was
working, answers to Claude's questions), every user-facing reply verbatim, and one line
per tool call. Dropped: the assistant's private reasoning blocks, tool outputs, injected
system context, and background-task notifications. Scrubbed: e-mail addresses and the
home directory. Standard library only.
"""

import argparse
import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG_DIR = REPO / "ai_collaboration_log"
SESSIONS_DIR = LOG_DIR / "sessions"
RAW_DIR = LOG_DIR / "raw"
# Claude Code names the project folder after the repo path with every non-alphanumeric
# character replaced by "-" (so "venv_projects" becomes "venv-projects").
CLAUDE_PROJECT_DIR = (
    Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(REPO))
)

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SYSTEM_BLOCK = re.compile(r"<system-reminder>.*?</system-reminder>\s*", re.DOTALL)
HOME = str(Path.home())


def scrub(text):
    text = SYSTEM_BLOCK.sub("", text or "")
    text = EMAIL.sub("[email]", text)
    return text.replace(HOME, "~").strip()


def tool_summary(block):
    """One line per tool call, from the tool's own arguments."""
    name = block.get("name", "?")
    args = block.get("input", {}) or {}
    if name == "Bash":
        return f"Bash: {args.get('description') or args.get('command', '')[:100]}"
    if name in ("Read", "Write", "Edit", "NotebookEdit"):
        return f"{name}: {scrub(str(args.get('file_path', '')))}"
    if name == "Agent":
        model = args.get("model") or "inherited"
        return f"Agent ({args.get('subagent_type', 'general')}, model {model}): {args.get('description', '')}"
    if name == "WebFetch":
        return f"WebFetch: {args.get('url', '')}"
    if name == "ToolSearch":
        return f"ToolSearch: {args.get('query', '')}"
    if name == "AskUserQuestion":
        headers = ", ".join(q.get("header", "?") for q in args.get("questions", []))
        return f"AskUserQuestion: {headers}"
    if name == "ExitPlanMode":
        return "ExitPlanMode: submitted the plan for approval"
    if name == "Monitor":
        return f"Monitor: {args.get('description', '')}"
    if name == "Skill":
        return f"Skill: {args.get('skill', '')}"
    return f"{name}"


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(
        b.get("text", "")
        for b in content
        if isinstance(b, dict) and b.get("type") == "text"
    )


def instructor_reply_in_result(content):
    """Instructor words that Claude Code embeds in tool results (question answers, plan feedback)."""
    text = text_of(content) if not isinstance(content, str) else content
    found = []
    for marker in (
        "The user answered: ",
        "the user said:\n",
        "The user sent a new message while you were working:\n",
    ):
        if marker in text:
            answer = text.split(marker, 1)[1]
            for tail in (
                "\n\nThis is how Claude Code",
                "\n\nRead the answers",
                "\n\nNote: The user's next message",
            ):
                answer = answer.split(tail)[0]
            found.append(answer.strip())
    return found


def load_entries(path):
    entries = []
    for line in open(path, encoding="utf-8"):
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def build_turns(entries):
    turns = []
    current = None
    stats = Counter()

    def new_turn(ts, user_text):
        nonlocal current
        current = {
            "turn": len(turns) + 1,
            "timestamp": ts,
            "ended": ts,
            "instructor": user_text,
            "instructor_while_working": [],
            "instructor_answers": [],
            "tool_calls": [],
            "assistant": [],
            "assistant_messages": [],
            "thinking_blocks": 0,
        }
        turns.append(current)

    for e in sorted(entries, key=lambda x: x.get("timestamp", "")):
        kind = e.get("type")
        ts = e.get("timestamp", "")
        if kind == "queue-operation" and e.get("operation") == "enqueue":
            text = scrub(e.get("content", ""))
            if (
                text
                and not text.startswith("<task-notification>")
                and current is not None
            ):
                current["instructor_while_working"].append(text)
            continue
        if kind not in ("user", "assistant"):
            continue
        content = e.get("message", {}).get("content")
        if kind == "user":
            if isinstance(content, str):
                text = scrub(content)
                if (
                    not text
                    or text.startswith("<task-notification>")
                    or text.startswith("<bash-stdout>")
                    or text.startswith("Another Claude session sent a message")
                ):
                    continue
                if text.startswith("<bash-input>"):
                    text = (
                        "Ran in the terminal: `"
                        + re.sub(r"</?bash-input>", "", text).strip()
                        + "`"
                    )
                new_turn(ts, text)
            else:
                for b in content:
                    if (
                        isinstance(b, dict)
                        and b.get("type") == "tool_result"
                        and current is not None
                    ):
                        current["ended"] = max(current["ended"], ts)
                        for call in current["tool_calls"]:
                            if (
                                call.get("id") == b.get("tool_use_id")
                                and "ended" not in call
                            ):
                                call["ended"] = ts
                        result_text = (
                            text_of(b.get("content", ""))
                            if not isinstance(b.get("content"), str)
                            else b.get("content", "")
                        )
                        # Only the result of the tool that asked the instructor carries their words;
                        # any other tool output that quotes these phrases is just output.
                        tool_name = next(
                            (
                                c["tool"]
                                for c in current["tool_calls"]
                                if c.get("id") == b.get("tool_use_id")
                            ),
                            None,
                        )
                        if tool_name not in ("ExitPlanMode", "AskUserQuestion"):
                            continue
                        # A plan decision is an instructor turn of its own: the work that follows answers it.
                        if (
                            tool_name == "ExitPlanMode"
                            and "User has approved your plan" in result_text
                        ):
                            new_turn(ts, "Approved the plan (ExitPlanMode).")
                            continue
                        if (
                            "The user doesn't want to proceed with this tool use"
                            in result_text
                            and "the user said:\n" in result_text
                        ):
                            new_turn(
                                ts,
                                "Rejected the proposed step and said:\n"
                                + scrub(instructor_reply_in_result(result_text)[0]),
                            )
                            continue
                        current["instructor_answers"].extend(
                            scrub(t)
                            for t in instructor_reply_in_result(b.get("content", ""))
                        )
                    elif (
                        isinstance(b, dict)
                        and b.get("type") == "text"
                        and current is not None
                    ):
                        text = scrub(b.get("text", ""))
                        if text and not text.startswith("<task-notification>"):
                            current["instructor_while_working"].append(text)
            continue
        if current is None:
            continue
        if isinstance(content, str):
            current["assistant"].append(scrub(content))
            continue
        for b in content:
            btype = b.get("type")
            if btype == "text":
                text = scrub(b.get("text", ""))
                if text:
                    current["assistant"].append(text)
                    current["assistant_messages"].append(
                        {"timestamp": ts, "text": text}
                    )
                    current["ended"] = max(current["ended"], ts)
            elif btype == "tool_use":
                current["tool_calls"].append(
                    {
                        "tool": b.get("name"),
                        "summary": scrub(tool_summary(b)),
                        "id": b.get("id"),
                        "started": ts,
                    }
                )
                current["ended"] = max(current["ended"], ts)
                stats[b.get("name")] += 1
            elif btype == "thinking":
                current["thinking_blocks"] += 1
    for t in turns:
        t["assistant"] = "\n\n".join(t["assistant"])
        t["reply_stored"] = bool(t["assistant"])
        if not t["assistant"] and t["tool_calls"]:
            t["assistant"] = (
                "(Claude Code did not store the reply text of this turn; the tool calls above show what was done.)"
            )
    return turns, stats


def fmt_ts(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
    except ValueError:
        return ts


def render_markdown(session_id, turns, stats, source_name):
    first, last = turns[0]["timestamp"], turns[-1]["timestamp"]
    n_tools = sum(len(t["tool_calls"]) for t in turns)
    lines = [
        f"# Session {session_id[:8]}: {fmt_ts(first)} to {fmt_ts(last)}",
        "",
        f"Exported from `{source_name}` by `tools/export_claude_sessions.py`. "
        f"{len(turns)} instructor turns, {n_tools} tool calls "
        f"({', '.join(f'{k} {v}' for k, v in stats.most_common())}). "
        "Instructor text and Claude's replies are verbatim as stored by Claude Code, which keeps the final "
        "reply of every turn but not every interim status line; tool calls are one-line summaries; "
        "Claude's private reasoning and tool outputs are not included.",
        "",
    ]
    for t in turns:
        lines += [
            f"## Turn {t['turn']} · {fmt_ts(t['timestamp'])}",
            "",
            "**Instructor:**",
            "",
        ]
        lines += ["> " + line for line in t["instructor"].splitlines()] + [""]
        for extra in t["instructor_while_working"]:
            lines += (
                ["**Instructor, while Claude was working:**", ""]
                + ["> " + line for line in extra.splitlines()]
                + [""]
            )
        for extra in t["instructor_answers"]:
            lines += (
                ["**Instructor's answers to Claude's questions:**", ""]
                + ["> " + line for line in extra.splitlines()]
                + [""]
            )
        if t["tool_calls"]:
            lines += [
                f"<details><summary>Claude worked with {len(t['tool_calls'])} tool calls</summary>",
                "",
            ]
            lines += [f"- {c['summary']}" for c in t["tool_calls"]] + [
                "",
                "</details>",
                "",
            ]
        lines += [
            "**Claude:**",
            "",
            t["assistant"] or "*(no user-facing text in this turn)*",
            "",
        ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--copy-raw",
        action="store_true",
        help="copy the JSONL files into ai_collaboration_log/raw/ (gitignored)",
    )
    args = parser.parse_args()

    sources = {}
    for folder in (RAW_DIR, CLAUDE_PROJECT_DIR):
        for path in sorted(folder.glob("*.jsonl")) if folder.exists() else []:
            sources[path.stem] = (
                path  # the ~/.claude copy wins when both exist (it is the freshest)
            )
    if not sources:
        raise SystemExit(f"No transcripts found in {CLAUDE_PROJECT_DIR} or {RAW_DIR}")

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    index = []
    for session_id, path in sources.items():
        if args.copy_raw and path.parent != RAW_DIR:
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, RAW_DIR / path.name)
        turns, stats = build_turns(load_entries(path))
        if not turns:
            continue
        stem = f"{turns[0]['timestamp'][:10]}_{session_id[:8]}"
        (SESSIONS_DIR / f"{stem}.md").write_text(
            render_markdown(session_id, turns, stats, path.name), encoding="utf-8"
        )
        (SESSIONS_DIR / f"{stem}.turns.json").write_text(
            json.dumps(
                {"session_id": session_id, "turns": turns}, indent=1, ensure_ascii=False
            )
            + "\n",
            encoding="utf-8",
        )
        index.append(
            (
                stem,
                len(turns),
                sum(len(t["tool_calls"]) for t in turns),
                fmt_ts(turns[0]["timestamp"]),
                fmt_ts(turns[-1]["timestamp"]),
            )
        )
        print(
            f"{stem}: {len(turns)} turns, {sum(len(t['tool_calls']) for t in turns)} tool calls"
        )

    lines = [
        "# Sessions",
        "",
        "| Session | Turns | Tool calls | From | To |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [f"| [{s}]({s}.md) | {n} | {k} | {a} | {b} |" for s, n, k, a, b in index]
    (SESSIONS_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
