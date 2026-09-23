#!/usr/bin/env python
"""Mirror an exported Claude Code session into MLflow as traces, then score it.

    uv run python tools/log_session_to_mlflow.py --session ai_collaboration_log/sessions/<stem>.turns.json
    uv run python tools/log_session_to_mlflow.py --session ... --feedback ai_collaboration_log/evaluation/<stem>.sonnet_scores.json
    uv run python tools/log_session_to_mlflow.py --session ... --evaluate [--judge ollama:/qwen3:1.7b]

One MLflow trace per instructor turn (root span: instructor text in, Claude's reply out;
one TOOL child span per tool call), in the experiment `ai-collaboration-log` on the
course tracking server. Idempotent: a turn already logged (same session id and turn
number in the trace tags) is skipped.

--feedback attaches the blind judge's scores (see ai_collaboration_log/evaluation/) to the
matching traces as LLM_JUDGE feedback. --evaluate runs mlflow.genai.evaluate over the
traces with deterministic scorers and a local Guidelines judge, so the two judges can be
compared in the MLflow UI. This is the course's own lecture-3 toolkit applied to the
transcript of how the course was built.
"""

import argparse
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXPERIMENT = "ai-collaboration-log"
MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5010")
TIER = os.environ.get("COURSE_TIER", "cpu")
DEFAULT_JUDGE = "ollama:/" + {"cpu": "qwen3:1.7b", "gpu": "qwen3:8b"}[TIER]

VERIFICATION_WORDS = re.compile(
    r"\b(verif|executed|ran |runs? clean|checked|passes|pass\b|resolve|audit|tested)",
    re.IGNORECASE,
)


def existing_turns(mlflow, session_id):
    traces = mlflow.search_traces(
        filter_string=f"tags.session_id = '{session_id}'", max_results=500
    )
    return (
        {int(row["tags"]["turn"]): row["trace_id"] for _, row in traces.iterrows()}
        if len(traces)
        else {}
    )


def to_ns(timestamp):
    """ISO-8601 timestamp from the transcript -> nanoseconds since the epoch."""
    from datetime import datetime

    return int(
        datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp() * 1e9
    )


ONE_SECOND = 1_000_000_000
ONE_MS = 1_000_000


def log_turns(mlflow, session, replace=False):
    """One trace per instructor turn, with the transcript's real timestamps.

    The root span runs from the instructor's message to the last event of the turn. Each
    tool call is a TOOL span from its call to its result. The gaps in between, when the
    assistant was thinking and writing, become "assistant" spans of type LLM, so the
    timeline shows where the wall-clock time went: model, tools, or waiting.
    """
    from mlflow.tracing.fluent import start_span_no_context

    session_id = session["session_id"]
    experiment_id = mlflow.get_experiment_by_name(EXPERIMENT).experiment_id
    done = existing_turns(mlflow, session_id)
    if replace and done:
        mlflow.MlflowClient().delete_traces(
            experiment_id, trace_ids=list(done.values())
        )
        print(f"deleted {len(done)} earlier traces of this session")
        done = {}
    trace_ids = dict(done)
    for turn in session["turns"]:
        n = turn["turn"]
        if n in done:
            continue
        t_start = to_ns(turn["timestamp"])
        t_end = max(to_ns(turn.get("ended") or turn["timestamp"]), t_start + ONE_MS)
        root = start_span_no_context(
            name=f"turn-{n:02d}",
            span_type="CHAIN",
            inputs={
                "instructor": turn["instructor"],
                "while_working": turn["instructor_while_working"],
                "answers": turn["instructor_answers"],
            },
            attributes={
                "timestamp": turn["timestamp"],
                "ended": turn.get("ended", ""),
                "thinking_blocks": turn["thinking_blocks"],
            },
            tags={
                "session_id": session_id,
                "turn": str(n),
                "source": "claude-code-transcript",
            },
            experiment_id=experiment_id,
            start_time_ns=t_start,
        )
        cursor = t_start  # the assistant is thinking from here until the next tool call
        for i, call in enumerate(turn["tool_calls"], 1):
            call_start = to_ns(call["started"]) if call.get("started") else cursor
            call_end = (
                to_ns(call["ended"]) if call.get("ended") else call_start + ONE_MS
            )
            if call_start > cursor + ONE_SECOND:
                thinking = start_span_no_context(
                    name="assistant",
                    span_type="LLM",
                    parent_span=root,
                    start_time_ns=cursor,
                )
                thinking.end(
                    outputs={"note": "model time between tool calls"},
                    end_time_ns=call_start,
                )
            tool_span = start_span_no_context(
                name=f"{i:03d} {call['tool']}",
                span_type="TOOL",
                parent_span=root,
                inputs={"summary": call["summary"]},
                start_time_ns=call_start,
            )
            tool_span.end(
                outputs={"note": "output not archived"},
                end_time_ns=max(call_end, call_start + ONE_MS),
            )
            cursor = max(cursor, call_end)
        if t_end > cursor + ONE_SECOND:
            final = start_span_no_context(
                name="assistant",
                span_type="LLM",
                parent_span=root,
                start_time_ns=cursor,
            )
            final.end(outputs={"reply": turn["assistant"]}, end_time_ns=t_end)
        root.end(outputs={"assistant": turn["assistant"]}, end_time_ns=t_end)
        trace_ids[n] = root.trace_id
    mlflow.flush_trace_async_logging()
    print(
        f"traces: {len(trace_ids)} turns in experiment '{EXPERIMENT}' "
        f"({len(trace_ids) - len(done)} new)"
    )
    return trace_ids


