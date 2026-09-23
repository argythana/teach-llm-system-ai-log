# Reflection: planning and lecture 1 (session 2026-09-14 to 2026-09-15)

*Draft prepared by the assistant from the session log; the instructor edits and owns
it.*

Session: `sessions/2026-09-14_ff09b61a.md`. Outcome: the course plan, the repository
skeleton and tooling, the exported corpus, and lecture 1 (six notebooks, goals,
exercises).

## Delegation

- **Kept by the instructor:** the format (3 x 2 x 75 minutes), the audience, the
  must-know ecosystems, the layout convention, every scope decision (Chroma over
  pgvector for the mandatory path, LangGraph in, DSPy optional, no AI-fluency readings),
  and the principle that model choice starts from business requirements.
- **Delegated:** exploring the two reference repositories, checking library versions and
  API names, drafting the plan, writing and executing the notebooks, formatting and link
  audits.
- **Worth noting:** delegation was staged. The assistant was asked to plan first,
  discuss, and only then build, with a review checkpoint after lecture 1 before lectures
  2 and 3.

## Description

- The opening prompt gave the audience, the constraints, candidate topics marked as
  suggestions, the reference repositories, and the quality bar ("TOP quality").
- Mid-course corrections were short and specific ("the local teach-mlflow is not
  up-to-date"; "system-native application is a better term"; "this should be combined in
  the first line of section 2").
- The assistant's clarifying questions (hardware, vector store, corpus, scope; layout,
  models, assessment, AI-fluency thread) were answered with decisions, and one answer
  reframed the question: two models were not needed, one reasoning model with thinking
  switched off per call was.

## Discernment

Moments where the instructor's judgement changed the work:

1. Rejecting the plan's size-first model choice: "it should always be a matter of
   business requirements." This added the `lec_01b` notebook and the decision-record
   requirement.
1. Catching "you never activate anything" in guide 00a: true for `uv run jupyter lab`,
   wrong for VS Code users.
1. Asking for the difference between the Ollama application and the `ollama` Python
   package to be explained, and where the package is used in the course.
1. Knowing that the local clone of the reference repository was stale, information the
   assistant could not have had.

Moments where the assistant's own checks changed the work, which the instructor should
verify rather than take on trust: Hub-pulled GGUF files ignoring Ollama's thinking
switch; the thinking demo running out of tokens; the tagging prompt over-using one
category.

## Diligence

- Every notebook was executed end to end before being shown; the course runner, the
  pre-commit hooks, and a link audit ran before the review.
- Personal data stays out of the repository: the raw transcripts are gitignored and the
  exported sessions are scrubbed.
- Disclosure: this folder, and the README's statement that the course was built with an
  AI assistant.
- Open items the instructor still owns: reconciling the diverged teach-mlflow clones,
  adding a license to the Python course repository, and confirming the exact evidence
  format the AI Fluency for Educators programme expects.
