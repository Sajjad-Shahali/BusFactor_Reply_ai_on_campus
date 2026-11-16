"""Page 4: peer-teaching missions."""
from __future__ import annotations


import streamlit as st

from busfactor import orchestrator as orc
from busfactor.i18n import t, tr_dynamic
from busfactor.missions import explain_mission
from busfactor.models import MissionStatus
from ui.state import ctx
from ui.theme import (
    MISSION_PILL,
)
from ui.widgets import (
    dlabel, empty_state, esc, flow, need_viewer, page_header,
    pill, show, show_reminders,
)


def render() -> None:
    cx = ctx()
    need_viewer()
    page_header(4, "Teach Each Other",
                "For each decision only one person can explain, a teammate who understands it teaches one who doesn't.")
    show_reminders()
    if st.button(t("Find knowledge silos and propose missions"), type="primary"):
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
                show('<div class="bf-muted">The people in this mission are shown only to them until both accept.</div>')
                continue

            show(flow(m))
            show(f'<div class="bf-muted">{esc(tr_dynamic(explain_mission(m, cx.labels)))}</div>')
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
