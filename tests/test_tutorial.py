"""The guided tour (the walking robot): its steps, translations, wiring and the script it injects (offline)."""
import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from busfactor import database as db
from busfactor import orchestrator as orc
from busfactor.i18n import IT, set_lang
from ui import tutorial

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def demo_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    db.set_db_path(tmp_path / "tour.db")
    orc.seed_demo_data()
    yield
    set_lang("en")


def extract_config(html: str) -> dict:
    """The JSON config the script was given (it is the first object literal after `const CFG =`)."""
    script = html.split("<script>", 1)[1]
    start = script.index("const CFG = ") + len("const CFG = ")
    depth, i = 0, start
    while True:
        depth += {"{": 1, "}": -1}.get(script[i], 0)
        i += 1
        if depth == 0:
            break
    return json.loads(script[start:i].replace("<\\/", "</"))


def test_the_tour_has_a_clear_story_in_order():
    steps = tutorial.step_definitions()
    ids = [s["id"] for s in steps]
    assert ids[0] == "welcome" and ids[-1] == "end" and len(ids) >= 14 and len(set(ids)) == len(ids)
    pages = [s["page"] for s in steps if s["page"] is not None]
    assert pages == sorted(pages) and set(pages) == {0, 1, 2, 3, 4, 5, 6}        # it visits every page, top to bottom
    for s in steps:
        assert s["title"].strip() and len(s["text"]) > 40
        assert (s["css"] is None) == (s["id"] in ("welcome", "end"))              # only the first and last stand in the middle


def test_every_step_is_translated_into_italian():
    set_lang("it")
    steps = tutorial.config()["steps"]
    english = tutorial.step_definitions()
    for it, en in zip(steps, english, strict=True):
        assert it["title"] != en["title"] and it["text"] != en["text"], en["id"]
        assert it["title"] in IT.values() and it["text"] in IT.values(), en["id"]
    ui = tutorial.config()["ui"]
    assert ui["next"] == "Avanti" and ui["back"] == "Indietro" and ui["finish"] == "Fatto"


def test_matching_texts_follow_the_language_of_the_page():
    en = {s["id"]: s["match"] for s in tutorial.config()["steps"] if s.get("match")}
    assert en["check"] == ["Get my questions"] and en["teach"] == ["Set up teaching sessions"]
    set_lang("it")
    it = {s["id"]: s["match"] for s in tutorial.config()["steps"] if s.get("match")}
    assert it["check"] == ["Ottieni le mie domande"] and it["teach"] != en["teach"]


def test_the_script_carries_the_config_as_data_and_never_as_code():
    html = tutorial.script_html()
    assert html.startswith('<div id="bf-tour-loader"></div><script>') and "__CONFIG__" not in html
    config = extract_config(html)
    assert len(config["steps"]) == len(tutorial.step_definitions())
    assert set(config["colors"]) >= {"hi", "eye", "robot", "plate", "bubble", "bubbleText", "accent", "onAccent"}
    assert html.count("</script>") == 1                                              # no text can close the script early


def test_text_with_script_tags_cannot_break_out_of_the_page(monkeypatch):
    monkeypatch.setattr(tutorial, "step_definitions", lambda: [
        dict(id="x", page=None, css=None, title="</script><img src=x onerror=alert(1)>", text="a" * 50 + "</script><script>alert(2)</script>")])
    html = tutorial.script_html()
    assert html.count("</script>") == 1 and "<script>alert(2)" not in html and "<img" not in html
    assert extract_config(html)["steps"][0]["title"].startswith("</script>")        # the text survives as plain data


def test_colours_come_from_the_palette_and_have_a_readable_cloud(monkeypatch):
    brass = tutorial.colors()
    assert brass["bubble"] == "#F3EEE6" and brass["bubbleText"] == "#120E0B"
    from ui import palettes
    monkeypatch.setattr(palettes, "DEFAULT", "classic")
    assert tutorial.colors()["hi"] == "#6F88FF"                                       # the original palette still works


def test_the_script_file_uses_text_nodes_and_a_throwaway_overlay():
    js = (ROOT / "web" / "tutorial.js").read_text(encoding="utf-8")
    assert "textContent" in js and "innerHTML" not in js                              # help text is never parsed as HTML
    assert "prefers-reduced-motion" in js and "role', 'dialog'" in js and "aria-live" in js
    assert "Escape" in js and "ArrowRight" in js                                      # keyboard control
    assert "st-key-tour-stop" in js                                                   # finishing tells the app the tour is over
    assert not re.search(r"\beval\s*\(|new Function|document\.write", js)


# ------------------------------------------------------------------ in the app

def open_app() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def test_the_sidebar_starts_and_stops_the_tour_and_no_key_is_used_twice():
    at = open_app()
    assert not any("bf-tour-loader" in h.value for h in at.get("html"))               # nothing is injected while it is off
    assert any(b.key == "tour-start" for b in at.sidebar.button) and any(b.key == "tour-start-page" for b in at.button)
    at.sidebar.button(key="tour-start").click()
    at.run()
    assert not at.exception, at.exception                                             # a duplicate button key used to crash the Overview
    assert any("bf-tour-loader" in h.value for h in at.get("html"))                   # the robot's script is on the page
    assert any(b.key == "tour-stop" for b in at.sidebar.button) and not any(b.key == "tour-start" for b in at.sidebar.button)
    assert not any(b.key == "tour-start-page" for b in at.button)                      # the page offers no second Stop/Start
    at.sidebar.button(key="tour-stop").click()
    at.run()
    assert not at.exception and not any("bf-tour-loader" in h.value for h in at.get("html"))


@pytest.mark.parametrize("page", ["Overview", "1. Project Setup", "2. Private Check", "3. Team Coverage",
                                  "4. Teach Each Other", "5. Defense Retest", "6. Evidence & Limits"])
def test_every_page_renders_with_the_tour_running(page):
    at = open_app()
    at.sidebar.button(key="tour-start").click()
    at.run()
    at.sidebar.selectbox(key="viewer").set_value("M04")
    at.sidebar.radio[0].set_value(page)
    at.run()
    assert not at.exception, (page, at.exception)
    assert sum(b.key == "tour-stop" for b in at.sidebar.button) == 1


def test_the_loader_takes_no_room_on_the_page():
    from ui.theme import CSS
    assert '[data-testid="stHtml"]:has(#bf-tour-loader)' in CSS and "display: none" in CSS.split("bf-tour-loader")[1][:60]
