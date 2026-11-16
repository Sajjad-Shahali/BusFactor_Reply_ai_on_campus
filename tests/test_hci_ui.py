"""HCI fixes seen through the real pages: guidance, session checklist, drafts, privacy, plain language, sign-in."""
import html
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from busfactor import auth
from busfactor import database as db
from busfactor import orchestrator as orc
from busfactor.i18n import set_lang

ROOT = Path(__file__).resolve().parents[1]
MISSION = "T-D03-M04"


@pytest.fixture(autouse=True)
def demo_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    db.set_db_path(tmp_path / "hci_ui.db")
    orc.seed_demo_data()
    yield
    set_lang("en")


def open_app(viewer: str, page: str, query: dict | None = None) -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    for k, v in (query or {}).items():
        at.query_params[k] = v
    at.run()
    at.sidebar.selectbox(key="viewer").set_value(viewer)
    at.sidebar.radio[0].set_value(page)
    at.run()
    assert not at.exception, at.exception
    return at


def text(at: AppTest) -> str:
    return html.unescape(" ".join(md.value for md in at.markdown))


def accepted() -> None:
    orc.propose_missions()
    orc.accept_mission(MISSION, "M02")
    orc.accept_mission(MISSION, "M04")


# ------------------------------------------------------------------ 1. your next step, Back/Next

def test_every_page_tells_the_member_what_to_do_next():
    for page in ("Overview", "2. Private Check", "3. Team Coverage", "4. Teach Each Other", "5. Defense Retest",
                 "6. Evidence & Limits"):
        out = text(open_app("M04", page))
        assert "Your next step" in out, page


def test_the_next_step_button_goes_to_the_right_page():
    at = open_app("M04", "3. Team Coverage")
    assert "Take your private check" in text(at)
    at.button(key="next-step").click()
    at.run()
    assert at.sidebar.radio[0].value == "2. Private Check"
    assert "Take your private check" in text(at)
    assert not any(b.key == "next-step" for b in at.button)            # already on the right page: no redundant button


def test_back_and_next_buttons_walk_through_the_pages():
    at = open_app("M01", "3. Team Coverage")
    at.button(key="nav-next-3").click()
    at.run()
    assert at.sidebar.radio[0].value == "4. Teach Each Other"
    at.button(key="nav-back-4").click()
    at.run()
    assert at.sidebar.radio[0].value == "3. Team Coverage"
    first = open_app("M01", "Overview")
    assert not any(b.key == "nav-back-0" for b in first.button) and any(b.key == "nav-next-0" for b in first.button)


# ------------------------------------------------------------------ 3. the teaching session

def test_the_pair_ticks_off_the_session_and_the_retest_unlocks():
    accepted()
    at = open_app("M04", "4. Teach Each Other")
    assert "Your teaching session" in text(at) and len([c for c in at.checkbox if c.key.startswith(f"step-{MISSION}")]) == 4
    assert any("Conversation starters" == e.label for e in at.expander)
    at.checkbox(key=f"step-{MISSION}-0").check()
    at.run()
    assert orc._mission(MISSION).steps_done == [0] and not orc._mission(MISSION).session_done
    at.button(key=f"done-{MISSION}").click()
    at.run()
    assert orc._mission(MISSION).session_done
    assert any("Session held" in s.value for s in at.success)
    assert any(b.key == f"to-retest-{MISSION}" for b in at.button)               # the learner gets a way on
    mentor = open_app("M02", "4. Teach Each Other")
    assert not any(b.key == f"to-retest-{MISSION}" for b in mentor.button)       # the mentor does not take the retest
    assert any("Session held" in s.value for s in mentor.success)


def test_others_see_the_mission_as_a_plain_list_without_the_checklist():
    accepted()
    outsider = open_app("M01", "4. Teach Each Other")
    assert not any(c.key.startswith("step-") for c in outsider.checkbox)


# ------------------------------------------------------------------ 4. drafts survive moving around

def test_a_typed_draft_survives_leaving_the_page():
    at = open_app("M04", "2. Private Check")
    at.multiselect[0].set_value(["D03"])
    next(b for b in at.button if b.label == "Get my questions").click()
    at.run()
    key = "a-Q-D03-M04-why" if any(a.key == "a-Q-D03-M04-why" for a in at.text_area) else at.text_area[0].key
    at.text_area(key=key).input("My half-written answer about the metric")
    at.run()
    at.sidebar.radio[0].set_value("3. Team Coverage")
    at.run()
    assert not any(a.key == key for a in at.text_area)                          # the widget is gone while we are away
    at.sidebar.radio[0].set_value("2. Private Check")
    at.run()
    assert at.text_area(key=key).value == "My half-written answer about the metric"
    assert any("cannot edit it" in c.value for c in at.caption)                 # the note about sending


def test_sending_an_answer_clears_its_draft():
    at = open_app("M04", "2. Private Check")
    at.multiselect[0].set_value(["D03"])
    next(b for b in at.button if b.label == "Get my questions").click()
    at.run()
    key = at.text_area[0].key
    at.text_area(key=key).input("Accuracy is bad with imbalanced classes.")
    next(b for b in at.button if b.label == "Submit").click()
    at.run()
    assert key not in at.session_state["drafts"]                                # the draft is gone once it is sent
    assert not any(a.key == key for a in at.text_area)


# ------------------------------------------------------------------ 7. who can see what

