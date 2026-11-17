"""The guided tour: a small 3D robot walks around the app and writes the help in a thought cloud.

The robot itself is web/tutorial.js (CSS 3D, no library). This module only builds what it shows: the steps, their text in
the current language and the colours of the active palette. The script is injected only while the tour is switched on
(sidebar "Start the tutorial"); the robot's last step clicks the sidebar "Stop the tutorial" button to say it is done.

Steps point at parts of the app by CSS selector (Streamlit widgets with a key have the class ``st-key-<key>``) or by the
text of a button or heading, and name the page that has to be open. If something is not on screen the robot says the
step anyway and stands in the middle, so the tour never gets stuck.
"""
from __future__ import annotations

import inspect
import json
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from busfactor.i18n import t
from ui import palettes

ROOT = Path(__file__).resolve().parents[1]
SIDEBAR = '[data-testid="stSidebar"]'


@lru_cache(maxsize=1)
def _script() -> str:
    return (ROOT / "web" / "tutorial.js").read_text(encoding="utf-8")


def step_definitions() -> list[dict]:
    """The tour in order. Text is English here and translated by t() when the config is built."""
    return [
        dict(id="welcome", page=None, css=None, title="Hi, I'm Bus!",
             text="I'll walk you through BusFactor in about two minutes. It helps a group project check that everyone can "
                  "explain the key decisions, not only their own part. Press Next, or use the arrow keys."),
        dict(id="project", page=None, css=".st-key-project", title="1. Pick a project",
             text="This is the demo, with made-up data, so you can play safely. Your own project shows up here after you "
                  "create it on the Project Setup page."),
        dict(id="viewer", page=None, css=".st-key-viewer", title="2. Pick who you are",
             text="In the demo, choose any member (A to D) to see the app through their eyes. In a real project you unlock "
                  "your own account with your personal access code."),
        dict(id="nav", page=None, css=".st-key-page", title="3. The six pages",
             text="Work from the top down: set up, private check, coverage, teaching, retest, evidence. You do not have to "
                  "remember the order, because every page tells you the next step."),
        dict(id="next-step", page=0, css=".bf-next", title="4. Always start here",
             text="“Your next step” is the one thing to do now. Press its button and it takes you to the right page."),
        dict(id="kpis", page=0, css=".bf-kpis", title="5. Four numbers",
             text="Coverage is how many key decisions at least two people can explain. “Only 1 person can explain” is the "
                  "risk. Missions and verified decisions show the progress."),
        dict(id="decisions", page=1, css=".bf-quote", title="6. Page 1: the decisions",
             text="The team's key decisions come from your report. Each one has a quote that the app checks on its page, and a "
                  "member confirms it before anybody is questioned."),
        dict(id="check", page=2, css="button", match="Get my questions", title="7. Page 2: your private check",
             text="Choose up to two decisions that you did NOT make and press this button. You get one question for each. "
                  "Only you see your answers."),
        dict(id="privacy", page=2, css='[data-testid="stExpander"]', match="Who can see what?", title="Your privacy",
             text="Open this to see exactly who can see what. In short: your answers are private and the team only sees counts."),
        dict(id="verdict", page=3, css=".bf-verdict", title="8. Page 3: the verdict",
             text="This sentence is the point of the app: how many decisions depend on one person. When it is red, "
                  "that is a gap in what the team knows."),
        dict(id="dots", page=3, css=".bf-dots2", title="The dots",
             text="Each dot is a person who can explain the decision. One filled dot means one person carries it."),
        dict(id="teach", page=4, css="button", match="Set up teaching sessions", title="9. Page 4: teach each other",
             text="For each decision only one person can explain, the app pairs a mentor with a learner. Both agree, talk it "
                  "through, tick the checklist, and the retest unlocks."),
        dict(id="retest", page=5, css='[data-testid="stHeading"]', match="Defense simulator", title="10. Page 5: prove it",
             text="After teaching, the learner answers a NEW question with no hints. Pass it and coverage goes up. Down here a "
                  "mock oral and a 5-question quiz let anyone practise; they never change coverage."),
        dict(id="evidence", page=6, css='[data-baseweb="tab-list"]', title="11. Page 6: evidence",
             text="Where every decision comes from, a plain-language log of what happened, a review queue for answers the "
                  "model could not score, and the limits of this prototype."),
        dict(id="model", page=None, css=f'{SIDEBAR} [data-testid="stExpander"]', match=["Connect a model", "Model: connected"],
             title="12. Connect a model (optional)",
             text="Without a model you get demo questions. Connect Claude, Codex or another model here and the app writes "
                  "real questions and scores answers. Your key stays in this session only."),
        dict(id="end", page=None, css=None, title="That is the whole loop",
             text="Find a risk, teach, retest, and watch coverage go up. On any page, start with “Your next step”. "
                  "You can call me again from the sidebar."),
    ]


