"""Page 5: independent retest, follow-up and the defense simulator."""
from __future__ import annotations


import streamlit as st

from busfactor import orchestrator as orc
from busfactor.i18n import t
from busfactor.models import MissionStatus
from ui.state import ctx
from ui.theme import (
    EVIDENCE_PILL, MISSION_PILL, PAGES,
)
from ui.widgets import (
    LOCK_SVG, coverage_text, dlabel, empty_state, esc, need_viewer, page_header,
    pill, show, show_reminders, win,
)


def render() -> None:
    cx = ctx()
    need_viewer()
    page_header(5, f"Defense Retest · {cx.names[cx.viewer]}",
                "After the teaching session, answer a new question on your own. No hints are available here.")
    show_reminders()
    mine = [m for m in orc.missions() if m.learner_id == cx.viewer and m.mentor_id]
    if not mine:
        empty_state("path", "You have no teaching mission as a learner",
                    "A retest opens after a mentor and you both accept a mission on the Teach Each Other page.")
        st.button(t("Go to Teach Each Other"), key="go-teach", on_click=lambda: st.session_state.update(page=PAGES[4]))
    for m in mine:
        with st.container(border=True):
            label, kind = MISSION_PILL[m.status.value]
            left, right = st.columns([5, 1.8])
            left.markdown(f"**{dlabel(m.decision_id)} · {cx.cards[m.decision_id].title}**")
            with right:
                show(pill(label, kind))

            if m.status == MissionStatus.proposed:
                st.write("Both people must accept the mission before the retest.")
                continue
            if m.status == MissionStatus.verified:
                show(win("Transfer verified", f"You explained {dlabel(m.decision_id)} on a new question, with no hints. "
                                              "Team coverage went up."))
                if orc.followup_due(m):
                    st.info(t("Follow-up check due: you passed the retest for {d} {n} days ago. One new question "
                              "shows whether it stuck.").format(d=dlabel(m.decision_id),
                                                                n=(orc.utcnow() - m.verified_at).days))
                    if st.button(t("Start the follow-up check"), key=f"fu-{m.id}"):
                        try:
                            orc.start_followup(m.id, cx.viewer)
                            st.rerun()
                        except ValueError as err:  # e.g. no unused scenario is left
                            st.warning(str(err))
                continue
            if not cx.members[cx.viewer].consent_assessment:
                st.warning("You have not agreed to be assessed, so the retest is not available.")
                continue
            q, ev = next(((q, ev) for q, ev in orc.my_questions(cx.viewer, cx.viewer) if q.id == m.retest_question_id),
                         (None, None))
            if ev is not None:  # one answer per question: a retry needs a NEW question
                show(f'<div class="bf-muted">Your answer to the last question was recorded: {esc(ev.feedback)}</div>')
            if q is None or ev is not None:
                if st.button(t("Start a new independent question"), key=f"rt-{m.id}"):
                    try:
                        orc.start_retest(m.id, cx.viewer)
                        st.rerun()
                    except ValueError as err:  # every scenario was used: no pass-chasing loop
                        st.warning(str(err))
                continue

            used_n, total_n = orc.retest_progress(m.id)
            attempt = (t("Attempt {n} of {m}").format(n=used_n, m=total_n) if total_n
                       else t("Attempt {n}").format(n=used_n))
            show(f'<div><span class="bf-lock">{LOCK_SVG}{esc(t("Independent check · no hints"))}</span>'
                 f'<span class="bf-lock">{esc(attempt)}</span></div>')
            if q.scenario:
                show(f'<div class="bf-muted">New situation: {esc(q.scenario)}</div>')
            show(f'<div class="bf-question">{esc(q.prompt)}</div>')
            with st.form(f"retest-{m.id}"):
                answer = st.text_area("Your answer", height=130)
                if st.form_submit_button("Submit", type="primary"):
                    res = orc.submit_retest(m.id, answer, cx.viewer)
                    if res.blocked:
                        st.error(res.message)
                    else:
                        cov = coverage_text(res.coverage.numerator, res.coverage.denominator)
                        if res.evidence.rubric_score == 2:
                            show(win("Transfer verified", f"New question passed. Team coverage is now {cov}."))
                        else:
                            label, kind = EVIDENCE_PILL[res.evidence.status.value]
                            show(pill(label, kind))
                        st.markdown(f"Result: {res.evidence.feedback}")
                        st.markdown(f"Mission status: **{res.mission.status.value}** · team coverage now {cov}")

    st.subheader(t("Defense simulator"))
    sim_intro = t("A mock oral: a random question on one of your project's decisions, no hints. Practice only: "
                  "it never changes team coverage.")
    show(f'<div class="bf-muted">{esc(sim_intro)}</div>')
    if not cx.members[cx.viewer].consent_assessment:
        st.warning(t("You have not agreed to be assessed, so the simulator is not available."))
    else:
        sim_open = orc.open_simulator_question(cx.viewer)
        sim_done = [(q, ev) for q, ev in orc.simulator_history(cx.viewer) if ev is not None]
        if sim_open is None:
            if st.button(t("Ask me a question"), key="sim-start"):
                try:
                    orc.start_simulator(cx.viewer)
                    st.rerun()
                except ValueError as err:   # every scenario was practised
                    st.warning(str(err))
        else:
            show(f'<div><span class="bf-lock">{LOCK_SVG}{esc(t("Independent check · no hints"))}</span>'
                 f'<span class="bf-muted">{esc(dlabel(sim_open.decision_id))} · {esc(cx.cards[sim_open.decision_id].title)}</span></div>')
            if sim_open.scenario:
                show(f'<div class="bf-muted">New situation: {esc(sim_open.scenario)}</div>')
            show(f'<div class="bf-question">{esc(sim_open.prompt)}</div>')
            with st.form("sim-form"):
                sim_answer = st.text_area(t("Your answer"), height=120, key="sim-answer")
                if st.form_submit_button(t("Send answer"), type="primary"):
                    res = orc.submit_simulator(sim_open.id, sim_answer, cx.viewer)
                    if res.blocked:
                        st.error(res.message)
                    else:
                        st.rerun()
        if sim_done:
            last_q, last_ev = sim_done[-1]
            label, kind = EVIDENCE_PILL[last_ev.status.value]
            show(f'{pill(label, kind)} <span class="bf-muted">{esc(dlabel(last_q.decision_id))} · '
                 f'{esc(t("{n} answered in the simulator").format(n=len(sim_done)))}</span>')
            st.markdown(f"{t('Result')}: {last_ev.feedback}")
