# AI collaboration log

This course was designed and built with an AI coding assistant (Claude Code, running
Claude models). This folder is the record of that collaboration, kept for two reasons:

- **Transparency to students.** A course about building LLM systems should show how it
  was itself built with one, including where the instructor corrected the assistant.
- **Evidence for the instructor's AI fluency practice.** The sessions and reflections
  document the four competencies of Anthropic's AI Fluency framework: Delegation,
  Description, Discernment, and Diligence.

## What is here

| Path                              | What it holds                                                                                                          | Tracked         |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------- |
| `sessions/<date>_<id>.md`         | the curated transcript of one session: every instructor message verbatim, every reply verbatim, one line per tool call | yes             |
| `sessions/<date>_<id>.turns.json` | the same session as data, one record per instructor turn                                                               | yes             |
| `reflections/`                    | the instructor's notes per session, organised by the four competencies                                                 | yes             |
| `evaluation/`                     | the rubric, the blind-judge prompt, and the judge's scores per session                                                 | yes             |
| `raw/`                            | the unedited Claude Code transcripts (JSONL), sub-agent transcripts, plan files                                        | no (gitignored) |

## How it is generated

```bash
uv run python tools/export_claude_sessions.py --copy-raw        # raw -> sessions/
uv run python tools/log_session_to_mlflow.py --session ai_collaboration_log/sessions/<stem>.turns.json --evaluate
```

The exporter reads Claude Code's own transcript files
(`~/.claude/projects/<project>/*.jsonl`). It keeps what the instructor typed, what the
assistant replied, and a one-line summary of each tool call; it drops the assistant's
private reasoning, tool outputs, injected system context, and background-task
notifications; it replaces e-mail addresses and the home directory. Re-run it after
every session; existing files are overwritten.

The second script is the course's own lecture-3 toolkit applied to this log: each
instructor turn becomes an MLflow **trace** (experiment `ai-collaboration-log` on the
course tracking server), tool calls become child spans, and `mlflow.genai.evaluate`
scores the replies with deterministic scorers and a local judge. `evaluation/README.md`
describes the blind judge and how its scores are attached as feedback. Nothing in MLflow
is the archive of record; the Markdown files are.

## A limitation of the source

Claude Code's transcript files store the instructor's messages and the assistant's final
reply of each turn completely, but not every interim status line the assistant printed
while working, and a turn that ended in a tool call can have no stored reply at all. The
exporter marks such turns. Replies were not reconstructed from memory: what is not in
the file is not in the log.

## What is deliberately not here

- The assistant's reasoning blocks. They are not shown to the user during a session, and
  the log records the collaboration as it was experienced.
- Tool outputs (command results, file contents read). They are large, often quote other
  repositories, and every artifact they produced is in this repository already.
- The instructor's manual ratings. The evaluation layer is automated by design; it
  showcases the method, it is not a graded review of the assistant.

## License

Like the rest of the course prose, this folder is licensed under
[CC BY 4.0](../LICENSE-CC-BY-4.0.txt). The assistant's replies were generated with
Claude Code; the instructor is responsible for their use here.