def attach_feedback(mlflow, trace_ids, feedback_path, prefix="judge"):
    from mlflow.entities import AssessmentSource

    scores = json.loads(Path(feedback_path).read_text(encoding="utf-8"))
    source = AssessmentSource(
        source_type="LLM_JUDGE", source_id=scores.get("judge", "blind-judge")
    )
    n = 0
    for entry in scores["turns"]:
        trace_id = trace_ids.get(entry["turn"])
        if not trace_id or not entry.get("scores"):
            continue  # unknown turn, or a turn the judge could not score (no stored reply)
        for criterion, detail in entry["scores"].items():
            mlflow.log_feedback(
                trace_id=trace_id,
                name=f"{prefix}/{criterion}",
                value=detail["score"],
                rationale=detail.get("rationale", ""),
                source=source,
            )
            n += 1
        if "overall" in entry:
            mlflow.log_feedback(
                trace_id=trace_id,
                name=f"{prefix}/overall",
                value=entry["overall"],
                rationale=entry.get("summary", ""),
                source=source,
            )
            n += 1
    mlflow.flush_trace_async_logging()
    print(f"feedback: {n} assessments from {source.source_id}")


def evaluate(mlflow, session_id, judge):
    from mlflow.genai import evaluate as genai_evaluate
    from mlflow.genai.scorers import Guidelines, scorer

    os.environ.setdefault("MLFLOW_GENAI_EVAL_MAX_WORKERS", "1")
    os.environ.setdefault("MLFLOW_GENAI_EVAL_MAX_SCORER_WORKERS", "1")

    @scorer
    def reply_words(outputs):
        return len(str(outputs.get("assistant", "")).split())

    @scorer
    def mentions_verification(outputs):
        return bool(VERIFICATION_WORDS.search(str(outputs.get("assistant", ""))))

    @scorer
    def house_style_no_em_dash(outputs):
        return "—" not in str(outputs.get("assistant", ""))

    @scorer
    def tool_calls(trace):
        return sum(1 for s in trace.data.spans if str(s.span_type).endswith("TOOL"))

    states_limits = Guidelines(
        name="states_limits",
        guidelines="The response says what was verified and names anything that remains unverified, skipped, or assumed.",
        model=judge,
    )
    answers_request = Guidelines(
        name="answers_request",
        guidelines="The response addresses what the instructor asked for, without silently narrowing or widening the request.",
        model=judge,
    )
    traces = mlflow.search_traces(
        filter_string=f"tags.session_id = '{session_id}'", max_results=500
    )
    results = genai_evaluate(
        data=traces,
        scorers=[
            reply_words,
            mentions_verification,
            house_style_no_em_dash,
            tool_calls,
            states_limits,
            answers_request,
        ],
    )
    print("evaluation run:", results.run_id)
    print(
        json.dumps(
            {
                k: (round(v, 3) if isinstance(v, float) else v)
                for k, v in results.metrics.items()
            },
            indent=1,
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--session", required=True, type=Path, help="a sessions/<stem>.turns.json file"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="delete this session's earlier traces and log them again",
    )
    parser.add_argument(
        "--feedback",
        type=Path,
        help="a judge scores JSON (see ai_collaboration_log/evaluation/README.md)",
    )
    parser.add_argument(
        "--feedback-prefix",
        default="judge",
        help="feedback name prefix for --feedback (e.g. judge, copilot)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="run mlflow.genai.evaluate with local scorers",
    )
    parser.add_argument(
        "--judge",
        default=DEFAULT_JUDGE,
        help=f"judge model URI for --evaluate (default {DEFAULT_JUDGE}; e.g. anthropic:/claude-sonnet-5 with ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args()

    import mlflow

    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT)
    session = json.loads(args.session.read_text(encoding="utf-8"))
    trace_ids = log_turns(mlflow, session, replace=args.replace)
    if args.feedback:
        attach_feedback(mlflow, trace_ids, args.feedback, args.feedback_prefix)
    if args.evaluate:
        evaluate(mlflow, session["session_id"], args.judge)


if __name__ == "__main__":
    main()
