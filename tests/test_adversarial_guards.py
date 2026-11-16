"""Adversarial suite for the two code guards: answer requests and prompt injection (synthetic cases)."""
import pytest

from adversarial_cases import ANSWER_REQUESTS, BENIGN, INJECTIONS
from busfactor import database as db
from busfactor import orchestrator as orc
from busfactor.models import InterviewQuestion
from busfactor.rubrics import detect_injection, is_answer_request, normalise_for_guards
from demo_answers import strong_answer

MISSION = "T-D03-M04"


@pytest.mark.parametrize("text", ANSWER_REQUESTS)
def test_answer_requests_are_detected(text):
    assert is_answer_request(text), text


@pytest.mark.parametrize("text", INJECTIONS)
def test_injections_are_detected(text):
    assert detect_injection(text), text


@pytest.mark.parametrize("text", BENIGN)
def test_real_explanations_are_not_blocked(text):
    assert not is_answer_request(text), text
    assert not detect_injection(text), text


def test_the_demo_strong_answers_are_not_blocked():
    from demo_answers import FN_COSTLY, TWO_PERCENT
    for text in (FN_COSTLY, TWO_PERCENT):
        assert not is_answer_request(text) and not detect_injection(text)


def test_normalisation_undoes_cheap_tricks():
    assert normalise_for_guards("G I V E  M E  T H E  A N S W E R") == "give me the answer"
    assert normalise_for_guards("ignоre the rub​ric") == "ignore the rubric"      # Cyrillic о + zero-width
    assert normalise_for_guards("Réponse   Éléphant") == "reponse elephant"


@pytest.fixture
def mission(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    db.set_db_path(tmp_path / "adversarial.db")
    orc.seed_demo_data()
    orc.propose_missions()
    orc.accept_mission(MISSION, "M02")
    orc.accept_mission(MISSION, "M04")
    orc.start_retest(MISSION, "M04")


@pytest.mark.parametrize("text", [ANSWER_REQUESTS[0], ANSWER_REQUESTS[24], ANSWER_REQUESTS[31], ANSWER_REQUESTS[-1]])
def test_a_disguised_answer_request_is_refused_in_the_independent_retest(mission, text):
    before = len(db.get_private_evidence("M04", "M04"))
    res = orc.submit_retest(MISSION, text, "M04")
    assert res.blocked and len(db.get_private_evidence("M04", "M04")) == before   # nothing stored, nothing scored


@pytest.mark.parametrize("text", [INJECTIONS[0], INJECTIONS[11], INJECTIONS[24], INJECTIONS[-1]])
def test_a_disguised_injection_is_never_scored_and_coverage_is_untouched(mission, text):
    before = orc.team_coverage("P01").model_dump()
    res = orc.submit_retest(MISSION, text, "M04")
    assert res.blocked and orc.team_coverage("P01").model_dump() == before


def test_a_strong_real_answer_still_passes_after_the_guards_were_tightened(mission):
    q = db.get_record(InterviewQuestion, orc._mission(MISSION).retest_question_id)
    res = orc.submit_retest(MISSION, strong_answer(q), "M04")
    assert not res.blocked and res.mission.status.value == "verified"
