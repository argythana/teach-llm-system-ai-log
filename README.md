# teach-llm-system: AI collaboration log

[teach-llm-system](https://github.com/argythana/teach-llm-system), a short course on
building a local LLM system with RAG and evaluation, was designed and built with an AI
coding assistant (Claude Code, running Claude models). This repository is the record of
that collaboration, kept for two reasons:

- **Transparency to students.** A course about building LLM systems should show how it
  was itself built with one, including where the instructor corrected the assistant.
- **Evidence for the instructor's AI fluency practice.** The sessions and reflections
  document the four competencies of Anthropic's AI Fluency framework: Delegation,
  Description, Discernment, and Diligence.

For the short version of how to work with an assistant, read the course's
[`CLAUDE.md`](https://github.com/argythana/teach-llm-system/blob/main/CLAUDE.md): it is
the specification that steered every session, distilled from the instructor's
corrections.

## Coverage

The log covers the first build of the course: the sessions from 14 to 30 September 2026,
up to commit `723253a` of the course repository. Later sessions are not exported yet.

Until October 2026 this log lived inside the course repository as
`ai_collaboration_log/`, and the history of its files moved with it. Paths in the
transcripts and score files that start with `ai_collaboration_log/` refer to that
layout.

## What is here

| Path                              | What it holds                                                                                                          | Tracked         |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------- |
| `sessions/<date>_<id>.md`         | the curated transcript of one session: every instructor message verbatim, every reply verbatim, one line per tool call | yes             |
| `sessions/<date>_<id>.turns.json` | the same session as data, one record per instructor turn                                                               | yes             |
| `reflections/`                    | the instructor's notes per session, organised by the four competencies                                                 | yes             |
| `evaluation/`                     | the rubric, the blind-judge prompt, and the judges' scores per session                                                 | yes             |
| `tools/`                          | the exporter, the MLflow logger, and the optional Copilot judge                                                        | yes             |
| `raw/`                            | the unedited Claude Code transcripts (JSONL), sub-agent transcripts, plan files                                        | no (gitignored) |

## Setup

```bash
uv sync
```

- **Ollama** with `qwen3:1.7b`, for the local judge (the course's guide `01c_ollama`).
- **This repository's MLflow server**, started from the repository root so that
  `mlflow.db` and `mlartifacts/` land there (both gitignored):
  `uv run mlflow server --host 127.0.0.1 --port 5011`. Port 5011 leaves 5010 to the
  course server (guide `03a_mlflow_server`); set `MLFLOW_TRACKING_URI` to use another
  server.
- **Optional:** the GitHub Copilot CLI, for a judge from another model family
  (`evaluation/README.md`).

## How it is generated

```bash
uv run python tools/export_claude_sessions.py --project ~/venv_projects/teach-llm-system --copy-raw
uv run python tools/log_session_to_mlflow.py --session sessions/<stem>.turns.json --evaluate
```

The exporter reads Claude Code's own transcript files
(`~/.claude/projects/<project>/*.jsonl`). `--project` names the course repository,
because Claude Code files a session under the folder it was started in.

It keeps what the instructor typed, what the assistant replied, and a one-line summary
of each tool call. It drops the assistant's private reasoning, tool outputs, injected
system context, and background-task notifications; it replaces e-mail addresses and the
home directory. Existing files are overwritten.

## The build, ported into MLflow

The second script applies the course's own lecture-3 toolkit to this log:

- **Traces.** Each instructor turn becomes one MLflow trace in the experiment
  `ai-collaboration-log`: the instructor's message as input, the assistant's reply as
  output, and one child span per tool call.

- **Judges.** Three independent judges score the replies against `evaluation/rubric.md`,
  and the Traces tab shows them side by side:

  - a **blind Claude judge**: a fresh Claude Code sub-agent on a Sonnet model that never
    saw the session (`judge/*` feedback, source `LLM_JUDGE`);
  - the **local judge** the course uses everywhere: `mlflow.genai.evaluate` with
    deterministic scorers and `Guidelines` scorers run by the Ollama model
    (`ollama:/qwen3:1.7b`);
  - optionally a **GitHub Copilot judge** from a different model family
    (`tools/judge_with_copilot.py`, default model `gpt-5.4`).

Why three: a model judging its own family can be lenient, a small local model is weak on
long technical replies, and a second family is the cheapest independent opinion.

The disagreements are the interesting part. `evaluation/README.md` has the procedure and
the caveats. Nothing in MLflow is the archive of record; the Markdown files are.

## A limitation of the source

Claude Code's transcript files store the instructor's messages and the assistant's final
reply of each turn completely, but not every interim status line the assistant printed
while working. A turn that ended in a tool call can have no stored reply at all, and the
exporter marks such turns.

Replies were not reconstructed from memory: what is not in the file is not in the log.

## What is deliberately not here

- **Reasoning blocks.** They are not shown to the user during a session, and the log
  records the collaboration as it was experienced.
- **Tool outputs** (command results, file contents read). They are large, often quote
  other repositories, and every artifact they produced is in the course repository.
- **Manual ratings by the instructor.** The evaluation layer is automated by design; it
  showcases the method, it is not a graded review of the assistant.

## License

Code in `tools/` is licensed under the [MIT License](LICENSE). Prose (Markdown files,
transcripts included) is licensed under [CC BY 4.0](LICENSE-CC-BY-4.0.txt). The
assistant's replies were generated with Claude Code; the instructor is responsible for
their use here.
