"""Compare BusFactor's grader with reference scores.

    python scripts/calibrate.py            # offline keyword rubric (no network)
    python scripts/calibrate.py --live     # also the live model (needs DEMO_MODE=false and LLM_API_KEY)
    python scripts/calibrate.py --write    # write docs/CALIBRATION.md

The reference scores in data/calibration/answers.json were drafted by the developer, not by an independent
grader: re-score them (a TA, ideally two people) before quoting the numbers as evidence. The set only covers
the synthetic demo decisions and the "why" question.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from busfactor.interview import bank_entry, rubric_for  # noqa: E402
from busfactor.models import DecisionCard, EvidenceStatus, InterviewQuestion, QuestionType  # noqa: E402

DATA = ROOT / "data" / "calibration" / "answers.json"
LABELS = (0, 1, 2)


def load_items() -> tuple[dict, list[dict], dict[str, DecisionCard]]:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    decisions = {d["id"]: DecisionCard.model_validate(d)
                 for d in json.loads((ROOT / "data" / "demo" / "decisions.json").read_text(encoding="utf-8"))["decisions"]}
    return raw, raw["items"], decisions


def grade(item: dict, decisions: dict[str, DecisionCard]) -> tuple[int | None, str]:
    """(score or None when the grader abstained, feedback)."""
    from busfactor.rubrics import evaluate_answer
    decision = decisions[item["decision_id"]]
    entry = bank_entry(decision)
    assert entry is not None, "the calibration set only covers demo decisions"
    question = InterviewQuestion(
        id=f"Q-cal-{item['id']}", decision_id=decision.id, member_id="CAL", prompt=entry["why"],
        question_type=QuestionType.why, rubric_expectations=rubric_for(decision), source_refs=decision.source_refs,
        mode="practice", project_id=decision.project_id)
    ev = evaluate_answer(question, item["answer"], decision)
    return (None if ev.status == EvidenceStatus.insufficient_evidence else ev.rubric_score), ev.feedback


def cohen_kappa(pairs: list[tuple[int, int]], weighted: bool) -> float:
    n = len(pairs)
    if n == 0:
        return float("nan")
    k = len(LABELS)
    weight = (lambda i, j: ((i - j) ** 2) / ((k - 1) ** 2)) if weighted else (lambda i, j: 0.0 if i == j else 1.0)
    observed = [[0] * k for _ in range(k)]
    for h, m in pairs:
        observed[h][m] += 1
    human, machine = Counter(h for h, _ in pairs), Counter(m for _, m in pairs)
    num = sum(weight(i, j) * observed[i][j] / n for i in range(k) for j in range(k))
    den = sum(weight(i, j) * (human[i] / n) * (machine[j] / n) for i in range(k) for j in range(k))
    return 1 - num / den if den else float("nan")


def summarise(name: str, results: list[tuple[dict, int | None]]) -> dict:
    scored = [(it["human_score"], s) for it, s in results if s is not None]
    abstained = len(results) - len(scored)
    exact = sum(h == m for h, m in scored)
    within1 = sum(abs(h - m) <= 1 for h, m in scored)
    over = sum(m > h for h, m in scored)
    under = sum(m < h for h, m in scored)
    matrix = [[sum(1 for h, m in scored if h == i and m == j) for j in LABELS] for i in LABELS]
    by_kind: dict[str, list[int]] = {}
    for it, s in results:
        if s is not None:
            by_kind.setdefault(it["kind"], []).append(int(it["human_score"] == s))
    return {"name": name, "n": len(results), "scored": len(scored), "abstained": abstained,
            "exact": exact / len(scored) if scored else float("nan"),
            "within1": within1 / len(scored) if scored else float("nan"),
            "kappa": cohen_kappa(scored, False), "wkappa": cohen_kappa(scored, True),
            "over": over, "under": under, "matrix": matrix,
            "by_kind": {k: (sum(v), len(v)) for k, v in sorted(by_kind.items())},
            "wrong": [(it["id"], it["kind"], it["human_score"], s) for it, s in results
                      if s is not None and s != it["human_score"]]}


def render(summaries: list[dict], note: str) -> str:
    lines = ["# Grader calibration", "", f"> {note}", ""]
    for s in summaries:
        lines += [f"## {s['name']}", "",
                  f"- Answers graded: {s['scored']} of {s['n']} (abstained and sent to human review: {s['abstained']})",
                  f"- Exact agreement with the reference score: **{s['exact']:.0%}** ({round(s['exact'] * s['scored'])}/{s['scored']})",
                  f"- Within one point: {s['within1']:.0%}",
                  f"- Cohen's kappa: {s['kappa']:.2f} · quadratic-weighted kappa: {s['wkappa']:.2f}",
                  f"- Scored higher than the reference: {s['over']} · lower: {s['under']}", "",
                  "Reference score (rows) vs grader score (columns):", "",
                  "| ref \\ grader | 0 | 1 | 2 |", "|---|---|---|---|"]
        lines += [f"| {i} | " + " | ".join(str(c) for c in row) + " |" for i, row in enumerate(s["matrix"])]
        lines += ["", "Agreement by answer type: " + ", ".join(f"{k} {a}/{b}" for k, (a, b) in s["by_kind"].items()), ""]
        if s["wrong"]:
            lines += ["Disagreements (id, type, reference, grader): " +
                      "; ".join(f"{i} {k} {h}→{m}" for i, k, h, m in s["wrong"]), ""]
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):   # Windows consoles default to a code page without arrows
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="also grade with the live model")
    parser.add_argument("--write", action="store_true", help="write docs/CALIBRATION.md")
    args = parser.parse_args()

    raw, items, decisions = load_items()
    summaries = []
    os.environ["DEMO_MODE"] = "true"
    summaries.append(summarise("Offline keyword rubric (demo mode)", [(it, grade(it, decisions)[0]) for it in items]))
    if args.live:
        os.environ["DEMO_MODE"] = "false"
        from busfactor import llm_provider
        if not llm_provider.llm_available():
            sys.exit("--live needs DEMO_MODE=false and LLM_API_KEY in the environment.")
        summaries.append(summarise("Live model", [(it, grade(it, decisions)[0]) for it in items]))
    note = ("Reference scores were drafted by the developer, not by an independent grader; this is a consistency "
            "check on a synthetic set of 40 answers, not a validation. Re-score `data/calibration/answers.json` "
            "with a TA before quoting these numbers.")
    report = render(summaries, note)
    print(report)
    if args.write:
        out = ROOT / "docs" / "CALIBRATION.md"
        out.write_text(report + "\n", encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
