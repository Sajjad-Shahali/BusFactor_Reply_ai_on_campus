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
    source_chip, LOCK_SVG, clear_draft, coverage_text, dlabel, draft_box, empty_state, esc, go_to, need_viewer, next_step_card, page_header, page_nav, pill, show, show_reminders, win,
)


QUIZ_LENGTH = 5


def quiz_summary(quiz: dict, history: list) -> None:
    """How the last quiz went. Practice only: it never changes coverage."""
    by_id = {q.id: ev for q, ev in history}
    scored = [by_id[i] for i in quiz["ids"] if by_id.get(i) is not None]
    strong = sum(e.rubric_score == 2 for e in scored)
    partial = sum(e.rubric_score == 1 for e in scored)
    review = sum(e.status.value == "insufficient_evidence" for e in scored)
    st.success(t("Quiz finished: {a} strong, {b} partly there, {c} not yet, out of {n}.").format(
        a=strong, b=partial, c=len(scored) - strong - partial - review, n=len(scored)))
    if review:
        st.info(t("{n} answer(s) could not be scored automatically and wait for human review.").format(n=review))
    st.caption(t("A quiz is practice only: it never changes team coverage."))


def render() -> None:
    cx = ctx()
    need_viewer()
    page_header(5, f"Defense Retest · {cx.names[cx.viewer]}",
                "After the teaching session, answer a new question on your own. No hints are available here.")
    next_step_card()
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
                st.write(t("Both people must accept the mission before the retest."))
                continue
            if m.status == MissionStatus.verified:
                show(win("Confirmed: you can explain it",
                         t("You explained {d} on a new question, with no hints. Team coverage went up.").format(
                             d=dlabel(m.decision_id))))
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
                st.warning(t("You have not agreed to be assessed, so the retest is not available."))
                continue
            if not m.session_done:   # the retest follows the teaching session
                st.info(t("Hold your teaching session first, then come back for the retest."))
                first, second = st.columns(2)
                first.button(f"{t(PAGES[4])} \u2192", key=f"to-teach-{m.id}", on_click=go_to, args=(4,))
                if second.button(t("We already did the session"), key=f"did-{m.id}"):
                    orc.mark_session_done(m.id, cx.viewer)
                    st.rerun()
                continue
            q, ev = next(((q, ev) for q, ev in orc.my_questions(cx.viewer, cx.viewer) if q.id == m.retest_question_id),
                         (None, None))
            if ev is not None:  # one answer per question: a retry needs a NEW question
                show(f'<div class="bf-muted">{esc(t("Your answer to the last question was recorded"))}: {esc(ev.feedback)}</div>')
            if q is None or ev is not None:
                if st.button(t("Start a new independent question"), key=f"rt-{m.id}"):
                    try:
                        with st.spinner(t("Preparing a question…")):
                            orc.start_retest(m.id, cx.viewer)
                        st.rerun()
                    except ValueError as err:  # every scenario was used: no pass-chasing loop
                        st.warning(str(err))
                continue

            used_n, total_n = orc.retest_progress(m.id)
            attempt = (t("Attempt {n} of {m}").format(n=used_n, m=total_n) if total_n
                       else t("Attempt {n}").format(n=used_n))
            show(f'<div><span class="bf-lock">{LOCK_SVG}{esc(t("Solo question · no hints"))}</span>'
                 f'<span class="bf-lock">{esc(attempt)}</span></div>')
            if q.scenario:
                show(f'<div class="bf-muted">{esc(t("New situation"))}: {esc(q.scenario)}</div>')
            show(f'<div class="bf-question">{esc(q.prompt)}</div>')
            show(source_chip(q))
            answer = draft_box(f"retest-{m.id}", t("Your answer"), 130)
            if st.button(t("Submit"), type="primary", key=f"retest-submit-{m.id}"):
                with st.spinner(t("Checking your answer…")):
                    res = orc.submit_retest(m.id, answer, cx.viewer)
                if res.blocked:
                    st.error(res.message)
                else:
                    clear_draft(f"retest-{m.id}")
                    cov = coverage_text(res.coverage.numerator, res.coverage.denominator)
                    if res.evidence.rubric_score == 2:
                        show(win("Confirmed: you can explain it", t("New question passed. Team coverage is now {cov}.").format(cov=cov)))
                    else:
                        label, kind = EVIDENCE_PILL[res.evidence.status.value]
                        show(pill(label, kind))
                        st.markdown(t("Not there yet. Ask your mentor to go through it again, then try a new question."))
                    st.markdown(f"{t('Result')}: {res.evidence.feedback}")
                    st.markdown(t("Mission status: **{status}** · team coverage now {cov}").format(
                        status=res.mission.status.value, cov=cov))

    st.subheader(t("Defense simulator"))
    sim_intro = t("A mock oral: a random question on one of your project's decisions, no hints. Practice only: "
                  "it never changes team coverage.")
    show(f'<div class="bf-muted">{esc(sim_intro)}</div>')
    if not cx.members[cx.viewer].consent_assessment:
        st.warning(t("You have not agreed to be assessed, so the simulator is not available."))
    else:
        sim_open = orc.open_simulator_question(cx.viewer)
        sim_done = [(q, ev) for q, ev in orc.simulator_history(cx.viewer) if ev is not None]
        quiz = st.session_state.get("quiz")
        if sim_open is None:
            if quiz and len(quiz["ids"]) >= quiz["total"]:
                quiz_summary(quiz, sim_done)
            first, second = st.columns(2)
            if first.button(t("Ask me a question"), key="sim-start"):
                st.session_state.pop("quiz", None)
                try:
                    with st.spinner(t("Preparing a question…")):
                        orc.start_simulator(cx.viewer)
                    st.rerun()
                except ValueError as err:   # every scenario was practised
                    st.warning(str(err))
            if second.button(t("Start a {n}-question quiz").format(n=QUIZ_LENGTH), key="quiz-start"):
                try:
                    with st.spinner(t("Preparing a question…")):
                        q = orc.start_simulator(cx.viewer)
                    st.session_state["quiz"] = {"total": QUIZ_LENGTH, "ids": [q.id]}
                    st.rerun()
                except ValueError as err:
                    st.warning(str(err))
        else:
            if quiz and sim_open.id in quiz["ids"]:
                show(f'<div class="bf-muted">{esc(t("Quiz: question {n} of {m}").format(n=quiz["ids"].index(sim_open.id) + 1, m=quiz["total"]))}</div>')
            show(f'<div><span class="bf-lock">{LOCK_SVG}{esc(t("Solo question · no hints"))}</span>'
                 f'<span class="bf-muted">{esc(dlabel(sim_open.decision_id))} · {esc(cx.cards[sim_open.decision_id].title)}</span></div>')
            if sim_open.scenario:
                show(f'<div class="bf-muted">{esc(t("New situation"))}: {esc(sim_open.scenario)}</div>')
            show(f'<div class="bf-question">{esc(sim_open.prompt)}</div>')
            show(source_chip(sim_open))
            sim_answer = draft_box("sim-answer", t("Your answer"), 120)
            if st.button(t("Send answer"), type="primary", key="sim-send"):
                with st.spinner(t("Checking your answer…")):
                    res = orc.submit_simulator(sim_open.id, sim_answer, cx.viewer)
                if res.blocked:
                    st.error(res.message)
                else:
                    clear_draft("sim-answer")
                    if quiz and sim_open.id in quiz["ids"] and len(quiz["ids"]) < quiz["total"]:
                        try:   # the next quiz question follows straight away
                            with st.spinner(t("Preparing a question…")):
                                quiz["ids"].append(orc.start_simulator(cx.viewer).id)
                        except ValueError:
                            quiz["total"] = len(quiz["ids"])   # nothing new is left: the quiz ends early
                    st.rerun()
        if sim_done:
            last_q, last_ev = sim_done[-1]
            label, kind = EVIDENCE_PILL[last_ev.status.value]
            show(f'{pill(label, kind)} <span class="bf-muted">{esc(dlabel(last_q.decision_id))} · '
                 f'{esc(t("{n} answered in the simulator").format(n=len(sim_done)))}</span>')
            st.markdown(f"{t('Result')}: {last_ev.feedback}")

    page_nav(5)
