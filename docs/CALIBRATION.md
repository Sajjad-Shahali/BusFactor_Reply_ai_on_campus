# Grader calibration

> Reference scores were drafted by the developer, not by an independent grader; this is a consistency check on a synthetic set of 40 answers, not a validation. Re-score `data/calibration/answers.json` with a TA before quoting these numbers.

## Offline keyword rubric (demo mode)

- Answers graded: 40 of 40 (abstained and sent to human review: 0)
- Exact agreement with the reference score: **72%** (29/40)
- Within one point: 92%
- Cohen's kappa: 0.60 · quadratic-weighted kappa: 0.62
- Scored higher than the reference: 6 · lower: 5

Reference score (rows) vs grader score (columns):

| ref \ grader | 0 | 1 | 2 |
|---|---|---|---|
| 0 | 9 | 6 | 0 |
| 1 | 0 | 10 | 0 |
| 2 | 3 | 2 | 10 |

Agreement by answer type: keyword_list 0/5, paraphrase 0/5, partial 10/10, strong 10/10, vague 4/5, wrong 5/5

Disagreements (id, type, reference, grader): C03 paraphrase 2→1; C06 keyword_list 0→1; C11 paraphrase 2→1; C14 keyword_list 0→1; C19 paraphrase 2→0; C22 keyword_list 0→1; C27 paraphrase 2→0; C30 keyword_list 0→1; C31 vague 0→1; C35 paraphrase 2→0; C38 keyword_list 0→1

