# Reflection: lecture 1, tracing and prose rules (session 2026-10-12 to 2026-10-13)

*Draft prepared by the assistant from the session log; the instructor edits and owns
it.*

Session: `sessions/2026-10-12_75fc2ea8.md`, turns 1 to 28 (turn 28 was in progress at
export). Outcome: `lec_01a` reworked around the instructor's edits, including a
`num_predict` correction; f-strings everywhere; the guides updated for Ollama 0.40, with
tested versions; tracing moved from `lec_02b` to `lec_03a`, query rewriting into
`lec_02d`, "judging the judge" made mandatory; definition and paragraph rules in
`CLAUDE.md`, with a checker and a generated glossary. Seventeen commits, all pushed.

## Delegation

- **Kept by the instructor:** the two prose patterns; where tracing belongs; keeping
  DSPy; updating Ollama, which needed their sudo password; when to commit and push; the
  review of the term inventory.
- **Delegated:** completing the phrases left in `lec_01a`; testing Ollama's behaviour;
  the f-string conversion; the restructure from an approved plan; the checker and
  glossary builder.
- **Worth noting:** structural questions stayed in discussion ("do not act just explore
  and discuss for now", turn 17), and plan mode gated both large jobs.

## Description

- Turn 7 asked for an explanation "to me, not the notebook"; turn 8 posed "a question
  that you need to think on" before any edit.
- Turn 11 turned one fix into a rule: "everywhere, in all such cases, use f-strings".
- Turn 22 named two patterns, gave their purpose (reading "during the presentation and
  when students are studying it at home") and asked for a review before any plan.

## Discernment

Moments where the instructor's judgement changed the work:

1. "Is there a good reason to have mlflow in 2b that is not covered in lecture 3?" (turn
   16). The assistant argued to keep tracing there; the instructor decided "Tracing
   should be its own topics together with scorers" (`cd7d851`, `8745725`).
1. "moves DSpy to 03g instead of throwing it away. Renumbering is not a real cost" (turn
   20), against the assistant's proposal to remove DSPy.
1. The tested-versions table with a warning in every guide was the instructor's idea
   (`b430c34`).
1. Turn 25: the assistant's rewrite of `lec_01a` had defined the stop token before the
   prompt, with no term for the response. The instructor named the patterns behind it;
   they became rules 9 and 10 and a `def-order` check (`101de9c`).

Moments where the assistant's checks changed the work, which the instructor should
verify rather than take on trust:

- The tokenizer showed the new example is 13 tokens, not 12, and the Greek ratio about
  five times, not almost six.
- `lec_02c` failed on Ollama 0.13.5; the guide now asks for 0.34 or newer.
- Measured before writing, query rewriting lowered hit@1 on the 19 evaluation questions
  from 0.84 to 0.74 in one run, so `lec_02d` teaches "measure before adopting".
- The assistant chose which run's outputs to commit; in turn 25 it kept the committed
  ones over the instructor's own run, whose temperature-0 answers disagreed.

Failures the log itself exposes:

- Turns 1 and 2: the assistant said `git pull` would update this PC "cleanly". Asked to
  verify, it found two notebooks that would block the pull.
- Turns 7 and 8: the assistant said a 3000-token prompt in a 4096 window leaves about
  1096 answer tokens "whatever `num_predict` says". Its own test a turn later showed
  Ollama writes past the window. The instructor asked for the correction to be "clear";
  it opens the message of `3544cad`.
- Turn 26: asked to push all but the instructor's AI-log commit, the assistant tried to
  move local `main` onto a reordered history that included it. Claude Code's permission
  check denied this as destructive; local history was never part of the request.

## Diligence

- Lectures 2 and 3 were executed after the restructure, lecture 2 with no MLflow server,
  and example answers were checked against fresh outputs; CI passed after each push.
- A script confirmed that the `lec_01a` prose rewrite left code and outputs as
  committed.
- Open items the instructor owns:
  - the draft judge labels that the now mandatory `lec_03c` teaches from;
  - a question that reliably misses retrieval, for `lec_03e`;
  - Plan 1 (the `uoa_py_course` skills) and the rollout to the other notebooks (465
    checker hits), both just started in turn 28;
  - the term inventory, kept in a temporary folder (turn 27);
  - the answers to the assistant's multiple-choice questions (the `03f` slot, the
    definition form, rule 11) were missing from the first export; the exporter now keeps
    them, so check that they read as intended.
