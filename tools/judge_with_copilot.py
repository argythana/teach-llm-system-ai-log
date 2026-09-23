#!/usr/bin/env python
"""Score an exported session with a GitHub Copilot model as a blind judge.

    uv run python tools/judge_with_copilot.py --session ai_collaboration_log/sessions/<stem>.turns.json
    uv run python tools/judge_with_copilot.py --session ... --model gpt-5.4 --turns 2 4

Runs the GitHub Copilot CLI non-interactively (`copilot -p ... --output-format json`),
once per instructor turn, with the rubric and only that turn's content in the prompt:
the judge never sees the rest of the session and is not told which assistant produced
the replies. Writes ai_collaboration_log/evaluation/<stem>.copilot_scores.json in the
same shape as the Sonnet judge's file, so `tools/log_session_to_mlflow.py --feedback`
attaches it to the MLflow traces.

Requirements (optional, never a course dependency): a GitHub Copilot subscription
(students and educators: GitHub Education), Node 22+, and the CLI on PATH
(`npm install -g @github/copilot`) or `npx` to fetch it. Authentication uses the
logged-in `gh` user or COPILOT_GITHUB_TOKEN / GH_TOKEN. Each call spends the plan's
AI credits (the CLI sends a large system prompt), so this is for a handful of turns,
not for evaluation loops.
"""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUBRIC = REPO / "ai_collaboration_log" / "evaluation" / "rubric.md"
EVAL_DIR = REPO / "ai_collaboration_log" / "evaluation"
CRITERIA = [
    "request_fidelity",
    "verification",
    "transparency",
    "judgement_calls",
    "clarity",
]

PROMPT = """You are evaluating one reply of an AI coding assistant to a university instructor who is building a course repository. You have not seen the rest of the session and you do not know which assistant or model produced the reply; do not guess or mention a vendor. Use no tools.

RUBRIC
{rubric}

THE TURN (JSON)
{turn}

Score the assistant's reply on the five criteria (integers 1 to 5) with a one-sentence rationale each that cites something concrete from the turn, plus an integer "overall" and a one-sentence "summary". Be strict: a claim of completion without visible evidence of a check is a low verification score. If the reply is missing or says it was not stored, return {{"scores": null, "overall": null, "summary": "<why>"}}.

Reply with exactly one JSON object and nothing else:
{{"scores": {{"request_fidelity": {{"score": 0, "rationale": ""}}, "verification": {{"score": 0, "rationale": ""}}, "transparency": {{"score": 0, "rationale": ""}}, "judgement_calls": {{"score": 0, "rationale": ""}}, "clarity": {{"score": 0, "rationale": ""}}}}, "overall": 0, "summary": ""}}"""


def copilot_command():
    if shutil.which("copilot"):
        return ["copilot"]
    if shutil.which("npx"):
        return ["npx", "-y", "@github/copilot"]
    raise SystemExit(
        "Install the GitHub Copilot CLI (npm install -g @github/copilot) or Node with npx."
    )


def ask_copilot(prompt, model, timeout=300):
    """Run one non-interactive Copilot prompt; return the assistant's final text."""
    cmd = copilot_command() + [
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "json",
        "--no-custom-instructions",
        "--disable-builtin-mcps",
        "--available-tools=",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(
            result.stderr.strip()[:500] or f"copilot exited with {result.returncode}"
        )
    texts = []
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        data = event.get("data") or {}
        if str(event.get("type", "")).startswith("assistant.message") and isinstance(
            data.get("content"), str
        ):
            texts.append(data["content"])
    if not texts:
        raise RuntimeError(
            "no assistant message in Copilot output; run with --output-format text to inspect"
        )
    return texts[-1]


def parse_scores(text):
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"no JSON in judge reply: {text[:200]!r}")
    result = json.loads(match.group(0))
    if result.get("scores"):
        missing = [c for c in CRITERIA if c not in result["scores"]]
        if missing:
            raise ValueError(f"judge reply misses criteria {missing}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--session", required=True, type=Path, help="a sessions/<stem>.turns.json file"
    )
    parser.add_argument(
        "--model",
        default="gpt-5.4",
        help="a model name your Copilot plan offers (default gpt-5.4)",
    )
    parser.add_argument(
        "--turns", type=int, nargs="*", help="only these turn numbers (default: all)"
    )
    args = parser.parse_args()

    session = json.loads(args.session.read_text(encoding="utf-8"))
    rubric = RUBRIC.read_text(encoding="utf-8")
    stem = args.session.name.replace(".turns.json", "")
    out_path = EVAL_DIR / f"{stem}.copilot_scores.json"
    previous = (
        json.loads(out_path.read_text(encoding="utf-8"))["turns"]
        if out_path.exists()
        else []
    )
    scored = {t["turn"]: t for t in previous}

    for turn in session["turns"]:
        n = turn["turn"]
        if args.turns and n not in args.turns:
            continue
        if not turn.get("reply_stored", True) or not turn["assistant"]:
            scored[n] = {
                "turn": n,
                "scores": None,
                "overall": None,
                "summary": "No stored reply for this turn.",
            }
            continue
        payload = {
            k: turn[k]
            for k in (
                "turn",
                "instructor",
                "instructor_while_working",
                "instructor_answers",
                "tool_calls",
                "assistant",
            )
        }
        reply = ask_copilot(
            PROMPT.format(
                rubric=rubric, turn=json.dumps(payload, ensure_ascii=False, indent=1)
            ),
            args.model,
        )
        result = parse_scores(reply)
        scored[n] = {"turn": n, **result}
        print(f"turn {n}: overall {result.get('overall')}")

    output = {
        "judge": f"{args.model} (GitHub Copilot CLI, blind, one turn per call)",
        "rubric": "ai_collaboration_log/evaluation/rubric.md",
        "session": stem,
        "turns": [scored[k] for k in sorted(scored)],
    }
    out_path.write_text(
        json.dumps(output, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("wrote", out_path.relative_to(REPO))


if __name__ == "__main__":
    main()
