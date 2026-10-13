# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## Purpose

The record of how [teach-llm-system](https://github.com/argythana/teach-llm-system) was
built with Claude Code: curated session transcripts, the instructor's reflections, and
an automated evaluation of the assistant's replies with the course's MLflow toolkit. It
is evidence of AI fluency practice, not course material.

## Workflow

- **Export.**
  `uv run python tools/export_claude_sessions.py --project ~/venv_projects/teach-llm-system --copy-raw`
  writes `sessions/` and copies the raw JSONL into `raw/` (gitignored). `--project` is
  the course repository, where the sessions were run.
- **Mirror and score.**
  `uv run python tools/log_session_to_mlflow.py --session <turns.json> --evaluate` logs
  one trace per turn into the experiment `ai-collaboration-log` on the course MLflow
  server (port 5010), then follow the blind-judge procedure in `evaluation/README.md`.
  Score only finished turns; after a session grows, re-log with `--replace` and
  re-attach every judge's feedback.
- **Reflections** are the instructor's own text: draft them, never finalise them.

## Rules

- `sessions/`, `*.turns.json` and `evaluation/*_scores.json` are records: never edit or
  reformat them by hand (mdformat excludes `sessions/`). Old `ai_collaboration_log/`
  paths inside them are historical.
- Before a push, skim newly exported transcripts for anything private; gitleaks runs on
  every commit.
- `uv` only, never pip. Python >= 3.12. `uv run prek run --all-files` runs the hooks.
- Commit messages: Conventional Commits, e.g. `docs(sessions): ...`, `fix(tools): ...`.
