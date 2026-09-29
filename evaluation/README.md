# Evaluation layer

Two automated judges score every instructor turn of a session, and MLflow shows them
side by side. No manual rating is involved; the point is to showcase the method the
course teaches in lecture 3 on the transcript of how the course was built.

1. **A blind judge from a different context.** A fresh agent that has not seen the
   session scores each turn against `rubric.md`, following `judge_prompt.md`, and writes
   `<stem>.sonnet_scores.json`. In this repository it was run as a Claude Code sub-agent
   on a Sonnet model; the prompt works unchanged with any capable model or API.

1. **The course's local judge.** `tools/log_session_to_mlflow.py --evaluate` runs
   `mlflow.genai.evaluate` with deterministic scorers (reply length, tool-call count,
   whether the reply mentions verification, whether it respects the house style) and two
   `Guidelines` scorers judged by the local Ollama model.

1. **Optionally, a judge from another model family.** `tools/judge_with_copilot.py` runs
   the same rubric, one turn per call, through the GitHub Copilot CLI with an explicitly
   chosen non-Claude model (default `gpt-5.4`) and writes `<stem>.copilot_scores.json`
   in the same shape. It needs a Copilot subscription (GitHub Education gives one to
   students and educators) and spends AI credits per call; it is never a course
   dependency.

```bash
uv run python tools/judge_with_copilot.py --session ai_collaboration_log/sessions/<stem>.turns.json
uv run python tools/log_session_to_mlflow.py --session ai_collaboration_log/sessions/<stem>.turns.json \
    --feedback ai_collaboration_log/evaluation/<stem>.sonnet_scores.json --evaluate
uv run python tools/log_session_to_mlflow.py --session ai_collaboration_log/sessions/<stem>.turns.json \
    --feedback ai_collaboration_log/evaluation/<stem>.copilot_scores.json --feedback-prefix copilot
```

Open the `ai-collaboration-log` experiment on the course MLflow server: the **Traces**
tab lists one trace per turn with the blind judge's scores as feedback (`judge/*`), and
the evaluation run holds the local scorers' results. Where the two judges disagree is
the interesting part, and a small local model judging long, technical replies is
expected to be the weaker of the two.

## Re-running after a session grows

The exporter overwrites the session files, and turn numbers stay stable because turns
are appended in time order. Score only the new turns (`--turns 9 10 11` for the Copilot
judge; give the Sonnet sub-agent the same turn numbers and merge its file), then re-log
the traces with real timings and re-attach every judge:

```bash
uv run python tools/log_session_to_mlflow.py --session <turns.json> --replace \
    --feedback ai_collaboration_log/evaluation/<stem>.sonnet_scores.json
uv run python tools/log_session_to_mlflow.py --session <turns.json> \
    --feedback ai_collaboration_log/evaluation/<stem>.copilot_scores.json --feedback-prefix copilot
```

Traces carry the transcript's real timestamps: the root span runs from the instructor's
message to the last event of the turn, each tool call is a span from call to result, and
the gaps in between are "assistant" spans (type LLM), the time the model spent thinking
and writing. The timeline therefore shows where the wall-clock time of a turn went.

## Caveats, stated up front

- A Claude model judging Claude's replies can be lenient towards its own style. The
  rubric anchors every score in a cited fact from the turn to limit that, and the local
  judge is an independent second opinion.
- A sub-agent is not a reproducible API call. The scores file is committed so the result
  is inspectable; re-running produces a new file, not the same numbers.
- The local judge reads at most Ollama's default context of 4,096 tokens. A longer turn
  is cut from the start, where the guideline sits, and the judge grades what is left: in
  session `2026-09-24_cbdb58da`, turn 29's prompt of 12,944 tokens (measured) arrived as
  4,096, and its `answers_request` call, like turn 31's, failed to parse. Such failures
  show as scorer errors on the trace; every other turn logged so far fits the window.
- The judge sees tool-call summaries, not tool outputs, so it can only check whether
  verification was *claimed and described*, not whether it happened. The repository's CI
  and the executed notebooks are the evidence for the latter.
