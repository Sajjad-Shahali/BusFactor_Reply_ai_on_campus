"""BusFactor Streamlit app. Run: streamlit run app.py

This file configures the page, builds the sidebar (project, language, identity, navigation) and hands the selected
page to its module in ui/pages/. Shared helpers are in ui/widgets.py, the theme in ui/theme.py."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from busfactor import auth  # noqa: E402
from busfactor import llm_provider  # noqa: E402
from busfactor import orchestrator as orc  # noqa: E402
from busfactor.i18n import LANGS, set_lang, t  # noqa: E402
from ui import tutorial  # noqa: E402
from ui.pages import check, coverage, evidence, overview, retest, setup, teach  # noqa: E402
from ui.state import Ctx, ctx  # noqa: E402
from ui.theme import BRAND, CSS, PAGE_HINTS, PAGES  # noqa: E402
from ui.widgets import avatar, esc, load_project_state, model_panel, model_status, show  # noqa: E402

st.set_page_config(page_title="BusFactor", page_icon=str(Path(__file__).parent / "web" / "favicon.png"), layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
orc.ensure_seeded()
st.session_state["_ctx"] = Ctx()   # fresh per run and per browser session (see ui/state.py)
# a model connected in this session (key in session memory only) is used for this run; None means the server default
llm_provider.set_session_config(st.session_state.get("llm"))
llm_provider.set_session_budget(st.session_state.setdefault("llm-budget", llm_provider.CallBudget()))

# ------------------------------------------------------------------ sidebar
with st.sidebar:   # the containers fix the display order; the code below fills them in the order logic needs
    box_top, box_you, box_nav, box_foot = st.container(), st.container(), st.container(), st.container()

with box_you:
    qp_lang = st.query_params.get("lang", "")
    lang_ids = list(LANGS)
    set_lang(st.selectbox("Language / Lingua", lang_ids, format_func=LANGS.get, key="lang",
                          index=lang_ids.index(qp_lang) if qp_lang in lang_ids else 0,
                          label_visibility="collapsed"))   # still read by screen readers

with box_top:
    show(BRAND)
    st.caption(t("Your grade is shared. Your understanding shouldn't be isolated."))
    tutorial.tour_button()
    model_status()
    all_projects = {p.id: p for p in orc.projects()}
    project_ids = list(all_projects)
    active = orc.active_project_id()
    chosen = st.selectbox(t("Project"), project_ids, index=project_ids.index(active) if active in project_ids else 0,
                          format_func=lambda pid: all_projects[pid].title
                          + (t(" · synthetic demo") if pid == orc.DEMO_PROJECT_ID else ""), key="project")
    if chosen != active:
        orc.open_project(chosen)
    load_project_state()
    members, names = ctx().members, ctx().names

# Optional deep links for demos and screenshots, e.g. ?page=3&as=M04
qp_page, qp_as = st.query_params.get("page", ""), st.query_params.get("as", "")
start_page = int(qp_page) if qp_page.isdigit() and 0 <= int(qp_page) < len(PAGES) else 0
member_ids = list(members)
protected = orc.is_protected()
unlocked = st.session_state.setdefault("unlocked", set())

with box_nav:
    current = st.session_state.get("page", PAGES[start_page])
    page = st.radio(t("Go to"), PAGES, index=start_page, format_func=t,
                    captions=[t(h) if PAGES[i] == current else "" for i, h in enumerate(PAGE_HINTS)],
                    key="page")   # keyed: the selected page survives a language switch

with box_you:
    picked = st.selectbox(t("Who are you?") if protected else t("View as"),
                          member_ids, format_func=lambda m: names[m] + (f" ({m})" if orc.is_demo_project() else ""),
                          index=member_ids.index(qp_as) if qp_as in member_ids else 0, key="viewer",
                          help=None if protected else t("Demo identity switch, not a login: anyone can pick any member."))
    if not protected:
        show(f'<div class="bf-muted">{esc(t("Demo identity switch, not a login."))}</div>')
    viewer, locked = picked, False
    # "keep me signed in": a signed, expiring token in the page link (opt-in, see below)
    token = st.query_params.get("k", "")
    if picked and protected and picked not in unlocked and token and auth.verify_session_token(token, picked):
        unlocked.add(picked)
    if picked and protected and picked not in unlocked:
        # a protected project shows a member's answers only after their personal access code is entered
        viewer, locked = None, True
        entered = st.text_input(t("Your access code"), type="password", key=f"code-{picked}")
        keep = st.checkbox(t("Keep me signed in on this device (7 days)"), key=f"keep-{picked}",
                           help=t("Adds a private token to this page's link. Anyone who has the link can open your "
                                  "answers until it expires, so do not share it."))
        if st.button(t("Unlock"), key=f"unlock-{picked}"):
            now = time.time()
            if now < st.session_state.get("lock_until", 0):
                st.error(t("Too many attempts. Wait 30 seconds."))
            elif auth.verify_member(picked, entered):
                unlocked.add(picked)
                st.session_state["fails"] = 0
                if keep:
                    st.query_params["k"] = auth.make_session_token(picked)
                st.rerun()
            else:
                st.session_state["fails"] = st.session_state.get("fails", 0) + 1
                if st.session_state["fails"] >= 5:   # throttle guessing (per browser session)
                    st.session_state.update(lock_until=now + 30, fails=0)
                st.error(t("That code does not match."))
        st.caption(t("Ask the project creator for your personal code."))
    if viewer:
        note = t("Signed in with an access code") if protected else t("Showing only this member's answers · no login yet")
        show(f'<div class="bf-me">{avatar(viewer, 30)}<div><b>{esc(names[viewer])}</b><span>{esc(note)}</span></div></div>')
        if protected:
            def sign_out(member: str = viewer) -> None:
                unlocked.discard(member)
                if "k" in st.query_params:
                    del st.query_params["k"]
            st.button(t("Sign out"), key="sign-out", on_click=sign_out)

with box_foot:
    st.divider()
    if st.toggle(t("Larger text"), key="big-text"):
        st.markdown("<style>html { font-size: 118%; }</style>", unsafe_allow_html=True)
    model_panel()
    st.caption(t(orc.grading_mode()))
    with st.popover(t("Reset demo data")):
        st.caption(t("Restores the synthetic demo to its starting point (coverage 1/5). Everything done in the demo "
                     "is lost. Your own projects are not touched."))
        if st.button(t("Reset the demo now"), key="reset-demo", type="primary"):
            orc.seed_demo_data()
            st.rerun()

c = ctx()
c.viewer, c.locked, c.protected, c.unlocked = viewer, locked, protected, unlocked

if st.session_state.get("tour_on"):
    tutorial.inject()   # the guided tour: a small robot that walks around the app (web/tutorial.js)

PAGE_MODULES = [overview, setup, check, coverage, teach, retest, evidence]
PAGE_MODULES[PAGES.index(page)].render()
