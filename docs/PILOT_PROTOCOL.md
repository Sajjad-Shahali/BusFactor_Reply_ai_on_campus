# Pilot protocol (2–3 consenting teams)

A small pilot turns "prototype indicator" into something you can describe honestly. It cannot prove that BusFactor
improves learning. It shows whether the loop works with real teams and what goes wrong. **No pilot has been run yet;
this file is the plan.**

## Before you start

1. **Permission.** Get the course lecturer's OK to use the project documents, and written consent from every
   participant. Use the template below. Participation is optional and can be withdrawn at any time (the app removes a
   member's answers from coverage when they withdraw consent).
2. **Data handling.** Run one instance per team on a machine you control (Docker is the easiest). Do not use a public
   deployment. Answers are stored in plain text in `busfactor.db`: delete the database when the pilot ends.
3. **Mode.** Live model (`DEMO_MODE=false`, `LLM_API_KEY`) means answers are sent to the API; say so in the consent
   text. Without the model, answers wait for human review (a TA can use the review queue).
4. **Baseline for scoring.** Ask a TA to score about 20 of the collected answers independently of the app, so you can
   report agreement between the grader and a human (see `scripts/calibrate.py` for the metrics).

## Procedure (about 60–90 minutes per team)

1. One member creates the project in **Project Setup**, uploads the team's real report, adds the team, and saves the
   **access codes** shown once. Add 4–6 decisions (by hand with exact quotes, or with the live model) and confirm them.
2. Each member signs in with their code, ticks consent, and takes the **private check** (two questions).
3. Record coverage on **Team Coverage** (this is the baseline; the app also stores it automatically).
4. Run **Teach Each Other**: propose missions, accept them, and let the pairs actually talk (10–15 minutes).
5. Learners take the **retest** (new question, no hints).
6. Optional: a few days later, the **follow-up** question opens; learners take it.
7. Each participant fills in a 3-question survey: *Did the questions feel fair? Did the teaching session help? Would
   you use this before a real oral defense?* (1–5 plus one free-text comment.)

## What to report

Run `python scripts/pilot_summary.py` for counts per team, then state:

- number of teams and members (and how many consented),
- coverage at the start and after the retest, per team, with numerator and denominator,
- missions proposed, accepted, verified; retests passed on the first and on a later attempt,
- human–grader agreement on the TA-scored sample,
- the survey results and what participants said was confusing,
- everything that failed: abstentions, blocked answer requests, people who withdrew.

**Do not claim** learning gains, causal effects or generalisation from two or three teams. Say "in this pilot, N of M
single points of failure became covered after a teaching session" and stop there.

## Consent text (template)

> I agree to take part in a short pilot of BusFactor, a study tool for group projects. My answers to project questions
> are stored in plain text on the organiser's computer, are visible only to me in the app, and are shown to my team only
> as counts. [If the live model is used: my answers and the project report are sent to the Anthropic API to be scored.]
> My scores are practice feedback, not grades. I can withdraw at any time and my answers will no longer count. The
> database is deleted at the end of the pilot.
