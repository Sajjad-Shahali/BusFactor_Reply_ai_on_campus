"""Page 2: a member's private check, consent and owner check."""
from __future__ import annotations


import streamlit as st

from busfactor import orchestrator as orc
from busfactor.i18n import t
from ui.state import ctx
from ui.theme import (
    EVIDENCE_PILL,
)
from ui.widgets import (
    clear_draft, dlabel, draft_box, empty_state, esc, need_viewer, next_step_card, page_header, page_nav, pill, privacy_panel, show,
)


def render() -> None:
    cx = ctx()
    need_viewer()
    page_header(2, f"Private Check · {cx.names[cx.viewer]}",
                "Questions about decisions you didn't make. Your answers and feedback are private to you.")
    next_step_card()
    privacy_panel()
    st.info(t("Scores are practice feedback, not grades. You can answer in English or Italian; "
              "grammar and language never lower the score."), icon="🔒")
    me = cx.members[cx.viewer]
    with st.expander(t("My consent"), expanded=not me.consent_assessment):
        st.caption("Only you can change these, and you can withdraw at any time. Withdrawing removes your answers "
                   "from the team's coverage." + (" In the demo, consent is synthetic." if orc.is_demo_project() else ""))
        c_assess = st.checkbox(t("I agree to be assessed (private questions and retests)"),
                               value=me.consent_assessment, key="c-assess")
        c_mentor = st.checkbox(t("I am willing to mentor a teammate"), value=me.consent_mentor, key="c-mentor")
        c_learn = st.checkbox(t("I am willing to learn from a teammate"), value=me.consent_learner, key="c-learn")
        c_review = st.checkbox(t("Allow a human reviewer to read my answers that the model could not score "
                                 "(without my name)"), value=me.consent_review, key="c-review")
        if st.button(t("Save my consent"), key="c-save"):
            orc.update_consent(cx.viewer, cx.viewer, assessment=c_assess, mentor=c_mentor, learner=c_learn,
                               review=c_review)
            st.rerun()
    if not me.consent_assessment:
        st.warning(t("You have not agreed to be assessed, so BusFactor will not ask or score you."))
        st.stop()

    with st.container(border=True):
        others = [d for d in cx.cards.values() if d.owner_id != cx.viewer]
        choice = st.multiselect("Choose up to 2 decisions to be checked on",
                                [d.id for d in others], default=orc.suggest_check_decisions(cx.viewer),
                                max_selections=2, format_func=lambda i: f"{dlabel(i)} · {cx.cards[i].title}")
        if st.button(t("Get my questions"), type="primary"):
            made = orc.start_check(cx.viewer, choice)
            st.success(f"{len(made)} new question(s) below." if made else "No new questions for these decisions.")

    owned = orc.owner_check_decisions(cx.viewer)
    if owned:   # secondary task: it sits below the main one
        with st.expander(t("Show you can explain your own decision")):
            show('<div class="bf-muted">Owning a decision is not proof you can defend it. One independent '
                 'question, no hints: only a full answer lets you mentor a teammate on it.</div>')
            pick = st.selectbox("Decision", owned, format_func=lambda i: f"{dlabel(i)} · {cx.cards[i].title}", key="own-pick")
            if st.button(t("Start my question"), key="own-start"):
                try:
                    orc.start_owner_check(cx.viewer, pick)
                    st.rerun()
                except ValueError as err:
                    st.warning(str(err))

    pairs = [(q, ev) for q, ev in orc.my_questions(cx.viewer, cx.viewer)
             if q.mode != "independent" or orc.is_owner_check(q)]
    open_qs = [(q, ev) for q, ev in pairs if ev is None]
    done_qs = [(q, ev) for q, ev in pairs if ev is not None]

    st.subheader(t("To answer ({n})").format(n=len(open_qs)))
    if not open_qs:
        empty_state("inbox", "Nothing to answer right now",
                    "Choose up to two decisions above and press \u201cGet my questions\u201d.")
    for q, _ in sorted(open_qs, key=lambda x: x[0].id):
        with st.container(border=True):
            kind_label = (t("Your own decision · no hints") if orc.is_owner_check(q)
                          else q.question_type.value.replace("_", " ").title())
            show(f'{pill(kind_label, "blue")} '
                 f'<span class="bf-muted">{esc(dlabel(q.decision_id))} · {esc(cx.cards[q.decision_id].title)}</span>')
            show(f'<div class="bf-question">{esc(q.prompt)}</div>')
            answer = draft_box(f"a-{q.id}", t("Your answer"), 110)
            if st.button(t("Submit"), type="primary", key=f"submit-{q.id}"):
                with st.spinner(t("Checking your answer…")):
                    res = orc.submit_answer(q.id, answer, cx.viewer)
                if res.blocked:
                    st.warning(res.message)
                else:
                    clear_draft(f"a-{q.id}")
                    st.rerun()

    st.subheader(t("Answered ({n})").format(n=len(done_qs)))
    for q, ev in sorted(done_qs, key=lambda x: x[0].id):
        with st.container(border=True):
            label, kind = EVIDENCE_PILL[ev.status.value]
            show(f'{pill(label, kind)} <span class="bf-muted">{esc(dlabel(q.decision_id))} · '
                 f'{esc(q.question_type.value.replace("_", " "))}</span>')
            show(f'<div class="bf-title" style="margin:0.4rem 0">{esc(q.prompt)}</div>')
            show(f'<div class="bf-muted">Your answer: {esc(ev.answer)}</div>')
            st.markdown(f"Result: {ev.feedback}")

    page_nav(2)
