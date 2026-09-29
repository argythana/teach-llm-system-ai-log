# Reflection: setup guides and lecture 2 (session 2026-09-24 to 2026-09-29)

*Draft prepared by the assistant from the session log; the instructor edits and owns
it.*

Session: `sessions/2026-09-24_cbdb58da.md`. Outcome: the setup guides rewritten for
beginners and moved into per-lecture `infra_tools/` folders, a `.env` settings pattern,
MLflow moved from lecture 1 to lecture 2, and lecture 2 (six notebooks, goals, nine
exercises with solutions, an evaluation set) built, reviewed by two blind reviewers, and
committed.

## Delegation

- **Kept by the instructor:** setup done together in class instead of "homework zero";
  the `.env` file as the one settings pattern; the folder and file naming
  (`infra_tools/01a_git_uv.md`); where MLflow enters the course; keeping Qwen3 after a
  candidate comparison; when to commit.
- **Delegated:** rewriting the guides, running llmfit to compare candidate models,
  building and executing all of lecture 2, and commissioning two blind reviews of it.
- **Worth noting:** the instructor separated discussion from action when a change was
  structural ("do not act on this yet"), then gave the go-ahead in a second message.

## Description

- The first prompt gave examples of the fixes wanted and asked to "look for similar
  things to improve", which set the scope by example.
- Questions came from running the tools: `uvx llmfit fit` listing hundreds of models, an
  unclear Runtime column, `-n 10` not ranking by score. Each became a guide change.
- The lecture 2 request carried its own acceptance test: two blind reviewers, judged on
  lecture scope and against lecture 1, and a list of important decisions at the end.

## Discernment

Moments where the instructor's judgement changed the work:

1. "remind me why we need mlflow in lecture 1. I think lecture 1 has already many
   tools": tracing now starts in `lec_02b`, with the first retrieve-then-generate
   pipeline.
1. Rejecting "homework zero": every guide now opens with a Quick start run in class.
1. Rejecting the reference course's top-level guides folder ("not optimal") for
   per-lecture `infra_tools/`.
1. "did you try to use 'name'?" caught an llmfit flag the assistant had not tested.
1. Terminal environment variables are "a pattern that confuses beginners": explained
   once, never used.

Moments where the assistant's checks changed the work, which the instructor should
verify rather than take on trust:

- An exported-notebook provenance comment and empty heading chunks distorted retrieval;
  the loader strips the comment and chunks under 80 characters are dropped.
- LangChain's Markdown splitter cut inside code blocks; a headings-first separator list
  replaced it.
- A claim that nomic task prefixes make "little difference" was false; measured, they
  raise MRR from 0.78 to 0.83. Plain text was kept, and the choice is open.

## Diligence

- Every lecture 2 notebook was executed from clean caches, and prose that contradicted
  its own outputs was corrected after each run; hooks passed before both commits.
- Open items the instructor owns: the nomic prefix decision; the evaluation set is used
  both to choose settings and to grade them (stated in the notebooks as a caveat); the
  02d/02e read-back about a mis-cited source was edited without re-running; lecture 3 is
  not written.