def _translated(step: dict) -> dict:
    out = dict(step)
    out["title"], out["text"] = t(step["title"]), t(step["text"])
    if step.get("match"):
        words = [step["match"]] if isinstance(step["match"], str) else list(step["match"])
        out["match"] = [t(w) for w in words]
    return out


def colors() -> dict:
    """Robot, cloud and highlight colours from the active palette (the original blue when there is none)."""
    p = palettes.get()
    if p is None:
        return dict(hi="#6F88FF", glow="rgba(111,136,255,.35)", eye="#9DB0FF", robot="#8FA5FF", robot2="#56628F",
                    plate="#0A0F1F", bubble="#E8EBF7", bubbleText="#0A0F1F", accent="#3A54E0", onAccent="#FFFFFF")
    return dict(hi=p["hi"], glow=f"rgba({p['hi_rgb']},.35)", eye=p["hi2"], robot=p["hi"], robot2=p["line_strong"],
                plate=p["bg"], bubble=p["text"], bubbleText=p["bg"], accent=p["fill"], onAccent=p["on_fill"])


def config() -> dict:
    return {
        "steps": [_translated(s) for s in step_definitions()],
        "colors": colors(),
        "ui": {"next": t("Next"), "back": t("Back"), "skip": t("Skip tour"), "finish": t("Done"),
               "step": t("Step {n} of {m}"), "moving": t("Walking over…"), "dialog": t("Tutorial")},
    }


def script_html() -> str:
    """The loader element plus the script with this run's config (JSON, so no text is ever treated as code)."""
    # every "<" becomes <: no text can look like a tag (</script>, <!--, <script>) to the HTML parser
    payload = json.dumps(config(), ensure_ascii=False).replace("<", "\\u003c")
    return '<div id="bf-tour-loader"></div><script>' + _script().replace("__CONFIG__", payload) + "</script>"


def inject() -> None:
    """Put the tour on the page. Newer Streamlit runs the script in the page; older versions use a zero-height iframe."""
    html = script_html()
    if "unsafe_allow_javascript" in inspect.signature(st.html).parameters:
        st.html(html, unsafe_allow_javascript=True)
    else:  # pragma: no cover - only on Streamlit versions before st.html could run scripts
        components.html(html, height=0)


def start() -> None:
    st.session_state["tour_on"] = True


def stop() -> None:
    st.session_state["tour_on"] = False


def tour_button(location: str = "sidebar") -> None:
    """Start/stop button. The stop button must exist while the tour runs: the robot clicks it when it finishes."""
    active = bool(st.session_state.get("tour_on"))
    if location == "page":   # a page only offers to START it: the one Stop button lives in the sidebar (a key must be unique)
        if not active:
            st.button(t("Take the 2-minute tutorial"), key="tour-start-page", on_click=start, type="primary",
                      icon=":material/smart_toy:")
        return
    if active:
        st.button(t("Stop the tutorial"), key="tour-stop", on_click=stop, icon=":material/close:", width="stretch")
    else:
        st.button(t("Start the tutorial"), key="tour-start", on_click=start, icon=":material/smart_toy:",
                  type="primary", width="stretch", help=t("A small robot walks you through the app in about two minutes."))
