"""Teaching-session progress, "your next step", talking points and the keep-me-signed-in token (offline)."""
from datetime import timedelta

import pytest

from busfactor import auth
from busfactor import database as db
from busfactor import orchestrator as orc
from busfactor.models import DecisionCard, MissionStatus, utcnow
from busfactor.missions import talking_points
from demo_answers import strong_answer

MISSION = "T-D03-M04"


@pytest.fixture(autouse=True)
def demo_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    db.set_db_path(tmp_path / "hci.db")
    orc.seed_demo_data()


def accepted():
    orc.propose_missions()
    orc.accept_mission(MISSION, "M02")
    orc.accept_mission(MISSION, "M04")


# ------------------------------------------------------------------ teaching-session progress

def test_ticking_all_steps_holds_the_session_and_stops_the_reminder():
    accepted()
    later = utcnow() + timedelta(days=orc.REMINDER_DAYS + 1)
    assert [r["kind"] for r in orc.reminders("M04", later)] == ["session"]
    for i in range(3):
        m = orc.set_session_step(MISSION, "M02", i, True)
        assert not m.session_done and m.session_done_at is None
    m = orc.set_session_step(MISSION, "M04", 3, True)
    assert m.session_done and m.steps_done == [0, 1, 2, 3] and m.session_done_at is not None
    assert orc.reminders("M04", later) == []                      # the pair did what the reminder asked
    m = orc.set_session_step(MISSION, "M04", 3, False)             # unticking reopens it
    assert not m.session_done and m.session_done_at is None


def test_only_the_pair_can_tick_and_only_after_both_accepted():
    orc.propose_missions()
    with pytest.raises(ValueError, match="accept the mission first"):
        orc.set_session_step(MISSION, "M02", 0, True)
    accepted_mission = orc.accept_mission(MISSION, "M02")
    assert accepted_mission.status == MissionStatus.proposed
    orc.accept_mission(MISSION, "M04")
    with pytest.raises(PermissionError):
        orc.set_session_step(MISSION, "M01", 0, True)              # not part of the mission
    with pytest.raises(ValueError, match="Unknown step"):
        orc.set_session_step(MISSION, "M02", 9, True)


def test_mark_session_done_ticks_everything_and_is_visible_only_to_the_pair_in_the_log():
    accepted()
    m = orc.mark_session_done(MISSION, "M04")
    assert m.session_done and len(m.steps_done) == len(m.steps)
    assert any(e.action == "session_progress" for e in orc.team_log("M02"))      # the mentor sees it
    assert not any(e.action == "session_progress" for e in orc.team_log("M01"))  # a third member does not


def test_talking_points_use_only_the_confirmed_card():
    card = db.get_record(DecisionCard, "D03")
    points = talking_points(card)
    assert card.title in points[0] and any("accuracy" in p.lower() for p in points)   # the card's alternative
    assert len(points) == 4 and points[-1].startswith("Swap roles")
    orc.propose_missions()
    assert orc.session_talking_points(MISSION) == points                       # the mission uses the same card


# ------------------------------------------------------------------ "your next step"

def test_next_step_follows_the_journey_of_a_member():
    first = orc.next_step("M04")
    assert first.page == 2 and "private check" in first.text.lower()          # nothing taken yet
    orc.propose_missions()
    assert orc.next_step("M04").page == 4 and "waiting for your OK" in orc.next_step("M04").text
    orc.accept_mission(MISSION, "M04")
    orc.accept_mission(MISSION, "M02")
    step = orc.next_step("M04")
    assert step.page == 4 and "Hold your teaching session" in step.text and step.params == {"d": "D03"}
    orc.mark_session_done(MISSION, "M04")
    step = orc.next_step("M04")
    assert step.page == 5 and "retest" in step.text.lower()
    q = orc.start_retest(MISSION, "M04")
    orc.submit_retest(MISSION, strong_answer(q), "M04")
    assert orc.next_step("M04", utcnow() + timedelta(days=orc.FOLLOWUP_DAYS, minutes=1)).text.startswith("Follow-up")


def test_next_step_asks_for_consent_and_for_confirmed_decisions_first():
    p = orc.create_project("Live", "", [("r.md", b"We chose PostgreSQL.")], ["Ada"])
    ada = f"{p.id}-M01"
    assert orc.next_step(ada).page == 1                                        # no confirmed decision yet
    card = orc.add_decision(title="Use PostgreSQL", rationale="Transactions.", alternatives=["MongoDB"],
                            source_file="r.md", page=1, quote="We chose PostgreSQL.")
    orc.confirm_decision(card.id, None, ada)
    assert orc.next_step(ada).page == 2 and "Agree to be assessed" in orc.next_step(ada).text
    orc.update_consent(ada, ada, assessment=True, mentor=False, learner=False)
    assert orc.next_step(ada).page in (2, 5)                                   # a check, or the simulator when none is left


def test_next_step_always_names_a_concrete_page_and_a_button():
    for member in ("M01", "M02", "M03", "M04"):
        step = orc.next_step(member)
        assert 1 <= step.page <= 5 and step.text and step.button


# ------------------------------------------------------------------ keep me signed in

def test_a_session_token_is_bound_to_one_member_and_expires():
    token = auth.make_session_token("M04", now=1_000_000.0)
    assert auth.verify_session_token(token, "M04", now=1_000_000.0 + 3600)
    assert not auth.verify_session_token(token, "M01", now=1_000_000.0 + 3600)             # another member
    assert not auth.verify_session_token(token, "M04", now=1_000_000.0 + 8 * 86400)        # expired
    tampered = token.replace("M04", "M01", 1)
    assert not auth.verify_session_token(tampered, "M01", now=1_000_000.0 + 3600)          # signature no longer fits
    assert not auth.verify_session_token("garbage", "M04") and not auth.verify_session_token("", "M04")


def test_the_signing_secret_is_created_once_and_never_the_member_code():
    first = auth.make_session_token("M04", now=5.0)
    second = auth.make_session_token("M04", now=5.0)
    assert first == second and db.get_setting("auth:secret")
    code = auth.issue_member_code("M04")
    assert code.replace("-", "") not in first
