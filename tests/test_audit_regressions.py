"""Regressions for defects found while auditing the new features, plus the design acceptance checks."""
import csv
import html
import io
import threading
from pathlib import Path

import pdfplumber
import pytest
from streamlit.testing.v1 import AppTest

from busfactor import database as db
from busfactor import orchestrator as orc
from busfactor.i18n import get_lang, set_lang, t

ROOT = Path(__file__).resolve().parents[1]
REPORT = b"We chose PostgreSQL instead of MongoDB because registrations must be transactional."


@pytest.fixture(autouse=True)
def demo_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    db.set_db_path(tmp_path / "audit.db")
    orc.seed_demo_data()
    yield
    set_lang("en")


def live_project(title="Campus Events", decision_title="Use PostgreSQL instead of MongoDB"):
    p = orc.create_project(title, "Databases & Co <2026>", [("report.md", REPORT)], ["Ada"])
    card = orc.add_decision(title=decision_title, rationale="Registrations must be transactional.",
                            alternatives=["MongoDB"], source_file="report.md", page=1,
                            quote="We chose PostgreSQL instead of MongoDB because registrations must be transactional.")
    return p, card


# ------------------------------------------------------------------ exports with hostile text

def test_the_pdf_survives_markup_characters_in_titles():
    p, _ = live_project(title="Fish & Chips <b>3</b>", decision_title="Use A < B & C </para> instead")
    data = orc.export_team_report_pdf(p.id)                       # used to raise or swallow text as markup
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "Fish & Chips <b>3</b>" in text and "A < B & C" in text


@pytest.mark.parametrize("bad", ["=HYPERLINK(\"http://x\")", "+1+1", "-2+3", "@SUM(A1)"])
def test_csv_cells_that_look_like_formulas_are_neutralised(bad):
    p, _ = live_project(decision_title=bad)
    rows = list(csv.reader(io.StringIO(orc.export_decisions_csv(p.id))))
    cell = rows[1][1]
    assert cell == "'" + bad and not cell.startswith(bad[:1])


def test_uploads_have_a_size_limit():
    big = b"x" * (orc.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(ValueError, match="larger than 20 MB"):
        orc.create_project("Big", "", [("report.md", big)], ["Ada"])
    assert [p.id for p in orc.projects()] == ["P01"]              # nothing half-created
    p, _ = live_project()
    with pytest.raises(ValueError, match="larger than 20 MB"):
        orc.add_course_material("lecture.md", big, p.id)
    assert orc.course_materials(p.id) == []


def test_course_pages_are_read_once_per_file_version():
    p, card = live_project()
    orc.add_course_material("lecture.md", b"PostgreSQL transactions make registrations transactional: a seat is never sold twice.", p.id)
    orc._course_pages.cache_clear()
    orc.find_course_pointers(card.id)
    orc.find_course_pointers(card.id)
    assert orc._course_pages.cache_info().hits >= 1


# ------------------------------------------------------------------ the language belongs to the session

def test_two_sessions_can_use_different_languages_at_the_same_time():
    seen = {}
    ready, go = threading.Barrier(2), threading.Barrier(2)

    def session(code):
        set_lang(code)
        ready.wait()           # both sessions have chosen a language before either one translates anything
        seen[code] = (get_lang(), t("Overview"))
        go.wait()

    threads = [threading.Thread(target=session, args=(c,)) for c in ("it", "en")]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert seen == {"it": ("it", "Panoramica"), "en": ("en", "Overview")}


# ------------------------------------------------------------------ design acceptance (rendered pages)

def open_app(query_as: str, page: str, lang: str = "en") -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    if lang != "en":
        at.sidebar.selectbox(key="lang").set_value(lang)
    at.sidebar.selectbox(key="viewer").set_value(query_as)
    at.sidebar.radio[0].set_value(page)
    at.run()
    assert not at.exception, at.exception
    return at


def text(at: AppTest) -> str:
    return html.unescape(" ".join(md.value for md in at.markdown))


def test_coverage_page_leads_with_a_one_line_verdict():
    out = text(open_app("M01", "3. Team Coverage"))
    assert "3 decisions depend on one person." in out
    assert out.index("depend on one person") < out.index('class="bf-panel"')          # verdict comes before the ring


def test_status_pills_carry_an_icon_as_well_as_a_colour():
    out = text(open_app("M01", "3. Team Coverage"))
    assert out.count('class="bf-pill') >= 5 and out.count('class="ic') >= out.count('class="bf-pill')


def test_italian_view_translates_the_generated_explanations():
    out = text(open_app("M01", "3. Team Coverage", "it"))
    assert "3 decisioni dipendono da una sola persona." in out
    assert "Solo 1 membro l'ha dimostrata" in out and "Prossimo passo:" in out
    assert "Only 1 member has demonstrated it" not in out


def test_empty_states_say_what_to_do_next():
    assert "No missions yet" in text(open_app("M04", "4. Teach Each Other"))
    assert "You have no teaching mission as a learner" in text(open_app("M01", "5. Defense Retest"))
    assert "Nothing is waiting for review" in text(open_app("M01", "6. Evidence & Limits"))
    at = open_app("M01", "5. Defense Retest")
    assert any(b.key == "go-teach" for b in at.button)                       # a button, not just a sentence


def test_retest_shows_the_no_hints_lock_and_the_attempt_counter():
    orc.propose_missions()
    orc.accept_mission("T-D03-M04", "M02")
    orc.accept_mission("T-D03-M04", "M04")
    orc.mark_session_done("T-D03-M04", "M04")
    orc.start_retest("T-D03-M04", "M04")
    out = text(open_app("M04", "5. Defense Retest"))
    assert "Solo question · no hints" in out and "Attempt 1 of 2" in out
    assert "Tentativo 1 di 2" in text(open_app("M04", "5. Defense Retest", "it"))


def test_the_page_selection_survives_switching_the_language():
    at = open_app("M01", "3. Team Coverage")
    at.sidebar.selectbox(key="lang").set_value("it")
    at.run()
    assert at.sidebar.radio[0].value == "3. Team Coverage" and "Copertura del team" in text(at)
