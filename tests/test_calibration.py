"""The grader calibration set and its agreement metrics (offline, synthetic)."""
import importlib.util
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("calibrate", ROOT / "scripts" / "calibrate.py")
calibrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibrate)


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")


def test_the_calibration_set_is_complete_and_labelled_honestly():
    raw, items, decisions = calibrate.load_items()
    assert len(items) >= 40 and len({i["id"] for i in items}) == len(items)
    assert {i["human_score"] for i in items} == {0, 1, 2}
    assert {i["decision_id"] for i in items} == set(decisions)                 # every demo decision is covered
    per_decision = Counter(i["decision_id"] for i in items)
    assert min(per_decision.values()) >= 8
    assert "developer" in raw["labelled_by"] and "teaching assistant" in raw["_note"]          # provenance is stated, not hidden
    assert all(i["answer"].strip() for i in items)


def test_kappa_is_one_for_perfect_agreement_and_zero_for_chance_level():
    perfect = [(0, 0), (1, 1), (2, 2), (2, 2)]
    assert calibrate.cohen_kappa(perfect, weighted=False) == pytest.approx(1.0)
    assert calibrate.cohen_kappa(perfect, weighted=True) == pytest.approx(1.0)
    chance = [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert calibrate.cohen_kappa(chance, weighted=False) == pytest.approx(0.0)


def test_the_offline_rubric_does_not_regress_on_the_reference_set():
    raw, items, decisions = calibrate.load_items()
    summary = calibrate.summarise("offline", [(it, calibrate.grade(it, decisions)[0]) for it in items])
    assert summary["abstained"] == 0
    assert summary["exact"] >= 0.65 and summary["within1"] >= 0.9 and summary["kappa"] >= 0.5
    # clear strong and partial answers are graded as the reference says; the known weakness is paraphrase
    assert summary["by_kind"]["strong"] == (10, 10) and summary["by_kind"]["partial"] == (10, 10)
    assert summary["by_kind"]["paraphrase"][0] < summary["by_kind"]["paraphrase"][1]