def test_the_privacy_panel_says_who_sees_what():
    at = open_app("M04", "2. Private Check")
    assert any(e.label == "Who can see what?" for e in at.expander)
    out = text(at)
    assert "Only you" in out and "counts only" in out and "never with your name" in out


# ------------------------------------------------------------------ 2. plain language, tooltips

def test_labels_use_plain_words_with_a_tooltip_for_the_term():
    out = text(open_app("M01", "3. Team Coverage"))
    assert "Only 1 can explain it" in out and "2+ can explain it" in out
    assert "Single point of failure" not in out and "knowledge silos" not in out
    assert 'title="Only one member has shown they can explain this decision' in out
    assert "Decisions only 1 person can explain" in out


# ------------------------------------------------------------------ 11. a readable log

def test_the_action_log_is_in_plain_sentences_until_technical_details_are_asked_for():
    orc.propose_missions()
    at = open_app("M01", "6. Evidence & Limits")
    tables = [df.value for df in at.dataframe]
    log = next(df for df in tables if "What happened" in df.columns)
    assert "Action" not in log.columns and "Detail" not in log.columns
    assert any("teaching sessions" in v.lower() for v in log["What happened"])
    assert not any("." in v and "_" in v for v in log["What happened"])        # no raw action names such as start_check.select
    at.toggle(key="log-details").set_value(True)
    at.run()
    detailed = next(df.value for df in at.dataframe if "What happened" in df.value.columns)
    assert "Action" in detailed.columns and "Detail" in detailed.columns


# ------------------------------------------------------------------ 9 + 10. overview: list first, map optional

def test_overview_lists_decisions_first_and_keeps_the_map_behind_a_toggle():
    at = open_app("M01", "Overview")
    out = text(at)
    assert any("Decisions at a glance" in h.value for h in at.subheader) and 'class="bf-list"' in out
    assert at.toggle(key="show-map").value is False
    assert any(b.key == "tour" for b in at.button)                              # a clear first action in the demo
    at.toggle(key="show-map").set_value(True)
    at.run()
    assert not at.exception


# ------------------------------------------------------------------ 8. sidebar, larger text

def test_the_sidebar_uses_a_short_label_and_offers_larger_text():
    at = open_app("M01", "Overview")
    assert at.sidebar.selectbox(key="viewer").label == "View as"
    assert "Demo identity switch, not a login." in " ".join(md.value for md in at.sidebar.markdown)
    at.sidebar.toggle(key="big-text").set_value(True)
    at.run()
    assert "font-size: 118%" in " ".join(md.value for md in at.sidebar.markdown)


# ------------------------------------------------------------------ 4. keep me signed in / sign out

def protected_project():
    p = orc.create_project("Campus Events", "Databases", [("r.md", b"We chose PostgreSQL.")], ["Ada", "Grace"])
    codes = orc.protect_project(p.id)
    orc.open_project(p.id)
    return p, f"{p.id}-M01", f"{p.id}-M02", codes


def open_protected(p, member, token=None):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    if token:
        at.query_params["k"] = token
    at.run()
    at.sidebar.selectbox(key="project").set_value(p.id)
    at.run()
    at.sidebar.selectbox(key="viewer").set_value(member)
    at.run()
    assert not at.exception, at.exception
    return at


def test_a_valid_token_signs_the_member_in_without_the_code():
    p, ada, grace, _ = protected_project()
    locked = open_protected(p, ada)
    assert any(t.key == f"code-{ada}" for t in locked.sidebar.text_input)          # asks for the code
    signed_in = open_protected(p, ada, auth.make_session_token(ada))
    assert not any(t.key == f"code-{ada}" for t in signed_in.sidebar.text_input)
    assert any(b.key == "sign-out" for b in signed_in.sidebar.button)


def test_a_token_for_another_member_or_a_forged_one_does_not_sign_anyone_in():
    p, ada, grace, _ = protected_project()
    other = open_protected(p, ada, auth.make_session_token(grace))
    assert any(t.key == f"code-{ada}" for t in other.sidebar.text_input)
    forged = open_protected(p, ada, f"{ada}|9999999999|{'0' * 32}")
    assert any(t.key == f"code-{ada}" for t in forged.sidebar.text_input)


def test_unlocking_with_the_keep_signed_in_box_adds_a_token_and_sign_out_removes_it():
    p, ada, grace, codes = protected_project()
    at = open_protected(p, ada)
    at.sidebar.text_input(key=f"code-{ada}").input(codes["members"][ada])
    at.sidebar.checkbox(key=f"keep-{ada}").check()
    at.sidebar.button(key=f"unlock-{ada}").click()
    at.run()
    assert "k" in at.query_params and auth.verify_session_token(at.query_params["k"][0] if isinstance(
        at.query_params["k"], list) else at.query_params["k"], ada)
    at.sidebar.button(key="sign-out").click()
    at.run()
    assert "k" not in at.query_params
    assert any(t.key == f"code-{ada}" for t in at.sidebar.text_input)


# ------------------------------------------------------------------ Italian leftovers

def test_the_limits_tab_and_log_columns_are_translated():
    set_lang("it")
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.query_params["lang"] = "it"
    at.run()
    at.sidebar.selectbox(key="viewer").set_value("M01")
    at.sidebar.radio[0].set_value("6. Evidence & Limits")
    at.run()
    out = text(at)
    assert "I punteggi sono feedback di allenamento" in out and "Scores are practice feedback" not in out
    assert any("Cosa è successo" in df.value.columns for df in at.dataframe)
