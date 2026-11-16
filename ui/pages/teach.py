"""Page 4: peer-teaching missions."""
from __future__ import annotations


import streamlit as st

from busfactor import orchestrator as orc
from busfactor.i18n import t, tr_dynamic
from busfactor.missions import explain_mission
from busfactor.models import MissionStatus
from ui.state import ctx
from ui.theme import (
    MISSION_PILL, PAGES,
)
from ui.widgets import (
    dlabel, empty_state, esc, flow, go_to, need_viewer, next_step_card, page_header, page_nav, pill, show, show_reminders,
)


def _tick(mission_id: str, index: int, viewer: str) -> None:
    """Checkbox callback: save one ticked (or unticked) step of the teaching session."""
    orc.set_session_step(mission_id, viewer, index, bool(st.session_state[f"step-{mission_id}-{index}"]))


def session_block(m, viewer: str) -> None:
    """The pair's checklist for the teaching session, conversation starters and the 'we did it' action."""
    done = set(m.steps_done)
    st.markdown(f"**{t('Your teaching session')}**")
    for i, step in enumerate(m.steps):
        st.checkbox(step, value=i in done, key=f"step-{m.id}-{i}", on_change=_tick, args=(m.id, i, viewer))
    with st.expander(t("Conversation starters")):
        # card text is team-written: show it as escaped HTML, not as markdown (no links or images)
        show("<ul>" + "".join(f"<li>{esc(point)}</li>" for point in orc.session_talking_points(m.id)) + "</ul>")
    if m.session_done:
        st.success(t("Session held. The learner can take the retest now."))
        if viewer == m.learner_id:
            st.button(f"{t(PAGES[5])} \u2192", key=f"to-retest-{m.id}", type="primary", on_click=go_to, args=(5,))
    elif st.button(t("We held the session: tick everything"), key=f"done-{m.id}"):
        orc.mark_session_done(m.id, viewer)
        st.rerun()


def render() -> None:
    cx = ctx()
    need_viewer()
    page_header(4, "Teach Each Other",
                "For each decision only one person can explain, a teammate who understands it teaches one who doesn't.")
    next_step_card()
    show_reminders()
    if st.button(t("Set up teaching sessions"), type="primary"):
        orc.propose_missions()
        st.rerun()

    all_missions = orc.missions()
    if not all_missions:
        empty_state("users", "No missions yet",
                    "Press the button above and BusFactor pairs a mentor with a learner for every decision only one "
                    "person can explain.")
    for m in all_missions:
        involved = cx.viewer in (m.mentor_id, m.learner_id)
        public = m.status in (MissionStatus.accepted, MissionStatus.completed, MissionStatus.verified)
        # a failed retest is the learner's private result: others just see the mission in progress
        shown = MissionStatus.accepted if m.status == MissionStatus.completed and not involved else m.status
        with st.container(border=True):
            label, kind = MISSION_PILL[shown.value]
            left, right = st.columns([5, 1.8])
            left.markdown(f"**{dlabel(m.decision_id)} · {cx.cards[m.decision_id].title}**")
            with right:
                show(pill(label, kind))

            if m.status == MissionStatus.fallback:
                st.write(m.fallback_message)
                if involved:
                    show(f'<div class="bf-muted">{esc(tr_dynamic(explain_mission(m, cx.labels)))}</div>')
                pointers = [] if orc.is_demo_project() else orc.find_course_pointers(m.decision_id)
                if pointers:
                    st.markdown(t("Where your course material talks about it:"))
                    for hit in pointers:
                        show(f'<div class="bf-quote">“{esc(hit["snippet"])}”<br><span class="bf-muted">'
                             f'{esc(hit["file"])} · {esc(t("page"))} {hit["page"]}</span></div>')
                continue
            if not (involved or public):
                show('<div class="bf-muted">' + esc(t("The people in this mission are shown only to them until both accept.")) + '</div>')
                continue

            show(flow(m))
            show(f'<div class="bf-muted">{esc(tr_dynamic(explain_mission(m, cx.labels)))}</div>')
            if involved and m.status in (MissionStatus.accepted, MissionStatus.completed):
                session_block(m, cx.viewer)
            else:
                st.markdown("\n".join(f"{i}. {step}" for i, step in enumerate(m.steps, 1)))

            if involved and m.status == MissionStatus.proposed:
                mine = m.mentor_consent if cx.viewer == m.mentor_id else m.learner_consent
                role = "mentor" if cx.viewer == m.mentor_id else "learner"
                if mine:
                    st.info(t("You accepted. Waiting for the other person."))
                elif st.button(t("I agree to take part as {role}").format(role=role), key=f"acc-{m.id}",
                               type="primary"):
                    orc.accept_mission(m.id, cx.viewer)
                    st.rerun()

    page_nav(4)
