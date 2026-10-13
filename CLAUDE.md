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
  one trace per turn into the experiment `ai-collaboration-log` on this repository's
  MLflow server (`uv run mlflow server --host 127.0.0.1 --port 5011` from the root),
  then follow the blind-judge procedure in `evaluation/README.md`. Score only finished
  turns; after a session grows, re-log with `--replace` and re-attach every judge's
  feedback.
- **Reflections** are the instructor's own text: draft them, never finalise them.

## Rules

- `sessions/`, `*.turns.json` and `evaluation/*_scores.json` are records: never edit or
  reformat them by hand (mdformat excludes `sessions/`). Old `ai_collaboration_log/`
  paths inside them are historical.
- Before a push, skim newly exported transcripts for anything private. gitleaks catches
  secrets; it cannot catch names. Names live in the gitignored `private_terms.txt`: add
  a new private name there before exporting, never write it into a tracked file. The
  `private-terms` hook (`tools/check_private_terms.py`) checks staged files and commit
  messages against that file, this machine's hostname and username, and Claude Code
  session links. Run `uv run prek install` once per clone, or the hooks do not run.
- `uv` only, never pip. Python >= 3.12. `uv run prek run --all-files` runs the hooks.
- Commit messages: Conventional Commits, e.g. `docs(sessions): ...`, `fix(tools): ...`.
