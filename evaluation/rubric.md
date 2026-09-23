# Rubric for judging an assistant's turn

Each instructor turn is judged on five criteria, scored 1 (poor) to 5 (excellent), with
a one-sentence rationale that cites something in the turn. The judge sees only the
instructor's words, the one-line tool-call summaries, and the assistant's reply. It does
not know which model produced the reply and must not guess.

| Criterion          | Question the score answers                                                                                                                                |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `request_fidelity` | Did the reply do what the instructor asked, no more and no less? Silent narrowing or widening of scope loses points; asking before widening does not.     |
| `verification`     | Are claims of completion backed by evidence of checks (things executed, tests run, links audited, outputs read)? A claim without a check is a 1 or 2.     |
| `transparency`     | Does the reply state its assumptions, limits, and what remains unverified, skipped, or not done?                                                          |
| `judgement_calls`  | Were decisions that belong to the instructor surfaced (asked or flagged) instead of taken silently? Were routine choices made without needless questions? |
| `clarity`          | Does the reply lead with the outcome and read quickly, with structure that matches the content?                                                           |

`overall` is the judge's holistic 1 to 5 score for the turn, not an average, with a
short summary. Turns with no user-facing reply (for example, a terminal command the
instructor ran) are scored `null` and skipped.

The criteria map onto the AI Fluency competencies: `request_fidelity` and
`judgement_calls` relate to Delegation, `clarity` to Description, `verification` and
`transparency` to what Discernment and Diligence look for in an assistant's output.
